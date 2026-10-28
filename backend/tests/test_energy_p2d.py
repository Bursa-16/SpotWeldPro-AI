"""
test_energy_p2d.py — P2-D Energy & Financial Intelligence Dashboard tests.

Test IDs:
  PRT-01   Pareto ordering: highest excess first
  PRT-02   Pareto percentages sum to 100% (within tolerance)
  PRT-03   Cumulative percentages are monotonically increasing, final ≈ 100%
  PRT-04   Zero excess points have pct_of_total_excess == 0
  PRT-05   All NOT_ESTABLISHED → pareto entries exist but excess = None

  FIN-01   Per-spot average = sum(excesses) / n
  FIN-02   kJ → kWh conversion: part_excess_kwh = part_excess_kj / 3600
  FIN-03   Per-1000-parts = part_excess_kwh × 1000
  FIN-04   Annual = part_excess_kwh × production_volume_annual
  FIN-05   EUR cost = annual_excess_kwh × tariff_eur
  FIN-06   USD cost computed independently (no cross-rate assumption)
  FIN-07   Missing production volume → annual and 1000-parts costs are None
  FIN-08   NOT_ESTABLISHED points (excess None) excluded from avg, part still None
  FIN-09   Negative signed delta (below ideal) → excess = 0, not negative

  SENS-01  Default sensitivity: 5 volumes × 5 tariffs = 25 rows
  SENS-02  Custom sensitivity: correct count
  SENS-03  Linear scaling: doubling volume doubles annual_excess_kwh
  SENS-04  All None when part_excess_kj is None

  API-D-01 POST /energy/dashboard — valid response, has pareto_detailed + financial + sensitivity
  API-D-02 POST /energy/dashboard — requires auth
  API-D-03 Pareto percentages correct via API
  API-D-04 Financial summary correct via API (kJ→kWh, annual, EUR cost)
  API-D-05 Sensitivity matrix via API (default 25 rows)
"""

from __future__ import annotations

import pytest

from app.domain.energy_dashboard import (
    compute_pareto_detailed,
    compute_financial_summary,
    compute_sensitivity,
    compute_dashboard_extras,
    _DEFAULT_SENSITIVITY_VOLUMES,
    _DEFAULT_SENSITIVITY_TARIFFS_EUR,
)
from app.domain.energy_aggregation import aggregate_multi_spot, WeldPointEnergySpec
from app.domain.energy_window import EnergyWindowStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_specs(points: list[tuple]) -> list[WeldPointEnergySpec]:
    """Build WeldPointEnergySpec list from (code, group, e_cur, e_min, e_ideal, e_max)."""
    return [
        WeldPointEnergySpec(
            point_code=code, group_name=group,
            e_current_kj=e_cur, e_min_kj=e_min, e_ideal_kj=e_ideal, e_max_kj=e_max,
        )
        for code, group, e_cur, e_min, e_ideal, e_max in points
    ]


def _aggr_rows(specs):
    return aggregate_multi_spot(specs).rows


# ---------------------------------------------------------------------------
# PRT: Pareto ordering and percentages
# ---------------------------------------------------------------------------

def test_prt01_highest_excess_first():
    specs = _make_specs([
        ('WP-001', 'G-A', 0.55, 0.28, 0.32, 0.42),  # excess = 0.55 - 0.32 = 0.23
        ('WP-002', 'G-A', 0.40, 0.28, 0.32, 0.42),  # excess = 0.40 - 0.32 = 0.08
        ('WP-003', 'G-A', 0.35, 0.28, 0.32, 0.42),  # excess = 0.35 - 0.32 = 0.03
    ])
    rows = compute_pareto_detailed(_aggr_rows(specs))
    assert rows[0].point_code == 'WP-001'
    assert rows[1].point_code == 'WP-002'
    assert rows[2].point_code == 'WP-003'
    # All excess must be non-negative
    for r in rows:
        if r.e_excess_kj is not None:
            assert r.e_excess_kj >= 0


def test_prt02_percentages_sum_to_100():
    specs = _make_specs([
        ('WP-001', 'G-A', 0.55, 0.28, 0.32, 0.42),
        ('WP-002', 'G-A', 0.40, 0.28, 0.32, 0.42),
        ('WP-003', 'G-A', 0.35, 0.28, 0.32, 0.42),
    ])
    rows = compute_pareto_detailed(_aggr_rows(specs))
    total_pct = sum(r.pct_of_total_excess or 0 for r in rows)
    assert total_pct == pytest.approx(100.0, abs=0.1)


def test_prt03_cumulative_monotonic_and_ends_100():
    specs = _make_specs([
        ('WP-001', 'G-A', 0.55, 0.28, 0.32, 0.42),
        ('WP-002', 'G-A', 0.40, 0.28, 0.32, 0.42),
        ('WP-003', 'G-A', 0.35, 0.28, 0.32, 0.42),
    ])
    rows = compute_pareto_detailed(_aggr_rows(specs))
    prev = 0.0
    for r in rows:
        if r.cumulative_pct is not None:
            assert r.cumulative_pct >= prev - 1e-6
            prev = r.cumulative_pct
    assert rows[-1].cumulative_pct == pytest.approx(100.0, abs=0.1)


