"""
D-01 OEM electrode selection regression tests.

OEM authority: Sheet 03 — Uç Seçimi-TamTah.Kont.
  0.6–1.7 mm reference thickness → contact tip Ø6.0 mm
  1.8–3.0 mm reference thickness → contact tip Ø8.0 mm

C-series: compliance rule correctness (evaluate_compliance)
E-series: engine recommended range alignment (evaluate_weld)
I-series: rule isolation and registry invariants
"""
from __future__ import annotations

import math
import pytest

from app.domain.rules_engine import DEFAULT_RULES, evaluate_compliance
from app.domain.engine import evaluate_weld

MILD_STEEL = "Düşük / Orta Karbonlu Çelik"
MILD_STEEL_SUB = "Düşük karbonlu çelik"

OEM_6MM_THICKNESSES = [0.6, 0.7, 0.8, 0.9, 1.0, 1.5, 1.7]
OEM_8MM_THICKNESSES = [1.8, 2.0, 3.0]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compliance(t_min: float, tip: float) -> dict:
    return evaluate_compliance(
        material_family=MILD_STEEL,
        stack_count="2T",
        t_min=t_min,
        values={
            "cooling_flow_lpm": 7.0,
            "cooling_temp_c": 20.0,
            "dc_current": True,
            "tip_diameter_mm": tip,
            "nugget_min_mm": round(4.0 * math.sqrt(t_min), 3),
        },
    )


def _rule_result(results: list, rule_id: str) -> dict | None:
    return next((r for r in results if r["rule_id"] == rule_id), None)


def _weld_input(t: float, tip: float = 6.0) -> dict:
    return {
        "material_family": MILD_STEEL,
        "material_subtype": MILD_STEEL_SUB,
        "stack_count": "2T",
        "layers": [
            {"material_family": MILD_STEEL, "material_subtype": MILD_STEEL_SUB,
             "thickness_mm": t, "coated": False},
            {"material_family": MILD_STEEL, "material_subtype": MILD_STEEL_SUB,
             "thickness_mm": t, "coated": False},
        ],
        "current_ka": 8.0, "weld_cycles": 12, "force_kn": 3.0,
        "tip_diameter_mm": tip, "squeeze_cycles": 15, "hold_cycles": 15,
        "cooling_flow_lpm": 7.0, "cooling_temp_c": 20.0,
        "dc_current": True, "adhesive": False, "shunt_risk": False,
    }


# ---------------------------------------------------------------------------
# C-series: compliance PASS at correct OEM electrode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", OEM_6MM_THICKNESSES)
def test_c_oe6_correct_electrode_passes(t):
    r = _rule_result(_compliance(t, 6.0)["results"], "TIP_DIAMETER_OEM_06_17_01")
    assert r is not None, f"Rule absent at t={t}"
    assert r["status"] == "Uygun", f"Expected PASS for Ø6 at t={t}: {r}"


@pytest.mark.parametrize("t", OEM_6MM_THICKNESSES)
def test_c_oe6_wrong_electrode_8mm_fails(t):
    r = _rule_result(_compliance(t, 8.0)["results"], "TIP_DIAMETER_OEM_06_17_01")
    assert r is not None, f"Rule absent at t={t}"
    assert r["status"] == "Uygun Değil", f"Expected FAIL for Ø8 at t={t}: {r}"


@pytest.mark.parametrize("t", OEM_8MM_THICKNESSES)
def test_c_oe8_correct_electrode_passes(t):
    r = _rule_result(_compliance(t, 8.0)["results"], "TIP_DIAMETER_OEM_18_30_01")
    assert r is not None, f"Rule absent at t={t}"
    assert r["status"] == "Uygun", f"Expected PASS for Ø8 at t={t}: {r}"


@pytest.mark.parametrize("t", OEM_8MM_THICKNESSES)
def test_c_oe8_wrong_electrode_6mm_fails(t):
    r = _rule_result(_compliance(t, 6.0)["results"], "TIP_DIAMETER_OEM_18_30_01")
    assert r is not None, f"Rule absent at t={t}"
    assert r["status"] == "Uygun Değil", f"Expected FAIL for Ø6 at t={t}: {r}"


# ---------------------------------------------------------------------------
# C-series: rule scoping — each OEM rule absent outside its range
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", OEM_6MM_THICKNESSES)
def test_c_oe8_rule_absent_in_6mm_range(t):
    r = _rule_result(_compliance(t, 6.0)["results"], "TIP_DIAMETER_OEM_18_30_01")
    assert r is None, f"TIP_DIAMETER_OEM_18_30_01 must be absent at t={t}"


@pytest.mark.parametrize("t", OEM_8MM_THICKNESSES)
def test_c_oe6_rule_absent_in_8mm_range(t):
    r = _rule_result(_compliance(t, 8.0)["results"], "TIP_DIAMETER_OEM_06_17_01")
    assert r is None, f"TIP_DIAMETER_OEM_06_17_01 must be absent at t={t}"


# ---------------------------------------------------------------------------
# C-series: disabled Ø5 rule never appears regardless of tip or thickness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", OEM_6MM_THICKNESSES + OEM_8MM_THICKNESSES)
@pytest.mark.parametrize("tip", [5.0, 6.0, 8.0])
def test_c_old_5mm_rule_never_present(t, tip):
    r = _rule_result(_compliance(t, tip)["results"], "TIP_DIAMETER_07_09_01")
    assert r is None, f"Disabled rule TIP_DIAMETER_07_09_01 appeared at t={t}, tip={tip}"


