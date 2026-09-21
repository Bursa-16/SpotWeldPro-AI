import { useState } from 'react'
import client from '../api/client'

export function OptimizationPage() {
  const [result, setResult] = useState<any>(null)
  const [model4, setModel4] = useState<any>(null)
  const [busyDoe, setBusyDoe] = useState(false)
  const [busyM4, setBusyM4] = useState(false)
  const [error, setError] = useState('')

  async function optimize() {
    setBusyDoe(true)
    setError('')
    try {
      const r = await client.post('/optimization/doe', {
        material_family: 'Düşük / Orta Karbonlu Çelik',
        thickness_mm: 1,
        min_nugget_mm: 4.2,
        target_nugget_mm: 5.2,
        current_min_ka: 6,
        current_max_ka: 12,
        current_step_ka: 0.5,
        time_min_cycles: 8,
        time_max_cycles: 18,
        time_step_cycles: 1,
        force_min_kn: 2,
        force_max_kn: 4,
        force_step_kn: 0.5,
      })
      setResult(r.data)
    } catch {
      setError('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.')
    } finally {
      setBusyDoe(false)
    }
  }

  async function runModel4() {
    setBusyM4(true)
    setError('')
    try {
      const r = await client.post('/optimization/model4/predict', {
        Current: 8000,
        Force: 300,
        Time: 12,
        Cooling: 0,
        Sequence: 15,
        Holding: 15,
        SheetThick: 1,
      })
      setModel4(r.data)
    } catch {
      setError('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.')
    } finally {
      setBusyM4(false)
    }
  }

  return (
    <div className="page active">
      <div className="ws-kicker">Engineering · Spot Welding Parametre Analysis</div>
      <header className="page-header">
        <div>
          <h1>DOE Optimization</h1>
          <p className="subtitle">Deterministic parameter-space screening with model-supported nugget prediction</p>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Engineering context">
        <span className="ctx-chip accent">Authority: <strong>backend deterministic search</strong></span>
        <span className="ctx-chip info">AI role: <strong>explanatory support only</strong></span>
      </div>
      {error && (
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">Backend connection unavailable</div>
            <div className="alert-text">Engineering data could not be loaded. Verify the API service and retry.</div>
          </div>
        </div>
      )}

      <div className="ws-grid-main">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
        <section className="panel" aria-label="Optimization objective">
          <div className="panel-header"><h3>Optimization objective and domain</h3><span className="panel-meta">constraints</span></div>
          <div className="panel-body">
          <div className="ws-zone-label">Objective · input domain · constraints</div>
          <div className="panel-header" style={{ marginTop: 'var(--sp-3)' }}>
            <h3>DOE parameter screening</h3>
            <button className="btn btn-primary btn-sm" onClick={optimize} disabled={busyDoe}>
              {busyDoe ? 'Taranıyor…' : 'Optimum Noktayı Bul'}
            </button>
          </div>
          {!result && !busyDoe && <div className="ws-empty" role="status"><span className="empty-glyph" aria-hidden="true">DO</span><strong>Optimization result unavailable</strong><span className="ws-empty-hint">Run optimization after defining the parameter domain. The backend screening result will appear here.</span><span className="empty-action">Next action: start the backend DOE screening.</span></div>}
          {busyDoe && (
            <div className="state-msg">
              <div className="spinner" />
              <span>Parametre uzayı taranıyor…</span>
            </div>
          )}
          {result && !busyDoe && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
              <div className="metric-card">
                <span className="metric-label">Değerlendirilen Kombinasyon</span>
                <strong className="metric-value">{result.evaluated_count}</strong>
              </div>
              <div className="trace-block">
                <div className="trace-row">
                  <span className="label">Optimum Kombinasyon</span>
                </div>
                <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-sm)', color: 'var(--accent)' }}>
                  {JSON.stringify(result.best, null, 2)}
                </pre>
              </div>
            </div>
          )}
          </div>
          <div className="panel-footer">Backend screening output only.</div>
        </section>

        <section className="panel" aria-label="Model-4 prediction">
          <div className="panel-header">
            <h3>Model-4 nugget prediction</h3>
            <button className="btn btn-secondary btn-sm" onClick={runModel4} disabled={busyM4}>
              {busyM4 ? 'Hesaplanıyor…' : 'Tahmin Çalıştır'}
            </button>
          </div>
          <div className="panel-body">
          {!model4 && !busyM4 && <div className="ws-empty" role="status"><span className="empty-glyph" aria-hidden="true">M4</span><strong>Optimization result unavailable</strong><span className="ws-empty-hint">Run optimization after defining the parameter domain. The backend Model-4 prediction will appear here.</span><span className="empty-action">Next action: run the backend Model-4 prediction.</span></div>}
          {busyM4 && (
            <div className="state-msg">
              <div className="spinner" />
              <span>Model-4 çalıştırılıyor…</span>
            </div>
          )}
          {model4 && !busyM4 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
              <div className="metric-card state-ok">
                <span className="metric-label">Tahmini Çekirdek Çapı</span>
                <strong className="metric-value">
                  {Number(model4.prediction_mm).toFixed(3)}
                  <span className="metric-unit"> mm</span>
                </strong>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Terim</th>
                    <th>Katkı (mm)</th>
                  </tr>
                </thead>
                <tbody>
                  {model4.top_contributions?.map((r: any) => (
                    <tr key={r.term}>
                      <td>{r.term}</td>
                      <td className="mono">{Number(r.contribution).toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          </div>
          <div className="panel-footer">Backend deterministic output only.</div>
        </section>
        </div>
        <section className="panel" aria-label="Optimization results">
          <div className="panel-header"><h3>Results</h3><span className="panel-meta">backend output</span></div>
          <div className="panel-body">
          <div className="ws-zone-label">Action area · results</div>
          {!result && !model4 && <div className="ws-empty" role="status"><span className="empty-glyph" aria-hidden="true">RS</span><strong>Analysis not yet run</strong><span className="ws-empty-hint">Backend optimization output will appear here after a screening or Model-4 run.</span><span className="empty-action">Next action: run a screening or prediction.</span></div>}
          {(result || model4) && (
            <div className="trace-block">
              <div className="trace-row"><span className="label">DOE screening</span><span className="value">{result ? `${result.evaluated_count} combinations evaluated` : 'not run'}</span></div>
              <div className="trace-row"><span className="label">Model-4</span><span className="value">{model4 ? `${Number(model4.prediction_mm).toFixed(3)} mm` : 'not run'}</span></div>
              <div className="trace-row"><span className="label">Authority</span><span className="value">backend deterministic output</span></div>
            </div>
          )}
          </div>
          <div className="panel-footer">Traceability: deterministic authority preserved.</div>
        </section>
      </div>
    </div>
  )
}

