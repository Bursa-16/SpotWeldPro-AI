"""
energy.py — Pydantic schemas for Energy Intelligence API.

MASTER-ENERGY-OPTIMIZATION-01, P0 + P1 scope.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from app.domain.energy_window import (
    EnergyMethod,
    EnergyWindowStatus,
    EnergyValidationStatus,
)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class EnergyEstimateRequest(BaseModel):
    """Single-pulse I²Rt energy estimate request."""

    current_ka: float = Field(
        gt=0,
        le=100,
        description=(
            "RMS weld current in kA. "
            "This is the weld-controller setpoint (effective/RMS value), "
            "not peak current. Valid for AC and DC/MFDC controllers."
        ),
        examples=[8.3],
    )
    resistance_micro_ohm: float = Field(
        gt=0,
        le=10_000,
        description="Constant contact resistance in µΩ.",
        examples=[120.0],
    )
    weld_cycles: float = Field(
        gt=0,
        le=1_000,
        description="Number of weld cycles at frequency_hz.",
        examples=[16.0],
    )
    frequency_hz: float = Field(
        default=50.0,
        gt=0,
        le=10_000,
        description="Supply or converter frequency in Hz (default 50 Hz).",
        examples=[50.0],
    )


class EnergyWindowRequest(BaseModel):
    """Five-indicator energy window evaluation request.

    All energy values in kJ/spot. Omit e_min_kj, e_ideal_kj, e_max_kj
    when no validated process window is available — they default to None,
    which produces window_status=NOT_ESTABLISHED.
    """

    e_current_kj: Optional[float] = Field(
        default=None,
        ge=0,
        description="Company current energy per spot in kJ. None if not measured.",
        examples=[0.400],
    )
    e_min_kj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Validated minimum energy bound in kJ/spot. "
            "Must be supported by experimental evidence. "
            "Leave None if not established."
        ),
        examples=[0.280],
    )
    e_ideal_kj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Validated ideal (target) energy in kJ/spot. "
            "Must satisfy e_min ≤ e_ideal ≤ e_max. "
            "Leave None if not established."
        ),
        examples=[0.320],
    )
    e_max_kj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Validated maximum energy bound in kJ/spot. "
            "Must be supported by experimental evidence. "
            "Leave None if not established."
        ),
        examples=[0.420],
    )
    method: EnergyMethod = Field(
        default=EnergyMethod.I2RT,
        description="Method used to compute energy values.",
    )
    validation_status: EnergyValidationStatus = Field(
        default=EnergyValidationStatus.NOT_VALIDATED,
        description="Validation level of the supplied window bounds.",
    )
    validation_note: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Free-text provenance note for the window bounds.",
    )

    @model_validator(mode="after")
    def _check_window_ordering(self) -> "EnergyWindowRequest":
        e_min = self.e_min_kj
        e_ideal = self.e_ideal_kj
        e_max = self.e_max_kj
        if e_min is not None and e_max is not None and e_min > e_max:
            raise ValueError(f"e_min_kj ({e_min}) must be ≤ e_max_kj ({e_max})")
        if (
            e_min is not None
            and e_ideal is not None
            and e_max is not None
            and not (e_min <= e_ideal <= e_max)
        ):
            raise ValueError(
                f"e_ideal_kj ({e_ideal}) must satisfy e_min_kj ({e_min}) ≤ e_ideal ≤ e_max_kj ({e_max})"
            )
        return self


class CostIntelligenceRequest(BaseModel):
    """Theoretical cost aggregation request for a single weld point type.

    The endpoint applies the §6 formula:
        ΔE_annual_kWh = (e_current_kj − e_ideal_kj) × spots_per_part × volume / 3600
        cost_EUR = ΔE_annual_kWh × tariff_eur_per_kwh
    """

    e_current_kj: float = Field(
        gt=0,
        description="Company current energy per spot in kJ.",
        examples=[4.0],
    )
    e_ideal_kj: float = Field(
        gt=0,
        description="Validated ideal energy per spot in kJ.",
        examples=[3.2],
    )
    spots_per_part: int = Field(
        gt=0,
        le=10_000,
        description="Number of weld spots of this type per production part.",
        examples=[40],
    )
    production_volume_annual: int = Field(
        gt=0,
        le=10_000_000,
        description="Annual production volume in parts.",
        examples=[200_000],
    )
    tariff_eur_per_kwh: float = Field(
        gt=0,
        description="Industrial electricity tariff in EUR/kWh.",
        examples=[0.18],
    )
    tariff_usd_per_kwh: float = Field(
        gt=0,
        description="Industrial electricity tariff in USD/kWh.",
        examples=[0.19],
    )
    ideal_validation_status: EnergyValidationStatus = Field(
        default=EnergyValidationStatus.NOT_VALIDATED,
        description="Validation level of e_ideal_kj.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class EnergyI2RTResponse(BaseModel):
    """Response for a single I²Rt energy estimate."""

    energy_j: float
    energy_kj: float
    energy_wh: float
    energy_kwh: float
    time_s: float
    current_ka: float
    resistance_micro_ohm: float
    weld_cycles: float
    frequency_hz: float
    method: EnergyMethod
    assumptions: List[str]


class EnergyWindowResponse(BaseModel):
    """Five-indicator energy window evaluation response.

    All energy values in kJ/spot unless field name specifies otherwise.
    None means NOT_ESTABLISHED or not calculable from available inputs.
    """

    # Indicator A
    e_min_kj: Optional[float]
    # Indicator B
    e_ideal_kj: Optional[float]
    # Indicator C
    e_max_kj: Optional[float]
    # Indicator D
    e_current_kj: Optional[float]
    e_current_j: Optional[float]
    e_current_wh: Optional[float]
    e_current_kwh: Optional[float]
    # Indicator E
    delta_e_signed_kj: Optional[float]
    e_excess_potential_kj: Optional[float]

    # Margins
    e_margin_upper_kj: Optional[float]
    e_margin_lower_kj: Optional[float]

    # Status
    window_status: EnergyWindowStatus
    quality_risk_flag: bool
    out_of_window: bool

    # Provenance
    method: EnergyMethod
    validation_status: EnergyValidationStatus
    validation_note: Optional[str]
    assumptions: List[str]


class CostIntelligenceResult(BaseModel):
    """Theoretical energy difference and cost aggregation.

    IMPORTANT: The disclaimer field must be read before presenting any
    cost figure to end users or management.
    """

    # Inputs echoed back
    e_current_kj: float
    e_ideal_kj: float
    spots_per_part: int
    production_volume_annual: int
    tariff_eur_per_kwh: float
    tariff_usd_per_kwh: float

    # Per-spot
    delta_e_spot_kj: float
    delta_e_spot_kwh: float

    # Per-part
    delta_e_part_kj: float
    delta_e_part_kwh: float

    # Per 1 000 parts
    delta_e_per_1000_parts_kwh: float
    cost_diff_eur_per_1000_parts: float
    cost_diff_usd_per_1000_parts: float

    # Annual
    delta_e_annual_kwh: float
    cost_diff_eur_annual: float
    cost_diff_usd_annual: float

    # Provenance
    ideal_validation_status: EnergyValidationStatus
    disclaimer: str  # MUST be present and non-empty; always set by domain logic


# ---------------------------------------------------------------------------
# P1: Multi-spot aggregation schemas
# ---------------------------------------------------------------------------

class WeldPointEnergySpecIn(BaseModel):
    """One weld point spec for multi-spot aggregation request."""
    point_code: str = Field(min_length=1, max_length=100)
    group_name: str = Field(default="DEFAULT", min_length=1, max_length=100)
    e_current_kj: Optional[float] = Field(default=None, ge=0)
    e_min_kj: Optional[float] = Field(default=None, ge=0)
    e_ideal_kj: Optional[float] = Field(default=None, ge=0)
    e_max_kj: Optional[float] = Field(default=None, ge=0)
    validation_status: EnergyValidationStatus = EnergyValidationStatus.NOT_VALIDATED
    validation_note: Optional[str] = Field(default=None, max_length=500)


class MultiSpotAggregationRequest(BaseModel):
    """Multi-spot energy aggregation request."""
    points: List[WeldPointEnergySpecIn] = Field(min_length=1, max_length=500)
    production_volume_annual: Optional[int] = Field(default=None, gt=0, le=10_000_000)
    tariff_eur_per_kwh: Optional[float] = Field(default=None, gt=0)
    tariff_usd_per_kwh: Optional[float] = Field(default=None, gt=0)
    pareto_top_n: int = Field(default=10, ge=1, le=50)


class WeldPointWindowRow(BaseModel):
    """Per-point window result row in aggregation response."""
    point_code: str
    group_name: str
    e_current_kj: Optional[float]
    e_min_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_max_kj: Optional[float]
    delta_e_signed_kj: Optional[float]
    e_excess_potential_kj: Optional[float]
    window_status: EnergyWindowStatus
    quality_risk_flag: bool
    out_of_window: bool


class WeldGroupSummaryOut(BaseModel):
    """Group-level energy summary."""
    group_name: str
    point_count: int
    e_current_total_kj: Optional[float]
    e_ideal_total_kj: Optional[float]
    delta_total_kj: Optional[float]
    e_excess_total_kj: Optional[float]
    points_in_window: int
    points_below_min: int
    points_above_max: int
    points_not_established: int
    points_quality_risk: int


class MultiSpotAggregationResponse(BaseModel):
    """Full multi-spot aggregation response."""
    rows: List[WeldPointWindowRow]
    groups: List[WeldGroupSummaryOut]
    # Part totals
    part_point_count: int
    part_e_current_total_kj: Optional[float]
    part_e_ideal_total_kj: Optional[float]
    part_delta_total_kj: Optional[float]
    part_e_excess_total_kj: Optional[float]
    part_points_in_window: int
    part_points_below_min: int
    part_points_above_max: int
    part_points_not_established: int
    part_points_quality_risk: int
    # Annual
    annual_e_excess_total_kwh: Optional[float]
    annual_cost_eur: Optional[float]
    annual_cost_usd: Optional[float]
    # Pareto
    pareto_by_excess: List[WeldPointWindowRow]
    # Provenance
    disclaimer: str
    production_volume_annual: Optional[int]
    tariff_eur_per_kwh: Optional[float]
    tariff_usd_per_kwh: Optional[float]


# ---------------------------------------------------------------------------
# P1: Import validation schemas
# ---------------------------------------------------------------------------

class ImportPreviewRequest(BaseModel):
    """CSV import preview/validation request."""
    csv_text: str = Field(min_length=1, max_length=2_000_000,
                          description="Full CSV file content as UTF-8 text.")
    existing_point_codes: List[str] = Field(
        default_factory=list,
        description="Point codes already in DB for duplicate detection.",
    )


class CellErrorOut(BaseModel):
    row_number: int
    column: str
    raw_value: str
    error_type: str
    message: str


class ImportPreviewRowOut(BaseModel):
    row_number: int
    point_code: str
    group_name: str
    e_current_kj: Optional[float]
    e_min_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_max_kj: Optional[float]
    validation_note: Optional[str]
    accepted: bool
    row_errors: List[CellErrorOut]


class ImportPreviewResponse(BaseModel):
    """Result of import preview/validation."""
    total_rows: int
    accepted_count: int
    rejected_count: int
    formula_injection_detected: bool
    formula_injection_cells: List[str]
    duplicate_point_codes: List[str]
    missing_columns: List[str]
    errors: List[CellErrorOut]
    preview_rows: List[ImportPreviewRowOut]
    has_blocking_errors: bool


# ---------------------------------------------------------------------------
# P2-B: Scenario comparison schemas
# ---------------------------------------------------------------------------

class ScenarioPointIn(BaseModel):
    """One weld point with baseline and proposed energy values."""
    point_code: str = Field(min_length=1, max_length=100)
    group_name: str = Field(default="DEFAULT", min_length=1, max_length=100)
    e_min_kj: Optional[float] = Field(default=None, ge=0)
    e_ideal_kj: Optional[float] = Field(default=None, ge=0)
    e_max_kj: Optional[float] = Field(default=None, ge=0)
    validation_status: EnergyValidationStatus = EnergyValidationStatus.NOT_VALIDATED
    baseline_e_current_kj: Optional[float] = Field(default=None, ge=0)
    proposed_e_current_kj: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_window_ordering(self) -> "ScenarioPointIn":
        e_min, e_ideal, e_max = self.e_min_kj, self.e_ideal_kj, self.e_max_kj
        if e_min is not None and e_max is not None and e_min > e_max:
            raise ValueError(f"e_min_kj ({e_min}) must be ≤ e_max_kj ({e_max})")
        if e_min is not None and e_ideal is not None and e_max is not None:
            if not (e_min <= e_ideal <= e_max):
                raise ValueError(
                    f"e_ideal_kj ({e_ideal}) must satisfy e_min ({e_min}) ≤ e_ideal ≤ e_max ({e_max})"
                )
        return self


class ScenarioComparisonRequest(BaseModel):
    """Request body for POST /energy/scenario/compare."""
    points: List[ScenarioPointIn] = Field(min_length=1, max_length=500)
    production_volume_annual: Optional[int] = Field(default=None, gt=0, le=10_000_000)
    tariff_eur_per_kwh: Optional[float] = Field(default=None, ge=0)
    tariff_usd_per_kwh: Optional[float] = Field(default=None, ge=0)


class ScenarioPointResultOut(BaseModel):
    point_code: str
    group_name: str
    e_min_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_max_kj: Optional[float]
    baseline_e_current_kj: Optional[float]
    baseline_window_status: EnergyWindowStatus
    baseline_delta_e_kj: Optional[float]
    baseline_excess_kj: Optional[float]
    baseline_quality_risk: bool
    proposed_e_current_kj: Optional[float]
    proposed_window_status: EnergyWindowStatus
    proposed_delta_e_kj: Optional[float]
    proposed_excess_kj: Optional[float]
    proposed_quality_risk: bool
    e_change_kj: Optional[float]
    excess_change_kj: Optional[float]
    quality_improved: bool
    quality_degraded: bool
    warnings: List[str]


class ScenarioGroupSummaryOut(BaseModel):
    group_name: str
    point_count: int
    baseline_e_total_kj: Optional[float]
    proposed_e_total_kj: Optional[float]
    e_reduction_kj: Optional[float]
    baseline_in_window: int
    proposed_in_window: int
    improved_count: int
    degraded_count: int


class ScenarioComparisonResponse(BaseModel):
    """Full scenario comparison response."""
    points: List[ScenarioPointResultOut]
    groups: List[ScenarioGroupSummaryOut]
    part_baseline_e_total_kj: Optional[float]
    part_proposed_e_total_kj: Optional[float]
    part_e_reduction_kj: Optional[float]
    annual_e_reduction_kwh: Optional[float]
    annual_cost_saving_eur: Optional[float]
    annual_cost_saving_usd: Optional[float]
    baseline_points_in_window: int
    proposed_points_in_window: int
    total_improved: int
    total_degraded: int
    production_volume_annual: Optional[int]
    tariff_eur_per_kwh: Optional[float]
    tariff_usd_per_kwh: Optional[float]
    disclaimer: str


# ---------------------------------------------------------------------------
# P2-D: Dashboard schemas
# ---------------------------------------------------------------------------

class DashboardRequest(BaseModel):
    """Request body for POST /energy/dashboard."""
    points: List[WeldPointEnergySpecIn] = Field(min_length=1, max_length=500)
    production_volume_annual: Optional[int] = Field(default=None, gt=0, le=10_000_000)
    tariff_eur_per_kwh: Optional[float] = Field(default=None, gt=0)
    tariff_usd_per_kwh: Optional[float] = Field(default=None, gt=0)
    pareto_top_n: int = Field(default=20, ge=1, le=100)
    sensitivity_volumes: Optional[List[int]] = Field(
        default=None,
        max_length=10,
        description="Custom production volumes for sensitivity matrix (default: 5 preset values).",
    )
    sensitivity_tariffs_eur: Optional[List[float]] = Field(
        default=None,
        max_length=10,
        description="Custom EUR tariffs for sensitivity matrix (default: 5 preset values).",
    )


class ParetoDetailRowOut(BaseModel):
    """One row of the enhanced Pareto — all points sorted by excess energy desc."""
    point_code: str
    group_name: str
    e_current_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_excess_kj: Optional[float]
    pct_of_total_excess: Optional[float]
    cumulative_pct: Optional[float]
    window_status: EnergyWindowStatus


class FinancialSummaryOut(BaseModel):
    """Hierarchical financial summary: per-spot → per-part → per-1000 → annual."""
    avg_excess_per_spot_kj: Optional[float]
    avg_excess_per_spot_kwh: Optional[float]
    part_excess_kj: Optional[float]
    part_excess_kwh: Optional[float]
    per_1000_parts_excess_kwh: Optional[float]
    cost_eur_per_1000_parts: Optional[float]
    cost_usd_per_1000_parts: Optional[float]
    annual_excess_kwh: Optional[float]
    annual_cost_eur: Optional[float]
    annual_cost_usd: Optional[float]
    production_volume_annual: Optional[int]
    tariff_eur_per_kwh: Optional[float]
    tariff_usd_per_kwh: Optional[float]


class SensitivityRowOut(BaseModel):
    """One cell of the sensitivity matrix (production_volume × tariff_EUR)."""
    production_volume: int
    tariff_eur_per_kwh: float
    annual_excess_kwh: Optional[float]
    cost_eur: Optional[float]
    cost_usd: Optional[float]


class DashboardResponse(MultiSpotAggregationResponse):
    """P2-D dashboard response: full aggregation + Pareto details + financial + sensitivity."""
    pareto_detailed: List[ParetoDetailRowOut]
    financial: FinancialSummaryOut
    sensitivity: List[SensitivityRowOut]
    dashboard_disclaimer: str
