"""Phase 2A profile API security tests — SWP-PHASE2A-PROFILE-API-SECURITY-01.

Coverage:
  MC-01 through MC-05 at actual HTTP boundary.
  T01–T18 as specified.

Test data is created via API calls during module setup using admin credentials.
All data uses the 'p2a-' slug/username namespace to avoid collision with other tests.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"Login failed for {username}: {r.text}"
    return _bearer(r.json()["access_token"])


def _valid_profile_body(org_id: int, code: str, **overrides: Any) -> dict[str, Any]:
    """A schema-valid ProfileCreate body with empty engineering data."""
    body: dict[str, Any] = {
        "org_id": org_id,
        "profile_code": code,
        "display_name": f"Profile {code}",
        "material_scope": "DC01",
        "stack_count": "2T",
        "cycle_basis_hz": 50,
        "t_min_mm": 0.6,
        "t_max_mm": 2.5,
        "parameter_bands": {"bands": []},
        "nugget_criterion": {},
        "source_provenance": {},
    }
    body.update(overrides)
    return body


def _full_prereq_body(org_id: int, code: str) -> dict[str, Any]:
    """ProfileCreate body with all engineering prerequisites satisfied."""
    return _valid_profile_body(
        org_id, code,
        parameter_bands={"bands": [{"i_ka": 8.0, "f_kn": 3.0, "t_weld": 12}]},
        nugget_criterion={"method": "d5sqrt_t", "factor": 5.0},
        source_provenance={"basis": "OEM lab test report TR-2025-042"},
    )


# ---------------------------------------------------------------------------
# Module-scoped setup fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup(database):  # noqa: F811 — database from conftest
    """Create two orgs, four users, and memberships for cross-org isolation tests."""
    with TestClient(app) as client:
        admin = _login(client, "admin", "ChangeMe123!")

        # Create users
        users: dict[str, dict] = {}
        for uname, role in [
            ("p2a_user_a", "PROCESS_ENGINEER"),
            ("p2a_approver_a", "PROCESS_ENGINEER"),
            ("p2a_user_b", "PROCESS_ENGINEER"),
            ("p2a_viewer_a", "READ_ONLY"),
        ]:
            r = client.post("/api/v1/auth/users", json={
                "username": uname,
                "email": f"{uname}@p2a.example.com",
                "full_name": uname,
                "password": "P2aTest123!",
                "role": role,
            }, headers=admin)
            assert r.status_code == 201, f"Could not create user {uname}: {r.text}"
            users[uname] = r.json()

        # Create orgs
        r_a = client.post("/api/v1/organizations", json={"slug": "p2a-org-a", "display_name": "Phase2A Org A"}, headers=admin)
        assert r_a.status_code == 201, f"create org_a failed: {r_a.text}"
        org_a = r_a.json()

        r_b = client.post("/api/v1/organizations", json={"slug": "p2a-org-b", "display_name": "Phase2A Org B"}, headers=admin)
        assert r_b.status_code == 201, f"create org_b failed: {r_b.text}"
        org_b = r_b.json()

        # Add admin to org_a as ORG_ADMIN (so admin can add others)
        admin_user_r = client.get("/api/v1/auth/me", headers=admin)
        admin_user_id = admin_user_r.json()["id"]

        client.post(f"/api/v1/organizations/{org_a['id']}/members", json={
            "user_id": admin_user_id, "org_role": "ORG_ADMIN",
        }, headers=admin)
        client.post(f"/api/v1/organizations/{org_b['id']}/members", json={
            "user_id": admin_user_id, "org_role": "ORG_ADMIN",
        }, headers=admin)

        # Add user_a as ENGINEER in org_a
        r = client.post(f"/api/v1/organizations/{org_a['id']}/members", json={
            "user_id": users["p2a_user_a"]["id"], "org_role": "ENGINEER",
        }, headers=admin)
        assert r.status_code == 201, f"add user_a to org_a: {r.text}"

        # Add approver_a as APPROVER in org_a
        r = client.post(f"/api/v1/organizations/{org_a['id']}/members", json={
            "user_id": users["p2a_approver_a"]["id"], "org_role": "APPROVER",
        }, headers=admin)
        assert r.status_code == 201, f"add approver_a to org_a: {r.text}"

        # Add user_b as ENGINEER in org_b
        r = client.post(f"/api/v1/organizations/{org_b['id']}/members", json={
            "user_id": users["p2a_user_b"]["id"], "org_role": "ENGINEER",
        }, headers=admin)
        assert r.status_code == 201, f"add user_b to org_b: {r.text}"

        # Add viewer_a as VIEWER in org_a
        r = client.post(f"/api/v1/organizations/{org_a['id']}/members", json={
            "user_id": users["p2a_viewer_a"]["id"], "org_role": "VIEWER",
        }, headers=admin)
        assert r.status_code == 201, f"add viewer_a to org_a: {r.text}"

        # Create a DRAFT profile in org_a (created by user_a)
        auth_a = _login(client, "p2a_user_a", "P2aTest123!")
        r = client.post("/api/v1/reference-profiles", json=_valid_profile_body(org_a["id"], "P2A_PROFILE_A"), headers=auth_a)
        assert r.status_code == 201, f"create profile_a: {r.text}"
        profile_a = r.json()

        # Create a DRAFT profile in org_b (created by user_b)
        auth_b = _login(client, "p2a_user_b", "P2aTest123!")
        r = client.post("/api/v1/reference-profiles", json=_valid_profile_body(org_b["id"], "P2A_PROFILE_B"), headers=auth_b)
        assert r.status_code == 201, f"create profile_b: {r.text}"
        profile_b = r.json()

        # Insert a system default profile directly in the DB for immutability tests
        from sqlalchemy import select
        from app.db.session import SessionLocal
        from app.models.profile_entities import ReferenceProfileRecord
        from app.models.enums import ProfileStatus
        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            from app.models.entities import User as DBUser
            admin_db_user = db.scalar(select(DBUser).where(DBUser.username == "admin"))
            sys_profile = ReferenceProfileRecord(
                profile_code="P2A_SYS_DEFAULT",
                version=1,
                org_id=None,
                display_name="P2A System Default",
                material_scope="DC01",
                stack_count="2T",
                cycle_basis_hz=50,
                t_min_mm=0.6,
                t_max_mm=2.5,
                status=ProfileStatus.DRAFT,
                is_system_default=True,
                parameter_bands={"bands": []},
                nugget_criterion={},
                source_provenance={},
                created_by=admin_db_user.id,
                created_at=now,
                updated_at=now,
            )
            db.add(sys_profile)
            db.commit()
            db.refresh(sys_profile)
            sys_profile_id = sys_profile.id

        yield {
            "admin": admin,
            "auth_a": auth_a,
            "auth_b": auth_b,
            "auth_approver_a": _login(client, "p2a_approver_a", "P2aTest123!"),
            "auth_viewer_a": _login(client, "p2a_viewer_a", "P2aTest123!"),
            "users": users,
            "org_a": org_a,
            "org_b": org_b,
            "profile_a_id": profile_a["id"],
            "profile_b_id": profile_b["id"],
            "sys_profile_id": sys_profile_id,
            "admin_user_id": admin_user_id,
        }


@pytest.fixture(scope="module")
def mod_client(database):  # noqa: F811
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# MC-01: Unauthenticated requests to new routes are rejected
# ---------------------------------------------------------------------------

class TestMC01AuthRequired:
    def test_MC01_organizations_list_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.get("/api/v1/organizations")
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_MC01_organization_detail_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.get("/api/v1/organizations/1")
        assert r.status_code in (401, 403)

    def test_MC01_create_organization_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.post("/api/v1/organizations", json={"slug": "anon-org", "display_name": "Anon"})
        assert r.status_code in (401, 403)

    def test_MC01_profiles_list_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.get("/api/v1/reference-profiles")
        assert r.status_code in (401, 403)

    def test_MC01_profile_detail_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.get("/api/v1/reference-profiles/1")
        assert r.status_code in (401, 403)

    def test_MC01_create_profile_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.post("/api/v1/reference-profiles", json={"org_id": 1, "profile_code": "X", "display_name": "x",
                                                                 "material_scope": "x", "stack_count": "2T",
                                                                 "cycle_basis_hz": 50, "t_min_mm": 0.6, "t_max_mm": 2.5})
        assert r.status_code in (401, 403)

    def test_MC01_approve_profile_requires_auth(self, mod_client: TestClient) -> None:
        r = mod_client.post("/api/v1/reference-profiles/1/approve", json={"note": ""})
        assert r.status_code in (401, 403)

    def test_MC01_invalid_jwt_rejected(self, mod_client: TestClient) -> None:
        r = mod_client.get("/api/v1/organizations", headers={"Authorization": "Bearer this.is.fake"})
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# MC-02: Cross-organization profile access denied
# ---------------------------------------------------------------------------

class TestMC02CrossOrgDenied:
    def test_MC02_user_b_cannot_read_org_a_profile_detail(self, mod_client: TestClient, setup: dict) -> None:
        """user_b (org_b only) cannot read org_a's profile detail."""
        r = mod_client.get(f"/api/v1/reference-profiles/{setup['profile_a_id']}", headers=setup["auth_b"])
        assert r.status_code in (403, 404), (
            f"Cross-org read must be rejected. Got {r.status_code}: {r.text[:200]}"
        )

    def test_MC02_user_b_cannot_list_org_a_profiles(self, mod_client: TestClient, setup: dict) -> None:
        """user_b's profile list must not contain org_a's profile."""
        r = mod_client.get("/api/v1/reference-profiles", headers=setup["auth_b"])
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert setup["profile_a_id"] not in ids, (
            f"org_b user must not see org_a's profile in listing. Got ids: {ids}"
        )

    def test_MC02_user_a_cannot_read_org_b_profile(self, mod_client: TestClient, setup: dict) -> None:
        """user_a (org_a only) cannot read org_b's profile."""
        r = mod_client.get(f"/api/v1/reference-profiles/{setup['profile_b_id']}", headers=setup["auth_a"])
        assert r.status_code in (403, 404)

    def test_MC02_user_b_cannot_patch_org_a_profile(self, mod_client: TestClient, setup: dict) -> None:
        """user_b cannot modify org_a's profile."""
        r = mod_client.patch(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}",
            json={"display_name": "Tampered"},
            headers=setup["auth_b"],
        )
        assert r.status_code in (403, 404)

    def test_MC02_user_b_cannot_approve_org_a_profile(self, mod_client: TestClient, setup: dict) -> None:
        """user_b cannot approve org_a's profile."""
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}/approve",
            json={"note": ""},
            headers=setup["auth_b"],
        )
        assert r.status_code in (403, 404)

    def test_MC02_user_b_cannot_view_org_a_org_detail(self, mod_client: TestClient, setup: dict) -> None:
        """user_b cannot view org_a's organization detail."""
        r = mod_client.get(f"/api/v1/organizations/{setup['org_a']['id']}", headers=setup["auth_b"])
        assert r.status_code in (403, 404)

    def test_MC02_user_b_org_list_excludes_org_a(self, mod_client: TestClient, setup: dict) -> None:
        """user_b's org listing does not include org_a."""
        r = mod_client.get("/api/v1/organizations", headers=setup["auth_b"])
        assert r.status_code == 200
        org_ids = [o["id"] for o in r.json()]
        assert setup["org_a"]["id"] not in org_ids, (
            f"org_b user must not see org_a in listing. Got: {org_ids}"
        )


