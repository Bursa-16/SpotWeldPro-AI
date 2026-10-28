"""
energy_aggregation.py — Multi-spot energy aggregation domain logic.

P1 scope — MASTER-ENERGY-OPTIMIZATION-01.

Hierarchy:
  weld_point → weld_group → part → annual

CONTRACT:
  - All inputs in kJ/spot; outputs in kJ or kWh as labeled.
  - None propagates: if any required input is None, the aggregate is None.
  - double-counting guard: each weld point is counted exactly once.
  - Cost figures carry the same disclaimer as compute_spot_cost_aggregation().
  - This module has no database access, no I/O.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.domain.energy_window import (
    EnergyWindowEstimate,
    EnergyWindowStatus,
    EnergyValidationStatus,
    compute_energy_window,
)


_COST_DISCLAIMER = (
    "THEORETICAL ENERGY DIFFERENCE ONLY. "
    "Excludes grid-side efficiency losses, auxiliary loads, machine utilization, "
    "production scrap, rework, electrode costs, and cycle-time variation. "
    "Not a verified production saving."
)


@dataclass
class WeldPointEnergySpec:
    """Input specification for one weld point in a multi-spot aggregation."""
    point_code: str
    group_name: str                     # used to cluster into WeldGroupSummary
    e_current_kj: Optional[float]
    e_min_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_max_kj: Optional[float]
    validation_status: EnergyValidationStatus = EnergyValidationStatus.NOT_VALIDATED
    validation_note: Optional[str] = None


@dataclass
class WeldPointAggrRow:
    """Per-point window result with its input spec, for table display."""
    spec: WeldPointEnergySpec
    window: EnergyWindowEstimate


@dataclass
class WeldGroupSummary:
    """Aggregated energy summary for one weld group."""
    group_name: str
    point_count: int

    # Totals (kJ): None if any contributing point lacks the value
    e_current_total_kj: Optional[float]
    e_ideal_total_kj: Optional[float]
    delta_total_kj: Optional[float]       # signed; e_current - e_ideal
    e_excess_total_kj: Optional[float]    # max(0, delta) per point, summed

    # Per-point status counts
    points_in_window: int
    points_below_min: int
    points_above_max: int
    points_not_established: int
    points_quality_risk: int              # e_current < e_ideal


@dataclass
class MultiSpotAggregation:
    """Full multi-spot aggregation result.

    Groups → part → annual hierarchy.
    """
    # Per-point detail rows (in input order)
    rows: list[WeldPointAggrRow]

    # Per-group summaries
    groups: list[WeldGroupSummary]

    # Part-level totals
    part_point_count: int
    part_e_current_total_kj: Optional[float]
    part_e_ideal_total_kj: Optional[float]
    part_delta_total_kj: Optional[float]        # signed
    part_e_excess_total_kj: Optional[float]     # max(0, delta) per point, summed
    part_points_in_window: int
    part_points_below_min: int
    part_points_above_max: int
    part_points_not_established: int
    part_points_quality_risk: int

    # Annual (requires production_volume and tariffs)
    annual_e_excess_total_kwh: Optional[float]
    annual_cost_eur: Optional[float]
    annual_cost_usd: Optional[float]

    # Pareto: top-N weld points by energy excess (descending)
    pareto_by_excess: list[WeldPointAggrRow]

    # Disclaimer always present
    disclaimer: str

    # Computation provenance
    production_volume_annual: Optional[int]
    tariff_eur_per_kwh: Optional[float]
    tariff_usd_per_kwh: Optional[float]


def aggregate_multi_spot(
    specs: list[WeldPointEnergySpec],
    production_volume_annual: Optional[int] = None,
    tariff_eur_per_kwh: Optional[float] = None,
    tariff_usd_per_kwh: Optional[float] = None,
    pareto_top_n: int = 10,
) -> MultiSpotAggregation:
    """Aggregate energy windows for multiple weld points.

    specs                    : ordered list of weld-point energy specifications.
    production_volume_annual : parts/year for annual cost rollup (None → skip cost).
    tariff_eur_per_kwh       : EUR electricity tariff (None → skip cost).
    tariff_usd_per_kwh       : USD electricity tariff (None → skip cost).
    pareto_top_n             : how many top-excess rows to include in pareto list.

    Raises ValueError for invalid tariff / volume inputs when provided.
    """
    if production_volume_annual is not None and production_volume_annual <= 0:
        raise ValueError(f"production_volume_annual must be positive, got {production_volume_annual!r}")
    if tariff_eur_per_kwh is not None and (not math.isfinite(tariff_eur_per_kwh) or tariff_eur_per_kwh <= 0):
        raise ValueError(f"tariff_eur_per_kwh must be positive, got {tariff_eur_per_kwh!r}")
    if tariff_usd_per_kwh is not None and (not math.isfinite(tariff_usd_per_kwh) or tariff_usd_per_kwh <= 0):
        raise ValueError(f"tariff_usd_per_kwh must be positive, got {tariff_usd_per_kwh!r}")

    # ── Evaluate per-point windows ─────────────────────────────────────────
    rows: list[WeldPointAggrRow] = []
    for spec in specs:
        window = compute_energy_window(
            e_current_kj=spec.e_current_kj,
            e_min_kj=spec.e_min_kj,
            e_ideal_kj=spec.e_ideal_kj,
            e_max_kj=spec.e_max_kj,
            validation_status=spec.validation_status,
            validation_note=spec.validation_note,
        )
        rows.append(WeldPointAggrRow(spec=spec, window=window))

    # ── Group summaries ────────────────────────────────────────────────────
    group_map: dict[str, list[WeldPointAggrRow]] = {}
    for row in rows:
        group_map.setdefault(row.spec.group_name, []).append(row)

    groups: list[WeldGroupSummary] = []
    for group_name, group_rows in group_map.items():
        g = _summarize_group(group_name, group_rows)
        groups.append(g)

    # ── Part-level totals ──────────────────────────────────────────────────
    part_e_current_total_kj: Optional[float] = _safe_sum(
        [r.window.e_current_kj for r in rows]
    )
    part_e_ideal_total_kj: Optional[float] = _safe_sum(
        [r.window.e_ideal_kj for r in rows]
    )
    part_delta_total_kj: Optional[float] = (
        part_e_current_total_kj - part_e_ideal_total_kj
        if part_e_current_total_kj is not None and part_e_ideal_total_kj is not None
        else None
    )
    # excess per point then sum (avoids negative deltas canceling positive ones)
    per_point_excess = [r.window.e_excess_potential_kj for r in rows]
    part_e_excess_total_kj: Optional[float] = _safe_sum(per_point_excess)

    part_points_in_window = sum(1 for r in rows if r.window.window_status == EnergyWindowStatus.IN_WINDOW)
    part_points_below_min = sum(1 for r in rows if r.window.window_status == EnergyWindowStatus.BELOW_MIN)
    part_points_above_max = sum(1 for r in rows if r.window.window_status == EnergyWindowStatus.ABOVE_MAX)
    part_points_not_established = sum(
        1 for r in rows if r.window.window_status == EnergyWindowStatus.NOT_ESTABLISHED
    )
    part_points_quality_risk = sum(1 for r in rows if r.window.quality_risk_flag)

    # ── Annual cost ────────────────────────────────────────────────────────
    annual_e_excess_total_kwh: Optional[float] = None
    annual_cost_eur: Optional[float] = None
    annual_cost_usd: Optional[float] = None

    if (
        part_e_excess_total_kj is not None
        and production_volume_annual is not None
    ):
        annual_e_excess_total_kwh = part_e_excess_total_kj / 3600.0 * production_volume_annual
        if tariff_eur_per_kwh is not None:
            annual_cost_eur = annual_e_excess_total_kwh * tariff_eur_per_kwh
        if tariff_usd_per_kwh is not None:
            annual_cost_usd = annual_e_excess_total_kwh * tariff_usd_per_kwh

    # ── Pareto (top-N by excess, descending) ──────────────────────────────
    sortable = [r for r in rows if r.window.e_excess_potential_kj is not None]
    sortable.sort(key=lambda r: r.window.e_excess_potential_kj or 0.0, reverse=True)
    pareto_by_excess = sortable[:pareto_top_n]

    return MultiSpotAggregation(
        rows=rows,
        groups=groups,
        part_point_count=len(rows),
        part_e_current_total_kj=part_e_current_total_kj,
        part_e_ideal_total_kj=part_e_ideal_total_kj,
        part_delta_total_kj=part_delta_total_kj,
        part_e_excess_total_kj=part_e_excess_total_kj,
        part_points_in_window=part_points_in_window,
        part_points_below_min=part_points_below_min,
        part_points_above_max=part_points_above_max,
        part_points_not_established=part_points_not_established,
        part_points_quality_risk=part_points_quality_risk,
        annual_e_excess_total_kwh=annual_e_excess_total_kwh,
        annual_cost_eur=annual_cost_eur,
        annual_cost_usd=annual_cost_usd,
        pareto_by_excess=pareto_by_excess,
        disclaimer=_COST_DISCLAIMER,
        production_volume_annual=production_volume_annual,
        tariff_eur_per_kwh=tariff_eur_per_kwh,
        tariff_usd_per_kwh=tariff_usd_per_kwh,
    )


def _safe_sum(values: list[Optional[float]]) -> Optional[float]:
    """Sum a list; returns None if any element is None."""
    if any(v is None for v in values):
        return None
    return sum(v for v in values if v is not None)


def _summarize_group(group_name: str, group_rows: list[WeldPointAggrRow]) -> WeldGroupSummary:
    e_current_total = _safe_sum([r.window.e_current_kj for r in group_rows])
    e_ideal_total = _safe_sum([r.window.e_ideal_kj for r in group_rows])
    delta_total = (
        e_current_total - e_ideal_total
        if e_current_total is not None and e_ideal_total is not None
        else None
    )
    per_point_excess = [r.window.e_excess_potential_kj for r in group_rows]
    e_excess_total = _safe_sum(per_point_excess)

    return WeldGroupSummary(
        group_name=group_name,
        point_count=len(group_rows),
        e_current_total_kj=e_current_total,
        e_ideal_total_kj=e_ideal_total,
        delta_total_kj=delta_total,
        e_excess_total_kj=e_excess_total,
        points_in_window=sum(1 for r in group_rows if r.window.window_status == EnergyWindowStatus.IN_WINDOW),
        points_below_min=sum(1 for r in group_rows if r.window.window_status == EnergyWindowStatus.BELOW_MIN),
        points_above_max=sum(1 for r in group_rows if r.window.window_status == EnergyWindowStatus.ABOVE_MAX),
        points_not_established=sum(1 for r in group_rows if r.window.window_status == EnergyWindowStatus.NOT_ESTABLISHED),
        points_quality_risk=sum(1 for r in group_rows if r.window.quality_risk_flag),
    )
