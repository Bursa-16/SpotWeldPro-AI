"""Engineering Library application service — governed writes.

CE-02C: thin service layer coordinating repository writes, content-hash
computation, and audit recording for all six engineering library aggregates.

Idempotency is intentionally deferred for CE-02C.
What IS preserved per governed pattern:
  - GovernedUnitOfWork transaction boundary
  - GovernedAuditService audit recording inside the transaction
  - Actor attribution on every write
  - Content hash computed before write and stored on revision
  - Transaction rollback on any unhandled exception (UoW __exit__)
  - DB/domain constraints fail closed on duplicates (no silent swallow)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from app.application.governed_audit_service import GovernedAuditService
from app.application.governed_unit_of_work import GovernedUnitOfWork
from app.domain.engineering_library_types import (
    CoatingRevisionDraft,
    ElectrodeRevisionDraft,
    EngineeringLibraryRevisionMetadata,
    MaterialRevisionDraft,
    StackUpRevisionDraft,
    WeldGunRevisionDraft,
    WeldScheduleRevisionDraft,
)
from app.models.engineering_library import (
    EngineeringCoating,
    EngineeringCoatingRevision,
    EngineeringElectrode,
    EngineeringElectrodeRevision,
    EngineeringMaterial,
    EngineeringMaterialRevision,
    EngineeringStackUp,
    EngineeringStackUpRevision,
    EngineeringWeldGun,
    EngineeringWeldGunRevision,
    EngineeringWeldPulse,
    EngineeringWeldSchedule,
    EngineeringWeldScheduleRevision,
)
from app.repositories.engineering_library_repository import (
    EngineeringLibraryRepository,
)

SOFTWARE_VERSION = "CE-02C"
SCHEMA_VERSION = "1"
CANONICALIZATION_VERSION = "1"
HASH_ALGORITHM = "sha256"

ACTOR_TYPE_USER = "user"


def _hash(value: object) -> str:
    """Canonical content hash — matches RuleRegistryService._hash()."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event_id() -> str:
    return str(uuid.uuid4())


def _correlation_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------


def _material_revision_canonical(draft: MaterialRevisionDraft) -> object:
    props = draft.properties
    return {
        "entity_type": "engineering_material",
        "revision_number": draft.metadata.revision_number,
        "lifecycle_status": draft.metadata.lifecycle_status.value,
        "source_class": draft.metadata.source_class.value,
        "supersedes_revision_id": draft.metadata.supersedes_revision_id,
        "family": draft.identity.family,
        "grade": draft.identity.grade,
        "form": draft.identity.form,
        "thickness_min_mm": draft.thickness_min_mm,
        "thickness_max_mm": draft.thickness_max_mm,
        "weldability_class": draft.weldability_class,
        "contact_resistance_class": draft.contact_resistance_class,
        "properties": {
            "electrical_resistivity_ohm_m": props.electrical_resistivity_ohm_m,
            "thermal_conductivity_w_mk": props.thermal_conductivity_w_mk,
            "specific_heat_j_kgk": props.specific_heat_j_kgk,
            "density_kg_m3": props.density_kg_m3,
            "solidus_c": props.solidus_c,
            "liquidus_c": props.liquidus_c,
            "yield_strength_mpa": props.yield_strength_mpa,
            "tensile_strength_mpa": props.tensile_strength_mpa,
            "hardness_hv": props.hardness_hv,
            "property_basis": props.property_basis.value,
            "resistivity_curve": [
                {"temperature_c": p.temperature_c, "value": p.value}
                for p in props.resistivity_curve
            ],
            "conductivity_curve": [
                {"temperature_c": p.temperature_c, "value": p.value}
                for p in props.conductivity_curve
            ],
            "specific_heat_curve": [
                {"temperature_c": p.temperature_c, "value": p.value}
                for p in props.specific_heat_curve
            ],
        },
        "evidence_reference_ids": sorted(draft.metadata.evidence_reference_ids),
        "notes": draft.notes,
    }


# ---------------------------------------------------------------------------
# Coating
# ---------------------------------------------------------------------------