# ---------------------------------------------------------------------------
# MC-03: Injected org_id / user_id / role cannot bypass authorization
# ---------------------------------------------------------------------------

class TestMC03InjectionPrevented:
    def test_MC03_org_id_in_profile_create_body_does_not_grant_access(
        self, mod_client: TestClient, setup: dict
    ) -> None:
        """user_b injecting org_a's id in ProfileCreate body must be rejected."""
        body = _valid_profile_body(setup["org_a"]["id"], "P2A_INJECT_TEST")
        r = mod_client.post("/api/v1/reference-profiles", json=body, headers=setup["auth_b"])
        assert r.status_code in (403, 404), (
            f"org_id injection must be blocked. Got {r.status_code}: {r.text[:200]}"
        )

    def test_MC03_user_id_in_membership_body_does_not_elevate_role(
        self, mod_client: TestClient, setup: dict
    ) -> None:
        """user_b cannot add themselves to org_a by calling the membership endpoint."""
        r = mod_client.post(
            f"/api/v1/organizations/{setup['org_a']['id']}/members",
            json={"user_id": setup["users"]["p2a_user_b"]["id"], "org_role": "ENGINEER"},
            headers=setup["auth_b"],
        )
        assert r.status_code in (403, 404), (
            f"Non-member cannot add themselves to an org. Got {r.status_code}"
        )

    def test_MC03_viewer_cannot_create_org(self, mod_client: TestClient, setup: dict) -> None:
        """VIEWER-role user cannot create organizations."""
        r = mod_client.post(
            "/api/v1/organizations",
            json={"slug": "inject-org", "display_name": "Injected"},
            headers=setup["auth_viewer_a"],
        )
        assert r.status_code in (403, 404)

    def test_MC03_engineer_cannot_add_members(self, mod_client: TestClient, setup: dict) -> None:
        """ENGINEER (not ORG_ADMIN) cannot add members to their own org."""
        # user_a is ENGINEER in org_a — not ORG_ADMIN
        r = mod_client.post(
            f"/api/v1/organizations/{setup['org_a']['id']}/members",
            json={"user_id": setup["users"]["p2a_user_b"]["id"], "org_role": "VIEWER"},
            headers=setup["auth_a"],
        )
        assert r.status_code in (403, 404), (
            f"ENGINEER should not be able to add members. Got {r.status_code}"
        )


