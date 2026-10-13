"""Phase 1: Organization, membership and reference profile tables.

Revision ID: 0015_organization_and_profile_tables
Revises: 0014_auth_ux03_username
Create Date: 2026-10-12

Additive migration only:
  - No existing table is altered or dropped.
  - No existing row is modified or deleted.
  - Existing projects, weld_points, and users are NOT assigned to any org.

New tables (created in FK dependency order):
  1. organizations
  2. org_members
  3. ref_profile_documents
  4. reference_profiles
  5. profile_approval_events

Seed (in upgrade only):
  - One system organization row (slug='system') is inserted.
    This row is required so the seed_default_profile.py script can
    create the Default profile with a valid FK to organizations.id.

Downgrade:
  - Drops tables in reverse FK order.
  - System org row is removed as part of dropping the organizations table.
  - LIMITATION: if any organization data was created between upgrade and
    downgrade, it will be permanently lost. This is expected behaviour for
    a rollback; no production DB is targeted by this migration.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0015_organization_and_profile_tables"
down_revision = "0014_auth_ux03_username"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────────
    # 1. organizations
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. org_members
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "org_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "org_id", sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("org_role", sa.String(40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "granted_by", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_members_org_user"),
    )
    op.create_index("ix_org_members_org_id", "org_members", ["org_id"])
    op.create_index("ix_org_members_user_id", "org_members", ["user_id"])

    # ─────────────────────────────────────────────────────────────────────────
    # 3. ref_profile_documents
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "ref_profile_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "org_id", sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("upload_id", sa.String(80), nullable=False),
        sa.Column("filename_original", sa.String(300), nullable=False),
        sa.Column("file_format", sa.String(10), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column(
            "uploaded_by", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extraction_status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("extraction_result", sa.JSON(), nullable=True),
        sa.UniqueConstraint("upload_id", name="uq_ref_profile_documents_upload_id"),
    )
    op.create_index("ix_ref_profile_documents_org_id", "ref_profile_documents", ["org_id"])
    op.create_index("ix_ref_profile_documents_upload_id", "ref_profile_documents", ["upload_id"], unique=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. reference_profiles
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "reference_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_code", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "org_id", sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("material_scope", sa.String(200), nullable=False),
        sa.Column("stack_count", sa.String(10), nullable=False),
        sa.Column("cycle_basis_hz", sa.Integer(), nullable=False),
        sa.Column("t_min_mm", sa.Float(), nullable=False),
        sa.Column("t_max_mm", sa.Float(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("is_system_default", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("parameter_bands", sa.JSON(), nullable=False),
        sa.Column("nugget_criterion", sa.JSON(), nullable=False),
        sa.Column("source_provenance", sa.JSON(), nullable=False),
        sa.Column(
            "source_document_id", sa.Integer(),
            sa.ForeignKey("ref_profile_documents.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "created_by", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "approver_user_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "profile_code", "version",
            name="uq_reference_profiles_code_version",
        ),
    )
    op.create_index("ix_reference_profiles_profile_code", "reference_profiles", ["profile_code"])
    op.create_index("ix_reference_profiles_org_id", "reference_profiles", ["org_id"])
    op.create_index("ix_reference_profiles_status", "reference_profiles", ["status"])
    op.create_index("ix_reference_profiles_is_system_default", "reference_profiles", ["is_system_default"])

    # ─────────────────────────────────────────────────────────────────────────
    # 5. profile_approval_events
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "profile_approval_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id", sa.Integer(),
            sa.ForeignKey("reference_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column(
            "actor_user_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("field_confirmations", sa.JSON(), nullable=True),
    )
    op.create_index("ix_profile_approval_events_profile_id", "profile_approval_events", ["profile_id"])

    # ─────────────────────────────────────────────────────────────────────────
    # Seed: system organization (required for Default profile FK integrity)
    # ─────────────────────────────────────────────────────────────────────────
    conn = op.get_bind()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        text(
            "INSERT INTO organizations (slug, display_name, is_active, created_at, updated_at) "
            "VALUES (:slug, :name, :active, :now, :now)"
        ),
        {"slug": "system", "name": "SpotWeldPro AI System", "active": 1, "now": now},
    )


def downgrade() -> None:
    # Drop in reverse FK dependency order.
    # LIMITATION: all organization data since upgrade will be permanently lost.
    op.drop_table("profile_approval_events")
    op.drop_table("reference_profiles")
    op.drop_table("ref_profile_documents")
    op.drop_table("org_members")
    op.drop_table("organizations")