def _coating_revision_canonical(draft: CoatingRevisionDraft) -> object:
    return {
        "entity_type": "engineering_coating",
        "revision_number": draft.metadata.revision_number,
        "lifecycle_status": draft.metadata.lifecycle_status.value,
        "source_class": draft.metadata.source_class.value,
        "supersedes_revision_id": draft.metadata.supersedes_revision_id,
        "family": draft.identity.family,
        "designation": draft.identity.designation,
        "nominal_thickness_um": draft.nominal_thickness_um,
        "electrical_contact_effect": draft.electrical_contact_effect,
        "electrode_wear_effect": draft.electrode_wear_effect,
        "evidence_reference_ids": sorted(draft.metadata.evidence_reference_ids),
        "notes": draft.notes,
    }


# ---------------------------------------------------------------------------
# Stack-Up
# ---------------------------------------------------------------------------


def _stack_up_revision_canonical(draft: StackUpRevisionDraft) -> object:
    return {
        "entity_type": "engineering_stack_up",
        "revision_number": draft.metadata.revision_number,
        "lifecycle_status": draft.metadata.lifecycle_status.value,
        "source_class": draft.metadata.source_class.value,
        "supersedes_revision_id": draft.metadata.supersedes_revision_id,
        "adhesive_present": draft.adhesive_present,
        "interface_notes": draft.interface_notes,
        "layers": [
            {
                "sequence": lyr.sequence,
                "material_revision_id": lyr.material_revision_id,
                "coating_revision_id": lyr.coating_revision_id,
                "thickness_mm": lyr.thickness_mm,
                "orientation": lyr.orientation,
            }
            for lyr in sorted(draft.layers, key=lambda ld: ld.sequence)
        ],
        "evidence_reference_ids": sorted(draft.metadata.evidence_reference_ids),
    }


# ---------------------------------------------------------------------------
# Electrode
# ---------------------------------------------------------------------------


def _electrode_revision_canonical(draft: ElectrodeRevisionDraft) -> object:
    cap = draft.cap_geometry
    return {
        "entity_type": "engineering_electrode",
        "revision_number": draft.metadata.revision_number,
        "lifecycle_status": draft.metadata.lifecycle_status.value,
        "source_class": draft.metadata.source_class.value,
        "supersedes_revision_id": draft.metadata.supersedes_revision_id,
        "face_geometry": cap.face_geometry.value,
        "face_diameter_mm": cap.face_diameter_mm,
        "tip_diameter_mm": cap.tip_diameter_mm,
        "radius_mm": cap.radius_mm,
        "included_angle_deg": cap.included_angle_deg,
        "material_designation": draft.material_designation,
        "cooling_channel_diameter_mm": draft.cooling_channel_diameter_mm,
        "recommended_flow_lpm": draft.recommended_flow_lpm,
        "recommended_max_inlet_temp_c": draft.recommended_max_inlet_temp_c,
        "evidence_reference_ids": sorted(draft.metadata.evidence_reference_ids),
        "notes": draft.notes,
    }


# ---------------------------------------------------------------------------
# Weld Gun
# ---------------------------------------------------------------------------


def _weld_gun_revision_canonical(draft: WeldGunRevisionDraft) -> object:
    transformer = None
    if draft.transformer is not None:
        t = draft.transformer
        transformer = {
            "transformer_id": t.transformer_id,
            "power_type": t.power_type.value,
            "rated_power_kva": t.rated_power_kva,
            "max_secondary_current_ka": t.max_secondary_current_ka,
            "nominal_frequency_hz": t.nominal_frequency_hz,
        }
    controller = None
    if draft.controller is not None:
        c = draft.controller
        controller = {
            "controller_id": c.controller_id,
            "manufacturer": c.manufacturer,
            "model": c.model,
            "supports_current_feedback": c.supports_current_feedback,
            "supports_voltage_feedback": c.supports_voltage_feedback,
            "supports_force_feedback": c.supports_force_feedback,
            "supports_displacement_feedback": c.supports_displacement_feedback,
        }
    cooling = None
    if draft.cooling is not None:
        cg = draft.cooling
        cooling = {
            "nominal_flow_lpm": cg.nominal_flow_lpm,
            "inlet_temperature_c": cg.inlet_temperature_c,
            "circuit_count": cg.circuit_count,
        }
    return {
        "entity_type": "engineering_weld_gun",
        "revision_number": draft.metadata.revision_number,
        "lifecycle_status": draft.metadata.lifecycle_status.value,
        "source_class": draft.metadata.source_class.value,
        "supersedes_revision_id": draft.metadata.supersedes_revision_id,
        "actuation_type": draft.actuation_type.value,
        "max_force_kn": draft.max_force_kn,
        "throat_depth_mm": draft.throat_depth_mm,
        "max_opening_mm": draft.max_opening_mm,
        "transformer": transformer,
        "controller": controller,
        "cooling": cooling,
        "evidence_reference_ids": sorted(draft.metadata.evidence_reference_ids),
        "notes": draft.notes,
    }