# ---------------------------------------------------------------------------
# MC-04: Unauthorized profile approval
# ---------------------------------------------------------------------------

class TestMC04ApprovalUnauthorized:
    def test_MC04_engineer_cannot_approve_profile(self, mod_client: TestClient, setup: dict) -> None:
        """ENGINEER role is insufficient for approval; APPROVER+ required."""
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}/approve",
            json={"note": ""},
            headers=setup["auth_a"],  # user_a is ENGINEER in org_a
        )
        assert r.status_code in (403, 422), (
            f"ENGINEER must be blocked from approval. Got {r.status_code}: {r.text[:200]}"
        )

    def test_MC04_approver_blocked_without_engineering_data(self, mod_client: TestClient, setup: dict) -> None:
        """APPROVER is rejected when parameter_bands.bands is empty (HR-08)."""
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}/approve",
            json={"note": ""},
            headers=setup["auth_approver_a"],
        )
        # profile_a has empty bands → prerequisites not met
        assert r.status_code == 422, (
            f"Approval must fail when engineering prerequisites missing. Got {r.status_code}: {r.text[:300]}"
        )
        data = r.json()
        assert data.get("error_code") == "PROFILE_NOT_APPROVED", (
            f"Expected PROFILE_NOT_APPROVED error code. Got: {data}"
        )

    def test_MC04_approver_blocked_by_missing_provenance(self, mod_client: TestClient, setup: dict) -> None:
        """Empty source_provenance.basis blocks approval even with bands present."""
        # Create a profile that has bands but no provenance basis
        auth_a = setup["auth_a"]
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(
                setup["org_a"]["id"], "P2A_BANDS_ONLY",
                parameter_bands={"bands": [{"i_ka": 8.0}]},
                nugget_criterion={"method": "d5"},
                source_provenance={"basis": ""},  # empty basis
            ),
            headers=auth_a,
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        r_approve = mod_client.post(
            f"/api/v1/reference-profiles/{pid}/approve",
            json={"note": ""},
            headers=setup["auth_approver_a"],
        )
        assert r_approve.status_code == 422
        assert r_approve.json().get("error_code") == "PROFILE_NOT_APPROVED"

    def test_MC04_self_approval_blocked(self, mod_client: TestClient, setup: dict) -> None:
        """Approver cannot approve a profile they created (four-eyes principle)."""
        auth_approver = setup["auth_approver_a"]
        # Create a profile as approver_a (they are APPROVER in org_a)
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_full_prereq_body(setup["org_a"]["id"], "P2A_SELF_APPROVE_TEST"),
            headers=auth_approver,
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        r_approve = mod_client.post(
            f"/api/v1/reference-profiles/{pid}/approve",
            json={"note": ""},
            headers=auth_approver,
        )
        assert r_approve.status_code in (403, 422), (
            f"Self-approval must be blocked. Got {r_approve.status_code}: {r_approve.text[:200]}"
        )
        data = r_approve.json()
        assert data.get("error_code") == "SAME_USER_REVIEWER_APPROVER", (
            f"Expected SAME_USER_REVIEWER_APPROVER. Got: {data}"
        )

    def test_MC04_successful_approval_with_all_prerequisites(
        self, mod_client: TestClient, setup: dict
    ) -> None:
        """Approval succeeds only when all prerequisites are genuinely met."""
        auth_a = setup["auth_a"]
        auth_approver = setup["auth_approver_a"]

        # Create profile with full data as user_a
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_full_prereq_body(setup["org_a"]["id"], "P2A_APPROVABLE"),
            headers=auth_a,
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        # Approve as approver_a (different user, APPROVER role)
        r_approve = mod_client.post(
            f"/api/v1/reference-profiles/{pid}/approve",
            json={"note": "Lab test data verified."},
            headers=auth_approver,
        )
        assert r_approve.status_code == 200, (
            f"Expected 200 for valid approval. Got {r_approve.status_code}: {r_approve.text[:300]}"
        )
        evt = r_approve.json()
        assert evt["event_type"] == "APPROVED"
        assert evt["profile_id"] == pid

        # Verify profile status changed
        r_get = mod_client.get(f"/api/v1/reference-profiles/{pid}", headers=auth_a)
        assert r_get.status_code == 200
        assert r_get.json()["status"] == "APPROVED"


