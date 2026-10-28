"""
reports.py — P2-F Engineering Report API router.

Routes:
  POST /api/v1/energy/report/csv   — download CSV energy report
  POST /api/v1/energy/report/xlsx  — download XLSX energy report
  POST /api/v1/energy/report/pdf   — download PDF energy report
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.dependencies import require_permission
from app.domain.energy_aggregation import WeldPointEnergySpec
from app.domain.energy_window import EnergyValidationStatus
from app.domain.report_engine import (
    build_report_context,
    generate_csv_report,
    generate_pdf_report,
    generate_xlsx_report,
)
from app.schemas.reports import EnergyReportRequest

router = APIRouter(prefix="/energy/report", tags=["Energy Reports (P2-F)"])


def _build_specs(req: EnergyReportRequest) -> list[WeldPointEnergySpec]:
    return [
        WeldPointEnergySpec(
            point_code=p.point_code,
            group_name=p.group_name,
            e_current_kj=p.e_current_kj,
            e_min_kj=p.e_min_kj,
            e_ideal_kj=p.e_ideal_kj,
            e_max_kj=p.e_max_kj,
            validation_status=EnergyValidationStatus.NOT_VALIDATED,
        )
        for p in req.points
    ]


def _safe_filename(base: str, ext: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"SWP-Energy-Report-{ts}.{ext}"


@router.post(
    "/csv",
    summary="Download energy analysis report as CSV",
    response_class=Response,
)
def report_csv(
    req: EnergyReportRequest,
    _: None = Depends(require_permission("weld:read")),
) -> Response:
    specs = _build_specs(req)
    ctx = build_report_context(
        specs,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        pareto_top_n=req.pareto_top_n,
        project_id=req.project_id,
        project_name=req.project_name,
        part_id=req.part_id,
        passport_id=req.passport_id,
        report_language=req.report_language,
        analyst_name=req.analyst_name,
        report_title=req.report_title,
        input_hash=req.input_hash,
    )
    data = generate_csv_report(ctx)
    fname = _safe_filename("SWP-Energy-Report", "csv")
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post(
    "/xlsx",
    summary="Download energy analysis report as XLSX",
    response_class=Response,
)
def report_xlsx(
    req: EnergyReportRequest,
    _: None = Depends(require_permission("weld:read")),
) -> Response:
    specs = _build_specs(req)
    ctx = build_report_context(
        specs,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        pareto_top_n=req.pareto_top_n,
        project_id=req.project_id,
        project_name=req.project_name,
        part_id=req.part_id,
        passport_id=req.passport_id,
        report_language=req.report_language,
        analyst_name=req.analyst_name,
        report_title=req.report_title,
        input_hash=req.input_hash,
    )
    data = generate_xlsx_report(ctx)
    fname = _safe_filename("SWP-Energy-Report", "xlsx")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post(
    "/pdf",
    summary="Download energy analysis report as PDF",
    response_class=Response,
)
def report_pdf(
    req: EnergyReportRequest,
    _: None = Depends(require_permission("weld:read")),
) -> Response:
    specs = _build_specs(req)
    ctx = build_report_context(
        specs,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        pareto_top_n=req.pareto_top_n,
        project_id=req.project_id,
        project_name=req.project_name,
        part_id=req.part_id,
        passport_id=req.passport_id,
        report_language=req.report_language,
        analyst_name=req.analyst_name,
        report_title=req.report_title,
        input_hash=req.input_hash,
    )
    data = generate_pdf_report(ctx)
    fname = _safe_filename("SWP-Energy-Report", "pdf")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
