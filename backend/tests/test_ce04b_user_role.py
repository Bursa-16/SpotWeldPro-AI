"""CE-04-B test suite: canonical role codes.

10 test groups:
 1. canonical UserCreate default
 2. canonicalize legacy input
 3. canonicalize canonical input
 4. canonicalize System Admin
 5. reject unknown input
 6. normalize idempotence
 7. ROLE_PERMISSIONS canonical keys only
 8. legacy-label allowlist scan
 9. POST /auth/users cannot persist legacy role
10. migration pre-check ordering and NULL safety
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.api.dependencies import ROLE_PERMISSIONS
from app.models.enums import UserRole
from app.models.role_policy import canonicalize_role, normalize_user_role
from app.schemas.auth import UserCreate

# ---------------------------------------------------------------------------
# Paths used in static-analysis tests
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parent.parent
ROLE_POLICY_PATH = BACKEND_ROOT / "app" / "models" / "role_policy.py"
MIGRATION_PATH = BACKEND_ROOT / "alembic" / "versions" / "0013_ce04b_canonical_role_codes.py"

# Legacy display labels – the complete authorised set
LEGACY_LABELS = {
    "System Admin",
    "Process Engineer",
    "Quality Engineer",
    "Manufacturing Engineer",
    "Maintenance",
    "Operator",
    "Read Only",
    "Customer",
}

# Canonical codes (all 8)
CANONICAL_CODES = {r.value for r in UserRole}


# ---------------------------------------------------------------------------
# Group 1 – canonical UserCreate default
# ---------------------------------------------------------------------------
class TestUserCreateDefault:
    def test_default_role_is_read_only(self):
        uc = UserCreate(email="x@example.com", full_name="Test User", password="Password1!")
        assert uc.role == UserRole.READ_ONLY

    def test_default_role_value_is_string(self):
        uc = UserCreate(email="x@example.com", full_name="Test User", password="Password1!")
        assert uc.role == "READ_ONLY"


# ---------------------------------------------------------------------------
# Group 2 – canonicalize legacy input
# ---------------------------------------------------------------------------
class TestCanonalizeLegacy:
    @pytest.mark.parametrize("legacy, expected", [
        ("Process Engineer",       UserRole.PROCESS_ENGINEER),
        ("Quality Engineer",       UserRole.QUALITY_ENGINEER),
        ("Manufacturing Engineer", UserRole.MANUFACTURING_ENGINEER),
        ("Maintenance",            UserRole.MAINTENANCE),
        ("Operator",               UserRole.OPERATOR),
        ("Read Only",              UserRole.READ_ONLY),
        ("Customer",               UserRole.CUSTOMER),
    ])
    def test_legacy_maps_to_canonical(self, legacy, expected):
        assert canonicalize_role(legacy) == expected


# ---------------------------------------------------------------------------
# Group 3 – canonicalize canonical input (idempotent on canonical code)
# ---------------------------------------------------------------------------
class TestCanonicalizeCanonical:
    @pytest.mark.parametrize("code", list(CANONICAL_CODES))
    def test_canonical_maps_to_itself(self, code):
        result = canonicalize_role(code)
        assert result == code
        assert isinstance(result, UserRole)


# ---------------------------------------------------------------------------
# Group 4 – canonicalize System Admin
# ---------------------------------------------------------------------------
class TestCanonalizeSystemAdmin:
    def test_legacy_system_admin(self):
        assert canonicalize_role("System Admin") == UserRole.SYSTEM_ADMIN

    def test_canonical_system_admin(self):
        assert canonicalize_role("SYSTEM_ADMIN") == UserRole.SYSTEM_ADMIN


# ---------------------------------------------------------------------------
# Group 5 – reject unknown input
# ---------------------------------------------------------------------------
class TestRejectUnknown:
    @pytest.mark.parametrize("bad", [
        "Super User",
        "admin",
        "ADMIN",
        "",
        "read_only",
        "system_admin",
    ])
    def test_unknown_raises_value_error(self, bad):
        with pytest.raises(ValueError, match="Unknown role"):
            canonicalize_role(bad)


# ---------------------------------------------------------------------------
# Group 6 – normalize idempotence (both legacy and canonical pass through)
# ---------------------------------------------------------------------------
class TestNormalizeIdempotence:
    def test_legacy_normalizes_to_canonical(self):
        assert normalize_user_role("System Admin") == "SYSTEM_ADMIN"
        assert normalize_user_role("Read Only") == "READ_ONLY"

    def test_canonical_is_idempotent(self):
        for code in CANONICAL_CODES:
            assert normalize_user_role(code) == code

    def test_unknown_passes_through(self):
        assert normalize_user_role("unknown_role") == "unknown_role"


# ---------------------------------------------------------------------------
# Group 7 – ROLE_PERMISSIONS canonical keys only
# ---------------------------------------------------------------------------
class TestRolePermissionsKeys:
    def test_all_keys_are_user_role_members(self):
        for key in ROLE_PERMISSIONS:
            assert isinstance(key, UserRole), f"Non-canonical key in ROLE_PERMISSIONS: {key!r}"

    def test_exactly_eight_entries(self):
        assert len(ROLE_PERMISSIONS) == 8

    def test_no_legacy_label_keys(self):
        for key in ROLE_PERMISSIONS:
            assert key not in LEGACY_LABELS, f"Legacy label used as key: {key!r}"


# ---------------------------------------------------------------------------
# Group 8 – legacy-label allowlist scan
# ---------------------------------------------------------------------------
class TestLegacyLabelAllowlist:
    """Legacy display labels may appear ONLY in role_policy.py and migration 0013."""

    def _collect_py_files(self) -> list[Path]:
        # Scan only production application code; test files legitimately
        # contain legacy labels as test inputs to canonicalize_role().
        app_root = BACKEND_ROOT / "app"
        return list(app_root.rglob("*.py"))

    def test_no_legacy_labels_outside_allowlist(self):
        violations: list[str] = []
        allowed = {ROLE_POLICY_PATH.resolve(), MIGRATION_PATH.resolve()}
        for path in self._collect_py_files():
            if path.resolve() in allowed:
                continue
            src = path.read_text(encoding="utf-8")
            for label in LEGACY_LABELS:
                # Only flag string literals containing the label, not e.g. comments.
                # Simple heuristic: look for the label surrounded by quotes.
                pattern = re.compile(r"""['"']""" + re.escape(label) + r"""['"']""")
                for m in pattern.finditer(src):
                    lineno = src[: m.start()].count("\n") + 1
                    violations.append(f"{path.relative_to(BACKEND_ROOT)}:{lineno}: {label!r}")

        assert not violations, (
            "Legacy display labels found outside the allowlist:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# Group 9 – POST /auth/users cannot persist legacy role
# ---------------------------------------------------------------------------
class TestPostUserCannotPersistLegacyRole:
    def test_legacy_role_returns_422(self, client, auth_headers):
        r = client.post(
            "/api/v1/auth/users",
            json={
                "email": "legacy_role_test@example.com",
                "full_name": "Legacy Test",
                "password": "Password1!",
                "role": "Process Engineer",
            },
            headers=auth_headers,
        )
        # The endpoint must reject legacy label submission with HTTP 422.
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_canonical_role_accepted(self, client, auth_headers):
        r = client.post(
            "/api/v1/auth/users",
            json={
                "email": "canonical_role_test@example.com",
                "full_name": "Canonical Test",
                "password": "Password1!",
                "role": "PROCESS_ENGINEER",
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["role"] == "PROCESS_ENGINEER"

    def test_unknown_role_returns_422(self, client, auth_headers):
        r = client.post(
            "/api/v1/auth/users",
            json={
                "email": "unknown_role_test@example.com",
                "full_name": "Unknown Role",
                "password": "Password1!",
                "role": "Super User",
            },
            headers=auth_headers,
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Group 10 – migration pre-check ordering and NULL safety
# ---------------------------------------------------------------------------
class TestMigrationPrecheck:
    def _get_migration_src(self) -> str:
        return MIGRATION_PATH.read_text(encoding="utf-8")

    def test_down_revision_correct(self):
        src = self._get_migration_src()
        assert 'down_revision = "0012_ce04a_replace_turkish_defaults"' in src

    def test_pre_check_before_updates(self):
        """The pre-check SELECT must appear before any UPDATE statement in upgrade()."""
        src = self._get_migration_src()
        select_pos = src.find("SELECT COUNT(*)")
        update_pos = src.find("UPDATE users SET role")
        assert select_pos != -1, "Pre-check SELECT not found"
        assert update_pos != -1, "UPDATE not found"
        assert select_pos < update_pos, (
            f"Pre-check SELECT (pos {select_pos}) must precede first UPDATE (pos {update_pos})"
        )

    def test_null_guard_in_pre_check(self):
        src = self._get_migration_src()
        assert "role IS NULL" in src, "Pre-check must handle NULL roles"

    def test_eight_upgrade_updates(self):
        src = self._get_migration_src()
        # Count UPDATE statements inside the upgrade() function body
        upgrade_start = src.find("def upgrade()")
        downgrade_start = src.find("def downgrade()")
        upgrade_body = src[upgrade_start:downgrade_start]
        updates = upgrade_body.count("UPDATE users SET role")
        assert updates == 8, f"Expected 8 upgrade UPDATEs, found {updates}"

    def test_eight_downgrade_updates(self):
        src = self._get_migration_src()
        downgrade_start = src.find("def downgrade()")
        downgrade_body = src[downgrade_start:]
        updates = downgrade_body.count("UPDATE users SET role")
        assert updates == 8, f"Expected 8 downgrade UPDATEs, found {updates}"

    def test_exception_raised_on_invalid_rows(self):
        """upgrade() body must raise an Exception when pre-check finds bad rows."""
        src = self._get_migration_src()
        upgrade_start = src.find("def upgrade()")
        downgrade_start = src.find("def downgrade()")
        upgrade_body = src[upgrade_start:downgrade_start]
        assert "raise Exception" in upgrade_body, "upgrade() must raise on pre-check failure"
