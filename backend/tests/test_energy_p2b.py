"""
test_energy_p2b.py — Scenario comparison tests for P2-B.

Test IDs:
  SC-01   heterogeneous groups, all points have window bounds
  SC-02   proposed improves quality (BELOW_MIN → IN_WINDOW)
  SC-03   proposed degrades quality (IN_WINDOW → ABOVE_MAX)
  SC-04   missing window bounds → NOT_ESTABLISHED in both scenarios
  SC-05   out-of-window baseline: proposed brings into window
  SC-06   group aggregation totals
  SC-07   annual energy reduction and cost savings
  SC-08   validation status preserved (NOT_ESTABLISHED when NOT_VALIDATED + no bounds)
  SC-09   single point, no group specified (uses DEFAULT)
  SC-10   all points NOT_ESTABLISHED — no window bounds supplied

  API-SC-01   POST /energy/scenario/compare — valid response
  API-SC-02   POST /energy/scenario/compare — requires auth
  API-SC-03   proposed ABOVE_MAX triggers warning
  API-SC-04   cost savings calculation via API
"""

from __future__ import annotations

import pytest

from app.domain.scenario_comparison import (
    ScenarioPointIn,
    compare_scenarios,
    DISCLAIMER,
)
from app.domain.energy_window import EnergyWindowStatus, EnergyValidationStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _point(
    code: str,
    group: str = "Group-A",
    base: float | None = 0.40,
    prop: float | None = 0.38,
    e_min: float | None = 0.28,
    e_ideal: float | None = 0.32,
    e_max: float | None = 0.42,
) -> ScenarioPointIn:
    return ScenarioPointIn(
        point_code=code,
        group_name=group,
        e_min_kj=e_min,
        e_ideal_kj=e_ideal,
        e_max_kj=e_max,
        baseline_e_current_kj=base,
        proposed_e_current_kj=prop,
    )


# ---------------------------------------------------------------------------
# SC-01: heterogeneous groups, all points have window bounds
# ---------------------------------------------------------------------------
def test_sc01_heterogeneous_groups():
    pts = [
        _point("WP-001", "Group-A", base=0.40, prop=0.35),
        _point("WP-002", "Group-A", base=0.45, prop=0.38),
        _point("WP-003", "Group-B", base=0.50, prop=0.42, e_min=0.30, e_ideal=0.38, e_max=0.48),
    ]
    res = compare_scenarios(pts)
    assert len(res.points) == 3
    assert len(res.groups) == 2
    group_names = {g.group_name for g in res.groups}
    assert "Group-A" in group_names
    assert "Group-B" in group_names
    assert res.disclaimer == DISCLAIMER


# ---------------------------------------------------------------------------
# SC-02: proposed improves quality (BELOW_MIN → IN_WINDOW)
# ---------------------------------------------------------------------------
def test_sc02_quality_improves():
    # baseline is BELOW_MIN (0.20 < e_min=0.28)
    # proposed is IN_WINDOW (0.35)
    pt = _point("WP-001", base=0.20, prop=0.35)
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.BELOW_MIN
    assert pr.proposed_window_status == EnergyWindowStatus.IN_WINDOW
    assert pr.quality_improved is True
    assert pr.quality_degraded is False
    assert res.proposed_points_in_window == 1
    assert res.baseline_points_in_window == 0


# ---------------------------------------------------------------------------
# SC-03: proposed degrades quality (IN_WINDOW → ABOVE_MAX)
# ---------------------------------------------------------------------------
def test_sc03_quality_degrades():
    # baseline IN_WINDOW (0.35), proposed ABOVE_MAX (0.50 > e_max=0.42)
    pt = _point("WP-001", base=0.35, prop=0.50)
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.IN_WINDOW
    assert pr.proposed_window_status == EnergyWindowStatus.ABOVE_MAX
    assert pr.quality_degraded is True
    assert pr.quality_improved is False
    assert res.total_degraded == 1
    assert res.total_improved == 0
    # Should have a warning about exceeding E_max
    assert any("expulsion" in w for w in pr.warnings)


# ---------------------------------------------------------------------------
# SC-04: missing window bounds → NOT_ESTABLISHED
# ---------------------------------------------------------------------------
def test_sc04_missing_bounds_not_established():
    pt = ScenarioPointIn(
        point_code="WP-001",
        baseline_e_current_kj=0.40,
        proposed_e_current_kj=0.38,
        # no e_min, e_ideal, e_max
    )
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.NOT_ESTABLISHED
    assert pr.proposed_window_status == EnergyWindowStatus.NOT_ESTABLISHED
    assert pr.quality_improved is False
    assert pr.quality_degraded is False


