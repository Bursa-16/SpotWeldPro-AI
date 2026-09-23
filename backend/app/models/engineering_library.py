"""Persistence foundation for governed engineering-library master data.

CE-02B1 scope:
- material identity + append-only revisions
- coating identity + append-only revisions
- stack-up identity + append-only revisions
- immutable stack layers pinned to exact material/coating revisions

No service/API authority is introduced here.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.domain.engineering_library_types import (
    EngineeringLibraryLifecycleStatus,
    EngineeringLibrarySourceClass,
)
from app.models.entities import utc_now
from app.models.governance import (
    ImmutableJSON,
    freeze_json_attribute,
    portable_enum,
    protect_immutable_model,
)


class EngineeringMaterial(Base):
    __tablename__ = "engineering_materials"
    __table_args__ = (
        UniqueConstraint(
            "material_id",
            name="uq_engineering_materials_material_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[str] = mapped_column(String(120))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringMaterialRevision(Base):
    __tablename__ = "engineering_material_revisions"
    __table_args__ = (
        UniqueConstraint(
            "engineering_material_id",
            "revision_number",
            name="uq_engineering_material_revisions_logical_revision",
        ),
        UniqueConstraint(
            "engineering_material_id",
            "id",
            name="uq_engineering_material_revisions_context_internal_id",
        ),
        UniqueConstraint(
            "supersedes_revision_id",
            name="uq_engineering_material_revisions_single_successor",
        ),
        ForeignKeyConstraint(
            ["engineering_material_id", "supersedes_revision_id"],
            [
                "engineering_material_revisions.engineering_material_id",
                "engineering_material_revisions.id",
            ],
            name="fk_engineering_material_revisions_same_material_supersession",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_engineering_material_revisions_positive_revision",
        ),
        CheckConstraint(
            "supersedes_revision_id IS NULL OR supersedes_revision_id != id",
            name="ck_engineering_material_revisions_not_self_superseding",
        ),
        CheckConstraint(
            "thickness_min_mm IS NULL OR thickness_min_mm > 0",
            name="ck_engineering_material_revisions_positive_min_thickness",
        ),
        CheckConstraint(
            "thickness_max_mm IS NULL OR thickness_max_mm > 0",
            name="ck_engineering_material_revisions_positive_max_thickness",
        ),
        CheckConstraint(
            "thickness_min_mm IS NULL OR thickness_max_mm IS NULL "
            "OR thickness_max_mm >= thickness_min_mm",
            name="ck_engineering_material_revisions_thickness_window",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_material_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_materials.id", ondelete="RESTRICT"),
        index=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    supersedes_revision_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    lifecycle_status: Mapped[EngineeringLibraryLifecycleStatus] = mapped_column(
        portable_enum(
            EngineeringLibraryLifecycleStatus,
            "ck_engineering_material_revisions_lifecycle_status",
        )
    )
    source_class: Mapped[EngineeringLibrarySourceClass] = mapped_column(
        portable_enum(
            EngineeringLibrarySourceClass,
            "ck_engineering_material_revisions_source_class",
        )
    )

    family: Mapped[str] = mapped_column(String(120))
    grade: Mapped[str] = mapped_column(String(160))
    form: Mapped[str | None] = mapped_column(String(120), nullable=True)

    thickness_min_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    thickness_max_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weldability_class: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    contact_resistance_class: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    properties_snapshot: Mapped[dict] = mapped_column(ImmutableJSON)
    evidence_reference_ids: Mapped[list[int]] = mapped_column(ImmutableJSON)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    schema_version: Mapped[str] = mapped_column(String(40))
    canonicalization_version: Mapped[str] = mapped_column(String(40))
    hash_algorithm: Mapped[str] = mapped_column(String(40))
    content_hash: Mapped[str] = mapped_column(String(128))
    software_version: Mapped[str] = mapped_column(String(80))

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringCoating(Base):
    __tablename__ = "engineering_coatings"
    __table_args__ = (
        UniqueConstraint(
            "coating_id",
            name="uq_engineering_coatings_coating_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coating_id: Mapped[str] = mapped_column(String(120))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringCoatingRevision(Base):
    __tablename__ = "engineering_coating_revisions"
    __table_args__ = (
        UniqueConstraint(
            "engineering_coating_id",
            "revision_number",
            name="uq_engineering_coating_revisions_logical_revision",
        ),
        UniqueConstraint(
            "engineering_coating_id",
            "id",
            name="uq_engineering_coating_revisions_context_internal_id",
        ),
        UniqueConstraint(
            "supersedes_revision_id",
            name="uq_engineering_coating_revisions_single_successor",
        ),
        ForeignKeyConstraint(
            ["engineering_coating_id", "supersedes_revision_id"],
            [
                "engineering_coating_revisions.engineering_coating_id",
                "engineering_coating_revisions.id",
            ],
            name="fk_engineering_coating_revisions_same_coating_supersession",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_engineering_coating_revisions_positive_revision",
        ),
        CheckConstraint(
            "supersedes_revision_id IS NULL OR supersedes_revision_id != id",
            name="ck_engineering_coating_revisions_not_self_superseding",
        ),
        CheckConstraint(
            "nominal_thickness_um IS NULL OR nominal_thickness_um > 0",
            name="ck_engineering_coating_revisions_positive_thickness",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_coating_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_coatings.id", ondelete="RESTRICT"),
        index=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    supersedes_revision_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    lifecycle_status: Mapped[EngineeringLibraryLifecycleStatus] = mapped_column(
        portable_enum(
            EngineeringLibraryLifecycleStatus,
            "ck_engineering_coating_revisions_lifecycle_status",
        )
    )
    source_class: Mapped[EngineeringLibrarySourceClass] = mapped_column(
        portable_enum(
            EngineeringLibrarySourceClass,
            "ck_engineering_coating_revisions_source_class",
        )
    )

    family: Mapped[str] = mapped_column(String(120))
    designation: Mapped[str] = mapped_column(String(160))
    nominal_thickness_um: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    electrical_contact_effect: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )
    electrode_wear_effect: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    evidence_reference_ids: Mapped[list[int]] = mapped_column(ImmutableJSON)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    schema_version: Mapped[str] = mapped_column(String(40))
    canonicalization_version: Mapped[str] = mapped_column(String(40))
    hash_algorithm: Mapped[str] = mapped_column(String(40))
    content_hash: Mapped[str] = mapped_column(String(128))
    software_version: Mapped[str] = mapped_column(String(80))

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringStackUp(Base):
    __tablename__ = "engineering_stack_ups"
    __table_args__ = (
        UniqueConstraint(
            "stack_id",
            name="uq_engineering_stack_ups_stack_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stack_id: Mapped[str] = mapped_column(String(120))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringStackUpRevision(Base):
    __tablename__ = "engineering_stack_up_revisions"
    __table_args__ = (
        UniqueConstraint(
            "engineering_stack_up_id",
            "revision_number",
            name="uq_engineering_stack_up_revisions_logical_revision",
        ),
        UniqueConstraint(
            "engineering_stack_up_id",
            "id",
            name="uq_engineering_stack_up_revisions_context_internal_id",
        ),
        UniqueConstraint(
            "supersedes_revision_id",
            name="uq_engineering_stack_up_revisions_single_successor",
        ),
        ForeignKeyConstraint(
            ["engineering_stack_up_id", "supersedes_revision_id"],
            [
                "engineering_stack_up_revisions.engineering_stack_up_id",
                "engineering_stack_up_revisions.id",
            ],
            name="fk_engineering_stack_up_revisions_same_stack_supersession",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_engineering_stack_up_revisions_positive_revision",
        ),
        CheckConstraint(
            "supersedes_revision_id IS NULL OR supersedes_revision_id != id",
            name="ck_engineering_stack_up_revisions_not_self_superseding",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_stack_up_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_stack_ups.id", ondelete="RESTRICT"),
        index=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    supersedes_revision_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    lifecycle_status: Mapped[EngineeringLibraryLifecycleStatus] = mapped_column(
        portable_enum(
            EngineeringLibraryLifecycleStatus,
            "ck_engineering_stack_up_revisions_lifecycle_status",
        )
    )
    source_class: Mapped[EngineeringLibrarySourceClass] = mapped_column(
        portable_enum(
            EngineeringLibrarySourceClass,
            "ck_engineering_stack_up_revisions_source_class",
        )
    )

    adhesive_present: Mapped[bool] = mapped_column(default=False)
    interface_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_reference_ids: Mapped[list[int]] = mapped_column(ImmutableJSON)

    schema_version: Mapped[str] = mapped_column(String(40))
    canonicalization_version: Mapped[str] = mapped_column(String(40))
    hash_algorithm: Mapped[str] = mapped_column(String(40))
    content_hash: Mapped[str] = mapped_column(String(128))
    software_version: Mapped[str] = mapped_column(String(80))

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringStackLayer(Base):
    __tablename__ = "engineering_stack_layers"
    __table_args__ = (
        UniqueConstraint(
            "stack_up_revision_id",
            "sequence",
            name="uq_engineering_stack_layers_revision_sequence",
        ),
        CheckConstraint(
            "sequence > 0",
            name="ck_engineering_stack_layers_positive_sequence",
        ),
        CheckConstraint(
            "thickness_mm > 0",
            name="ck_engineering_stack_layers_positive_thickness",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stack_up_revision_id: Mapped[int] = mapped_column(
        ForeignKey(
            "engineering_stack_up_revisions.id",
            ondelete="RESTRICT",
        ),
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer)

    material_revision_id: Mapped[int] = mapped_column(
        ForeignKey(
            "engineering_material_revisions.id",
            ondelete="RESTRICT",
        ),
        index=True,
    )
    coating_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "engineering_coating_revisions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    thickness_mm: Mapped[float] = mapped_column(Float)
    orientation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


freeze_json_attribute(EngineeringMaterialRevision.properties_snapshot)
freeze_json_attribute(EngineeringMaterialRevision.evidence_reference_ids)
freeze_json_attribute(EngineeringCoatingRevision.evidence_reference_ids)
freeze_json_attribute(EngineeringStackUpRevision.evidence_reference_ids)

protect_immutable_model(EngineeringMaterial)
protect_immutable_model(EngineeringMaterialRevision)
protect_immutable_model(EngineeringCoating)
protect_immutable_model(EngineeringCoatingRevision)
protect_immutable_model(EngineeringStackUp)
protect_immutable_model(EngineeringStackUpRevision)
protect_immutable_model(EngineeringStackLayer)
