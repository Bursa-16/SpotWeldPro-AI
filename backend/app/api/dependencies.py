
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import UserRole
from app.models.role_policy import normalize_user_role

bearer = HTTPBearer(auto_error=True)

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
    credentials: HTTPAuthorizationCredentials = Depends(bearer),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    try:
        email = decode_token(credentials.credentials, "access")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
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
