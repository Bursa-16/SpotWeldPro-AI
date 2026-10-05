"""CE-04-C1 error contract tests.

Verifies:
- ApiErrorCode catalogue completeness
- ResourceType catalogue completeness
- Global HTTPException handler converts unstructured exceptions to INTERNAL_ERROR
- GovernedAPIError CE-04-B compatibility (detail field preserved)
- Structured error_code is always present in governed error responses
"""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models.error_codes import ApiErrorCode, ResourceType


# ---------------------------------------------------------------------------
# Catalogue completeness
# ---------------------------------------------------------------------------

EXPECTED_ERROR_CODES = {
    "INVALID_TOKEN",
    "INACTIVE_USER",
    "PERMISSION_DENIED",
    "RESOURCE_NOT_FOUND",
    "INVALID_REQUEST",
    "IDEMPOTENCY_CONFLICT",
    "IDEMPOTENCY_IN_PROGRESS",
    "GOVERNED_TRANSACTION_FAILED",
    "MISSING_IDEMPOTENCY_KEY",
    "INTERNAL_ERROR",
    "VALIDATION_ERROR",
    "INVALID_CREDENTIALS",
    "MACHINE_READINESS_REVISION_NOT_FOUND",
    "LIBRARY_RESOURCE_NOT_FOUND",
    "RESOURCE_CONFLICT",
    "LIBRARY_CONFLICT",
}

EXPECTED_RESOURCE_TYPES = {
    "material",
    "material_revision",
    "coating",
    "coating_revision",
    "stack_up",
    "electrode",
    "weld_gun",
    "weld_schedule",
    "weld_point",
    "project",
}


def test_api_error_code_catalogue_completeness():
    actual = {member.value for member in ApiErrorCode}
    assert actual == EXPECTED_ERROR_CODES, (
        f"ApiErrorCode mismatch. Missing: {EXPECTED_ERROR_CODES - actual}. "
        f"Extra: {actual - EXPECTED_ERROR_CODES}."
    )


def test_resource_type_catalogue_completeness():
    actual = {member.value for member in ResourceType}
    assert actual == EXPECTED_RESOURCE_TYPES, (
        f"ResourceType mismatch. Missing: {EXPECTED_RESOURCE_TYPES - actual}. "
        f"Extra: {actual - EXPECTED_RESOURCE_TYPES}."
    )


# ---------------------------------------------------------------------------
# Global handler: unstructured plain-string detail → 500 INTERNAL_ERROR
# ---------------------------------------------------------------------------

def test_global_handler_plain_string_becomes_internal_error(client):
    """An HTTPException with a plain string detail must return 500 INTERNAL_ERROR.

    The global handler in main.py detects that detail is not a governed dict
    and substitutes a safe INTERNAL_ERROR response, preventing raw exception
    strings from crossing the API boundary.
    """
    from app.main import app

    @app.get("/__test_ce04c1_plain_string__")
    def _raise_plain():
        raise HTTPException(status_code=400, detail="raw internal message")

    with TestClient(app) as tc:
        r = tc.get("/__test_ce04c1_plain_string__")

    assert r.status_code == 500
    body = r.json()
    assert body.get("error_code") == "INTERNAL_ERROR"
    assert "raw internal message" not in r.text


# ---------------------------------------------------------------------------
# CE-04-B compat: GovernedAPIError must still have a detail field
# ---------------------------------------------------------------------------

def test_governed_api_error_has_detail_field(client, auth_headers):
    """GovernedAPIError.detail must remain present (CE-04-B backward compat)."""
    r = client.get("/api/v1/engineering-library/materials/999999", headers=auth_headers)
    assert r.status_code == 404
    body = r.json()
    assert "error_code" in body
    assert "message" in body
    # detail may be None or a dict — presence of the key is the compat contract
    assert "detail" in body


# ---------------------------------------------------------------------------
# Structured error_code always present on governed 4xx responses
# ---------------------------------------------------------------------------

def test_missing_idempotency_key_returns_error_code(client, auth_headers):
    """Rule-registry endpoint without Idempotency-Key must return error_code."""
    r = client.post(
        "/api/v1/rule-registry/source-backed-promotion",
        json={
            "rule_id": "test-rule",
            "source_revision": "rev-1",
            "revision": "v1",
            "version_metadata": {
                "version": "1.0",
                "label": "test",
                "published_by": "test-user",
                "published_at": "2024-01-01T00:00:00Z",
            },
            "authority_scope": {
                "policy_identifier": "test-ns",
                "policy_version": "1",
                "authorized_by": "test-user",
                "authorization_reference": "ref-1",
            },
            "decision_reason": "ce04c1 test",
        },
        headers=auth_headers,
    )
    assert r.status_code == 400
    body = r.json()
    assert body.get("error_code") == "MISSING_IDEMPOTENCY_KEY"
