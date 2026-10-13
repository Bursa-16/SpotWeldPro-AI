"""Seed script: create the demo user for SpotWeldPro AI demo environment.

Usage:
    cd backend
    DEMO_USERNAME=demo DEMO_PASSWORD=<secret> python scripts/seed_demo_user.py

Or load a local .env before running:
    set -a && source ../.env && set +a  (bash)
    python scripts/seed_demo_user.py

Environment variables:
    DEMO_USERNAME   canonical demo username (default: "demo")
    DEMO_PASSWORD   required — no default; the script exits if unset

The script is idempotent — it skips creation silently if the canonical
username already exists. Run it once after applying migration 0014.

Role: READ_ONLY (least-privileged role for product demonstration).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from the backend root: python scripts/seed_demo_user.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Required environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite:///./spot_welding.db")
if not os.environ.get("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "seed-script-placeholder-not-used-for-tokens"

from sqlalchemy import select

from app.core.security import canonicalize_username, hash_password
from app.db.session import SessionLocal
from app.models.entities import User
from app.models.enums import UserRole

DEMO_USERNAME = os.environ.get("DEMO_USERNAME", "demo")
_raw_password = os.environ.get("DEMO_PASSWORD")
if not _raw_password:
    sys.exit("[seed] DEMO_PASSWORD environment variable is required. Set it before running this script.")
DEMO_PASSWORD = _raw_password
del _raw_password
DEMO_EMAIL = f"{DEMO_USERNAME}@internal.spotwelding"
DEMO_FULL_NAME = "Demo User"
DEMO_ROLE = UserRole.READ_ONLY


def seed_demo_user() -> None:
    canonical = canonicalize_username(DEMO_USERNAME)

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == canonical))
        if existing:
            print(f"[seed] Demo user '{canonical}' already exists (id={existing.id}). Skipped.")
            return

        user = User(
            username=canonical,
            email=DEMO_EMAIL,
            full_name=DEMO_FULL_NAME,
            password_hash=hash_password(DEMO_PASSWORD),
            role=DEMO_ROLE,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[seed] Demo user created: username='{user.username}', email='{user.email}', role='{user.role}', id={user.id}")


if __name__ == "__main__":
    seed_demo_user()
