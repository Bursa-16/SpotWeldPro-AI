"""
scenario_comparison.py — Baseline vs proposed scenario evaluation for multi-spot welding.

P2-B — MASTER-ENERGY-OPTIMIZATION-01.

DESIGN CONTRACT:
  1. This is a SCENARIO EVALUATION, NOT a validated optimisation.
     No nugget diameter, expulsion, or coating model is applied.
  2. For each weld point, two energy window evaluations are performed:
     baseline (current company practice) and proposed (candidate change).
  3. Window bounds (e_min, e_ideal, e_max) are shared between both scenarios —
     they represent the validated process envelope and do not change per scenario.
  4. Quality rank comparison uses a conservative ordering:
       IN_WINDOW < ABOVE_MAX < BELOW_MIN < E_CURRENT_ABSENT < NOT_ESTABLISHED
     (BELOW_MIN is ranked worse than ABOVE_MAX because it directly risks
     insufficient nugget formation.)
  5. Annual cost savings are theoretical — same disclaimer applies as §6 cost.
  6. No database access, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.energy_window import (
    EnergyValidationStatus,
    EnergyWindowStatus,
    compute_energy_window,
)

DISCLAIMER = (
    "SCENARIO EVALUATION ONLY — Not a validated optimisation. "
    "Results are theoretical comparisons of energy values. "
    "Nugget diameter, expulsion risk, indentation depth and coating "
    "requirements are not modelled. All proposed values require validated "
    "experimental confirmation before production implementation."
)

# Conservative quality rank: lower = better
_STATUS_RANK: dict[EnergyWindowStatus, int] = {
    EnergyWindowStatus.IN_WINDOW:        0,
    EnergyWindowStatus.ABOVE_MAX:        1,
    EnergyWindowStatus.BELOW_MIN:        2,
    EnergyWindowStatus.E_CURRENT_ABSENT: 3,
    EnergyWindowStatus.NOT_ESTABLISHED:  4,
}


# ---------------------------------------------------------------------------
# Input dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScenarioPointIn:
    point_code: str
    group_name: str = "DEFAULT"
    e_min_kj: Optional[float] = None
    e_ideal_kj: Optional[float] = None
    e_max_kj: Optional[float] = None
    validation_status: EnergyValidationStatus = EnergyValidationStatus.NOT_VALIDATED
    baseline_e_current_kj: Optional[float] = None
    proposed_e_current_kj: Optional[float] = None


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ScenarioPointResult:
    point_code: str
    group_name: str
    e_min_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_max_kj: Optional[float]
    # Baseline
    baseline_e_current_kj: Optional[float]
    baseline_window_status: EnergyWindowStatus
    baseline_delta_e_kj: Optional[float]
    baseline_excess_kj: Optional[float]
    baseline_quality_risk: bool
    # Proposed
    proposed_e_current_kj: Optional[float]
    proposed_window_status: EnergyWindowStatus
    proposed_delta_e_kj: Optional[float]
    proposed_excess_kj: Optional[float]
    proposed_quality_risk: bool
    # Cross-scenario deltas
    e_change_kj: Optional[float]       # proposed − baseline (negative = energy reduced)
    excess_change_kj: Optional[float]  # proposed_excess − baseline_excess (negative = improved)
    quality_improved: bool             # proposed rank < baseline rank
    quality_degraded: bool             # proposed rank > baseline rank
    warnings: list[str]


@dataclass
class ScenarioGroupSummary:
    group_name: str
    point_count: int
    baseline_e_total_kj: Optional[float]
    proposed_e_total_kj: Optional[float]
    e_reduction_kj: Optional[float]  # baseline − proposed; positive = less energy proposed
    baseline_in_window: int
    proposed_in_window: int
    improved_count: int
    degraded_count: int


@dataclass
class ScenarioComparisonResult:
    points: list[ScenarioPointResult]
    groups: list[ScenarioGroupSummary]
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
# Helpers
# ---------------------------------------------------------------------------

def _safe_sub(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return None if (a is None or b is None) else a - b


def _accum(total: Optional[float], val: Optional[float]) -> Optional[float]:
    """Accumulate val into total; propagates None if either is None."""
    if total is None or val is None:
        return None
    return total + val


# ---------------------------------------------------------------------------
# Domain function
# ---------------------------------------------------------------------------

def compare_scenarios(
    points: list[ScenarioPointIn],
    production_volume_annual: Optional[int] = None,
    tariff_eur_per_kwh: Optional[float] = None,
    tariff_usd_per_kwh: Optional[float] = None,
) -> ScenarioComparisonResult:
    """Evaluate baseline vs proposed energy for each weld point.

    Returns per-point, per-group, and part-level comparison metrics.
    Annual cost savings are computed when production_volume_annual and tariffs
    are supplied.

    This is a SCENARIO EVALUATION — see module docstring for constraints.
    """
    point_results: list[ScenarioPointResult] = []

    for sp in points:
        base = compute_energy_window(
            e_current_kj=sp.baseline_e_current_kj,
            e_min_kj=sp.e_min_kj,
            e_ideal_kj=sp.e_ideal_kj,
            e_max_kj=sp.e_max_kj,
            validation_status=sp.validation_status,
        )
        prop = compute_energy_window(
            e_current_kj=sp.proposed_e_current_kj,
            e_min_kj=sp.e_min_kj,
            e_ideal_kj=sp.e_ideal_kj,
            e_max_kj=sp.e_max_kj,
            validation_status=sp.validation_status,
        )

        e_change = _safe_sub(prop.e_current_kj, base.e_current_kj)
        excess_change = _safe_sub(prop.e_excess_potential_kj, base.e_excess_potential_kj)

        base_rank = _STATUS_RANK.get(base.window_status, 4)
        prop_rank = _STATUS_RANK.get(prop.window_status, 4)

        warnings: list[str] = []
        if prop.window_status == EnergyWindowStatus.ABOVE_MAX:
            warnings.append(
                f"{sp.point_code}: proposed energy exceeds E_max — expulsion risk possible"
            )
        if prop.window_status == EnergyWindowStatus.BELOW_MIN:
            warnings.append(
                f"{sp.point_code}: proposed energy below E_min — insufficient nugget risk"
            )
        elif prop.quality_risk_flag:
            warnings.append(
                f"{sp.point_code}: proposed energy below E_ideal — quality risk flag"
            )

        point_results.append(ScenarioPointResult(
            point_code=sp.point_code,
            group_name=sp.group_name,
            e_min_kj=sp.e_min_kj,
            e_ideal_kj=sp.e_ideal_kj,
            e_max_kj=sp.e_max_kj,
            baseline_e_current_kj=base.e_current_kj,
            baseline_window_status=base.window_status,
            baseline_delta_e_kj=base.delta_e_signed_kj,
            baseline_excess_kj=base.e_excess_potential_kj,
            baseline_quality_risk=base.quality_risk_flag,
            proposed_e_current_kj=prop.e_current_kj,
            proposed_window_status=prop.window_status,
            proposed_delta_e_kj=prop.delta_e_signed_kj,
            proposed_excess_kj=prop.e_excess_potential_kj,
            proposed_quality_risk=prop.quality_risk_flag,
            e_change_kj=e_change,
            excess_change_kj=excess_change,
            quality_improved=(prop_rank < base_rank),
            quality_degraded=(prop_rank > base_rank),
            warnings=warnings,
        ))

    # ── Group aggregation ──────────────────────────────────────────────────
    group_map: dict[str, list[ScenarioPointResult]] = {}
    for pr in point_results:
        group_map.setdefault(pr.group_name, []).append(pr)

    groups: list[ScenarioGroupSummary] = []
    for gname, gpts in group_map.items():
        base_total: Optional[float] = 0.0
        prop_total: Optional[float] = 0.0
        for gp in gpts:
            base_total = _accum(base_total, gp.baseline_e_current_kj)
            prop_total = _accum(prop_total, gp.proposed_e_current_kj)
        groups.append(ScenarioGroupSummary(
            group_name=gname,
            point_count=len(gpts),
            baseline_e_total_kj=base_total,
            proposed_e_total_kj=prop_total,
            e_reduction_kj=_safe_sub(base_total, prop_total),
            baseline_in_window=sum(1 for gp in gpts if gp.baseline_window_status == EnergyWindowStatus.IN_WINDOW),
            proposed_in_window=sum(1 for gp in gpts if gp.proposed_window_status == EnergyWindowStatus.IN_WINDOW),
            improved_count=sum(1 for gp in gpts if gp.quality_improved),
            degraded_count=sum(1 for gp in gpts if gp.quality_degraded),
        ))

    # ── Part-level aggregation ─────────────────────────────────────────────
    part_base: Optional[float] = 0.0
    part_prop: Optional[float] = 0.0
    for pr in point_results:
        part_base = _accum(part_base, pr.baseline_e_current_kj)
        part_prop = _accum(part_prop, pr.proposed_e_current_kj)

    part_reduction = _safe_sub(part_base, part_prop)

    # ── Annual cost savings ────────────────────────────────────────────────
    annual_reduction_kwh: Optional[float] = None
    annual_saving_eur: Optional[float] = None
    annual_saving_usd: Optional[float] = None

    if (
        part_reduction is not None
        and production_volume_annual is not None
        and production_volume_annual > 0
    ):
        annual_reduction_kwh = (part_reduction / 3600.0) * production_volume_annual
        if tariff_eur_per_kwh is not None and tariff_eur_per_kwh >= 0:
            annual_saving_eur = annual_reduction_kwh * tariff_eur_per_kwh
        if tariff_usd_per_kwh is not None and tariff_usd_per_kwh >= 0:
            annual_saving_usd = annual_reduction_kwh * tariff_usd_per_kwh

    return ScenarioComparisonResult(
        points=point_results,
        groups=groups,
        part_baseline_e_total_kj=part_base,
        part_proposed_e_total_kj=part_prop,
        part_e_reduction_kj=part_reduction,
        annual_e_reduction_kwh=annual_reduction_kwh,
        annual_cost_saving_eur=annual_saving_eur,
        annual_cost_saving_usd=annual_saving_usd,
        baseline_points_in_window=sum(
            1 for pr in point_results if pr.baseline_window_status == EnergyWindowStatus.IN_WINDOW
        ),
        proposed_points_in_window=sum(
            1 for pr in point_results if pr.proposed_window_status == EnergyWindowStatus.IN_WINDOW
        ),
        total_improved=sum(1 for pr in point_results if pr.quality_improved),
        total_degraded=sum(1 for pr in point_results if pr.quality_degraded),
        production_volume_annual=production_volume_annual,
        tariff_eur_per_kwh=tariff_eur_per_kwh,
        tariff_usd_per_kwh=tariff_usd_per_kwh,
        disclaimer=DISCLAIMER,
    )
