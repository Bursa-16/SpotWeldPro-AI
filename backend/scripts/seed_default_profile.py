"""Idempotent seeder: system organization + SWP_DEFAULT v1 reference profile.

Run after alembic upgrade 0015_organization_and_profile_tables.

The Default profile parameter_bands are read directly from the REF_BANDS
constant in reference_profile.py — that constant is the single authoritative
source of truth for the engineering parameter ranges.

Usage:
    cd backend
    python scripts/seed_default_profile.py

Environment variable DATABASE_URL is read if set; otherwise the default
dev SQLite path is used.

Idempotency:
    - System org is created only if slug='system' does not already exist.
    - Default profile v1 is created only if (profile_code='SWP_DEFAULT', version=1)
      does not already exist.
    - Safe to re-run at any time.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the backend package is importable when run as a script.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.reference_profile import REF_BANDS
from app.models.entities import User
from app.models.profile_entities import (
    Organization,
    ReferenceProfileRecord,
    SYSTEM_ORG_SLUG,
)

_DEFAULT_DB = str(_BACKEND_DIR / "spot_welding.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_DEFAULT_DB}")

PROFILE_CODE = "SWP_DEFAULT"
PROFILE_VERSION = 1


def _build_nugget_criterion() -> dict:
    return {
        "method": "d5_formula",
        "formula": "d5 = 5 * sqrt(t_min_mm)",
        "unit": "mm",
        "approval_status": "ENGINEERING_APPROVAL_PENDING",
        "note": "Verify against customer weld spec before production use.",
    }


def _build_source_provenance() -> dict:
    return {
        "basis": "AWS_D8.1M_2013",
        "excel_sha256": "PENDING_VERIFICATION",
        "blocker": "B01",
        "note": (
            "REF_BANDS sourced from internal reference; "
            "pending cross-check against PuntaKaynak_CheckList_Rev03_22062017(2).xlsx"
        ),
        "approval_status": "ENGINEERING_APPROVAL_PENDING",
    }


def _get_or_create_system_org(session: Session) -> Organization:
    org = session.scalar(
        select(Organization).where(Organization.slug == SYSTEM_ORG_SLUG)
    )
    if org is None:
        now = datetime.now(timezone.utc)
        org = Organization(
            slug=SYSTEM_ORG_SLUG,
            display_name="SpotWeldPro AI System",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(org)
        session.flush()
        print(f"[seed] Created system organization (id={org.id})")
    else:
        print(f"[seed] System organization already exists (id={org.id})")
    return org


def _get_system_actor(session: Session) -> User:
    """Return the first SYSTEM_ADMIN user, or any user, as the profile creator."""
    user = session.scalar(
        select(User).where(User.role == "SYSTEM_ADMIN").limit(1)
    )
    if user is None:
        user = session.scalar(select(User).limit(1))
    if user is None:
        raise RuntimeError(
            "No user found in the database. "
            "Run the application and create at least one user before seeding."
        )
    return user


def _ensure_default_profile(session: Session, org: Organization, actor: User) -> None:
    existing = session.scalar(
        select(ReferenceProfileRecord).where(
            ReferenceProfileRecord.profile_code == PROFILE_CODE,
            ReferenceProfileRecord.version == PROFILE_VERSION,
        )
    )
    if existing is not None:
        print(
            f"[seed] Default profile already exists "
            f"(id={existing.id}, status={existing.status})"
        )
        return

    # Convert REF_BANDS (Tuple[ParameterBand, ...]) to a JSON-serializable list.
    parameter_bands: dict = {
        "bands": [
            {
                "band_id": b.band_id,
                "t_min_mm": b.t_min_mm,
                "t_max_mm": b.t_max_mm,
                "force_min_dan": b.force_min_dan,
                "force_max_dan": b.force_max_dan,
                "current_min_ka": b.current_min_ka,
                "current_max_ka": b.current_max_ka,
                "cooling_time_min_ms": b.cooling_time_min_ms,
                "cooling_time_max_ms": b.cooling_time_max_ms,
                "recommended_tip_diameter_mm": b.recommended_tip_diameter_mm,
            }
            for b in REF_BANDS
        ],
        "approval_status": "ENGINEERING_APPROVAL_PENDING",
        "note": "Derived from REF_BANDS constant; pending Excel cross-check (B01).",
    }

    now = datetime.now(timezone.utc)
    profile = ReferenceProfileRecord(
        profile_code=PROFILE_CODE,
        version=PROFILE_VERSION,
        org_id=None,
        display_name="SpotWeldPro Default Profile v1",
        material_scope="DC01/DC03/DC04 uncoated and HDG steel, automotive grade",
        stack_count="2T",
        cycle_basis_hz=50,
        t_min_mm=0.6,
        t_max_mm=2.5,
        status="DRAFT",
        is_system_default=True,
        parameter_bands=parameter_bands,
        nugget_criterion=_build_nugget_criterion(),
        source_provenance=_build_source_provenance(),
        source_document_id=None,
        created_by=actor.id,
        reviewer_user_id=None,
        approver_user_id=None,
        approved_at=None,
        deprecated_at=None,
        deprecation_reason=None,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.flush()
    print(
        f"[seed] Created Default profile "
        f"(id={profile.id}, code={PROFILE_CODE}, version={PROFILE_VERSION})"
    )


def main() -> None:
    print(f"[seed] Connecting to {DATABASE_URL}")
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        org = _get_or_create_system_org(session)
        actor = _get_system_actor(session)
        _ensure_default_profile(session, org, actor)
        session.commit()

    print("[seed] Done.")


if __name__ == "__main__":
    main()
