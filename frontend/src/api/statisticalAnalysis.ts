/**
 * statisticalAnalysis.ts — Taguchi DOE ve ANOVA API istemcisi.
 * Tüm istekler /api/v1/statistical-analysis/* adresine gider.
 */
import client from './client'

// ── Ortak ─────────────────────────────────────────────────────────────────────
export interface FactorLevelSpec {
  name: string
  unit: string
  levels: number[]
}

export interface ANOVARowOut {
  source: string
  ss: number
  df: number
  ms: number | null
  f_statistic: number | null
  p_value: number | null
  contribution_pct: number | null
  note: string
}

// ── Taguchi Design ─────────────────────────────────────────────────────────────
export interface TaguchiDesignRequest {
  array_type: string
  factors: FactorLevelSpec[]
}

export interface ExperimentRunOut {
  run_number: number
  factor_values: Record<string, number>
}

export interface TaguchiDesignResponse {
  array_type: string
  runs: number
  n_factors: number
  levels_per_factor: number
  degrees_of_freedom: Record<string, number>
  residual_df: number
  saturated: boolean
  experiment_matrix: ExperimentRunOut[]
  warnings: string[]
}

// ── Taguchi Analyze ────────────────────────────────────────────────────────────
export interface TaguchiAnalyzeRequest {
  array_type: string
  factors: FactorLevelSpec[]
  sn_objective: string
  responses: number[]
  response_variable?: string
  response_unit?: string
}

export interface LevelEffectOut {
  level_index: number
  level_value: number
  mean_response: number
  sn_ratio: number
}

export interface FactorEffectOut {
  factor_name: string
  unit: string
  levels: LevelEffectOut[]
  delta_response: number
  delta_sn: number
  rank_response: number
  rank_sn: number
}

export interface OptimalSettingOut {
  factor_name: string
  unit: string
  optimal_level_index: number
  optimal_level_value: number
}

export interface TaguchiAnalyzeResponse {
  capability_type: string
  semantic_note: string
  array_type: string
  n_runs: number
  n_factors: number
  sn_objective: string
  grand_mean_response: number
  grand_mean_sn: number
  factor_effects: FactorEffectOut[]
  optimal_settings: OptimalSettingOut[]
  additive_prediction: number | null
  additive_prediction_note: string
  anova_table: ANOVARowOut[]
  warnings: string[]
}

// ── One-way ANOVA ──────────────────────────────────────────────────────────────
export interface ANOVAGroupData {
  group_name: string
  values: number[]
}

export interface ANOVAAnalyzeRequest {
  factor_name?: string
  response_variable?: string
  response_unit?: string
  groups: ANOVAGroupData[]
}

export interface ANOVAAnalyzeResponse {
  capability_type: string
  semantic_note: string
  design_type: string
  n_observations: number
  grand_mean: number
  table: ANOVARowOut[]
  residual_df: number
  rank_deficient: boolean
  saturated: boolean
  warnings: string[]
  assumptions: string[]
}

// ── API fonksiyonları ──────────────────────────────────────────────────────────
export async function taguchiDesign(req: TaguchiDesignRequest): Promise<TaguchiDesignResponse> {
  const resp = await client.post<TaguchiDesignResponse>('/statistical-analysis/taguchi/design', req)
  return resp.data
}

export async function taguchiAnalyze(req: TaguchiAnalyzeRequest): Promise<TaguchiAnalyzeResponse> {
  const resp = await client.post<TaguchiAnalyzeResponse>('/statistical-analysis/taguchi/analyze', req)
  return resp.data
}

export async function anovaAnalyze(req: ANOVAAnalyzeRequest): Promise<ANOVAAnalyzeResponse> {
  const resp = await client.post<ANOVAAnalyzeResponse>('/statistical-analysis/anova', req)
  return resp.data
}
