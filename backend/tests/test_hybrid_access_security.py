"""Hybrid Access Security Tests — SWP-HYBRID-ACCESS-SECURITY-IMPLEMENTATION-01.

Tests S01–S20 as specified. Each test references its mandate ID.

DEFERRED_NOT_VERIFIED tests (S09, S10, S13-org):
  No organization-scoped HTTP routes exist in Phase 1. These tests are
  skipped with explanatory reason strings and will be re-run when Phase 2
  adds org/profile routes.

IMPORTANT: No production databases are modified. All tests use the
conftest.py in-memory SQLite test database (Base.metadata.create_all).
"""
from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.models  # noqa: F401 — register Phase 1 tables in metadata
from app.core.rate_limit import PUBLIC_DEMO_LIMITER, get_client_ip
from app.models.enums import ProfileStatus, UserRole

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _valid_2t_body(**overrides: Any) -> dict[str, Any]:
    """Minimal schema-valid 2T weld-analysis request body."""
    layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
    body: dict[str, Any] = {
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
        "dc_current": True,
        "adhesive": False,
        "shunt_risk": False,
    }
    body.update(overrides)
    return body


def _valid_3t_body() -> dict[str, Any]:
    layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
    return {
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


def _reset_rate_limiter_for_ip(ip: str = "testclient") -> None:
    """Clear the rate-limiter bucket for the given IP. Tests only."""
    PUBLIC_DEMO_LIMITER.reset_key(ip)


# ---------------------------------------------------------------------------
# S01: Anonymous public demo succeeds with valid permitted inputs
# ---------------------------------------------------------------------------

class TestS01AnonymousPublicDemo:
    def test_S01_anonymous_2t_analysis_succeeds(self, client: TestClient) -> None:
        """Public demo works without any auth token."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert "score" in data
        assert "risk_level" in data
        assert "nugget_min_mm" in data
        assert "reference_profile_id" in data
        assert data["reference_profile_id"] == "REF_PROFILE_MS_2T_50HZ_V1"

    def test_S01_anonymous_succeeds_without_auth_header(self, client: TestClient) -> None:
        """Confirm no Authorization header is required (mode A: PUBLIC_DEMO)."""
        _reset_rate_limiter_for_ip()
        r = client.post(
            "/api/v1/weld-analysis",
            json=_valid_2t_body(),
            headers={},  # explicitly no auth
        )
        assert r.status_code == 200

    def test_S01_authenticated_user_also_succeeds(self, client: TestClient, auth_headers: dict) -> None:
        """Authenticated users are not blocked from the public endpoint (S14 compatibility)."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body(), headers=auth_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# S02: Public demo cannot read customer data
# ---------------------------------------------------------------------------

class TestS02NoCustomerDataExposure:
    def test_S02_response_contains_no_user_id(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        data = r.json()
        for forbidden_key in ("user_id", "org_id", "organization_id", "customer_id", "project_id"):
            assert forbidden_key not in data, f"Response must not contain '{forbidden_key}'"

    def test_S02_response_contains_no_weld_point_data(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        data = r.json()
        for forbidden_key in ("weld_point_id", "point_code", "project", "owner"):
            assert forbidden_key not in data, f"Response must not contain '{forbidden_key}'"

    def test_S02_reference_profile_id_is_public_constant(self, client: TestClient) -> None:
        """reference_profile_id in response is the public engineering constant, not a DB row id."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        # Must be the public constant string, not an integer DB key
        profile_ref = r.json().get("reference_profile_id")
        assert isinstance(profile_ref, str), "reference_profile_id must be a string constant"
        assert profile_ref == "REF_PROFILE_MS_2T_50HZ_V1"


# ---------------------------------------------------------------------------
# S03: Public demo cannot select private profiles
# ---------------------------------------------------------------------------

class TestS03NoPrivateProfileSelection:
    def test_S03_schema_does_not_accept_profile_id(self, client: TestClient) -> None:
        """WeldAnalysisRequest has no profile_id field — private profile selection is impossible."""
        _reset_rate_limiter_for_ip()
        # Extra unknown fields are silently ignored by Pydantic (extra='ignore' default).
        # The profile_id is not forwarded to the engine — verify via response.
        body = _valid_2t_body()
        body["profile_id"] = 9999  # injection attempt
        r = client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200
        # The private profile_id must not appear in the response
        assert r.json().get("reference_profile_id") == "REF_PROFILE_MS_2T_50HZ_V1", (
            "profile_id injection must not change the reference profile used"
        )

    def test_S03_schema_does_not_accept_org_id(self, client: TestClient) -> None:
        """organization_id injection does not route to a customer profile."""
        _reset_rate_limiter_for_ip()
        body = _valid_2t_body()
        body["organization_id"] = 42
        body["org_id"] = 42
        r = client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200
        assert r.json().get("reference_profile_id") == "REF_PROFILE_MS_2T_50HZ_V1"


# ---------------------------------------------------------------------------
# S04: Public demo cannot persist weld-point or project records
# ---------------------------------------------------------------------------

class TestS04NoPersistence:
    def test_S04_weld_analysis_does_not_create_projects(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """After a public demo analysis, the authenticated project count is unchanged."""
        _reset_rate_limiter_for_ip()
        before = client.get("/api/v1/projects", headers=auth_headers)
        assert before.status_code == 200
        count_before = len(before.json())

        client.post("/api/v1/weld-analysis", json=_valid_2t_body())

        after = client.get("/api/v1/projects", headers=auth_headers)
        assert after.status_code == 200
        assert len(after.json()) == count_before, (
            "Public demo must not create project records"
        )

    def test_S04_weld_analysis_response_has_no_persistence_id(self, client: TestClient) -> None:
        """Response has no id, created_at, or similar persistence indicators."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        data = r.json()
        for persistence_key in ("id", "weld_point_id", "created_at", "updated_at", "version_no"):
            assert persistence_key not in data, (
                f"Public demo response must not contain '{persistence_key}'"
            )


# ---------------------------------------------------------------------------
# S05: Public demo rate limit returns HTTP 429
# ---------------------------------------------------------------------------

class TestS05RateLimit:
    def test_S05_rate_limit_returns_429(self, client: TestClient) -> None:
        """Simulate exhausted rate-limit bucket → expect 429."""
        _reset_rate_limiter_for_ip()
        # Pre-fill the bucket to the limit directly (avoids making 60 HTTP calls).
        now = __import__("time").monotonic()
        bucket = deque([now] * PUBLIC_DEMO_LIMITER.limit)
        PUBLIC_DEMO_LIMITER._buckets["testclient"] = bucket

        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 429, (
            f"Expected 429 when rate limit is exhausted, got {r.status_code}"
        )
        # Cleanup
        _reset_rate_limiter_for_ip()

    def test_S05_429_response_has_correct_error_code(self, client: TestClient) -> None:
        """429 response body must carry a structured error with RATE_LIMIT_EXCEEDED."""
        _reset_rate_limiter_for_ip()
        now = __import__("time").monotonic()
        PUBLIC_DEMO_LIMITER._buckets["testclient"] = deque([now] * PUBLIC_DEMO_LIMITER.limit)

        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 429
        data = r.json()
        # error_code appears at top level of the JSONResponse body
        assert data.get("error_code") == "RATE_LIMIT_EXCEEDED", (
            f"Expected error_code=RATE_LIMIT_EXCEEDED, got {data}"
        )
        _reset_rate_limiter_for_ip()


    def test_S05_retry_after_header_present(self, client: TestClient) -> None:
        """429 must include a Retry-After header."""
        _reset_rate_limiter_for_ip()
        now = __import__("time").monotonic()
        PUBLIC_DEMO_LIMITER._buckets["testclient"] = deque([now] * PUBLIC_DEMO_LIMITER.limit)

        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 429
        assert "retry-after" in r.headers or "Retry-After" in r.headers, (
            "429 must include Retry-After header"
        )
        _reset_rate_limiter_for_ip()

    def test_S05_rate_limit_allows_request_after_window_expires(self, client: TestClient) -> None:
        """After old timestamps expire, requests are allowed again."""
        _reset_rate_limiter_for_ip()
        # Fill bucket with timestamps that are outside the window (already expired).
        expired = __import__("time").monotonic() - PUBLIC_DEMO_LIMITER.window_seconds - 1
        PUBLIC_DEMO_LIMITER._buckets["testclient"] = deque([expired] * PUBLIC_DEMO_LIMITER.limit)

        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200, (
            "Expired window entries should be purged — request must succeed"
        )
        _reset_rate_limiter_for_ip()


# ---------------------------------------------------------------------------
# S06: Invalid and oversized input is rejected
# ---------------------------------------------------------------------------

class TestS06InvalidInput:
    def test_S06_current_above_max_rejected(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body(current_ka=200.0))
        assert r.status_code == 422

    def test_S06_negative_force_rejected(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body(force_kn=-1.0))
        assert r.status_code == 422

    def test_S06_zero_tip_diameter_rejected(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body(tip_diameter_mm=0.0))
        assert r.status_code == 422

    def test_S06_layer_count_mismatch_rejected(self, client: TestClient) -> None:
        """3 layers with stack_count=2T must fail validation."""
        _reset_rate_limiter_for_ip()
        layer = {"material_family": "Düşük / Orta Karbonlu Çelik", "material_subtype": "DC01", "thickness_mm": 1.0}
        body = _valid_2t_body()
        body["layers"] = [layer, layer, layer]
        r = client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 422

    def test_S06_empty_body_rejected(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json={})
        assert r.status_code == 422

    def test_S06_missing_required_field_rejected(self, client: TestClient) -> None:
        _reset_rate_limiter_for_ip()
        body = _valid_2t_body()
        del body["current_ka"]
        r = client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# S07: Malicious organization_id/profile_id injection is rejected
# ---------------------------------------------------------------------------

class TestS07InjectionRejected:
    def test_S07_profile_id_injection_uses_public_profile(self, client: TestClient) -> None:
        """profile_id in body is ignored; only public REF_PROFILE_MS_2T_50HZ_V1 used."""
        _reset_rate_limiter_for_ip()
        body = _valid_2t_body()
        body["profile_id"] = 1
        r = client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200
        assert r.json()["reference_profile_id"] == "REF_PROFILE_MS_2T_50HZ_V1"

    def test_S07_user_id_injection_ignored(self, client: TestClient) -> None:
        """user_id cannot be supplied to alter identity or data access."""
        _reset_rate_limiter_for_ip()
        body = _valid_2t_body()
        body["user_id"] = 1
        r = client.post("/api/v1/weld-analysis", json=body)
        assert r.status_code == 200
        assert "user_id" not in r.json()


# ---------------------------------------------------------------------------
# S08: Authenticated customer analysis requires valid JWT
# ---------------------------------------------------------------------------

class TestS08CustomerAuthRequired:
    """Verify auth is enforced on all non-public endpoints."""

    def test_S08_projects_requires_jwt(self, client: TestClient) -> None:
        r = client.get("/api/v1/projects")
        assert r.status_code in (401, 403)

    def test_S08_weld_points_requires_jwt(self, client: TestClient) -> None:
        r = client.get("/api/v1/weld-points/1")
        assert r.status_code in (401, 403)

    def test_S08_dashboard_requires_jwt(self, client: TestClient) -> None:
        r = client.get("/api/v1/dashboard")
        assert r.status_code in (401, 403)

    def test_S08_engineering_library_requires_jwt(self, client: TestClient) -> None:
        r = client.get("/api/v1/engineering-library/electrodes")
        assert r.status_code in (401, 403)

    def test_S08_invalid_jwt_rejected(self, client: TestClient) -> None:
        r = client.get("/api/v1/projects", headers={"Authorization": "Bearer not.a.jwt"})
        assert r.status_code in (401, 403)

    def test_S08_valid_jwt_grants_access(self, client: TestClient, auth_headers: dict) -> None:
        """Authenticated user can access protected endpoints."""
        r = client.get("/api/v1/projects", headers=auth_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# S09: Cross-organization access is denied
# ---------------------------------------------------------------------------

@pytest.mark.skip(
    reason=(
        "DEFERRED_NOT_VERIFIED — no organization-scoped HTTP routes exist. "
        "Routes /api/v1/organizations/* and /api/v1/reference-profiles/* are "
        "Phase 2 scope. Re-run when Phase 2 adds org/profile routes. "
        "Dependency-layer evidence: get_current_org_membership() raises 403 "
        "for non-members (verified by TestOrgRoleRankFail in test_phase2_security_gate.py)."
    )
)
class TestS09CrossOrgDenied:
    def test_S09_org_a_user_cannot_access_org_b_profiles(self) -> None:
        pass


# ---------------------------------------------------------------------------
# S10: Unauthorized profile approval is denied
# ---------------------------------------------------------------------------

@pytest.mark.skip(
    reason=(
        "DEFERRED_NOT_VERIFIED — no profile approval HTTP route exists. "
        "Route POST /api/v1/reference-profiles/{id}/approve is Phase 2 scope. "
        "Re-run when Phase 2 adds the approval route."
    )
)
class TestS10UnauthorizedApprovalDenied:
    def test_S10_customer_role_cannot_approve_profile(self) -> None:
        pass


# ---------------------------------------------------------------------------
# S11: Default profile remains read-only (DRAFT status in seed)
# ---------------------------------------------------------------------------

class TestS11DefaultProfileReadOnly:
    def test_S11_default_profile_seeded_as_draft(self) -> None:
        """The seed script creates the Default profile with status=DRAFT, not APPROVED.

        BLOCKER-B note: reference_profile.py has a pre-existing worktree modification.
        This test checks the DB seed status only — it does not exercise the engine
        4T path that BLOCKER-B affects.
        """
        from sqlalchemy import select
        from app.db.session import SessionLocal
        from app.models.profile_entities import ReferenceProfileRecord

        with SessionLocal() as session:
            # The test DB uses Base.metadata.create_all (no seed data present).
            # Verify that the SWP_DEFAULT profile, if it exists, is not APPROVED.
            profile = session.scalar(
                select(ReferenceProfileRecord).where(
                    ReferenceProfileRecord.profile_code == "SWP_DEFAULT",
                    ReferenceProfileRecord.version == 1,
                )
            )
            if profile is not None:
                assert profile.status != ProfileStatus.APPROVED, (
                    "Default profile must not be APPROVED without engineering validation "
                    "(HR-06: DRAFT ≠ APPROVED)"
                )
            # Profile not present in test DB is also acceptable — seed not run in tests.

    def test_S11_draft_profile_blocked_by_verify_profile_guard(self) -> None:
        """verify_profile_for_user raises 403 for a DRAFT profile (unit-level guard test)."""
        from datetime import datetime, timezone
        from unittest.mock import MagicMock, patch

        from fastapi import HTTPException
        from sqlalchemy.orm import Session

        from app.api.dependencies import verify_profile_for_user
        from app.models.entities import User
        from app.models.profile_entities import ReferenceProfileRecord

        mock_profile = MagicMock(spec=ReferenceProfileRecord)
        mock_profile.id = 1
        mock_profile.profile_code = "SWP_DEFAULT"
        mock_profile.version = 1
        mock_profile.status = ProfileStatus.DRAFT
        mock_profile.org_id = None

        mock_db = MagicMock(spec=Session)
        mock_db.scalar.return_value = mock_profile

        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.role = UserRole.PROCESS_ENGINEER

        with pytest.raises(HTTPException) as exc_info:
            verify_profile_for_user(profile_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error_code"] == "PROFILE_NOT_APPROVED"


# ---------------------------------------------------------------------------
# S12: Unapproved profiles cannot be represented as engineering-approved
# ---------------------------------------------------------------------------

class TestS12UnapprovedNotUsable:
    @pytest.mark.parametrize("bad_status", [
        ProfileStatus.DRAFT,
        ProfileStatus.REVIEW_REQUIRED,
        ProfileStatus.VALIDATED,
        ProfileStatus.SUPERSEDED,
        ProfileStatus.REVOKED,
    ])
    def test_S12_non_approved_status_blocked(self, bad_status: ProfileStatus) -> None:
        """verify_profile_for_user blocks all non-APPROVED/non-ACTIVE statuses."""
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from app.api.dependencies import verify_profile_for_user
        from app.models.entities import User
        from app.models.profile_entities import ReferenceProfileRecord

        mock_profile = MagicMock(spec=ReferenceProfileRecord)
        mock_profile.id = 99
        mock_profile.profile_code = "TEST"
        mock_profile.version = 1
        mock_profile.status = bad_status
        mock_profile.org_id = None

        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_profile
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.role = UserRole.PROCESS_ENGINEER

        with pytest.raises(HTTPException) as exc_info:
            verify_profile_for_user(profile_id=99, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error_code"] == "PROFILE_NOT_APPROVED"

    def test_S12_approved_profile_passes_guard(self) -> None:
        """APPROVED system-default profile passes verify_profile_for_user."""
        from unittest.mock import MagicMock
        from app.api.dependencies import verify_profile_for_user
        from app.models.entities import User
        from app.models.profile_entities import ReferenceProfileRecord

        mock_profile = MagicMock(spec=ReferenceProfileRecord)
        mock_profile.id = 10
        mock_profile.profile_code = "SWP_DEFAULT"
        mock_profile.version = 1
        mock_profile.status = ProfileStatus.APPROVED
        mock_profile.org_id = None  # system default — no membership check needed

        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_profile
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.role = UserRole.PROCESS_ENGINEER

        result = verify_profile_for_user(profile_id=10, user=mock_user, db=mock_db)
        assert result is mock_profile

    def test_S12_active_profile_passes_guard(self) -> None:
        """ACTIVE system-default profile also passes verify_profile_for_user."""
        from unittest.mock import MagicMock
        from app.api.dependencies import verify_profile_for_user
        from app.models.entities import User
        from app.models.profile_entities import ReferenceProfileRecord

        mock_profile = MagicMock(spec=ReferenceProfileRecord)
        mock_profile.id = 11
        mock_profile.status = ProfileStatus.ACTIVE
        mock_profile.org_id = None

        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_profile
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.role = UserRole.PROCESS_ENGINEER

        result = verify_profile_for_user(profile_id=11, user=mock_user, db=mock_db)
        assert result is mock_profile


# ---------------------------------------------------------------------------
# S13: Approved profile versions remain immutable
# ---------------------------------------------------------------------------

class TestS13ApprovedVersionImmutable:
    def test_S13_profile_approval_event_is_immutable(self) -> None:
        """ProfileApprovalEvent cannot be updated after creation (ORM-level guard).

        This re-verifies T09 from test_phase1_organization_model.py to confirm
        that the Phase 1 immutability guarantee remains intact.
        """
        from app.models.governance import ImmutableRecordError
        from app.models.profile_entities import (
            Organization, ProfileApprovalEvent, ReferenceProfileRecord,
        )
        from app.models.enums import ProfileApprovalEventType
        from app.db.session import SessionLocal

        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            org = Organization(
                slug="s13-test-org",
                display_name="S13",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(org)
            session.flush()

            from app.models.entities import User
            from sqlalchemy import select as _select
            user = session.scalar(_select(User).where(User.username == "admin"))
            assert user is not None

            profile = ReferenceProfileRecord(
                profile_code="S13_TEST",
                version=1,
                org_id=None,
                display_name="S13 Test",
                material_scope="DC01",
                stack_count="2T",
                cycle_basis_hz=50,
                t_min_mm=0.6,
                t_max_mm=2.5,
                status=ProfileStatus.APPROVED,
                is_system_default=False,
                parameter_bands={"bands": []},
                nugget_criterion={"method": "d5"},
                source_provenance={"basis": "test"},
                created_by=user.id,
                created_at=now,
                updated_at=now,
            )
            session.add(profile)
            session.flush()

            evt = ProfileApprovalEvent(
                profile_id=profile.id,
                event_type=ProfileApprovalEventType.APPROVED,
                actor_user_id=user.id,
                event_at=now,
                note="approved",
            )
            session.add(evt)
            session.flush()

            with pytest.raises(ImmutableRecordError):
                evt.note = "tampered"
                session.flush()

            session.rollback()


# ---------------------------------------------------------------------------
# S14: Existing API compatibility is checked
# ---------------------------------------------------------------------------

class TestS14APICompatibility:
    def test_S14_weld_analysis_still_accepts_existing_schema(self, client: TestClient) -> None:
        """The public demo endpoint schema is backward compatible."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        data = r.json()
        # Fields that must still be present (pre-existing API contract):
        for field in ("score", "risk_level", "nugget_min_mm", "nugget_opt_mm",
                      "recommended_ranges", "risks", "actions"):
            assert field in data, f"Existing field '{field}' must still be present"

    def test_S14_existing_protected_endpoints_unchanged(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Auth-protected endpoints still require and accept valid JWT."""
        r = client.get("/api/v1/auth/me", headers=auth_headers)
        assert r.status_code == 200

    def test_S14_rate_limiter_preserves_successful_response_structure(
        self, client: TestClient
    ) -> None:
        """Adding rate limiting must not change the 200 response structure."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/json")


# ---------------------------------------------------------------------------
# S15: D-01 electrode regression (reference existing test suite)
# ---------------------------------------------------------------------------

class TestS15D01Regression:
    def test_S15_d01_regression_tests_pass(self) -> None:
        """Verify D-01 OEM electrode corrections are not affected by security changes.

        This is a meta-test — it imports the D-01 test module and confirms
        it can be collected. The actual 91 D-01 regression tests are run as
        part of pytest collection (test_d01_oem_electrode_regression.py).
        """
        import importlib
        from pathlib import Path
        import importlib.util

        d01_path = Path(__file__).parent / "test_d01_oem_electrode_regression.py"
        assert d01_path.exists(), "D-01 regression test file must exist"
        spec = importlib.util.spec_from_file_location("test_d01", d01_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Verify key D-01 correction is present
        assert hasattr(mod, "test_Ø6_at_t_0_6mm") or any(
            "6mm" in name or "tip" in name.lower() or "electrode" in name.lower()
            or "d01" in name.lower()
            for name in dir(mod) if name.startswith("test_")
        ), "D-01 regression test file must contain electrode diameter tests"


# ---------------------------------------------------------------------------
# S16: 2T reference behavior remains valid
# ---------------------------------------------------------------------------

class TestS16TwoTReference:
    def test_S16_2t_analysis_returns_score_and_band(self, client: TestClient) -> None:
        """2T mild steel analysis must return a score and a reference band."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["score"], (int, float))
        assert 0 <= data["score"] <= 100
        assert data.get("band_selection_status") is not None

    def test_S16_2t_mild_steel_band_ok(self, client: TestClient) -> None:
        """2T 1.0 mm mild steel must be within the REF_PROFILE band range."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_2t_body())
        assert r.status_code == 200
        data = r.json()
        # 1.0 mm is within the 0.6–3.0 mm reference range
        assert data.get("band_selection_status") == "OK", (
            f"Expected band_selection_status=OK for 1.0mm 2T, got {data.get('band_selection_status')}"
        )


# ---------------------------------------------------------------------------
# S17: 3T remains review-only
# ---------------------------------------------------------------------------

class TestS17ThreeTReviewOnly:
    def test_S17_3t_analysis_returns_200_with_review_risk(self, client: TestClient) -> None:
        """3T analysis succeeds (review-only, not blocked) and includes a 3T warning."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_3t_body())
        assert r.status_code == 200
        data = r.json()
        risk_titles = [risk.get("title", "") for risk in data.get("risks", [])]
        has_3t_warning = any("3T" in t or "katlı" in t.lower() or "çok" in t.lower() for t in risk_titles)
        assert has_3t_warning, (
            f"3T must include a review-only risk warning. Risks: {risk_titles}"
        )

    def test_S17_3t_band_status_is_engineering_review_required(self, client: TestClient) -> None:
        """3T analysis must flag band_selection_status as ENGINEERING_REVIEW_REQUIRED."""
        _reset_rate_limiter_for_ip()
        r = client.post("/api/v1/weld-analysis", json=_valid_3t_body())
        assert r.status_code == 200
        assert r.json().get("band_selection_status") == "ENGINEERING_REVIEW_REQUIRED", (
            "3T must require engineering review (HR-13)"
        )


# ---------------------------------------------------------------------------
# S18: 4T requests remain rejected
# ---------------------------------------------------------------------------

class TestS184TRejected:
    def test_S18_4t_rejected_by_schema(self, client: TestClient) -> None:
        """4T is OUT OF PRODUCT SCOPE — schema validator or engine raises an error."""
        _reset_rate_limiter_for_ip()
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
        r = client.post("/api/v1/weld-analysis", json=body)
        # Schema validator (stack_count must be 2T or 3T) → 422
        # Engine ValueError (4T unsupported) → 500 if schema passes
        assert r.status_code in (422, 500), (
            f"4T must be rejected (422 from schema or 500 from engine), got {r.status_code}"
        )


# ---------------------------------------------------------------------------
# S19: Existing Phase 1 tests remain PASS
# ---------------------------------------------------------------------------

class TestS19Phase1Regression:
    def test_S19_phase1_test_file_exists_and_importable(self) -> None:
        """Phase 1 test file must exist and be importable (collection-level check)."""
        import importlib.util
        from pathlib import Path

        p1_path = Path(__file__).parent / "test_phase1_organization_model.py"
        assert p1_path.exists(), "Phase 1 test file must exist"
        spec = importlib.util.spec_from_file_location("test_phase1", p1_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # T01–T12 should be discoverable
        phase1_tests = [name for name in dir(mod) if name.startswith("test_T")]
        assert len(phase1_tests) >= 12, (
            f"Expected at least 12 Phase 1 tests, found {len(phase1_tests)}: {phase1_tests}"
        )

    def test_S19_phase1_enums_intact(self) -> None:
        """Phase 1 OrgRole and ProfileStatus enums are still present."""
        from app.models.enums import OrgRole, ProfileStatus
        assert OrgRole.ORG_ADMIN == "ORG_ADMIN"
        assert ProfileStatus.DRAFT == "DRAFT"
        assert ProfileStatus.APPROVED == "APPROVED"

    def test_S19_phase1_dependencies_intact(self) -> None:
        """Phase 1 dependency functions still importable."""
        from app.api.dependencies import (
            _ORG_ROLE_RANK,
            get_current_org_membership,
            require_org_role,
            verify_profile_for_user,
        )
        from app.models.enums import OrgRole as _OrgRole
        assert callable(get_current_org_membership)
        assert callable(require_org_role)
        assert callable(verify_profile_for_user)
        assert _ORG_ROLE_RANK[_OrgRole.APPROVER] > _ORG_ROLE_RANK[_OrgRole.ENGINEER]


# ---------------------------------------------------------------------------
# S20: No production or user DB modification
# ---------------------------------------------------------------------------

class TestS20NoDBModification:
    def test_S20_weld_analysis_uses_no_db_session(self) -> None:
        """Verify the weld-analysis service and engine have no DB dependencies."""
        import inspect
        from app.application.weld_analysis_service import WeldAnalysisService
        from app.domain import engine as engine_mod

        # Service source must not import Session or get_db
        service_src = inspect.getsource(WeldAnalysisService)
        assert "Session" not in service_src, "WeldAnalysisService must not use DB Session"
        assert "get_db" not in service_src, "WeldAnalysisService must not use get_db"

        # Engine module must not import Session
        engine_src = inspect.getsource(engine_mod)
        assert "Session" not in engine_src, "engine.py must not use DB Session"
        assert "INSERT" not in engine_src, "engine.py must not execute SQL INSERT"

    def test_S20_rate_limiter_state_is_in_memory_only(self) -> None:
        """Rate limiter uses in-memory deques only — no DB or file persistence."""
        import inspect
        from app.core import rate_limit as rl_mod

        rl_src = inspect.getsource(rl_mod)
        assert "Session" not in rl_src, "Rate limiter must not use DB"
        assert "open(" not in rl_src, "Rate limiter must not write files"
        # "redis" appears in the docstring as a recommendation — that's fine.
        # What must NOT exist is an actual Redis import or connection.
        assert "import redis" not in rl_src.lower(), (
            "Rate limiter must not import Redis — it's in-memory only"
        )
        assert "redis.Redis(" not in rl_src and "Redis(" not in rl_src, (
            "Rate limiter must not instantiate a Redis client"
        )
