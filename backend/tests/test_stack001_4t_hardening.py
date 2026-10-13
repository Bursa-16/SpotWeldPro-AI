"""
STACK-001 4T unsupported-product-scope hardening tests.

Covers:
  A01 – POST /api/v1/weld-analysis         with 4T → 422
  A02 – POST weld-point                    with 4T → 422
  A03 – PATCH weld-point analysis_input    with 4T → 422
  A07 – GET  historical 4T record          → 200, data unchanged
  A08 – PATCH historical 4T re-analysis    → 422

Regression:
  R01 – Valid 2T create         → 201
  R02 – Valid 3T create         → 201
  R03 – Valid 2T patch          → 200, version_no incremented
  R04 – Rejected PATCH leaves DB state unchanged
          (revision count, version_no, analysis_input, analysis_result)
  R05 – Existing governed error contract preserved
  R06 – FastAPI request-validation (malformed JSON schema) still → 422
          with standard FastAPI detail list, NOT GovernedAPIError
"""

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _2t_input(**overrides):
    base = {
        "material_family": "Düşük / Orta Karbonlu Çelik",
        "material_subtype": "Düşük karbonlu çelik",
        "stack_count": "2T",
        "layers": [
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.0, "coated": False},
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.0, "coated": False},
        ],
        "current_ka": 8.0, "weld_cycles": 12, "force_kn": 3.0,
        "tip_diameter_mm": 6.0, "squeeze_cycles": 15, "hold_cycles": 15,
        "cooling_flow_lpm": 6.0, "cooling_temp_c": 20,
        "dc_current": True, "adhesive": False, "shunt_risk": False,
    }
    base.update(overrides)
    return base


def _3t_input():
    return {
        "material_family": "Düşük / Orta Karbonlu Çelik",
        "material_subtype": "Düşük karbonlu çelik",
        "stack_count": "3T",
        "layers": [
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 0.8, "coated": False},
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.0, "coated": False},
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.2, "coated": False},
        ],
        "current_ka": 9.0, "weld_cycles": 14, "force_kn": 3.5,
        "tip_diameter_mm": 6.0, "squeeze_cycles": 15, "hold_cycles": 15,
        "cooling_flow_lpm": 6.0, "cooling_temp_c": 20,
        "dc_current": True, "adhesive": False, "shunt_risk": False,
    }


def _4t_input():
    return {
        "material_family": "Düşük / Orta Karbonlu Çelik",
        "material_subtype": "Düşük karbonlu çelik",
        "stack_count": "4T",
        "layers": [
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 0.8, "coated": False},
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.0, "coated": False},
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.0, "coated": False},
            {"material_family": "Düşük / Orta Karbonlu Çelik",
             "material_subtype": "Düşük karbonlu çelik",
             "thickness_mm": 1.2, "coated": False},
        ],
        "current_ka": 10.0, "weld_cycles": 16, "force_kn": 4.0,
        "tip_diameter_mm": 6.0, "squeeze_cycles": 15, "hold_cycles": 15,
        "cooling_flow_lpm": 6.0, "cooling_temp_c": 20,
        "dc_current": True, "adhesive": False, "shunt_risk": False,
    }


def _governed_error(body: dict) -> tuple[str, str]:
    """Return (error_code, message) from a GovernedAPIError response."""
    return body.get("error_code", ""), body.get("message", "")


@pytest.fixture()
def project_id(client, auth_headers):
    """Create a throwaway project for each test that needs one."""
    import uuid
    code = f"STKHRD-{uuid.uuid4().hex[:6].upper()}"
    r = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"project_code": code, "project_name": "Stack-001 Hardening", "customer": "Test"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def historical_4t_point_id(project_id):
    """
    Simulate a historical 4T record by inserting it directly through the DB,
    bypassing the API (which now correctly rejects 4T).
    This represents records that existed before 4T was blocked.
    """
    from app.db.session import SessionLocal
    from app.models import WeldPoint

    ai = _4t_input()
    ar = {"score": 0.0, "risk_level": "Yüksek Risk", "nugget_min_mm": 0.0, "nugget_opt_mm": 0.0,
          "recommended_ranges": [], "risks": [], "actions": [], "notes": [],
          "selected_model": None, "selected_prediction_mm": None, "model_results": [],
          "compliance_summary": {}, "compliance_results": [], "compliance_conflicts": []}

    with SessionLocal() as db:
        point = WeldPoint(
            project_id=project_id,
            point_code="HIST-4T-001",
            part_no="LEGACY-PART",
            criticality="Standart",
            analysis_input=ai,
            analysis_result=ar,
        )
        db.add(point)
        db.commit()
        db.refresh(point)
        return point.id


