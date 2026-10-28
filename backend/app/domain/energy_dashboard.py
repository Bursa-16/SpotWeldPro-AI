"""
energy_dashboard.py — P2-D Energy & Financial Intelligence Dashboard domain logic.

Adds on top of P1 multi-spot aggregation (energy_aggregation.py):
  1. Enhanced Pareto with per-point percentages and cumulative %.
  2. Detailed financial summary: per-spot, per-part, per-1000-parts, annual in kJ + kWh.
  3. Sensitivity analysis matrix: annual excess kwh and costs across volume × tariff_EUR.

CONTRACT:
  - All inputs in kJ/spot; outputs in kJ or kWh as labeled.
  - None propagates through all calculations.
  - NOT_ESTABLISHED is preserved; values are never fabricated.
  - Sensitivity only computes when part_excess_kj is not None.
  - No database access, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.energy_aggregation import WeldPointAggrRow

_DASHBOARD_DISCLAIMER = (
    "THEORETICAL EXCESS ENERGY ONLY — NOT a verified electricity or financial saving. "
    "Values represent E_current minus validated E_ideal per weld point. "
    "Grid-side electricity consumption includes transformer efficiency losses, "
    "auxiliary loads, electrode cooling, machine utilization, and production scrap "
    "not modelled here. "
    "Financial figures require independent energy metering and engineering validation "
    "before use in production decisions."
)

_DEFAULT_SENSITIVITY_VOLUMES: list[int] = [50_000, 100_000, 200_000, 500_000, 1_000_000]
_DEFAULT_SENSITIVITY_TARIFFS_EUR: list[float] = [0.10, 0.15, 0.20, 0.25, 0.30]


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------

@dataclass
class ParetoDetailRow:
    """Single row of the enhanced Pareto (all points sorted by excess desc)."""
    point_code: str
    group_name: str
    e_current_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_excess_kj: Optional[float]
    pct_of_total_excess: Optional[float]   # 0–100; None when total_excess == 0
    cumulative_pct: Optional[float]        # running sum; None when total_excess == 0
    window_status: str                     # EnergyWindowStatus.value


@dataclass
class FinancialSummary:
    """Hierarchical financial summary: per-spot → per-part → per-1000 → annual."""
    # Per-spot (average of all points that have a calculable excess)
    avg_excess_per_spot_kj: Optional[float]
    avg_excess_per_spot_kwh: Optional[float]
    # Per-part (sum of all per-point excesses)
    part_excess_kj: Optional[float]
    part_excess_kwh: Optional[float]
    # Per 1 000 parts
    per_1000_parts_excess_kwh: Optional[float]
    cost_eur_per_1000_parts: Optional[float]
    cost_usd_per_1000_parts: Optional[float]
    # Annual
    annual_excess_kwh: Optional[float]
    annual_cost_eur: Optional[float]
    annual_cost_usd: Optional[float]
    # Echoed inputs
    production_volume_annual: Optional[int]
    tariff_eur_per_kwh: Optional[float]
    tariff_usd_per_kwh: Optional[float]


@dataclass
class SensitivityRow:
    """One cell of the sensitivity matrix (production_volume × tariff_eur)."""
    production_volume: int
    tariff_eur_per_kwh: float
    annual_excess_kwh: Optional[float]
    cost_eur: Optional[float]
    cost_usd: Optional[float]  # requires tariff_usd_per_kwh from request


@dataclass
class DashboardExtras:
    """Extra outputs produced by P2-D beyond the standard P1 aggregation."""
    pareto_detailed: list[ParetoDetailRow]
    financial: FinancialSummary
    sensitivity: list[SensitivityRow]
    disclaimer: str


# ---------------------------------------------------------------------------
# Pareto computation
# ---------------------------------------------------------------------------

def compute_pareto_detailed(aggr_rows: list[WeldPointAggrRow]) -> list[ParetoDetailRow]:
    """Compute per-point excess with Pareto percentages and cumulative %."""
    result: list[ParetoDetailRow] = []
    for r in aggr_rows:
        result.append(ParetoDetailRow(
            point_code=r.spec.point_code,
            group_name=r.spec.group_name,
            e_current_kj=r.window.e_current_kj,
            e_ideal_kj=r.window.e_ideal_kj,
            e_excess_kj=r.window.e_excess_potential_kj,
            pct_of_total_excess=None,
            cumulative_pct=None,
            window_status=r.window.window_status.value,
        ))

    # Sort: highest excess first; None last
    result.sort(key=lambda r: (r.e_excess_kj is None, -(r.e_excess_kj or 0.0)))

    total_excess = sum(r.e_excess_kj for r in result if r.e_excess_kj is not None)
    cumulative = 0.0
    for r in result:
        if r.e_excess_kj is not None and total_excess > 0:
            pct = r.e_excess_kj / total_excess * 100.0
            cumulative += pct
            r.pct_of_total_excess = round(pct, 2)
            r.cumulative_pct = round(min(cumulative, 100.0), 2)
        else:
            r.pct_of_total_excess = 0.0
            r.cumulative_pct = round(min(cumulative, 100.0), 2)

    return result


# ---------------------------------------------------------------------------
# Financial summary
# ---------------------------------------------------------------------------

def compute_financial_summary(
    part_excess_kj: Optional[float],
    production_volume_annual: Optional[int],
    tariff_eur_per_kwh: Optional[float],
    tariff_usd_per_kwh: Optional[float],
    all_excess_values: list[Optional[float]],
) -> FinancialSummary:
    """Compute hierarchical financial summary from part-level excess."""
    valid = [e for e in all_excess_values if e is not None]
    n = len(valid)

    avg_kj = sum(valid) / n if n > 0 else None
    avg_kwh = avg_kj / 3600.0 if avg_kj is not None else None

    part_kwh = part_excess_kj / 3600.0 if part_excess_kj is not None else None

    per_1000_kwh = part_kwh * 1_000.0 if part_kwh is not None else None
    cost_eur_1000 = (
        per_1000_kwh * tariff_eur_per_kwh
        if per_1000_kwh is not None and tariff_eur_per_kwh is not None
        else None
    )
    cost_usd_1000 = (
        per_1000_kwh * tariff_usd_per_kwh
        if per_1000_kwh is not None and tariff_usd_per_kwh is not None
        else None
    )

    annual_kwh = (
        part_kwh * production_volume_annual
        if part_kwh is not None and production_volume_annual is not None
        else None
    )
    annual_eur = (
        annual_kwh * tariff_eur_per_kwh
        if annual_kwh is not None and tariff_eur_per_kwh is not None
        else None
    )
    annual_usd = (
        annual_kwh * tariff_usd_per_kwh
        if annual_kwh is not None and tariff_usd_per_kwh is not None
        else None
    )

    return FinancialSummary(
        avg_excess_per_spot_kj=avg_kj,
        avg_excess_per_spot_kwh=avg_kwh,
        part_excess_kj=part_excess_kj,
        part_excess_kwh=part_kwh,
        per_1000_parts_excess_kwh=per_1000_kwh,
        cost_eur_per_1000_parts=cost_eur_1000,
        cost_usd_per_1000_parts=cost_usd_1000,
        annual_excess_kwh=annual_kwh,
        annual_cost_eur=annual_eur,
        annual_cost_usd=annual_usd,
        production_volume_annual=production_volume_annual,
        tariff_eur_per_kwh=tariff_eur_per_kwh,
        tariff_usd_per_kwh=tariff_usd_per_kwh,
    )


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------

def compute_sensitivity(
    part_excess_kj: Optional[float],
    tariff_usd_per_kwh: Optional[float],
    volumes: Optional[list[int]] = None,
    tariffs_eur: Optional[list[float]] = None,
) -> list[SensitivityRow]:
    """Compute sensitivity matrix: annual excess kWh and costs at volume × tariff_EUR."""
    vols = volumes if volumes else _DEFAULT_SENSITIVITY_VOLUMES
    tariffs = tariffs_eur if tariffs_eur else _DEFAULT_SENSITIVITY_TARIFFS_EUR

    rows: list[SensitivityRow] = []
    for vol in vols:
        for t_eur in tariffs:
            if part_excess_kj is not None:
                annual_kwh = (part_excess_kj / 3600.0) * vol
                cost_eur = annual_kwh * t_eur
                cost_usd = (
                    annual_kwh * tariff_usd_per_kwh
                    if tariff_usd_per_kwh is not None
                    else None
                )
            else:
                annual_kwh = None
                cost_eur = None
                cost_usd = None
            rows.append(SensitivityRow(
                production_volume=vol,
                tariff_eur_per_kwh=t_eur,
                annual_excess_kwh=annual_kwh,
                cost_eur=cost_eur,
                cost_usd=cost_usd,
            ))
    return rows


# ---------------------------------------------------------------------------
# Combined extras computation
# ---------------------------------------------------------------------------

def compute_dashboard_extras(
    aggr_rows: list[WeldPointAggrRow],
    part_excess_kj: Optional[float],
    production_volume_annual: Optional[int],
    tariff_eur_per_kwh: Optional[float],
    tariff_usd_per_kwh: Optional[float],
    sensitivity_volumes: Optional[list[int]] = None,
    sensitivity_tariffs_eur: Optional[list[float]] = None,
) -> DashboardExtras:
    """Compute all P2-D extras: Pareto + financial + sensitivity."""
    pareto = compute_pareto_detailed(aggr_rows)

    all_excesses = [r.window.e_excess_potential_kj for r in aggr_rows]
    financial = compute_financial_summary(
        part_excess_kj=part_excess_kj,
        production_volume_annual=production_volume_annual,
        tariff_eur_per_kwh=tariff_eur_per_kwh,
        tariff_usd_per_kwh=tariff_usd_per_kwh,
        all_excess_values=all_excesses,
    )

    sensitivity = compute_sensitivity(
        part_excess_kj=part_excess_kj,
        tariff_usd_per_kwh=tariff_usd_per_kwh,
        volumes=sensitivity_volumes,
        tariffs_eur=sensitivity_tariffs_eur,
    )

    return DashboardExtras(
        pareto_detailed=pareto,
        financial=financial,
        sensitivity=sensitivity,
        disclaimer=_DASHBOARD_DISCLAIMER,
    )
