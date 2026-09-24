"""Engineering Library API router — CE-02C.

Endpoints for all six engineering library aggregates.
GET endpoints: get_current_user (read-only access).
POST endpoints: get_governed_actor_user (strongest auth, actor attribution).
No PUT / PATCH / DELETE — governed append-only history.
No lifecycle transition endpoints in CE-02C.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_governed_actor_user
from app.application.engineering_library_service import EngineeringLibraryService
from app.application.governed_unit_of_work import GovernedUnitOfWork
from app.db.session import SessionLocal
from app.domain.engineering_library_types import (
    CoatingIdentity,
    CoatingRevisionDraft,
    ControllerSpecification,
    CoolingConfiguration,
    ElectrodeCapGeometry,
    ElectrodeRevisionDraft,
    EngineeringLibraryRevisionMetadata,
    MaterialIdentity,
    MaterialPropertySet,
    MaterialRevisionDraft,
    StackLayerDraft,
    StackUpRevisionDraft,
    TemperaturePropertyPoint,
    TransformerSpecification,
    WeldGunRevisionDraft,
    WeldPulseDraft,
    WeldScheduleRevisionDraft,
)
from app.models.entities import User
from app.repositories.engineering_library_repository import (
    AmbiguousCurrentRevisionError,
    EngineeringLibraryRepository,
)
from app.schemas.engineering_library import (
    CoatingCreateRequest,
    CoatingCreateResponse,
    CoatingIdentityResponse,
    CoatingRevisionResponse,
    ElectrodeCreateRequest,
    ElectrodeCreateResponse,
    ElectrodeIdentityResponse,
    ElectrodeRevisionResponse,
    MaterialCreateRequest,
    MaterialCreateResponse,
    MaterialIdentityResponse,
    MaterialRevisionResponse,
    StackLayerResponse,
    StackUpCreateRequest,
    StackUpCreateResponse,
    StackUpIdentityResponse,
    StackUpRevisionResponse,
    WeldGunCreateRequest,
    WeldGunCreateResponse,
    WeldGunIdentityResponse,
    WeldGunRevisionResponse,
    WeldPulseResponse,
    WeldScheduleCreateRequest,
    WeldScheduleCreateResponse,
    WeldScheduleIdentityResponse,
    WeldScheduleRevisionResponse,
)

router = APIRouter(prefix="/engineering-library", tags=["Engineering Library"])

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _actor_id(user: User) -> str:
    return f"user:{user.id}"


def _governed_error(status_code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


def _meta(req_meta) -> EngineeringLibraryRevisionMetadata:
    return EngineeringLibraryRevisionMetadata(
        revision_number=req_meta.revision_number,
        lifecycle_status=req_meta.lifecycle_status,
        source_class=req_meta.source_class,
        created_by_actor_id="__placeholder__",  # overridden in service
        supersedes_revision_id=req_meta.supersedes_revision_id,
        evidence_reference_ids=tuple(req_meta.evidence_reference_ids or []),
    )


# ---------------------------------------------------------------------------
# Materialisation helpers (request → domain draft)
# ---------------------------------------------------------------------------


def _build_material_draft(req: MaterialCreateRequest, actor_id: str) -> MaterialRevisionDraft:
    meta = EngineeringLibraryRevisionMetadata(
        revision_number=req.metadata.revision_number,
        lifecycle_status=req.metadata.lifecycle_status,
        source_class=req.metadata.source_class,
        created_by_actor_id=actor_id,
        supersedes_revision_id=req.metadata.supersedes_revision_id,
        evidence_reference_ids=tuple(req.metadata.evidence_reference_ids or []),
    )
    props_req = req.properties
    properties = MaterialPropertySet(
        electrical_resistivity_ohm_m=props_req.electrical_resistivity_ohm_m,
        thermal_conductivity_w_mk=props_req.thermal_conductivity_w_mk,
        specific_heat_j_kgk=props_req.specific_heat_j_kgk,
        density_kg_m3=props_req.density_kg_m3,
        solidus_c=props_req.solidus_c,
        liquidus_c=props_req.liquidus_c,
        yield_strength_mpa=props_req.yield_strength_mpa,
        tensile_strength_mpa=props_req.tensile_strength_mpa,
        hardness_hv=props_req.hardness_hv,
        resistivity_curve=tuple(
            TemperaturePropertyPoint(p.temperature_c, p.value)
            for p in props_req.resistivity_curve
        ),
        conductivity_curve=tuple(
            TemperaturePropertyPoint(p.temperature_c, p.value)
            for p in props_req.conductivity_curve
        ),
        specific_heat_curve=tuple(
            TemperaturePropertyPoint(p.temperature_c, p.value)
            for p in props_req.specific_heat_curve
        ),
        property_basis=props_req.property_basis,
    )
    return MaterialRevisionDraft(
        identity=MaterialIdentity(
            material_id=req.material_id,
            family=req.family,
            grade=req.grade,
            form=req.form,
        ),
        metadata=meta,
        properties=properties,
        thickness_min_mm=req.thickness_min_mm,
        thickness_max_mm=req.thickness_max_mm,
        weldability_class=req.weldability_class,
        contact_resistance_class=req.contact_resistance_class,
        notes=req.metadata.notes,
    )


def _build_coating_draft(req: CoatingCreateRequest, actor_id: str) -> CoatingRevisionDraft:
    meta = EngineeringLibraryRevisionMetadata(
        revision_number=req.metadata.revision_number,
        lifecycle_status=req.metadata.lifecycle_status,
        source_class=req.metadata.source_class,
        created_by_actor_id=actor_id,
        supersedes_revision_id=req.metadata.supersedes_revision_id,
        evidence_reference_ids=tuple(req.metadata.evidence_reference_ids or []),
    )
    return CoatingRevisionDraft(
        identity=CoatingIdentity(
            coating_id=req.coating_id,
            family=req.family,
            designation=req.designation,
        ),
        metadata=meta,
        nominal_thickness_um=req.nominal_thickness_um,
        electrical_contact_effect=req.electrical_contact_effect,
        electrode_wear_effect=req.electrode_wear_effect,
        notes=req.metadata.notes,
    )


def _build_stack_up_draft(req: StackUpCreateRequest, actor_id: str) -> StackUpRevisionDraft:
    meta = EngineeringLibraryRevisionMetadata(
        revision_number=req.metadata.revision_number,
        lifecycle_status=req.metadata.lifecycle_status,
        source_class=req.metadata.source_class,
        created_by_actor_id=actor_id,
        supersedes_revision_id=req.metadata.supersedes_revision_id,
        evidence_reference_ids=tuple(req.metadata.evidence_reference_ids or []),
    )
    layers = tuple(
        StackLayerDraft(
            sequence=lyr.sequence,
            material_revision_id=lyr.material_revision_id,
            thickness_mm=lyr.thickness_mm,
            coating_revision_id=lyr.coating_revision_id,
            orientation=lyr.orientation,
        )
        for lyr in sorted(req.layers, key=lambda lyr_: lyr_.sequence)
    )
    return StackUpRevisionDraft(
        stack_id=req.stack_id,
        metadata=meta,
        layers=layers,
        adhesive_present=req.adhesive_present,
        interface_notes=req.interface_notes,
    )


def _build_electrode_draft(req: ElectrodeCreateRequest, actor_id: str) -> ElectrodeRevisionDraft:
    meta = EngineeringLibraryRevisionMetadata(
        revision_number=req.metadata.revision_number,
        lifecycle_status=req.metadata.lifecycle_status,
        source_class=req.metadata.source_class,
        created_by_actor_id=actor_id,
        supersedes_revision_id=req.metadata.supersedes_revision_id,
        evidence_reference_ids=tuple(req.metadata.evidence_reference_ids or []),
    )
    cap = ElectrodeCapGeometry(
        face_geometry=req.cap_geometry.face_geometry,
        face_diameter_mm=req.cap_geometry.face_diameter_mm,
        tip_diameter_mm=req.cap_geometry.tip_diameter_mm,
        radius_mm=req.cap_geometry.radius_mm,
        included_angle_deg=req.cap_geometry.included_angle_deg,
    )
    return ElectrodeRevisionDraft(
        electrode_id=req.electrode_id,
        metadata=meta,
        cap_geometry=cap,
        material_designation=req.material_designation,
        cooling_channel_diameter_mm=req.cooling_channel_diameter_mm,
        recommended_flow_lpm=req.recommended_flow_lpm,
        recommended_max_inlet_temp_c=req.recommended_max_inlet_temp_c,
        notes=req.metadata.notes,
    )


def _build_weld_gun_draft(req: WeldGunCreateRequest, actor_id: str) -> WeldGunRevisionDraft:
    meta = EngineeringLibraryRevisionMetadata(
        revision_number=req.metadata.revision_number,
        lifecycle_status=req.metadata.lifecycle_status,
        source_class=req.metadata.source_class,
        created_by_actor_id=actor_id,
        supersedes_revision_id=req.metadata.supersedes_revision_id,
        evidence_reference_ids=tuple(req.metadata.evidence_reference_ids or []),
    )
    transformer = None
    if req.transformer is not None:
        t = req.transformer
        transformer = TransformerSpecification(
            transformer_id=t.transformer_id,
            power_type=t.power_type,
            rated_power_kva=t.rated_power_kva,
            max_secondary_current_ka=t.max_secondary_current_ka,
            nominal_frequency_hz=t.nominal_frequency_hz,
        )
    controller = None
    if req.controller is not None:
        c = req.controller
        controller = ControllerSpecification(
            controller_id=c.controller_id,
            manufacturer=c.manufacturer,
            model=c.model,
            supports_current_feedback=c.supports_current_feedback,
            supports_voltage_feedback=c.supports_voltage_feedback,
            supports_force_feedback=c.supports_force_feedback,
            supports_displacement_feedback=c.supports_displacement_feedback,
        )
    cooling = None
    if req.cooling is not None:
        cg = req.cooling
        cooling = CoolingConfiguration(
            nominal_flow_lpm=cg.nominal_flow_lpm,
            inlet_temperature_c=cg.inlet_temperature_c,
            circuit_count=cg.circuit_count,
        )
    return WeldGunRevisionDraft(
        gun_id=req.gun_id,
        metadata=meta,
        actuation_type=req.actuation_type,
        max_force_kn=req.max_force_kn,
        throat_depth_mm=req.throat_depth_mm,
        max_opening_mm=req.max_opening_mm,
        transformer=transformer,
        controller=controller,
        cooling=cooling,
        notes=req.metadata.notes,
    )


def _build_weld_schedule_draft(req: WeldScheduleCreateRequest, actor_id: str) -> WeldScheduleRevisionDraft:
    meta = EngineeringLibraryRevisionMetadata(
        revision_number=req.metadata.revision_number,
        lifecycle_status=req.metadata.lifecycle_status,
        source_class=req.metadata.source_class,
        created_by_actor_id=actor_id,
        supersedes_revision_id=req.metadata.supersedes_revision_id,
        evidence_reference_ids=tuple(req.metadata.evidence_reference_ids or []),
    )
    pulses = tuple(
        WeldPulseDraft(
            sequence=p.sequence,
            pulse_type=p.pulse_type,
            current_ka=p.current_ka,
            duration_cycles=p.duration_cycles,
            force_kn=p.force_kn,
        )
        for p in sorted(req.pulses, key=lambda p: p.sequence)
    )
    return WeldScheduleRevisionDraft(
        schedule_id=req.schedule_id,
        metadata=meta,
        squeeze_cycles=req.squeeze_cycles,
        hold_cycles=req.hold_cycles,
        nominal_force_kn=req.nominal_force_kn,
        process_metadata=req.process_metadata,
        pulses=pulses,
    )


# ---------------------------------------------------------------------------
# Serialisation helpers (ORM → response)
# ---------------------------------------------------------------------------


def _mat_id_resp(entity) -> MaterialIdentityResponse:
    return MaterialIdentityResponse(
        id=entity.id,
        material_id=entity.material_id,
        created_by_actor_id=entity.created_by_actor_id,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _mat_rev_resp(rev) -> MaterialRevisionResponse:
    return MaterialRevisionResponse(
        id=rev.id,
        engineering_material_id=rev.engineering_material_id,
        revision_number=rev.revision_number,
        lifecycle_status=rev.lifecycle_status,
        source_class=rev.source_class,
        supersedes_revision_id=rev.supersedes_revision_id,
        family=rev.family,
        grade=rev.grade,
        form=rev.form,
        thickness_min_mm=rev.thickness_min_mm,
        thickness_max_mm=rev.thickness_max_mm,
        weldability_class=rev.weldability_class,
        contact_resistance_class=rev.contact_resistance_class,
        properties_snapshot=dict(rev.properties_snapshot),
        evidence_reference_ids=list(rev.evidence_reference_ids),
        notes=rev.notes,
        content_hash=rev.content_hash,
        schema_version=rev.schema_version,
        canonicalization_version=rev.canonicalization_version,
        hash_algorithm=rev.hash_algorithm,
        software_version=rev.software_version,
        created_by_actor_id=rev.created_by_actor_id,
        created_by_user_id=rev.created_by_user_id,
        created_at=rev.created_at,
    )


def _coat_id_resp(entity) -> CoatingIdentityResponse:
    return CoatingIdentityResponse(
        id=entity.id,
        coating_id=entity.coating_id,
        created_by_actor_id=entity.created_by_actor_id,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _coat_rev_resp(rev) -> CoatingRevisionResponse:
    return CoatingRevisionResponse(
        id=rev.id,
        engineering_coating_id=rev.engineering_coating_id,
        revision_number=rev.revision_number,
        lifecycle_status=rev.lifecycle_status,
        source_class=rev.source_class,
        supersedes_revision_id=rev.supersedes_revision_id,
        family=rev.family,
        designation=rev.designation,
        nominal_thickness_um=rev.nominal_thickness_um,
        electrical_contact_effect=rev.electrical_contact_effect,
        electrode_wear_effect=rev.electrode_wear_effect,
        evidence_reference_ids=list(rev.evidence_reference_ids),
        notes=rev.notes,
        content_hash=rev.content_hash,
        schema_version=rev.schema_version,
        canonicalization_version=rev.canonicalization_version,
        hash_algorithm=rev.hash_algorithm,
        software_version=rev.software_version,
        created_by_actor_id=rev.created_by_actor_id,
        created_by_user_id=rev.created_by_user_id,
        created_at=rev.created_at,
    )


def _layer_resp(layer) -> StackLayerResponse:
    return StackLayerResponse(
        id=layer.id,
        stack_up_revision_id=layer.stack_up_revision_id,
        sequence=layer.sequence,
        material_revision_id=layer.material_revision_id,
        coating_revision_id=layer.coating_revision_id,
        thickness_mm=layer.thickness_mm,
        orientation=layer.orientation,
        created_at=layer.created_at,
    )


def _stack_id_resp(entity) -> StackUpIdentityResponse:
    return StackUpIdentityResponse(
        id=entity.id,
        stack_id=entity.stack_id,
        created_by_actor_id=entity.created_by_actor_id,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _stack_rev_resp(rev, layers=None) -> StackUpRevisionResponse:
    return StackUpRevisionResponse(
        id=rev.id,
        engineering_stack_up_id=rev.engineering_stack_up_id,
        revision_number=rev.revision_number,
        lifecycle_status=rev.lifecycle_status,
        source_class=rev.source_class,
        supersedes_revision_id=rev.supersedes_revision_id,
        adhesive_present=rev.adhesive_present,
        interface_notes=rev.interface_notes,
        evidence_reference_ids=list(rev.evidence_reference_ids),
        content_hash=rev.content_hash,
        schema_version=rev.schema_version,
        canonicalization_version=rev.canonicalization_version,
        hash_algorithm=rev.hash_algorithm,
        software_version=rev.software_version,
        created_by_actor_id=rev.created_by_actor_id,
        created_by_user_id=rev.created_by_user_id,
        created_at=rev.created_at,
        layers=[_layer_resp(lyr) for lyr in (layers or [])],
    )


def _elec_id_resp(entity) -> ElectrodeIdentityResponse:
    return ElectrodeIdentityResponse(
        id=entity.id,
        electrode_id=entity.electrode_id,
        created_by_actor_id=entity.created_by_actor_id,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _elec_rev_resp(rev) -> ElectrodeRevisionResponse:
    return ElectrodeRevisionResponse(
        id=rev.id,
        engineering_electrode_id=rev.engineering_electrode_id,
        revision_number=rev.revision_number,
        lifecycle_status=rev.lifecycle_status,
        source_class=rev.source_class,
        supersedes_revision_id=rev.supersedes_revision_id,
        face_geometry=rev.face_geometry,
        face_diameter_mm=rev.face_diameter_mm,
        tip_diameter_mm=rev.tip_diameter_mm,
        radius_mm=rev.radius_mm,
        included_angle_deg=rev.included_angle_deg,
        material_designation=rev.material_designation,
        cooling_channel_diameter_mm=rev.cooling_channel_diameter_mm,
        recommended_flow_lpm=rev.recommended_flow_lpm,
        recommended_max_inlet_temp_c=rev.recommended_max_inlet_temp_c,
        evidence_reference_ids=list(rev.evidence_reference_ids),
        notes=rev.notes,
        content_hash=rev.content_hash,
        schema_version=rev.schema_version,
        canonicalization_version=rev.canonicalization_version,
        hash_algorithm=rev.hash_algorithm,
        software_version=rev.software_version,
        created_by_actor_id=rev.created_by_actor_id,
        created_by_user_id=rev.created_by_user_id,
        created_at=rev.created_at,
    )


def _gun_id_resp(entity) -> WeldGunIdentityResponse:
    return WeldGunIdentityResponse(
        id=entity.id,
        gun_id=entity.gun_id,
        created_by_actor_id=entity.created_by_actor_id,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _gun_rev_resp(rev) -> WeldGunRevisionResponse:
    return WeldGunRevisionResponse(
        id=rev.id,
        engineering_weld_gun_id=rev.engineering_weld_gun_id,
        revision_number=rev.revision_number,
        lifecycle_status=rev.lifecycle_status,
        source_class=rev.source_class,
        supersedes_revision_id=rev.supersedes_revision_id,
        actuation_type=rev.actuation_type,
        max_force_kn=rev.max_force_kn,
        throat_depth_mm=rev.throat_depth_mm,
        max_opening_mm=rev.max_opening_mm,
        transformer_snapshot=dict(rev.transformer_snapshot) if rev.transformer_snapshot else None,
        controller_snapshot=dict(rev.controller_snapshot) if rev.controller_snapshot else None,
        cooling_snapshot=dict(rev.cooling_snapshot) if rev.cooling_snapshot else None,
        evidence_reference_ids=list(rev.evidence_reference_ids),
        notes=rev.notes,
        content_hash=rev.content_hash,
        schema_version=rev.schema_version,
        canonicalization_version=rev.canonicalization_version,
        hash_algorithm=rev.hash_algorithm,
        software_version=rev.software_version,
        created_by_actor_id=rev.created_by_actor_id,
        created_by_user_id=rev.created_by_user_id,
        created_at=rev.created_at,
    )


def _pulse_resp(pulse) -> WeldPulseResponse:
    return WeldPulseResponse(
        id=pulse.id,
        engineering_weld_schedule_revision_id=pulse.engineering_weld_schedule_revision_id,
        sequence_number=pulse.sequence_number,
        pulse_type=pulse.pulse_type,
        current_ka=pulse.current_ka,
        duration_cycles=pulse.duration_cycles,
        force_kn=pulse.force_kn,
        created_at=pulse.created_at,
    )


def _sched_id_resp(entity) -> WeldScheduleIdentityResponse:
    return WeldScheduleIdentityResponse(
        id=entity.id,
        schedule_id=entity.schedule_id,
        created_by_actor_id=entity.created_by_actor_id,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _sched_rev_resp(rev, pulses=None) -> WeldScheduleRevisionResponse:
    return WeldScheduleRevisionResponse(
        id=rev.id,
        engineering_weld_schedule_id=rev.engineering_weld_schedule_id,
        revision_number=rev.revision_number,
        lifecycle_status=rev.lifecycle_status,
        source_class=rev.source_class,
        supersedes_revision_id=rev.supersedes_revision_id,
        squeeze_cycles=rev.squeeze_cycles,
        hold_cycles=rev.hold_cycles,
        nominal_force_kn=rev.nominal_force_kn,
        process_metadata=dict(rev.process_metadata) if rev.process_metadata else None,
        evidence_reference_ids=list(rev.evidence_reference_ids),
        notes=rev.notes,
        content_hash=rev.content_hash,
        schema_version=rev.schema_version,
        canonicalization_version=rev.canonicalization_version,
        hash_algorithm=rev.hash_algorithm,
        software_version=rev.software_version,
        created_by_actor_id=rev.created_by_actor_id,
        created_by_user_id=rev.created_by_user_id,
        created_at=rev.created_at,
        pulses=[_pulse_resp(p) for p in (pulses or [])],
    )


# ===========================================================================
# MATERIAL endpoints
# ===========================================================================


@router.get("/materials", response_model=list[MaterialIdentityResponse])
def list_materials(current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        return [_mat_id_resp(e) for e in repo.list_material_identities()]


@router.post("/materials", response_model=MaterialCreateResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    req: MaterialCreateRequest,
    current_user: User = Depends(get_governed_actor_user),  # noqa: B008
):
    actor_id = _actor_id(current_user)
    draft = _build_material_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_material_with_revision(
                draft=draft,
                actor_id=actor_id,
                actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            uow.commit()
            return MaterialCreateResponse(
                identity=_mat_id_resp(identity),
                revision=_mat_rev_resp(revision),
            )
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/materials/{material_id}", response_model=MaterialIdentityResponse)
def get_material(material_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_material_identity_by_business_id(material_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"material '{material_id}' not found")
        return _mat_id_resp(entity)


@router.get("/materials/{material_id}/revisions", response_model=list[MaterialRevisionResponse])
def list_material_revisions(material_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_material_identity_by_business_id(material_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"material '{material_id}' not found")
        return [_mat_rev_resp(r) for r in repo.list_material_revisions(entity.id)]


@router.get("/materials/{material_id}/revisions/current", response_model=MaterialRevisionResponse)
def get_current_material_revision(material_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_material_identity_by_business_id(material_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"material '{material_id}' not found")
        try:
            rev = repo.resolve_current_material_revision(entity.id)
        except AmbiguousCurrentRevisionError as exc:
            raise _governed_error(status.HTTP_409_CONFLICT, str(exc)) from exc
        if rev is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, "no current ACTIVE revision")
        return _mat_rev_resp(rev)


@router.get("/materials/{material_id}/revisions/{revision_number}", response_model=MaterialRevisionResponse)
def get_material_revision(
    material_id: str, revision_number: int, current_user: User = Depends(get_current_user)  # noqa: B008
):
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_material_identity_by_business_id(material_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"material '{material_id}' not found")
        revisions = repo.list_material_revisions(entity.id)
        for r in revisions:
            if r.revision_number == revision_number:
                return _mat_rev_resp(r)
        raise _governed_error(status.HTTP_404_NOT_FOUND, f"revision {revision_number} not found")


@router.post("/materials/{material_id}/revisions", response_model=MaterialRevisionResponse, status_code=status.HTTP_201_CREATED)
def add_material_revision(
    material_id: str,
    req: MaterialCreateRequest,
    current_user: User = Depends(get_governed_actor_user),  # noqa: B008
):
    actor_id = _actor_id(current_user)
    draft = _build_material_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            repo = EngineeringLibraryRepository(governed_session)
            entity = repo.get_material_identity_by_business_id(material_id)
            if entity is None:
                raise _governed_error(status.HTTP_404_NOT_FOUND, f"material '{material_id}' not found")
            svc = EngineeringLibraryService(uow)
            revision = svc.add_material_revision(
                entity_id=entity.id,
                draft=draft,
                actor_id=actor_id,
                actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            uow.commit()
            return _mat_rev_resp(revision)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


# ===========================================================================
# COATING endpoints
# ===========================================================================


@router.get("/coatings", response_model=list[CoatingIdentityResponse])
def list_coatings(current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        return [_coat_id_resp(e) for e in repo.list_coating_identities()]


@router.post("/coatings", response_model=CoatingCreateResponse, status_code=status.HTTP_201_CREATED)
def create_coating(req: CoatingCreateRequest, current_user: User = Depends(get_governed_actor_user)):  # noqa: B008
    actor_id = _actor_id(current_user)
    draft = _build_coating_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_coating_with_revision(
                draft=draft, actor_id=actor_id, actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            uow.commit()
            return CoatingCreateResponse(identity=_coat_id_resp(identity), revision=_coat_rev_resp(revision))
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/coatings/{coating_id}", response_model=CoatingIdentityResponse)
def get_coating(coating_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_coating_identity_by_business_id(coating_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"coating '{coating_id}' not found")
        return _coat_id_resp(entity)


@router.get("/coatings/{coating_id}/revisions", response_model=list[CoatingRevisionResponse])
def list_coating_revisions(coating_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_coating_identity_by_business_id(coating_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"coating '{coating_id}' not found")
        return [_coat_rev_resp(r) for r in repo.list_coating_revisions(entity.id)]


@router.get("/coatings/{coating_id}/revisions/current", response_model=CoatingRevisionResponse)
def get_current_coating_revision(coating_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_coating_identity_by_business_id(coating_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"coating '{coating_id}' not found")
        try:
            rev = repo.resolve_current_coating_revision(entity.id)
        except AmbiguousCurrentRevisionError as exc:
            raise _governed_error(status.HTTP_409_CONFLICT, str(exc)) from exc
        if rev is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, "no current ACTIVE revision")
        return _coat_rev_resp(rev)


@router.post("/coatings/{coating_id}/revisions", response_model=CoatingRevisionResponse, status_code=status.HTTP_201_CREATED)
def add_coating_revision(
    coating_id: str, req: CoatingCreateRequest, current_user: User = Depends(get_governed_actor_user)  # noqa: B008
):
    actor_id = _actor_id(current_user)
    draft = _build_coating_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            repo = EngineeringLibraryRepository(governed_session)
            entity = repo.get_coating_identity_by_business_id(coating_id)
            if entity is None:
                raise _governed_error(status.HTTP_404_NOT_FOUND, f"coating '{coating_id}' not found")
            svc = EngineeringLibraryService(uow)
            revision = svc.add_coating_revision(
                entity_id=entity.id, draft=draft, actor_id=actor_id,
                actor_user_id=current_user.id, reason=req.metadata.reason,
            )
            uow.commit()
            return _coat_rev_resp(revision)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


# ===========================================================================
# STACK-UP endpoints
# ===========================================================================


@router.get("/stack-ups", response_model=list[StackUpIdentityResponse])
def list_stack_ups(current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        return [_stack_id_resp(e) for e in repo.list_stack_up_identities()]


@router.post("/stack-ups", response_model=StackUpCreateResponse, status_code=status.HTTP_201_CREATED)
def create_stack_up(req: StackUpCreateRequest, current_user: User = Depends(get_governed_actor_user)):  # noqa: B008
    actor_id = _actor_id(current_user)
    try:
        draft = _build_stack_up_draft(req, actor_id)
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_stack_up_with_revision(
                draft=draft, actor_id=actor_id, actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            repo = EngineeringLibraryRepository(governed_session)
            layers = repo.list_stack_layers(revision.id)
            uow.commit()
            return StackUpCreateResponse(
                identity=_stack_id_resp(identity),
                revision=_stack_rev_resp(revision, layers),
            )
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/stack-ups/{stack_id}", response_model=StackUpIdentityResponse)
def get_stack_up(stack_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_stack_up_identity_by_business_id(stack_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"stack-up '{stack_id}' not found")
        return _stack_id_resp(entity)


@router.get("/stack-ups/{stack_id}/revisions", response_model=list[StackUpRevisionResponse])
def list_stack_up_revisions(stack_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_stack_up_identity_by_business_id(stack_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"stack-up '{stack_id}' not found")
        revisions = repo.list_stack_up_revisions(entity.id)
        return [
            _stack_rev_resp(r, repo.list_stack_layers(r.id))
            for r in revisions
        ]


@router.get("/stack-ups/{stack_id}/revisions/current", response_model=StackUpRevisionResponse)
def get_current_stack_up_revision(stack_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_stack_up_identity_by_business_id(stack_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"stack-up '{stack_id}' not found")
        try:
            rev = repo.resolve_current_stack_up_revision(entity.id)
        except AmbiguousCurrentRevisionError as exc:
            raise _governed_error(status.HTTP_409_CONFLICT, str(exc)) from exc
        if rev is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, "no current ACTIVE revision")
        return _stack_rev_resp(rev, repo.list_stack_layers(rev.id))


@router.post("/stack-ups/{stack_id}/revisions", response_model=StackUpRevisionResponse, status_code=status.HTTP_201_CREATED)
def add_stack_up_revision(
    stack_id: str, req: StackUpCreateRequest, current_user: User = Depends(get_governed_actor_user)  # noqa: B008
):
    actor_id = _actor_id(current_user)
    try:
        draft = _build_stack_up_draft(req, actor_id)
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            repo = EngineeringLibraryRepository(governed_session)
            entity = repo.get_stack_up_identity_by_business_id(stack_id)
            if entity is None:
                raise _governed_error(status.HTTP_404_NOT_FOUND, f"stack-up '{stack_id}' not found")
            svc = EngineeringLibraryService(uow)
            revision = svc.add_stack_up_revision(
                entity_id=entity.id, draft=draft, actor_id=actor_id,
                actor_user_id=current_user.id, reason=req.metadata.reason,
            )
            layers = repo.list_stack_layers(revision.id)
            uow.commit()
            return _stack_rev_resp(revision, layers)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


# ===========================================================================
# ELECTRODE endpoints
# ===========================================================================


@router.get("/electrodes", response_model=list[ElectrodeIdentityResponse])
def list_electrodes(current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        return [_elec_id_resp(e) for e in EngineeringLibraryRepository(session).list_electrode_identities()]


@router.post("/electrodes", response_model=ElectrodeCreateResponse, status_code=status.HTTP_201_CREATED)
def create_electrode(req: ElectrodeCreateRequest, current_user: User = Depends(get_governed_actor_user)):  # noqa: B008
    actor_id = _actor_id(current_user)
    draft = _build_electrode_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_electrode_with_revision(
                draft=draft, actor_id=actor_id, actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            uow.commit()
            return ElectrodeCreateResponse(identity=_elec_id_resp(identity), revision=_elec_rev_resp(revision))
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/electrodes/{electrode_id}", response_model=ElectrodeIdentityResponse)
def get_electrode(electrode_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        entity = EngineeringLibraryRepository(session).get_electrode_identity_by_business_id(electrode_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"electrode '{electrode_id}' not found")
        return _elec_id_resp(entity)


@router.get("/electrodes/{electrode_id}/revisions", response_model=list[ElectrodeRevisionResponse])
def list_electrode_revisions(electrode_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_electrode_identity_by_business_id(electrode_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"electrode '{electrode_id}' not found")
        return [_elec_rev_resp(r) for r in repo.list_electrode_revisions(entity.id)]


@router.get("/electrodes/{electrode_id}/revisions/current", response_model=ElectrodeRevisionResponse)
def get_current_electrode_revision(electrode_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_electrode_identity_by_business_id(electrode_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"electrode '{electrode_id}' not found")
        try:
            rev = repo.resolve_current_electrode_revision(entity.id)
        except AmbiguousCurrentRevisionError as exc:
            raise _governed_error(status.HTTP_409_CONFLICT, str(exc)) from exc
        if rev is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, "no current ACTIVE revision")
        return _elec_rev_resp(rev)


@router.post("/electrodes/{electrode_id}/revisions", response_model=ElectrodeRevisionResponse, status_code=status.HTTP_201_CREATED)
def add_electrode_revision(
    electrode_id: str, req: ElectrodeCreateRequest, current_user: User = Depends(get_governed_actor_user)  # noqa: B008
):
    actor_id = _actor_id(current_user)
    draft = _build_electrode_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            repo = EngineeringLibraryRepository(governed_session)
            entity = repo.get_electrode_identity_by_business_id(electrode_id)
            if entity is None:
                raise _governed_error(status.HTTP_404_NOT_FOUND, f"electrode '{electrode_id}' not found")
            svc = EngineeringLibraryService(uow)
            revision = svc.add_electrode_revision(
                entity_id=entity.id, draft=draft, actor_id=actor_id,
                actor_user_id=current_user.id, reason=req.metadata.reason,
            )
            uow.commit()
            return _elec_rev_resp(revision)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


# ===========================================================================
# WELD GUN endpoints
# ===========================================================================


@router.get("/weld-guns", response_model=list[WeldGunIdentityResponse])
def list_weld_guns(current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        return [_gun_id_resp(e) for e in EngineeringLibraryRepository(session).list_weld_gun_identities()]


@router.post("/weld-guns", response_model=WeldGunCreateResponse, status_code=status.HTTP_201_CREATED)
def create_weld_gun(req: WeldGunCreateRequest, current_user: User = Depends(get_governed_actor_user)):  # noqa: B008
    actor_id = _actor_id(current_user)
    draft = _build_weld_gun_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_weld_gun_with_revision(
                draft=draft, actor_id=actor_id, actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            uow.commit()
            return WeldGunCreateResponse(identity=_gun_id_resp(identity), revision=_gun_rev_resp(revision))
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/weld-guns/{gun_id}", response_model=WeldGunIdentityResponse)
def get_weld_gun(gun_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        entity = EngineeringLibraryRepository(session).get_weld_gun_identity_by_business_id(gun_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld gun '{gun_id}' not found")
        return _gun_id_resp(entity)


@router.get("/weld-guns/{gun_id}/revisions", response_model=list[WeldGunRevisionResponse])
def list_weld_gun_revisions(gun_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_weld_gun_identity_by_business_id(gun_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld gun '{gun_id}' not found")
        return [_gun_rev_resp(r) for r in repo.list_weld_gun_revisions(entity.id)]


@router.get("/weld-guns/{gun_id}/revisions/current", response_model=WeldGunRevisionResponse)
def get_current_weld_gun_revision(gun_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_weld_gun_identity_by_business_id(gun_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld gun '{gun_id}' not found")
        try:
            rev = repo.resolve_current_weld_gun_revision(entity.id)
        except AmbiguousCurrentRevisionError as exc:
            raise _governed_error(status.HTTP_409_CONFLICT, str(exc)) from exc
        if rev is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, "no current ACTIVE revision")
        return _gun_rev_resp(rev)


@router.post("/weld-guns/{gun_id}/revisions", response_model=WeldGunRevisionResponse, status_code=status.HTTP_201_CREATED)
def add_weld_gun_revision(
    gun_id: str, req: WeldGunCreateRequest, current_user: User = Depends(get_governed_actor_user)  # noqa: B008
):
    actor_id = _actor_id(current_user)
    draft = _build_weld_gun_draft(req, actor_id)
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            repo = EngineeringLibraryRepository(governed_session)
            entity = repo.get_weld_gun_identity_by_business_id(gun_id)
            if entity is None:
                raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld gun '{gun_id}' not found")
            svc = EngineeringLibraryService(uow)
            revision = svc.add_weld_gun_revision(
                entity_id=entity.id, draft=draft, actor_id=actor_id,
                actor_user_id=current_user.id, reason=req.metadata.reason,
            )
            uow.commit()
            return _gun_rev_resp(revision)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


# ===========================================================================
# WELD SCHEDULE endpoints
# ===========================================================================


@router.get("/weld-schedules", response_model=list[WeldScheduleIdentityResponse])
def list_weld_schedules(current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        return [_sched_id_resp(e) for e in EngineeringLibraryRepository(session).list_weld_schedule_identities()]


@router.post("/weld-schedules", response_model=WeldScheduleCreateResponse, status_code=status.HTTP_201_CREATED)
def create_weld_schedule(req: WeldScheduleCreateRequest, current_user: User = Depends(get_governed_actor_user)):  # noqa: B008
    actor_id = _actor_id(current_user)
    try:
        draft = _build_weld_schedule_draft(req, actor_id)
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision, pulses = svc.create_weld_schedule_with_revision(
                draft=draft, actor_id=actor_id, actor_user_id=current_user.id,
                reason=req.metadata.reason,
            )
            uow.commit()
            return WeldScheduleCreateResponse(
                identity=_sched_id_resp(identity),
                revision=_sched_rev_resp(revision, pulses),
            )
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/weld-schedules/{schedule_id}", response_model=WeldScheduleIdentityResponse)
def get_weld_schedule(schedule_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        entity = EngineeringLibraryRepository(session).get_weld_schedule_identity_by_business_id(schedule_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld schedule '{schedule_id}' not found")
        return _sched_id_resp(entity)


@router.get("/weld-schedules/{schedule_id}/revisions", response_model=list[WeldScheduleRevisionResponse])
def list_weld_schedule_revisions(schedule_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_weld_schedule_identity_by_business_id(schedule_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld schedule '{schedule_id}' not found")
        revisions = repo.list_weld_schedule_revisions(entity.id)
        return [_sched_rev_resp(r, repo.list_weld_pulses(r.id)) for r in revisions]


@router.get("/weld-schedules/{schedule_id}/revisions/current", response_model=WeldScheduleRevisionResponse)
def get_current_weld_schedule_revision(schedule_id: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    with SessionLocal() as session:
        repo = EngineeringLibraryRepository(session)
        entity = repo.get_weld_schedule_identity_by_business_id(schedule_id)
        if entity is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld schedule '{schedule_id}' not found")
        try:
            rev = repo.resolve_current_weld_schedule_revision(entity.id)
        except AmbiguousCurrentRevisionError as exc:
            raise _governed_error(status.HTTP_409_CONFLICT, str(exc)) from exc
        if rev is None:
            raise _governed_error(status.HTTP_404_NOT_FOUND, "no current ACTIVE revision")
        return _sched_rev_resp(rev, repo.list_weld_pulses(rev.id))


@router.post("/weld-schedules/{schedule_id}/revisions", response_model=WeldScheduleRevisionResponse, status_code=status.HTTP_201_CREATED)
def add_weld_schedule_revision(
    schedule_id: str, req: WeldScheduleCreateRequest, current_user: User = Depends(get_governed_actor_user)  # noqa: B008
):
    actor_id = _actor_id(current_user)
    try:
        draft = _build_weld_schedule_draft(req, actor_id)
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    try:
        with SessionLocal() as governed_session, GovernedUnitOfWork(governed_session) as uow:
            repo = EngineeringLibraryRepository(governed_session)
            entity = repo.get_weld_schedule_identity_by_business_id(schedule_id)
            if entity is None:
                raise _governed_error(status.HTTP_404_NOT_FOUND, f"weld schedule '{schedule_id}' not found")
            svc = EngineeringLibraryService(uow)
            revision, pulses = svc.add_weld_schedule_revision(
                entity_id=entity.id, draft=draft, actor_id=actor_id,
                actor_user_id=current_user.id, reason=req.metadata.reason,
            )
            uow.commit()
            return _sched_rev_resp(revision, pulses)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise _governed_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