# ---------------------------------------------------------------------------
# C-series: boundary conditions
# ---------------------------------------------------------------------------

def test_c_boundary_1_7_maps_to_oe6_pass():
    r = _rule_result(_compliance(1.7, 6.0)["results"], "TIP_DIAMETER_OEM_06_17_01")
    assert r is not None
    assert r["status"] == "Uygun"


def test_c_boundary_1_7_oe8_absent():
    r = _rule_result(_compliance(1.7, 6.0)["results"], "TIP_DIAMETER_OEM_18_30_01")
    assert r is None


def test_c_boundary_1_8_maps_to_oe8_pass():
    r = _rule_result(_compliance(1.8, 8.0)["results"], "TIP_DIAMETER_OEM_18_30_01")
    assert r is not None
    assert r["status"] == "Uygun"


def test_c_boundary_1_8_oe6_absent():
    r = _rule_result(_compliance(1.8, 8.0)["results"], "TIP_DIAMETER_OEM_06_17_01")
    assert r is None


def test_c_boundary_1_8_with_6mm_fails():
    r = _rule_result(_compliance(1.8, 6.0)["results"], "TIP_DIAMETER_OEM_18_30_01")
    assert r is not None
    assert r["status"] == "Uygun Değil"


def test_c_boundary_1_7_with_8mm_fails():
    r = _rule_result(_compliance(1.7, 8.0)["results"], "TIP_DIAMETER_OEM_06_17_01")
    assert r is not None
    assert r["status"] == "Uygun Değil"


# ---------------------------------------------------------------------------
# E-series: engine recommended range alignment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", OEM_6MM_THICKNESSES)
def test_e_engine_recommends_6mm_range(t):
    result = evaluate_weld(_weld_input(t, tip=6.0))
    tip_row = next(
        (r for r in result["recommended_ranges"] if r["Parametre"] == "Elektrot uç çapı"),
        None,
    )
    assert tip_row is not None, f"Elektrot uç çapı absent in recommended_ranges at t={t}"
    assert tip_row["Önerilen Min"] == 6.0, f"Expected min=6.0 at t={t}: {tip_row}"
    assert tip_row["Önerilen Maks"] == 6.0, f"Expected max=6.0 at t={t}: {tip_row}"


@pytest.mark.parametrize("t", OEM_8MM_THICKNESSES)
def test_e_engine_recommends_8mm_range(t):
    result = evaluate_weld(_weld_input(t, tip=8.0))
    tip_row = next(
        (r for r in result["recommended_ranges"] if r["Parametre"] == "Elektrot uç çapı"),
        None,
    )
    assert tip_row is not None, f"Elektrot uç çapı absent in recommended_ranges at t={t}"
    assert tip_row["Önerilen Min"] == 8.0, f"Expected min=8.0 at t={t}: {tip_row}"
    assert tip_row["Önerilen Maks"] == 8.0, f"Expected max=8.0 at t={t}: {tip_row}"


@pytest.mark.parametrize("t", OEM_6MM_THICKNESSES)
def test_e_engine_6mm_correct_is_uygun(t):
    result = evaluate_weld(_weld_input(t, tip=6.0))
    tip_row = next(r for r in result["recommended_ranges"] if r["Parametre"] == "Elektrot uç çapı")
    assert tip_row["Durum"] == "Uygun", f"Expected Uygun for Ø6 at t={t}: {tip_row}"


@pytest.mark.parametrize("t", OEM_8MM_THICKNESSES)
def test_e_engine_8mm_correct_is_uygun(t):
    result = evaluate_weld(_weld_input(t, tip=8.0))
    tip_row = next(r for r in result["recommended_ranges"] if r["Parametre"] == "Elektrot uç çapı")
    assert tip_row["Durum"] == "Uygun", f"Expected Uygun for Ø8 at t={t}: {tip_row}"


# ---------------------------------------------------------------------------
# I-series: rule registry invariants
# ---------------------------------------------------------------------------

def test_i_old_rule_disabled_in_registry():
    rules = [r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_07_09_01"]
    assert len(rules) == 1
    assert rules[0].enabled is False


def test_i_oem_06_17_exists_with_correct_values():
    rules = [r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_OEM_06_17_01"]
    assert len(rules) == 1
    r = rules[0]
    assert r.min_value == 6.0
    assert r.max_value == 6.0
    assert r.t_min_applicability_mm == 0.6
    assert r.t_max_applicability_mm == 1.7
    assert r.enabled is True


def test_i_oem_18_30_exists_with_correct_values():
    rules = [r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_OEM_18_30_01"]
    assert len(rules) == 1
    r = rules[0]
    assert r.min_value == 8.0
    assert r.max_value == 8.0
    assert r.t_min_applicability_mm == 1.8
    assert r.t_max_applicability_mm == 3.0
    assert r.enabled is True


def test_i_oem_rules_do_not_overlap():
    oem6 = next(r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_OEM_06_17_01")
    oem8 = next(r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_OEM_18_30_01")
    assert oem6.t_max_applicability_mm < oem8.t_min_applicability_mm


def test_i_oem_rules_cover_full_range_without_gap_at_boundaries():
    oem6 = next(r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_OEM_06_17_01")
    oem8 = next(r for r in DEFAULT_RULES if r.rule_id == "TIP_DIAMETER_OEM_18_30_01")
    assert oem6.t_min_applicability_mm == 0.6
    assert oem6.t_max_applicability_mm == 1.7
    assert oem8.t_min_applicability_mm == 1.8
    assert oem8.t_max_applicability_mm == 3.0
