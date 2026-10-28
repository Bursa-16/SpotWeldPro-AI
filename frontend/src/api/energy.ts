/**
 * energy.ts — Energy Intelligence API client.
 * P0 + P1 — MASTER-ENERGY-OPTIMIZATION-01.
 */
import client from './client'

// ── Enums (mirror backend) ────────────────────────────────────────────────────
export type EnergyWindowStatus =
  | 'NOT_ESTABLISHED'
  | 'IN_WINDOW'
  | 'BELOW_MIN'
  | 'ABOVE_MAX'
  | 'E_CURRENT_ABSENT'

export type EnergyValidationStatus = 'NOT_VALIDATED' | 'HYPOTHESIS' | 'VALIDATED'
export type EnergyMethod = 'I2RT' | 'WAVEFORM' | 'USER_ENTERED'

// ── P0: Single estimate ────────────────────────────────────────────────────────
export interface EnergyEstimateRequest {
  current_ka: number
  resistance_micro_ohm: number
  weld_cycles: number
  frequency_hz?: number
}

export interface EnergyI2RTResponse {
  energy_j: number
  energy_kj: number
  energy_wh: number
  energy_kwh: number
  time_s: number
  current_ka: number
  resistance_micro_ohm: number
  weld_cycles: number
  frequency_hz: number
  method: EnergyMethod
  assumptions: string[]
}

// ── P0: Energy window ─────────────────────────────────────────────────────────
export interface EnergyWindowRequest {
  e_current_kj?: number | null
  e_min_kj?: number | null
  e_ideal_kj?: number | null
  e_max_kj?: number | null
  method?: EnergyMethod
  validation_status?: EnergyValidationStatus
  validation_note?: string | null
}

export interface EnergyWindowResponse {
  e_min_kj: number | null
  e_ideal_kj: number | null
  e_max_kj: number | null
  e_current_kj: number | null
  e_current_j: number | null
  e_current_wh: number | null
  e_current_kwh: number | null
  delta_e_signed_kj: number | null
  e_excess_potential_kj: number | null
  e_margin_upper_kj: number | null
  e_margin_lower_kj: number | null
  window_status: EnergyWindowStatus
  quality_risk_flag: boolean
  out_of_window: boolean
  method: EnergyMethod
  validation_status: EnergyValidationStatus
  validation_note: string | null
  assumptions: string[]
}

// ── P0: Cost ──────────────────────────────────────────────────────────────────
export interface CostIntelligenceRequest {
  e_current_kj: number
  e_ideal_kj: number
  spots_per_part: number
  production_volume_annual: number
  tariff_eur_per_kwh: number
  tariff_usd_per_kwh: number
  ideal_validation_status?: EnergyValidationStatus
}

export interface CostIntelligenceResult {
  e_current_kj: number
  e_ideal_kj: number
  spots_per_part: number
  production_volume_annual: number
  tariff_eur_per_kwh: number
  tariff_usd_per_kwh: number
  delta_e_spot_kj: number
  delta_e_spot_kwh: number
  delta_e_part_kj: number
  delta_e_part_kwh: number
  delta_e_per_1000_parts_kwh: number
  cost_diff_eur_per_1000_parts: number
  cost_diff_usd_per_1000_parts: number
  delta_e_annual_kwh: number
  cost_diff_eur_annual: number
  cost_diff_usd_annual: number
  ideal_validation_status: EnergyValidationStatus
  disclaimer: string
}

// ── P1: Multi-spot aggregation ────────────────────────────────────────────────
export interface WeldPointEnergySpecIn {
  point_code: string
  group_name?: string
  e_current_kj?: number | null
  e_min_kj?: number | null
  e_ideal_kj?: number | null
  e_max_kj?: number | null
  validation_status?: EnergyValidationStatus
  validation_note?: string | null
}

export interface MultiSpotAggregationRequest {
  points: WeldPointEnergySpecIn[]
  production_volume_annual?: number | null
  tariff_eur_per_kwh?: number | null
  tariff_usd_per_kwh?: number | null
  pareto_top_n?: number
}

export interface WeldPointWindowRow {
  point_code: string
  group_name: string
  e_current_kj: number | null
  e_min_kj: number | null
  e_ideal_kj: number | null
  e_max_kj: number | null
  delta_e_signed_kj: number | null
  e_excess_potential_kj: number | null
  window_status: EnergyWindowStatus
  quality_risk_flag: boolean
  out_of_window: boolean
}

export interface WeldGroupSummaryOut {
  group_name: string
  point_count: number
  e_current_total_kj: number | null
  e_ideal_total_kj: number | null
  delta_total_kj: number | null
  e_excess_total_kj: number | null
  points_in_window: number
  points_below_min: number
  points_above_max: number
  points_not_established: number
  points_quality_risk: number
}

