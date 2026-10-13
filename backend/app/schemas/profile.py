"""Pydantic I/O schemas for Organization and Reference Profile endpoints."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OrganizationCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$")
    display_name: str = Field(min_length=2, max_length=200)


class OrganizationResponse(BaseModel):
    id: int
    slug: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipCreate(BaseModel):
    user_id: int
    org_role: str = "VIEWER"


class MembershipResponse(BaseModel):
    id: int
    org_id: int
    user_id: int
    org_role: str
    is_active: bool
    granted_by: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileRecordResponse(BaseModel):
    id: int
    profile_code: str
    version: int
    org_id: Optional[int]
    display_name: str
    material_scope: str
    stack_count: str
    cycle_basis_hz: int
    t_min_mm: float
    t_max_mm: float
    status: str
    is_system_default: bool
    parameter_bands: dict
    nugget_criterion: dict
    source_provenance: dict
    approved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileSummaryResponse(BaseModel):
    """Lightweight profile descriptor for ComboBox population (Phase 3)."""
    id: int
    profile_code: str
    version: int
    display_name: str
    material_scope: str
    stack_count: str
    status: str
    is_system_default: bool
    approved_at: Optional[datetime]
    org_id: Optional[int]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Phase 2A — write schemas
# ---------------------------------------------------------------------------

class ProfileCreate(BaseModel):
    org_id: int
    profile_code: str = Field(min_length=2, max_length=80)
    display_name: str = Field(min_length=2, max_length=200)
    material_scope: str = Field(min_length=2, max_length=200)
    stack_count: str
    cycle_basis_hz: int = Field(ge=1, le=1000)
    t_min_mm: float = Field(gt=0, le=10)
    t_max_mm: float = Field(gt=0, le=20)
    parameter_bands: dict = Field(default_factory=dict)
    nugget_criterion: dict = Field(default_factory=dict)
    source_provenance: dict = Field(default_factory=dict)

    @field_validator("profile_code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        if not re.match(r"^[A-Z0-9][A-Z0-9_]*$", v):
            raise ValueError("profile_code must be uppercase alphanumeric (underscores allowed, no leading underscore)")
        return v

    @field_validator("stack_count")
    @classmethod
    def _validate_stack_count(cls, v: str) -> str:
        if v not in ("2T", "3T"):
            raise ValueError("stack_count must be 2T or 3T (4T is OUT OF PRODUCT SCOPE — HR-16)")
        return v

    @model_validator(mode="after")
    def _t_range(self) -> "ProfileCreate":
        if self.t_min_mm >= self.t_max_mm:
            raise ValueError("t_min_mm must be less than t_max_mm")
        return self


class ProfilePatch(BaseModel):
    """Mutable fields. Only applicable to DRAFT profiles (HR-09)."""
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    material_scope: Optional[str] = Field(None, min_length=2, max_length=200)
    t_min_mm: Optional[float] = Field(None, gt=0, le=10)
    t_max_mm: Optional[float] = Field(None, gt=0, le=20)
    parameter_bands: Optional[dict] = None
    nugget_criterion: Optional[dict] = None
    source_provenance: Optional[dict] = None


class ProfileApproveRequest(BaseModel):
    note: str = Field(default="", max_length=2000)
    field_confirmations: Optional[dict] = None


class ProfileApprovalEventResponse(BaseModel):
    id: int
    profile_id: int
    event_type: str
    actor_user_id: int
    event_at: datetime
    note: str
    field_confirmations: Optional[dict]

    model_config = {"from_attributes": True}