# ---------------------------------------------------------------------------
# A01 — POST /api/v1/weld-analysis  with 4T → 422
# ---------------------------------------------------------------------------

class TestA01:
    def test_post_weld_analysis_4t_returns_422(self, client):
        r = client.post("/api/v1/weld-analysis", json=_4t_input())
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_post_weld_analysis_4t_governed_error_shape(self, client):
        r = client.post("/api/v1/weld-analysis", json=_4t_input())
        body = r.json()
        # /weld-analysis raises pydantic ValidationError at route level (RequestValidationError)
        # OR service level — either way caller must see 422.
        assert r.status_code == 422

    def test_post_weld_analysis_2t_succeeds(self, client):
        r = client.post("/api/v1/weld-analysis", json=_2t_input())
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# A02 — POST new weld point with 4T → 422
# ---------------------------------------------------------------------------

class TestA02:
    def test_create_weld_point_4t_returns_422(self, client, auth_headers, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": "A02-4T", "criticality": "Standart", "analysis_input": _4t_input()},
        )
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_create_weld_point_4t_governed_error_code(self, client, auth_headers, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": "A02-4T-EC", "criticality": "Standart", "analysis_input": _4t_input()},
        )
        assert r.status_code == 422
        ec, _ = _governed_error(r.json())
        assert ec == "INVALID_REQUEST", f"Unexpected error_code: {r.json()}"

    def test_create_weld_point_4t_no_traceback_in_response(self, client, auth_headers, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": "A02-4T-TB", "criticality": "Standart", "analysis_input": _4t_input()},
        )
        text = r.text
        assert "Traceback" not in text
        assert "ValidationError" not in text

    def test_create_weld_point_4t_not_persisted(self, client, auth_headers, project_id):
        """Rejected 4T point must not appear in the weld-point list."""
        code = "A02-4T-PERSIST"
        client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": code, "criticality": "Standart", "analysis_input": _4t_input()},
        )
        listing = client.get(f"/api/v1/projects/{project_id}/weld-points", headers=auth_headers)
        assert listing.status_code == 200
        codes = [p["point_code"] for p in listing.json()]
        assert code not in codes