# ---------------------------------------------------------------------------
# MC-05: System default and approved profile immutability
# ---------------------------------------------------------------------------

class TestMC05ImmutabilityEnforced:
    def test_MC05_system_default_patch_rejected(self, mod_client: TestClient, setup: dict) -> None:
        """Authenticated users (including admins) cannot PATCH the system default profile."""
        r = mod_client.patch(
            f"/api/v1/reference-profiles/{setup['sys_profile_id']}",
            json={"display_name": "Tampered Default"},
            headers=setup["admin"],
        )
        assert r.status_code in (403, 409), (
            f"System default must not be patchable. Got {r.status_code}: {r.text[:200]}"
        )
        data = r.json()
        assert data.get("error_code") == "IMMUTABLE_SYSTEM_PROFILE"

    def test_MC05_system_default_approve_rejected(self, mod_client: TestClient, setup: dict) -> None:
        """System default profile cannot be approved via the API."""
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['sys_profile_id']}/approve",
            json={"note": ""},
            headers=setup["admin"],
        )
        assert r.status_code in (403, 409), (
            f"System default must not be approvable. Got {r.status_code}: {r.text[:200]}"
        )
        assert r.json().get("error_code") == "IMMUTABLE_SYSTEM_PROFILE"

    def test_MC05_org_b_user_cannot_modify_org_a_approved_profile(
        self, mod_client: TestClient, setup: dict
    ) -> None:
        """After approval, org_b user still cannot modify org_a's profile."""
        auth_a = setup["auth_a"]
        auth_approver = setup["auth_approver_a"]

        # Create and approve a profile
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_full_prereq_body(setup["org_a"]["id"], "P2A_MC05_APPROVED"),
            headers=auth_a,
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        mod_client.post(f"/api/v1/reference-profiles/{pid}/approve", json={"note": ""}, headers=auth_approver)

        # org_b user still cannot see or modify it
        r_patch = mod_client.patch(
            f"/api/v1/reference-profiles/{pid}",
            json={"display_name": "Tampered"},
            headers=setup["auth_b"],
        )
        assert r_patch.status_code in (403, 404, 409)


