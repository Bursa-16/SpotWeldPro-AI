"""Organization management endpoints — Phase 2A.

ACCESS POLICY:
  All endpoints require authenticated user (HTTPBearer JWT).
  Cross-organization enumeration is prevented:
    - List returns only orgs where the caller holds active membership.
    - Detail requires active membership.
    - Member operations require ORG_ADMIN or SYSTEM_ADMIN.
"""
from __future__ import annotations

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
from app.models.enums import OrgRole, UserRole
from app.models.error_codes import ApiErrorCode
from app.models.profile_entities import Organization, OrganizationMember
from app.models.role_policy import normalize_user_role
from app.schemas.profile import (
    MembershipCreate,
    MembershipResponse,
    OrganizationCreate,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Organization]:
    """Return organizations the caller belongs to.
    SYSTEM_ADMIN sees all active organizations.
    """
    normalized = normalize_user_role(user.role)
    if normalized == UserRole.SYSTEM_ADMIN:
        return list(db.scalars(select(Organization).where(Organization.is_active.is_(True))).all())

    memberships = db.scalars(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active.is_(True),
        )
    ).all()
    org_ids = [m.org_id for m in memberships]
    if not org_ids:
        return []
    return list(db.scalars(
        select(Organization).where(
            Organization.id.in_(org_ids),
            Organization.is_active.is_(True),
        )
    ).all())


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """Get org detail. Requires active membership (or SYSTEM_ADMIN)."""
    get_current_org_membership(org_id=org_id, user=user, db=db)
    org = db.scalar(select(Organization).where(Organization.id == org_id))
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ApiErrorCode.RESOURCE_NOT_FOUND,
                "message": "Organization not found.",
                "context": {"org_id": org_id},
            },
        )
    return org


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    body: OrganizationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """Create an organization. SYSTEM_ADMIN only."""
    if normalize_user_role(user.role) != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.PERMISSION_DENIED,
                "message": "Only SYSTEM_ADMIN can create organizations.",
            },
        )
    if db.scalar(select(Organization).where(Organization.slug == body.slug)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": ApiErrorCode.RESOURCE_CONFLICT,
                "message": f"Organization slug '{body.slug}' already exists.",
                "context": {"slug": body.slug},
            },
        )
    org = Organization(slug=body.slug, display_name=body.display_name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}/members", response_model=list[MembershipResponse])
def list_members(
    org_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrganizationMember]:
    """List org members. Any active member may call this."""
    get_current_org_membership(org_id=org_id, user=user, db=db)
    return list(db.scalars(
        select(OrganizationMember).where(OrganizationMember.org_id == org_id)
    ).all())


@router.post(
    "/{org_id}/members",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    org_id: int,
    body: MembershipCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    """Add a member. Requires ORG_ADMIN or SYSTEM_ADMIN."""
    membership = get_current_org_membership(org_id=org_id, user=user, db=db)

    normalized = normalize_user_role(user.role)
    if normalized != UserRole.SYSTEM_ADMIN:
        if _ORG_ROLE_RANK.get(membership.org_role, 0) < _ORG_ROLE_RANK[OrgRole.ORG_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": ApiErrorCode.PERMISSION_DENIED,
                    "message": "ORG_ADMIN role required to add members.",
                },
            )

    valid_roles = {r.value for r in OrgRole}
    if body.org_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": ApiErrorCode.INVALID_REQUEST,
                "message": f"Invalid org_role. Must be one of {sorted(valid_roles)}.",
                "context": {"received": body.org_role},
            },
        )

    target_user = db.scalar(select(User).where(User.id == body.user_id))
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ApiErrorCode.RESOURCE_NOT_FOUND,
                "message": "Target user not found.",
                "context": {"user_id": body.user_id},
            },
        )

    if db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == body.user_id,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": ApiErrorCode.RESOURCE_CONFLICT,
                "message": "User is already a member of this organization.",
                "context": {"user_id": body.user_id, "org_id": org_id},
            },
        )

    new_member = OrganizationMember(
        org_id=org_id,
        user_id=body.user_id,
        org_role=body.org_role,
        is_active=True,
        granted_by=user.id,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member
