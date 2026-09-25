"""CE-04-B: Canonicalise role display labels to stable role codes.

Revision ID: 0013_ce04b_canonical_role_codes
Revises: 0012_ce04a_replace_turkish_defaults
Create Date: 2026-09-25
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "0013_ce04b_canonical_role_codes"
down_revision = "0012_ce04a_replace_turkish_defaults"
branch_labels = None
depends_on = None

# The 8 known legacy display labels that are valid pre-migration values.
_KNOWN_LEGACY = (
    "System Admin",
    "Process Engineer",
    "Quality Engineer",
    "Manufacturing Engineer",
    "Maintenance",
    "Operator",
    "Read Only",
    "Customer",
)

# Placeholders for the IN clause (:v0 … :v7)
_PLACEHOLDERS = ", ".join(f":v{i}" for i in range(len(_KNOWN_LEGACY)))


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # PRE-CHECK: fail fast if any row has NULL or an unrecognised role.
    # NOT IN does not match NULL rows, so we check IS NULL separately.
    # ------------------------------------------------------------------
    params = {f"v{i}": v for i, v in enumerate(_KNOWN_LEGACY)}
    bad_rows = conn.execute(
        text(
            f"SELECT COUNT(*) FROM users "
            f"WHERE role IS NULL OR role NOT IN ({_PLACEHOLDERS})"
        ),
        params,
    ).scalar()

    if bad_rows:
        raise Exception(
            f"CE-04-B migration pre-check failed: {bad_rows} row(s) in the users "
            f"table have a NULL or unrecognised role value. "
            f"Resolve those rows before running this migration."
        )

    # ------------------------------------------------------------------
    # UPDATE: legacy display label → canonical code (WHERE-guarded).
    # ------------------------------------------------------------------
    conn.execute(text("UPDATE users SET role = 'SYSTEM_ADMIN'           WHERE role = 'System Admin'"))
    conn.execute(text("UPDATE users SET role = 'PROCESS_ENGINEER'       WHERE role = 'Process Engineer'"))
    conn.execute(text("UPDATE users SET role = 'QUALITY_ENGINEER'       WHERE role = 'Quality Engineer'"))
    conn.execute(text("UPDATE users SET role = 'MANUFACTURING_ENGINEER' WHERE role = 'Manufacturing Engineer'"))
    conn.execute(text("UPDATE users SET role = 'MAINTENANCE'            WHERE role = 'Maintenance'"))
    conn.execute(text("UPDATE users SET role = 'OPERATOR'               WHERE role = 'Operator'"))
    conn.execute(text("UPDATE users SET role = 'READ_ONLY'              WHERE role = 'Read Only'"))
    conn.execute(text("UPDATE users SET role = 'CUSTOMER'               WHERE role = 'Customer'"))


def downgrade() -> None:
    conn = op.get_bind()

    # Deterministic 8 reverse UPDATEs (WHERE-guarded).
    conn.execute(text("UPDATE users SET role = 'System Admin'           WHERE role = 'SYSTEM_ADMIN'"))
    conn.execute(text("UPDATE users SET role = 'Process Engineer'       WHERE role = 'PROCESS_ENGINEER'"))
    conn.execute(text("UPDATE users SET role = 'Quality Engineer'       WHERE role = 'QUALITY_ENGINEER'"))
    conn.execute(text("UPDATE users SET role = 'Manufacturing Engineer' WHERE role = 'MANUFACTURING_ENGINEER'"))
    conn.execute(text("UPDATE users SET role = 'Maintenance'            WHERE role = 'MAINTENANCE'"))
    conn.execute(text("UPDATE users SET role = 'Operator'               WHERE role = 'OPERATOR'"))
    conn.execute(text("UPDATE users SET role = 'Read Only'              WHERE role = 'READ_ONLY'"))
    conn.execute(text("UPDATE users SET role = 'Customer'               WHERE role = 'CUSTOMER'"))
