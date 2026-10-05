"""AUTH-UX-03 test suite for username-based authentication.

Covers all required scenarios from the AUTH-UX-03 task spec:
  - valid username login
  - wrong username
  - wrong password
  - username normalization / case-insensitive login
  - duplicate username rejected on admin create
  - existing email remains persisted (not removed by migration)
  - admin user creation requires both username and email
  - demo/A1234 login succeeds
  - demo account role is READ_ONLY (minimum-privilege)
  - email-only login rejected under final contract
  - migration backfill assertions (null / duplicate checks via unit test)

The conftest database fixture creates:
  - admin  / ChangeMe123!  / SYSTEM_ADMIN
  - demo   / A1234         / READ_ONLY
"""

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _login(client, username: str, password: str):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────────────────────
# Existing regression: login + dashboard still works (updated to username)
# ──────────────────────────────────────────────────────────────────────────────

def test_login_and_dashboard(client):
    response = _login(client, "admin", "ChangeMe123!")
    assert response.status_code == 200
    token = response.json()["access_token"]

    dashboard = client.get("/api/v1/dashboard", headers=_bearer(token))
    assert dashboard.status_code == 200
    assert "total_projects" in dashboard.json()


def test_protected_projects_require_token(client):
    response = client.get("/api/v1/projects")
    assert response.status_code in (401, 403)
    body = response.json()
    assert body.get("error_code") in ("INVALID_TOKEN", "PERMISSION_DENIED")


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — valid username login
# ──────────────────────────────────────────────────────────────────────────────

def test_valid_username_login(client):
    r = _login(client, "admin", "ChangeMe123!")
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body.get("token_type") == "bearer"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — wrong username returns 401
# ──────────────────────────────────────────────────────────────────────────────

def test_wrong_username_returns_401(client):
    r = _login(client, "nonexistent_user_xyz", "ChangeMe123!")
    assert r.status_code == 401
    assert r.json().get("error_code") == "INVALID_CREDENTIALS"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — wrong password returns 401
# ──────────────────────────────────────────────────────────────────────────────

def test_wrong_password_returns_401(client):
    r = _login(client, "admin", "WrongPassword!")
    assert r.status_code == 401
    assert r.json().get("error_code") == "INVALID_CREDENTIALS"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — username normalization (case-insensitive login)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("variant", ["admin", "Admin", "ADMIN", " admin ", " ADMIN "])
def test_username_case_normalization(client, variant):
    """All case and whitespace variants of 'admin' must resolve to the same user."""
    r = _login(client, variant, "ChangeMe123!")
    assert r.status_code == 200, f"Expected 200 for username variant {repr(variant)}, got {r.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — demo account credentials
# ──────────────────────────────────────────────────────────────────────────────

def test_demo_login_succeeds(client):
    r = _login(client, "demo", "A1234")
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.parametrize("variant", ["demo", "Demo", "DEMO"])
def test_demo_username_normalization(client, variant):
    r = _login(client, variant, "A1234")
    assert r.status_code == 200, f"demo variant {repr(variant)} should authenticate"


def test_demo_role_is_read_only(client):
    """Demo account must use the least-privileged role (READ_ONLY)."""
    r = _login(client, "demo", "A1234")
    assert r.status_code == 200
    token = r.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.status_code == 200
    assert me.json()["role"] == "READ_ONLY"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — email is NOT accepted as login identifier
# ──────────────────────────────────────────────────────────────────────────────

def test_email_login_is_rejected(client):
    """After AUTH-UX-03, email may not be used as a login identifier."""
    r = _login(client, "admin@spotwelding.example", "ChangeMe123!")
    # email@domain is not a valid username for this user — should return 401
    assert r.status_code == 401
    assert r.json().get("error_code") == "INVALID_CREDENTIALS"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — /me returns username in response
# ──────────────────────────────────────────────────────────────────────────────

