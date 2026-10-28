"""add import_batches table

Revision ID: 0019_import_batches
Revises: 0018_weld_point_energy_fields
Create Date: 2026-10-28

NOTE: This migration file was generated as part of MASTER-ENERGY-OPTIMIZATION-01 P0.
It has NOT been executed against any database.
Running it is the operator's responsibility.

Purpose: tracks bulk XLSX/CSV import sessions with formula-injection status.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0019_import_batches"
down_revision = "0018_weld_point_energy_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("file_hash_sha256", sa.String(length=64), nullable=True),
        sa.Column("rows_accepted", sa.Integer(), nullable=True),
        sa.Column("rows_rejected", sa.Integer(), nullable=True),
        sa.Column("formula_injection_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("formula_injection_cells", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("imported_by_user_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_batches_id", "import_batches", ["id"])
    op.create_index("ix_import_batches_status", "import_batches", ["status"])
    op.create_index("ix_import_batches_project_id", "import_batches", ["project_id"])
    op.create_index("ix_import_batches_imported_by_user_id", "import_batches", ["imported_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_import_batches_imported_by_user_id", table_name="import_batches")
    op.drop_index("ix_import_batches_project_id", table_name="import_batches")
    op.drop_index("ix_import_batches_status", table_name="import_batches")
    op.drop_index("ix_import_batches_id", table_name="import_batches")
    op.drop_table("import_batches")