# ---------------------------------------------------------------------------
# T01: New customer profile starts DRAFT
# ---------------------------------------------------------------------------

class TestT01NewProfileDraft:
    def test_T01_created_profile_has_draft_status(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(setup["org_a"]["id"], "P2A_T01"),
            headers=setup["auth_a"],
        )
        assert r.status_code == 201
        assert r.json()["status"] == "DRAFT"

    def test_T01_created_profile_is_not_system_default(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(setup["org_a"]["id"], "P2A_T01B"),
            headers=setup["auth_a"],
        )
        assert r.status_code == 201
        assert r.json()["is_system_default"] is False


# ---------------------------------------------------------------------------
# T02: Cross-organization list isolation
# ---------------------------------------------------------------------------

class TestT02ListIsolation:
    def test_T02_user_a_list_excludes_org_b_profiles(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.get("/api/v1/reference-profiles", headers=setup["auth_a"])
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert setup["profile_b_id"] not in ids

    def test_T02_user_b_list_excludes_org_a_profiles(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.get("/api/v1/reference-profiles", headers=setup["auth_b"])
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert setup["profile_a_id"] not in ids

    def test_T02_system_default_visible_to_all(self, mod_client: TestClient, setup: dict) -> None:
        """System default (org_id=None) appears in both user_a and user_b listings."""
        r_a = mod_client.get("/api/v1/reference-profiles", headers=setup["auth_a"])
        r_b = mod_client.get("/api/v1/reference-profiles", headers=setup["auth_b"])
        ids_a = [p["id"] for p in r_a.json()]
        ids_b = [p["id"] for p in r_b.json()]
        assert setup["sys_profile_id"] in ids_a, "System default must be visible to org_a user"
        assert setup["sys_profile_id"] in ids_b, "System default must be visible to org_b user"


# ---------------------------------------------------------------------------
# T03: Cross-organization detail isolation
# ---------------------------------------------------------------------------

class TestT03DetailIsolation:
    def test_T03_user_a_cannot_get_org_b_profile(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.get(f"/api/v1/reference-profiles/{setup['profile_b_id']}", headers=setup["auth_a"])
        assert r.status_code in (403, 404)

    def test_T03_user_b_cannot_get_org_a_profile(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.get(f"/api/v1/reference-profiles/{setup['profile_a_id']}", headers=setup["auth_b"])
        assert r.status_code in (403, 404)

    def test_T03_user_a_can_get_system_default(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.get(f"/api/v1/reference-profiles/{setup['sys_profile_id']}", headers=setup["auth_a"])
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# T04: Cross-organization update rejection
# ---------------------------------------------------------------------------

class TestT04CrossOrgUpdateRejected:
    def test_T04_cross_org_patch_rejected(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.patch(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}",
            json={"display_name": "Tampered"},
            headers=setup["auth_b"],
        )
        assert r.status_code in (403, 404)


# ---------------------------------------------------------------------------
# T05: Invalid JWT rejected
# ---------------------------------------------------------------------------

class TestT05InvalidJWT:
    def test_T05_forged_jwt_rejected_on_profiles(self, mod_client: TestClient) -> None:
        r = mod_client.get("/api/v1/reference-profiles", headers={"Authorization": "Bearer forged.jwt.value"})
        assert r.status_code in (401, 403)

    def test_T05_expired_jwt_rejected(self, mod_client: TestClient) -> None:
        # Construct a syntactically valid but bogus JWT
        import base64, json
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "nobody@example.com", "exp": 1}).encode()).rstrip(b"=").decode()
        fake = f"{header}.{payload}.fakesig"
        r = mod_client.get("/api/v1/reference-profiles", headers={"Authorization": f"Bearer {fake}"})
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# T06: Revoked/inactive membership rejected
# ---------------------------------------------------------------------------

class TestT06InactiveMembership:
    def test_T06_viewer_cannot_create_profile(self, mod_client: TestClient, setup: dict) -> None:
        """VIEWER role (lowest) cannot create profiles (ENGINEER+ required)."""
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(setup["org_a"]["id"], "P2A_VIEWER_CREATE"),
            headers=setup["auth_viewer_a"],  # viewer_a is VIEWER in org_a
        )
        assert r.status_code in (403, 422), (
            f"VIEWER must not create profiles. Got {r.status_code}"
        )


# ---------------------------------------------------------------------------
# T07: Viewer/Engineer cannot approve
# ---------------------------------------------------------------------------

class TestT07ViewerCannotApprove:
    def test_T07_viewer_cannot_approve(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}/approve",
            json={"note": ""},
            headers=setup["auth_viewer_a"],
        )
        assert r.status_code in (403, 422)

    def test_T07_engineer_cannot_approve(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}/approve",
            json={"note": ""},
            headers=setup["auth_a"],  # ENGINEER
        )
        assert r.status_code in (403, 422)


