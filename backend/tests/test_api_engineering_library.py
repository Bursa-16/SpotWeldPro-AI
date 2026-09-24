"""API integration tests for Engineering Library — CE-02C.

Uses the session-scoped SQLite database + FastAPI TestClient from conftest.py.
All tests authenticate as the admin user created by conftest.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Minimal payloads
# ---------------------------------------------------------------------------

MATERIAL_META = {
    "revision_number": 1,
    "lifecycle_status": "ACTIVE",
    "source_class": "SOURCE_BACKED",
    "reason": "api test",
}

MATERIAL_PAYLOAD = {
    "material_id": "API-MAT-001",
    "family": "Steel",
    "grade": "DP780",
    "metadata": MATERIAL_META,
}

COATING_PAYLOAD = {
    "coating_id": "API-COAT-001",
    "family": "Zinc",
    "designation": "GI",
    "metadata": MATERIAL_META,
}

ELECTRODE_PAYLOAD = {
    "electrode_id": "API-ELEC-001",
    "cap_geometry": {
        "face_geometry": "FLAT",
        "face_diameter_mm": 16.0,
    },
    "material_designation": "CuCrZr",
    "metadata": MATERIAL_META,
}

GUN_PAYLOAD = {
    "gun_id": "API-GUN-001",
    "actuation_type": "PNEUMATIC",
    "max_force_kn": 5.0,
    "metadata": MATERIAL_META,
}

SCHEDULE_PAYLOAD = {
    "schedule_id": "API-SCHED-001",
    "squeeze_cycles": 30.0,
    "hold_cycles": 10.0,
    "pulses": [
        {
            "sequence": 1,
            "pulse_type": "WELD",
            "current_ka": 8.5,
            "duration_cycles": 14.0,
            "force_kn": 4.2,
        }
    ],
    "metadata": MATERIAL_META,
}


# ---------------------------------------------------------------------------
# Material endpoint tests
# ---------------------------------------------------------------------------

class TestMaterialAPI:
    def test_create_material_201(self, client, auth_headers):
        r = client.post("/api/v1/engineering-library/materials", json=MATERIAL_PAYLOAD, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["identity"]["material_id"] == "API-MAT-001"
        assert body["revision"]["revision_number"] == 1
        assert body["revision"]["lifecycle_status"] == "ACTIVE"
        assert len(body["revision"]["content_hash"]) == 64

    def test_create_material_requires_auth(self, client):
        r = client.post("/api/v1/engineering-library/materials", json=MATERIAL_PAYLOAD)
        assert r.status_code in (401, 403)

    def test_list_materials(self, client, auth_headers):
        r = client.get("/api/v1/engineering-library/materials", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_material_by_id(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/materials",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-GET"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        mat_id = r.json()["identity"]["material_id"]
        r2 = client.get(f"/api/v1/engineering-library/materials/{mat_id}", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["material_id"] == "API-MAT-GET"

    def test_get_material_404(self, client, auth_headers):
        r = client.get("/api/v1/engineering-library/materials/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_list_revisions(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/materials",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-REVLIST"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        mat_id = r.json()["identity"]["material_id"]
        r2 = client.get(f"/api/v1/engineering-library/materials/{mat_id}/revisions", headers=auth_headers)
        assert r2.status_code == 200
        assert len(r2.json()) >= 1

    def test_get_current_revision(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/materials",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-CURRENT"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        mat_id = r.json()["identity"]["material_id"]
        r2 = client.get(
            f"/api/v1/engineering-library/materials/{mat_id}/revisions/current",
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert r2.json()["revision_number"] == 1

    def test_add_revision(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/materials",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-ADD-REV"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        mat_id = body["identity"]["material_id"]
        rev1_id = body["revision"]["id"]

        meta2 = {**MATERIAL_META, "revision_number": 2, "supersedes_revision_id": rev1_id}
        r2 = client.post(
            f"/api/v1/engineering-library/materials/{mat_id}/revisions",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-ADD-REV", "metadata": meta2},
            headers=auth_headers,
        )
        assert r2.status_code == 201
        assert r2.json()["revision_number"] == 2

    def test_extra_fields_forbidden(self, client, auth_headers):
        bad = {**MATERIAL_PAYLOAD, "material_id": "API-MAT-EXTRA", "unexpected_field": True}
        r = client.post("/api/v1/engineering-library/materials", json=bad, headers=auth_headers)
        assert r.status_code == 422

    def test_missing_reason_rejected(self, client, auth_headers):
        meta_no_reason = {k: v for k, v in MATERIAL_META.items() if k != "reason"}
        r = client.post(
            "/api/v1/engineering-library/materials",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-NO-REASON", "metadata": meta_no_reason},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_no_put_patch_delete(self, client, auth_headers):
        for method in ("put", "patch", "delete"):
            r = getattr(client, method)(
                "/api/v1/engineering-library/materials/1", headers=auth_headers
            )
            assert r.status_code == 405


# ---------------------------------------------------------------------------
# Coating endpoint tests
# ---------------------------------------------------------------------------

class TestCoatingAPI:
    def test_create_coating_201(self, client, auth_headers):
        r = client.post("/api/v1/engineering-library/coatings", json=COATING_PAYLOAD, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["identity"]["coating_id"] == "API-COAT-001"
        assert len(body["revision"]["content_hash"]) == 64

    def test_list_coatings(self, client, auth_headers):
        r = client.get("/api/v1/engineering-library/coatings", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# StackUp endpoint tests (requires valid material_revision_id)
# ---------------------------------------------------------------------------

class TestStackUpAPI:
    @pytest.fixture()
    def mat_rev_id(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/materials",
            json={**MATERIAL_PAYLOAD, "material_id": "API-MAT-FOR-STACK"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        return r.json()["revision"]["id"]

    def test_create_stack_up_201(self, client, auth_headers, mat_rev_id):
        payload = {
            "stack_id": "API-STACK-001",
            "layers": [
                {"sequence": 1, "material_revision_id": mat_rev_id, "thickness_mm": 1.2},
                {"sequence": 2, "material_revision_id": mat_rev_id, "thickness_mm": 1.5},
            ],
            "metadata": MATERIAL_META,
        }
        r = client.post("/api/v1/engineering-library/stack-ups", json=payload, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["identity"]["stack_id"] == "API-STACK-001"
        assert len(body["revision"]["layers"]) == 2

    def test_invalid_material_revision_422_or_400(self, client, auth_headers):
        payload = {
            "stack_id": "API-STACK-BAD",
            "layers": [
                {"sequence": 1, "material_revision_id": 999999, "thickness_mm": 1.2},
                {"sequence": 2, "material_revision_id": 999999, "thickness_mm": 1.5},
            ],
            "metadata": MATERIAL_META,
        }
        r = client.post("/api/v1/engineering-library/stack-ups", json=payload, headers=auth_headers)
        assert r.status_code in (400, 422, 500), r.text


# ---------------------------------------------------------------------------
# Electrode endpoint tests
# ---------------------------------------------------------------------------

class TestElectrodeAPI:
    def test_create_electrode_201(self, client, auth_headers):
        r = client.post("/api/v1/engineering-library/electrodes", json=ELECTRODE_PAYLOAD, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["identity"]["electrode_id"] == "API-ELEC-001"
        assert body["revision"]["face_geometry"] == "FLAT"

    def test_list_electrodes(self, client, auth_headers):
        r = client.get("/api/v1/engineering-library/electrodes", headers=auth_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Weld Gun endpoint tests
# ---------------------------------------------------------------------------

class TestWeldGunAPI:
    def test_create_gun_201(self, client, auth_headers):
        r = client.post("/api/v1/engineering-library/weld-guns", json=GUN_PAYLOAD, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["identity"]["gun_id"] == "API-GUN-001"
        assert body["revision"]["actuation_type"] == "PNEUMATIC"


# ---------------------------------------------------------------------------
# Weld Schedule endpoint tests
# ---------------------------------------------------------------------------

class TestWeldScheduleAPI:
    def test_create_schedule_201(self, client, auth_headers):
        r = client.post("/api/v1/engineering-library/weld-schedules", json=SCHEDULE_PAYLOAD, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["identity"]["schedule_id"] == "API-SCHED-001"
        assert len(body["revision"]["pulses"]) == 1

    def test_schedule_content_hash_present(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/weld-schedules",
            json={**SCHEDULE_PAYLOAD, "schedule_id": "API-SCHED-HASH"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert len(r.json()["revision"]["content_hash"]) == 64

    def test_empty_pulses_rejected(self, client, auth_headers):
        payload = {**SCHEDULE_PAYLOAD, "schedule_id": "API-SCHED-NO-PULSES", "pulses": []}
        r = client.post("/api/v1/engineering-library/weld-schedules", json=payload, headers=auth_headers)
        assert r.status_code == 422

    def test_current_schedule_revision(self, client, auth_headers):
        r = client.post(
            "/api/v1/engineering-library/weld-schedules",
            json={**SCHEDULE_PAYLOAD, "schedule_id": "API-SCHED-CURRENT"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        sched_id = r.json()["identity"]["schedule_id"]
        r2 = client.get(
            f"/api/v1/engineering-library/weld-schedules/{sched_id}/revisions/current",
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert r2.json()["revision_number"] == 1
        assert len(r2.json()["pulses"]) == 1
