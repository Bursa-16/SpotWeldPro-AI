"""Regression tests for GATE_12_R5: material_family validation and normalization.

Covers:
  - Valid Turkish canonical keys (all 7 families) → 200
  - Valid English aliases (unambiguous) → 200 with same numerical result as Turkish
  - Ambiguous English 'Steel' → 422
  - Completely unknown strings → 422
  - Empty string → 422
  - Whitespace-only string → 422
  - TR/EN equivalence: identical numerical output for mapped aliases
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain.materials import MATERIAL_FAMILIES, resolve_material_family

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weld_payload(material_family: str, **overrides) -> dict:
    base = {
        "material_family": material_family,
        "material_subtype": "test",
        "stack_count": "2T",
        "layers": [
            {"material_family": material_family, "material_subtype": "test",
             "thickness_mm": 1.5, "coated": False},
            {"material_family": material_family, "material_subtype": "test",
             "thickness_mm": 1.5, "coated": False},
        ],
        "current_ka": 8.5,
        "weld_cycles": 12,
        "force_kn": 3.5,
        "tip_diameter_mm": 6.0,
        "squeeze_cycles": 30,
        "hold_cycles": 10,
        "cooling_flow_lpm": 7.0,
        "cooling_temp_c": 20.0,
        "dc_current": False,
        "adhesive": False,
        "shunt_risk": False,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Unit tests: resolve_material_family()
# ---------------------------------------------------------------------------

class TestResolveMaterialFamily:
    def test_exact_turkish_canonical_keys_pass(self):
        for key in MATERIAL_FAMILIES:
            assert resolve_material_family(key) == key

    def test_english_mild_steel_aliases(self):
        for alias in ("Mild Steel", "mild steel", "MILD STEEL",
                      "Low Carbon Steel", "low carbon steel"):
            result = resolve_material_family(alias)
            assert result == "Düşük / Orta Karbonlu Çelik", f"failed for: {alias}"

    def test_english_ahss_aliases(self):
        for alias in ("AHSS", "ahss", "UHSS", "uhss", "PHS", "phs"):
            result = resolve_material_family(alias)
            assert result == "AHSS / UHSS / PHS", f"failed for: {alias}"

    def test_english_galvanized_aliases(self):
        for alias in ("Galvanized Steel", "galvanized", "Coated Steel",
                      "Galvanised Steel", "galvanised", "Zinc Coated"):
            result = resolve_material_family(alias)
            assert result == "Galvanizli / Kaplamalı Çelik", f"failed for: {alias}"

    def test_english_stainless_aliases(self):
        for alias in ("Stainless Steel", "stainless", "STAINLESS STEEL"):
            result = resolve_material_family(alias)
            assert result == "Paslanmaz Çelik", f"failed for: {alias}"

    def test_english_aluminum_aliases(self):
        for alias in ("Aluminum Alloys", "Aluminium Alloys", "Aluminum", "aluminium"):
            result = resolve_material_family(alias)
            assert result == "Alüminyum Alaşımları", f"failed for: {alias}"

    def test_english_superalloy_aliases(self):
        for alias in ("Superalloy", "superalloys", "Super Alloy"):
            result = resolve_material_family(alias)
            assert result == "Süper Alaşımlar", f"failed for: {alias}"

    def test_english_mixed_aliases(self):
        for alias in ("Mixed", "mixed material", "Dissimilar"):
            result = resolve_material_family(alias)
            assert result == "Karma Malzeme", f"failed for: {alias}"

    def test_whitespace_stripped(self):
        result = resolve_material_family("  Mild Steel  ")
        assert result == "Düşük / Orta Karbonlu Çelik"

    def test_ambiguous_steel_raises(self):
        with pytest.raises(ValueError, match="UNSUPPORTED_MATERIAL_FAMILY"):
            resolve_material_family("Steel")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="UNSUPPORTED_MATERIAL_FAMILY"):
            resolve_material_family("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="UNSUPPORTED_MATERIAL_FAMILY"):
            resolve_material_family("   ")

    def test_unknown_string_raises(self):
        with pytest.raises(ValueError, match="UNSUPPORTED_MATERIAL_FAMILY"):
            resolve_material_family("Unobtainium")

    def test_partial_match_does_not_resolve(self):
        # "Steel" is ambiguous — must NOT silently map to any family
        with pytest.raises(ValueError):
            resolve_material_family("Steel")

    def test_error_message_lists_supported_families(self):
        try:
            resolve_material_family("InvalidFamily")
        except ValueError as e:
            msg = str(e)
            assert "UNSUPPORTED_MATERIAL_FAMILY" in msg
            assert "Düşük / Orta Karbonlu Çelik" in msg


# ---------------------------------------------------------------------------
# API tests: POST /api/v1/weld-analysis
# ---------------------------------------------------------------------------

class TestWeldAnalysisValidation:
    def test_valid_turkish_mild_steel_returns_200(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Düşük / Orta Karbonlu Çelik"))
        assert r.status_code == 200
        b = r.json()
        assert b["nugget_min_mm"] == 5.2
        assert b["nugget_opt_mm"] == 6.7

    def test_valid_turkish_ahss_returns_200(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("AHSS / UHSS / PHS"))
        assert r.status_code == 200

    def test_valid_turkish_galvanized_returns_200(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Galvanizli / Kaplamalı Çelik"))
        assert r.status_code == 200

    def test_english_mild_steel_returns_200(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Mild Steel"))
        assert r.status_code == 200

    def test_english_ahss_returns_200(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("AHSS"))
        assert r.status_code == 200

    def test_english_galvanized_returns_200(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Galvanized Steel"))
        assert r.status_code == 200

    def test_ambiguous_steel_returns_422(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Steel"))
        assert r.status_code == 422

    def test_unknown_family_returns_422(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Unobtainium"))
        assert r.status_code == 422

    def test_empty_family_returns_422(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload(""))
        assert r.status_code == 422

    def test_whitespace_family_returns_422(self):
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("   "))
        assert r.status_code == 422

    def test_missing_family_returns_422(self):
        payload = _weld_payload("Düşük / Orta Karbonlu Çelik")
        del payload["material_family"]
        r = client.post("/api/v1/weld-analysis", json=payload)
        assert r.status_code == 422

    # --- TR/EN numerical equivalence ---

    def test_mild_steel_tr_en_numerical_equivalence(self):
        """Turkish and English mild steel aliases must produce identical outputs."""
        tr_r = client.post("/api/v1/weld-analysis",
                           json=_weld_payload("Düşük / Orta Karbonlu Çelik"))
        en_r = client.post("/api/v1/weld-analysis",
                           json=_weld_payload("Mild Steel"))
        assert tr_r.status_code == 200
        assert en_r.status_code == 200
        tr_b = tr_r.json()
        en_b = en_r.json()
        assert tr_b["score"] == en_b["score"]
        assert tr_b["risk_level"] == en_b["risk_level"]
        assert tr_b["nugget_min_mm"] == en_b["nugget_min_mm"]
        assert tr_b["nugget_opt_mm"] == en_b["nugget_opt_mm"]
        assert tr_b["selected_model"] == en_b["selected_model"]

    def test_ahss_tr_en_numerical_equivalence(self):
        tr_r = client.post("/api/v1/weld-analysis",
                           json=_weld_payload("AHSS / UHSS / PHS"))
        en_r = client.post("/api/v1/weld-analysis",
                           json=_weld_payload("AHSS"))
        assert tr_r.status_code == 200
        assert en_r.status_code == 200
        tr_b, en_b = tr_r.json(), en_r.json()
        assert tr_b["score"] == en_b["score"]
        assert tr_b["nugget_min_mm"] == en_b["nugget_min_mm"]

    def test_galvanized_tr_en_numerical_equivalence(self):
        tr_r = client.post("/api/v1/weld-analysis",
                           json=_weld_payload("Galvanizli / Kaplamalı Çelik"))
        en_r = client.post("/api/v1/weld-analysis",
                           json=_weld_payload("Galvanized Steel"))
        assert tr_r.status_code == 200
        assert en_r.status_code == 200
        tr_b, en_b = tr_r.json(), en_r.json()
        assert tr_b["score"] == en_b["score"]
        assert tr_b["nugget_min_mm"] == en_b["nugget_min_mm"]

    def test_original_failure_reproduced_before_fix_would_have_been_500(self):
        """'Steel' must now return 422, not 500. Confirms the blocker is fixed."""
        r = client.post("/api/v1/weld-analysis",
                        json=_weld_payload("Steel"))
        assert r.status_code == 422, (
            f"Expected 422 for ambiguous 'Steel'; got {r.status_code}. "
            "KeyError bug may still be present."
        )
        body = r.json()
        assert "detail" in body
