"""GATE-08 regression tests for security fixes.

Covers:
  - CORS origins: env-driven, localhost default, no wildcard
  - API docs: DISABLE_DOCS hides /docs /redoc /openapi.json
  - JWT guard: placeholder and short secrets rejected in HOSTED_DEMO mode
  - Admin seeder: username required in lifespan

NOTE: Tests that use importlib.reload() restore the original module state via
the `restore_modules` autouse fixture so they do not pollute test_auth.py or
any other test module that imports from the same process.
"""

import importlib
import os
import pytest


@pytest.fixture(autouse=True)
def restore_modules():
    """Save and restore app.main and app.core.security module state around each test."""
    import app.core.security as sec
    import app.main as main_mod

    original_secret = sec.SECRET_KEY
    original_origins = list(main_mod._ALLOWED_ORIGINS)
    original_disable = main_mod._disable_docs

    yield

    # Restore module-level variables mutated by reload() calls.
    sec.SECRET_KEY = original_secret
    main_mod._ALLOWED_ORIGINS = original_origins
    main_mod._disable_docs = original_disable


# ── CORS ─────────────────────────────────────────────────────────────────────

class TestCorsConfiguration:
    def test_default_includes_localhost_5173(self, monkeypatch):
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        import app.main as m
        importlib.reload(m)
        assert "http://localhost:5173" in m._ALLOWED_ORIGINS

    def test_env_var_overrides_default(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "https://demo.example.internal,https://demo2.example.internal")
        import app.main as m
        importlib.reload(m)
        assert "https://demo.example.internal" in m._ALLOWED_ORIGINS
        assert "https://demo2.example.internal" in m._ALLOWED_ORIGINS
        assert "http://localhost:5173" not in m._ALLOWED_ORIGINS

    def test_env_var_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "  https://demo.example.internal  ,  http://localhost:5173  ")
        import app.main as m
        importlib.reload(m)
        assert "https://demo.example.internal" in m._ALLOWED_ORIGINS
        assert "http://localhost:5173" in m._ALLOWED_ORIGINS

    def test_no_wildcard_in_allowed_origins(self, monkeypatch):
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        import app.main as m
        importlib.reload(m)
        assert "*" not in m._ALLOWED_ORIGINS

    def test_cors_rejects_unlisted_origin(self, client):
        r = client.options(
            "/api/v1/health",
            headers={"Origin": "https://attacker.example.com", "Access-Control-Request-Method": "GET"},
        )
        # Either no ACAO header, or it must not be the attacker's origin
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "https://attacker.example.com"

    def test_cors_allows_configured_origin(self, client):
        r = client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao == "http://localhost:5173"


# ── API documentation ─────────────────────────────────────────────────────────

class TestApiDocsConfiguration:
    def test_docs_enabled_by_default(self, client):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_redoc_enabled_by_default(self, client):
        r = client.get("/redoc")
        assert r.status_code == 200

    def test_openapi_json_enabled_by_default(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200

    def test_disable_docs_hides_docs(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "true")
        import app.main as m
        importlib.reload(m)
        assert m._disable_docs is True
        assert m.app.docs_url is None

    def test_disable_docs_hides_redoc(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "true")
        import app.main as m
        importlib.reload(m)
        assert m.app.redoc_url is None

    def test_disable_docs_hides_openapi(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "true")
        import app.main as m
        importlib.reload(m)
        assert m.app.openapi_url is None

    def test_disable_docs_false_keeps_docs(self, monkeypatch):
        monkeypatch.setenv("DISABLE_DOCS", "false")
        import app.main as m
        importlib.reload(m)
        assert m._disable_docs is False
        assert m.app.docs_url is not None


# ── JWT secret guard ──────────────────────────────────────────────────────────

class TestJwtSecretGuard:
    def _reload_security(self, monkeypatch, *, secret, hosted_demo="true"):
        monkeypatch.setenv("JWT_SECRET_KEY", secret)
        monkeypatch.setenv("HOSTED_DEMO", hosted_demo)
        import app.core.security as s
        importlib.reload(s)

    def test_placeholder_rejected_in_hosted_mode(self, monkeypatch):
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

    def test_strong_secret_accepted_in_hosted_mode(self, monkeypatch):
        strong = "a" * 32
        monkeypatch.setenv("JWT_SECRET_KEY", strong)
        monkeypatch.setenv("HOSTED_DEMO", "true")
        import app.core.security as s
        importlib.reload(s)  # must not raise
        assert s.SECRET_KEY == strong

    def test_placeholder_allowed_in_dev_mode(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "replace-with-a-long-random-secret")
        monkeypatch.delenv("HOSTED_DEMO", raising=False)
        import app.core.security as s
        importlib.reload(s)  # must not raise in dev mode

    def test_missing_secret_always_rejected(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.delenv("HOSTED_DEMO", raising=False)
        import app.core.security as s
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            importlib.reload(s)


# ── Admin seeder username ─────────────────────────────────────────────────────

class TestAdminSeederUsername:
    def test_lifespan_requires_admin_username(self, monkeypatch):
        """Seeder must read ADMIN_USERNAME from env (not just ADMIN_EMAIL)."""
        import app.main as m
        importlib.reload(m)
        # The _ALLOWED_ORIGINS list means the module loaded correctly;
        # verify the lifespan uses ADMIN_USERNAME by checking the source.
        import inspect
        src = inspect.getsource(m.lifespan)
        assert "ADMIN_USERNAME" in src

    def test_lifespan_uses_canonicalize_username(self, monkeypatch):
        import app.main as m
        importlib.reload(m)
        import inspect
        src = inspect.getsource(m.lifespan)
        assert "canonicalize_username" in src