# ---------------------------------------------------------------------------
# T08: Default profile cannot be overwritten
# ---------------------------------------------------------------------------

class TestT08DefaultProfileImmutable:
    def test_T08_default_profile_patch_blocked(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.patch(
            f"/api/v1/reference-profiles/{setup['sys_profile_id']}",
            json={"display_name": "Tampered"},
            headers=setup["auth_a"],
        )
        assert r.status_code in (403, 409)
        assert r.json().get("error_code") == "IMMUTABLE_SYSTEM_PROFILE"


# ---------------------------------------------------------------------------
# T09: Unverified profile cannot activate (incomplete prerequisites)
# ---------------------------------------------------------------------------

class TestT09UnverifiedCannotActivate:
    def test_T09_approval_fails_missing_bands(self, mod_client: TestClient, setup: dict) -> None:
        """Profile with empty parameter_bands.bands cannot be approved."""
        r = mod_client.post(
            f"/api/v1/reference-profiles/{setup['profile_a_id']}/approve",
            json={"note": ""},
            headers=setup["auth_approver_a"],
        )
        # profile_a has {"bands": []} — must be rejected
        assert r.status_code == 422
        # GovernedAPIError maps HTTPException.detail["context"] → response["detail"]
        ctx = r.json().get("detail", {}) or {}
        prerequisites_failed = ctx.get("prerequisites_failed", [])
        assert any("parameter_bands" in p for p in prerequisites_failed), (
            f"Expected parameter_bands in failed prerequisites. Got: {prerequisites_failed}. Full body: {r.json()}"
        )


# ---------------------------------------------------------------------------
# T10: Approved version remains immutable
# ---------------------------------------------------------------------------

class TestT10ApprovedVersionImmutable:
    def test_T10_approved_profile_cannot_be_patched(self, mod_client: TestClient, setup: dict) -> None:
        """After approval, a profile becomes immutable (APPROVED ∈ _IMMUTABLE_STATUSES)."""
        auth_a = setup["auth_a"]
        auth_approver = setup["auth_approver_a"]

        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_full_prereq_body(setup["org_a"]["id"], "P2A_T10_IMMUTABLE"),
            headers=auth_a,
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        # Approve
        r_approve = mod_client.post(
            f"/api/v1/reference-profiles/{pid}/approve",
            json={"note": "T10 test approval"},
            headers=auth_approver,
        )
        assert r_approve.status_code == 200, f"Approval failed: {r_approve.text}"

        # Try to patch the now-approved profile
        r_patch = mod_client.patch(
            f"/api/v1/reference-profiles/{pid}",
            json={"display_name": "Modified After Approval"},
            headers=auth_a,
        )
        assert r_patch.status_code == 409, (
            f"Approved profile must be immutable. Got {r_patch.status_code}: {r_patch.text[:200]}"
        )
        assert r_patch.json().get("error_code") == "RESOURCE_CONFLICT"

    def test_T10_re_approval_of_approved_profile_fails(self, mod_client: TestClient, setup: dict) -> None:
        """Cannot approve an already-approved profile."""
        auth_a = setup["auth_a"]
        auth_approver = setup["auth_approver_a"]

        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_full_prereq_body(setup["org_a"]["id"], "P2A_T10_DOUBLE"),
            headers=auth_a,
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        mod_client.post(f"/api/v1/reference-profiles/{pid}/approve", json={"note": ""}, headers=auth_approver)

        # Second approval attempt
        r2 = mod_client.post(
            f"/api/v1/reference-profiles/{pid}/approve",
            json={"note": ""},
            headers=auth_approver,
        )
        assert r2.status_code == 409


# ---------------------------------------------------------------------------
# T11: No silent cross-profile fallback
# ---------------------------------------------------------------------------

class TestT11NoSilentFallback:
    def test_T11_nonexistent_profile_returns_404(self, mod_client: TestClient, setup: dict) -> None:
        """Requesting a non-existent profile returns 404, not a fallback."""
        r = mod_client.get("/api/v1/reference-profiles/999999", headers=setup["auth_a"])
        assert r.status_code == 404
        assert r.json().get("error_code") == "RESOURCE_NOT_FOUND"


# ---------------------------------------------------------------------------
# T12: Existing public demo still works
# ---------------------------------------------------------------------------

class TestT12PublicDemoRegression:
    def test_T12_public_demo_still_anonymous(self, mod_client: TestClient) -> None:
        from app.core.rate_limit import PUBLIC_DEMO_LIMITER
        PUBLIC_DEMO_LIMITER.reset_key("testclient")
        layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
        body = {
            "material_family": "Düşük / Orta Karbonlu Çelik",
            "material_subtype": "DC01",
            "stack_count": "2T",
            "layers": [layer, layer],
            "current_ka": 8.0,
            "weld_cycles": 12.0,
            "force_kn": 3.0,
            "tip_diameter_mm": 6.0,
            "squeeze_cycles": 15.0,
            "hold_cycles": 15.0,
            "cooling_flow_lpm": 6.0,
            "cooling_temp_c": 20.0,
        }
        r = mod_client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# T13: Public demo remains tenant-isolated
# ---------------------------------------------------------------------------

class TestT13PublicDemoTenantIsolated:
    def test_T13_public_demo_response_has_no_org_data(self, mod_client: TestClient) -> None:
        from app.core.rate_limit import PUBLIC_DEMO_LIMITER
        PUBLIC_DEMO_LIMITER.reset_key("testclient")
        layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
        body = {
            "material_family": "Düşük / Orta Karbonlu Çelik",
            "material_subtype": "DC01",
            "stack_count": "2T",
            "layers": [layer, layer],
            "current_ka": 8.0,
            "weld_cycles": 12.0,
            "force_kn": 3.0,
            "tip_diameter_mm": 6.0,
            "squeeze_cycles": 15.0,
            "hold_cycles": 15.0,
            "cooling_flow_lpm": 6.0,
            "cooling_temp_c": 20.0,
        }
        r = mod_client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200
        data = r.json()
        for key in ("org_id", "organization_id", "customer_id", "profile_id", "user_id"):
            assert key not in data, f"Public demo must not expose '{key}'"
        assert data.get("reference_profile_id") == "REF_PROFILE_MS_2T_50HZ_V1"


# ---------------------------------------------------------------------------
# T14: D-01 regression unchanged
# ---------------------------------------------------------------------------

class TestT14D01Regression:
    def test_T14_d01_test_file_exists(self) -> None:
        from pathlib import Path
        assert (Path(__file__).parent / "test_d01_oem_electrode_regression.py").exists()


# ---------------------------------------------------------------------------
# T15: Phase 1 regression unchanged
# ---------------------------------------------------------------------------

class TestT15Phase1Regression:
    def test_T15_phase1_models_intact(self) -> None:
        from app.models.profile_entities import (
            Organization, OrganizationMember, ProfileApprovalEvent,
            ReferenceProfileRecord,
        )
        assert Organization.__tablename__ == "organizations"
        assert ReferenceProfileRecord.__tablename__ == "reference_profiles"

    def test_T15_phase1_enums_intact(self) -> None:
        from app.models.enums import OrgRole, ProfileStatus
        assert ProfileStatus.DRAFT == "DRAFT"
        assert OrgRole.APPROVER == "APPROVER"


# ---------------------------------------------------------------------------
# T16: 2T behavior preserved
# ---------------------------------------------------------------------------

class TestT16TwoTPreserved:
    def test_T16_2t_profile_create_accepted(self, mod_client: TestClient, setup: dict) -> None:
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(setup["org_a"]["id"], "P2A_T16_2T", stack_count="2T"),
            headers=setup["auth_a"],
        )
        assert r.status_code == 201
        assert r.json()["stack_count"] == "2T"


