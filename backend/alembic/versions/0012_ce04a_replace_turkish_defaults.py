"""CE-04-A: replace Turkish column defaults with stable English codes

Revision ID: 0012_ce04a_replace_turkish_defaults
Revises: 0011_engineering_library_foundation
Create Date: 2026-09-25

Data changes:
  projects.status:          'Aktif'    -> 'ACTIVE'
  weld_points.criticality:  'Standart' -> 'STANDARD'
  weld_points.approval_status: 'Taslak' -> 'DRAFT'

These three columns use Python-side SQLAlchemy defaults only (no server_default
in the original DDL), so no ALTER COLUMN DEFAULT is required.  The migration
performs a safe data sweep and documents the code substitution; downgrade
reverses the data sweep.

Engineering calculations, domain contracts, governed library tables, content
hashes, and RBAC logic are untouched.
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0012_ce04a_replace_turkish_defaults"
down_revision = "0011_engineering_library_foundation"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    conn = op.get_bind()

    # projects.status: 'Aktif' -> 'ACTIVE'
    conn.execute(
        text("UPDATE projects SET status = 'ACTIVE' WHERE status = 'Aktif'")
    )

    # weld_points.criticality: 'Standart' -> 'STANDARD'
    conn.execute(
        text("UPDATE weld_points SET criticality = 'STANDARD' WHERE criticality = 'Standart'")
    )

    # weld_points.approval_status: 'Taslak' -> 'DRAFT'
    conn.execute(
        text("UPDATE weld_points SET approval_status = 'DRAFT' WHERE approval_status = 'Taslak'")
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    conn = op.get_bind()

    # weld_points.approval_status: 'DRAFT' -> 'Taslak'
    # NOTE: rows that were already 'DRAFT' before the upgrade are not
    # distinguishable from rows changed by upgrade.  Downgrade restores
    # ALL 'DRAFT' rows to 'Taslak', which is the original default.
    conn.execute(
        text("UPDATE weld_points SET approval_status = 'Taslak' WHERE approval_status = 'DRAFT'")
    )

    # weld_points.criticality: 'STANDARD' -> 'Standart'
    conn.execute(
        text("UPDATE weld_points SET criticality = 'Standart' WHERE criticality = 'STANDARD'")
    )

    # projects.status: 'ACTIVE' -> 'Aktif'
    conn.execute(
        text("UPDATE projects SET status = 'Aktif' WHERE status = 'ACTIVE'")
    )
