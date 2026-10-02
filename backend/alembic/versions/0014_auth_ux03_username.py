"""AUTH-UX-03: Add username column to users table (phased migration).

Revision ID: 0014_auth_ux03_username
Revises: 0013_ce04b_canonical_role_codes
Create Date: 2026-09-29

Phase A  — Add username as nullable (no unique constraint yet).
Phase B  — Backfill each row deterministically from the email local-part.
           Canonical form: stripped + lowercase (matches canonicalize_username).
Phase C  — Collision resolution: ali, ali-2, ali-3 … (ORDER BY id — oldest row wins).
Phase D  — Assert: NULL count == 0, duplicate count == 0.
Phase E  — Create unique index on username.
Phase F  — Alter column to NOT NULL (via batch_alter_table for SQLite compat).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text


revision = "0014_auth_ux03_username"
down_revision = "0013_ce04b_canonical_role_codes"
branch_labels = None
depends_on = None


def _email_local_part(email: str) -> str:
    """Return the lowercase local-part of an email address."""
    local = email.split("@")[0]
    return local.strip().lower()


def _next_slug(used: set[str], base: str) -> str:
    """Return base if unused, else base-2, base-3, … (deterministic, no gaps)."""
    if base not in used:
        return base
    i = 2
    while f"{base}-{i}" in used:
        i += 1
    return f"{base}-{i}"


def upgrade() -> None:
    conn = op.get_bind()

    # ──────────────────────────────────────────────────────────────────────────
    # Phase A — add nullable username column (no unique constraint yet)
    # ──────────────────────────────────────────────────────────────────────────
    op.add_column("users", sa.Column("username", sa.String(100), nullable=True))

    # ──────────────────────────────────────────────────────────────────────────
    # Phase B + C — backfill with deterministic collision resolution
    # Rows are processed in id order so the earliest row wins the base slug.
    # ──────────────────────────────────────────────────────────────────────────
    rows = conn.execute(text("SELECT id, email FROM users ORDER BY id")).fetchall()
    used_usernames: set[str] = set()
    for row_id, email in rows:
        base = _email_local_part(email)
        slug = _next_slug(used_usernames, base)
        used_usernames.add(slug)
        conn.execute(
            text("UPDATE users SET username = :u WHERE id = :id"),
            {"u": slug, "id": row_id},
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Phase D — integrity assertions (fail migration if violated)
    # ──────────────────────────────────────────────────────────────────────────
    null_count = conn.execute(
        text("SELECT COUNT(*) FROM users WHERE username IS NULL")
    ).scalar()
    if null_count:
        raise RuntimeError(
            f"0014 migration assertion failed: {null_count} row(s) still have "
            f"NULL username after backfill."
        )

    # COUNT(*) - COUNT(DISTINCT username) > 0  ⟺  there are duplicates
    dup_count = conn.execute(
        text("SELECT COUNT(*) - COUNT(DISTINCT username) FROM users")
    ).scalar()
    if dup_count:
        raise RuntimeError(
            f"0014 migration assertion failed: {dup_count} duplicate username(s) "
            f"detected after backfill. Inspect the users table before retrying."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Phase E — unique index on username
    # ──────────────────────────────────────────────────────────────────────────
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Phase F — make column NOT NULL
    # batch_alter_table is required for SQLite; PostgreSQL handles it normally.
    # ──────────────────────────────────────────────────────────────────────────
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("username", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_username")
        batch_op.drop_column("username")