def test_prt04_in_window_point_has_zero_pct():
    specs = _make_specs([
        ('WP-001', 'G-A', 0.55, 0.28, 0.32, 0.42),  # ABOVE_MAX → excess > 0
        ('WP-002', 'G-A', 0.35, 0.28, 0.32, 0.42),  # IN_WINDOW → excess = 0.03
        ('WP-003', 'G-A', 0.32, 0.28, 0.32, 0.42),  # IN_WINDOW → excess = 0
    ])
    rows = compute_pareto_detailed(_aggr_rows(specs))
    wp3 = next(r for r in rows if r.point_code == 'WP-003')
    assert wp3.e_excess_kj == pytest.approx(0.0, abs=1e-9)
    assert wp3.pct_of_total_excess == 0.0


def test_prt05_all_not_established_excess_none():
    specs = _make_specs([
        ('WP-001', 'G-A', 0.40, None, None, None),
        ('WP-002', 'G-A', 0.38, None, None, None),
    ])
    rows = compute_pareto_detailed(_aggr_rows(specs))
    assert all(r.e_excess_kj is None for r in rows)
    # cumulative stays at 0
    assert all(r.cumulative_pct == 0.0 for r in rows)


# ---------------------------------------------------------------------------
# FIN: Financial summary calculations
# ---------------------------------------------------------------------------

def test_fin01_avg_excess_per_spot():
    part_excess = 0.31  # 0.23 + 0.08
    all_excess = [0.23, 0.08]
    fs = compute_financial_summary(part_excess, None, None, None, all_excess)
    assert fs.avg_excess_per_spot_kj == pytest.approx(0.155, abs=1e-9)


def test_fin02_kj_to_kwh_conversion():
    part_excess = 0.36  # kJ
    fs = compute_financial_summary(part_excess, None, None, None, [0.36])
    assert fs.part_excess_kwh == pytest.approx(0.36 / 3600.0, rel=1e-6)


def test_fin03_per_1000_parts():
    part_excess = 0.36
    fs = compute_financial_summary(part_excess, None, None, None, [0.36])
    expected = (0.36 / 3600.0) * 1000.0
    assert fs.per_1000_parts_excess_kwh == pytest.approx(expected, rel=1e-6)


def test_fin04_annual_excess_kwh():
    part_excess = 0.36
    vol = 200_000
    fs = compute_financial_summary(part_excess, vol, None, None, [0.36])
    expected = (0.36 / 3600.0) * vol
    assert fs.annual_excess_kwh == pytest.approx(expected, rel=1e-6)


def test_fin05_eur_cost():
    part_excess = 0.36
    vol = 200_000
    tariff_eur = 0.18
    fs = compute_financial_summary(part_excess, vol, tariff_eur, None, [0.36])
    expected_kwh = (0.36 / 3600.0) * vol
    assert fs.annual_cost_eur == pytest.approx(expected_kwh * tariff_eur, rel=1e-6)


def test_fin06_usd_cost_independent_of_eur():
    part_excess = 0.36
    vol = 200_000
    tariff_eur = 0.18
    tariff_usd = 0.22
    fs = compute_financial_summary(part_excess, vol, tariff_eur, tariff_usd, [0.36])
    expected_kwh = (0.36 / 3600.0) * vol
    assert fs.annual_cost_eur == pytest.approx(expected_kwh * tariff_eur, rel=1e-6)
    assert fs.annual_cost_usd == pytest.approx(expected_kwh * tariff_usd, rel=1e-6)
    # Verify they differ (no exchange rate assumed)
    assert fs.annual_cost_eur != pytest.approx(fs.annual_cost_usd, rel=1e-6)


def test_fin07_missing_volume_costs_are_none():
    fs = compute_financial_summary(0.36, None, 0.18, 0.20, [0.36])
    assert fs.annual_excess_kwh is None
    assert fs.annual_cost_eur is None
    assert fs.annual_cost_usd is None
    assert fs.per_1000_parts_excess_kwh is not None  # per-1000 doesn't need volume


def test_fin08_all_not_established_financial():
    # No excess values → part_excess is None, all financial output None
    fs = compute_financial_summary(None, 200_000, 0.18, 0.20, [None, None])
    assert fs.part_excess_kj is None
    assert fs.part_excess_kwh is None
    assert fs.annual_excess_kwh is None
    assert fs.annual_cost_eur is None


def test_fin09_negative_delta_gives_zero_excess():
    # e_current < e_ideal → signed delta negative → excess = 0 (not negative)
    specs = _make_specs([
        ('WP-001', 'G-A', 0.28, 0.28, 0.32, 0.42),  # BELOW_MIN → excess = 0
    ])
    rows = _aggr_rows(specs)
    pareto = compute_pareto_detailed(rows)
    assert pareto[0].e_excess_kj == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# SENS: Sensitivity analysis
# ---------------------------------------------------------------------------

def test_sens01_default_matrix_has_25_rows():
    rows = compute_sensitivity(0.36, None)
    expected = len(_DEFAULT_SENSITIVITY_VOLUMES) * len(_DEFAULT_SENSITIVITY_TARIFFS_EUR)
    assert len(rows) == expected
    assert expected == 25


