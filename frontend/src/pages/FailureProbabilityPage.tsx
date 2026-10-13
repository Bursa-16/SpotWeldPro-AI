
import { useState } from 'react'
import client from '../api/client'
import { useWeldAnalysis } from '../context/WeldAnalysisContext'
import { useAppLanguage } from '../i18n/useAppLanguage'
import type { RecommendedRangeRow } from '../types/weld'
import { VisualWeldInspector } from '../components/weld/VisualWeldInspector'

type FailureMode = {
  code: string
  title: string
  probability_percent: number
  confidence: string
  severity: string
  contributions: Array<{
    factor: string
    normalized_effect: number
    explanation: string
  }>
  validation_tests: string[]
  recommended_actions: string[]
}

type AnalysisResult = {
  failure_modes: FailureMode[]
  priority_actions: string[]
  disclaimer: string
}

function extractRanges(ranges: RecommendedRangeRow[] | undefined) {
  if (!ranges || ranges.length === 0) return null
  const byParam: Record<string, { min: number; max: number }> = {}
  for (const row of ranges) {
    byParam[row.Parametre] = { min: row['Önerilen Min'], max: row['Önerilen Maks'] }
  }
  const cur = byParam['Akım']
  const time = byParam['Kaynak süresi']
  const force = byParam['Elektrot kuvveti']
  const tip = byParam['Elektrot uç çapı']
  if (!cur || !time || !force || !tip) return null
  return { cur, time, force, tip }
}

