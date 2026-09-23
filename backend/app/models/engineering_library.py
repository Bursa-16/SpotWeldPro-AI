"""Persistence foundation for governed engineering-library master data.

CE-02B1 scope:
- material identity + append-only revisions
- coating identity + append-only revisions
- stack-up identity + append-only revisions
- immutable stack layers pinned to exact material/coating revisions

CE-02B2 scope:
- electrode identity + append-only revisions
- weld gun identity + append-only revisions
- weld schedule identity + append-only revisions
- ordered weld pulses pinned to exact schedule revisions

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
    ElectrodeFaceGeometry,
    EngineeringLibraryLifecycleStatus,
    EngineeringLibrarySourceClass,
    GunActuationType,
    WeldPulseType,
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


# ---------------------------------------------------------------------------
# CE-02B2 — Electrode + WeldGun + WeldSchedule Persistence
# ---------------------------------------------------------------------------


class EngineeringElectrode(Base):
    __tablename__ = "engineering_electrodes"
    __table_args__ = (
        UniqueConstraint(
            "electrode_id",
            name="uq_engineering_electrodes_electrode_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    electrode_id: Mapped[str] = mapped_column(String(120))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringElectrodeRevision(Base):
    __tablename__ = "engineering_electrode_revisions"
    __table_args__ = (
        UniqueConstraint(
            "engineering_electrode_id",
            "revision_number",
            name="uq_engineering_electrode_revisions_logical_revision",
        ),
        UniqueConstraint(
            "engineering_electrode_id",
            "id",
            name="uq_engineering_electrode_revisions_context_internal_id",
        ),
        UniqueConstraint(
            "supersedes_revision_id",
            name="uq_engineering_electrode_revisions_single_successor",
        ),
        ForeignKeyConstraint(
            ["engineering_electrode_id", "supersedes_revision_id"],
            [
                "engineering_electrode_revisions.engineering_electrode_id",
                "engineering_electrode_revisions.id",
            ],
            name="fk_engineering_electrode_revisions_same_electrode_supersession",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_engineering_electrode_revisions_positive_revision",
        ),
        CheckConstraint(
            "supersedes_revision_id IS NULL OR supersedes_revision_id != id",
            name="ck_engineering_electrode_revisions_not_self_superseding",
        ),
        CheckConstraint(
            "face_diameter_mm > 0",
            name="ck_engineering_electrode_revisions_positive_face_diameter",
        ),
        CheckConstraint(
            "tip_diameter_mm IS NULL OR tip_diameter_mm > 0",
            name="ck_engineering_electrode_revisions_positive_tip_diameter",
        ),
        CheckConstraint(
            "radius_mm IS NULL OR radius_mm > 0",
            name="ck_engineering_electrode_revisions_positive_radius",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_electrode_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_electrodes.id", ondelete="RESTRICT"),
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
            "ck_engineering_electrode_revisions_lifecycle_status",
        )
    )
    source_class: Mapped[EngineeringLibrarySourceClass] = mapped_column(
        portable_enum(
            EngineeringLibrarySourceClass,
            "ck_engineering_electrode_revisions_source_class",
        )
    )

    face_geometry: Mapped[ElectrodeFaceGeometry] = mapped_column(
        portable_enum(
            ElectrodeFaceGeometry,
            "ck_engineering_electrode_revisions_face_geometry",
        )
    )
    face_diameter_mm: Mapped[float] = mapped_column(Float)
    tip_diameter_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    included_angle_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    material_designation: Mapped[str] = mapped_column(String(120))
    cooling_channel_diameter_mm: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    recommended_flow_lpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_max_inlet_temp_c: Mapped[float | None] = mapped_column(
        Float, nullable=True
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


class EngineeringWeldGun(Base):
    __tablename__ = "engineering_weld_guns"
    __table_args__ = (
        UniqueConstraint(
            "gun_id",
            name="uq_engineering_weld_guns_gun_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gun_id: Mapped[str] = mapped_column(String(120))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringWeldGunRevision(Base):
    __tablename__ = "engineering_weld_gun_revisions"
    __table_args__ = (
        UniqueConstraint(
            "engineering_weld_gun_id",
            "revision_number",
            name="uq_engineering_weld_gun_revisions_logical_revision",
        ),
        UniqueConstraint(
            "engineering_weld_gun_id",
            "id",
            name="uq_engineering_weld_gun_revisions_context_internal_id",
        ),
        UniqueConstraint(
            "supersedes_revision_id",
            name="uq_engineering_weld_gun_revisions_single_successor",
        ),
        ForeignKeyConstraint(
            ["engineering_weld_gun_id", "supersedes_revision_id"],
            [
                "engineering_weld_gun_revisions.engineering_weld_gun_id",
                "engineering_weld_gun_revisions.id",
            ],
            name="fk_engineering_weld_gun_revisions_same_gun_supersession",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_engineering_weld_gun_revisions_positive_revision",
        ),
        CheckConstraint(
            "supersedes_revision_id IS NULL OR supersedes_revision_id != id",
            name="ck_engineering_weld_gun_revisions_not_self_superseding",
        ),
        CheckConstraint(
            "max_force_kn > 0",
            name="ck_engineering_weld_gun_revisions_positive_max_force",
        ),
        CheckConstraint(
            "throat_depth_mm IS NULL OR throat_depth_mm > 0",
            name="ck_engineering_weld_gun_revisions_positive_throat_depth",
        ),
        CheckConstraint(
            "max_opening_mm IS NULL OR max_opening_mm > 0",
            name="ck_engineering_weld_gun_revisions_positive_max_opening",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_weld_gun_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_weld_guns.id", ondelete="RESTRICT"),
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
            "ck_engineering_weld_gun_revisions_lifecycle_status",
        )
    )
    source_class: Mapped[EngineeringLibrarySourceClass] = mapped_column(
        portable_enum(
            EngineeringLibrarySourceClass,
            "ck_engineering_weld_gun_revisions_source_class",
        )
    )

    actuation_type: Mapped[GunActuationType] = mapped_column(
        portable_enum(
            GunActuationType,
            "ck_engineering_weld_gun_revisions_actuation_type",
        )
    )
    max_force_kn: Mapped[float] = mapped_column(Float)
    throat_depth_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_opening_mm: Mapped[float | None] = mapped_column(Float, nullable=True)

    transformer_snapshot: Mapped[dict | None] = mapped_column(
        ImmutableJSON, nullable=True
    )
    controller_snapshot: Mapped[dict | None] = mapped_column(
        ImmutableJSON, nullable=True
    )
    cooling_snapshot: Mapped[dict | None] = mapped_column(
        ImmutableJSON, nullable=True
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


class EngineeringWeldSchedule(Base):
    __tablename__ = "engineering_weld_schedules"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            name="uq_engineering_weld_schedules_schedule_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_id: Mapped[str] = mapped_column(String(120))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_actor_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EngineeringWeldScheduleRevision(Base):
    __tablename__ = "engineering_weld_schedule_revisions"
    __table_args__ = (
        UniqueConstraint(
            "engineering_weld_schedule_id",
            "revision_number",
            name="uq_engineering_weld_schedule_revisions_logical_revision",
        ),
        UniqueConstraint(
            "engineering_weld_schedule_id",
            "id",
            name="uq_engineering_weld_schedule_revisions_context_internal_id",
        ),
        UniqueConstraint(
            "supersedes_revision_id",
            name="uq_engineering_weld_schedule_revisions_single_successor",
        ),
        ForeignKeyConstraint(
            ["engineering_weld_schedule_id", "supersedes_revision_id"],
            [
                "engineering_weld_schedule_revisions.engineering_weld_schedule_id",
                "engineering_weld_schedule_revisions.id",
            ],
            name="fk_engineering_weld_schedule_revisions_same_schedule_supersession",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="ck_engineering_weld_schedule_revisions_positive_revision",
        ),
        CheckConstraint(
            "supersedes_revision_id IS NULL OR supersedes_revision_id != id",
            name="ck_engineering_weld_schedule_revisions_not_self_superseding",
        ),
        CheckConstraint(
            "squeeze_cycles >= 0",
            name="ck_engineering_weld_schedule_revisions_non_negative_squeeze",
        ),
        CheckConstraint(
            "hold_cycles >= 0",
            name="ck_engineering_weld_schedule_revisions_non_negative_hold",
        ),
        CheckConstraint(
            "nominal_force_kn IS NULL OR nominal_force_kn > 0",
            name="ck_engineering_weld_schedule_revisions_positive_nominal_force",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_weld_schedule_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_weld_schedules.id", ondelete="RESTRICT"),
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
            "ck_engineering_weld_schedule_revisions_lifecycle_status",
        )
    )
    source_class: Mapped[EngineeringLibrarySourceClass] = mapped_column(
        portable_enum(
            EngineeringLibrarySourceClass,
            "ck_engineering_weld_schedule_revisions_source_class",
        )
    )

    squeeze_cycles: Mapped[float] = mapped_column(Float)
    hold_cycles: Mapped[float] = mapped_column(Float)
    nominal_force_kn: Mapped[float | None] = mapped_column(Float, nullable=True)
    process_metadata: Mapped[dict | None] = mapped_column(ImmutableJSON, nullable=True)

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


class EngineeringWeldPulse(Base):
    __tablename__ = "engineering_weld_pulses"
    __table_args__ = (
        UniqueConstraint(
            "engineering_weld_schedule_revision_id",
            "sequence_number",
            name="uq_engineering_weld_pulses_revision_sequence",
        ),
        CheckConstraint(
            "sequence_number > 0",
            name="ck_engineering_weld_pulses_positive_sequence_number",
        ),
        CheckConstraint(
            "duration_cycles >= 0",
            name="ck_engineering_weld_pulses_non_negative_duration",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engineering_weld_schedule_revision_id: Mapped[int] = mapped_column(
        ForeignKey(
            "engineering_weld_schedule_revisions.id",
            ondelete="RESTRICT",
        ),
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    pulse_type: Mapped[WeldPulseType] = mapped_column(
        portable_enum(
            WeldPulseType,
            "ck_engineering_weld_pulses_pulse_type",
        )
    )
    current_ka: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_cycles: Mapped[float] = mapped_column(Float)
    force_kn: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


# ---------------------------------------------------------------------------
# CE-02B1 governance wiring
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# CE-02B2 governance wiring
# ---------------------------------------------------------------------------

freeze_json_attribute(EngineeringElectrodeRevision.evidence_reference_ids)
freeze_json_attribute(EngineeringWeldGunRevision.transformer_snapshot)
freeze_json_attribute(EngineeringWeldGunRevision.controller_snapshot)
freeze_json_attribute(EngineeringWeldGunRevision.cooling_snapshot)
freeze_json_attribute(EngineeringWeldGunRevision.evidence_reference_ids)
freeze_json_attribute(EngineeringWeldScheduleRevision.process_metadata)
freeze_json_attribute(EngineeringWeldScheduleRevision.evidence_reference_ids)

protect_immutable_model(EngineeringElectrode)
protect_immutable_model(EngineeringElectrodeRevision)
protect_immutable_model(EngineeringWeldGun)
protect_immutable_model(EngineeringWeldGunRevision)
protect_immutable_model(EngineeringWeldSchedule)
protect_immutable_model(EngineeringWeldScheduleRevision)
protect_immutable_model(EngineeringWeldPulse)
