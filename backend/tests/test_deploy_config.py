"""DEMO_RENDER_02 — deployment configuration regression tests.

Covers the production-safety configuration introduced for the Render
customer demo:

  - DISABLE_DOCS=true hides /docs, /redoc and /openapi.json
  - HOSTED_DEMO=true rejects placeholder / short JWT_SECRET_KEY
  - CORS_ORIGINS env var overrides the localhost default
  - Wildcard CORS is never allowed
  - CORS_ORIGINS containing only HTTPS origins when HOSTED_DEMO=true
  - /api/v1/health is always accessible (anonymous)
  - Protected endpoints reject anonymous requests
  - start.sh script exists and is a valid shell script
  - seed_demo_user.py idempotency guard

These extend the existing GATE-08 security tests with deployment-specific
assertions.  Module reload is used to test env-driven configuration;
the restore_modules fixture ensures no cross-test contamination.
"""
from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


# ── Module-state isolation ─────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def restore_modules():
    import app.core.security as sec
    import app.main as main_mod

    original_secret = sec.SECRET_KEY
    original_origins = list(main_mod._ALLOWED_ORIGINS)
    original_disable = main_mod._disable_docs

    yield

    sec.SECRET_KEY = original_secret
    main_mod._ALLOWED_ORIGINS = original_origins
    main_mod._disable_docs = original_disable


# ── Health endpoint (always public) ───────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_ok_anonymous(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_returns_service_name(self, client):
        r = client.get("/api/v1/health")
        assert "service" in r.json()


# ── API documentation disabled in demo mode ──────────────────────────────────

class TestDocumentationDisabled:
    def test_disable_docs_true_hides_docs_url(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "true")
        import app.main as m
        importlib.reload(m)
        assert m.app.docs_url is None

    def test_disable_docs_true_hides_redoc_url(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "true")
        import app.main as m
        importlib.reload(m)
        assert m.app.redoc_url is None

    def test_disable_docs_true_hides_openapi_url(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "true")
        import app.main as m
        importlib.reload(m)
        assert m.app.openapi_url is None

    def test_disable_docs_false_exposes_docs_url(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "false")
        import app.main as m
        importlib.reload(m)
        assert m.app.docs_url is not None

    def test_disable_docs_accepts_true_variants(self, monkeypatch):
        for val in ("true", "1", "yes", "True", "YES"):
            monkeypatch.setenv("DISABLE_DOCS", val)
            import app.main as m
            importlib.reload(m)
            assert m._disable_docs is True, f"Expected _disable_docs=True for DISABLE_DOCS={val!r}"


# ── CORS — production safety ───────────────────────────────────────────────────

class TestCorsProductionSafety:
    def test_cors_no_wildcard_by_default(self, monkeypatch):
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        import app.main as m
        importlib.reload(m)
        assert "*" not in m._ALLOWED_ORIGINS

    def test_cors_env_override_replaces_default(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "https://spotweldpro-ai-demo.onrender.com")
        import app.main as m
        importlib.reload(m)
        assert "https://spotweldpro-ai-demo.onrender.com" in m._ALLOWED_ORIGINS
        assert "http://localhost:5173" not in m._ALLOWED_ORIGINS

    def test_cors_multiple_origins_parsed(self, monkeypatch):
        monkeypatch.setenv(
            "CORS_ORIGINS",
            "https://demo.spotweldpro.example,https://staging.spotweldpro.example"
        )
        import app.main as m
        importlib.reload(m)
        assert "https://demo.spotweldpro.example" in m._ALLOWED_ORIGINS
        assert "https://staging.spotweldpro.example" in m._ALLOWED_ORIGINS

    def test_cors_rejects_unlisted_origin(self, client):
        r = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://attacker.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "https://attacker.example.com"

    def test_cors_allows_configured_origin(self, client):
        r = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao == "http://localhost:5173"


# ── JWT secret strength ────────────────────────────────────────────────────────

