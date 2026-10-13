
import { useState } from 'react'
import client from '../api/client'
import { useAppLanguage } from '../i18n/useAppLanguage'

type LobePoint = {
  current_ka: number
  weld_cycles: number
  nugget_mm: number
  expulsion_risk: number
  fusion_risk: number
  zone: string
}

export function EngineeringPage() {
  const { t } = useAppLanguage()
  const ep = t.engineeringLobeLabPage
  const [result, setResult] = useState<{
    optimum: LobePoint | null
    safe_count: number
    warning_count: number
    unsafe_count: number
    sensitivity: Array<Record<string, unknown>>
  } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function calculate() {
    setBusy(true)
    setError('')
    try {
      const response = await client.post('/engineering/weld-lobe', {
        material_family: 'Düşük / Orta Karbonlu Çelik',
        thickness_mm: 1.0,
        force_kn: 3.0,
        min_nugget_mm: 4.2,
        current_min_ka: 6.0,
        current_max_ka: 12.0,
        current_step_ka: 0.5,
        time_min_cycles: 8,
        time_max_cycles: 18,
        time_step_cycles: 1,
      })
      setResult(response.data)
    } catch {
      setError('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page active">
      <div className="ws-kicker">{ep.kicker}</div>
      <header className="page-header">
        <div>
          <h1>{ep.title}</h1>
          <p className="subtitle">{ep.subtitle}</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={calculate} disabled={busy}>
            {busy ? ep.calculating : ep.calculateBtn}
          </button>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Engineering context">
        <span className="ctx-chip accent">{ep.authorityChip.split(':')[0]}: <strong>{ep.authorityChip.split(':')[1]?.trim()}</strong></span>
        <span className="ctx-chip">Method: <strong>{ep.methodChip.split(':')[1]?.trim()}</strong></span>
        <span className="ctx-chip">Curves: <strong>{ep.curvesChip.split(':')[1]?.trim()}</strong></span>
      </div>
      {error && (
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">Backend connection unavailable</div>
            <div className="alert-text">Engineering data could not be loaded. Verify the API service and retry.</div>
          </div>
        </div>
      )}

      {!result && !busy && (
        <div className="ws-grid-main">
          <section className="panel" aria-label="Engineering context">
            <div className="panel-header">
              <h3>{ep.contextTitle}</h3>
              <span className="panel-meta">{ep.contextMeta}</span>
            </div>
            <div className="panel-body">
            <div className="trace-block">
              <div className="trace-row"><span className="label">Material</span><span className="value">{ep.contextMaterial}</span></div>
              <div className="trace-row"><span className="label">Force</span><span className="value">{ep.contextForce}</span></div>
              <div className="trace-row"><span className="label">Current sweep</span><span className="value">{ep.contextCurrentSweep}</span></div>
              <div className="trace-row"><span className="label">Time sweep</span><span className="value">{ep.contextTimeSweep}</span></div>
            </div>
            </div>
            <div className="panel-footer">{ep.contextFooter}</div>
          </section>
          <section className="panel" aria-label="Process window workspace">
            <div className="panel-header">
              <h3>{ep.processWindowTitle}</h3>
              <span className="panel-meta">{ep.processWindowMeta}</span>
            </div>
            <div className="panel-body">
            <div className="chart-ready" role="status">
              <div className="chart-frame" aria-hidden="true">
                <div className="chart-axes" />
                <div className="chart-caption">Current × Time · safe-window frame</div>
              </div>
              <strong>{ep.noDataMessage}</strong>
              <span>{ep.noDataHint}</span>
              <span className="empty-action">{ep.noDataAction}</span>
            </div>
            </div>
            <div className="panel-footer">{ep.processWindowFooter}</div>
          </section>
        </div>
      )}

      {busy && (
        <div className="state-msg" role="status">
          <div className="spinner" aria-hidden="true" />
          <span>{ep.calculatingVerbose}</span>
        </div>
      )}

      {result && !busy && (
        <div className="ws-grid-main">
          <section className="panel" aria-label="Process window summary">
            <div className="panel-header">
              <h3>{ep.summaryTitle}</h3>
              <span className="panel-meta">{ep.summaryMeta}</span>
            </div>
            <div className="panel-body">
            <div className="grid-2">
              <article className="metric-card state-ok">
                <span className="metric-label">{ep.safeCount}</span>
                <strong className="metric-value">{result.safe_count}</strong>
              </article>
              <article className="metric-card state-warn">
                <span className="metric-label">{ep.warningCount}</span>
                <strong className="metric-value">{result.warning_count}</strong>
              </article>
              <article className="metric-card state-danger">
                <span className="metric-label">{ep.unsafeCount}</span>
                <strong className="metric-value">{result.unsafe_count}</strong>
              </article>
              <article className="metric-card">
                <span className="metric-label">{ep.optimumPoint}</span>
                <strong className="metric-value" style={{ fontSize: 'var(--fs-h4)' }}>
                  {result.optimum ? `${result.optimum.current_ka} kA / ${result.optimum.weld_cycles} cyc` : '—'}
                </strong>
              </article>
            </div>
            </div>
            <div className="panel-footer">{ep.summaryFooter}</div>
          </section>

          <section className="panel" aria-label={ep.sensitivityTitle}>
            <div className="panel-header">
              <h3>{ep.sensitivityTitle}</h3>
              <span className="panel-meta">{ep.sensitivityMeta}</span>
            </div>
            <div className="panel-body">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{ep.sensitivityRank}</th>
                  <th>{ep.sensitivityParam}</th>
                  <th>{ep.sensitivityImpact}</th>
                  <th>{ep.sensitivitySensitivity}</th>
                </tr>
              </thead>
              <tbody>
                {result.sensitivity.map((row) => (
                  <tr key={String(row.parameter)}>
                    <td className="mono">{String(row.priority_rank)}</td>
                    <td>{String(row.parameter)}</td>
                    <td className="mono">{String(row.absolute_impact)}</td>
                    <td className="mono">{String(row.sensitivity_mm_per_unit)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
            <div className="panel-footer">{ep.sensitivityFooter}</div>
          </section>
        </div>
      )}
    </div>
  )
}
