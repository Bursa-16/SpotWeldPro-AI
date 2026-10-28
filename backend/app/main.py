
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

import app.models
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.digital_weld_passport import router as digital_weld_passport_router
from app.api.v1.engineering import router as engineering_router
from app.api.v1.engineering_library import router as engineering_library_router
from app.api.v1.evidence_verification import router as evidence_verification_router
from app.api.v1.failure_probability import router as failure_probability_router
from app.api.v1.health import router as health_router
from app.api.v1.machine_readiness import router as machine_readiness_router
from app.api.v1.projects import router as projects_router
from app.api.v1.rule_evaluation import router as rule_evaluation_router
from app.api.v1.rule_registry import router as rule_registry_router
from app.api.v1.tests import router as tests_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.reference_profiles import router as reference_profiles_router
from app.api.v1.weld_analysis import router as weld_analysis_router
from app.api.v1.model_catalog import router as model_catalog_router
from app.api.v1.statistical_analysis import router as statistical_analysis_router
from app.api.v1.energy import router as energy_router
from app.api.v1.reports import router as reports_router
from app.core.security import canonicalize_username, hash_password
from app.db.session import SessionLocal
from app.models.entities import User
from app.models.enums import UserRole
from app.schemas.governed_api import GovernedAPIError

_log = logging.getLogger(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Development default: all local Vite dev-server ports.
# Override for private demo hosting via CORS_ORIGINS env var (comma-separated).
# Trailing slashes on each origin are stripped: browser Origin headers never
# include a trailing slash, so an operator-entered trailing slash would silently
# reject every preflight from the deployed frontend.
_CORS_DEFAULT = ",".join([
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5180",
    "http://127.0.0.1:4175",
    "http://127.0.0.1:4177",
])
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
_ALLOWED_ORIGINS = [
    o.strip().rstrip("/")
    for o in (_cors_env or _CORS_DEFAULT).split(",")
    if o.strip()
]

# DEMO_CORS_01: fail-fast when HOSTED_DEMO=true — mirrors the JWT_SECRET_KEY and
# DATABASE_URL guards in security.py and db/session.py.  Without CORS_ORIGINS the
# server falls back to localhost-only defaults and every browser preflight from
# the deployed frontend fails with no Access-Control-Allow-Origin header.
if os.getenv("HOSTED_DEMO", "").strip().lower() in ("1", "true", "yes"):
    if not _cors_env:
        raise RuntimeError(
            "CORS_ORIGINS is required when HOSTED_DEMO=true. "
            "Set it to the deployed frontend HTTPS URL in the Render dashboard, "
            "e.g. https://spotweldpro-ai-demo.onrender.com"
        )
    _https_origins = [o for o in _ALLOWED_ORIGINS if o.startswith("https://")]
    if not _https_origins:
        raise RuntimeError(
            "CORS_ORIGINS must include at least one HTTPS origin when HOSTED_DEMO=true. "
            "All configured origins are HTTP — the deployed frontend uses HTTPS."
        )
    del _https_origins
del _cors_env

# ── API documentation ─────────────────────────────────────────────────────────
# Set DISABLE_DOCS=true in a private-demo .env to hide /docs, /redoc and
# /openapi.json from the hosted instance.
_disable_docs = os.getenv("DISABLE_DOCS", "").strip().lower() in ("1", "true", "yes")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with SessionLocal() as db:
        admin_email    = os.getenv("ADMIN_EMAIL")
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if admin_email and admin_username and admin_password:
            canonical = canonicalize_username(admin_username)
            admin = db.scalar(select(User).where(User.username == canonical))
            if not admin:
                db.add(User(
                    username=canonical,
                    email=admin_email,
                    full_name="System Administrator",
                    password_hash=hash_password(admin_password),
                    role=UserRole.SYSTEM_ADMIN,
                ))
                db.commit()
    yield


app = FastAPI(
    title="Spot Welding Platform API",
    version="1.3.0",
    description="Spot welding parameter analysis and engineering decision-support API",
    lifespan=lifespan,
    docs_url=None if _disable_docs else "/docs",
    redoc_url=None if _disable_docs else "/redoc",
    openapi_url=None if _disable_docs else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error_code" in detail:
        payload = GovernedAPIError(
            error_code=detail["error_code"],
            message=detail.get("message", ""),
            detail=detail.get("context"),
        )
        headers = {}
        if exc.headers and "WWW-Authenticate" in exc.headers:
            headers["WWW-Authenticate"] = exc.headers["WWW-Authenticate"]
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
            headers=headers or None,
        )
    _log.error("unstructured HTTPException: status=%s detail=%r", exc.status_code, detail)
    payload = GovernedAPIError(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


app.include_router(health_router, prefix="/api/v1")
app.include_router(failure_probability_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(engineering_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(rule_evaluation_router, prefix="/api/v1")
app.include_router(digital_weld_passport_router, prefix="/api/v1")
app.include_router(machine_readiness_router, prefix="/api/v1")
app.include_router(rule_registry_router, prefix="/api/v1")
app.include_router(evidence_verification_router, prefix="/api/v1")
app.include_router(weld_analysis_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tests_router, prefix="/api/v1")
app.include_router(engineering_library_router, prefix="/api/v1")
app.include_router(organizations_router, prefix="/api/v1")
app.include_router(reference_profiles_router, prefix="/api/v1")
app.include_router(model_catalog_router, prefix="/api/v1")
app.include_router(statistical_analysis_router, prefix="/api/v1")
app.include_router(energy_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
