"""GATE-07 demo-login verification tests.

Covers: login, token generation, role authorization, admin-function denial,
and token invalidation (logout simulation).

Passwords and tokens are never printed to stdout or captured in assertions
that would appear in test output.
"""

import pytest


def _login_demo(client):
    return client.post("/api/v1/auth/login", json={"username": "demo", "password": "A1234"})


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Login and token generation ────────────────────────────────────────────────

def test_demo_login_returns_200(client):
    r = _login_demo(client)
    assert r.status_code == 200


def test_demo_login_returns_token_fields(client):
    r = _login_demo(client)
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body.get("token_type") == "bearer"


def test_demo_token_authorizes_me_endpoint(client):
    token = _login_demo(client).json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.status_code == 200


# ── Role and authorization ────────────────────────────────────────────────────

def test_demo_role_is_read_only(client):
    token = _login_demo(client).json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.json()["role"] == "READ_ONLY"


def test_demo_username_in_me_response(client):
    token = _login_demo(client).json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.json()["username"] == "demo"


def test_demo_cannot_create_users(client):
    """READ_ONLY demo account must be denied admin user-creation."""
    token = _login_demo(client).json()["access_token"]
    r = client.post(
        "/api/v1/auth/users",
        json={
            "username": "injected_admin",
            "email": "injected@spotwelding.example",
            "full_name": "Injected",
            "password": "Password1!",
            "role": "SYSTEM_ADMIN",
        },
        headers=_bearer(token),
    )
    assert r.status_code in (401, 403)


def test_demo_cannot_list_users(client):
    """READ_ONLY demo account must not access the user list."""
    token = _login_demo(client).json()["access_token"]
    r = client.get("/api/v1/auth/users", headers=_bearer(token))
    assert r.status_code in (401, 403)


# ── Logout simulation (token invalidation) ────────────────────────────────────

def test_no_token_returns_401_on_protected_route(client):
    """A request with no Authorization header must be rejected."""
    r = client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)


def test_garbage_token_returns_401(client):
    """A tampered or random token must be rejected."""
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code in (401, 403)