# ---------------------------------------------------------------------------
# SC-05: out-of-window baseline, proposed brings into window
# ---------------------------------------------------------------------------
def test_sc05_out_of_window_to_in_window():
    pt = _point("WP-001", base=0.55, prop=0.35)  # baseline ABOVE_MAX → proposed IN_WINDOW
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.ABOVE_MAX
    assert pr.proposed_window_status == EnergyWindowStatus.IN_WINDOW
    assert pr.quality_improved is True
    assert pr.e_change_kj is not None
    assert pr.e_change_kj < 0  # proposed < baseline → negative change (energy reduced)


# ---------------------------------------------------------------------------
# SC-06: group aggregation totals
# ---------------------------------------------------------------------------
def test_sc06_group_aggregation():
    pts = [
        _point("WP-001", "Group-A", base=0.40, prop=0.35),
        _point("WP-002", "Group-A", base=0.38, prop=0.36),
    ]
    res = compare_scenarios(pts)
    g = res.groups[0]
    assert g.group_name == "Group-A"
    assert g.point_count == 2
    assert g.baseline_e_total_kj == pytest.approx(0.78, abs=1e-9)
    assert g.proposed_e_total_kj == pytest.approx(0.71, abs=1e-9)
    assert g.e_reduction_kj == pytest.approx(0.07, abs=1e-9)


# ---------------------------------------------------------------------------
# SC-07: annual energy reduction and cost savings
# ---------------------------------------------------------------------------
def test_sc07_annual_cost_savings():
    pts = [_point("WP-001", base=0.40, prop=0.35)]
    res = compare_scenarios(
        pts,
        production_volume_annual=200_000,
        tariff_eur_per_kwh=0.18,
        tariff_usd_per_kwh=0.19,
    )
    # part_e_reduction = 0.40 - 0.35 = 0.05 kJ
    # annual_reduction_kwh = (0.05 / 3600) * 200_000
    expected_kwh = (0.05 / 3600) * 200_000
    assert res.part_e_reduction_kj == pytest.approx(0.05, abs=1e-9)
    assert res.annual_e_reduction_kwh == pytest.approx(expected_kwh, rel=1e-6)
    assert res.annual_cost_saving_eur == pytest.approx(expected_kwh * 0.18, rel=1e-6)
    assert res.annual_cost_saving_usd == pytest.approx(expected_kwh * 0.19, rel=1e-6)
    assert res.production_volume_annual == 200_000


# ---------------------------------------------------------------------------
# SC-08: validation status NOT_VALIDATED + bounds = NOT_ESTABLISHED
# ---------------------------------------------------------------------------
def test_sc08_not_validated_status_propagated():
    pt = ScenarioPointIn(
        point_code="WP-001",
        baseline_e_current_kj=0.40,
        proposed_e_current_kj=0.35,
        # no window bounds — status should be NOT_ESTABLISHED
        validation_status=EnergyValidationStatus.NOT_VALIDATED,
    )
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.NOT_ESTABLISHED
    assert pr.proposed_window_status == EnergyWindowStatus.NOT_ESTABLISHED


# ---------------------------------------------------------------------------
# SC-09: single point, group defaults to DEFAULT
# ---------------------------------------------------------------------------
def test_sc09_single_point_default_group():
    pt = ScenarioPointIn(
        point_code="WP-SOLO",
        baseline_e_current_kj=0.40,
        proposed_e_current_kj=0.38,
        e_min_kj=0.28,
        e_ideal_kj=0.32,
        e_max_kj=0.42,
    )
    res = compare_scenarios([pt])
    assert len(res.points) == 1
    assert len(res.groups) == 1
    assert res.groups[0].group_name == "DEFAULT"
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.IN_WINDOW
    assert pr.proposed_window_status == EnergyWindowStatus.IN_WINDOW


# ---------------------------------------------------------------------------
# SC-10: all points NOT_ESTABLISHED — window_bounds absent
# ---------------------------------------------------------------------------
def test_sc10_all_not_established():
    pts = [
        ScenarioPointIn(point_code=f"WP-{i:03d}", baseline_e_current_kj=0.40, proposed_e_current_kj=0.38)
        for i in range(1, 4)
    ]
    res = compare_scenarios(pts)
    assert res.baseline_points_in_window == 0
    assert res.proposed_points_in_window == 0
    assert all(pr.baseline_window_status == EnergyWindowStatus.NOT_ESTABLISHED for pr in res.points)
    assert all(pr.proposed_window_status == EnergyWindowStatus.NOT_ESTABLISHED for pr in res.points)


