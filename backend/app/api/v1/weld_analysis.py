"""POST /api/v1/weld-analysis — Public Demo endpoint.

ACCESS POLICY: PUBLIC_DEMO (anonymous access permitted)
  This endpoint is intentionally public. It performs bounded, stateless,
  in-memory engineering calculations using only the hardcoded public
  reference profile (REF_PROFILE_MS_2T_50HZ_V1).

ISOLATION CONTRACT (must be maintained on every future change):
  ✓  No database reads of any kind.
  ✓  No database writes of any kind.
  ✓  No access to user, project, weld-point, or organization records.
  ✓  No customer-owned reference profiles — system constant only.
  ✓  No WeldPoint persistence — calculation result is never stored.
  ✓  Response contains only deterministic computation outputs.
  ✗  profile_id — NOT accepted, NOT forwarded to the engine.
  ✗  org_id     — NOT accepted, NOT forwarded to the engine.

RATE LIMITING:
  60 requests / IP / 60 seconds (per-process in-memory limiter).
  See app/core/rate_limit.py for deployment scope and proxy notes.

ESCALATION PATH:
  For analysis with a customer-owned reference profile, use the
  authenticated CUSTOMER_ANALYSIS tier (Phase 2 scope, not yet live).
  That tier will require Depends(get_current_user) + org membership + APPROVED
  profile status — it will NOT share this route or this service instance.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.application.weld_analysis_service import WeldAnalysisService
from app.core.rate_limit import PUBLIC_DEMO_LIMITER, get_client_ip
from app.schemas.analysis import WeldAnalysisRequest, WeldAnalysisResponse

router = APIRouter(prefix="/weld-analysis", tags=["Weld Analysis"])


def get_service() -> WeldAnalysisService:
    return WeldAnalysisService()


@router.post("", response_model=WeldAnalysisResponse)
def analyze_weld(
    request: Request,
    payload: WeldAnalysisRequest,
    service: WeldAnalysisService = Depends(get_service),  # noqa: B008
):
    """Public demo calculation. Anonymous access; stateless; no customer data."""
    ip = get_client_ip(request)
    allowed, _remaining = PUBLIC_DEMO_LIMITER.is_allowed(ip)
    if not allowed:
        # Return JSONResponse directly so Retry-After survives the custom
        # exception handler in main.py (which only passes through WWW-Authenticate).
        return JSONResponse(
            status_code=429,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down and try again.",
                "detail": {
                    "limit": PUBLIC_DEMO_LIMITER.limit,
                    "window_seconds": PUBLIC_DEMO_LIMITER.window_seconds,
                },
            },
            headers={"Retry-After": str(PUBLIC_DEMO_LIMITER.window_seconds)},
        )
    return service.analyze(payload)
