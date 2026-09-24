"""Pydantic schemas for Engineering Library API — CE-02C.

Request/response models for all six aggregates.
extra="forbid" on all request models.
No PUT / PATCH / DELETE shapes — governed append-only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.engineering_library_types import (
    ElectrodeFaceGeometry,
    EngineeringLibraryLifecycleStatus,
    EngineeringLibrarySourceClass,
    GunActuationType,
    MaterialPropertyBasis,
    WeldPowerType,
    WeldPulseType,
)

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class RevisionMetadataRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_number: int = Field(ge=1)
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None = None
    evidence_reference_ids: list[int] = Field(default_factory=list)
    notes: str | None = None
    reason: str = Field(min_length=1)


class IdentityResponse(BaseModel):
    id: int
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------


class TemperaturePointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    temperature_c: float
    value: float


class MaterialPropertiesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    electrical_resistivity_ohm_m: float | None = None
    thermal_conductivity_w_mk: float | None = None
    specific_heat_j_kgk: float | None = None
    density_kg_m3: float | None = None
    solidus_c: float | None = None
    liquidus_c: float | None = None
    yield_strength_mpa: float | None = None
    tensile_strength_mpa: float | None = None
    hardness_hv: float | None = None
    resistivity_curve: list[TemperaturePointRequest] = Field(default_factory=list)
    conductivity_curve: list[TemperaturePointRequest] = Field(default_factory=list)
    specific_heat_curve: list[TemperaturePointRequest] = Field(default_factory=list)
    property_basis: MaterialPropertyBasis = MaterialPropertyBasis.REFERENCE_ONLY


class MaterialCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_id: str = Field(min_length=1, max_length=120)
    family: str = Field(min_length=1, max_length=120)
    grade: str = Field(min_length=1, max_length=160)
    form: str | None = None
    thickness_min_mm: float | None = Field(default=None, gt=0)
    thickness_max_mm: float | None = Field(default=None, gt=0)
    weldability_class: str | None = None
    contact_resistance_class: str | None = None
    properties: MaterialPropertiesRequest = Field(default_factory=MaterialPropertiesRequest)
    metadata: RevisionMetadataRequest


class MaterialIdentityResponse(IdentityResponse):
    material_id: str


class MaterialRevisionResponse(BaseModel):
    id: int
    engineering_material_id: int
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None
    family: str
    grade: str
    form: str | None
    thickness_min_mm: float | None
    thickness_max_mm: float | None
    weldability_class: str | None
    contact_resistance_class: str | None
    properties_snapshot: dict[str, Any]
    evidence_reference_ids: list[int]
    notes: str | None
    content_hash: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: str
    software_version: str
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime


class MaterialCreateResponse(BaseModel):
    identity: MaterialIdentityResponse
    revision: MaterialRevisionResponse


# ---------------------------------------------------------------------------
# Coating
# ---------------------------------------------------------------------------


class CoatingCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coating_id: str = Field(min_length=1, max_length=120)
    family: str = Field(min_length=1, max_length=120)
    designation: str = Field(min_length=1, max_length=160)
    nominal_thickness_um: float | None = Field(default=None, gt=0)
    electrical_contact_effect: str | None = None
    electrode_wear_effect: str | None = None
    metadata: RevisionMetadataRequest


class CoatingIdentityResponse(IdentityResponse):
    coating_id: str


class CoatingRevisionResponse(BaseModel):
    id: int
    engineering_coating_id: int
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None
    family: str
    designation: str
    nominal_thickness_um: float | None
    electrical_contact_effect: str | None
    electrode_wear_effect: str | None
    evidence_reference_ids: list[int]
    notes: str | None
    content_hash: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: str
    software_version: str
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime


class CoatingCreateResponse(BaseModel):
    identity: CoatingIdentityResponse
    revision: CoatingRevisionResponse


# ---------------------------------------------------------------------------
# Stack-Up
# ---------------------------------------------------------------------------


class StackLayerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=1)
    material_revision_id: int = Field(ge=1)
    thickness_mm: float = Field(gt=0)
    coating_revision_id: int | None = Field(default=None, ge=1)
    orientation: str | None = None


class StackUpCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stack_id: str = Field(min_length=1, max_length=120)
    adhesive_present: bool = False
    interface_notes: str | None = None
    layers: list[StackLayerRequest] = Field(min_length=2)
    metadata: RevisionMetadataRequest


class StackUpIdentityResponse(IdentityResponse):
    stack_id: str


class StackLayerResponse(BaseModel):
    id: int
    stack_up_revision_id: int
    sequence: int
    material_revision_id: int
    coating_revision_id: int | None
    thickness_mm: float
    orientation: str | None
    created_at: datetime


class StackUpRevisionResponse(BaseModel):
    id: int
    engineering_stack_up_id: int
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None
    adhesive_present: bool
    interface_notes: str | None
    evidence_reference_ids: list[int]
    content_hash: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: str
    software_version: str
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime
    layers: list[StackLayerResponse] = Field(default_factory=list)


class StackUpCreateResponse(BaseModel):
    identity: StackUpIdentityResponse
    revision: StackUpRevisionResponse


# ---------------------------------------------------------------------------
# Electrode
# ---------------------------------------------------------------------------


class ElectrodeCapGeometryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    face_geometry: ElectrodeFaceGeometry
    face_diameter_mm: float = Field(gt=0)
    tip_diameter_mm: float | None = Field(default=None, gt=0)
    radius_mm: float | None = Field(default=None, gt=0)
    included_angle_deg: float | None = None


class ElectrodeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    electrode_id: str = Field(min_length=1, max_length=120)
    cap_geometry: ElectrodeCapGeometryRequest
    material_designation: str = Field(min_length=1, max_length=120)
    cooling_channel_diameter_mm: float | None = None
    recommended_flow_lpm: float | None = None
    recommended_max_inlet_temp_c: float | None = None
    metadata: RevisionMetadataRequest


class ElectrodeIdentityResponse(IdentityResponse):
    electrode_id: str


class ElectrodeRevisionResponse(BaseModel):
    id: int
    engineering_electrode_id: int
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None
    face_geometry: ElectrodeFaceGeometry
    face_diameter_mm: float
    tip_diameter_mm: float | None
    radius_mm: float | None
    included_angle_deg: float | None
    material_designation: str
    cooling_channel_diameter_mm: float | None
    recommended_flow_lpm: float | None
    recommended_max_inlet_temp_c: float | None
    evidence_reference_ids: list[int]
    notes: str | None
    content_hash: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: str
    software_version: str
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime


class ElectrodeCreateResponse(BaseModel):
    identity: ElectrodeIdentityResponse
    revision: ElectrodeRevisionResponse


# ---------------------------------------------------------------------------
# Weld Gun
# ---------------------------------------------------------------------------


class TransformerSpecRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transformer_id: str = Field(min_length=1)
    power_type: WeldPowerType
    rated_power_kva: float | None = None
    max_secondary_current_ka: float | None = None
    nominal_frequency_hz: float | None = None


class ControllerSpecRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controller_id: str = Field(min_length=1)
    manufacturer: str | None = None
    model: str | None = None
    supports_current_feedback: bool = False
    supports_voltage_feedback: bool = False
    supports_force_feedback: bool = False
    supports_displacement_feedback: bool = False


class CoolingConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nominal_flow_lpm: float | None = None
    inlet_temperature_c: float | None = None
    circuit_count: int | None = Field(default=None, ge=1)


class WeldGunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gun_id: str = Field(min_length=1, max_length=120)
    actuation_type: GunActuationType
    max_force_kn: float = Field(gt=0)
    throat_depth_mm: float | None = Field(default=None, gt=0)
    max_opening_mm: float | None = Field(default=None, gt=0)
    transformer: TransformerSpecRequest | None = None
    controller: ControllerSpecRequest | None = None
    cooling: CoolingConfigRequest | None = None
    metadata: RevisionMetadataRequest


class WeldGunIdentityResponse(IdentityResponse):
    gun_id: str


class WeldGunRevisionResponse(BaseModel):
    id: int
    engineering_weld_gun_id: int
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None
    actuation_type: GunActuationType
    max_force_kn: float
    throat_depth_mm: float | None
    max_opening_mm: float | None
    transformer_snapshot: dict[str, Any] | None
    controller_snapshot: dict[str, Any] | None
    cooling_snapshot: dict[str, Any] | None
    evidence_reference_ids: list[int]
    notes: str | None
    content_hash: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: str
    software_version: str
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime


class WeldGunCreateResponse(BaseModel):
    identity: WeldGunIdentityResponse
    revision: WeldGunRevisionResponse


# ---------------------------------------------------------------------------
# Weld Schedule
# ---------------------------------------------------------------------------


class WeldPulseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=1)
    pulse_type: WeldPulseType
    current_ka: float | None = Field(default=None, ge=0)
    duration_cycles: float = Field(default=0.0, ge=0)
    force_kn: float | None = Field(default=None, gt=0)


class WeldScheduleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schedule_id: str = Field(min_length=1, max_length=120)
    squeeze_cycles: float = Field(default=0.0, ge=0)
    hold_cycles: float = Field(default=0.0, ge=0)
    nominal_force_kn: float | None = Field(default=None, gt=0)
    process_metadata: dict[str, Any] = Field(default_factory=dict)
    pulses: list[WeldPulseRequest] = Field(min_length=1)
    metadata: RevisionMetadataRequest


class WeldScheduleIdentityResponse(IdentityResponse):
    schedule_id: str


class WeldPulseResponse(BaseModel):
    id: int
    engineering_weld_schedule_revision_id: int
    sequence_number: int
    pulse_type: WeldPulseType
    current_ka: float | None
    duration_cycles: float
    force_kn: float | None
    created_at: datetime


class WeldScheduleRevisionResponse(BaseModel):
    id: int
    engineering_weld_schedule_id: int
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    supersedes_revision_id: int | None
    squeeze_cycles: float
    hold_cycles: float
    nominal_force_kn: float | None
    process_metadata: dict[str, Any] | None
    evidence_reference_ids: list[int]
    notes: str | None
    content_hash: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: str
    software_version: str
    created_by_actor_id: str
    created_by_user_id: int | None
    created_at: datetime
    pulses: list[WeldPulseResponse] = Field(default_factory=list)


class WeldScheduleCreateResponse(BaseModel):
    identity: WeldScheduleIdentityResponse
    revision: WeldScheduleRevisionResponse
