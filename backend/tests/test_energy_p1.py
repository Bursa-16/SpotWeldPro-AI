"""
test_energy_p1.py — P1 tests for Multi-Spot Energy & Cost Intelligence.

MASTER-ENERGY-OPTIMIZATION-01, P1 scope.

Test IDs:
  AGG-01 … AGG-07  — energy_aggregation domain
  IMP-01 … IMP-09  — import_validation domain
  API-P1-01 … 04   — FastAPI aggregate + import routes (use conftest fixtures)
  FIN-01 … FIN-03  — financial cost rollup accuracy

Run: pytest tests/test_energy_p1.py -v
"""

from __future__ import annotations

import math
import pytest
from app.domain.energy_aggregation import (
    WeldPointEnergySpec,
    aggregate_multi_spot,
)
from app.domain.import_validation import (
    validate_csv_import,
    is_formula_injection,
    TEMPLATE_COLUMNS,
    REQUIRED_COLUMNS,
)
from app.domain.energy_window import EnergyWindowStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _spec(
    point_code: str,
    group_name: str = "G",
    e_current_kj: float | None = None,
    e_min_kj: float | None = None,
    e_ideal_kj: float | None = None,
    e_max_kj: float | None = None,
) -> WeldPointEnergySpec:
    return WeldPointEnergySpec(
        point_code=point_code,
        group_name=group_name,
        e_current_kj=e_current_kj,
        e_min_kj=e_min_kj,
        e_ideal_kj=e_ideal_kj,
        e_max_kj=e_max_kj,
    )


def _approx(v: float, rel: float = 1e-5) -> pytest.approx:  # type: ignore[type-arg]
    return pytest.approx(v, rel=rel)


# ---------------------------------------------------------------------------
# AGG-01: single in-window point
# ---------------------------------------------------------------------------
def test_agg01_single_in_window():
    specs = [_spec("WP-001", e_current_kj=0.35, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)]
    r = aggregate_multi_spot(specs)
    assert r.part_point_count == 1
    assert r.part_points_in_window == 1
    assert r.part_points_below_min == 0
    assert r.part_points_above_max == 0
    row = r.rows[0]
    assert row.window.window_status == EnergyWindowStatus.IN_WINDOW
    # e_current=0.35 > e_ideal=0.32 → excess = 0.03 (positive even while in-window)
    assert row.window.e_excess_potential_kj == _approx(0.03)


# ---------------------------------------------------------------------------
# AGG-02: above-max flags quality risk
# ---------------------------------------------------------------------------
def test_agg02_above_max_quality_risk():
    specs = [_spec("WP-002", e_current_kj=0.50, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)]
    r = aggregate_multi_spot(specs)
    row = r.rows[0]
    assert row.window.window_status == EnergyWindowStatus.ABOVE_MAX
    # excess = e_current - e_ideal = 0.50 - 0.32 = 0.18
    assert row.window.e_excess_potential_kj == _approx(0.18)
    assert row.window.out_of_window is True


# ---------------------------------------------------------------------------
# AGG-03: below-min flags quality risk
# ---------------------------------------------------------------------------
def test_agg03_below_min_quality_risk():
    specs = [_spec("WP-003", e_current_kj=0.20, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)]
    r = aggregate_multi_spot(specs)
    row = r.rows[0]
    assert row.window.window_status == EnergyWindowStatus.BELOW_MIN
    assert row.window.quality_risk_flag is True


# ---------------------------------------------------------------------------
# AGG-04: NOT_ESTABLISHED when window bounds are all None
# ---------------------------------------------------------------------------
def test_agg04_not_established():
    specs = [_spec("WP-004", e_current_kj=0.35)]
    r = aggregate_multi_spot(specs)
    assert r.rows[0].window.window_status == EnergyWindowStatus.NOT_ESTABLISHED
    assert r.part_points_not_established == 1


# ---------------------------------------------------------------------------
# AGG-05: pareto ordering — highest excess first
# ---------------------------------------------------------------------------
def test_agg05_pareto_order():
    specs = [
        _spec("WP-A", e_current_kj=0.60, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42),
        _spec("WP-B", e_current_kj=0.50, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42),
        _spec("WP-C", e_current_kj=0.70, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42),
    ]
    r = aggregate_multi_spot(specs, pareto_top_n=3)
    excesses = [row.window.e_excess_potential_kj for row in r.pareto_by_excess]
    assert excesses == sorted(excesses, reverse=True)


# ---------------------------------------------------------------------------
# AGG-06: excess does NOT cancel — negative delta does not offset positive
# ---------------------------------------------------------------------------
def test_agg06_no_cancellation():
    specs = [
        _spec("WP-OVER", e_current_kj=0.50, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42),
        _spec("WP-UNDER", e_current_kj=0.20, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42),
    ]
    r = aggregate_multi_spot(specs)
    # excess for OVER = 0.50 - 0.32 = 0.18; UNDER excess = 0 (max(0, delta))
    assert r.part_e_excess_total_kj == _approx(0.18)


