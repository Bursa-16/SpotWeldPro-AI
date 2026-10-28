"""add weld_groups table

Revision ID: 0017_weld_groups
Revises: 0016_merge_heads
Create Date: 2026-10-28

NOTE: This migration file was generated as part of MASTER-ENERGY-OPTIMIZATION-01 P0.
It has NOT been executed against any database.
Running it is the operator's responsibility.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0017_weld_groups"
down_revision = "0016_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weld_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("part_id", sa.Integer(), nullable=True),
        sa.Column("assembly_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_weld_groups_id", "weld_groups", ["id"])
    op.create_index("ix_weld_groups_part_id", "weld_groups", ["part_id"])
    op.create_index("ix_weld_groups_assembly_id", "weld_groups", ["assembly_id"])


def downgrade() -> None:
    op.drop_index("ix_weld_groups_assembly_id", table_name="weld_groups")
    op.drop_index("ix_weld_groups_part_id", table_name="weld_groups")
    op.drop_index("ix_weld_groups_id", table_name="weld_groups")
    op.drop_table("weld_groups")
