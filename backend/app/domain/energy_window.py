"""
energy_window.py — Five-indicator energy intelligence for resistance spot welding.

P0 foundation — MASTER-ENERGY-OPTIMIZATION-01.

FIVE INDICATORS (TR/EN):
  A. E_min   — Hesaplanan Minimum Enerji    / Calculated Minimum Energy    [kJ/spot]
  B. E_ideal — Hesaplanan İdeal Enerji      / Calculated Ideal Energy      [kJ/spot]
  C. E_max   — Hesaplanan Maksimum Enerji   / Calculated Maximum Energy    [kJ/spot]
  D. E_current — Firmanın Mevcut Enerjisi   / Company Current Energy       [kJ/spot]
  E. ΔE      — Fark / Potansiyel Fazla      / Difference / Potential Excess [kJ/spot]

DESIGN CONTRACT — must hold for every call:
  1. E_min, E_ideal, E_max are NEVER invented or estimated here.
     If any window bound is None → window_status = NOT_ESTABLISHED.
  2. delta_e_signed and e_excess_potential are computed ONLY when both
     E_current and E_ideal are present; otherwise both are None.
  3. E_excess_potential = max(0, delta_e_signed) — never negative, never None
     when delta_e_signed is available.
  4. A negative delta (E_current < E_ideal) sets quality_risk_flag=True.
     It does NOT produce a non-zero E_excess_potential.
  5. Process-window status (IN_WINDOW / BELOW_MIN / ABOVE_MAX) requires
     E_min, E_max, and E_current to all be present.
  6. This module has no database access, no API dependencies, no I/O.

ENERGY METHOD (EnergyMethod enum):
  I2RT        — E = I_rms² × R × t with constant resistance (domain/energy.py).
  WAVEFORM    — E = ∫V(t)·I(t)dt (P2 scope; placeholder defined here for schema completeness).
  USER_ENTERED — Direct user-supplied energy value; no formula applied.

CURRENT TYPE DOCUMENTATION:
  current_ka in estimate functions is always the RMS (effective) value.
  For DC / MFDC: I_mean ≈ I_rms for quasi-constant current; same formula.
  For 50 Hz AC: the formula is valid only when current_ka is the controller RMS setpoint.
  See domain/energy.py module docstring for the full assumption statement.

COST AGGREGATION:
  compute_spot_cost_aggregation() performs the §6 verification example arithmetic.
  It is THEORETICAL — it states clearly that the result excludes grid-side efficiency,
  auxiliary loads, scrap, rework, and electrode effects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EnergyMethod(StrEnum):
    I2RT         = "I2RT"          # E = I_rms² × R × t; constant resistance
    WAVEFORM     = "WAVEFORM"      # E = ∫V(t)·I(t)dt; P2 scope
    USER_ENTERED = "USER_ENTERED"  # direct user-supplied value


class EnergyWindowStatus(StrEnum):
    NOT_ESTABLISHED  = "NOT_ESTABLISHED"   # window bounds not available
    IN_WINDOW        = "IN_WINDOW"         # E_min ≤ E_current ≤ E_max
    BELOW_MIN        = "BELOW_MIN"         # E_current < E_min
    ABOVE_MAX        = "ABOVE_MAX"         # E_current > E_max
    E_CURRENT_ABSENT = "E_CURRENT_ABSENT"  # window bounds present but no current energy


class EnergyValidationStatus(StrEnum):
    NOT_VALIDATED  = "NOT_VALIDATED"   # default; no supporting evidence recorded
    HYPOTHESIS     = "HYPOTHESIS"      # supported by limited or indirect evidence
    VALIDATED      = "VALIDATED"       # supported by documented experimental evidence


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class EnergyI2RTResult:
    """Result from a single I²Rt energy estimate."""
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
    assumptions: list[str]


@dataclass
class EnergyWindowEstimate:
    """Five-indicator energy window result.

    All energy values in kJ/spot unless noted.
    Fields may be None when evidence is absent (NOT_ESTABLISHED contract).
    """
    # ── Indicator A: Minimum energy ──────────────────────────────────────────
    e_min_kj: Optional[float]               # None → NOT_ESTABLISHED

    # ── Indicator B: Ideal energy ────────────────────────────────────────────
    e_ideal_kj: Optional[float]             # None → NOT_ESTABLISHED

    # ── Indicator C: Maximum energy ──────────────────────────────────────────
    e_max_kj: Optional[float]               # None → NOT_ESTABLISHED

    # ── Indicator D: Company current energy ──────────────────────────────────
    e_current_kj: Optional[float]           # None when not provided

    # ── Indicator E: Difference / potential excess ───────────────────────────
    delta_e_signed_kj: Optional[float]      # E_current − E_ideal; None when either absent
    e_excess_potential_kj: Optional[float]  # max(0, delta); None when delta absent

    # ── Derived margins (None when bounds or current absent) ─────────────────
    e_margin_upper_kj: Optional[float]      # E_max − E_current
    e_margin_lower_kj: Optional[float]      # E_current − E_min

    # ── Window and quality status ─────────────────────────────────────────────
    window_status: EnergyWindowStatus
    quality_risk_flag: bool                 # True when E_current < E_ideal

    # ── Process-window violation ─────────────────────────────────────────────
    out_of_window: bool                     # True when BELOW_MIN or ABOVE_MAX

    # ── Provenance ────────────────────────────────────────────────────────────
    method: EnergyMethod
    validation_status: EnergyValidationStatus
    validation_note: Optional[str]

    # ── Assumptions (always populated) ────────────────────────────────────────
    assumptions: list[str] = field(default_factory=list)

    # ── Unit helpers (derived from kJ) ────────────────────────────────────────
    e_current_j: Optional[float] = None
    e_current_wh: Optional[float] = None
    e_current_kwh: Optional[float] = None


@dataclass
class SpotCostAggregation:
    """Theoretical energy difference and cost aggregation for a single weld point.

    DISCLAIMER: This is a theoretical energy difference only.
    It excludes grid-side efficiency losses, auxiliary loads, machine utilization,
    production scrap, rework, electrode costs, and cycle-time effects.
    It is NOT a verified production saving.
    """
    # ── Inputs ─────────────────────────────────────────────────────────────────
    e_current_kj: float
    e_ideal_kj: float
    production_volume_annual: int
    tariff_eur_per_kwh: float
    tariff_usd_per_kwh: float
    spots_per_part: int

    # ── Per-spot ───────────────────────────────────────────────────────────────
    delta_e_spot_kj: float          # E_current − E_ideal per spot
    delta_e_spot_kwh: float

    # ── Per-part ───────────────────────────────────────────────────────────────
    delta_e_part_kj: float          # delta_e_spot_kj × spots_per_part
    delta_e_part_kwh: float

    # ── Per 1000 parts ─────────────────────────────────────────────────────────
    delta_e_per_1000_parts_kwh: float
    cost_diff_eur_per_1000_parts: float
    cost_diff_usd_per_1000_parts: float

    # ── Annual ─────────────────────────────────────────────────────────────────
    delta_e_annual_kwh: float
    cost_diff_eur_annual: float
    cost_diff_usd_annual: float

    # ── Provenance ─────────────────────────────────────────────────────────────
    disclaimer: str
    ideal_validation_status: EnergyValidationStatus


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

_NOT_ESTABLISHED_NOTE = (
    "E_min, E_ideal and E_max are NOT ESTABLISHED. "
    "Validated experimental data or a physically defensible process-window model "
    "is required before these bounds can be stated. "
    "Using I²Rt or lobe-model estimates as window bounds without experimental "
    "validation is not acceptable engineering practice."
)

_COST_DISCLAIMER = (
    "THEORETICAL ENERGY DIFFERENCE ONLY. "
    "This figure represents the arithmetic difference between E_current and E_ideal "
    "at the electrode side. It excludes: grid-side efficiency losses, transformer and "
    "cable losses, auxiliary and standby loads, machine utilization rate, production "
    "scrap and rework effects, electrode wear cost, and cycle-time variation. "
    "It is NOT a verified production saving and must not be presented as such."
)


def compute_energy_i2rt(
    current_ka: float,
    resistance_micro_ohm: float,
    weld_cycles: float,
    frequency_hz: float = 50.0,
) -> EnergyI2RTResult:
    """Compute electrode-side energy via E = I_rms² × R × t.

    current_ka          : RMS weld current in kA (controller setpoint, not peak).
    resistance_micro_ohm: constant contact resistance in µΩ.
    weld_cycles         : number of cycles at frequency_hz.
    frequency_hz        : supply / converter frequency in Hz.

    Raises ValueError for non-positive inputs.
    """
    if not math.isfinite(current_ka) or current_ka <= 0:
        raise ValueError(f"current_ka must be a positive finite number, got {current_ka!r}")
    if not math.isfinite(resistance_micro_ohm) or resistance_micro_ohm <= 0:
        raise ValueError(f"resistance_micro_ohm must be positive, got {resistance_micro_ohm!r}")
    if not math.isfinite(weld_cycles) or weld_cycles <= 0:
        raise ValueError(f"weld_cycles must be positive, got {weld_cycles!r}")
    if not math.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError(f"frequency_hz must be positive, got {frequency_hz!r}")

    current_a = current_ka * 1000.0           # kA → A (RMS)
    resistance_ohm = resistance_micro_ohm * 1e-6  # µΩ → Ω
    time_s = weld_cycles / frequency_hz

    energy_j = (current_a ** 2) * resistance_ohm * time_s
    energy_kj = energy_j / 1000.0
    energy_wh = energy_j / 3600.0
    energy_kwh = energy_wh / 1000.0

    return EnergyI2RTResult(
        energy_j=energy_j,
        energy_kj=energy_kj,
        energy_wh=energy_wh,
        energy_kwh=energy_kwh,
        time_s=time_s,
        current_ka=current_ka,
        resistance_micro_ohm=resistance_micro_ohm,
        weld_cycles=weld_cycles,
        frequency_hz=frequency_hz,
        method=EnergyMethod.I2RT,
        assumptions=[
            "current_ka is RMS (effective) current — standard weld-controller setpoint",
            "The formula E = I_rms² × R × t is valid for DC, MFDC, and 50 Hz AC "
            "when current_ka is the RMS value",
            f"Contact resistance is constant at {resistance_micro_ohm} µΩ "
            "across the full weld duration (single-value R; dynamic variation ignored)",
            f"Weld duration: {weld_cycles} cycles at {frequency_hz} Hz = {time_s:.4f} s",
            "Single-pulse calculation; multi-pulse schedules require per-pulse summation",
            "Electrode-side energy only; grid-side consumption requires efficiency correction",
        ],
    )


def compute_energy_window(
    e_current_kj: Optional[float],
    e_min_kj: Optional[float],
    e_ideal_kj: Optional[float],
    e_max_kj: Optional[float],
    method: EnergyMethod = EnergyMethod.I2RT,
    validation_status: EnergyValidationStatus = EnergyValidationStatus.NOT_VALIDATED,
    validation_note: Optional[str] = None,
    extra_assumptions: Optional[list[str]] = None,
) -> EnergyWindowEstimate:
    """Compute the five energy indicators and window status.

    All inputs in kJ/spot. None means 'not available / not established'.

    Rules enforced (see module docstring §DESIGN CONTRACT):
    - Window bounds are never invented; None → NOT_ESTABLISHED.
    - delta and excess computed only when both E_current and E_ideal present.
    - E_excess_potential = max(0, delta); never negative.
    - quality_risk_flag set when E_current < E_ideal.
    """
    assumptions: list[str] = list(extra_assumptions or [])
    window_bounds_present = e_min_kj is not None and e_max_kj is not None

    # ── Validate numeric inputs ───────────────────────────────────────────────
    for name, val in [
        ("e_current_kj", e_current_kj),
        ("e_min_kj", e_min_kj),
        ("e_ideal_kj", e_ideal_kj),
        ("e_max_kj", e_max_kj),
    ]:
        if val is not None and not math.isfinite(val):
            raise ValueError(f"{name} must be a finite number, got {val!r}")
        if val is not None and val < 0:
            raise ValueError(f"{name} must be non-negative, got {val!r}")

    if e_min_kj is not None and e_max_kj is not None and e_min_kj > e_max_kj:
        raise ValueError(
            f"e_min_kj ({e_min_kj}) must be ≤ e_max_kj ({e_max_kj})"
        )
    if (
        e_min_kj is not None
        and e_ideal_kj is not None
        and e_max_kj is not None
        and not (e_min_kj <= e_ideal_kj <= e_max_kj)
    ):
        raise ValueError(
            f"e_ideal_kj ({e_ideal_kj}) must be between e_min_kj ({e_min_kj}) "
            f"and e_max_kj ({e_max_kj})"
        )

    # ── Indicator E: delta and excess ─────────────────────────────────────────
    delta_e_signed_kj: Optional[float] = None
    e_excess_potential_kj: Optional[float] = None
    quality_risk_flag = False

    if e_current_kj is not None and e_ideal_kj is not None:
        delta_e_signed_kj = e_current_kj - e_ideal_kj
        e_excess_potential_kj = max(0.0, delta_e_signed_kj)
        if delta_e_signed_kj < 0:
            quality_risk_flag = True

    # ── Margins ───────────────────────────────────────────────────────────────
    e_margin_upper_kj: Optional[float] = None
    e_margin_lower_kj: Optional[float] = None
    if e_current_kj is not None and e_max_kj is not None:
        e_margin_upper_kj = e_max_kj - e_current_kj
    if e_current_kj is not None and e_min_kj is not None:
        e_margin_lower_kj = e_current_kj - e_min_kj

    # ── Window status ─────────────────────────────────────────────────────────
    if e_min_kj is None or e_ideal_kj is None or e_max_kj is None:
        window_status = EnergyWindowStatus.NOT_ESTABLISHED
        assumptions.append(_NOT_ESTABLISHED_NOTE)
    elif e_current_kj is None:
        window_status = EnergyWindowStatus.E_CURRENT_ABSENT
    elif e_current_kj < e_min_kj:
        window_status = EnergyWindowStatus.BELOW_MIN
    elif e_current_kj > e_max_kj:
        window_status = EnergyWindowStatus.ABOVE_MAX
    else:
        window_status = EnergyWindowStatus.IN_WINDOW

    out_of_window = window_status in (
        EnergyWindowStatus.BELOW_MIN,
        EnergyWindowStatus.ABOVE_MAX,
    )

    # ── Unit helpers for E_current ────────────────────────────────────────────
    e_current_j: Optional[float] = None
    e_current_wh: Optional[float] = None
    e_current_kwh: Optional[float] = None
    if e_current_kj is not None:
        e_current_j = e_current_kj * 1000.0
        e_current_wh = e_current_kj / 3.6
        e_current_kwh = e_current_kj / 3600.0

    if not validation_note and window_status == EnergyWindowStatus.NOT_ESTABLISHED:
        validation_note = _NOT_ESTABLISHED_NOTE

    return EnergyWindowEstimate(
        e_min_kj=e_min_kj,
        e_ideal_kj=e_ideal_kj,
        e_max_kj=e_max_kj,
        e_current_kj=e_current_kj,
        delta_e_signed_kj=delta_e_signed_kj,
        e_excess_potential_kj=e_excess_potential_kj,
        e_margin_upper_kj=e_margin_upper_kj,
        e_margin_lower_kj=e_margin_lower_kj,
        window_status=window_status,
        quality_risk_flag=quality_risk_flag,
        out_of_window=out_of_window,
        method=method,
        validation_status=validation_status,
        validation_note=validation_note,
        assumptions=assumptions,
        e_current_j=e_current_j,
        e_current_wh=e_current_wh,
        e_current_kwh=e_current_kwh,
    )


def compute_spot_cost_aggregation(
    e_current_kj: float,
    e_ideal_kj: float,
    spots_per_part: int,
    production_volume_annual: int,
    tariff_eur_per_kwh: float,
    tariff_usd_per_kwh: float,
    ideal_validation_status: EnergyValidationStatus = EnergyValidationStatus.NOT_VALIDATED,
) -> SpotCostAggregation:
    """Compute theoretical energy difference and cost at all aggregation levels.

    PRECONDITION: caller must confirm e_ideal_kj is engineering-validated before
    presenting cost results as actionable. This function adds the disclaimer
    regardless of validation_status.

    §6 verification example (SOFTWARE TESTING ONLY):
      spots=40, volume=200000, e_current=4.0, e_ideal=3.2, tariff=0.18 EUR/kWh
      → delta_e_annual_kwh = 1777.778, cost_diff_eur_annual = 320.00 EUR
    """
    for name, val in [
        ("e_current_kj", e_current_kj),
        ("e_ideal_kj", e_ideal_kj),
        ("tariff_eur_per_kwh", tariff_eur_per_kwh),
        ("tariff_usd_per_kwh", tariff_usd_per_kwh),
    ]:
        if not math.isfinite(val) or val <= 0:
            raise ValueError(f"{name} must be a positive finite number, got {val!r}")
    if spots_per_part <= 0:
        raise ValueError(f"spots_per_part must be positive, got {spots_per_part!r}")
    if production_volume_annual <= 0:
        raise ValueError(f"production_volume_annual must be positive, got {production_volume_annual!r}")

    # Per spot
    delta_e_spot_kj = e_current_kj - e_ideal_kj
    delta_e_spot_kwh = delta_e_spot_kj / 3600.0

    # Per part
    delta_e_part_kj = delta_e_spot_kj * spots_per_part
    delta_e_part_kwh = delta_e_spot_kwh * spots_per_part

    # Per 1000 parts
    delta_e_per_1000_parts_kwh = delta_e_part_kwh * 1000.0
    cost_diff_eur_per_1000_parts = delta_e_per_1000_parts_kwh * tariff_eur_per_kwh
    cost_diff_usd_per_1000_parts = delta_e_per_1000_parts_kwh * tariff_usd_per_kwh

    # Annual
    delta_e_annual_kwh = delta_e_part_kwh * production_volume_annual
    cost_diff_eur_annual = delta_e_annual_kwh * tariff_eur_per_kwh
    cost_diff_usd_annual = delta_e_annual_kwh * tariff_usd_per_kwh

    return SpotCostAggregation(
        e_current_kj=e_current_kj,
        e_ideal_kj=e_ideal_kj,
        production_volume_annual=production_volume_annual,
        tariff_eur_per_kwh=tariff_eur_per_kwh,
        tariff_usd_per_kwh=tariff_usd_per_kwh,
        spots_per_part=spots_per_part,
        delta_e_spot_kj=delta_e_spot_kj,
        delta_e_spot_kwh=delta_e_spot_kwh,
        delta_e_part_kj=delta_e_part_kj,
        delta_e_part_kwh=delta_e_part_kwh,
        delta_e_per_1000_parts_kwh=delta_e_per_1000_parts_kwh,
        cost_diff_eur_per_1000_parts=cost_diff_eur_per_1000_parts,
        cost_diff_usd_per_1000_parts=cost_diff_usd_per_1000_parts,
        delta_e_annual_kwh=delta_e_annual_kwh,
        cost_diff_eur_annual=cost_diff_eur_annual,
        cost_diff_usd_annual=cost_diff_usd_annual,
        disclaimer=_COST_DISCLAIMER,
        ideal_validation_status=ideal_validation_status,
    )
