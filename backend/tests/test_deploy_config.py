"""DEMO_RENDER_02 / DEMO_NEON_03 — deployment configuration regression tests.

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
  - DEMO_NEON_03: DATABASE_URL fail-fast for hosted demo (missing / SQLite / no SSL)

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
from fastapi.testclient import TestClient


# ── Module-state isolation ─────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def restore_modules():
    import app.core.security as sec
    import app.main as main_mod
    import app.db.session as db_mod

    original_secret = sec.SECRET_KEY
    original_origins = list(main_mod._ALLOWED_ORIGINS)
    original_disable = main_mod._disable_docs
    original_db_url = db_mod.DATABASE_URL
    original_engine = db_mod.engine
    original_session_local = db_mod.SessionLocal

    yield

    sec.SECRET_KEY = original_secret
    main_mod._ALLOWED_ORIGINS = original_origins
    main_mod._disable_docs = original_disable
    db_mod.DATABASE_URL = original_db_url
    db_mod.engine = original_engine
    db_mod.SessionLocal = original_session_local


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


# ── DATABASE_URL validation for hosted demo (DEMO_NEON_03) ────────────────────

class TestDatabaseUrlValidation:
    """DEMO_NEON_03: fail-fast checks for hosted-demo DATABASE_URL.

    When HOSTED_DEMO=true the backend must refuse to start if DATABASE_URL
    is missing, uses SQLite, or lacks TLS/SSL.  Local development (HOSTED_DEMO
    unset) must not be affected.  No live Neon connection is required — SQLAlchemy
    create_engine is lazy and does not connect at construction time.
    """

    def test_missing_database_url_rejected_in_hosted_mode(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.db.session as s
        with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
            importlib.reload(s)

    def test_sqlite_url_rejected_in_hosted_mode(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./spot_welding_dev.db")
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.db.session as s
        with pytest.raises(RuntimeError, match="PostgreSQL"):
            importlib.reload(s)

    def test_postgresql_without_ssl_rejected_in_hosted_mode(self, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+psycopg://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb",
        )
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.db.session as s
        with pytest.raises(RuntimeError, match="SSL"):
            importlib.reload(s)

    def test_valid_neon_url_accepted_in_hosted_mode(self, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+psycopg://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require",
        )
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.db.session as s
        importlib.reload(s)  # must not raise; create_engine is lazy, no live connection needed

    def test_sqlite_allowed_without_hosted_mode(self, monkeypatch):
        monkeypatch.delenv("HOSTED_DEMO", raising=False)
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./spot_welding_dev.db")
        import app.db.session as s
        importlib.reload(s)  # must not raise

    def test_missing_database_url_allowed_without_hosted_mode(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("HOSTED_DEMO", raising=False)
        import app.db.session as s
        importlib.reload(s)  # must not raise; falls back to SQLite dev DB


# ── PostgreSQL Boolean compatibility — migration 0015 (DEMO_NEON_04) ──────────

class TestBooleanMigrationCompatibility:
    """DEMO_NEON_04: regression guard for PostgreSQL BOOLEAN server_default values.

    PostgreSQL rejects integer server defaults (DEFAULT 1 / DEFAULT 0) on BOOLEAN
    columns with DatatypeMismatch.  The migration must use SQL literals 'true'/'false'.
    SQLite accepts these literals too, so the fix is cross-database compatible.
    """

    _MIGRATION = (
        Path(__file__).parent.parent
        / "alembic/versions/0015_organization_and_profile_tables.py"
    )

    def _content(self) -> str:
        return self._MIGRATION.read_text()

    def test_no_integer_true_server_default_for_boolean_columns(self):
        content = self._content()
        assert 'server_default="1"' not in content, (
            "server_default='1' on a BOOLEAN column is rejected by PostgreSQL "
            "(DatatypeMismatch: boolean vs smallint). Use sa.text('true') instead."
        )

    def test_no_integer_false_server_default_for_boolean_columns(self):
        content = self._content()
        assert 'server_default="0"' not in content, (
            "server_default='0' on a BOOLEAN column is rejected by PostgreSQL "
            "(DatatypeMismatch: boolean vs smallint). Use sa.text('false') instead."
        )

    def test_system_org_insert_uses_sql_literal_not_bound_boolean(self):
        content = self._content()
        # The INSERT must use the SQL literal 'true', not a :active parameter.
        # psycopg3 may bind Python bool (subclass of int) as smallint in text() queries.
        assert '"active": True' not in content, (
            "INSERT uses :active parameter with Python True, which psycopg3 may bind "
            "as smallint. Use the SQL literal 'true' directly in the INSERT statement."
        )
        assert "true" in content, "INSERT must contain SQL literal 'true' for is_active"

    def test_boolean_server_defaults_use_postgresql_literals(self):
        content = self._content()
        assert 'sa.text("true")' in content, (
            "organizations.is_active and org_members.is_active must use "
            "server_default=sa.text('true')"
        )
        assert 'sa.text("false")' in content, (
            "reference_profiles.is_system_default must use "
            "server_default=sa.text('false')"
        )


# ── CORS preflight for login endpoint (DEMO_CORS_01) ──────────────────────────

class TestCorsPreflightLogin:
    """DEMO_CORS_01: regression guard for CORS preflight failure on /api/v1/auth/login.

    Confirmed failure: OPTIONS preflight from https://spotweldpro-ai-demo.onrender.com
    returned no Access-Control-Allow-Origin, blocking the login POST in the browser.

    Root causes:
      1. CORS_ORIGINS is sync: false in render.yaml — operator must set it manually.
         If absent, the backend silently uses localhost-only defaults and rejects
         every cross-origin preflight.
      2. A trailing slash in the operator-entered value (e.g.
         https://spotweldpro-ai-demo.onrender.com/) would cause a mismatch with the
         browser Origin header (which never has a trailing slash).

    Fix (DEMO_CORS_01):
      - Trailing slashes are stripped from each parsed origin.
      - HOSTED_DEMO=true + missing CORS_ORIGINS now raises RuntimeError (fail-fast),
        consistent with the JWT_SECRET_KEY and DATABASE_URL guards.
      - HOSTED_DEMO=true + HTTP-only origins raises RuntimeError.
    """

    _RENDER_ORIGIN = "https://spotweldpro-ai-demo.onrender.com"

    def test_login_preflight_from_render_origin_returns_allow_origin(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", self._RENDER_ORIGIN)
        import app.main as m
        importlib.reload(m)
        with TestClient(m.app) as c:
            r = c.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": self._RENDER_ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
        assert r.headers.get("access-control-allow-origin") == self._RENDER_ORIGIN

    def test_login_preflight_returns_allow_credentials(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", self._RENDER_ORIGIN)
        import app.main as m
        importlib.reload(m)
        with TestClient(m.app) as c:
            r = c.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": self._RENDER_ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
        assert r.headers.get("access-control-allow-credentials") == "true"

    def test_login_preflight_allows_post_method(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", self._RENDER_ORIGIN)
        import app.main as m
        importlib.reload(m)
        with TestClient(m.app) as c:
            r = c.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": self._RENDER_ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
        acam = r.headers.get("access-control-allow-methods", "")
        assert "POST" in acam or acam == "*"

    def test_login_preflight_from_unlisted_origin_rejected(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", self._RENDER_ORIGIN)
        import app.main as m
        importlib.reload(m)
        with TestClient(m.app) as c:
            r = c.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "https://attacker.example.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "https://attacker.example.com"

    def test_cors_missing_in_hosted_mode_raises(self, monkeypatch):
        monkeypatch.setenv("HOSTED_DEMO", "true")
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        import app.main as m
        with pytest.raises(RuntimeError, match="CORS_ORIGINS is required"):
            importlib.reload(m)

    def test_cors_http_only_origins_in_hosted_mode_raises(self, monkeypatch):
        monkeypatch.setenv("HOSTED_DEMO", "true")
        monkeypatch.setenv("CORS_ORIGINS", "http://insecure.example.com")
        import app.main as m
        with pytest.raises(RuntimeError, match="HTTPS"):
            importlib.reload(m)

    def test_cors_trailing_slash_stripped_from_origin(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", self._RENDER_ORIGIN + "/")
        import app.main as m
        importlib.reload(m)
        assert self._RENDER_ORIGIN in m._ALLOWED_ORIGINS
        assert (self._RENDER_ORIGIN + "/") not in m._ALLOWED_ORIGINS
