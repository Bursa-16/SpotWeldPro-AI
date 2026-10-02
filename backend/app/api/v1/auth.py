
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_permission
from app.application.audit_service import write_audit
from app.core.security import (
    canonicalize_username, create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password,
)
from app.db.session import get_db
from app.models.entities import User
from app.models.role_policy import canonicalize_role
from app.schemas.auth import (
    LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # AUTH-UX-03: authenticate by canonical username (stripped + lowercase).
    # JWT subject remains user.email — see AUTH-UX-03B for migration to user.id.
    canonical = canonicalize_username(payload.username)
    user = db.scalar(select(User).where(User.username == canonical))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    write_audit(db, user, "LOGIN", "User", str(user.id), {"email": user.email})
    return TokenResponse(
        # JWT sub = user.email (stable, backward-compatible; see AUTH-UX-03B).
        access_token=create_access_token(user.email),
        refresh_token=create_refresh_token(user.email),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        email = decode_token(payload.refresh_token, "refresh")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    return TokenResponse(
        access_token=create_access_token(user.email),
        refresh_token=create_refresh_token(user.email),
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    canonical_username = canonicalize_username(payload.username)

    # Check username uniqueness first
    if db.scalar(select(User).where(User.username == canonical_username)):
        raise HTTPException(status_code=409, detail="Username already exists")

    # Check email uniqueness
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already exists")

    try:
        canonical_role = canonicalize_role(payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    user = User(
        username=canonical_username,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=canonical_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, admin, "CREATE", "User", str(user.id), {"email": user.email, "role": user.role})
    return user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    return list(db.scalars(select(User).order_by(User.full_name)).all())
