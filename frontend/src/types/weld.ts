export type LayerInput = {
  material_family: string
  material_subtype: string
  thickness_mm: number
  coated: boolean
}

export type WeldAnalysisRequest = {
  material_family: string
  material_subtype: string
  stack_count: '2T' | '3T' | '4T'
  layers: LayerInput[]
  current_ka: number
  weld_cycles: number
  force_kn: number
  tip_diameter_mm: number
  squeeze_cycles: number
  hold_cycles: number
  cooling_flow_lpm: number
  cooling_temp_c: number
  dc_current: boolean
  adhesive: boolean
  shunt_risk: boolean
}

export type WeldAnalysisResponse = {
  score: number
  risk_level: string
  nugget_min_mm: number
  nugget_opt_mm: number
  selected_model: string | null
  selected_prediction_mm?: number | null
  compliance_summary: {
    total_rules?: number
    passed?: number
    failed?: number
    review?: number
    score: number
  }
  risks: Array<{ title: string; detail: string }>
  actions: string[]
  recommended_ranges?: RecommendedRangeRow[]
  notes?: unknown[]
  model_results?: ModelResultRow[]
  compliance_results?: ComplianceRuleRow[]
  compliance_conflicts?: ComplianceConflictRow[]
}

export type RecommendedRangeRow = {
  Parametre: string
  'Önerilen Min': number
  'Önerilen Maks': number
  Birim: string
  Mevcut: number
  Durum: string
}

export type ComplianceRuleRow = {
  rule_id: string | number
  rule_name: string
  source_type: string
  source_name: string
  priority: number
  parameter: string
  actual_value: number
  expected: string
  status: string
  note?: string
}

export type ComplianceConflictRow = {
  parameter: string
  material_family: string
  stack_count: string
  winner_rule: string
  winner_source: string
  challenger_rule: string
  challenger_source: string
  decision: string
}

export type ModelResultRow = {
  model_name?: string
  prediction_mm?: number
  validation_status?: string
  [key: string]: unknown
}
