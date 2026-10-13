from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./spot_welding_dev.db",
)

# DEMO_NEON_03: fail-fast checks for hosted-demo database configuration.
# Mirrors the JWT_SECRET_KEY check in app.core.security — only active when
# HOSTED_DEMO=true so local development is never affected.
if os.getenv("HOSTED_DEMO", "").strip().lower() in ("1", "true", "yes"):
    _hosted_db_url = os.getenv("DATABASE_URL")
    if not _hosted_db_url:
        raise RuntimeError(
            "DATABASE_URL is required when HOSTED_DEMO=true. "
            "Set it to the Neon PostgreSQL connection string in the Render dashboard."
        )
    if not _hosted_db_url.startswith(("postgresql://", "postgresql+", "postgres://")):
        raise RuntimeError(
            "DATABASE_URL must be a PostgreSQL connection URL when HOSTED_DEMO=true. "
            "SQLite and other databases are not permitted in the hosted demo."
        )
    _ssl_modes = ("sslmode=require", "sslmode=verify-full", "sslmode=verify-ca")
    if not any(mode in _hosted_db_url for mode in _ssl_modes):
        raise RuntimeError(
            "DATABASE_URL must include SSL (sslmode=require or stronger) when HOSTED_DEMO=true. "
            "Neon PostgreSQL connection strings include ?sslmode=require by default."
        )
    del _hosted_db_url, _ssl_modes

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