def test_sens02_custom_sensitivity_count():
    vols = [100_000, 200_000]
    tariffs = [0.15, 0.20, 0.25]
    rows = compute_sensitivity(0.36, None, volumes=vols, tariffs_eur=tariffs)
    assert len(rows) == 6


def test_sens03_linear_volume_scaling():
    rows = compute_sensitivity(0.36, None, volumes=[100_000, 200_000], tariffs_eur=[0.18])
    kwh_100k = rows[0].annual_excess_kwh
    kwh_200k = rows[1].annual_excess_kwh
    assert kwh_100k is not None
    assert kwh_200k == pytest.approx(kwh_100k * 2, rel=1e-6)


def test_sens04_all_none_when_no_excess():
    rows = compute_sensitivity(None, None)
    assert all(r.annual_excess_kwh is None for r in rows)
    assert all(r.cost_eur is None for r in rows)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_api_d01_valid_dashboard(client, auth_headers):
    body = {
        "points": [
            {"point_code": "WP-001", "group_name": "G-A",
             "e_current_kj": 0.55, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
            {"point_code": "WP-002", "group_name": "G-A",
             "e_current_kj": 0.40, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
            {"point_code": "WP-003", "group_name": "G-B",
             "e_current_kj": 0.30, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
        ],
        "production_volume_annual": 200_000,
        "tariff_eur_per_kwh": 0.18,
        "tariff_usd_per_kwh": 0.22,
    }
    resp = client.post("/api/v1/energy/dashboard", json=body, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Standard aggregation fields present
    assert "rows" in data
    assert "groups" in data
    assert "financial" in data
    assert "pareto_detailed" in data
    assert "sensitivity" in data
    assert "dashboard_disclaimer" in data
    assert "THEORETICAL" in data["dashboard_disclaimer"]
    assert len(data["rows"]) == 3
    assert len(data["pareto_detailed"]) == 3


def test_api_d02_requires_auth(client):
    body = {"points": [{"point_code": "WP-001", "e_current_kj": 0.40}]}
    resp = client.post("/api/v1/energy/dashboard", json=body)
    assert resp.status_code == 401


def test_api_d03_pareto_percentages_correct(client, auth_headers):
    # WP-001 excess = 0.23, WP-002 excess = 0.08 → total = 0.31
    # WP-001 pct ≈ 74.2%, WP-002 pct ≈ 25.8%
    body = {
        "points": [
            {"point_code": "WP-001", "group_name": "G-A",
             "e_current_kj": 0.55, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
            {"point_code": "WP-002", "group_name": "G-A",
             "e_current_kj": 0.40, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
        ],
    }
    resp = client.post("/api/v1/energy/dashboard", json=body, headers=auth_headers)
    assert resp.status_code == 200
    pareto = resp.json()["pareto_detailed"]
    assert pareto[0]["point_code"] == "WP-001"
    assert pareto[0]["pct_of_total_excess"] == pytest.approx(74.19, abs=0.1)
    total_pct = sum(p["pct_of_total_excess"] for p in pareto)
    assert total_pct == pytest.approx(100.0, abs=0.1)


def test_api_d04_financial_summary_correct(client, auth_headers):
    # WP-001: excess = 0.23, WP-002: excess = 0.08 → part_excess = 0.31 kJ
    body = {
        "points": [
            {"point_code": "WP-001", "group_name": "G-A",
             "e_current_kj": 0.55, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
            {"point_code": "WP-002", "group_name": "G-A",
             "e_current_kj": 0.40, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
        ],
        "production_volume_annual": 200_000,
        "tariff_eur_per_kwh": 0.18,
    }
    resp = client.post("/api/v1/energy/dashboard", json=body, headers=auth_headers)
    assert resp.status_code == 200
    fin = resp.json()["financial"]
    assert fin["part_excess_kj"] == pytest.approx(0.31, abs=1e-6)
    assert fin["part_excess_kwh"] == pytest.approx(0.31 / 3600.0, rel=1e-5)
    expected_annual = (0.31 / 3600.0) * 200_000
    assert fin["annual_excess_kwh"] == pytest.approx(expected_annual, rel=1e-5)
    assert fin["annual_cost_eur"] == pytest.approx(expected_annual * 0.18, rel=1e-5)


def test_api_d05_sensitivity_default_count(client, auth_headers):
    body = {
        "points": [
            {"point_code": "WP-001", "group_name": "G-A",
             "e_current_kj": 0.55, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
        ],
    }
    resp = client.post("/api/v1/energy/dashboard", json=body, headers=auth_headers)
    assert resp.status_code == 200
    sens = resp.json()["sensitivity"]
    expected = len(_DEFAULT_SENSITIVITY_VOLUMES) * len(_DEFAULT_SENSITIVITY_TARIFFS_EUR)
    assert len(sens) == expected
    # Verify structure
    assert "production_volume" in sens[0]
    assert "tariff_eur_per_kwh" in sens[0]
    assert "cost_eur" in sens[0]
