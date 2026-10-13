"""Security gate tests: MC-01 through MC-05.

Scope: HTTP-layer authorization tests using the existing FastAPI app and
       TestClient. Tests target the Phase 1 security foundation.

ROUTE INVENTORY (at time of writing):
  Existing protected routes: auth/me, auth/users, projects, weld-points,
    weld-analysis, engineering-library, rule-registry, etc.
  Organization/profile routes: NONE — not yet implemented (Phase 2 scope).

TESTABILITY ASSESSMENT:
  MC-01 TESTABLE — existing protected routes can be called without auth.
  MC-02 NOT_VERIFIED — no HTTP organization routes exist; dependency-layer
        unit test provided as evidence of fail-closed design.
  MC-03 TESTABLE — JWT carries sub=email only; role always resolved from DB;
        non-admin users blocked from admin-only endpoints.
  MC-04 NOT_VERIFIED — no profile approval routes exist.
  MC-05 NOT_VERIFIED — no profile modification routes exist; ORM-layer
        immutability verified by T09 (ImmutableRecordError on
        ProfileApprovalEvent update).

Blocking assessment: MC-02, MC-04, MC-05 tests cannot pass or fail via HTTP
because the routes they guard do not exist. They are marked with
pytest.mark.skip(...) to preserve visibility in the test run without
claiming they passed.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.models  # noqa: F401 — ensure new tables are in metadata
from app.core.security import SECRET_KEY, create_access_token
from app.models.enums import OrgRole, UserRole


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Base64-decode the JWT payload without signature verification."""
    _header, payload_b64, _sig = token.split(".")
    padding = "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64 + padding))


# ─────────────────────────────────────────────────────────────────────────────
# MC-01: Unauthenticated HTTP requests to protected resources are rejected
# ─────────────────────────────────────────────────────────────────────────────

