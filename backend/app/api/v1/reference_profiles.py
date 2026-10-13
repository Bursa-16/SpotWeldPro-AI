"""Reference profile management endpoints — Phase 2A.

ACCESS POLICY:
  All endpoints require authenticated user (HTTPBearer JWT).

ISOLATION CONTRACT:
  - System default profiles (org_id IS NULL): readable by all authenticated users.
  - Organization-owned profiles: readable/writable only by org members.
  - Cross-organization enumeration is prevented.
  - System defaults are read-only for all non-SYSTEM_ADMIN users (HR-06).

APPROVAL PREREQUISITES (HR-08 — fail-closed):
  1. Approver holds APPROVER+ role in the profile's organization.
  2. Approver is not the profile creator (four-eyes principle).
  3. parameter_bands.bands is non-empty (engineering measurement data present).
  4. nugget_criterion is a non-empty dict.
  5. source_provenance.basis is a non-empty string (evidence source documented).
  Any unmet prerequisite → HTTP 422, explicit error, no state change.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    _ORG_ROLE_RANK,
    get_current_org_membership,
    get_current_user,
)
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import OrgRole, ProfileApprovalEventType, ProfileStatus, UserRole
from app.models.error_codes import ApiErrorCode
from app.models.profile_entities import (
    OrganizationMember,
    ProfileApprovalEvent,
    ReferenceProfileRecord,
)
from app.models.role_policy import normalize_user_role
from app.schemas.profile import (
    ProfileApprovalEventResponse,
    ProfileApproveRequest,
    ProfileCreate,
    ProfilePatch,
    ProfileRecordResponse,
    ProfileSummaryResponse,
)

router = APIRouter(prefix="/reference-profiles", tags=["Reference Profiles"])

_APPROVABLE_STATUSES = {
    ProfileStatus.DRAFT,
    ProfileStatus.REVIEW_REQUIRED,
    ProfileStatus.VALIDATED,
}
_IMMUTABLE_STATUSES = {
    ProfileStatus.APPROVED,
    ProfileStatus.ACTIVE,
    ProfileStatus.REVOKED,
    ProfileStatus.SUPERSEDED,
}


def _require_org_membership_at_least(
    org_id: int,
    user: User,
    db: Session,
    minimum_role: OrgRole,
) -> OrganizationMember:
    """Raise 403 if caller lacks minimum_role in org_id."""
    membership = get_current_org_membership(org_id=org_id, user=user, db=db)
    if normalize_user_role(user.role) == UserRole.SYSTEM_ADMIN:
        return membership
    actual_rank = _ORG_ROLE_RANK.get(membership.org_role, 0)
    required_rank = _ORG_ROLE_RANK[minimum_role]
    if actual_rank < required_rank:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.PERMISSION_DENIED,
                "message": f"Org role {minimum_role} or higher required.",
                "context": {"required": minimum_role, "actual": membership.org_role},
            },
        )
    return membership


def _check_profile_readable(profile: ReferenceProfileRecord, user: User, db: Session) -> None:
    """Raise 403/404 if caller cannot read this profile."""
    if profile.org_id is None:
        return  # system default — all authenticated users may read
    get_current_org_membership(org_id=profile.org_id, user=user, db=db)


def _check_approval_prerequisites(profile: ReferenceProfileRecord) -> None:
    """Raise 422 if engineering evidence prerequisites are not met. HR-08."""
    errors: list[str] = []

    bands = profile.parameter_bands.get("bands", []) if isinstance(profile.parameter_bands, dict) else []
    if not bands:
        errors.append(
            "parameter_bands.bands must be a non-empty list "
            "(engineering measurement data required before approval)"
        )

    if not profile.nugget_criterion or profile.nugget_criterion == {}:
        errors.append("nugget_criterion must be a non-empty dict (nugget size criterion required)")

    basis = (
        profile.source_provenance.get("basis", "").strip()
        if isinstance(profile.source_provenance, dict)
        else ""
    )
    if not basis:
        errors.append(
            "source_provenance.basis must be a non-empty string "
            "(engineering evidence source required)"
        )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": ApiErrorCode.PROFILE_NOT_APPROVED,
                "message": "Profile cannot be approved: engineering prerequisites not met (HR-08).",
                "context": {"prerequisites_failed": errors},
            },
        )


@router.get("", response_model=list[ProfileSummaryResponse])
def list_profiles(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReferenceProfileRecord]:
    """List profiles accessible to the caller.
    Returns: (1) system default profiles (org_id IS NULL) and
             (2) profiles owned by the caller's orgs.
    Org B profiles are never returned to an Org A-only member.
    """
    memberships = db.scalars(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active.is_(True),
        )
    ).all()
    member_org_ids = [m.org_id for m in memberships]

    from sqlalchemy import or_, and_
    stmt = select(ReferenceProfileRecord).where(
        or_(
            ReferenceProfileRecord.org_id.is_(None),
            ReferenceProfileRecord.org_id.in_(member_org_ids) if member_org_ids else and_(False),
        )
    ).order_by(ReferenceProfileRecord.profile_code, ReferenceProfileRecord.version)

    return list(db.scalars(stmt).all())


@router.get("/{profile_id}", response_model=ProfileRecordResponse)
def get_profile(
    profile_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReferenceProfileRecord:
    """Get profile detail. System defaults visible to all; org profiles require membership."""
    profile = db.scalar(select(ReferenceProfileRecord).where(ReferenceProfileRecord.id == profile_id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ApiErrorCode.RESOURCE_NOT_FOUND,
                "message": "Reference profile not found.",
                "context": {"profile_id": profile_id},
            },
        )
    _check_profile_readable(profile, user, db)
    return profile


@router.post("", response_model=ProfileRecordResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    body: ProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReferenceProfileRecord:
    """Create a new DRAFT profile in the specified organization.
    Requires ENGINEER+ role in the target org. Customer profiles always start DRAFT.
    """
    _require_org_membership_at_least(
        org_id=body.org_id, user=user, db=db, minimum_role=OrgRole.ENGINEER
    )

    # Unique constraint: profile_code + version
    if db.scalar(
        select(ReferenceProfileRecord).where(
            ReferenceProfileRecord.profile_code == body.profile_code,
            ReferenceProfileRecord.org_id == body.org_id,
        )
    ):
        # Auto-increment version: find max version for this code in this org
        from sqlalchemy import func
        max_version = db.scalar(
            select(func.max(ReferenceProfileRecord.version)).where(
                ReferenceProfileRecord.profile_code == body.profile_code,
                ReferenceProfileRecord.org_id == body.org_id,
            )
        ) or 0
        new_version = max_version + 1
    else:
        new_version = 1

    now = datetime.now(timezone.utc)
    profile = ReferenceProfileRecord(
        profile_code=body.profile_code,
        version=new_version,
        org_id=body.org_id,
        display_name=body.display_name,
        material_scope=body.material_scope,
        stack_count=body.stack_count,
        cycle_basis_hz=body.cycle_basis_hz,
        t_min_mm=body.t_min_mm,
        t_max_mm=body.t_max_mm,
        status=ProfileStatus.DRAFT,
        is_system_default=False,  # customers cannot create system defaults (HR-05)
        parameter_bands=body.parameter_bands,
        nugget_criterion=body.nugget_criterion,
        source_provenance=body.source_provenance,
        created_by=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(profile)
    db.flush()

    event = ProfileApprovalEvent(
        profile_id=profile.id,
        event_type=ProfileApprovalEventType.CREATED,
        actor_user_id=user.id,
        event_at=now,
        note=f"Profile created by user {user.id}.",
    )
    db.add(event)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/{profile_id}", response_model=ProfileRecordResponse)
def patch_profile(
    profile_id: int,
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReferenceProfileRecord:
    """Update a DRAFT profile. Approved/Active/Revoked profiles are immutable (HR-09)."""
    profile = db.scalar(select(ReferenceProfileRecord).where(ReferenceProfileRecord.id == profile_id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ApiErrorCode.RESOURCE_NOT_FOUND,
                "message": "Reference profile not found.",
                "context": {"profile_id": profile_id},
            },
        )

    # System defaults are read-only (HR-06)
    if profile.is_system_default or profile.org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.IMMUTABLE_SYSTEM_PROFILE,
                "message": "The system default profile is read-only and cannot be modified.",
            },
        )

    # Immutable statuses (HR-09)
    if profile.status in _IMMUTABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": ApiErrorCode.RESOURCE_CONFLICT,
                "message": (
                    f"Profile with status '{profile.status}' is immutable. "
                    "Only DRAFT profiles may be modified."
                ),
                "context": {"profile_id": profile_id, "status": profile.status},
            },
        )

    _require_org_membership_at_least(
        org_id=profile.org_id, user=user, db=db, minimum_role=OrgRole.ENGINEER
    )

    if body.display_name is not None:
        profile.display_name = body.display_name
    if body.material_scope is not None:
        profile.material_scope = body.material_scope
    if body.t_min_mm is not None:
        profile.t_min_mm = body.t_min_mm
    if body.t_max_mm is not None:
        profile.t_max_mm = body.t_max_mm
    if body.parameter_bands is not None:
        profile.parameter_bands = body.parameter_bands
    if body.nugget_criterion is not None:
        profile.nugget_criterion = body.nugget_criterion
    if body.source_provenance is not None:
        profile.source_provenance = body.source_provenance

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/{profile_id}/approve", response_model=ProfileApprovalEventResponse)
def approve_profile(
    profile_id: int,
    body: ProfileApproveRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileApprovalEvent:
    """Approve a profile. Strict fail-closed prerequisites enforced (HR-08).

    Prerequisites (all must pass, else 422):
      1. Approver has APPROVER+ org role.
      2. Approver is not the profile creator (four-eyes).
      3. parameter_bands.bands is non-empty.
      4. nugget_criterion is non-empty dict.
      5. source_provenance.basis is non-empty string.
    """
    profile = db.scalar(select(ReferenceProfileRecord).where(ReferenceProfileRecord.id == profile_id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ApiErrorCode.RESOURCE_NOT_FOUND,
                "message": "Reference profile not found.",
                "context": {"profile_id": profile_id},
            },
        )

    # System defaults cannot be approved via this endpoint (HR-05/HR-06)
    if profile.is_system_default or profile.org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.IMMUTABLE_SYSTEM_PROFILE,
                "message": "The system default profile cannot be approved or modified.",
            },
        )

    # Status must be approvable
    if profile.status not in _APPROVABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": ApiErrorCode.RESOURCE_CONFLICT,
                "message": (
                    f"Profile status '{profile.status}' cannot transition to APPROVED. "
                    f"Must be one of {sorted(s.value for s in _APPROVABLE_STATUSES)}."
                ),
                "context": {"profile_id": profile_id, "current_status": profile.status},
            },
        )

    # APPROVER+ role required
    _require_org_membership_at_least(
        org_id=profile.org_id, user=user, db=db, minimum_role=OrgRole.APPROVER
    )

    # Four-eyes: approver cannot be creator (HR-08)
    if user.id == profile.created_by:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.SAME_USER_REVIEWER_APPROVER,
                "message": "The approver cannot be the same person who created the profile.",
                "context": {"profile_id": profile_id, "creator_id": profile.created_by},
            },
        )

    # Engineering prerequisites (HR-08 — fail-closed)
    _check_approval_prerequisites(profile)

    now = datetime.now(timezone.utc)
    profile.status = ProfileStatus.APPROVED
    profile.approver_user_id = user.id
    profile.approved_at = now
    profile.updated_at = now

    event = ProfileApprovalEvent(
        profile_id=profile.id,
        event_type=ProfileApprovalEventType.APPROVED,
        actor_user_id=user.id,
        event_at=now,
        note=body.note,
        field_confirmations=body.field_confirmations,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
