"""merge divergent heads: electrode-weldschedule branch + org-profile branch

Revision ID: 0016_merge_heads
Revises: 0012_electrode_weldgun_weldschedule_persistence, 0015_organization_and_profile_tables
Create Date: 2026-10-12
"""

from __future__ import annotations

from alembic import op

revision = "0016_merge_heads"
down_revision = (
    "0012_electrode_weldgun_weldschedule_persistence",
    "0015_organization_and_profile_tables",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
