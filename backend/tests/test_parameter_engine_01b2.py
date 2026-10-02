"""
PARAMETER-ENGINE-01B2: Backend contract and service tests.

Tests A–R as specified in the task spec.
Tests run with pytest against the live schema/service.
No fabricated values. No engineering logic invented here.
"""
import pytest
from pydantic import ValidationError
from app.schemas.analysis import WeldAnalysisRequest, WeldAnalysisResponse, LayerInput


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _base_2t_request(**overrides) -> dict:
    """Minimal valid 2T mild-steel request. All fields explicit — no hidden defaults."""
    base = {
        "material_family": "mild_steel",
        "material_subtype": "IF",
        "stack_count": "2T",
        "layers": [
            {"material_family": "mild_steel", "material_subtype": "IF",
             "thickness_mm": 0.8, "coated": False},
            {"material_family": "mild_steel", "material_subtype": "IF",
             "thickness_mm": 0.8, "coated": False},
        ],
        "current_ka": 8.0,
        "weld_cycles": 12.0,
        "force_kn": 3.5,
        "tip_diameter_mm": 6.0,
        "squeeze_cycles": 30.0,
        "hold_cycles": 8.0,
        "cooling_flow_lpm": 4.0,
        "cooling_temp_c": 20.0,
        "dc_current": True,
        "adhesive": False,
        "shunt_risk": False,
    }
    base.update(overrides)
    return base


# ── A: Backend request accepts approach_cycles ────────────────────────────────

def test_A_request_accepts_approach_cycles():
    data = _base_2t_request(approach_cycles=20.0)
    req = WeldAnalysisRequest(**data)
    assert req.approach_cycles == 20.0


# ── B: Backend request accepts cooling_cycles ─────────────────────────────────

def test_B_request_accepts_cooling_cycles():
    data = _base_2t_request(cooling_cycles=15.0)
    req = WeldAnalysisRequest(**data)
    assert req.cooling_cycles == 15.0


# ── C: Backend request accepts air_pressure_bar ───────────────────────────────

def test_C_request_accepts_air_pressure_bar():
    data = _base_2t_request(air_pressure_bar=5.5)
    req = WeldAnalysisRequest(**data)
    assert req.air_pressure_bar == 5.5


# ── D: Response schema accepts 01B1 reference fields ─────────────────────────

def test_D_response_schema_accepts_reference_fields():
    """WeldAnalysisResponse must accept all four 01B1 reference fields."""
    resp = WeldAnalysisResponse(
        score=85.0,
        risk_level="LOW",
        nugget_min_mm=4.0,
        nugget_opt_mm=5.5,
        recommended_ranges=[],
        risks=[],
        actions=[],
        notes=[],
        selected_model="model_a",
        selected_prediction_mm=5.2,
        model_results=[],
        compliance_summary={},
        compliance_results=[],
        compliance_conflicts=[],
        reference_profile_id="REF-2T-001",
        effective_thickness_mm=1.6,
        selected_band="BAND_A",
        band_selection_status="AUTO_SELECTED",
    )
    assert resp.reference_profile_id == "REF-2T-001"
    assert resp.effective_thickness_mm == 1.6
    assert resp.selected_band == "BAND_A"
    assert resp.band_selection_status == "AUTO_SELECTED"


# ── D2: Response reference fields default to None ─────────────────────────────

def test_D2_response_reference_fields_default_none():
    resp = WeldAnalysisResponse(
        score=70.0, risk_level="MEDIUM",
        nugget_min_mm=3.5, nugget_opt_mm=4.8,
        recommended_ranges=[], risks=[], actions=[],
        selected_model=None, selected_prediction_mm=None,
        model_results=[], compliance_summary={},
        compliance_results=[], compliance_conflicts=[],
    )
    assert resp.reference_profile_id is None
    assert resp.effective_thickness_mm is None
    assert resp.selected_band is None
    assert resp.band_selection_status is None