export function FailureProbabilityPage({ onNavigateToAnalysis }: { onNavigateToAnalysis?: () => void }) {
  const { t } = useAppLanguage()
  const fp = t.failurePage
  const { lastInputs, lastResult } = useWeldAnalysis()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const ranges = extractRanges(lastResult?.recommended_ranges)
  const contextReady = lastInputs !== null && lastResult !== null && ranges !== null

  const anyCoated = lastInputs?.layers.some((l) => l.coated) ?? false
  const thicknessLabel = lastInputs?.layers.map((l) => `${l.thickness_mm} mm`).join(' + ') ?? '—'
  const coatingLabel = anyCoated ? fp.coated : fp.uncoated

  async function analyze() {
    if (!contextReady || !lastInputs || !lastResult || !ranges) return
    setLoading(true)
    setError('')
    try {
      const response = await client.post('/failure-probability/analyze', {
        material_family: lastInputs.material_family,
        stack_count: lastInputs.stack_count,
        coated: anyCoated,
        adhesive: lastInputs.adhesive,
        shunt_risk: lastInputs.shunt_risk,
        thicknesses_mm: lastInputs.layers.map((l) => Number(l.thickness_mm)),

        current_ka: lastInputs.current_ka,
        weld_cycles: lastInputs.weld_cycles,
        force_kn: lastInputs.force_kn,
        tip_diameter_mm: lastInputs.tip_diameter_mm,
        squeeze_cycles: lastInputs.squeeze_cycles,
        hold_cycles: lastInputs.hold_cycles,
        cooling_flow_lpm: lastInputs.cooling_flow_lpm,
        cooling_temp_c: lastInputs.cooling_temp_c,

        recommended_current_min_ka: ranges.cur.min,
        recommended_current_max_ka: ranges.cur.max,
        recommended_time_min_cycles: ranges.time.min,
        recommended_time_max_cycles: ranges.time.max,
        recommended_force_min_kn: ranges.force.min,
        recommended_force_max_kn: ranges.force.max,
        recommended_tip_min_mm: ranges.tip.min,
        recommended_tip_max_mm: ranges.tip.max,

        predicted_nugget_mm: lastResult.nugget_opt_mm,
        minimum_nugget_mm: lastResult.nugget_min_mm,
      })
      setResult(response.data)
    } catch {
      setError('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page active">
      <div className="ws-kicker">{fp.kicker}</div>
      <header className="page-header">
        <div>
          <h1>{fp.title}</h1>
          <p className="subtitle">{fp.subtitle}</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={analyze} disabled={loading || !contextReady}>
            {loading ? fp.calculating : fp.calculateBtn}
          </button>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Engineering context">
        <span className="ctx-chip accent">
          {fp.authorityChip.split(':')[0]}: <strong>{fp.authorityChip.split(':')[1]?.trim()}</strong>
        </span>
        <span className="ctx-chip">
          Input source: <strong>{contextReady ? fp.inputSourceReady : fp.inputSourceNone}</strong>
        </span>
        <span className="ctx-chip">Output: <strong>{fp.outputChip}</strong></span>
      </div>

      {!contextReady && (
        <div className="ws-grid-main">
          <section className="panel" aria-label="No context">
            <div className="panel-header"><h3>{fp.noContextTitle}</h3></div>
            <div className="panel-body">
              <div className="ws-empty" role="status">
                <span className="empty-glyph" aria-hidden="true">FA</span>
                <strong>{fp.noContextMessage}</strong>
                <span className="ws-empty-hint">{fp.noContextMessageDetail}</span>
                {onNavigateToAnalysis && (
                  <button className="btn btn-primary" style={{ marginTop: 'var(--sp-4)' }} onClick={onNavigateToAnalysis}>
                    {fp.noContextNavigate}
                  </button>
                )}
              </div>
            </div>
          </section>
        </div>
      )}

      {contextReady && !result && !loading && (
        <div className="ws-grid-main">
          <section className="panel" aria-label="Engineering inputs">
            <div className="panel-header">
              <h3>{fp.inputsTitle}</h3>
              <span className="panel-meta">{fp.inputsMeta}</span>
            </div>
            <div className="panel-body">
              <div className="trace-block">
                <div className="trace-row">
                  <span className="label">{fp.labelMaterial}</span>
                  <span className="value">{lastInputs!.material_family} · {coatingLabel} · {lastInputs!.stack_count} · {thicknessLabel}</span>
                </div>
                <div className="trace-row">
                  <span className="label">{fp.labelProcess}</span>
                  <span className="value">{lastInputs!.current_ka} kA · {lastInputs!.weld_cycles} cyc · {lastInputs!.force_kn} kN · {lastInputs!.tip_diameter_mm} mm tip</span>
                </div>
                <div className="trace-row">
                  <span className="label">{fp.labelRecommendationWindow}</span>
                  <span className="value">{ranges!.cur.min} – {ranges!.cur.max} kA · {ranges!.time.min} – {ranges!.time.max} cyc · {ranges!.force.min} – {ranges!.force.max} kN</span>
                </div>
              </div>
            </div>
            <div className="panel-footer">{fp.inputsFooter}</div>
          </section>
          <section className="panel" aria-label="Risk result workspace">
            <div className="panel-header">
              <h3>{fp.resultTitle}</h3>
              <span className="panel-meta">{fp.resultMeta}</span>
            </div>
            <div className="panel-body">
              <div className="ws-empty" role="status">
                <span className="empty-glyph" aria-hidden="true">RA</span>
                <strong>{fp.notYetRun}</strong>
                <span className="ws-empty-hint">{fp.notYetRunHint}</span>
                <span className="empty-action">{fp.notYetRunAction}</span>
              </div>
            </div>
            <div className="panel-footer">Probabilities render only when returned by the API.</div>
          </section>
        </div>
      )}

      {error && (
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">Backend connection unavailable</div>
            <div className="alert-text">Engineering data could not be loaded. Verify the API service and retry.</div>
          </div>
        </div>
      )}

      {loading && (
        <div className="state-msg" role="status">
          <div className="spinner" aria-hidden="true" />
          <span>{fp.calculating}</span>
        </div>
      )}

      {result && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>
          {contextReady && (
            <section className="panel" aria-label="Analysis context">
              <div className="panel-header">
                <h3>{fp.inputsTitle}</h3>
                <span className="panel-meta">{fp.inputsMeta}</span>
              </div>
              <div className="panel-body">
                <div className="trace-block">
                  <div className="trace-row">
                    <span className="label">{fp.labelMaterial}</span>
                    <span className="value">{lastInputs!.material_family} · {coatingLabel} · {lastInputs!.stack_count} · {thicknessLabel}</span>
                  </div>
                  <div className="trace-row">
                    <span className="label">{fp.labelProcess}</span>
                    <span className="value">{lastInputs!.current_ka} kA · {lastInputs!.weld_cycles} cyc · {lastInputs!.force_kn} kN · {lastInputs!.tip_diameter_mm} mm tip</span>
                  </div>
                </div>
              </div>
              <div className="panel-footer">These are the actual submitted inputs — not a default scenario.</div>
            </section>
          )}

          <section className="panel" aria-label={fp.priorityRisksTitle}>
            <div className="panel-header">
              <h3>{fp.priorityRisksTitle}</h3>
              <span className="panel-meta">{result.failure_modes.length} {fp.priorityRisksMetaSuffix}</span>
            </div>
            <div className="panel-body">
            <div className="grid-3">
              {result.failure_modes.slice(0, 6).map((mode) => {
                const isHigh = mode.probability_percent > 40
                return (
                  <article key={mode.code} className={`metric-card ${isHigh ? 'state-warn' : ''}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="metric-label">{mode.title}</span>
                      <span className={`badge ${isHigh ? 'warn' : 'ok'}`}>{mode.severity}</span>
                    </div>
                    <strong className="metric-value">%{mode.probability_percent.toFixed(1)}</strong>
                    <span className="metric-sub">{fp.confidenceLabel}: {mode.confidence}</span>

                    <div style={{ marginTop: 'var(--sp-2)' }}>
                      <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>{fp.mainFactorsLabel}:</span>
                      <ul className="action-list" style={{ marginTop: 'var(--sp-1)' }}>
                        {mode.contributions.filter((c) => c.normalized_effect !== 0).slice(0, 2).map((item) => (
                          <li key={item.factor}>
                            <strong>{item.factor}:</strong> {item.explanation}
                          </li>
                        ))}
                        {mode.contributions.filter((c) => c.normalized_effect !== 0).length === 0 && (
                          <li style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>{fp.noActiveFactors}</li>
                        )}
                      </ul>
                    </div>
                  </article>
                )
              })}
            </div>
            </div>
            <div className="panel-footer">API-returned probabilities only.</div>
          </section>

          <section className="panel" aria-label={fp.preventiveActionsTitle}>
            <div className="panel-header">
              <h3>{fp.preventiveActionsTitle}</h3>
            </div>
            <div className="panel-body">
            <ul className="action-list">
              {result.priority_actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ul>
            <p className="notice" style={{ marginTop: 'var(--sp-4)', fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)', borderTop: '1px solid var(--border)', paddingTop: 'var(--sp-3)' }}>
              {fp.ultrasonicGuidance}
            </p>
            {result.disclaimer && (
              <p className="notice" style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
                {result.disclaimer}
              </p>
            )}
            </div>
            <div className="panel-footer">Backend preventive actions only.</div>
          </section>

          <div className="alert neutral" role="note" style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)' }}>
            <div className="alert-body">
              <div className="alert-title">Notice</div>
              <div className="alert-text">{fp.qualificationDisclaimer}</div>
            </div>
          </div>
        </div>
      )}
      <VisualWeldInspector />
    </div>
  )
}
