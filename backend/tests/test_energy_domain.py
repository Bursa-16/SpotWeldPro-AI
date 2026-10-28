"""
test_energy_domain.py — Automated tests for P0 Energy Intelligence.

MASTER-ENERGY-OPTIMIZATION-01, P0 test contract.

Coverage:
  ENERGY-01  AC RMS vs peak: formula is applied to RMS, not peak current
  ENERGY-02  DC/MFDC path: identical formula, current is mean ≈ RMS
  ENERGY-03  Unit conversions: J, kJ, Wh, kWh relationships
  ENERGY-04  Missing / None values: NOT_ESTABLISHED sentinel
  ENERGY-05  Energy window: IN_WINDOW
  ENERGY-06  Energy window: BELOW_MIN
  ENERGY-07  Energy window: ABOVE_MAX
  ENERGY-08  Signed difference and excess: positive, negative, zero
  ENERGY-09  quality_risk_flag: set only when E_current < E_ideal
  ENERGY-10  §6 cost aggregation: 40 spots × 200k parts × 0.8 kJ/spot × 0.18 EUR
  ENERGY-11  Validation: invalid inputs raise ValueError
  ENERGY-12  Window ordering constraint: e_ideal outside [e_min, e_max] raises
  ENERGY-13  compare_energy backward-compatible kJ keys (energy.py)
  API-01     POST /api/v1/energy/estimate — authenticated
  API-02     POST /api/v1/energy/window — NOT_ESTABLISHED when bounds absent
  API-03     POST /api/v1/energy/cost — §6 verification
  API-04     POST /api/v1/energy/estimate — unauthenticated → 401/403
"""

from __future__ import annotations

import math
import pytest