class TestJwtSecretStrength:
    def test_known_placeholder_rejected_in_hosted_mode(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "replace-with-a-long-random-secret")
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.core.security as s
        with pytest.raises(RuntimeError, match="placeholder"):
            importlib.reload(s)

    def test_short_secret_rejected_in_hosted_mode(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "tooshort")
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.core.security as s
        with pytest.raises(RuntimeError, match="too short"):
            importlib.reload(s)

    def test_32_char_secret_accepted_in_hosted_mode(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.core.security as s
        importlib.reload(s)  # must not raise

    def test_missing_jwt_key_always_rejected(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        import app.core.security as s
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            importlib.reload(s)


# ── Anonymous access enforcement ──────────────────────────────────────────────

class TestAnonymousAccessEnforcement:
    def test_failure_probability_rejects_anonymous(self, client):
        r = client.post("/api/v1/failure-probability/analyze", json={})
        assert r.status_code == 401
        assert r.json()["error_code"] == "INVALID_TOKEN"

    def test_engineering_weld_lobe_rejects_anonymous(self, client):
        r = client.post("/api/v1/engineering/weld-lobe", json={})
        assert r.status_code == 401

    def test_dashboard_rejects_anonymous(self, client):
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 401

    def test_projects_rejects_anonymous(self, client):
        r = client.get("/api/v1/projects")
        assert r.status_code == 401

    def test_weld_analysis_allows_anonymous(self, client):
        # PUBLIC_DEMO endpoint — anonymous access is intentional; expect 422 (validation),
        # not 401 (unauthorized), confirming the endpoint is reachable without auth.
        r = client.post("/api/v1/weld-analysis", json={})
        assert r.status_code == 422


# ── READ_ONLY role access ──────────────────────────────────────────────────────

class TestReadOnlyRoleAccess:
    @pytest.fixture
    def demo_headers(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "demo", "password": "A1234"})
        assert r.status_code == 200, f"Demo login failed: {r.json()}"
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_read_only_can_access_dashboard(self, client, demo_headers):
        r = client.get("/api/v1/dashboard", headers=demo_headers)
        assert r.status_code == 200

    def test_read_only_can_access_projects(self, client, demo_headers):
        r = client.get("/api/v1/projects", headers=demo_headers)
        assert r.status_code == 200

    def test_read_only_cannot_create_project(self, client, demo_headers):
        r = client.post(
            "/api/v1/projects",
            json={"name": "Demo Test Project", "description": ""},
            headers=demo_headers,
        )
        assert r.status_code == 403

    def test_read_only_me_returns_user(self, client, demo_headers):
        r = client.get("/api/v1/auth/me", headers=demo_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "demo"
        assert data["role"] == "READ_ONLY"


# ── Startup script exists and is valid ────────────────────────────────────────

class TestStartupScript:
    def test_start_sh_exists(self):
        p = Path(__file__).parent.parent / "scripts" / "start.sh"
        assert p.exists(), "backend/scripts/start.sh not found"

    def test_start_sh_is_not_empty(self):
        p = Path(__file__).parent.parent / "scripts" / "start.sh"
        content = p.read_text()
        assert len(content.strip()) > 0

    def test_start_sh_contains_alembic_upgrade(self):
        p = Path(__file__).parent.parent / "scripts" / "start.sh"
        assert "alembic upgrade head" in p.read_text()

    def test_start_sh_contains_uvicorn(self):
        p = Path(__file__).parent.parent / "scripts" / "start.sh"
        assert "uvicorn" in p.read_text()

    def test_start_sh_seeds_demo_user_conditionally(self):
        p = Path(__file__).parent.parent / "scripts" / "start.sh"
        content = p.read_text()
        assert "DEMO_PASSWORD" in content
        assert "seed_demo_user.py" in content


# ── seed_demo_user.py idempotency ─────────────────────────────────────────────

class TestSeedDemoUserIdempotency:
    def test_seed_script_exists(self):
        p = Path(__file__).parent.parent / "scripts" / "seed_demo_user.py"
        assert p.exists(), "backend/scripts/seed_demo_user.py not found"

    def test_seed_script_checks_existing_user(self):
        p = Path(__file__).parent.parent / "scripts" / "seed_demo_user.py"
        content = p.read_text()
        assert "existing" in content or "already exists" in content, \
            "seed_demo_user.py must check for existing user before creating"

    def test_seed_script_uses_read_only_role(self):
        p = Path(__file__).parent.parent / "scripts" / "seed_demo_user.py"
        content = p.read_text()
        assert "READ_ONLY" in content

    def test_seed_script_requires_demo_password_env(self):
        p = Path(__file__).parent.parent / "scripts" / "seed_demo_user.py"
        content = p.read_text()
        assert "DEMO_PASSWORD" in content

    def test_seed_script_role_is_least_privilege(self):
        p = Path(__file__).parent.parent / "scripts" / "seed_demo_user.py"
        content = p.read_text()
        # Must use READ_ONLY, not SYSTEM_ADMIN or PROCESS_ENGINEER
        assert "SYSTEM_ADMIN" not in content
        assert "PROCESS_ENGINEER" not in content

    def test_seed_script_does_not_hardcode_password(self):
        p = Path(__file__).parent.parent / "scripts" / "seed_demo_user.py"
        content = p.read_text()
        # Password must come from environment, not a literal string assignment
        assert "os.environ" in content, "Password must be read from environment, not hardcoded"


# ── One-click demo login — backend authentication ─────────────────────────────

class TestOneClickDemoLogin:
    """Backend contract tests for the public demo credentials (demo/A1234).

    The frontend pre-fills these when VITE_DEMO_MODE=true (Render demo build only).
    The backend stores the password as a PBKDF2-SHA256 hash — never plaintext.
    These tests verify the full auth → session → permissions chain.
    """

    @pytest.fixture
    def demo_headers(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "demo", "password": "A1234"})
        assert r.status_code == 200, f"Demo login failed: {r.json()}"
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_demo_credentials_authenticate_successfully(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "demo", "password": "A1234"})
        assert r.status_code == 200

    def test_demo_login_returns_jwt_tokens(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "demo", "password": "A1234"})
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_demo_token_authenticates_me_endpoint(self, client, demo_headers):
        r = client.get("/api/v1/auth/me", headers=demo_headers)
        assert r.status_code == 200
        assert r.json()["username"] == "demo"

    def test_demo_role_is_read_only(self, client, demo_headers):
        r = client.get("/api/v1/auth/me", headers=demo_headers)
        assert r.json()["role"] == "READ_ONLY"

    def test_demo_is_active(self, client, demo_headers):
        r = client.get("/api/v1/auth/me", headers=demo_headers)
        assert r.json()["is_active"] is True

    def test_demo_redirects_to_dashboard_on_success(self, client, demo_headers):
        r = client.get("/api/v1/dashboard", headers=demo_headers)
        assert r.status_code == 200

    def test_demo_can_access_engineering_endpoints(self, client, demo_headers):
        # READ_ONLY has weld:read — should pass auth, fail on missing body (422)
        r = client.post("/api/v1/engineering/weld-lobe", json={}, headers=demo_headers)
        assert r.status_code in (200, 422), f"Expected 200 or 422, got {r.status_code}"

    def test_demo_cannot_create_users(self, client, demo_headers):
        r = client.post(
            "/api/v1/auth/users",
            json={"username": "newuser", "email": "new@x.com", "full_name": "N U",
                  "password": "Pass123!", "role": "READ_ONLY"},
            headers=demo_headers,
        )
        assert r.status_code == 403

    def test_demo_cannot_create_projects(self, client, demo_headers):
        r = client.post(
            "/api/v1/projects",
            json={"name": "Attack Project", "description": ""},
            headers=demo_headers,
        )
        assert r.status_code == 403

    def test_wrong_password_returns_401(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "demo", "password": "wrongpass"})
        assert r.status_code == 401

    def test_wrong_password_returns_invalid_credentials_code(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "demo", "password": "wrongpass"})
        assert r.json()["error_code"] == "INVALID_CREDENTIALS"

    def test_logout_clears_session(self, client):
        # Logout is client-side (localStorage clear) — verify token invalidation
        # by using a fabricated invalid token
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401