export interface MultiSpotAggregationResponse {
  rows: WeldPointWindowRow[]
  groups: WeldGroupSummaryOut[]
  part_point_count: number
  part_e_current_total_kj: number | null
  part_e_ideal_total_kj: number | null
  part_delta_total_kj: number | null
  part_e_excess_total_kj: number | null
  part_points_in_window: number
  part_points_below_min: number
  part_points_above_max: number
  part_points_not_established: number
  part_points_quality_risk: number
  annual_e_excess_total_kwh: number | null
  annual_cost_eur: number | null
  annual_cost_usd: number | null
  pareto_by_excess: WeldPointWindowRow[]
  disclaimer: string
  production_volume_annual: number | null
  tariff_eur_per_kwh: number | null
  tariff_usd_per_kwh: number | null
}

// ── P1: Import ────────────────────────────────────────────────────────────────
export interface ImportPreviewRequest {
  csv_text: string
  existing_point_codes?: string[]
}

export interface CellErrorOut {
  row_number: number
  column: string
  raw_value: string
  error_type: string
  message: string
}

export interface ImportPreviewRowOut {
  row_number: number
  point_code: string
  group_name: string
  e_current_kj: number | null
  e_min_kj: number | null
  e_ideal_kj: number | null
  e_max_kj: number | null
  validation_note: string | null
  accepted: boolean
  row_errors: CellErrorOut[]
}

export interface ImportPreviewResponse {
  total_rows: number
  accepted_count: number
  rejected_count: number
  formula_injection_detected: boolean
  formula_injection_cells: string[]
  duplicate_point_codes: string[]
  missing_columns: string[]
  errors: CellErrorOut[]
  preview_rows: ImportPreviewRowOut[]
  has_blocking_errors: boolean
}

// ── P2-B: Scenario comparison ─────────────────────────────────────────────────
export interface ScenarioPointIn {
  point_code: string
  group_name?: string
  e_min_kj?: number | null
  e_ideal_kj?: number | null
  e_max_kj?: number | null
  validation_status?: EnergyValidationStatus
  baseline_e_current_kj?: number | null
  proposed_e_current_kj?: number | null
}

export interface ScenarioComparisonRequest {
  points: ScenarioPointIn[]
  production_volume_annual?: number | null
  tariff_eur_per_kwh?: number | null
  tariff_usd_per_kwh?: number | null
}

export interface ScenarioPointResultOut {
  point_code: string
  group_name: string
  e_min_kj: number | null
  e_ideal_kj: number | null
  e_max_kj: number | null
  baseline_e_current_kj: number | null
  baseline_window_status: EnergyWindowStatus
  baseline_delta_e_kj: number | null
  baseline_excess_kj: number | null
  baseline_quality_risk: boolean
  proposed_e_current_kj: number | null
  proposed_window_status: EnergyWindowStatus
  proposed_delta_e_kj: number | null
  proposed_excess_kj: number | null
  proposed_quality_risk: boolean
  e_change_kj: number | null
  excess_change_kj: number | null
  quality_improved: boolean
  quality_degraded: boolean
  warnings: string[]
}

export interface ScenarioGroupSummaryOut {
  group_name: string
  point_count: number
  baseline_e_total_kj: number | null
  proposed_e_total_kj: number | null
  e_reduction_kj: number | null
  baseline_in_window: number
  proposed_in_window: number
  improved_count: number
  degraded_count: number
}

export interface ScenarioComparisonResponse {
  points: ScenarioPointResultOut[]
  groups: ScenarioGroupSummaryOut[]
  part_baseline_e_total_kj: number | null
  part_proposed_e_total_kj: number | null
  part_e_reduction_kj: number | null
  annual_e_reduction_kwh: number | null
  annual_cost_saving_eur: number | null
  annual_cost_saving_usd: number | null
  baseline_points_in_window: number
  proposed_points_in_window: number
  total_improved: number
  total_degraded: number
  production_volume_annual: number | null
  tariff_eur_per_kwh: number | null
  tariff_usd_per_kwh: number | null
  disclaimer: string
}

// ── P2-D: Dashboard ───────────────────────────────────────────────────────────
export interface DashboardRequest {
  points: WeldPointEnergySpecIn[]
  production_volume_annual?: number | null
  tariff_eur_per_kwh?: number | null
  tariff_usd_per_kwh?: number | null
  pareto_top_n?: number
  sensitivity_volumes?: number[] | null
  sensitivity_tariffs_eur?: number[] | null
}

