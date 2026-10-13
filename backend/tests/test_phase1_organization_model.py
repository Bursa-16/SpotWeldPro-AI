"""Phase 1 regression suite — Organization and Reference Profile foundation.

Tests T01–T11: model and migration correctness.

Migration tests (T10, T11) use explicit revision IDs, NOT 'head', to avoid
the pre-existing multi-head anomaly in the migration chain (0012 branch).

The pre-existing multi-head anomaly in test_migrations.py is documented and
intentionally NOT fixed here (HR-15: NO SILENT REPAIR).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command

import app.models  # noqa: F401 — registers all new tables with Base.metadata
from app.db.session import Base
from app.models.entities import User
from app.models.enums import OrgRole, ProfileApprovalEventType, ProfileStatus
from app.models.error_codes import ApiErrorCode, ResourceType
from app.models.profile_entities import (
    Organization,
    OrganizationMember,
    ProfileApprovalEvent,
    ReferenceProfileDocument,
    ReferenceProfileRecord,
    SYSTEM_ORG_SLUG,
)

BACKEND_ROOT = Path(__file__).parents[1]

PHASE1_TABLES = {
    "organizations",
    "org_members",
    "ref_profile_documents",
    "reference_profiles",
    "profile_approval_events",
}


# ─────────────────────────────────────────────────────────────────────────────
# Migration helpers (mirrors test_migrations.py convention)
# ─────────────────────────────────────────────────────────────────────────────

def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def _run_upgrade(monkeypatch, database_url: str, revision: str) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(_alembic_config(), revision)


def _run_downgrade(monkeypatch, database_url: str, revision: str) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.downgrade(_alembic_config(), revision)


@contextmanager
def _sqlite_engine(database_url: str):
    eng = create_engine(database_url)

    @event.listens_for(eng, "connect")
    def enable_fk(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    try:
        yield eng
    finally:
        eng.dispose()


# NOTE: We do NOT override the `database` fixture here. The conftest session
# fixture (Base.metadata.create_all) must run so that T07–T09 can use ORM tables.
# T10/T11 migration tests use isolated temp DBs and are unaffected by this.

@pytest.fixture()
def migration_database_dir():
    with TemporaryDirectory(prefix="phase1-migration-") as path:
        yield Path(path)


# ─────────────────────────────────────────────────────────────────────────────
# T01 — Enum completeness: OrgRole
# ─────────────────────────────────────────────────────────────────────────────

def test_T01_org_role_enum_values() -> None:
    assert set(OrgRole) == {
        OrgRole.ORG_ADMIN,
        OrgRole.APPROVER,
        OrgRole.ENGINEER,
        OrgRole.VIEWER,
    }


# ─────────────────────────────────────────────────────────────────────────────
# T02 — Enum completeness: ProfileStatus
# ─────────────────────────────────────────────────────────────────────────────

def test_T02_profile_status_enum_values() -> None:
    assert set(ProfileStatus) == {
        ProfileStatus.DRAFT,
        ProfileStatus.REVIEW_REQUIRED,
        ProfileStatus.VALIDATED,
        ProfileStatus.APPROVED,
        ProfileStatus.ACTIVE,
        ProfileStatus.SUPERSEDED,
        ProfileStatus.REVOKED,
    }


# ─────────────────────────────────────────────────────────────────────────────
# T03 — Enum completeness: ProfileApprovalEventType
# ─────────────────────────────────────────────────────────────────────────────

def test_T03_profile_approval_event_type_enum_values() -> None:
    assert ProfileApprovalEventType.CREATED == "CREATED"
    assert ProfileApprovalEventType.APPROVED == "APPROVED"
    assert ProfileApprovalEventType.REVOKED == "REVOKED"


# ─────────────────────────────────────────────────────────────────────────────
# T04 — New error codes present in ApiErrorCode
# ─────────────────────────────────────────────────────────────────────────────

def test_T04_new_api_error_codes_present() -> None:
    assert ApiErrorCode.PROFILE_NOT_APPROVED == "PROFILE_NOT_APPROVED"
    assert ApiErrorCode.PROFILE_DEPRECATED == "PROFILE_DEPRECATED"
    assert ApiErrorCode.PROFILE_ORG_MISMATCH == "PROFILE_ORG_MISMATCH"
    assert ApiErrorCode.IMMUTABLE_SYSTEM_PROFILE == "IMMUTABLE_SYSTEM_PROFILE"
    assert ApiErrorCode.SAME_USER_REVIEWER_APPROVER == "SAME_USER_REVIEWER_APPROVER"
    assert ApiErrorCode.ORG_MEMBERSHIP_REQUIRED == "ORG_MEMBERSHIP_REQUIRED"


# ─────────────────────────────────────────────────────────────────────────────
# T05 — New resource types present in ResourceType
# ─────────────────────────────────────────────────────────────────────────────

def test_T05_new_resource_types_present() -> None:
    assert ResourceType.ORGANIZATION == "ORGANIZATION"
    assert ResourceType.PROFILE == "PROFILE"
    assert ResourceType.PROFILE_DOCUMENT == "PROFILE_DOCUMENT"


# ─────────────────────────────────────────────────────────────────────────────
# T06 — Base.metadata registers all five Phase 1 tables
# ─────────────────────────────────────────────────────────────────────────────

def test_T06_phase1_tables_registered_in_metadata() -> None:
    registered = set(Base.metadata.tables.keys())
    assert PHASE1_TABLES <= registered, (
        f"Missing from Base.metadata: {PHASE1_TABLES - registered}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T07 — Organization CRUD and unique slug constraint (ORM level)
# ─────────────────────────────────────────────────────────────────────────────

def test_T07_organization_unique_slug_constraint(db_session: Session) -> None:
    now = datetime.now(timezone.utc)
    org = Organization(
        slug="test-org-t07",
        display_name="Test Org T07",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.commit()

    duplicate = Organization(
        slug="test-org-t07",
        display_name="Duplicate",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# T08 — OrganizationMember unique (org_id, user_id) constraint
# ─────────────────────────────────────────────────────────────────────────────

def test_T08_org_member_unique_constraint(db_session: Session) -> None:
    now = datetime.now(timezone.utc)
    org = Organization(
        slug="test-org-t08",
        display_name="Test Org T08",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.flush()

    user = db_session.query(User).filter(User.username == "admin").first()
    assert user is not None, "conftest admin user must exist"

    m1 = OrganizationMember(
        org_id=org.id,
        user_id=user.id,
        org_role=OrgRole.ENGINEER,
        is_active=True,
        created_at=now,
    )
    db_session.add(m1)
    db_session.flush()

    m2 = OrganizationMember(
        org_id=org.id,
        user_id=user.id,
        org_role=OrgRole.VIEWER,
        is_active=True,
        created_at=now,
    )
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# T09 — ProfileApprovalEvent is immutable (protect_immutable_model enforced)
# ─────────────────────────────────────────────────────────────────────────────

def test_T09_profile_approval_event_is_immutable(db_session: Session) -> None:
    from app.models.governance import ImmutableRecordError

    now = datetime.now(timezone.utc)
    user = db_session.query(User).filter(User.username == "admin").first()
    assert user is not None

    # Create an organization (with null org_id on profile = system default)
    org = Organization(
        slug="sys-t09",
        display_name="System T09",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.flush()

    profile = ReferenceProfileRecord(
        profile_code="TEST_T09",
        version=1,
        org_id=None,
        display_name="T09 Profile",
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
    db_session.add(profile)
    db_session.flush()

    evt = ProfileApprovalEvent(
        profile_id=profile.id,
        event_type=ProfileApprovalEventType.CREATED,
        actor_user_id=user.id,
        event_at=now,
        note="initial",
    )
    db_session.add(evt)
    db_session.flush()

    # Attempting to UPDATE the event must raise ImmutableRecordError
    with pytest.raises(ImmutableRecordError):
        evt.note = "tampered"
        db_session.flush()

    db_session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# T10 — Migration round-trip: upgrade 0014 → 0015, verify tables, downgrade
# ─────────────────────────────────────────────────────────────────────────────

def test_T10_migration_0015_upgrade_creates_phase1_tables(
    monkeypatch, migration_database_dir: Path
) -> None:
    db_path = migration_database_dir / "t10.db"
    url = f"sqlite:///{db_path.as_posix()}"

    # Upgrade to the pre-Phase-1 HEAD of the main chain
    _run_upgrade(monkeypatch, url, "0014_auth_ux03_username")

    with _sqlite_engine(url) as eng:
        inspector = inspect(eng)
        pre_tables = set(inspector.get_table_names())
        for t in PHASE1_TABLES:
            assert t not in pre_tables, f"Table {t!r} should NOT exist before 0015"

    # Apply Phase 1
    _run_upgrade(monkeypatch, url, "0015_organization_and_profile_tables")

    with _sqlite_engine(url) as eng:
        inspector = inspect(eng)
        post_tables = set(inspector.get_table_names())
        for t in PHASE1_TABLES:
            assert t in post_tables, f"Table {t!r} should exist after 0015"

        # Verify system org was seeded
        with Session(eng) as session:
            result = session.execute(
                text("SELECT slug FROM organizations WHERE slug = 'system'")
            ).fetchall()
            assert len(result) == 1, "System organization must be seeded by 0015"

        # Verify alembic_version includes 0015
        with Session(eng) as session:
            versions = {
                row[0]
                for row in session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchall()
            }
        assert "0015_organization_and_profile_tables" in versions


# ─────────────────────────────────────────────────────────────────────────────
# T11 — Migration downgrade: 0015 → 0014 removes Phase 1 tables
# ─────────────────────────────────────────────────────────────────────────────

def test_T11_migration_0015_downgrade_removes_phase1_tables(
    monkeypatch, migration_database_dir: Path
) -> None:
    db_path = migration_database_dir / "t11.db"
    url = f"sqlite:///{db_path.as_posix()}"

    _run_upgrade(monkeypatch, url, "0015_organization_and_profile_tables")
    _run_downgrade(monkeypatch, url, "0014_auth_ux03_username")

    with _sqlite_engine(url) as eng:
        inspector = inspect(eng)
        remaining = set(inspector.get_table_names())
        for t in PHASE1_TABLES:
            assert t not in remaining, f"Table {t!r} should NOT exist after downgrade"

        # Verify alembic_version reverted to 0014
        with Session(eng) as session:
            versions = {
                row[0]
                for row in session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchall()
            }
        assert "0014_auth_ux03_username" in versions
        assert "0015_organization_and_profile_tables" not in versions


# ─────────────────────────────────────────────────────────────────────────────
# T12 — down_revision chain: 0015 follows 0014 (not head, not 0012_electrode)
# ─────────────────────────────────────────────────────────────────────────────

def test_T12_migration_0015_has_correct_down_revision() -> None:
    """Verify the down_revision constant at module level (static check)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "migration_0015",
        BACKEND_ROOT / "alembic" / "versions" / "0015_organization_and_profile_tables.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.down_revision == "0014_auth_ux03_username"
    assert mod.revision == "0015_organization_and_profile_tables"
    assert mod.branch_labels is None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers for ORM tests (session-scoped DB from conftest.py)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_session():
    """Short-lived Session that rolls back after each test to keep tests isolated."""
    from app.db.session import SessionLocal
    with SessionLocal() as session:
        yield session
        session.rollback()