# ---------------------------------------------------------------------------
# AGG-07: annual cost rollup (EUR)
# ---------------------------------------------------------------------------
def test_agg07_annual_cost():
    specs = [_spec("WP-001", e_current_kj=0.40, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)]
    r = aggregate_multi_spot(
        specs,
        production_volume_annual=100_000,
        tariff_eur_per_kwh=0.18,
    )
    # ΔE = 0.40 - 0.32 = 0.08 kJ → 0.08/3600 kWh per spot
    # annual kWh = 0.08/3600 * 100_000
    expected_kwh = (0.08 / 3600) * 100_000
    expected_eur = expected_kwh * 0.18
    assert r.annual_e_excess_total_kwh == _approx(expected_kwh)
    assert r.annual_cost_eur == _approx(expected_eur)


# ---------------------------------------------------------------------------
# IMP-01: template columns complete
# ---------------------------------------------------------------------------
def test_imp01_template_columns():
    assert "point_code" in TEMPLATE_COLUMNS
    assert "group_name" in TEMPLATE_COLUMNS
    assert "e_current_kj" in TEMPLATE_COLUMNS
    assert "e_ideal_kj" in TEMPLATE_COLUMNS
    assert "validation_note" in TEMPLATE_COLUMNS


# ---------------------------------------------------------------------------
# IMP-02: required columns enforced
# ---------------------------------------------------------------------------
def test_imp02_required_columns():
    assert "point_code" in REQUIRED_COLUMNS
    assert "group_name" in REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# IMP-03: formula injection detection
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad", ["=SUM(A1)", "+CMD", "@bad", "|pipe", "DDE(foo)"])
def test_imp03_injection_detected(bad: str):
    assert is_formula_injection(bad) is True


@pytest.mark.parametrize("ok", ["WP-001", "0.35", "3.14", "", " ", "Group-A"])
def test_imp03_clean_values(ok: str):
    assert is_formula_injection(ok) is False


# ---------------------------------------------------------------------------
# IMP-04: valid CSV passes
# ---------------------------------------------------------------------------
def test_imp04_valid_csv():
    csv = (
        "point_code,group_name,e_current_kj,e_min_kj,e_ideal_kj,e_max_kj,validation_note\n"
        "WP-001,Group-A,0.400,0.280,0.320,0.420,OK\n"
        "WP-002,Group-A,0.380,0.280,0.320,0.420,\n"
    )
    result = validate_csv_import(csv)
    assert result.total_rows == 2
    assert result.accepted_count == 2
    assert result.rejected_count == 0
    assert not result.has_blocking_errors
    assert not result.formula_injection_detected


# ---------------------------------------------------------------------------
# IMP-05: formula injection in CSV blocks import
# ---------------------------------------------------------------------------
def test_imp05_injection_blocks():
    csv = (
        "point_code,group_name,e_current_kj\n"
        "=evil,Group-A,0.4\n"
    )
    result = validate_csv_import(csv)
    assert result.formula_injection_detected is True
    assert result.has_blocking_errors is True
    assert result.accepted_count == 0


# ---------------------------------------------------------------------------
# IMP-06: duplicate point codes flagged
# ---------------------------------------------------------------------------
def test_imp06_duplicate_flagged():
    csv = (
        "point_code,group_name\n"
        "WP-001,G\n"
        "WP-001,G\n"
    )
    result = validate_csv_import(csv)
    assert "WP-001" in result.duplicate_point_codes
    assert result.has_blocking_errors is True


# ---------------------------------------------------------------------------
# IMP-07: existing DB point codes flagged as duplicate
# ---------------------------------------------------------------------------
def test_imp07_existing_codes_flagged():
    csv = (
        "point_code,group_name\n"
        "WP-DB-01,G\n"
    )
    result = validate_csv_import(csv, existing_point_codes={"WP-DB-01"})
    assert "WP-DB-01" in result.duplicate_point_codes
    assert result.has_blocking_errors is True


# ---------------------------------------------------------------------------
# IMP-08: invalid numeric value → row rejected, report error
# ---------------------------------------------------------------------------
def test_imp08_invalid_numeric():
    csv = (
        "point_code,group_name,e_current_kj\n"
        "WP-001,G,NOTANUMBER\n"
    )
    result = validate_csv_import(csv)
    assert result.rejected_count == 1
    assert any(e.error_type == "INVALID_NUMBER" for e in result.errors)


