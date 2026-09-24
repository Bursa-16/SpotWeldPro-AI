"""Engineering Library repository — append-only governed persistence.

CE-02C: repository layer for all six engineering library aggregates.

Transaction ownership always remains with the caller (GovernedUnitOfWork).
This repository adds and flushes records; it never commits or rolls back.

Current-revision resolver policy (CE-02C):
  Eligible = ACTIVE lifecycle_status AND not the target of any supersedes_revision_id
  within the same identity.
  - zero eligible → None (explicit no-current result)
  - one eligible  → return it
  - multiple      → AmbiguousCurrentRevisionError (fail closed)

  This is the CE-02C resolver policy, not a complete lifecycle-governance
  definition. No lifecycle transition engine is implemented at this stage.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.domain.engineering_library_types import (
    CoatingRevisionDraft,
    ElectrodeRevisionDraft,
    EngineeringLibraryLifecycleStatus,
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
    EngineeringStackLayer,
    EngineeringStackUp,
    EngineeringStackUpRevision,
    EngineeringWeldGun,
    EngineeringWeldGunRevision,
    EngineeringWeldPulse,
    EngineeringWeldSchedule,
    EngineeringWeldScheduleRevision,
)


class AmbiguousCurrentRevisionError(RuntimeError):
    """Multiple eligible ACTIVE revisions found for one identity (fail closed)."""


class CrossIdentitySupersessionError(ValueError):
    """Supersession revision belongs to a different identity (reject)."""


class EngineeringLibraryRepository:
    """Append-only governed persistence for all six engineering library aggregates.

    Public methods are aggregate-specific and explicit.
    Common internal helpers are shared but never hide aggregate-specific validation.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # -------------------------------------------------------------------------
    # Internal shared helpers
    # -------------------------------------------------------------------------

    def _resolve_current_revision(
        self,
        model_class: type,
        entity_id_attr: InstrumentedAttribute,
        entity_id: int,
    ) -> object | None:
        """CE-02C resolver: exactly one ACTIVE + unsuperseded revision.

        Never uses revision_number as a tiebreaker.
        Fails closed on ambiguity.
        """
        superseded_subq = (
            select(model_class.supersedes_revision_id)
            .where(
                entity_id_attr == entity_id,
                model_class.supersedes_revision_id.is_not(None),
            )
            .scalar_subquery()
        )
        stmt = select(model_class).where(
            entity_id_attr == entity_id,
            model_class.lifecycle_status == EngineeringLibraryLifecycleStatus.ACTIVE,
            model_class.id.not_in(superseded_subq),
        )
        eligible = list(self.session.scalars(stmt))
        if len(eligible) == 0:
            return None
        if len(eligible) == 1:
            return eligible[0]
        ids = sorted(r.id for r in eligible)
        raise AmbiguousCurrentRevisionError(
            f"multiple eligible ACTIVE unsuperseded revisions for identity "
            f"{entity_id}: ids={ids!r}; resolver fails closed"
        )

    def _list_revisions(
        self,
        model_class: type,
        entity_id_attr: InstrumentedAttribute,
        entity_id: int,
    ) -> list:
        stmt = (
            select(model_class)
            .where(entity_id_attr == entity_id)
            .order_by(model_class.revision_number)
        )
        return list(self.session.scalars(stmt))

    def _validate_supersession(
        self,
        revision_class: type,
        entity_id_field_name: str,
        entity_id: int,
        supersedes_revision_id: int | None,
    ) -> None:
        if supersedes_revision_id is None:
            return
        target = self.session.get(revision_class, supersedes_revision_id)
        if target is None:
            raise ValueError(
                f"superseded revision {supersedes_revision_id} does not exist"
            )
        if getattr(target, entity_id_field_name) != entity_id:
            raise CrossIdentitySupersessionError(
                f"cross-identity supersession rejected: revision "
                f"{supersedes_revision_id} belongs to identity "
                f"{getattr(target, entity_id_field_name)!r}, not {entity_id!r}"
            )

    # -------------------------------------------------------------------------
    # Material
    # -------------------------------------------------------------------------

    def create_material_identity(
        self,
        *,
        material_id: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringMaterial:
        entity = EngineeringMaterial(
            material_id=material_id,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_material_revision(
        self,
        *,
        entity_id: int,
        draft: MaterialRevisionDraft,
        content_hash: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringMaterialRevision:
        meta = draft.metadata
        self._validate_supersession(
            EngineeringMaterialRevision,
            "engineering_material_id",
            entity_id,
            meta.supersedes_revision_id,
        )
        props = draft.properties
        props_snapshot = {
            "electrical_resistivity_ohm_m": props.electrical_resistivity_ohm_m,
            "thermal_conductivity_w_mk": props.thermal_conductivity_w_mk,
            "specific_heat_j_kgk": props.specific_heat_j_kgk,
            "density_kg_m3": props.density_kg_m3,
            "solidus_c": props.solidus_c,
            "liquidus_c": props.liquidus_c,
            "yield_strength_mpa": props.yield_strength_mpa,
            "tensile_strength_mpa": props.tensile_strength_mpa,
            "hardness_hv": props.hardness_hv,
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
            "property_basis": props.property_basis.value,
        }
        revision = EngineeringMaterialRevision(
            engineering_material_id=entity_id,
            revision_number=meta.revision_number,
            supersedes_revision_id=meta.supersedes_revision_id,
            lifecycle_status=meta.lifecycle_status,
            source_class=meta.source_class,
            family=draft.identity.family,
            grade=draft.identity.grade,
            form=draft.identity.form,
            thickness_min_mm=draft.thickness_min_mm,
            thickness_max_mm=draft.thickness_max_mm,
            weldability_class=draft.weldability_class,
            contact_resistance_class=draft.contact_resistance_class,
            properties_snapshot=props_snapshot,
            evidence_reference_ids=list(meta.evidence_reference_ids),
            notes=draft.notes,
            schema_version=meta.schema_version,
            canonicalization_version=meta.canonicalization_version,
            hash_algorithm=meta.hash_algorithm,
            content_hash=content_hash,
            software_version=meta.software_version,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(revision)
        self.session.flush()
        return revision

    def get_material_identity(self, entity_id: int) -> EngineeringMaterial | None:
        return self.session.get(EngineeringMaterial, entity_id)

    def get_material_identity_by_business_id(
        self, material_id: str
    ) -> EngineeringMaterial | None:
        return self.session.scalar(
            select(EngineeringMaterial).where(
                EngineeringMaterial.material_id == material_id
            )
        )

    def list_material_identities(self) -> list[EngineeringMaterial]:
        return list(self.session.scalars(select(EngineeringMaterial).order_by(EngineeringMaterial.id)))

    def get_material_revision(
        self, revision_id: int
    ) -> EngineeringMaterialRevision | None:
        return self.session.get(EngineeringMaterialRevision, revision_id)

    def list_material_revisions(
        self, entity_id: int
    ) -> list[EngineeringMaterialRevision]:
        return self._list_revisions(
            EngineeringMaterialRevision,
            EngineeringMaterialRevision.engineering_material_id,
            entity_id,
        )

    def resolve_current_material_revision(
        self, entity_id: int
    ) -> EngineeringMaterialRevision | None:
        return self._resolve_current_revision(  # type: ignore[return-value]
            EngineeringMaterialRevision,
            EngineeringMaterialRevision.engineering_material_id,
            entity_id,
        )

    # -------------------------------------------------------------------------
    # Coating
    # -------------------------------------------------------------------------

    def create_coating_identity(
        self,
        *,
        coating_id: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringCoating:
        entity = EngineeringCoating(
            coating_id=coating_id,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_coating_revision(
        self,
        *,
        entity_id: int,
        draft: CoatingRevisionDraft,
        content_hash: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringCoatingRevision:
        meta = draft.metadata
        self._validate_supersession(
            EngineeringCoatingRevision,
            "engineering_coating_id",
            entity_id,
            meta.supersedes_revision_id,
        )
        revision = EngineeringCoatingRevision(
            engineering_coating_id=entity_id,
            revision_number=meta.revision_number,
            supersedes_revision_id=meta.supersedes_revision_id,
            lifecycle_status=meta.lifecycle_status,
            source_class=meta.source_class,
            family=draft.identity.family,
            designation=draft.identity.designation,
            nominal_thickness_um=draft.nominal_thickness_um,
            electrical_contact_effect=draft.electrical_contact_effect,
            electrode_wear_effect=draft.electrode_wear_effect,
            evidence_reference_ids=list(meta.evidence_reference_ids),
            notes=draft.notes,
            schema_version=meta.schema_version,
            canonicalization_version=meta.canonicalization_version,
            hash_algorithm=meta.hash_algorithm,
            content_hash=content_hash,
            software_version=meta.software_version,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(revision)
        self.session.flush()
        return revision

    def get_coating_identity(self, entity_id: int) -> EngineeringCoating | None:
        return self.session.get(EngineeringCoating, entity_id)

    def get_coating_identity_by_business_id(
        self, coating_id: str
    ) -> EngineeringCoating | None:
        return self.session.scalar(
            select(EngineeringCoating).where(
                EngineeringCoating.coating_id == coating_id
            )
        )

    def list_coating_identities(self) -> list[EngineeringCoating]:
        return list(self.session.scalars(select(EngineeringCoating).order_by(EngineeringCoating.id)))

    def get_coating_revision(
        self, revision_id: int
    ) -> EngineeringCoatingRevision | None:
        return self.session.get(EngineeringCoatingRevision, revision_id)

    def list_coating_revisions(
        self, entity_id: int
    ) -> list[EngineeringCoatingRevision]:
        return self._list_revisions(
            EngineeringCoatingRevision,
            EngineeringCoatingRevision.engineering_coating_id,
            entity_id,
        )

    def resolve_current_coating_revision(
        self, entity_id: int
    ) -> EngineeringCoatingRevision | None:
        return self._resolve_current_revision(  # type: ignore[return-value]
            EngineeringCoatingRevision,
            EngineeringCoatingRevision.engineering_coating_id,
            entity_id,
        )

    # -------------------------------------------------------------------------
    # Stack-Up
    # -------------------------------------------------------------------------

    def create_stack_up_identity(
        self,
        *,
        stack_id: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringStackUp:
        entity = EngineeringStackUp(
            stack_id=stack_id,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_stack_up_revision(
        self,
        *,
        entity_id: int,
        draft: StackUpRevisionDraft,
        content_hash: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringStackUpRevision:
        """Add a stack-up revision with all layers atomically.

        Validates exact material/coating revision references before writing.
        If any layer reference is missing, raises ValueError before any row is added.
        The revision row and all layer rows are written in the same flush sequence
        within the caller's GovernedUnitOfWork; a DB error in any layer flushes
        nothing (the UoW rolls back on exit without commit).
        """
        meta = draft.metadata
        self._validate_supersession(
            EngineeringStackUpRevision,
            "engineering_stack_up_id",
            entity_id,
            meta.supersedes_revision_id,
        )
        # Validate exact revision pinning before any write
        for layer in draft.layers:
            if self.session.get(EngineeringMaterialRevision, layer.material_revision_id) is None:
                raise ValueError(
                    f"stack-up layer {layer.sequence}: material revision "
                    f"{layer.material_revision_id} does not exist"
                )
            if (
                layer.coating_revision_id is not None
                and self.session.get(EngineeringCoatingRevision, layer.coating_revision_id) is None
            ):
                raise ValueError(
                        f"stack-up layer {layer.sequence}: coating revision "
                        f"{layer.coating_revision_id} does not exist"
                    )

        revision = EngineeringStackUpRevision(
            engineering_stack_up_id=entity_id,
            revision_number=meta.revision_number,
            supersedes_revision_id=meta.supersedes_revision_id,
            lifecycle_status=meta.lifecycle_status,
            source_class=meta.source_class,
            adhesive_present=draft.adhesive_present,
            interface_notes=draft.interface_notes,
            evidence_reference_ids=list(meta.evidence_reference_ids),
            schema_version=meta.schema_version,
            canonicalization_version=meta.canonicalization_version,
            hash_algorithm=meta.hash_algorithm,
            content_hash=content_hash,
            software_version=meta.software_version,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(revision)
        self.session.flush()  # Obtain revision.id before adding layers

        # Add layers in sequence order (atomic with revision in caller's transaction)
        for layer_draft in sorted(draft.layers, key=lambda ld: ld.sequence):
            layer = EngineeringStackLayer(
                stack_up_revision_id=revision.id,
                sequence=layer_draft.sequence,
                material_revision_id=layer_draft.material_revision_id,
                coating_revision_id=layer_draft.coating_revision_id,
                thickness_mm=layer_draft.thickness_mm,
                orientation=layer_draft.orientation,
            )
            self.session.add(layer)
        self.session.flush()
        return revision

    def get_stack_up_identity(self, entity_id: int) -> EngineeringStackUp | None:
        return self.session.get(EngineeringStackUp, entity_id)

    def get_stack_up_identity_by_business_id(
        self, stack_id: str
    ) -> EngineeringStackUp | None:
        return self.session.scalar(
            select(EngineeringStackUp).where(
                EngineeringStackUp.stack_id == stack_id
            )
        )

    def list_stack_up_identities(self) -> list[EngineeringStackUp]:
        return list(self.session.scalars(select(EngineeringStackUp).order_by(EngineeringStackUp.id)))

    def get_stack_up_revision(
        self, revision_id: int
    ) -> EngineeringStackUpRevision | None:
        return self.session.get(EngineeringStackUpRevision, revision_id)

    def list_stack_up_revisions(
        self, entity_id: int
    ) -> list[EngineeringStackUpRevision]:
        return self._list_revisions(
            EngineeringStackUpRevision,
            EngineeringStackUpRevision.engineering_stack_up_id,
            entity_id,
        )

    def resolve_current_stack_up_revision(
        self, entity_id: int
    ) -> EngineeringStackUpRevision | None:
        return self._resolve_current_revision(  # type: ignore[return-value]
            EngineeringStackUpRevision,
            EngineeringStackUpRevision.engineering_stack_up_id,
            entity_id,
        )

    def list_stack_layers(
        self, stack_up_revision_id: int
    ) -> list[EngineeringStackLayer]:
        stmt = (
            select(EngineeringStackLayer)
            .where(EngineeringStackLayer.stack_up_revision_id == stack_up_revision_id)
            .order_by(EngineeringStackLayer.sequence)
        )
        return list(self.session.scalars(stmt))

    # -------------------------------------------------------------------------
    # Electrode
    # -------------------------------------------------------------------------

    def create_electrode_identity(
        self,
        *,
        electrode_id: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringElectrode:
        entity = EngineeringElectrode(
            electrode_id=electrode_id,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_electrode_revision(
        self,
        *,
        entity_id: int,
        draft: ElectrodeRevisionDraft,
        content_hash: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringElectrodeRevision:
        meta = draft.metadata
        self._validate_supersession(
            EngineeringElectrodeRevision,
            "engineering_electrode_id",
            entity_id,
            meta.supersedes_revision_id,
        )
        cap = draft.cap_geometry
        revision = EngineeringElectrodeRevision(
            engineering_electrode_id=entity_id,
            revision_number=meta.revision_number,
            supersedes_revision_id=meta.supersedes_revision_id,
            lifecycle_status=meta.lifecycle_status,
            source_class=meta.source_class,
            face_geometry=cap.face_geometry,
            face_diameter_mm=cap.face_diameter_mm,
            tip_diameter_mm=cap.tip_diameter_mm,
            radius_mm=cap.radius_mm,
            included_angle_deg=cap.included_angle_deg,
            material_designation=draft.material_designation,
            cooling_channel_diameter_mm=draft.cooling_channel_diameter_mm,
            recommended_flow_lpm=draft.recommended_flow_lpm,
            recommended_max_inlet_temp_c=draft.recommended_max_inlet_temp_c,
            evidence_reference_ids=list(meta.evidence_reference_ids),
            notes=draft.notes,
            schema_version=meta.schema_version,
            canonicalization_version=meta.canonicalization_version,
            hash_algorithm=meta.hash_algorithm,
            content_hash=content_hash,
            software_version=meta.software_version,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(revision)
        self.session.flush()
        return revision

    def get_electrode_identity(self, entity_id: int) -> EngineeringElectrode | None:
        return self.session.get(EngineeringElectrode, entity_id)

    def get_electrode_identity_by_business_id(
        self, electrode_id: str
    ) -> EngineeringElectrode | None:
        return self.session.scalar(
            select(EngineeringElectrode).where(
                EngineeringElectrode.electrode_id == electrode_id
            )
        )

    def list_electrode_identities(self) -> list[EngineeringElectrode]:
        return list(self.session.scalars(select(EngineeringElectrode).order_by(EngineeringElectrode.id)))

    def get_electrode_revision(
        self, revision_id: int
    ) -> EngineeringElectrodeRevision | None:
        return self.session.get(EngineeringElectrodeRevision, revision_id)

    def list_electrode_revisions(
        self, entity_id: int
    ) -> list[EngineeringElectrodeRevision]:
        return self._list_revisions(
            EngineeringElectrodeRevision,
            EngineeringElectrodeRevision.engineering_electrode_id,
            entity_id,
        )

    def resolve_current_electrode_revision(
        self, entity_id: int
    ) -> EngineeringElectrodeRevision | None:
        return self._resolve_current_revision(  # type: ignore[return-value]
            EngineeringElectrodeRevision,
            EngineeringElectrodeRevision.engineering_electrode_id,
            entity_id,
        )

    # -------------------------------------------------------------------------
    # Weld Gun
    # -------------------------------------------------------------------------

    def create_weld_gun_identity(
        self,
        *,
        gun_id: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringWeldGun:
        entity = EngineeringWeldGun(
            gun_id=gun_id,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_weld_gun_revision(
        self,
        *,
        entity_id: int,
        draft: WeldGunRevisionDraft,
        content_hash: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringWeldGunRevision:
        meta = draft.metadata
        self._validate_supersession(
            EngineeringWeldGunRevision,
            "engineering_weld_gun_id",
            entity_id,
            meta.supersedes_revision_id,
        )
        transformer_snapshot = None
        if draft.transformer is not None:
            t = draft.transformer
            transformer_snapshot = {
                "transformer_id": t.transformer_id,
                "power_type": t.power_type.value,
                "rated_power_kva": t.rated_power_kva,
                "max_secondary_current_ka": t.max_secondary_current_ka,
                "nominal_frequency_hz": t.nominal_frequency_hz,
            }
        controller_snapshot = None
        if draft.controller is not None:
            c = draft.controller
            controller_snapshot = {
                "controller_id": c.controller_id,
                "manufacturer": c.manufacturer,
                "model": c.model,
                "supports_current_feedback": c.supports_current_feedback,
                "supports_voltage_feedback": c.supports_voltage_feedback,
                "supports_force_feedback": c.supports_force_feedback,
                "supports_displacement_feedback": c.supports_displacement_feedback,
            }
        cooling_snapshot = None
        if draft.cooling is not None:
            cg = draft.cooling
            cooling_snapshot = {
                "nominal_flow_lpm": cg.nominal_flow_lpm,
                "inlet_temperature_c": cg.inlet_temperature_c,
                "circuit_count": cg.circuit_count,
            }
        revision = EngineeringWeldGunRevision(
            engineering_weld_gun_id=entity_id,
            revision_number=meta.revision_number,
            supersedes_revision_id=meta.supersedes_revision_id,
            lifecycle_status=meta.lifecycle_status,
            source_class=meta.source_class,
            actuation_type=draft.actuation_type,
            max_force_kn=draft.max_force_kn,
            throat_depth_mm=draft.throat_depth_mm,
            max_opening_mm=draft.max_opening_mm,
            transformer_snapshot=transformer_snapshot,
            controller_snapshot=controller_snapshot,
            cooling_snapshot=cooling_snapshot,
            evidence_reference_ids=list(meta.evidence_reference_ids),
            notes=draft.notes,
            schema_version=meta.schema_version,
            canonicalization_version=meta.canonicalization_version,
            hash_algorithm=meta.hash_algorithm,
            content_hash=content_hash,
            software_version=meta.software_version,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(revision)
        self.session.flush()
        return revision

    def get_weld_gun_identity(self, entity_id: int) -> EngineeringWeldGun | None:
        return self.session.get(EngineeringWeldGun, entity_id)

    def get_weld_gun_identity_by_business_id(
        self, gun_id: str
    ) -> EngineeringWeldGun | None:
        return self.session.scalar(
            select(EngineeringWeldGun).where(
                EngineeringWeldGun.gun_id == gun_id
            )
        )

    def list_weld_gun_identities(self) -> list[EngineeringWeldGun]:
        return list(self.session.scalars(select(EngineeringWeldGun).order_by(EngineeringWeldGun.id)))

    def get_weld_gun_revision(
        self, revision_id: int
    ) -> EngineeringWeldGunRevision | None:
        return self.session.get(EngineeringWeldGunRevision, revision_id)

    def list_weld_gun_revisions(
        self, entity_id: int
    ) -> list[EngineeringWeldGunRevision]:
        return self._list_revisions(
            EngineeringWeldGunRevision,
            EngineeringWeldGunRevision.engineering_weld_gun_id,
            entity_id,
        )

    def resolve_current_weld_gun_revision(
        self, entity_id: int
    ) -> EngineeringWeldGunRevision | None:
        return self._resolve_current_revision(  # type: ignore[return-value]
            EngineeringWeldGunRevision,
            EngineeringWeldGunRevision.engineering_weld_gun_id,
            entity_id,
        )

    # -------------------------------------------------------------------------
    # Weld Schedule
    # -------------------------------------------------------------------------

    def create_weld_schedule_identity(
        self,
        *,
        schedule_id: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> EngineeringWeldSchedule:
        entity = EngineeringWeldSchedule(
            schedule_id=schedule_id,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_weld_schedule_revision(
        self,
        *,
        entity_id: int,
        draft: WeldScheduleRevisionDraft,
        content_hash: str,
        created_by_actor_id: str,
        created_by_user_id: int | None,
    ) -> tuple[EngineeringWeldScheduleRevision, list[EngineeringWeldPulse]]:
        """Add a schedule revision with all pulse rows atomically.

        The revision row and all pulse rows are written in sequence order
        within the caller's GovernedUnitOfWork. If any pulse flush fails
        (e.g., a constraint violation), the UoW rolls back on exit and no
        revision or partial pulse sequence remains persisted.
        """
        meta = draft.metadata
        self._validate_supersession(
            EngineeringWeldScheduleRevision,
            "engineering_weld_schedule_id",
            entity_id,
            meta.supersedes_revision_id,
        )
        process_meta = dict(draft.process_metadata) if draft.process_metadata else None
        revision = EngineeringWeldScheduleRevision(
            engineering_weld_schedule_id=entity_id,
            revision_number=meta.revision_number,
            supersedes_revision_id=meta.supersedes_revision_id,
            lifecycle_status=meta.lifecycle_status,
            source_class=meta.source_class,
            squeeze_cycles=draft.squeeze_cycles,
            hold_cycles=draft.hold_cycles,
            nominal_force_kn=draft.nominal_force_kn,
            process_metadata=process_meta,
            evidence_reference_ids=list(meta.evidence_reference_ids),
            notes=None,
            schema_version=meta.schema_version,
            canonicalization_version=meta.canonicalization_version,
            hash_algorithm=meta.hash_algorithm,
            content_hash=content_hash,
            software_version=meta.software_version,
            created_by_actor_id=created_by_actor_id,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(revision)
        self.session.flush()  # Obtain revision.id before adding pulses

        # Add pulses ordered by sequence_number (atomic with revision)
        pulses: list[EngineeringWeldPulse] = []
        for pulse_draft in sorted(draft.pulses, key=lambda p: p.sequence):
            pulse = EngineeringWeldPulse(
                engineering_weld_schedule_revision_id=revision.id,
                sequence_number=pulse_draft.sequence,
                pulse_type=pulse_draft.pulse_type,
                current_ka=pulse_draft.current_ka,
                duration_cycles=pulse_draft.duration_cycles,
                force_kn=pulse_draft.force_kn,
            )
            self.session.add(pulse)
            pulses.append(pulse)
        self.session.flush()
        return revision, pulses

    def get_weld_schedule_identity(
        self, entity_id: int
    ) -> EngineeringWeldSchedule | None:
        return self.session.get(EngineeringWeldSchedule, entity_id)

    def get_weld_schedule_identity_by_business_id(
        self, schedule_id: str
    ) -> EngineeringWeldSchedule | None:
        return self.session.scalar(
            select(EngineeringWeldSchedule).where(
                EngineeringWeldSchedule.schedule_id == schedule_id
            )
        )

    def list_weld_schedule_identities(self) -> list[EngineeringWeldSchedule]:
        return list(self.session.scalars(select(EngineeringWeldSchedule).order_by(EngineeringWeldSchedule.id)))

    def get_weld_schedule_revision(
        self, revision_id: int
    ) -> EngineeringWeldScheduleRevision | None:
        return self.session.get(EngineeringWeldScheduleRevision, revision_id)

    def list_weld_schedule_revisions(
        self, entity_id: int
    ) -> list[EngineeringWeldScheduleRevision]:
        return self._list_revisions(
            EngineeringWeldScheduleRevision,
            EngineeringWeldScheduleRevision.engineering_weld_schedule_id,
            entity_id,
        )

    def resolve_current_weld_schedule_revision(
        self, entity_id: int
    ) -> EngineeringWeldScheduleRevision | None:
        return self._resolve_current_revision(  # type: ignore[return-value]
            EngineeringWeldScheduleRevision,
            EngineeringWeldScheduleRevision.engineering_weld_schedule_id,
            entity_id,
        )

    def list_weld_pulses(
        self, schedule_revision_id: int
    ) -> list[EngineeringWeldPulse]:
        stmt = (
            select(EngineeringWeldPulse)
            .where(
                EngineeringWeldPulse.engineering_weld_schedule_revision_id
                == schedule_revision_id
            )
            .order_by(EngineeringWeldPulse.sequence_number)
        )
        return list(self.session.scalars(stmt))