# ── E: 2T stack → two layers ──────────────────────────────────────────────────

def test_E_2t_stack_requires_two_layers():
    data = _base_2t_request()
    req = WeldAnalysisRequest(**data)
    assert req.stack_count == "2T"
    assert len(req.layers) == 2


# ── F: 3T stack → three layers ────────────────────────────────────────────────

def test_F_3t_stack_requires_three_layers():
    layers_3 = [
        {"material_family": "mild_steel", "material_subtype": "IF",
         "thickness_mm": 0.8, "coated": False},
    ] * 3
    data = _base_2t_request(stack_count="3T", layers=layers_3)
    req = WeldAnalysisRequest(**data)
    assert req.stack_count == "3T"
    assert len(req.layers) == 3


# ── G: 4T stack → four layers ────────────────────────────────────────────────

def test_G_4t_stack_requires_four_layers():
    layers_4 = [
        {"material_family": "mild_steel", "material_subtype": "IF",
         "thickness_mm": 0.8, "coated": False},
    ] * 4
    data = _base_2t_request(stack_count="4T", layers=layers_4)
    req = WeldAnalysisRequest(**data)
    assert req.stack_count == "4T"
    assert len(req.layers) == 4


# ── H: Layer-count mismatch raises ValidationError ───────────────────────────

def test_H_layer_count_mismatch_raises():
    """3T with only 2 layers must be rejected by the schema validator."""
    data = _base_2t_request(stack_count="3T")
    # layers still has 2 entries → mismatch
    with pytest.raises(ValidationError):
        WeldAnalysisRequest(**data)


# ── I: ms → cycles conversion preserves fractional cycles ───────────────────
# This is a frontend concern; the backend only receives cycles.
# Test that fractional cycle values are accepted by the schema.

def test_I_fractional_cycles_accepted():
    """150 ms at 50 Hz = 7.5 cycles — must be accepted by backend float field."""
    data = _base_2t_request(weld_cycles=7.5)
    req = WeldAnalysisRequest(**data)
    assert req.weld_cycles == 7.5


def test_I2_fractional_approach_cycles_accepted():
    data = _base_2t_request(approach_cycles=2.5)
    req = WeldAnalysisRequest(**data)
    assert req.approach_cycles == 2.5


# ── J: cycles → ms conversion (frontend concern; verified by schema acceptance)

def test_J_full_cycle_value_accepted():
    """7 cycles * 20 ms = 140 ms. Backend accepts 7 cycles."""
    data = _base_2t_request(weld_cycles=7.0)
    req = WeldAnalysisRequest(**data)
    assert req.weld_cycles == 7.0


# ── K: No *_ms fields exist in the schema ────────────────────────────────────

def test_K_no_ms_fields_in_schema():
    """The schema must not have any *_ms request fields."""
    import inspect
    fields = WeldAnalysisRequest.model_fields
    ms_fields = [f for f in fields if f.endswith('_ms')]
    assert ms_fields == [], f"Unexpected ms fields in schema: {ms_fields}"


# ── L: Missing optional field remains absent → not substituted ───────────────

def test_L_missing_optional_approach_cycles_is_none():
    data = _base_2t_request()  # no approach_cycles
    req = WeldAnalysisRequest(**data)
    assert req.approach_cycles is None


def test_L2_missing_optional_cooling_cycles_is_none():
    data = _base_2t_request()
    req = WeldAnalysisRequest(**data)
    assert req.cooling_cycles is None


def test_L3_missing_optional_air_pressure_is_none():
    data = _base_2t_request()
    req = WeldAnalysisRequest(**data)
    assert req.air_pressure_bar is None


# ── M: Layer thickness values are actual (not defaulted) ─────────────────────

