
from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    # Authentication identifier is username (canonical: stripped, lowercase).
    # Password min_length not enforced here — wrong credentials return 401,
    # never a validation error that reveals password policy.
    username: str = Field(min_length=1, max_length=100, strip_whitespace=True)
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    # Both username (auth identity) and email (contact/notification/recovery)
    # are required when creating a user. See AUTH-UX-03.
    username: str = Field(min_length=1, max_length=100, strip_whitespace=True)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=8)
    role: str = UserRole.READ_ONLY


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
