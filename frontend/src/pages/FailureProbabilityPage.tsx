
import { useState } from 'react'
import client from '../api/client'

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

export function FailureProbabilityPage() {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function analyze() {
    setLoading(true)
    setError('')
    try {
      const response = await client.post('/failure-probability/analyze', {
        material_family: 'Galvanizli / Kaplamalı Çelik',
        stack_count: '2T',
        coated: true,
        adhesive: false,
        shunt_risk: false,
        thicknesses_mm: [1.0, 1.0],

        current_ka: 11.5,
        weld_cycles: 15,
        force_kn: 2.2,
        tip_diameter_mm: 6.0,
        squeeze_cycles: 15,
        hold_cycles: 12,
        cooling_flow_lpm: 5.0,
        cooling_temp_c: 28,

        recommended_current_min_ka: 8.0,
        recommended_current_max_ka: 10.5,
        recommended_time_min_cycles: 10,
        recommended_time_max_cycles: 12,
        recommended_force_min_kn: 2.5,
        recommended_force_max_kn: 3.5,
        recommended_tip_min_mm: 6,
        recommended_tip_max_mm: 6,

        predicted_nugget_mm: 5.0,
        minimum_nugget_mm: 4.2,
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
      <div className="ws-kicker">Engineering · Spot Welding Parametre Analysis</div>
      <header className="page-header">
        <div>
          <h1>Failure Analysis</h1>
          <p className="subtitle">Backend risk-engineering evaluation — probabilities are shown only when returned by the API</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={analyze} disabled={loading}>
            {loading ? 'Hesaplanıyor…' : 'Hata Olasılıklarını Hesapla'}
          </button>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Engineering context">
        <span className="ctx-chip accent">Authority: <strong>backend failure model</strong></span>
        <span className="ctx-chip">Output: <strong>only API-returned probabilities</strong></span>
      </div>
      {error && (
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">Backend connection unavailable</div>
            <div className="alert-text">Engineering data could not be loaded. Verify the API service and retry.</div>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="ws-grid-main">
          <section className="panel" aria-label="Engineering inputs">
            <div className="panel-header"><h3>Engineering inputs</h3><span className="panel-meta">backend request context</span></div>
            <div className="panel-body">
            <div className="trace-block">
              <div className="trace-row"><span className="label">Material</span><span className="value">coated steel · 2T · 1.0 + 1.0 mm</span></div>
              <div className="trace-row"><span className="label">Process</span><span className="value">11.5 kA · 15 cyc · 2.2 kN · 6.0 mm tip</span></div>
              <div className="trace-row"><span className="label">Recommendation window</span><span className="value">8.0 – 10.5 kA · 10 – 12 cyc · 2.5 – 3.5 kN</span></div>
            </div>
            </div>
            <div className="panel-footer">Request context only — probabilities come from backend.</div>
          </section>
          <section className="panel" aria-label="Risk result workspace">
            <div className="panel-header"><h3>Risk result</h3><span className="panel-meta">result-ready</span></div>
            <div className="panel-body">
            <div className="ws-empty" role="status"><span className="empty-glyph" aria-hidden="true">RA</span><strong>Analysis not yet run</strong><span className="ws-empty-hint">Run the backend failure analysis to populate risk modes, probabilities and preventive actions.</span><span className="empty-action">Next action: run the backend failure analysis.</span></div>
            </div>
            <div className="panel-footer">Probabilities render only when returned by the API.</div>
          </section>
        </div>
      )}

      {loading && (
        <div className="state-msg" role="status">
          <div className="spinner" aria-hidden="true" />
          <span>Hata modelleri hesaplanıyor…</span>
        </div>
      )}

      {result && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>
          <section className="panel" aria-label="Öncelikli Riskler">
            <div className="panel-header">
              <h3>Öncelikli Risk Modları</h3>
              <span className="panel-meta">{result.failure_modes.length} mod değerlendirildi</span>
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
                    <span className="metric-sub">Güven Derecesi: {mode.confidence}</span>

                    <div style={{ marginTop: 'var(--sp-2)' }}>
                      <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>Ana Etkenler:</span>
                      <ul className="action-list" style={{ marginTop: 'var(--sp-1)' }}>
                        {mode.contributions.slice(0, 2).map((item) => (
                          <li key={item.factor}>
                            <strong>{item.factor}:</strong> {item.explanation}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </article>
                )
              })}
            </div>
            </div>
            <div className="panel-footer">API-returned probabilities only.</div>
          </section>

          <section className="panel" aria-label="Önerilen Aksiyonlar">
            <div className="panel-header">
              <h3>Genel Öncelikli Önleyici Aksiyonlar</h3>
            </div>
            <div className="panel-body">
            <ul className="action-list">
              {result.priority_actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ul>
            {result.disclaimer && (
              <p className="notice" style={{ marginTop: 'var(--sp-4)', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
                {result.disclaimer}
              </p>
            )}
            </div>
            <div className="panel-footer">Backend preventive actions only.</div>
          </section>
        </div>
      )}
    </div>
  )
}