# ---------------------------------------------------------------------------
# IMP-09: window ordering validation (e_min > e_max)
# ---------------------------------------------------------------------------
def test_imp09_window_ordering():
    csv = (
        "point_code,group_name,e_current_kj,e_min_kj,e_ideal_kj,e_max_kj,validation_note\n"
        "WP-001,G,0.4,0.5,0.45,0.3,\n"
    )
    result = validate_csv_import(csv)
    assert any(e.error_type == "INVALID_NUMBER" for e in result.errors)


# ---------------------------------------------------------------------------
# FIN-01: ΔE formula (kJ → kWh conversion)
# ---------------------------------------------------------------------------
def test_fin01_delta_e_kwh_conversion():
    specs = [_spec("WP-001", e_current_kj=4.0, e_min_kj=3.0, e_ideal_kj=3.2, e_max_kj=4.5)]
    r = aggregate_multi_spot(specs, production_volume_annual=200_000, tariff_eur_per_kwh=0.18)
    # ΔE excess per spot = 4.0 - 3.2 = 0.8 kJ = 0.8/3600 kWh
    expected_kwh = (0.8 / 3600) * 200_000
    assert r.annual_e_excess_total_kwh == _approx(expected_kwh)


# ---------------------------------------------------------------------------
# FIN-02: EUR tariff cost
# ---------------------------------------------------------------------------
def test_fin02_eur_cost():
    specs = [_spec("WP-001", e_current_kj=4.0, e_min_kj=3.0, e_ideal_kj=3.2, e_max_kj=4.5)]
    r = aggregate_multi_spot(specs, production_volume_annual=200_000, tariff_eur_per_kwh=0.18)
    expected_kwh = (0.8 / 3600) * 200_000
    assert r.annual_cost_eur == _approx(expected_kwh * 0.18)


# ---------------------------------------------------------------------------
# FIN-03: annual cost is None when no tariff provided
# ---------------------------------------------------------------------------
def test_fin03_no_tariff_gives_none():
    specs = [_spec("WP-001", e_current_kj=0.40, e_min_kj=0.28, e_ideal_kj=0.32, e_max_kj=0.42)]
    r = aggregate_multi_spot(specs, production_volume_annual=100_000)
    # tariff_eur_per_kwh not given → annual_cost_eur should be None
    assert r.annual_cost_eur is None
    assert r.annual_cost_usd is None


# ---------------------------------------------------------------------------
# API-P1-01: POST /api/v1/energy/aggregate happy path
# ---------------------------------------------------------------------------
def test_api_p1_01_aggregate(client, auth_headers):
    payload = {
        "points": [
            {"point_code": "WP-001", "group_name": "G-A",
             "e_current_kj": 0.40, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
            {"point_code": "WP-002", "group_name": "G-A",
             "e_current_kj": 0.55, "e_min_kj": 0.28, "e_ideal_kj": 0.32, "e_max_kj": 0.42},
        ],
        "production_volume_annual": 100000,
        "tariff_eur_per_kwh": 0.18,
        "tariff_usd_per_kwh": 0.19,
    }
    resp = client.post("/api/v1/energy/aggregate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "rows" in data
    assert len(data["rows"]) == 2
    assert "disclaimer" in data
    assert data["part_point_count"] == 2


# ---------------------------------------------------------------------------
# API-P1-02: POST /api/v1/energy/import/preview valid CSV
# ---------------------------------------------------------------------------
def test_api_p1_02_import_preview_valid(client, auth_headers):
    csv_text = (
        "point_code,group_name,e_current_kj,e_min_kj,e_ideal_kj,e_max_kj,validation_note\n"
        "WP-001,Group-A,0.400,0.280,0.320,0.420,Test\n"
    )
    resp = client.post("/api/v1/energy/import/preview", json={"csv_text": csv_text}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted_count"] == 1
    assert data["formula_injection_detected"] is False
    assert not data["has_blocking_errors"]


# ---------------------------------------------------------------------------
# API-P1-03: POST /api/v1/energy/import/preview injection blocked
# ---------------------------------------------------------------------------
def test_api_p1_03_import_preview_injection(client, auth_headers):
    csv_text = (
        "point_code,group_name\n"
        "=CMD,Group-A\n"
    )
    resp = client.post("/api/v1/energy/import/preview", json={"csv_text": csv_text}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["formula_injection_detected"] is True
    assert data["has_blocking_errors"] is True
    assert data["accepted_count"] == 0


# ---------------------------------------------------------------------------
# API-P1-04: GET /api/v1/energy/import/template returns CSV
# ---------------------------------------------------------------------------
def test_api_p1_04_import_template(client, auth_headers):
    resp = client.get("/api/v1/energy/import/template", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "point_code" in resp.text
    assert "group_name" in resp.text
