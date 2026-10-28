"""
energy.py — Electrode-side delivered energy for resistance spot welding.

ENGINEERING ASSUMPTIONS (documented, not implicit):

current_ka is the RMS (effective) weld current in kA.
  - This is the standard weld-controller setpoint for both AC and DC/MFDC equipment.
  - Weld controllers report and set RMS current (Ieff), not peak current.
  - For constant DC / MFDC: I_rms ≈ I_mean; E = I² · R · t is valid.
  - For 50 Hz AC sinusoidal: E = I_rms² · R · t is valid when current_ka is the RMS
    value. The formula does NOT apply a peak-to-RMS correction because current_ka
    is ALREADY the RMS value as set on the controller.

resistance_micro_ohm is the CONSTANT dynamic resistance across the full weld duration.
  - Real resistance varies with temperature and indentation (see domain/dynamic_resistance.py).
  - Using a single constant R is a simplification appropriate for comparative estimation.

weld_cycles / frequency_hz gives weld duration in seconds.
  - Multi-pulse schedules: each pulse should be estimated separately and summed.

This module computes electrode-side delivered energy only.
Grid-side electricity consumption requires efficiency and auxiliary load corrections.
"""

from __future__ import annotations
from typing import Dict


def estimate_energy(
    current_ka: float,
    resistance_micro_ohm: float,
    weld_cycles: float,
    frequency_hz: float = 50.0,
) -> Dict[str, float]:
    """Compute electrode-side delivered energy via E = I_rms² · R · t.

    current_ka : RMS weld current in kA (weld-controller setpoint, not peak current).
    resistance_micro_ohm : constant contact resistance in µΩ.
    weld_cycles : number of AC / MFDC cycles at frequency_hz.
    frequency_hz : supply or converter frequency in Hz (default 50 Hz).

    Returns energy_j, energy_wh, energy_kj, energy_kwh, time_s.
    The kJ and kWh keys are additive — existing callers that used energy_j / energy_wh
    are unaffected.
    """
    current_a = current_ka * 1000.0           # kA → A (RMS)
    resistance_ohm = resistance_micro_ohm * 1e-6  # µΩ → Ω
    time_s = weld_cycles / frequency_hz
    energy_j = (current_a ** 2) * resistance_ohm * time_s
    energy_wh = energy_j / 3600.0
    energy_kj = energy_j / 1000.0
    energy_kwh = energy_wh / 1000.0
    return {
        "energy_j": energy_j,
        "energy_wh": energy_wh,
        "energy_kj": energy_kj,
        "energy_kwh": energy_kwh,
        "time_s": time_s,
    }


def compare_energy(
    current_ka: float,
    weld_cycles: float,
    recommended_current_ka: float,
    recommended_cycles: float,
    resistance_micro_ohm: float,
    annual_spot_count: int,
    electricity_kgco2_per_kwh: float,
) -> Dict[str, float]:
    """Compare actual vs recommended energy; return unsigned annual difference.

    Both current values are treated as RMS in kA (see module docstring).
    Returns existing keys unchanged plus kJ variants for new consumers.
    """
    actual = estimate_energy(current_ka, resistance_micro_ohm, weld_cycles)
    recommended = estimate_energy(
        recommended_current_ka, resistance_micro_ohm, recommended_cycles
    )

    delta_wh = actual["energy_wh"] - recommended["energy_wh"]
    delta_kj = actual["energy_kj"] - recommended["energy_kj"]
    annual_kwh = delta_wh * annual_spot_count / 1000.0
    annual_co2_kg = annual_kwh * electricity_kgco2_per_kwh

    return {
        # Original keys preserved for backward compatibility
        "actual_wh_per_spot": actual["energy_wh"],
        "recommended_wh_per_spot": recommended["energy_wh"],
        "delta_wh_per_spot": delta_wh,
        "annual_kwh_difference": annual_kwh,
        "annual_co2_kg_difference": annual_co2_kg,
        # New kJ keys (P0 addition)
        "actual_kj_per_spot": actual["energy_kj"],
        "recommended_kj_per_spot": recommended["energy_kj"],
        "delta_kj_per_spot": delta_kj,
    }