# ---------------------------------------------------------------------------
# Weld Schedule
# ---------------------------------------------------------------------------


def _weld_schedule_revision_canonical(draft: WeldScheduleRevisionDraft) -> object:
    return {
        "entity_type": "engineering_weld_schedule",
        "revision_number": draft.metadata.revision_number,
        "lifecycle_status": draft.metadata.lifecycle_status.value,
        "source_class": draft.metadata.source_class.value,
        "supersedes_revision_id": draft.metadata.supersedes_revision_id,
        "squeeze_cycles": draft.squeeze_cycles,
        "hold_cycles": draft.hold_cycles,
        "nominal_force_kn": draft.nominal_force_kn,
        "process_metadata": dict(draft.process_metadata),
        "pulses": [
            {
                "sequence": p.sequence,
                "pulse_type": p.pulse_type.value,
                "current_ka": p.current_ka,
                "duration_cycles": p.duration_cycles,
                "force_kn": p.force_kn,
            }
            for p in sorted(draft.pulses, key=lambda p: p.sequence)
        ],
        "evidence_reference_ids": sorted(draft.metadata.evidence_reference_ids),
    }


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class EngineeringLibraryService:
    """Governed writes for all six engineering library aggregates.

    All write methods require a GovernedUnitOfWork; the caller must call
    unit_of_work.commit() after the method returns successfully.
    The UoW auto-rolls back on unhandled exceptions.
    """

    def __init__(self, unit_of_work: GovernedUnitOfWork) -> None:
        self._uow = unit_of_work
        self._repo = EngineeringLibraryRepository(unit_of_work.session)
        self._audit = GovernedAuditService(unit_of_work)

    def _record(
        self,
        *,
        entity_type: str,
        entity_id: str,
        entity_revision: str,
        action: str,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
        correlation_id: str,
        content_hash: str,
        meta: EngineeringLibraryRevisionMetadata,
        created_at: datetime,
        prior_content_hash: str | None = None,
    ) -> None:
        self._audit.record_event(
            event_id=_event_id(),
            entity_type=entity_type,
            entity_id=entity_id,
            entity_revision=entity_revision,
            action=action,
            actor_id=actor_id,
            actor_type=ACTOR_TYPE_USER,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            schema_version=SCHEMA_VERSION,
            software_version=SOFTWARE_VERSION,
            canonicalization_version=CANONICALIZATION_VERSION,
            hash_algorithm=HASH_ALGORITHM,
            new_content_hash=content_hash,
            prior_content_hash=prior_content_hash,
            created_at=created_at,
        )

    # ---- Material ----

    def create_material_with_revision(
        self,
        *,
        draft: MaterialRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringMaterial, EngineeringMaterialRevision]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_material_revision_canonical(draft))
        identity = self._repo.create_material_identity(
            material_id=draft.identity.material_id,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        revision = self._repo.add_material_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_material",
            entity_id=draft.identity.material_id,
            entity_revision=str(draft.metadata.revision_number),
            action="create_identity_with_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return identity, revision

    def add_material_revision(
        self,
        *,
        entity_id: int,
        draft: MaterialRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> EngineeringMaterialRevision:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_material_revision_canonical(draft))
        revision = self._repo.add_material_revision(
            entity_id=entity_id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_material",
            entity_id=str(entity_id),
            entity_revision=str(draft.metadata.revision_number),
            action="add_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return revision

    # ---- Coating ----

    def create_coating_with_revision(
        self,
        *,
        draft: CoatingRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringCoating, EngineeringCoatingRevision]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_coating_revision_canonical(draft))
        identity = self._repo.create_coating_identity(
            coating_id=draft.identity.coating_id,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        revision = self._repo.add_coating_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_coating",
            entity_id=draft.identity.coating_id,
            entity_revision=str(draft.metadata.revision_number),
            action="create_identity_with_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return identity, revision

    def add_coating_revision(
        self,
        *,
        entity_id: int,
        draft: CoatingRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> EngineeringCoatingRevision:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_coating_revision_canonical(draft))
        revision = self._repo.add_coating_revision(
            entity_id=entity_id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_coating",
            entity_id=str(entity_id),
            entity_revision=str(draft.metadata.revision_number),
            action="add_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return revision

    # ---- Stack-Up ----

    def create_stack_up_with_revision(
        self,
        *,
        draft: StackUpRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringStackUp, EngineeringStackUpRevision]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_stack_up_revision_canonical(draft))
        identity = self._repo.create_stack_up_identity(
            stack_id=draft.stack_id,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        revision = self._repo.add_stack_up_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_stack_up",
            entity_id=draft.stack_id,
            entity_revision=str(draft.metadata.revision_number),
            action="create_identity_with_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return identity, revision

    def add_stack_up_revision(
        self,
        *,
        entity_id: int,
        draft: StackUpRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> EngineeringStackUpRevision:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_stack_up_revision_canonical(draft))
        revision = self._repo.add_stack_up_revision(
            entity_id=entity_id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_stack_up",
            entity_id=str(entity_id),
            entity_revision=str(draft.metadata.revision_number),
            action="add_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return revision

    # ---- Electrode ----

    def create_electrode_with_revision(
        self,
        *,
        draft: ElectrodeRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringElectrode, EngineeringElectrodeRevision]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_electrode_revision_canonical(draft))
        identity = self._repo.create_electrode_identity(
            electrode_id=draft.electrode_id,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        revision = self._repo.add_electrode_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_electrode",
            entity_id=draft.electrode_id,
            entity_revision=str(draft.metadata.revision_number),
            action="create_identity_with_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return identity, revision

    def add_electrode_revision(
        self,
        *,
        entity_id: int,
        draft: ElectrodeRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> EngineeringElectrodeRevision:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_electrode_revision_canonical(draft))
        revision = self._repo.add_electrode_revision(
            entity_id=entity_id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_electrode",
            entity_id=str(entity_id),
            entity_revision=str(draft.metadata.revision_number),
            action="add_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return revision

    # ---- Weld Gun ----

    def create_weld_gun_with_revision(
        self,
        *,
        draft: WeldGunRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringWeldGun, EngineeringWeldGunRevision]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_weld_gun_revision_canonical(draft))
        identity = self._repo.create_weld_gun_identity(
            gun_id=draft.gun_id,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        revision = self._repo.add_weld_gun_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_weld_gun",
            entity_id=draft.gun_id,
            entity_revision=str(draft.metadata.revision_number),
            action="create_identity_with_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return identity, revision

    def add_weld_gun_revision(
        self,
        *,
        entity_id: int,
        draft: WeldGunRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> EngineeringWeldGunRevision:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_weld_gun_revision_canonical(draft))
        revision = self._repo.add_weld_gun_revision(
            entity_id=entity_id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_weld_gun",
            entity_id=str(entity_id),
            entity_revision=str(draft.metadata.revision_number),
            action="add_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return revision

    # ---- Weld Schedule ----

    def create_weld_schedule_with_revision(
        self,
        *,
        draft: WeldScheduleRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringWeldSchedule, EngineeringWeldScheduleRevision, list[EngineeringWeldPulse]]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_weld_schedule_revision_canonical(draft))
        identity = self._repo.create_weld_schedule_identity(
            schedule_id=draft.schedule_id,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        revision, pulses = self._repo.add_weld_schedule_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_weld_schedule",
            entity_id=draft.schedule_id,
            entity_revision=str(draft.metadata.revision_number),
            action="create_identity_with_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return identity, revision, pulses

    def add_weld_schedule_revision(
        self,
        *,
        entity_id: int,
        draft: WeldScheduleRevisionDraft,
        actor_id: str,
        actor_user_id: int | None,
        reason: str,
    ) -> tuple[EngineeringWeldScheduleRevision, list[EngineeringWeldPulse]]:
        self._uow.ensure_open()
        correlation_id = _correlation_id()
        created_at = _now()
        content_hash = _hash(_weld_schedule_revision_canonical(draft))
        revision, pulses = self._repo.add_weld_schedule_revision(
            entity_id=entity_id,
            draft=draft,
            content_hash=content_hash,
            created_by_actor_id=actor_id,
            created_by_user_id=actor_user_id,
        )
        self._record(
            entity_type="engineering_weld_schedule",
            entity_id=str(entity_id),
            entity_revision=str(draft.metadata.revision_number),
            action="add_revision",
            actor_id=actor_id,
            actor_user_id=actor_user_id,
            reason=reason,
            correlation_id=correlation_id,
            content_hash=content_hash,
            meta=draft.metadata,
            created_at=created_at,
        )
        return revision, pulses