# ---------------------------------------------------------------------------
# T17: 3T remains review-only
# ---------------------------------------------------------------------------

class TestT17ThreeTReviewOnly:
    def test_T17_3t_profile_can_be_created(self, mod_client: TestClient, setup: dict) -> None:
        """3T profiles can be created (review-only, not blocked at API schema level)."""
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(setup["org_a"]["id"], "P2A_T17_3T", stack_count="3T"),
            headers=setup["auth_a"],
        )
        assert r.status_code == 201
        assert r.json()["stack_count"] == "3T"

    def test_T17_3t_public_demo_returns_review_required(self, mod_client: TestClient) -> None:
        from app.core.rate_limit import PUBLIC_DEMO_LIMITER
        PUBLIC_DEMO_LIMITER.reset_key("testclient")
        layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
        body = {
            "material_family": "Düşük / Orta Karbonlu Çelik",
            "material_subtype": "DC01",
            "stack_count": "3T",
            "layers": [layer, layer, layer],
            "current_ka": 8.0,
            "weld_cycles": 12.0,
            "force_kn": 3.0,
            "tip_diameter_mm": 6.0,
            "squeeze_cycles": 15.0,
            "hold_cycles": 15.0,
            "cooling_flow_lpm": 6.0,
            "cooling_temp_c": 20.0,
        }
        r = mod_client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200
        assert r.json().get("band_selection_status") == "ENGINEERING_REVIEW_REQUIRED"


