"""PostgreSQL integration tests for the Engineering Library — CE-02C.

Uses the ``postgresql_engine`` fixture supplied by
``tests_postgresql/conftest.py``.  That fixture:
  - requires ``POSTGRES_TEST_DATABASE_URL`` (raises RuntimeError at collection
    if missing — no module-level skipif here);
  - creates an isolated schema;
  - runs ``alembic upgrade head`` before yielding the engine.

Tests verify database-level constraints (UNIQUE, FK, CHECK) that only the
real PostgreSQL dialect enforces.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_user(session: Session, email: str) -> int:
    result = session.execute(
        text(
            "INSERT INTO users (email, full_name, password_hash, role) "
            "VALUES (:email, 'Test User', 'x', 'Engineer') RETURNING id"
        ),
        {"email": email},
    )
    return result.scalar_one()


def _insert_material_identity(session: Session, material_id: str, user_id: int) -> int:
    result = session.execute(
        text(
            "INSERT INTO engineering_materials "
            "(material_id, created_by_user_id) "
            "VALUES (:material_id, :uid) RETURNING id"
        ),
        {"material_id": material_id, "uid": user_id},
    )
    return result.scalar_one()


def _insert_material_revision(
    session: Session,
    identity_pk: int,
    revision_number: int,
    user_id: int,
    lifecycle_status: str = "ACTIVE",
) -> int:
    result = session.execute(
        text(
            "INSERT INTO engineering_material_revisions "
            "(engineering_material_id, revision_number, name, specification, "
            " material_type, content_hash, software_version, schema_version, "
            " canonicalization_version, hash_algorithm, "
            " lifecycle_status, source_class, actor_id, reason) "
            "VALUES "
            "(:eid, :rev, 'Steel', 'ASTM A36', 'STEEL', 'abc123', "
            " 'CE-02C', '1', '1', 'sha256', "
            " :status, 'MEASURED', :actor, 'initial') "
            "RETURNING id"
        ),
        {
            "eid": identity_pk,
            "rev": revision_number,
            "status": lifecycle_status,
            "actor": f"user:{user_id}",
        },
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMaterialUniqueConstraints:
    """UNIQUE constraints on the material identity table."""

    def test_duplicate_material_id_raises(self, postgresql_engine):
        """Two identities with the same material_id violate the UNIQUE index."""
        with Session(postgresql_engine) as session:
            user_id = _insert_user(session, "pg_dup_mat@example.com")
            _insert_material_identity(session, "MAT-PG-DUP-001", user_id)
            session.flush()

            with pytest.raises(IntegrityError):
                _insert_material_identity(session, "MAT-PG-DUP-001", user_id)
                session.flush()

            session.rollback()


class TestMaterialRevisionUniqueConstraints:
    """UNIQUE constraints on the material revision table."""

    def test_duplicate_revision_number_raises(self, postgresql_engine):
        """Two revisions with the same (identity, revision_number) violate UNIQUE."""
        with Session(postgresql_engine) as session:
            user_id = _insert_user(session, "pg_dup_rev@example.com")
            identity_pk = _insert_material_identity(session, "MAT-PG-DUPREV-001", user_id)
            session.flush()

            _insert_material_revision(session, identity_pk, 1, user_id)
            session.flush()

            with pytest.raises(IntegrityError):
                _insert_material_revision(session, identity_pk, 1, user_id)
                session.flush()

            session.rollback()


class TestMaterialRevisionForeignKey:
    """FK constraints on the material revision table."""

    def test_nonexistent_identity_fk_raises(self, postgresql_engine):
        """Revision referencing a non-existent engineering_material_id raises."""
        with Session(postgresql_engine) as session:
            user_id = _insert_user(session, "pg_fk_mat@example.com")
            session.flush()

            with pytest.raises(IntegrityError):
                _insert_material_revision(session, 999_999_999, 1, user_id)
                session.flush()

            session.rollback()


class TestMaterialRevisionLifecycleCheckConstraint:
    """CHECK constraint on lifecycle_status column."""

    def test_invalid_lifecycle_status_raises(self, postgresql_engine):
        """An unrecognised lifecycle_status value violates the CHECK constraint."""
        with Session(postgresql_engine) as session:
            user_id = _insert_user(session, "pg_check_lc@example.com")
            identity_pk = _insert_material_identity(session, "MAT-PG-CHECK-001", user_id)
            session.flush()

            with pytest.raises(IntegrityError):
                _insert_material_revision(
                    session, identity_pk, 1, user_id,
                    lifecycle_status="INVALID_STATUS",
                )
                session.flush()

            session.rollback()


class TestCoatingUniqueConstraint:
    """Spot-check UNIQUE constraint on the coating identity table."""

    def test_duplicate_coating_id_raises(self, postgresql_engine):
        """Two identities with the same coating_id violate the UNIQUE index."""
        with Session(postgresql_engine) as session:
            user_id = _insert_user(session, "pg_dup_coat@example.com")
            session.execute(
                text(
                    "INSERT INTO engineering_coatings "
                    "(coating_id, created_by_user_id) "
                    "VALUES (:cid, :uid)"
                ),
                {"cid": "COAT-PG-DUP-001", "uid": user_id},
            )
            session.flush()

            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "INSERT INTO engineering_coatings "
                        "(coating_id, created_by_user_id) "
                        "VALUES (:cid, :uid)"
                    ),
                    {"cid": "COAT-PG-DUP-001", "uid": user_id},
                )
                session.flush()

            session.rollback()
