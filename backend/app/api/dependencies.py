
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import OrgRole, UserRole
from app.models.error_codes import ApiErrorCode
from app.models.role_policy import normalize_user_role

bearer = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    UserRole.SYSTEM_ADMIN:           {"*"},
    UserRole.PROCESS_ENGINEER:       {"project:read", "project:write", "weld:read", "weld:write", "approval:read", "test:read"},
    UserRole.QUALITY_ENGINEER:       {"project:read", "weld:read", "approval:read", "approval:write", "test:read", "test:write"},
    UserRole.MANUFACTURING_ENGINEER: {"project:read", "weld:read", "weld:write", "test:read"},
    UserRole.MAINTENANCE:            {"project:read", "weld:read", "test:read"},
    UserRole.OPERATOR:               {"project:read", "weld:read", "test:read"},
    UserRole.READ_ONLY:              {"project:read", "weld:read", "approval:read", "test:read"},
    UserRole.CUSTOMER:               {"project:read", "weld:read", "approval:read", "test:read"},
}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": ApiErrorCode.INVALID_TOKEN, "message": "Authentication required.", "context": None},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        email = decode_token(credentials.credentials, "access")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": ApiErrorCode.INVALID_TOKEN, "message": "Invalid or expired token.", "context": None},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": ApiErrorCode.INVALID_TOKEN, "message": "User not found or inactive.", "context": None},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_governed_actor_user(user: User = Depends(get_current_user)) -> User:  # noqa: B008
    """Return the authenticated durable human actor identity.

    Governed API slices must not trust client-supplied actor identity or role
    claims as authority. The authenticated durable ``User`` row is the only
    actor identity source here.
    """

    return user


def require_permission(permission: str):
    def dependency(user: User = Depends(get_current_user)) -> User:  # noqa: B008
        normalized = normalize_user_role(user.role)
        permissions = ROLE_PERMISSIONS.get(normalized, set())
        if "*" not in permissions and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return user
    return dependency


_ORG_ROLE_RANK: dict[str, int] = {
    OrgRole.VIEWER:    1,
    OrgRole.ENGINEER:  2,
    OrgRole.APPROVER:  3,
    OrgRole.ORG_ADMIN: 4,
}


def get_current_org_membership(
    org_id: int,
    user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Return the authenticated user's active OrganizationMember row for org_id.

    SYSTEM_ADMIN bypasses membership for platform-wide audit/admin access.
    Returns the membership object or raises 403.
    """
    from app.models.profile_entities import OrganizationMember

    normalized = normalize_user_role(user.role)
    if normalized == UserRole.SYSTEM_ADMIN:
        # System admins can access any org for audit; return a synthetic sentinel.
        return _SystemAdminOrgContext(user_id=user.id, org_id=org_id)

    member = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active.is_(True),
        )
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.ORG_MEMBERSHIP_REQUIRED,
                "message": "No active membership in this organization.",
                "context": {"org_id": org_id},
            },
        )
    return member


class _SystemAdminOrgContext:
    """Sentinel returned by get_current_org_membership for SYSTEM_ADMIN users."""

    def __init__(self, user_id: int, org_id: int) -> None:
        self.user_id = user_id
        self.org_id = org_id
        self.org_role = OrgRole.ORG_ADMIN
        self.is_active = True


def require_org_role(minimum_org_role: OrgRole):
    """Factory: combined system-role + org-role guard.

    The returned dependency checks that the resolved membership has at least
    minimum_org_role. Use after get_current_org_membership to add a minimum
    org-role requirement.
    """
    min_rank = _ORG_ROLE_RANK.get(minimum_org_role, 0)

    def dependency(membership=Depends(get_current_org_membership)) -> object:  # noqa: B008
        actual_rank = _ORG_ROLE_RANK.get(membership.org_role, 0)
        if actual_rank < min_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": ApiErrorCode.PERMISSION_DENIED,
                    "message": f"Org role {minimum_org_role} or higher required.",
                    "context": {"required": minimum_org_role, "actual": membership.org_role},
                },
            )
        return membership

    return dependency


# ---------------------------------------------------------------------------
# Profile access guard — Phase 2 prerequisite
# ---------------------------------------------------------------------------

def verify_profile_for_user(
    profile_id: int,
    user: User,
    db: Session,
):
    """Verify that `user` may use `profile_id` for an authenticated analysis.

    Checks (fail-closed on any failure — HR-16):
      1. Profile exists in the database.
      2. Profile status is APPROVED or ACTIVE (HR-06: DRAFT ≠ engineering approved).
      3. Profile is the system default (org_id IS NULL, accessible to all
         authenticated users) OR the user holds an active membership in the
         profile's organization.

    Returns the ReferenceProfileRecord on success.
    Raises HTTPException(403/404) on any check failure.

    DEFERRED: No route currently calls this guard. It is implemented here so
    that Phase 2 profile-selection routes can import and use it without adding
    new security logic at route definition time.
    """
    from app.models.enums import ProfileStatus
    from app.models.profile_entities import ReferenceProfileRecord

    profile = db.scalar(
        select(ReferenceProfileRecord).where(ReferenceProfileRecord.id == profile_id)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ApiErrorCode.RESOURCE_NOT_FOUND,
                "message": "Reference profile not found.",
                "context": {"profile_id": profile_id},
            },
        )

    # HR-06: DRAFT, REVIEW_REQUIRED, VALIDATED are not engineering-approved.
    _USABLE_STATUSES = {ProfileStatus.APPROVED, ProfileStatus.ACTIVE}
    if profile.status not in _USABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": ApiErrorCode.PROFILE_NOT_APPROVED,
                "message": (
                    f"Profile '{profile.profile_code}' v{profile.version} "
                    f"has status '{profile.status}' and is not available for use. "
                    "Only APPROVED or ACTIVE profiles may be used."
                ),
                "context": {
                    "profile_id": profile_id,
                    "status": profile.status,
                },
            },
        )

    # System-default profiles (org_id IS NULL) are accessible to all
    # authenticated users regardless of organization membership.
    if profile.org_id is None:
        return profile

    # Organization-owned profiles: verify active membership.
    # get_current_org_membership raises 403 if not a member — fail-closed.
    get_current_org_membership(org_id=profile.org_id, user=user, db=db)
    return profile
