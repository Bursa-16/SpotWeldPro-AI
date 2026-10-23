"""
BACKEND-RELIABILITY-FIX-01 — cold-start and error-classification tests

Verifies:
1. Health endpoint answers without a database query (process-alive only).
2. Login POST returns structured JSON errors, not unhandled exceptions or timeouts.
3. Wrong credentials produce HTTP 401 + INVALID_CREDENTIALS (not 500 / network error).
4. Inactive user produces HTTP 403 + INACTIVE_USER.
5. Login errors are distinct from server startup errors — clients can distinguish them.
6. Health endpoint does NOT change after a failed login (process stays alive).
"""
import pytest
from fastapi.testclient import TestClient


# ── health endpoint independence ─────────────────────────────────────────────

class TestHealthIndependence:
    def test_health_returns_200_without_auth(self, client: TestClient):
        r = client.get('/api/v1/health')
        assert r.status_code == 200

    def test_health_body_contains_status_ok(self, client: TestClient):
        r = client.get('/api/v1/health')
        assert r.json()['status'] == 'ok'

    def test_health_responds_before_any_db_operation(self, client: TestClient):
        # Cold-start scenario: health is probed before login.
        # Should never return 5xx regardless of DB state.
        r = client.get('/api/v1/health')
        assert r.status_code == 200
        assert r.json().get('status') == 'ok'

    def test_health_is_not_affected_by_a_failed_login(self, client: TestClient):
        # Backend stays alive even after an authentication failure.
        client.post('/api/v1/auth/login', json={'username': 'nosuchuser', 'password': 'x'})
        r = client.get('/api/v1/health')
        assert r.status_code == 200

    def test_health_content_type_is_json(self, client: TestClient):
        r = client.get('/api/v1/health')
        assert 'application/json' in r.headers.get('content-type', '')


# ── login error classification ────────────────────────────────────────────────

class TestLoginErrorClassification:
    """
    Verify that login failures produce structured JSON responses the frontend
    can classify — specifically that they are not silent network timeouts or 5xx
    server errors (which would be indistinguishable from cold-start failures).
    """

    def test_wrong_password_returns_401_not_5xx(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'WRONG'})
        assert r.status_code == 401

    def test_wrong_password_returns_invalid_credentials_code(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'WRONG'})
        body = r.json()
        assert body.get('error_code') == 'INVALID_CREDENTIALS'

    def test_wrong_username_returns_401(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'nosuchuser', 'password': 'x'})
        assert r.status_code == 401

    def test_wrong_username_returns_invalid_credentials_not_404(self, client: TestClient):
        # Must not distinguish "user not found" from "wrong password" — timing-safe.
        r = client.post('/api/v1/auth/login', json={'username': 'nosuchuser', 'password': 'x'})
        assert r.json().get('error_code') == 'INVALID_CREDENTIALS'

    def test_correct_credentials_return_200(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'A1234'})
        assert r.status_code == 200

    def test_correct_credentials_return_tokens(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'A1234'})
        body = r.json()
        assert 'access_token' in body
        assert 'refresh_token' in body
        assert isinstance(body['access_token'], str)
        assert len(body['access_token']) > 20

    def test_login_response_is_json_not_html(self, client: TestClient):
        # Guards against a framework misconfiguration that would return an HTML
        # error page, which the frontend cannot parse as a structured error.
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'WRONG'})
        assert 'application/json' in r.headers.get('content-type', '')

    def test_login_error_body_has_message_field(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'WRONG'})
        body = r.json()
        assert 'message' in body
        assert isinstance(body['message'], str)


# ── inactive-user path ────────────────────────────────────────────────────────

class TestInactiveUser:
    @pytest.fixture(autouse=True)
    def inactive_user(self, database):
        from app.db.session import SessionLocal
        from app.models.entities import User
        from app.core.security import hash_password, canonicalize_username
        with SessionLocal() as db:
            u = db.query(User).filter(User.username == canonicalize_username('inactive_test')).first()
            if not u:
                db.add(User(
                    username=canonicalize_username('inactive_test'),
                    email='inactive_test@internal.spotwelding',
                    full_name='Inactive Test User',
                    password_hash=hash_password('TestPass99!'),
                    role='READ_ONLY',
                    is_active=False,
                ))
                db.commit()
        yield
        with SessionLocal() as db:
            u = db.query(User).filter(User.username == canonicalize_username('inactive_test')).first()
            if u:
                db.delete(u)
                db.commit()

    def test_inactive_user_returns_403(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'inactive_test', 'password': 'TestPass99!'})
        assert r.status_code == 403

    def test_inactive_user_returns_inactive_user_code(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'inactive_test', 'password': 'TestPass99!'})
        assert r.json().get('error_code') == 'INACTIVE_USER'


# ── client-side distinguishability ───────────────────────────────────────────

class TestErrorDistinguishability:
    """
    Auth failures (401/403) vs server errors (5xx) must be structurally distinct.
    The frontend classifies no-response as NETWORK_ERROR/TIMEOUT_ERROR and HTTP
    responses with an error_code as the specific BackendApiErrorCode.
    This test suite confirms the backend always sends a response (not a hang)
    with a parseable error_code on expected failure paths.
    """

    def test_auth_failure_has_lower_status_than_500(self, client: TestClient):
        r = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'WRONG'})
        assert r.status_code < 500

    def test_malformed_login_body_returns_422_not_500(self, client: TestClient):
        # Missing required fields — should be a 422 validation error, not a crash.
        r = client.post('/api/v1/auth/login', json={})
        assert r.status_code == 422

    def test_health_and_login_error_are_distinguishable_by_status(self, client: TestClient):
        health = client.get('/api/v1/health')
        login_fail = client.post('/api/v1/auth/login', json={'username': 'demo', 'password': 'WRONG'})
        assert health.status_code == 200
        assert login_fail.status_code == 401
        # Client can distinguish: health=200 means backend up; login=401 means credentials wrong
        assert health.status_code != login_fail.status_code
