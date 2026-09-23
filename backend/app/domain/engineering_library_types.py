"""Governed engineering-library domain contracts.

CE-02A foundation only:
- no persistence
- no database authority
- no engineering calculation authority
- immutable revision-oriented domain inputs
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class EngineeringLibraryLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"


class EngineeringLibrarySourceClass(StrEnum):
    SOURCE_BACKED = "SOURCE_BACKED"
    EXPERIMENTAL = "EXPERIMENTAL"
    FIELD_CALIBRATED = "FIELD_CALIBRATED"
    DERIVED = "DERIVED"
    PROPOSED = "PROPOSED"
    UNRESOLVED = "UNRESOLVED"


class MaterialPropertyBasis(StrEnum):
    CONSTANT = "CONSTANT"
    TEMPERATURE_DEPENDENT = "TEMPERATURE_DEPENDENT"
    RANGE = "RANGE"
    REFERENCE_ONLY = "REFERENCE_ONLY"


class ElectrodeFaceGeometry(StrEnum):
    FLAT = "FLAT"
    DOME = "DOME"
    RADIUS = "RADIUS"
    TRUNCATED_CONE = "TRUNCATED_CONE"
    CUSTOM = "CUSTOM"


class WeldPowerType(StrEnum):
    AC = "AC"
    MFDC = "MFDC"
    DC = "DC"
    CAPACITOR_DISCHARGE = "CAPACITOR_DISCHARGE"
    OTHER = "OTHER"


class GunActuationType(StrEnum):
    SERVO = "SERVO"
    PNEUMATIC = "PNEUMATIC"
    HYDRAULIC = "HYDRAULIC"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


class WeldPulseType(StrEnum):
    PREHEAT = "PREHEAT"
    WELD = "WELD"
    COOL = "COOL"
    POSTHEAT = "POSTHEAT"
    TEMPER = "TEMPER"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True, slots=True)
class EngineeringLibraryRevisionMetadata:
    revision_number: int
    lifecycle_status: EngineeringLibraryLifecycleStatus
    source_class: EngineeringLibrarySourceClass
    created_by_actor_id: str
    evidence_reference_ids: tuple[int, ...] = ()
    supersedes_revision_id: int | None = None
    created_by_user_id: int | None = None
    schema_version: str = "1"
    canonicalization_version: str = "1"
    hash_algorithm: str = "sha256"
    software_version: str = ""

    def __post_init__(self) -> None:
        if self.revision_number <= 0:
            raise ValueError("revision_number must be positive")
        if not self.created_by_actor_id.strip():
            raise ValueError("created_by_actor_id must be non-empty")
        if self.supersedes_revision_id is not None and self.supersedes_revision_id <= 0:
            raise ValueError("supersedes_revision_id must be positive")
        if any(reference_id <= 0 for reference_id in self.evidence_reference_ids):
            raise ValueError("evidence_reference_ids must contain positive ids")


@dataclass(frozen=True, slots=True)
class TemperaturePropertyPoint:
    temperature_c: float
    value: float


@dataclass(frozen=True, slots=True)
class MaterialIdentity:
    material_id: str
    family: str
    grade: str
    form: str | None = None

    def __post_init__(self) -> None:
        if not self.material_id.strip():
            raise ValueError("material_id must be non-empty")
        if not self.family.strip():
            raise ValueError("family must be non-empty")
        if not self.grade.strip():
            raise ValueError("grade must be non-empty")


@dataclass(frozen=True, slots=True)
class MaterialPropertySet:
    electrical_resistivity_ohm_m: float | None = None
    thermal_conductivity_w_mk: float | None = None
    specific_heat_j_kgk: float | None = None
    density_kg_m3: float | None = None
    solidus_c: float | None = None
    liquidus_c: float | None = None
    yield_strength_mpa: float | None = None
    tensile_strength_mpa: float | None = None
    hardness_hv: float | None = None
    resistivity_curve: tuple[TemperaturePropertyPoint, ...] = ()
    conductivity_curve: tuple[TemperaturePropertyPoint, ...] = ()
    specific_heat_curve: tuple[TemperaturePropertyPoint, ...] = ()
    property_basis: MaterialPropertyBasis = MaterialPropertyBasis.REFERENCE_ONLY


@dataclass(frozen=True, slots=True)
class MaterialRevisionDraft:
    identity: MaterialIdentity
    metadata: EngineeringLibraryRevisionMetadata
    properties: MaterialPropertySet
    thickness_min_mm: float | None = None
    thickness_max_mm: float | None = None
    weldability_class: str | None = None
    contact_resistance_class: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.thickness_min_mm is not None and self.thickness_min_mm <= 0:
            raise ValueError("thickness_min_mm must be positive")
        if self.thickness_max_mm is not None and self.thickness_max_mm <= 0:
            raise ValueError("thickness_max_mm must be positive")
        if (
            self.thickness_min_mm is not None
            and self.thickness_max_mm is not None
            and self.thickness_min_mm > self.thickness_max_mm
        ):
            raise ValueError("thickness_min_mm cannot exceed thickness_max_mm")


@dataclass(frozen=True, slots=True)
class CoatingIdentity:
    coating_id: str
    family: str
    designation: str

    def __post_init__(self) -> None:
        if not self.coating_id.strip():
            raise ValueError("coating_id must be non-empty")
        if not self.family.strip():
            raise ValueError("family must be non-empty")
        if not self.designation.strip():
            raise ValueError("designation must be non-empty")


@dataclass(frozen=True, slots=True)
class CoatingRevisionDraft:
    identity: CoatingIdentity
    metadata: EngineeringLibraryRevisionMetadata
    nominal_thickness_um: float | None = None
    electrical_contact_effect: str | None = None
    electrode_wear_effect: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class StackLayerDraft:
    sequence: int
    material_revision_id: int
    thickness_mm: float
    coating_revision_id: int | None = None
    orientation: str | None = None

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise ValueError("sequence must be positive")
        if self.material_revision_id <= 0:
            raise ValueError("material_revision_id must be positive")
        if self.thickness_mm <= 0:
            raise ValueError("thickness_mm must be positive")
        if self.coating_revision_id is not None and self.coating_revision_id <= 0:
            raise ValueError("coating_revision_id must be positive")


@dataclass(frozen=True, slots=True)
class StackUpRevisionDraft:
    stack_id: str
    metadata: EngineeringLibraryRevisionMetadata
    layers: tuple[StackLayerDraft, ...]
    adhesive_present: bool = False
    interface_notes: str | None = None

    def __post_init__(self) -> None:
        if not self.stack_id.strip():
            raise ValueError("stack_id must be non-empty")
        if len(self.layers) < 2:
            raise ValueError("stack-up requires at least two layers")
        sequences = tuple(layer.sequence for layer in self.layers)
        if sequences != tuple(range(1, len(self.layers) + 1)):
            raise ValueError("stack layer sequence must be contiguous starting at 1")


@dataclass(frozen=True, slots=True)
class ElectrodeCapGeometry:
    face_geometry: ElectrodeFaceGeometry
    face_diameter_mm: float
    tip_diameter_mm: float | None = None
    radius_mm: float | None = None
    included_angle_deg: float | None = None

    def __post_init__(self) -> None:
        if self.face_diameter_mm <= 0:
            raise ValueError("face_diameter_mm must be positive")
        if self.tip_diameter_mm is not None and self.tip_diameter_mm <= 0:
            raise ValueError("tip_diameter_mm must be positive")
        if self.radius_mm is not None and self.radius_mm <= 0:
            raise ValueError("radius_mm must be positive")


@dataclass(frozen=True, slots=True)
class ElectrodeRevisionDraft:
    electrode_id: str
    metadata: EngineeringLibraryRevisionMetadata
    cap_geometry: ElectrodeCapGeometry
    material_designation: str
    cooling_channel_diameter_mm: float | None = None
    recommended_flow_lpm: float | None = None
    recommended_max_inlet_temp_c: float | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.electrode_id.strip():
            raise ValueError("electrode_id must be non-empty")
        if not self.material_designation.strip():
            raise ValueError("material_designation must be non-empty")


@dataclass(frozen=True, slots=True)
class TransformerSpecification:
    transformer_id: str
    power_type: WeldPowerType
    rated_power_kva: float | None = None
    max_secondary_current_ka: float | None = None
    nominal_frequency_hz: float | None = None

    def __post_init__(self) -> None:
        if not self.transformer_id.strip():
            raise ValueError("transformer_id must be non-empty")


@dataclass(frozen=True, slots=True)
class ControllerSpecification:
    controller_id: str
    manufacturer: str | None = None
    model: str | None = None
    supports_current_feedback: bool = False
    supports_voltage_feedback: bool = False
    supports_force_feedback: bool = False
    supports_displacement_feedback: bool = False


@dataclass(frozen=True, slots=True)
class CoolingConfiguration:
    nominal_flow_lpm: float | None = None
    inlet_temperature_c: float | None = None
    circuit_count: int | None = None

    def __post_init__(self) -> None:
        if self.nominal_flow_lpm is not None and self.nominal_flow_lpm < 0:
            raise ValueError("nominal_flow_lpm cannot be negative")
        if self.circuit_count is not None and self.circuit_count <= 0:
            raise ValueError("circuit_count must be positive")


@dataclass(frozen=True, slots=True)
class WeldGunRevisionDraft:
    gun_id: str
    metadata: EngineeringLibraryRevisionMetadata
    actuation_type: GunActuationType
    max_force_kn: float
    transformer: TransformerSpecification | None = None
    controller: ControllerSpecification | None = None
    cooling: CoolingConfiguration | None = None
    throat_depth_mm: float | None = None
    max_opening_mm: float | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.gun_id.strip():
            raise ValueError("gun_id must be non-empty")
        if self.max_force_kn <= 0:
            raise ValueError("max_force_kn must be positive")


@dataclass(frozen=True, slots=True)
class WeldPulseDraft:
    sequence: int
    pulse_type: WeldPulseType
    current_ka: float | None = None
    duration_cycles: float = 0.0
    force_kn: float | None = None

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise ValueError("sequence must be positive")
        if self.duration_cycles < 0:
            raise ValueError("duration_cycles cannot be negative")
        if self.current_ka is not None and self.current_ka < 0:
            raise ValueError("current_ka cannot be negative")
        if self.force_kn is not None and self.force_kn <= 0:
            raise ValueError("force_kn must be positive")


@dataclass(frozen=True, slots=True)
class WeldScheduleRevisionDraft:
    schedule_id: str
    metadata: EngineeringLibraryRevisionMetadata
    pulses: tuple[WeldPulseDraft, ...]
    squeeze_cycles: float = 0.0
    hold_cycles: float = 0.0
    nominal_force_kn: float | None = None
    process_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.schedule_id.strip():
            raise ValueError("schedule_id must be non-empty")
        if not self.pulses:
            raise ValueError("weld schedule requires at least one pulse")
        sequences = tuple(pulse.sequence for pulse in self.pulses)
        if sequences != tuple(range(1, len(self.pulses) + 1)):
            raise ValueError("pulse sequence must be contiguous starting at 1")
        if self.squeeze_cycles < 0:
            raise ValueError("squeeze_cycles cannot be negative")
        if self.hold_cycles < 0:
            raise ValueError("hold_cycles cannot be negative")
        if self.nominal_force_kn is not None and self.nominal_force_kn <= 0:
            raise ValueError("nominal_force_kn must be positive")
