"""Weld-point / part / weld-map / engineering-change domain contracts.

CE-03A foundation only:
- no persistence
- no database authority
- no engineering calculation authority
- immutable revision-oriented domain inputs
- exact engineering library revision references are mandatory;
  "latest" is never implicitly resolved
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EngineeringChangeReason(StrEnum):
    QUALITY_ISSUE = "QUALITY_ISSUE"
    SMALL_NUGGET = "SMALL_NUGGET"
    EXPULSION = "EXPULSION"
    ELECTRODE_WEAR = "ELECTRODE_WEAR"
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    SUPPLIER_CHANGE = "SUPPLIER_CHANGE"
    THICKNESS_CHANGE = "THICKNESS_CHANGE"
    COATING_CHANGE = "COATING_CHANGE"
    MACHINE_CHANGE = "MACHINE_CHANGE"
    PROCESS_OPTIMIZATION = "PROCESS_OPTIMIZATION"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    OTHER = "OTHER"


class EngineeringChangeStatus(StrEnum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    VALIDATION = "VALIDATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Product / Part identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ProductIdentity:
    """Top-level product / vehicle programme context."""

    product_id: str
    product_name: str
    project_code: str | None = None

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.product_name.strip():
            raise ValueError("product_name must be non-empty")


@dataclass(frozen=True, slots=True)
class PartIdentity:
    """Part number anchored to a product."""

    part_number: str
    product_id: str
    part_description: str | None = None

    def __post_init__(self) -> None:
        if not self.part_number.strip():
            raise ValueError("part_number must be non-empty")
        if not self.product_id.strip():
            raise ValueError("product_id must be non-empty")


@dataclass(frozen=True, slots=True)
class PartRevision:
    """Exact revision of a part — mandatory before any ECR or weld-point revision.

    revision_id is a positive integer primary key that uniquely identifies
    this exact part revision in the governed part library; it is never
    resolved lazily to "current" or "latest".
    """

    revision_id: int
    part_number: str
    revision_label: str
    drawing_reference: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.revision_id <= 0:
            raise ValueError("revision_id must be positive")
        if not self.part_number.strip():
            raise ValueError("part_number must be non-empty")
        if not self.revision_label.strip():
            raise ValueError("revision_label must be non-empty")


# ---------------------------------------------------------------------------
# Manufacturing location
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ManufacturingLocationContext:
    """Physical manufacturing cell context."""

    plant: str
    line: str | None = None
    station: str | None = None
    robot: str | None = None
    gun_mount: str | None = None

    def __post_init__(self) -> None:
        if not self.plant.strip():
            raise ValueError("plant must be non-empty")


# ---------------------------------------------------------------------------
# Weld point identity and geometry
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WeldPointIdentity:
    """Stable identifier for a weld point, anchored to a part."""

    weld_point_id: str
    part_number: str
    product_id: str
    point_description: str | None = None

    def __post_init__(self) -> None:
        if not self.weld_point_id.strip():
            raise ValueError("weld_point_id must be non-empty")
        if not self.part_number.strip():
            raise ValueError("part_number must be non-empty")
        if not self.product_id.strip():
            raise ValueError("product_id must be non-empty")


@dataclass(frozen=True, slots=True)
class WeldPointLocation:
    """3-D nominal location and approach vector in part co-ordinates."""

    x_mm: float
    y_mm: float
    z_mm: float
    normal_x: float | None = None
    normal_y: float | None = None
    normal_z: float | None = None

    def __post_init__(self) -> None:
        for name, value in (("x_mm", self.x_mm), ("y_mm", self.y_mm), ("z_mm", self.z_mm)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if (self.normal_x is None) != (self.normal_y is None) or (self.normal_y is None) != (self.normal_z is None):
            raise ValueError("normal vector components must all be supplied or all be omitted")
        if self.normal_x is not None:
            for name, v in (("normal_x", self.normal_x), ("normal_y", self.normal_y), ("normal_z", self.normal_z)):
                if not math.isfinite(v):  # type: ignore[arg-type]
                    raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True, slots=True)
class WeldPointEngineeringContext:
    """Exact engineering library revision references for a weld point.

    Every field is mandatory; "latest" is never implicitly resolved.
    All IDs are positive integer primary keys in their respective
    governed library tables.
    """

    stack_up_revision_id: int
    electrode_revision_id: int
    weld_gun_revision_id: int
    weld_schedule_revision_id: int

    def __post_init__(self) -> None:
        for name, value in (
            ("stack_up_revision_id", self.stack_up_revision_id),
            ("electrode_revision_id", self.electrode_revision_id),
            ("weld_gun_revision_id", self.weld_gun_revision_id),
            ("weld_schedule_revision_id", self.weld_schedule_revision_id),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")


@dataclass(frozen=True, slots=True)
class WeldPointRevisionDraft:
    """Draft input for creating or revising a weld point record."""

    identity: WeldPointIdentity
    part_revision_id: int
    engineering_context: WeldPointEngineeringContext
    location: WeldPointLocation | None = None
    manufacturing_location: ManufacturingLocationContext | None = None
    criticality: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.part_revision_id <= 0:
            raise ValueError("part_revision_id must be positive")


# ---------------------------------------------------------------------------
# Weld map
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WeldMapPoint:
    """One weld point entry in a weld map revision."""

    weld_point_id: str
    part_revision_id: int
    engineering_context: WeldPointEngineeringContext
    location: WeldPointLocation | None = None

    def __post_init__(self) -> None:
        if not self.weld_point_id.strip():
            raise ValueError("weld_point_id must be non-empty")
        if self.part_revision_id <= 0:
            raise ValueError("part_revision_id must be positive")


@dataclass(frozen=True, slots=True)
class WeldMapIdentity:
    """Stable identifier for a weld map."""

    weld_map_id: str
    product_id: str
    part_number: str

    def __post_init__(self) -> None:
        if not self.weld_map_id.strip():
            raise ValueError("weld_map_id must be non-empty")
        if not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.part_number.strip():
            raise ValueError("part_number must be non-empty")


@dataclass(frozen=True, slots=True)
class WeldMapRevisionDraft:
    """Draft input for creating or revising a weld map.

    Duplicate weld_point_id values are forbidden within a single revision.
    """

    identity: WeldMapIdentity
    revision_number: int
    points: tuple[WeldMapPoint, ...]
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.revision_number <= 0:
            raise ValueError("revision_number must be positive")
        if not self.points:
            raise ValueError("weld map must contain at least one point")
        ids = [p.weld_point_id for p in self.points]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate weld_point_id values are forbidden within a weld map revision")


# ---------------------------------------------------------------------------
# Weld parameter snapshot
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WeldPulseSnapshot:
    """Immutable snapshot of a single pulse within a weld parameter snapshot."""

    sequence: int
    pulse_type: str
    current_ka: float | None = None
    duration_cycles: float = 0.0
    force_kn: float | None = None

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise ValueError("sequence must be positive")
        if not self.pulse_type.strip():
            raise ValueError("pulse_type must be non-empty")
        if self.duration_cycles < 0:
            raise ValueError("duration_cycles cannot be negative")
        if self.current_ka is not None and (not math.isfinite(self.current_ka) or self.current_ka < 0):
            raise ValueError("current_ka must be a non-negative finite number")
        if self.force_kn is not None and (not math.isfinite(self.force_kn) or self.force_kn <= 0):
            raise ValueError("force_kn must be a positive finite number")


@dataclass(frozen=True, slots=True)
class WeldParameterSnapshot:
    """Immutable point-in-time snapshot of weld process parameters.

    Used as old/new state in engineering change records.  Both snapshots
    are independent; neither references the other.
    """

    weld_current_ka: float
    weld_cycles: float
    electrode_force_kn: float
    squeeze_cycles: float
    hold_cycles: float
    pulses: tuple[WeldPulseSnapshot, ...]
    electrode_tip_diameter_mm: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.weld_current_ka) or self.weld_current_ka <= 0:
            raise ValueError("weld_current_ka must be a positive finite number")
        if not math.isfinite(self.weld_cycles) or self.weld_cycles <= 0:
            raise ValueError("weld_cycles must be positive")
        if not math.isfinite(self.electrode_force_kn) or self.electrode_force_kn <= 0:
            raise ValueError("electrode_force_kn must be positive")
        if not math.isfinite(self.squeeze_cycles) or self.squeeze_cycles < 0:
            raise ValueError("squeeze_cycles cannot be negative")
        if not math.isfinite(self.hold_cycles) or self.hold_cycles < 0:
            raise ValueError("hold_cycles cannot be negative")
        if not self.pulses:
            raise ValueError("at least one pulse is required in a parameter snapshot")
        if self.electrode_tip_diameter_mm is not None and (not math.isfinite(self.electrode_tip_diameter_mm) or self.electrode_tip_diameter_mm <= 0):
            raise ValueError("electrode_tip_diameter_mm must be a positive finite number")
        sequences = tuple(p.sequence for p in self.pulses)
        if sequences != tuple(range(1, len(self.pulses) + 1)):
            raise ValueError("pulse sequence must be contiguous starting at 1")


# ---------------------------------------------------------------------------
# Validation evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ValidationEvidence:
    """Evidence record attached to an engineering change request."""

    test_type: str
    sample_quantity: int
    result: str
    evidence_date: str
    conducted_by: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.test_type.strip():
            raise ValueError("test_type must be non-empty")
        if self.sample_quantity <= 0:
            raise ValueError("sample_quantity must be positive")
        if not self.result.strip():
            raise ValueError("result must be non-empty")
        if not self.evidence_date.strip():
            raise ValueError("evidence_date must be non-empty")
        if not self.conducted_by.strip():
            raise ValueError("conducted_by must be non-empty")


# ---------------------------------------------------------------------------
# Approval record
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """Single approver decision on an engineering change request."""

    approver_actor_id: str
    approval_date: str
    approved: bool
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.approver_actor_id.strip():
            raise ValueError("approver_actor_id must be non-empty")
        if not self.approval_date.strip():
            raise ValueError("approval_date must be non-empty")


# ---------------------------------------------------------------------------
# Release metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ReleaseMetadata:
    """Release record attached to an approved engineering change."""

    release_number: str
    release_date: str
    released_by_actor_id: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.release_number.strip():
            raise ValueError("release_number must be non-empty")
        if not self.release_date.strip():
            raise ValueError("release_date must be non-empty")
        if not self.released_by_actor_id.strip():
            raise ValueError("released_by_actor_id must be non-empty")


# ---------------------------------------------------------------------------
# Engineering change identity and request draft
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EngineeringChangeIdentity:
    """Stable identifier for an engineering change request."""

    change_id: str
    product_id: str
    part_number: str
    weld_point_id: str

    def __post_init__(self) -> None:
        if not self.change_id.strip():
            raise ValueError("change_id must be non-empty")
        if not self.product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not self.part_number.strip():
            raise ValueError("part_number must be non-empty")
        if not self.weld_point_id.strip():
            raise ValueError("weld_point_id must be non-empty")


@dataclass(frozen=True, slots=True)
class EngineeringChangeRequestDraft:
    """Draft input for creating an engineering change request.

    Constraints:
    - part_revision_id is mandatory and must be positive (exact revision,
      never "latest")
    - weld_point_id is mandatory and must be non-empty (exact point)
    - old_parameter_snapshot and new_parameter_snapshot are independent
      immutable objects; they must not be the same object
    - exact engineering library revision references in old/new snapshots
      are not cross-validated here — that is the service layer's
      responsibility
    """

    identity: EngineeringChangeIdentity
    part_revision_id: int
    requester_actor_id: str
    request_date: str
    reason: EngineeringChangeReason
    owner_actor_id: str
    old_parameter_snapshot: WeldParameterSnapshot
    new_parameter_snapshot: WeldParameterSnapshot
    status: EngineeringChangeStatus = EngineeringChangeStatus.DRAFT
    reason_detail: str | None = None
    problem_reference: str | None = None
    project_context: str | None = None
    validation_evidence: tuple[ValidationEvidence, ...] = ()
    approvals: tuple[ApprovalRecord, ...] = ()
    release_metadata: ReleaseMetadata | None = None

    def __post_init__(self) -> None:
        if self.part_revision_id <= 0:
            raise ValueError("part_revision_id must be positive")
        if not self.requester_actor_id.strip():
            raise ValueError("requester_actor_id must be non-empty")
        if not self.request_date.strip():
            raise ValueError("request_date must be non-empty")
        if not self.owner_actor_id.strip():
            raise ValueError("owner_actor_id must be non-empty")
        if self.old_parameter_snapshot is self.new_parameter_snapshot:
            raise ValueError(
                "old_parameter_snapshot and new_parameter_snapshot must be independent objects"
            )