from app.domain.energy import estimate_energy, compare_energy
from app.domain.energy_window import (
    EnergyMethod,
    EnergyValidationStatus,
    EnergyWindowStatus,
    compute_energy_i2rt,
    compute_energy_window,
    compute_spot_cost_aggregation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _approx(expected: float, rel: float = 1e-6) -> float:
    """pytest.approx wrapper with tighter tolerance for energy math."""
    return pytest.approx(expected, rel=rel)


# ---------------------------------------------------------------------------
# ENERGY-01: AC RMS vs peak — formula uses RMS, not peak current
# ---------------------------------------------------------------------------

def test_energy01_rms_not_peak():
    """
    For a 10 kA RMS, 100 µΩ, 16-cycle at 50 Hz scenario:
      t = 16/50 = 0.32 s
      E = (10000)² × 100e-6 × 0.32 = 3200 J = 3.2 kJ

    If code incorrectly used peak (14.142 kA for sinusoidal AC), it would
    compute ~6400 J — exactly 2× the correct answer.

    This test verifies the 3200 J result to confirm RMS is used.
    """
    result = compute_energy_i2rt(
        current_ka=10.0,
        resistance_micro_ohm=100.0,
        weld_cycles=16.0,
        frequency_hz=50.0,
    )
    # E = I_rms² × R × t = 10000² × 100e-6 × 0.32
    expected_j = (10_000.0 ** 2) * 100e-6 * (16.0 / 50.0)
    assert result.energy_j == _approx(expected_j)
    assert result.energy_kj == _approx(expected_j / 1000.0)

    # Explicitly verify it is NOT the peak-current result
    # For sinusoidal AC: I_peak = I_rms × √2; E_peak = 2 × E_rms
    peak_energy_j = (10_000.0 * math.sqrt(2)) ** 2 * 100e-6 * (16.0 / 50.0)
    assert result.energy_j != _approx(peak_energy_j, rel=0.01), (
        "energy_j must not equal the peak-current result — "
        "controller setpoint is RMS, not peak"
    )


def test_energy01_rms_documented_in_assumptions():
    """Assumptions list must state RMS, not peak."""
    result = compute_energy_i2rt(8.3, 120.0, 16.0)
    rms_stated = any("rms" in a.lower() or "effective" in a.lower() for a in result.assumptions)
    assert rms_stated, "At least one assumption must document the RMS current convention"


# ---------------------------------------------------------------------------
# ENERGY-02: DC/MFDC path — same formula, I_mean ≈ I_rms
# ---------------------------------------------------------------------------

def test_energy02_dc_mfdc_path():
    """
    DC/MFDC current is constant; I_mean ≈ I_rms; same formula applies.
    Test with 8.3 kA (typical MFDC setpoint for 1.5 mm galvanised steel).
    """
    result = compute_energy_i2rt(
        current_ka=8.3,
        resistance_micro_ohm=120.0,
        weld_cycles=16.0,
        frequency_hz=1000.0,  # MFDC at 1 kHz
    )
    expected_j = (8300.0 ** 2) * 120e-6 * (16.0 / 1000.0)
    assert result.energy_j == _approx(expected_j)
    assert result.method == EnergyMethod.I2RT


# ---------------------------------------------------------------------------
# ENERGY-03: Unit conversions
# ---------------------------------------------------------------------------

def test_energy03_unit_conversions():
    """kJ = J/1000; kWh = Wh/1000; Wh = J/3600."""
    result = compute_energy_i2rt(10.0, 100.0, 16.0, 50.0)
    assert result.energy_kj == _approx(result.energy_j / 1000.0)
    assert result.energy_wh == _approx(result.energy_j / 3600.0)
    assert result.energy_kwh == _approx(result.energy_wh / 1000.0)
    assert result.energy_kwh == _approx(result.energy_j / 3_600_000.0)


def test_energy03_estimate_energy_kj_keys():
    """energy.py (legacy function) must include energy_kj and energy_kwh."""
    result = estimate_energy(10.0, 100.0, 16.0, 50.0)
    assert "energy_kj" in result
    assert "energy_kwh" in result
    assert result["energy_kj"] == _approx(result["energy_j"] / 1000.0)
    assert result["energy_kwh"] == _approx(result["energy_wh"] / 1000.0)


# ---------------------------------------------------------------------------
# ENERGY-04: Missing values → NOT_ESTABLISHED
# ---------------------------------------------------------------------------

def test_energy04_none_bounds_gives_not_established():
    r = compute_energy_window(e_current_kj=0.4, e_min_kj=None, e_ideal_kj=None, e_max_kj=None)
    assert r.window_status == EnergyWindowStatus.NOT_ESTABLISHED
    assert r.delta_e_signed_kj is None
    assert r.e_excess_potential_kj is None


def test_energy04_partial_bounds_none():
    r = compute_energy_window(e_current_kj=0.4, e_min_kj=0.28, e_ideal_kj=None, e_max_kj=0.42)
    assert r.window_status == EnergyWindowStatus.NOT_ESTABLISHED


def test_energy04_no_current_no_bounds():
    r = compute_energy_window(e_current_kj=None, e_min_kj=None, e_ideal_kj=None, e_max_kj=None)
    assert r.window_status == EnergyWindowStatus.NOT_ESTABLISHED
    assert r.e_current_j is None
    assert r.e_current_wh is None
    assert r.e_current_kwh is None


def test_energy04_bounds_present_current_absent():
    r = compute_energy_window(e_current_kj=None, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)
    assert r.window_status == EnergyWindowStatus.E_CURRENT_ABSENT
    assert r.delta_e_signed_kj is None
    assert r.e_excess_potential_kj is None


# ---------------------------------------------------------------------------
# ENERGY-05: IN_WINDOW
# ---------------------------------------------------------------------------

def test_energy05_in_window():
    r = compute_energy_window(
        e_current_kj=0.35, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.window_status == EnergyWindowStatus.IN_WINDOW
    assert r.out_of_window is False


def test_energy05_at_min_boundary():
    r = compute_energy_window(
        e_current_kj=0.28, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.window_status == EnergyWindowStatus.IN_WINDOW


def test_energy05_at_max_boundary():
    r = compute_energy_window(
        e_current_kj=0.42, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.window_status == EnergyWindowStatus.IN_WINDOW


# ---------------------------------------------------------------------------
# ENERGY-06: BELOW_MIN
# ---------------------------------------------------------------------------

def test_energy06_below_min():
    r = compute_energy_window(
        e_current_kj=0.20, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.window_status == EnergyWindowStatus.BELOW_MIN
    assert r.out_of_window is True
    assert r.quality_risk_flag is True  # also below ideal


# ---------------------------------------------------------------------------
# ENERGY-07: ABOVE_MAX
# ---------------------------------------------------------------------------

def test_energy07_above_max():
    r = compute_energy_window(
        e_current_kj=0.50, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.window_status == EnergyWindowStatus.ABOVE_MAX
    assert r.out_of_window is True
    assert r.quality_risk_flag is False  # current is above ideal → no quality risk


# ---------------------------------------------------------------------------
# ENERGY-08: Signed difference and excess
# ---------------------------------------------------------------------------

def test_energy08_positive_delta():
    """E_current > E_ideal → positive delta, positive excess."""
    r = compute_energy_window(
        e_current_kj=0.40, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    expected_delta = 0.40 - 0.32
    assert r.delta_e_signed_kj == _approx(expected_delta)
    assert r.e_excess_potential_kj == _approx(expected_delta)


def test_energy08_negative_delta_zero_excess():
    """E_current < E_ideal → negative signed delta, but excess = 0."""
    r = compute_energy_window(
        e_current_kj=0.30, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.delta_e_signed_kj == _approx(0.30 - 0.32)
    assert r.delta_e_signed_kj < 0
    assert r.e_excess_potential_kj == 0.0


def test_energy08_zero_delta():
    """E_current == E_ideal → delta = 0, excess = 0."""
    r = compute_energy_window(
        e_current_kj=0.32, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42
    )
    assert r.delta_e_signed_kj == _approx(0.0)
    assert r.e_excess_potential_kj == _approx(0.0)


# ---------------------------------------------------------------------------
# ENERGY-09: quality_risk_flag
# ---------------------------------------------------------------------------

def test_energy09_risk_flag_only_when_below_ideal():
    above = compute_energy_window(0.40, 0.28, 0.32, 0.42)
    equal = compute_energy_window(0.32, 0.28, 0.32, 0.42)
    below = compute_energy_window(0.30, 0.28, 0.32, 0.42)
    assert above.quality_risk_flag is False
    assert equal.quality_risk_flag is False
    assert below.quality_risk_flag is True


# ---------------------------------------------------------------------------
# ENERGY-10: §6 cost aggregation verification
# ---------------------------------------------------------------------------

def test_energy10_section6_cost_example():
    """
    §6 reference example:
      spots_per_part = 40
      production_volume = 200 000 parts/year
      e_current_kj = 4.0, e_ideal_kj = 3.2 → Δ = 0.8 kJ/spot
      tariff = 0.18 EUR/kWh

    Expected:
      delta_e_annual_kWh = 0.8/3600 × 40 × 200000 = 1777.777…
      cost_eur_annual = 1777.777… × 0.18 = 320.000 EUR
    """
    result = compute_spot_cost_aggregation(
        e_current_kj=4.0,
        e_ideal_kj=3.2,
        spots_per_part=40,
        production_volume_annual=200_000,
        tariff_eur_per_kwh=0.18,
        tariff_usd_per_kwh=0.19,
    )
    # Per spot
    assert result.delta_e_spot_kj == _approx(0.8)
    assert result.delta_e_spot_kwh == _approx(0.8 / 3600.0)

    # Per part (40 spots)
    assert result.delta_e_part_kj == _approx(32.0)   # 0.8 × 40
    assert result.delta_e_part_kwh == _approx(32.0 / 3600.0)

    # Annual
    expected_annual_kwh = (0.8 / 3600.0) * 40 * 200_000
    assert result.delta_e_annual_kwh == _approx(expected_annual_kwh)
    assert result.cost_diff_eur_annual == _approx(expected_annual_kwh * 0.18)
    assert result.cost_diff_eur_annual == _approx(320.0, rel=1e-4)

    # Disclaimer must be present and non-empty
    assert isinstance(result.disclaimer, str) and len(result.disclaimer) > 20


# ---------------------------------------------------------------------------
# ENERGY-11: Input validation raises ValueError
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kwargs", [
    {"current_ka": 0, "resistance_micro_ohm": 100, "weld_cycles": 16},
    {"current_ka": -1.0, "resistance_micro_ohm": 100, "weld_cycles": 16},
    {"current_ka": 10.0, "resistance_micro_ohm": 0, "weld_cycles": 16},
    {"current_ka": 10.0, "resistance_micro_ohm": 100, "weld_cycles": 0},
    {"current_ka": 10.0, "resistance_micro_ohm": 100, "weld_cycles": 16, "frequency_hz": 0},
])
def test_energy11_invalid_inputs_raise(kwargs):
    with pytest.raises(ValueError):
        compute_energy_i2rt(**kwargs)


def test_energy11_negative_e_window_input():
    with pytest.raises(ValueError):
        compute_energy_window(e_current_kj=-0.1, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)


def test_energy11_cost_non_positive_volume():
    with pytest.raises(ValueError):
        compute_spot_cost_aggregation(4.0, 3.2, 40, 0, 0.18, 0.19)


# ---------------------------------------------------------------------------
# ENERGY-12: Window ordering constraint
# ---------------------------------------------------------------------------

def test_energy12_min_greater_than_max_raises():
    with pytest.raises(ValueError):
        compute_energy_window(
            e_current_kj=0.35, e_min_kj=0.50, e_ideal_kj=0.50, e_max_kj=0.28
        )


def test_energy12_ideal_outside_window_raises():
    with pytest.raises(ValueError):
        compute_energy_window(
            e_current_kj=0.35, e_min_kj=0.28, e_ideal_kj=0.50, e_max_kj=0.42
        )


def test_energy12_ideal_below_min_raises():
    with pytest.raises(ValueError):
        compute_energy_window(
            e_current_kj=0.35, e_min_kj=0.28, e_ideal_kj=0.10, e_max_kj=0.42
        )


# ---------------------------------------------------------------------------
# ENERGY-13: compare_energy backward-compatible kJ keys
# ---------------------------------------------------------------------------

def test_energy13_compare_energy_original_keys_preserved():
    result = compare_energy(
        current_ka=10.0,
        weld_cycles=16.0,
        recommended_current_ka=9.0,
        recommended_cycles=16.0,
        resistance_micro_ohm=100.0,
        annual_spot_count=1_000_000,
        electricity_kgco2_per_kwh=0.4,
    )
    for key in ("actual_wh_per_spot", "recommended_wh_per_spot", "delta_wh_per_spot",
                "annual_kwh_difference", "annual_co2_kg_difference"):
        assert key in result, f"Legacy key {key!r} must be preserved"


def test_energy13_compare_energy_new_kj_keys():
    result = compare_energy(
        current_ka=10.0,
        weld_cycles=16.0,
        recommended_current_ka=9.0,
        recommended_cycles=16.0,
        resistance_micro_ohm=100.0,
        annual_spot_count=1_000_000,
        electricity_kgco2_per_kwh=0.4,
    )
    for key in ("actual_kj_per_spot", "recommended_kj_per_spot", "delta_kj_per_spot"):
        assert key in result, f"New kJ key {key!r} must be present"
    assert result["actual_kj_per_spot"] == _approx(result["actual_wh_per_spot"] * 3.6)
    assert result["delta_kj_per_spot"] == _approx(result["actual_kj_per_spot"] - result["recommended_kj_per_spot"])


# ---------------------------------------------------------------------------
# API tests — require the TestClient fixtures from conftest.py
# ---------------------------------------------------------------------------

def test_api01_energy_estimate_authenticated(client, auth_headers):
    """POST /api/v1/energy/estimate must succeed with valid auth."""
    payload = {
        "current_ka": 10.0,
        "resistance_micro_ohm": 100.0,
        "weld_cycles": 16.0,
        "frequency_hz": 50.0,
    }
    response = client.post("/api/v1/energy/estimate", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "energy_kj" in data
    assert data["energy_kj"] == pytest.approx((10_000.0 ** 2) * 100e-6 * (16.0 / 50.0) / 1000.0, rel=1e-6)
    assert isinstance(data["assumptions"], list)
    assert len(data["assumptions"]) > 0


def test_api02_energy_window_not_established(client, auth_headers):
    """POST /api/v1/energy/window with no bounds → NOT_ESTABLISHED."""
    payload = {"e_current_kj": 0.4}
    response = client.post("/api/v1/energy/window", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["window_status"] == "NOT_ESTABLISHED"
    assert data["delta_e_signed_kj"] is None
    assert data["e_excess_potential_kj"] is None


def test_api02_energy_window_in_window(client, auth_headers):
    """POST /api/v1/energy/window with full bounds → IN_WINDOW."""
    payload = {
        "e_current_kj": 0.35,
        "e_min_kj": 0.28,
        "e_ideal_kj": 0.32,
        "e_max_kj": 0.42,
    }
    response = client.post("/api/v1/energy/window", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["window_status"] == "IN_WINDOW"


def test_api03_energy_cost_section6(client, auth_headers):
    """POST /api/v1/energy/cost — §6 verification: 320 EUR/year."""
    payload = {
        "e_current_kj": 4.0,
        "e_ideal_kj": 3.2,
        "spots_per_part": 40,
        "production_volume_annual": 200_000,
        "tariff_eur_per_kwh": 0.18,
        "tariff_usd_per_kwh": 0.19,
    }
    response = client.post("/api/v1/energy/cost", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["cost_diff_eur_annual"] == pytest.approx(320.0, rel=1e-4)
    assert "disclaimer" in data
    assert len(data["disclaimer"]) > 20


def test_api04_energy_estimate_unauthenticated(client):
    """POST /api/v1/energy/estimate without auth must be rejected."""
    payload = {
        "current_ka": 10.0,
        "resistance_micro_ohm": 100.0,
        "weld_cycles": 16.0,
    }
    response = client.post("/api/v1/energy/estimate", json=payload)
    assert response.status_code in (401, 403), (
        f"Expected 401 or 403, got {response.status_code}: {response.text}"
    )