def test_M_layer_thickness_is_user_value():
    data = _base_2t_request()
    data["layers"][0]["thickness_mm"] = 1.2
    data["layers"][1]["thickness_mm"] = 1.5
    req = WeldAnalysisRequest(**data)
    assert req.layers[0].thickness_mm == 1.2
    assert req.layers[1].thickness_mm == 1.5


# ── N: No silent engineering defaults — invalid missing required field rejected

def test_N_missing_current_ka_raises():
    data = _base_2t_request()
    del data["current_ka"]
    with pytest.raises(ValidationError):
        WeldAnalysisRequest(**data)


def test_N2_missing_tip_diameter_raises():
    data = _base_2t_request()
    del data["tip_diameter_mm"]
    with pytest.raises(ValidationError):
        WeldAnalysisRequest(**data)


# ── O: Reference profile shown neutrally — no provenance strings in schema ───

def test_O_reference_profile_id_is_opaque_string():
    """reference_profile_id must be Optional[str]; no content constraint."""
    resp = WeldAnalysisResponse(
        score=90.0, risk_level="LOW",
        nugget_min_mm=4.5, nugget_opt_mm=5.8,
        recommended_ranges=[], risks=[], actions=[],
        selected_model=None, selected_prediction_mm=None,
        model_results=[], compliance_summary={},
        compliance_results=[], compliance_conflicts=[],
        reference_profile_id="PROFILE-NEUTRAL-001",
    )
    assert isinstance(resp.reference_profile_id, str)


# ── P: Provenance strings absent from request fields ─────────────────────────

def test_P_no_provenance_fields_in_request_schema():
    prohibited = ['source_name', 'source_type', 'source_document', 'source_url']
    fields = list(WeldAnalysisRequest.model_fields.keys())
    found = [f for f in fields if any(p in f for p in prohibited)]
    assert found == [], f"Provenance fields found in request schema: {found}"


def test_P2_no_provenance_fields_in_response_schema():
    prohibited = ['source_name', 'source_type', 'source_document', 'source_url']
    fields = list(WeldAnalysisResponse.model_fields.keys())
    found = [f for f in fields if any(p in f for p in prohibited)]
    assert found == [], f"Provenance fields found in response schema: {found}"


# ── Q: Guidance warning does not force FAIL / change risk level ──────────────

def test_Q_response_risk_level_is_independent_of_reference_fields():
    """Backend sets risk_level from compliance rules, not reference band status.
    This test verifies the response schema allows any risk_level regardless
    of band_selection_status — they are independent fields."""
    for risk in ("LOW", "MEDIUM", "HIGH"):
        for band_status in ("AUTO_SELECTED", "ENGINEERING_REVIEW_REQUIRED", None):
            resp = WeldAnalysisResponse(
                score=80.0, risk_level=risk,
                nugget_min_mm=4.0, nugget_opt_mm=5.5,
                recommended_ranges=[], risks=[], actions=[],
                selected_model=None, selected_prediction_mm=None,
                model_results=[], compliance_summary={},
                compliance_results=[], compliance_conflicts=[],
                band_selection_status=band_status,
            )
            assert resp.risk_level.value == risk if hasattr(resp.risk_level, 'value') else str(resp.risk_level) == risk or resp.risk_level == risk


# ── R: Existing analyze submission remains compatible ─────────────────────────

def test_R_legacy_request_without_new_optional_fields_is_valid():
    """A request without approach_cycles, cooling_cycles, air_pressure_bar
    (as would have been submitted before 01B2) must remain valid."""
    data = _base_2t_request()
    # Ensure no new fields are present
    assert 'approach_cycles' not in data
    assert 'cooling_cycles' not in data
    assert 'air_pressure_bar' not in data
    req = WeldAnalysisRequest(**data)
    assert req.approach_cycles is None
    assert req.cooling_cycles is None
    assert req.air_pressure_bar is None
    # All pre-existing fields still present
    assert req.current_ka == 8.0
    assert req.weld_cycles == 12.0
    assert req.stack_count == "2T"
    assert len(req.layers) == 2
