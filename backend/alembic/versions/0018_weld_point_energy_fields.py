"""add energy indicator columns to weld_points

Revision ID: 0018_weld_point_energy_fields
Revises: 0017_weld_groups
Create Date: 2026-10-28

NOTE: This migration file was generated as part of MASTER-ENERGY-OPTIMIZATION-01 P0.
It has NOT been executed against any database.
All new columns are nullable; no existing data is altered.
Running it is the operator's responsibility.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0018_weld_point_energy_fields"
down_revision = "0017_weld_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Foreign key to weld_groups (nullable; existing rows unaffected)
    op.add_column("weld_points", sa.Column("weld_group_id", sa.Integer(), nullable=True))
    op.create_index("ix_weld_points_weld_group_id", "weld_points", ["weld_group_id"])

    # Energy indicator A: E_min
    op.add_column("weld_points", sa.Column("e_min_kj", sa.Float(), nullable=True))

    # Energy indicator B: E_ideal
    op.add_column("weld_points", sa.Column("e_ideal_kj", sa.Float(), nullable=True))

    # Energy indicator C: E_max
    op.add_column("weld_points", sa.Column("e_max_kj", sa.Float(), nullable=True))

    # Energy indicator D: E_current (company measured)
    op.add_column("weld_points", sa.Column("e_current_kj", sa.Float(), nullable=True))

    # Raw computed energy in J (from I²Rt; preserved for audit)
    op.add_column("weld_points", sa.Column("e_computed_j", sa.Float(), nullable=True))

    # Method enum string: I2RT | WAVEFORM | USER_ENTERED
    op.add_column("weld_points", sa.Column("energy_method", sa.String(length=32), nullable=True))

    # Process-window status string: NOT_ESTABLISHED | IN_WINDOW | BELOW_MIN | ABOVE_MAX | E_CURRENT_ABSENT
    op.add_column("weld_points", sa.Column("energy_window_status", sa.String(length=32), nullable=True))

    # Annual production volume for cost aggregation
    op.add_column("weld_points", sa.Column("production_volume_annual", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("weld_points", "production_volume_annual")
    op.drop_column("weld_points", "energy_window_status")
    op.drop_column("weld_points", "energy_method")
    op.drop_column("weld_points", "e_computed_j")
    op.drop_column("weld_points", "e_current_kj")
    op.drop_column("weld_points", "e_max_kj")
    op.drop_column("weld_points", "e_ideal_kj")
    op.drop_column("weld_points", "e_min_kj")
    op.drop_index("ix_weld_points_weld_group_id", table_name="weld_points")
    op.drop_column("weld_points", "weld_group_id")
