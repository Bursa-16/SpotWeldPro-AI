"""
energy.py — Energy Intelligence API router.

P0 + P1 + P2-B + P2-D scope: MASTER-ENERGY-OPTIMIZATION-01.

Routes:
  POST /api/v1/energy/estimate             — single I²Rt energy estimate
  POST /api/v1/energy/window               — five-indicator energy window
  POST /api/v1/energy/cost                 — theoretical cost aggregation
  POST /api/v1/energy/aggregate            — multi-spot aggregation (P1)
  POST /api/v1/energy/import/preview       — CSV import validation (JSON body) (P1)
  POST /api/v1/energy/import/preview/file  — CSV or XLSX file upload preview (P1)
  GET  /api/v1/energy/import/template      — downloadable CSV template (P1)
  POST /api/v1/energy/scenario/compare     — baseline vs proposed scenario comparison (P2-B)
  POST /api/v1/energy/dashboard            — energy & financial intelligence dashboard (P2-D)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import PlainTextResponse

from app.api.dependencies import require_permission
from app.domain.energy_window import (
    compute_energy_i2rt,
    compute_energy_window,
    compute_spot_cost_aggregation,
)
from app.domain.energy_aggregation import (
    WeldPointEnergySpec,
    aggregate_multi_spot,
)
from app.domain.import_validation import (
    validate_csv_import,
    ImportValidationResult,
    TEMPLATE_CSV,
)
from app.domain.excel_import import validate_xlsx_import
from app.domain.energy_window import EnergyValidationStatus
from app.domain.scenario_comparison import (
    ScenarioPointIn as ScenarioDomainPointIn,
    compare_scenarios,
)
from app.domain.energy_dashboard import compute_dashboard_extras
from app.schemas.energy import (
    CostIntelligenceRequest,
    CostIntelligenceResult,
    EnergyEstimateRequest,
    EnergyI2RTResponse,
    EnergyWindowRequest,
    EnergyWindowResponse,
    MultiSpotAggregationRequest,
    MultiSpotAggregationResponse,
    WeldPointWindowRow,
    WeldGroupSummaryOut,
    ImportPreviewRequest,
    ImportPreviewResponse,
    CellErrorOut,
    ImportPreviewRowOut,
    ScenarioComparisonRequest,
    ScenarioComparisonResponse,
    ScenarioPointResultOut,
    ScenarioGroupSummaryOut,
    DashboardRequest,
    DashboardResponse,
    ParetoDetailRowOut,
    FinancialSummaryOut,
    SensitivityRowOut,
)

router = APIRouter(
    prefix="/energy",
    tags=["energy"],
)


@router.post("/estimate", response_model=EnergyI2RTResponse)
def estimate_energy(
    req: EnergyEstimateRequest,
    _: None = Depends(require_permission("weld:read")),
) -> EnergyI2RTResponse:
    """Compute electrode-side energy via E = I_rms² × R × t.

    current_ka must be the RMS weld-controller setpoint, not peak current.
    Returns energy in J, kJ, Wh, and kWh.
    """
    result = compute_energy_i2rt(
        current_ka=req.current_ka,
        resistance_micro_ohm=req.resistance_micro_ohm,
        weld_cycles=req.weld_cycles,
        frequency_hz=req.frequency_hz,
    )
    return EnergyI2RTResponse(
        energy_j=result.energy_j,
        energy_kj=result.energy_kj,
        energy_wh=result.energy_wh,
        energy_kwh=result.energy_kwh,
        time_s=result.time_s,
        current_ka=result.current_ka,
        resistance_micro_ohm=result.resistance_micro_ohm,
        weld_cycles=result.weld_cycles,
        frequency_hz=result.frequency_hz,
        method=result.method,
        assumptions=result.assumptions,
    )


@router.post("/window", response_model=EnergyWindowResponse)
def evaluate_energy_window(
    req: EnergyWindowRequest,
    _: None = Depends(require_permission("weld:read")),
) -> EnergyWindowResponse:
    """Evaluate the five energy indicators and process-window status.

    Supply e_min_kj, e_ideal_kj, e_max_kj only when supported by validated
    experimental evidence. Omit them (leave None) to receive
    window_status=NOT_ESTABLISHED rather than an invented estimate.
    """
    result = compute_energy_window(
        e_current_kj=req.e_current_kj,
        e_min_kj=req.e_min_kj,
        e_ideal_kj=req.e_ideal_kj,
        e_max_kj=req.e_max_kj,
        method=req.method,
        validation_status=req.validation_status,
        validation_note=req.validation_note,
    )
    return EnergyWindowResponse(
        e_min_kj=result.e_min_kj,
        e_ideal_kj=result.e_ideal_kj,
        e_max_kj=result.e_max_kj,
        e_current_kj=result.e_current_kj,
        e_current_j=result.e_current_j,
        e_current_wh=result.e_current_wh,
        e_current_kwh=result.e_current_kwh,
        delta_e_signed_kj=result.delta_e_signed_kj,
        e_excess_potential_kj=result.e_excess_potential_kj,
        e_margin_upper_kj=result.e_margin_upper_kj,
        e_margin_lower_kj=result.e_margin_lower_kj,
        window_status=result.window_status,
        quality_risk_flag=result.quality_risk_flag,
        out_of_window=result.out_of_window,
        method=result.method,
        validation_status=result.validation_status,
        validation_note=result.validation_note,
        assumptions=result.assumptions,
    )


@router.post("/cost", response_model=CostIntelligenceResult)
def compute_cost_intelligence(
    req: CostIntelligenceRequest,
    _: None = Depends(require_permission("weld:read")),
) -> CostIntelligenceResult:
    """Compute theoretical energy-difference cost aggregation.

    The response always includes a `disclaimer` field.
    Present all cost figures together with the disclaimer text.
    """
    result = compute_spot_cost_aggregation(
        e_current_kj=req.e_current_kj,
        e_ideal_kj=req.e_ideal_kj,
        spots_per_part=req.spots_per_part,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        ideal_validation_status=req.ideal_validation_status,
    )
    return CostIntelligenceResult(
        e_current_kj=result.e_current_kj,
        e_ideal_kj=result.e_ideal_kj,
        spots_per_part=result.spots_per_part,
        production_volume_annual=result.production_volume_annual,
        tariff_eur_per_kwh=result.tariff_eur_per_kwh,
        tariff_usd_per_kwh=result.tariff_usd_per_kwh,
        delta_e_spot_kj=result.delta_e_spot_kj,
        delta_e_spot_kwh=result.delta_e_spot_kwh,
        delta_e_part_kj=result.delta_e_part_kj,
        delta_e_part_kwh=result.delta_e_part_kwh,
        delta_e_per_1000_parts_kwh=result.delta_e_per_1000_parts_kwh,
        cost_diff_eur_per_1000_parts=result.cost_diff_eur_per_1000_parts,
        cost_diff_usd_per_1000_parts=result.cost_diff_usd_per_1000_parts,
        delta_e_annual_kwh=result.delta_e_annual_kwh,
        cost_diff_eur_annual=result.cost_diff_eur_annual,
        cost_diff_usd_annual=result.cost_diff_usd_annual,
        ideal_validation_status=result.ideal_validation_status,
        disclaimer=result.disclaimer,
    )


# ---------------------------------------------------------------------------
# P1: Multi-spot aggregation
# ---------------------------------------------------------------------------

@router.post("/aggregate", response_model=MultiSpotAggregationResponse)
def aggregate_energy(
    req: MultiSpotAggregationRequest,
    _: None = Depends(require_permission("weld:read")),
) -> MultiSpotAggregationResponse:
    """Aggregate energy windows for multiple weld points.

    Returns per-point, per-group, part-level, and annual totals.
    Provide production_volume_annual and tariffs for annual cost rollup.
    """
    specs = [
        WeldPointEnergySpec(
            point_code=p.point_code,
            group_name=p.group_name,
            e_current_kj=p.e_current_kj,
            e_min_kj=p.e_min_kj,
            e_ideal_kj=p.e_ideal_kj,
            e_max_kj=p.e_max_kj,
            validation_status=p.validation_status,
            validation_note=p.validation_note,
        )
        for p in req.points
    ]
    result = aggregate_multi_spot(
        specs=specs,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        pareto_top_n=req.pareto_top_n,
    )

    def _row(r) -> WeldPointWindowRow:
        return WeldPointWindowRow(
            point_code=r.spec.point_code,
            group_name=r.spec.group_name,
            e_current_kj=r.window.e_current_kj,
            e_min_kj=r.window.e_min_kj,
            e_ideal_kj=r.window.e_ideal_kj,
            e_max_kj=r.window.e_max_kj,
            delta_e_signed_kj=r.window.delta_e_signed_kj,
            e_excess_potential_kj=r.window.e_excess_potential_kj,
            window_status=r.window.window_status,
            quality_risk_flag=r.window.quality_risk_flag,
            out_of_window=r.window.out_of_window,
        )

    groups_out = [
        WeldGroupSummaryOut(
            group_name=g.group_name,
            point_count=g.point_count,
            e_current_total_kj=g.e_current_total_kj,
            e_ideal_total_kj=g.e_ideal_total_kj,
            delta_total_kj=g.delta_total_kj,
            e_excess_total_kj=g.e_excess_total_kj,
            points_in_window=g.points_in_window,
            points_below_min=g.points_below_min,
            points_above_max=g.points_above_max,
            points_not_established=g.points_not_established,
            points_quality_risk=g.points_quality_risk,
        )
        for g in result.groups
    ]

    return MultiSpotAggregationResponse(
        rows=[_row(r) for r in result.rows],
        groups=groups_out,
        part_point_count=result.part_point_count,
        part_e_current_total_kj=result.part_e_current_total_kj,
        part_e_ideal_total_kj=result.part_e_ideal_total_kj,
        part_delta_total_kj=result.part_delta_total_kj,
        part_e_excess_total_kj=result.part_e_excess_total_kj,
        part_points_in_window=result.part_points_in_window,
        part_points_below_min=result.part_points_below_min,
        part_points_above_max=result.part_points_above_max,
        part_points_not_established=result.part_points_not_established,
        part_points_quality_risk=result.part_points_quality_risk,
        annual_e_excess_total_kwh=result.annual_e_excess_total_kwh,
        annual_cost_eur=result.annual_cost_eur,
        annual_cost_usd=result.annual_cost_usd,
        pareto_by_excess=[_row(r) for r in result.pareto_by_excess],
        disclaimer=result.disclaimer,
        production_volume_annual=result.production_volume_annual,
        tariff_eur_per_kwh=result.tariff_eur_per_kwh,
        tariff_usd_per_kwh=result.tariff_usd_per_kwh,
    )


# ---------------------------------------------------------------------------
# P1: Import preview and template
# ---------------------------------------------------------------------------

def _build_preview_response(result: ImportValidationResult) -> ImportPreviewResponse:
    """Convert a domain ImportValidationResult to an API ImportPreviewResponse."""
    def _cell_err(e) -> CellErrorOut:
        return CellErrorOut(
            row_number=e.row_number,
            column=e.column,
            raw_value=e.raw_value,
            error_type=e.error_type,
            message=e.message,
        )

    preview_rows_out = [
        ImportPreviewRowOut(
            row_number=r.row_number,
            point_code=r.point_code,
            group_name=r.group_name,
            e_current_kj=r.e_current_kj,
            e_min_kj=r.e_min_kj,
            e_ideal_kj=r.e_ideal_kj,
            e_max_kj=r.e_max_kj,
            validation_note=r.validation_note,
            accepted=r.accepted,
            row_errors=[_cell_err(e) for e in r.row_errors],
        )
        for r in result.preview_rows
    ]

    return ImportPreviewResponse(
        total_rows=result.total_rows,
        accepted_count=result.accepted_count,
        rejected_count=result.rejected_count,
        formula_injection_detected=result.formula_injection_detected,
        formula_injection_cells=result.formula_injection_cells,
        duplicate_point_codes=result.duplicate_point_codes,
        missing_columns=result.missing_columns,
        errors=[_cell_err(e) for e in result.errors],
        preview_rows=preview_rows_out,
        has_blocking_errors=result.has_blocking_errors,
    )


@router.post("/import/preview", response_model=ImportPreviewResponse)
def import_preview(
    req: ImportPreviewRequest,
    _: None = Depends(require_permission("weld:read")),
) -> ImportPreviewResponse:
    """Validate a CSV import without writing to the database.

    Returns a full validation report including formula-injection detection,
    duplicate detection, and per-row accept/reject status.

    The caller MUST show this report to the user and require explicit
    confirmation before writing any rows.
    """
    result = validate_csv_import(
        csv_text=req.csv_text,
        existing_point_codes=set(req.existing_point_codes),
    )
    return _build_preview_response(result)


_XLSX_CONTENT_TYPES = frozenset({
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
})

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/import/preview/file", response_model=ImportPreviewResponse)
async def import_preview_file(
    file: UploadFile = File(...),
    _: None = Depends(require_permission("weld:read")),
) -> ImportPreviewResponse:
    """Validate a CSV or XLSX file upload without writing to the database.

    Accepts:
      - .csv  (UTF-8 text, same validation as /import/preview)
      - .xlsx (Excel Open XML; formulas are never evaluated — data_only=True)

    Format is detected from the file extension first, then Content-Type.
    Returns the same ImportPreviewResponse as /import/preview.
    """
    raw = await file.read(_MAX_UPLOAD_BYTES + 1)

    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    is_xlsx = filename.endswith(".xlsx") or "spreadsheetml" in content_type

    if len(raw) > _MAX_UPLOAD_BYTES:
        from app.domain.import_validation import CellError, ImportValidationResult as IVR
        result: ImportValidationResult = IVR(
            total_rows=0, accepted_count=0, rejected_count=0,
            formula_injection_detected=False, formula_injection_cells=[],
            duplicate_point_codes=[], missing_columns=[],
            errors=[CellError(0, "", "", "FILE_TOO_LARGE",
                              "Uploaded file exceeds the 10 MB limit.")],
            preview_rows=[], has_blocking_errors=True,
        )
    elif is_xlsx:
        result = validate_xlsx_import(raw)
    else:
        text = raw.decode("utf-8", errors="replace")
        result = validate_csv_import(text)

    return _build_preview_response(result)


# ---------------------------------------------------------------------------
# P2-B: Scenario comparison
# ---------------------------------------------------------------------------

@router.post("/scenario/compare", response_model=ScenarioComparisonResponse)
def compare_energy_scenarios(
    req: ScenarioComparisonRequest,
    _: None = Depends(require_permission("weld:read")),
) -> ScenarioComparisonResponse:
    """Compare baseline vs proposed energy scenarios for multiple weld points.

    This is a SCENARIO EVALUATION, not a validated optimisation.
    Nugget diameter, expulsion risk, and coating models are not applied.
    All proposed values require validated experimental confirmation.
    """
    domain_points = [
        ScenarioDomainPointIn(
            point_code=p.point_code,
            group_name=p.group_name,
            e_min_kj=p.e_min_kj,
            e_ideal_kj=p.e_ideal_kj,
            e_max_kj=p.e_max_kj,
            validation_status=p.validation_status,
            baseline_e_current_kj=p.baseline_e_current_kj,
            proposed_e_current_kj=p.proposed_e_current_kj,
        )
        for p in req.points
    ]
    result = compare_scenarios(
        points=domain_points,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
    )

    return ScenarioComparisonResponse(
        points=[
            ScenarioPointResultOut(
                point_code=pr.point_code,
                group_name=pr.group_name,
                e_min_kj=pr.e_min_kj,
                e_ideal_kj=pr.e_ideal_kj,
                e_max_kj=pr.e_max_kj,
                baseline_e_current_kj=pr.baseline_e_current_kj,
                baseline_window_status=pr.baseline_window_status,
                baseline_delta_e_kj=pr.baseline_delta_e_kj,
                baseline_excess_kj=pr.baseline_excess_kj,
                baseline_quality_risk=pr.baseline_quality_risk,
                proposed_e_current_kj=pr.proposed_e_current_kj,
                proposed_window_status=pr.proposed_window_status,
                proposed_delta_e_kj=pr.proposed_delta_e_kj,
                proposed_excess_kj=pr.proposed_excess_kj,
                proposed_quality_risk=pr.proposed_quality_risk,
                e_change_kj=pr.e_change_kj,
                excess_change_kj=pr.excess_change_kj,
                quality_improved=pr.quality_improved,
                quality_degraded=pr.quality_degraded,
                warnings=pr.warnings,
            )
            for pr in result.points
        ],
        groups=[
            ScenarioGroupSummaryOut(
                group_name=g.group_name,
                point_count=g.point_count,
                baseline_e_total_kj=g.baseline_e_total_kj,
                proposed_e_total_kj=g.proposed_e_total_kj,
                e_reduction_kj=g.e_reduction_kj,
                baseline_in_window=g.baseline_in_window,
                proposed_in_window=g.proposed_in_window,
                improved_count=g.improved_count,
                degraded_count=g.degraded_count,
            )
            for g in result.groups
        ],
        part_baseline_e_total_kj=result.part_baseline_e_total_kj,
        part_proposed_e_total_kj=result.part_proposed_e_total_kj,
        part_e_reduction_kj=result.part_e_reduction_kj,
        annual_e_reduction_kwh=result.annual_e_reduction_kwh,
        annual_cost_saving_eur=result.annual_cost_saving_eur,
        annual_cost_saving_usd=result.annual_cost_saving_usd,
        baseline_points_in_window=result.baseline_points_in_window,
        proposed_points_in_window=result.proposed_points_in_window,
        total_improved=result.total_improved,
        total_degraded=result.total_degraded,
        production_volume_annual=result.production_volume_annual,
        tariff_eur_per_kwh=result.tariff_eur_per_kwh,
        tariff_usd_per_kwh=result.tariff_usd_per_kwh,
        disclaimer=result.disclaimer,
    )


# ---------------------------------------------------------------------------
# P2-D: Energy & Financial Intelligence Dashboard
# ---------------------------------------------------------------------------

@router.post("/dashboard", response_model=DashboardResponse)
def compute_energy_dashboard(
    req: DashboardRequest,
    _: None = Depends(require_permission("weld:read")),
) -> DashboardResponse:
    """P2-D: Energy & Financial Intelligence Dashboard.

    Combines multi-spot aggregation (P1) with enhanced Pareto percentages,
    hierarchical financial summary, and sensitivity analysis matrix.

    All cost and excess energy figures are THEORETICAL — see dashboard_disclaimer.
    """
    specs = [
        WeldPointEnergySpec(
            point_code=p.point_code,
            group_name=p.group_name,
            e_current_kj=p.e_current_kj,
            e_min_kj=p.e_min_kj,
            e_ideal_kj=p.e_ideal_kj,
            e_max_kj=p.e_max_kj,
            validation_status=p.validation_status,
            validation_note=p.validation_note,
        )
        for p in req.points
    ]
    aggr = aggregate_multi_spot(
        specs=specs,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        pareto_top_n=req.pareto_top_n,
    )

    extras = compute_dashboard_extras(
        aggr_rows=aggr.rows,
        part_excess_kj=aggr.part_e_excess_total_kj,
        production_volume_annual=req.production_volume_annual,
        tariff_eur_per_kwh=req.tariff_eur_per_kwh,
        tariff_usd_per_kwh=req.tariff_usd_per_kwh,
        sensitivity_volumes=req.sensitivity_volumes,
        sensitivity_tariffs_eur=req.sensitivity_tariffs_eur,
    )

    def _row(r) -> WeldPointWindowRow:
        return WeldPointWindowRow(
            point_code=r.spec.point_code,
            group_name=r.spec.group_name,
            e_current_kj=r.window.e_current_kj,
            e_min_kj=r.window.e_min_kj,
            e_ideal_kj=r.window.e_ideal_kj,
            e_max_kj=r.window.e_max_kj,
            delta_e_signed_kj=r.window.delta_e_signed_kj,
            e_excess_potential_kj=r.window.e_excess_potential_kj,
            window_status=r.window.window_status,
            quality_risk_flag=r.window.quality_risk_flag,
            out_of_window=r.window.out_of_window,
        )

    groups_out = [
        WeldGroupSummaryOut(
            group_name=g.group_name,
            point_count=g.point_count,
            e_current_total_kj=g.e_current_total_kj,
            e_ideal_total_kj=g.e_ideal_total_kj,
            delta_total_kj=g.delta_total_kj,
            e_excess_total_kj=g.e_excess_total_kj,
            points_in_window=g.points_in_window,
            points_below_min=g.points_below_min,
            points_above_max=g.points_above_max,
            points_not_established=g.points_not_established,
            points_quality_risk=g.points_quality_risk,
        )
        for g in aggr.groups
    ]

    pareto_detailed_out = [
        ParetoDetailRowOut(
            point_code=pr.point_code,
            group_name=pr.group_name,
            e_current_kj=pr.e_current_kj,
            e_ideal_kj=pr.e_ideal_kj,
            e_excess_kj=pr.e_excess_kj,
            pct_of_total_excess=pr.pct_of_total_excess,
            cumulative_pct=pr.cumulative_pct,
            window_status=pr.window_status,
        )
        for pr in extras.pareto_detailed
    ]

    f = extras.financial
    financial_out = FinancialSummaryOut(
        avg_excess_per_spot_kj=f.avg_excess_per_spot_kj,
        avg_excess_per_spot_kwh=f.avg_excess_per_spot_kwh,
        part_excess_kj=f.part_excess_kj,
        part_excess_kwh=f.part_excess_kwh,
        per_1000_parts_excess_kwh=f.per_1000_parts_excess_kwh,
        cost_eur_per_1000_parts=f.cost_eur_per_1000_parts,
        cost_usd_per_1000_parts=f.cost_usd_per_1000_parts,
        annual_excess_kwh=f.annual_excess_kwh,
        annual_cost_eur=f.annual_cost_eur,
        annual_cost_usd=f.annual_cost_usd,
        production_volume_annual=f.production_volume_annual,
        tariff_eur_per_kwh=f.tariff_eur_per_kwh,
        tariff_usd_per_kwh=f.tariff_usd_per_kwh,
    )

    sensitivity_out = [
        SensitivityRowOut(
            production_volume=s.production_volume,
            tariff_eur_per_kwh=s.tariff_eur_per_kwh,
            annual_excess_kwh=s.annual_excess_kwh,
            cost_eur=s.cost_eur,
            cost_usd=s.cost_usd,
        )
        for s in extras.sensitivity
    ]

    return DashboardResponse(
        rows=[_row(r) for r in aggr.rows],
        groups=groups_out,
        part_point_count=aggr.part_point_count,
        part_e_current_total_kj=aggr.part_e_current_total_kj,
        part_e_ideal_total_kj=aggr.part_e_ideal_total_kj,
        part_delta_total_kj=aggr.part_delta_total_kj,
        part_e_excess_total_kj=aggr.part_e_excess_total_kj,
        part_points_in_window=aggr.part_points_in_window,
        part_points_below_min=aggr.part_points_below_min,
        part_points_above_max=aggr.part_points_above_max,
        part_points_not_established=aggr.part_points_not_established,
        part_points_quality_risk=aggr.part_points_quality_risk,
        annual_e_excess_total_kwh=aggr.annual_e_excess_total_kwh,
        annual_cost_eur=aggr.annual_cost_eur,
        annual_cost_usd=aggr.annual_cost_usd,
        pareto_by_excess=[_row(r) for r in aggr.pareto_by_excess],
        disclaimer=aggr.disclaimer,
        production_volume_annual=aggr.production_volume_annual,
        tariff_eur_per_kwh=aggr.tariff_eur_per_kwh,
        tariff_usd_per_kwh=aggr.tariff_usd_per_kwh,
        pareto_detailed=pareto_detailed_out,
        financial=financial_out,
        sensitivity=sensitivity_out,
        dashboard_disclaimer=extras.disclaimer,
    )


@router.get("/import/template", response_class=PlainTextResponse)
def get_import_template(
    _: None = Depends(require_permission("weld:read")),
) -> str:
    """Download the energy import CSV template.

    Returns a UTF-8 CSV file with the required columns and example rows.
    """
    return PlainTextResponse(
        content=TEMPLATE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="energy_import_template.csv"'},
    )