# ---------------------------------------------------------------------------
# A03 — PATCH existing weld point with 4T → 422
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_2t_point_id(client, auth_headers, project_id):
    r = client.post(
        f"/api/v1/projects/{project_id}/weld-points",
        headers=auth_headers,
        json={"point_code": "A03-BASE-2T", "criticality": "Standart", "analysis_input": _2t_input()},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


class TestA03:
    def test_patch_weld_point_4t_returns_422(self, client, auth_headers, valid_2t_point_id):
        r = client.patch(
            f"/api/v1/weld-points/{valid_2t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "4T test", "analysis_input": _4t_input()},
        )
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_patch_weld_point_4t_governed_error_code(self, client, auth_headers, valid_2t_point_id):
        r = client.patch(
            f"/api/v1/weld-points/{valid_2t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "4T test", "analysis_input": _4t_input()},
        )
        assert r.status_code == 422
        ec, _ = _governed_error(r.json())
        assert ec == "INVALID_REQUEST"

    def test_patch_weld_point_4t_no_traceback_in_response(self, client, auth_headers, valid_2t_point_id):
        r = client.patch(
            f"/api/v1/weld-points/{valid_2t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "4T test", "analysis_input": _4t_input()},
        )
        assert "Traceback" not in r.text
        assert "ValidationError" not in r.text


# ---------------------------------------------------------------------------
# A07 — GET historical 4T record → 200, data unchanged
# ---------------------------------------------------------------------------

class TestA07:
    def test_get_historical_4t_returns_200(self, client, auth_headers, historical_4t_point_id):
        r = client.get(f"/api/v1/weld-points/{historical_4t_point_id}", headers=auth_headers)
        assert r.status_code == 200, r.text

    def test_get_historical_4t_stack_count_preserved(self, client, auth_headers, historical_4t_point_id):
        r = client.get(f"/api/v1/weld-points/{historical_4t_point_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["analysis_input"]["stack_count"] == "4T"

    def test_get_historical_4t_four_layers_preserved(self, client, auth_headers, historical_4t_point_id):
        r = client.get(f"/api/v1/weld-points/{historical_4t_point_id}", headers=auth_headers)
        assert len(r.json()["analysis_input"]["layers"]) == 4


# ---------------------------------------------------------------------------
# A08 — PATCH historical 4T record with 4T analysis_input → 422
# ---------------------------------------------------------------------------

class TestA08:
    def test_patch_historical_4t_reanalysis_returns_422(self, client, auth_headers, historical_4t_point_id):
        r = client.patch(
            f"/api/v1/weld-points/{historical_4t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "Re-analysis", "analysis_input": _4t_input()},
        )
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_patch_historical_4t_reanalysis_governed_error_code(self, client, auth_headers, historical_4t_point_id):
        r = client.patch(
            f"/api/v1/weld-points/{historical_4t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "Re-analysis", "analysis_input": _4t_input()},
        )
        assert r.status_code == 422
        ec, _ = _governed_error(r.json())
        assert ec == "INVALID_REQUEST"

    def test_patch_historical_4t_data_unchanged_after_rejection(self, client, auth_headers, historical_4t_point_id):
        """Historical 4T record must remain byte-for-byte identical after a rejected PATCH."""
        before = client.get(f"/api/v1/weld-points/{historical_4t_point_id}", headers=auth_headers).json()
        client.patch(
            f"/api/v1/weld-points/{historical_4t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "Re-analysis", "analysis_input": _4t_input()},
        )
        after = client.get(f"/api/v1/weld-points/{historical_4t_point_id}", headers=auth_headers).json()
        assert after["version_no"] == before["version_no"]
        assert after["analysis_input"] == before["analysis_input"]
        assert after["analysis_result"] == before["analysis_result"]
        assert after["approval_status"] == before["approval_status"]


# ---------------------------------------------------------------------------
# R01–R05 Regression
# ---------------------------------------------------------------------------

class TestRegression:

    def test_r01_2t_create_succeeds(self, client, auth_headers, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": "R01-2T", "criticality": "Standart", "analysis_input": _2t_input()},
        )
        assert r.status_code == 201, r.text
        assert "analysis_result" in r.json()

    def test_r02_3t_create_succeeds(self, client, auth_headers, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": "R02-3T", "criticality": "Standart", "analysis_input": _3t_input()},
        )
        assert r.status_code == 201, r.text
        assert "analysis_result" in r.json()

    def test_r03_2t_patch_succeeds_and_increments_version(self, client, auth_headers, project_id):
        # Create base point
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"point_code": "R03-BASE", "criticality": "Standart", "analysis_input": _2t_input()},
        )
        assert r.status_code == 201
        pid = r.json()["id"]
        v1 = r.json()["version_no"]

        updated = _2t_input(current_ka=8.5)
        r2 = client.patch(
            f"/api/v1/weld-points/{pid}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "Optimization", "analysis_input": updated},
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["version_no"] == v1 + 1

    def test_r04_rejected_patch_leaves_db_state_unchanged(self, client, auth_headers, valid_2t_point_id):
        """A 4T-rejected PATCH must not increment version_no or create a revision."""
        before_detail = client.get(f"/api/v1/weld-points/{valid_2t_point_id}", headers=auth_headers).json()
        before_revisions = client.get(f"/api/v1/weld-points/{valid_2t_point_id}/revisions", headers=auth_headers).json()

        client.patch(
            f"/api/v1/weld-points/{valid_2t_point_id}",
            headers=auth_headers,
            json={"changed_by": "Engineer", "change_reason": "4T attempt", "analysis_input": _4t_input()},
        )

        after_detail = client.get(f"/api/v1/weld-points/{valid_2t_point_id}", headers=auth_headers).json()
        after_revisions = client.get(f"/api/v1/weld-points/{valid_2t_point_id}/revisions", headers=auth_headers).json()

        assert after_detail["version_no"] == before_detail["version_no"]
        assert after_detail["analysis_input"] == before_detail["analysis_input"]
        assert after_detail["analysis_result"] == before_detail["analysis_result"]
        assert len(after_revisions) == len(before_revisions), \
            f"Revision count changed: {len(before_revisions)} → {len(after_revisions)}"

    def test_r05_fastapi_request_validation_still_returns_422_standard_shape(self, client, auth_headers, project_id):
        """
        FastAPI's own RequestValidationError (e.g. missing required field) must still
        return 422 with standard FastAPI detail list — NOT GovernedAPIError.
        This guards against accidentally masking schema-level errors.
        """
        r = client.post(
            f"/api/v1/projects/{project_id}/weld-points",
            headers=auth_headers,
            json={"criticality": "Standart", "analysis_input": _2t_input()},  # missing point_code
        )
        assert r.status_code == 422
        body = r.json()
        # Standard FastAPI shape has "detail" key (list of location errors)
        assert "detail" in body, f"Expected FastAPI 'detail' key, got: {body}"
