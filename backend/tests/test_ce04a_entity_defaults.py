"""CE-04-A: Tests for English entity defaults and migration data sweep.

Covers:
- Project.status defaults to 'ACTIVE'
- WeldPoint.criticality defaults to 'STANDARD'
- WeldPoint.approval_status defaults to 'DRAFT'
- Migration upgrade SQL targets correct table/column/value pairs
- Migration downgrade SQL reverses every upgrade statement
- Migration revision chain is correctly wired
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

from app.models.entities import Project, WeldPoint

# ---------------------------------------------------------------------------
# Locate migration file once for all migration tests
# ---------------------------------------------------------------------------

_MIGRATION_FILE = (
    pathlib.Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "0012_ce04a_replace_turkish_defaults.py"
)


def _load_migration():
    """Load the digit-prefixed migration module via importlib."""
    spec = importlib.util.spec_from_file_location(
        "migration_0012_ce04a", _MIGRATION_FILE
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Model default tests (no DB required — inspect column defaults directly)
# ---------------------------------------------------------------------------

class TestProjectDefaults:
    def test_status_default_is_active(self) -> None:
        col = Project.__table__.c["status"]
        assert col.default.arg == "ACTIVE", (
            f"Project.status default must be 'ACTIVE', got {col.default.arg!r}"
        )

    def test_status_default_is_not_turkish(self) -> None:
        col = Project.__table__.c["status"]
        assert col.default.arg != "Aktif", (
            "Project.status default must not be the legacy Turkish value 'Aktif'"
        )


class TestWeldPointDefaults:
    def test_criticality_default_is_standard(self) -> None:
        col = WeldPoint.__table__.c["criticality"]
        assert col.default.arg == "STANDARD", (
            f"WeldPoint.criticality default must be 'STANDARD', got {col.default.arg!r}"
        )

    def test_criticality_default_is_not_turkish(self) -> None:
        col = WeldPoint.__table__.c["criticality"]
        assert col.default.arg != "Standart", (
            "WeldPoint.criticality default must not be the legacy Turkish value 'Standart'"
        )

    def test_approval_status_default_is_draft(self) -> None:
        col = WeldPoint.__table__.c["approval_status"]
        assert col.default.arg == "DRAFT", (
            f"WeldPoint.approval_status default must be 'DRAFT', got {col.default.arg!r}"
        )

    def test_approval_status_default_is_not_turkish(self) -> None:
        col = WeldPoint.__table__.c["approval_status"]
        assert col.default.arg != "Taslak", (
            "WeldPoint.approval_status default must not be the legacy Turkish value 'Taslak'"
        )


# ---------------------------------------------------------------------------
# Migration chain tests
# ---------------------------------------------------------------------------

class TestMigrationChain:
    """Verify revision identifiers are correctly wired."""

    @pytest.fixture(scope="class")
    def migration(self):
        assert _MIGRATION_FILE.exists(), f"Migration file not found: {_MIGRATION_FILE}"
        return _load_migration()

    def test_revision_id(self, migration) -> None:
        assert migration.revision == "0012_ce04a_replace_turkish_defaults"

    def test_down_revision(self, migration) -> None:
        assert migration.down_revision == "0011_engineering_library_foundation"

    def test_branch_labels_none(self, migration) -> None:
        assert migration.branch_labels is None

    def test_depends_on_none(self, migration) -> None:
        assert migration.depends_on is None


# ---------------------------------------------------------------------------
# Migration SQL content tests (source inspection — no DB runner required)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def migration_source() -> tuple[str, str]:
    """Return (upgrade_source, downgrade_source) as plain strings."""
    import inspect
    mod = _load_migration()
    return inspect.getsource(mod.upgrade), inspect.getsource(mod.downgrade)


class TestUpgradeSQL:
    def test_converts_aktif_to_active(self, migration_source) -> None:
        upgrade, _ = migration_source
        assert "Aktif" in upgrade
        assert "ACTIVE" in upgrade
        assert "projects" in upgrade

    def test_converts_standart_to_standard(self, migration_source) -> None:
        upgrade, _ = migration_source
        assert "Standart" in upgrade
        assert "STANDARD" in upgrade
        assert "weld_points" in upgrade

    def test_converts_taslak_to_draft(self, migration_source) -> None:
        upgrade, _ = migration_source
        assert "Taslak" in upgrade
        assert "DRAFT" in upgrade
        assert "weld_points" in upgrade

    def test_uses_where_clause_not_unconditional(self, migration_source) -> None:
        upgrade, _ = migration_source
        assert "WHERE" in upgrade.upper()


class TestDowngradeSQL:
    def test_reverses_active_to_aktif(self, migration_source) -> None:
        _, downgrade = migration_source
        assert "ACTIVE" in downgrade
        assert "Aktif" in downgrade

    def test_reverses_standard_to_standart(self, migration_source) -> None:
        _, downgrade = migration_source
        assert "STANDARD" in downgrade
        assert "Standart" in downgrade

    def test_reverses_draft_to_taslak(self, migration_source) -> None:
        _, downgrade = migration_source
        assert "DRAFT" in downgrade
        assert "Taslak" in downgrade

    def test_uses_where_clause_not_unconditional(self, migration_source) -> None:
        _, downgrade = migration_source
        assert "WHERE" in downgrade.upper()