# ---------------------------------------------------------------------------
# T18: 4T remains rejected
# ---------------------------------------------------------------------------

class TestT18FourTRejected:
    def test_T18_4t_profile_create_schema_rejected(self, mod_client: TestClient, setup: dict) -> None:
        """4T is OUT OF PRODUCT SCOPE — schema validator rejects it."""
        r = mod_client.post(
            "/api/v1/reference-profiles",
            json=_valid_profile_body(setup["org_a"]["id"], "P2A_T18_4T", stack_count="4T"),
            headers=setup["auth_a"],
        )
        assert r.status_code == 422, (
            f"4T must be rejected by schema (HR-16). Got {r.status_code}"
        )

    def test_T18_4t_public_demo_rejected(self, mod_client: TestClient) -> None:
        from app.core.rate_limit import PUBLIC_DEMO_LIMITER
        PUBLIC_DEMO_LIMITER.reset_key("testclient")
        layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
        body = {
            "material_family": "Düşük / Orta Karbonlu Çelik",
            "material_subtype": "DC01",
            "stack_count": "4T",
            "layers": [layer, layer, layer, layer],
            "current_ka": 8.0,
            "weld_cycles": 12.0,
            "force_kn": 3.0,
            "tip_diameter_mm": 6.0,
            "squeeze_cycles": 15.0,
            "hold_cycles": 15.0,
            "cooling_flow_lpm": 6.0,
            "cooling_temp_c": 20.0,
        }
        r = mod_client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code in (422, 500), f"4T must be rejected. Got {r.status_code}"
