"""Organization and Reference Profile persistence models — Phase 1 foundation."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.entities import User, utc_now
from app.models.governance import ImmutableJSON, protect_immutable_model

SYSTEM_ORG_SLUG: str = "system"


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    members: Mapped[list[OrganizationMember]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    profiles: Mapped[list[ReferenceProfileRecord]] = relationship(
        back_populates="organization", foreign_keys="ReferenceProfileRecord.org_id"
    )


class OrganizationMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_org_members_org_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    org_role: Mapped[str] = mapped_column(String(40))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    granted_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="members")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class ReferenceProfileDocument(Base):
    __tablename__ = "ref_profile_documents"
    __table_args__ = (
        UniqueConstraint("upload_id", name="uq_ref_profile_documents_upload_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    upload_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    filename_original: Mapped[str] = mapped_column(String(300))
    file_format: Mapped[str] = mapped_column(String(10))
    file_sha256: Mapped[str] = mapped_column(String(64))
    file_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    extraction_status: Mapped[str] = mapped_column(String(40), default="PENDING")
    extraction_result: Mapped[Optional[dict]] = mapped_column(ImmutableJSON, nullable=True)


class ReferenceProfileRecord(Base):
    """Versioned reference profile owned by an organization (or system for Default)."""
    __tablename__ = "reference_profiles"
    __table_args__ = (
        UniqueConstraint(
            "profile_code", "version",
            name="uq_reference_profiles_code_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_code: Mapped[str] = mapped_column(String(80), index=True)
    version: Mapped[int] = mapped_column(Integer)
    # org_id IS NULL → system Default profile (HR-04)
    # org_id IS NOT NULL → organization-owned profile (HR-05)
    org_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=True, index=True,
    )
    display_name: Mapped[str] = mapped_column(String(200))
    material_scope: Mapped[str] = mapped_column(String(200))
    stack_count: Mapped[str] = mapped_column(String(10))
    cycle_basis_hz: Mapped[int] = mapped_column(Integer)
    t_min_mm: Mapped[float] = mapped_column(Float)
    t_max_mm: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(40), index=True)
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Immutable once written (ImmutableJSON prevents in-memory dict mutation)
    parameter_bands: Mapped[dict] = mapped_column(ImmutableJSON)
    nugget_criterion: Mapped[dict] = mapped_column(ImmutableJSON)
    source_provenance: Mapped[dict] = mapped_column(ImmutableJSON)

    source_document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ref_profile_documents.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    reviewer_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    approver_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deprecation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    organization: Mapped[Optional[Organization]] = relationship(
        back_populates="profiles", foreign_keys=[org_id]
    )
    approval_events: Mapped[list[ProfileApprovalEvent]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class ProfileApprovalEvent(Base):
    """Append-only audit record for profile lifecycle transitions."""
    __tablename__ = "profile_approval_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("reference_profiles.id", ondelete="RESTRICT"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(60))
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    note: Mapped[str] = mapped_column(Text, default="")
    field_confirmations: Mapped[Optional[dict]] = mapped_column(ImmutableJSON, nullable=True)

    profile: Mapped[ReferenceProfileRecord] = relationship(back_populates="approval_events")


# Enforce append-only semantics: no UPDATE or DELETE on approval events (HR-11)
protect_immutable_model(ProfileApprovalEvent)