def test_me_returns_username(client):
    token = _login(client, "admin", "ChangeMe123!").json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "admin"
    assert body["email"] == "admin@spotwelding.example"  # email still persisted


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — existing email remains persisted (not dropped by migration)
# ──────────────────────────────────────────────────────────────────────────────

def test_existing_email_persisted_after_migration(client):
    """The email field must survive the migration intact."""
    token = _login(client, "admin", "ChangeMe123!").json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert me.status_code == 200
    assert me.json()["email"] == "admin@spotwelding.example"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — admin create-user requires BOTH username AND email
# ──────────────────────────────────────────────────────────────────────────────

def test_create_user_missing_username_returns_422(client, auth_headers):
    r = client.post(
        "/api/v1/auth/users",
        json={"email": "test@example.com", "full_name": "Test User", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_create_user_missing_email_returns_422(client, auth_headers):
    r = client.post(
        "/api/v1/auth/users",
        json={"username": "testuser", "full_name": "Test User", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_create_user_success(client, auth_headers):
    r = client.post(
        "/api/v1/auth/users",
        json={
            "username": "newengineer",
            "email": "newengineer@spotwelding.example",
            "full_name": "New Engineer",
            "password": "Password1!",
            "role": "READ_ONLY",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "newengineer"
    assert body["email"] == "newengineer@spotwelding.example"


def test_create_user_username_canonicalized(client, auth_headers):
    """Username must be stored in canonical (lowercase) form."""
    r = client.post(
        "/api/v1/auth/users",
        json={
            "username": "  UpperUser  ",
            "email": "upperuser@spotwelding.example",
            "full_name": "Upper User",
            "password": "Password1!",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["username"] == "upperuser"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — duplicate username rejected
# ──────────────────────────────────────────────────────────────────────────────

def test_duplicate_username_rejected(client, auth_headers):
    # Create first user
    client.post(
        "/api/v1/auth/users",
        json={"username": "dupuser", "email": "dup1@spotwelding.example", "full_name": "Dup One", "password": "Password1!"},
        headers=auth_headers,
    )
    # Attempt to create second user with same username (different email)
    r = client.post(
        "/api/v1/auth/users",
        json={"username": "dupuser", "email": "dup2@spotwelding.example", "full_name": "Dup Two", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 409
    assert r.json().get("error_code") == "USERNAME_ALREADY_EXISTS"


def test_duplicate_username_case_insensitive_rejected(client, auth_headers):
    """DupUser2 and dupuser2 must be treated as the same username."""
    client.post(
        "/api/v1/auth/users",
        json={"username": "dupuser2", "email": "dup3@spotwelding.example", "full_name": "Dup Three", "password": "Password1!"},
        headers=auth_headers,
    )
    r = client.post(
        "/api/v1/auth/users",
        json={"username": "DUPUSER2", "email": "dup4@spotwelding.example", "full_name": "Dup Four", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 409
    assert r.json().get("error_code") == "USERNAME_ALREADY_EXISTS"


# ──────────────────────────────────────────────────────────────────────────────
# AUTH-UX-03 — migration backfill assertions (unit test, no DB migration run)
# ──────────────────────────────────────────────────────────────────────────────

def test_migration_backfill_no_null_usernames():
    """The backfill helper must produce a non-null slug for any email."""
    from alembic.versions import _0014_auth_ux03_username as m  # noqa: PLC0415
    emails = [
        "admin@example.com",
        "alice@corp.io",
        "bob@corp.io",
    ]
    used: set[str] = set()
    for email in emails:
        base = m._email_local_part(email)
        slug = m._next_slug(used, base)
        assert slug is not None
        assert len(slug) > 0
        used.add(slug)
    assert None not in used


def test_migration_backfill_no_duplicate_usernames():
    """The collision resolver must produce unique slugs for duplicate local-parts."""
    from alembic.versions import _0014_auth_ux03_username as m  # noqa: PLC0415
    # Three users all have 'ali' as the email local-part
    emails = ["ali@a.com", "ali@b.com", "ali@c.com"]
    used: set[str] = set()
    slugs = []
    for email in emails:
        base = m._email_local_part(email)
        slug = m._next_slug(used, base)
        used.add(slug)
        slugs.append(slug)
    assert slugs == ["ali", "ali-2", "ali-3"]
    assert len(set(slugs)) == 3  # all unique


def test_wrong_username_returns_401_with_error_code(client):
    r = _login(client, "nonexistent_user_xyz", "ChangeMe123!")
    assert r.status_code == 401
    body = r.json()
    assert body.get("error_code") == "INVALID_CREDENTIALS"
    assert "message" in body
    assert body.get("context", {}).get("error_code") == "INVALID_CREDENTIALS"


# Invalid credentials error contract: wrong password returns 401


def test_wrong_password_returns_401_with_error_code(client):
    r = _login(client, "admin", "WrongPassword!")
    assert r.status_code == 401
    body = r.json()
    assert body.get("error_code") == "INVALID_CREDENTIALS"
    assert "message" in body
    assert body.get("context", {}).get("error_code") == "INVALID_CREDENTIALS"


# Username normalization (case-insensitive login)

@pytest.mark.parametrize("variant", ["admin", "Admin", "ADMIN", " admin ", " ADMIN "])

def test_email_login_is_rejected_with_error_code(client):
    """After AUTH-UX-03, email may not be used as a login identifier."""
    r = _login(client, "admin@spotwelding.example", "ChangeMe123!")
    assert r.status_code == 401
    body = r.json()
    assert body.get("error_code") == "INVALID_CREDENTIALS"
    assert "message" in body


# /me returns username in response


def test_duplicate_username_rejected_with_error_code(client, auth_headers):
    # Create first user
    client.post(
        "/api/v1/auth/users",
        json={"username": "dupuser", "email": "dup1@spotwelding.example", "full_name": "Dup One", "password": "Password1!"},
        headers=auth_headers,
    )
    # Attempt to create second user with same username (different email)
    r = client.post(
        "/api/v1/auth/users",
        json={"username": "dupuser", "email": "dup2@spotwelding.example", "full_name": "Dup Two", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 409
    body = r.json()
    assert body.get("error_code") == "USERNAME_ALREADY_EXISTS"
    assert "message" in body
    assert body.get("context", {}).get("resource_type") == "USER"



def test_duplicate_username_case_insensitive_rejected_with_error_code(client, auth_headers):
    """DupUser2 and dupuser2 must be treated as the same username."""
    client.post(
        "/api/v1/auth/users",
        json={"username": "dupuser2", "email": "dup3@spotwelding.example", "full_name": "Dup Three", "password": "Password1!"},
        headers=auth_headers,
    )
    r = client.post(
        "/api/v1/auth/users",
        json={"username": "DUPUSER2", "email": "dup4@spotwelding.example", "full_name": "Dup Four", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 409
    body = r.json()
    assert body.get("error_code") == "USERNAME_ALREADY_EXISTS"
    assert "message" in body


# Duplicate email rejected with EMAIL_ALREADY_EXISTS error code


def test_duplicate_email_rejected_with_error_code(client, auth_headers):
    # Create first user
    client.post(
        "/api/v1/auth/users",
        json={"username": "user1", "email": "shared@spotwelding.example", "full_name": "User One", "password": "Password1!"},
        headers=auth_headers,
    )
    # Attempt to create second user with same email (different username)
    r = client.post(
        "/api/v1/auth/users",
        json={"username": "user2", "email": "shared@spotwelding.example", "full_name": "User Two", "password": "Password1!"},
        headers=auth_headers,
    )
    assert r.status_code == 409
    body = r.json()
    assert body.get("error_code") == "EMAIL_ALREADY_EXISTS"
    assert "message" in body
    assert body.get("context", {}).get("resource_type") == "USER"


# Migration backfill assertions (unit test, no DB migration run)