# ---------------------------------------------------------------------------
# SC-11: both scenarios absent current → E_CURRENT_ABSENT
# ---------------------------------------------------------------------------
def test_sc11_both_current_absent():
    pt = ScenarioPointIn(
        point_code="WP-001",
        e_min_kj=0.28,
        e_ideal_kj=0.32,
        e_max_kj=0.42,
        baseline_e_current_kj=None,
        proposed_e_current_kj=None,
    )
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.baseline_window_status == EnergyWindowStatus.E_CURRENT_ABSENT
    assert pr.proposed_window_status == EnergyWindowStatus.E_CURRENT_ABSENT
    assert pr.e_change_kj is None
    assert pr.excess_change_kj is None


# ---------------------------------------------------------------------------
# SC-12: proposed BELOW_MIN generates quality warning
# ---------------------------------------------------------------------------
def test_sc12_proposed_below_min_warning():
    pt = _point("WP-001", base=0.35, prop=0.10)  # prop 0.10 < e_min=0.28
    res = compare_scenarios([pt])
    pr = res.points[0]
    assert pr.proposed_window_status == EnergyWindowStatus.BELOW_MIN
    assert any("quality risk" in w or "below E_min" in w for w in pr.warnings)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_api_sc01_valid_comparison(client, auth_headers):
    body = {
        "points": [
            {
                "point_code": "WP-001",
                "group_name": "Group-A",
                "e_min_kj": 0.28,
                "e_ideal_kj": 0.32,
                "e_max_kj": 0.42,
                "baseline_e_current_kj": 0.40,
                "proposed_e_current_kj": 0.35,
            },
            {
                "point_code": "WP-002",
                "group_name": "Group-A",
                "e_min_kj": 0.28,
                "e_ideal_kj": 0.32,
                "e_max_kj": 0.42,
                "baseline_e_current_kj": 0.38,
                "proposed_e_current_kj": 0.33,
            },
        ],
        "production_volume_annual": 100000,
        "tariff_eur_per_kwh": 0.18,
        "tariff_usd_per_kwh": 0.19,
    }
    resp = client.post("/api/v1/energy/scenario/compare", json=body, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["points"]) == 2
    assert len(data["groups"]) == 1
    assert data["groups"][0]["group_name"] == "Group-A"
    assert data["annual_e_reduction_kwh"] is not None
    assert data["annual_cost_saving_eur"] is not None
    assert "disclaimer" in data
    assert "SCENARIO EVALUATION" in data["disclaimer"]


def test_api_sc02_requires_auth(client):
    body = {"points": [{"point_code": "WP-001", "baseline_e_current_kj": 0.40, "proposed_e_current_kj": 0.35}]}
    resp = client.post("/api/v1/energy/scenario/compare", json=body)
    assert resp.status_code == 401


def test_api_sc03_above_max_warning(client, auth_headers):
    body = {
        "points": [{
            "point_code": "WP-001",
            "e_min_kj": 0.28,
            "e_ideal_kj": 0.32,
            "e_max_kj": 0.42,
            "baseline_e_current_kj": 0.35,
            "proposed_e_current_kj": 0.55,  # > e_max
        }]
    }
    resp = client.post("/api/v1/energy/scenario/compare", json=body, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    pr = data["points"][0]
    assert pr["proposed_window_status"] == "ABOVE_MAX"
    assert pr["quality_degraded"] is True
    assert any("expulsion" in w for w in pr["warnings"])


def test_api_sc04_cost_savings(client, auth_headers):
    # 0.40 baseline, 0.35 proposed → reduction = 0.05 kJ/spot
    # annual_kwh = 0.05/3600 * 200000
    body = {
        "points": [{
            "point_code": "WP-001",
            "e_min_kj": 0.28,
            "e_ideal_kj": 0.32,
            "e_max_kj": 0.42,
            "baseline_e_current_kj": 0.40,
            "proposed_e_current_kj": 0.35,
        }],
        "production_volume_annual": 200000,
        "tariff_eur_per_kwh": 0.18,
    }
    resp = client.post("/api/v1/energy/scenario/compare", json=body, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    expected_kwh = (0.05 / 3600) * 200000
    assert data["annual_e_reduction_kwh"] == pytest.approx(expected_kwh, rel=1e-5)
    assert data["annual_cost_saving_eur"] == pytest.approx(expected_kwh * 0.18, rel=1e-5)