export interface ParetoDetailRowOut {
  point_code: string
  group_name: string
  e_current_kj: number | null
  e_ideal_kj: number | null
  e_excess_kj: number | null
  pct_of_total_excess: number | null
  cumulative_pct: number | null
  window_status: EnergyWindowStatus
}

export interface FinancialSummaryOut {
  avg_excess_per_spot_kj: number | null
  avg_excess_per_spot_kwh: number | null
  part_excess_kj: number | null
  part_excess_kwh: number | null
  per_1000_parts_excess_kwh: number | null
  cost_eur_per_1000_parts: number | null
  cost_usd_per_1000_parts: number | null
  annual_excess_kwh: number | null
  annual_cost_eur: number | null
  annual_cost_usd: number | null
  production_volume_annual: number | null
  tariff_eur_per_kwh: number | null
  tariff_usd_per_kwh: number | null
}

export interface SensitivityRowOut {
  production_volume: number
  tariff_eur_per_kwh: number
  annual_excess_kwh: number | null
  cost_eur: number | null
  cost_usd: number | null
}

export interface DashboardResponse extends MultiSpotAggregationResponse {
  pareto_detailed: ParetoDetailRowOut[]
  financial: FinancialSummaryOut
  sensitivity: SensitivityRowOut[]
  dashboard_disclaimer: string
}

// ── API functions ─────────────────────────────────────────────────────────────
export async function energyEstimate(req: EnergyEstimateRequest): Promise<EnergyI2RTResponse> {
  const resp = await client.post<EnergyI2RTResponse>('/energy/estimate', req)
  return resp.data
}

export async function energyWindow(req: EnergyWindowRequest): Promise<EnergyWindowResponse> {
  const resp = await client.post<EnergyWindowResponse>('/energy/window', req)
  return resp.data
}

export async function energyCost(req: CostIntelligenceRequest): Promise<CostIntelligenceResult> {
  const resp = await client.post<CostIntelligenceResult>('/energy/cost', req)
  return resp.data
}

export async function energyAggregate(req: MultiSpotAggregationRequest): Promise<MultiSpotAggregationResponse> {
  const resp = await client.post<MultiSpotAggregationResponse>('/energy/aggregate', req)
  return resp.data
}

export async function energyImportPreview(req: ImportPreviewRequest): Promise<ImportPreviewResponse> {
  const resp = await client.post<ImportPreviewResponse>('/energy/import/preview', req)
  return resp.data
}

export async function energyImportPreviewFile(
  file: File,
  existingPointCodes?: string[],
): Promise<ImportPreviewResponse> {
  const form = new FormData()
  form.append('file', file)
  if (existingPointCodes?.length) {
    form.append('existing_point_codes', existingPointCodes.join(','))
  }
  const resp = await client.post<ImportPreviewResponse>(
    '/energy/import/preview/file',
    form,
  )
  return resp.data
}

export async function energyScenarioCompare(req: ScenarioComparisonRequest): Promise<ScenarioComparisonResponse> {
  const resp = await client.post<ScenarioComparisonResponse>('/energy/scenario/compare', req)
  return resp.data
}

export async function energyDashboard(req: DashboardRequest): Promise<DashboardResponse> {
  const resp = await client.post<DashboardResponse>('/energy/dashboard', req)
  return resp.data
}

export function energyImportTemplateUrl(): string {
  const base = (import.meta as { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE ?? '/api/v1'
  return `${base}/energy/import/template`
}

// ── P2-F: Report generation ────────────────────────────────────────────────────

export interface EnergyReportRequest {
  points: Array<{
    point_code: string
    group_name: string
    e_current_kj?: number | null
    e_min_kj?: number | null
    e_ideal_kj?: number | null
    e_max_kj?: number | null
  }>
  production_volume_annual?: number | null
  tariff_eur_per_kwh?: number | null
  tariff_usd_per_kwh?: number | null
  pareto_top_n?: number
  project_id?: string | null
  project_name?: string | null
  part_id?: string | null
  passport_id?: string | null
  report_language?: 'en' | 'tr'
  analyst_name?: string | null
  report_title?: string | null
}

export type ReportFormat = 'csv' | 'xlsx' | 'pdf'

export async function downloadEnergyReport(
  req: EnergyReportRequest,
  format: ReportFormat,
): Promise<{ filename: string }> {
  const resp = await client.post(`/energy/report/${format}`, req, {
    responseType: 'blob',
  })
  const cd: string = resp.headers['content-disposition'] ?? ''
  const fnMatch = cd.match(/filename="?([^";\n]+)"?/)
  const filename = fnMatch?.[1] ?? `SWP-Energy-Report.${format}`
  const url = URL.createObjectURL(new Blob([resp.data as BlobPart]))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  return { filename }
}