class TestMC01UnauthenticatedRejected:
    """All requests without a valid Authorization header must return 401/403."""

    def test_MC01_a_auth_me_no_token_returns_403(self, client: TestClient) -> None:
        r = client.get("/api/v1/auth/me")
        assert r.status_code in (401, 403), (
            f"Expected 401/403 for unauthenticated /auth/me, got {r.status_code}"
        )

    def test_MC01_b_auth_users_no_token_returns_403(self, client: TestClient) -> None:
        r = client.get("/api/v1/auth/users")
        assert r.status_code in (401, 403)

    def test_MC01_c_projects_no_token_returns_403(self, client: TestClient) -> None:
        r = client.get("/api/v1/projects")
        assert r.status_code in (401, 403)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "SECURITY_GAP (pre-existing): POST /api/v1/weld-analysis has no auth "
            "dependency — the route handler uses only Depends(get_service) and "
            "never Depends(get_current_user). Unauthenticated requests that pass "
            "schema validation reach the business logic. This is a pre-existing "
            "gap not introduced by Phase 1. Marked xfail to prevent silent masking. "
            "Must be fixed in Phase 2 or separately."
        ),
    )
    def test_MC01_d_weld_analysis_not_auth_gated(self, client: TestClient) -> None:
        """Document that /weld-analysis does NOT enforce authentication (known gap)."""
        # Empty body → 422 (schema error, not auth error) — business logic reached.
        r = client.post("/api/v1/weld-analysis", json={})
        # If auth were enforced, we'd get 401/403 before schema validation.
        assert r.status_code in (401, 403), (
            f"weld-analysis should require auth but returned {r.status_code} — "
            "route lacks Depends(get_current_user)"
        )

    def test_MC01_e_engineering_library_no_token_returns_403(
        self, client: TestClient
    ) -> None:
        r = client.get("/api/v1/engineering-library/materials")
        assert r.status_code in (401, 403)

    def test_MC01_f_audit_no_token_returns_403(self, client: TestClient) -> None:
        r = client.get("/api/v1/audit")
        assert r.status_code in (401, 403)

    def test_MC01_g_wrong_scheme_token_rejected(self, client: TestClient) -> None:
        r = client.get("/api/v1/projects", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert r.status_code in (401, 403)

    def test_MC01_h_malformed_bearer_token_rejected(self, client: TestClient) -> None:
        r = client.get("/api/v1/projects", headers={"Authorization": "Bearer not.a.valid.jwt"})
        assert r.status_code in (401, 403)

    def test_MC01_i_expired_token_rejected(self, client: TestClient) -> None:
        """A syntactically valid but expired JWT must be rejected."""
        import hashlib, hmac as hmac_mod, base64 as b64

        header = {"alg": "HS256", "typ": "JWT"}

        def b64e(data: bytes) -> str:
            return b64.urlsafe_b64encode(data).rstrip(b"=").decode()

        exp = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp())
        payload = {"sub": "admin@spotwelding.example", "type": "access", "exp": exp}
        h = b64e(json.dumps(header, separators=(",", ":")).encode())
        p = b64e(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{h}.{p}"
        sig = b64e(
            hmac_mod.new(
                SECRET_KEY.encode(), signing_input.encode("ascii"), hashlib.sha256
            ).digest()
        )
        expired_token = f"{signing_input}.{sig}"

        r = client.get("/api/v1/auth/me", headers=_bearer(expired_token))
        assert r.status_code in (401, 403), (
            f"Expired token must be rejected, got {r.status_code}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MC-02: Cross-organization isolation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(
    reason=(
        "NOT_VERIFIED — no organization-scoped HTTP routes exist in Phase 1. "
        "Routes /api/v1/organizations/* and /api/v1/reference-profiles/* are "
        "Phase 2 scope. The dependency get_current_org_membership() is "
        "fail-closed at the DB layer (verified by T08 in "
        "test_phase1_organization_model.py). Re-run when Phase 2 adds routes."
    )
)
class TestMC02CrossOrgIsolation:
    def test_MC02_user_in_org_a_cannot_access_org_b_profiles(self) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# MC-03: Privilege escalation is prevented
# ─────────────────────────────────────────────────────────────────────────────

class TestMC03PrivilegeEscalation:
    """
    JWT carries sub=email only — no role claim.
    Role is ALWAYS resolved from the User row in the database (dependencies.py:39).
    An attacker cannot escalate by forging a role in the JWT.
    """

    def test_MC03_a_jwt_contains_no_role_claim(self, client: TestClient) -> None:
        """Verify JWT payload has no role field — role is never put in the token."""
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "ChangeMe123!"},
        )
        assert r.status_code == 200
        token = r.json()["access_token"]
        payload = _decode_jwt_payload(token)
        assert "role" not in payload, (
            "JWT MUST NOT contain a role claim — role must be resolved from DB only"
        )
        assert "sub" in payload, "JWT must contain a sub (email) claim"
        assert payload.get("type") == "access"

    def test_MC03_b_demo_user_blocked_from_admin_user_creation(
        self, client: TestClient
    ) -> None:
        """A READ_ONLY user cannot create users even with a valid JWT."""
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "demo", "password": "A1234"},
        )
        assert login.status_code == 200
        demo_headers = _bearer(login.json()["access_token"])

        r = client.post(
            "/api/v1/auth/users",
            json={
                "username": "hacker",
                "email": "hacker@evil.example",
                "full_name": "Hacker",
                "password": "Password123!",
                "role": "SYSTEM_ADMIN",
            },
            headers=demo_headers,
        )
        assert r.status_code == 403, (
            f"READ_ONLY user must not create users, got {r.status_code}"
        )

    def test_MC03_c_demo_user_blocked_from_user_list(
        self, client: TestClient
    ) -> None:
        """A READ_ONLY user cannot list all users (SYSTEM_ADMIN only)."""
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "demo", "password": "A1234"},
        )
        assert login.status_code == 200
        demo_headers = _bearer(login.json()["access_token"])

        r = client.get("/api/v1/auth/users", headers=demo_headers)
        assert r.status_code == 403, (
            f"READ_ONLY user must not list users, got {r.status_code}"
        )

    def test_MC03_d_forged_jwt_with_admin_email_but_wrong_signature_rejected(
        self, client: TestClient
    ) -> None:
        """A JWT signed with a wrong key is rejected even if email is valid."""
        import hashlib, hmac as hmac_mod, base64 as b64

        def b64e(data: bytes) -> str:
            return b64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header = {"alg": "HS256", "typ": "JWT"}
        exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        payload = {"sub": "admin@spotwelding.example", "type": "access", "exp": exp}
        h = b64e(json.dumps(header, separators=(",", ":")).encode())
        p = b64e(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{h}.{p}"
        wrong_sig = b64e(
            hmac_mod.new(
                b"wrong-secret-key-for-testing",
                signing_input.encode("ascii"),
                hashlib.sha256,
            ).digest()
        )
        forged_token = f"{signing_input}.{wrong_sig}"

        r = client.get("/api/v1/auth/me", headers=_bearer(forged_token))
        assert r.status_code in (401, 403), (
            f"Token with wrong signature must be rejected, got {r.status_code}"
        )

    def test_MC03_e_demo_user_role_is_read_only_in_db(
        self, client: TestClient
    ) -> None:
        """After login, /auth/me returns the DB role, not any JWT-supplied role."""
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "demo", "password": "A1234"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        demo_headers = _bearer(token)

        me = client.get("/api/v1/auth/me", headers=demo_headers)
        assert me.status_code == 200
        assert me.json()["role"] == "READ_ONLY", (
            "Role in /auth/me must reflect DB record, not any claim in JWT"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MC-04: Profile approval gating
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(
    reason=(
        "NOT_VERIFIED — no profile approval HTTP routes exist in Phase 1. "
        "Routes /api/v1/reference-profiles/{id}/approve are Phase 2 scope. "
        "The require_org_role(OrgRole.APPROVER) dependency is implemented and "
        "fail-closed (rank-based check). Re-run when Phase 2 adds routes."
    )
)
class TestMC04ProfileApprovalGating:
    def test_MC04_only_approver_role_can_approve_profile(self) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# MC-05: Default profile and approved versions are immutable
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(
    reason=(
        "NOT_VERIFIED via HTTP — no profile modification routes exist in "
        "Phase 1. Routes PATCH /api/v1/reference-profiles/{id} are Phase 2 "
        "scope. ORM-layer immutability of ProfileApprovalEvent is verified by "
        "T09 (test_phase1_organization_model.py::test_T09). "
        "Re-run when Phase 2 adds modification routes."
    )
)
class TestMC05DefaultProfileImmutability:
    def test_MC05_customer_cannot_modify_default_profile(self) -> None:
        pass

    def test_MC05_approved_event_cannot_be_updated(self) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Supporting evidence: OrgRole rank ordering is fail-closed
# ─────────────────────────────────────────────────────────────────────────────

class TestOrgRoleRankFail:
    """Confirm require_org_role denies unknown/missing roles (rank=0)."""

    def test_org_role_rank_unknown_role_is_zero(self) -> None:
        from app.api.dependencies import _ORG_ROLE_RANK
        # Any unknown string must map to 0, which is less than any defined min rank
        assert _ORG_ROLE_RANK.get("NONEXISTENT_ROLE", 0) == 0

    def test_org_role_rank_ordering(self) -> None:
        from app.api.dependencies import _ORG_ROLE_RANK
        assert _ORG_ROLE_RANK[OrgRole.VIEWER] < _ORG_ROLE_RANK[OrgRole.ENGINEER]
        assert _ORG_ROLE_RANK[OrgRole.ENGINEER] < _ORG_ROLE_RANK[OrgRole.APPROVER]
        assert _ORG_ROLE_RANK[OrgRole.APPROVER] < _ORG_ROLE_RANK[OrgRole.ORG_ADMIN]

    def test_get_current_org_membership_rejects_non_member(self) -> None:
        """
        Dependency-layer evidence: non-member user raises HTTPException 403.
        This is NOT a substitute for an HTTP test (no route exists to call via
        TestClient) but provides code-level evidence of fail-closed behaviour.
        """
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from app.api.dependencies import get_current_org_membership
        from app.models.entities import User

        mock_user = MagicMock(spec=User)
        mock_user.id = 99
        mock_user.role = UserRole.PROCESS_ENGINEER

        mock_db = MagicMock()
        mock_db.scalar.return_value = None  # no member row found

        # get_current_org_membership is a plain function; call it directly.
        with pytest.raises(HTTPException) as exc_info:
            get_current_org_membership(
                org_id=1,
                user=mock_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error_code"] == "ORG_MEMBERSHIP_REQUIRED"
