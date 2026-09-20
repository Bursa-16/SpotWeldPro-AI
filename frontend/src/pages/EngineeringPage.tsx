
import { useState } from 'react'
import client from '../api/client'

type LobePoint = {
  current_ka: number
  weld_cycles: number
  nugget_mm: number
  expulsion_risk: number
  fusion_risk: number
  zone: string
}

export function EngineeringPage() {
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
      <div className="ws-kicker">Engineering · Spot Welding Parametre Analysis</div>
      <header className="page-header">
        <div>
          <h1>Weld Lobe Lab</h1>
          <p className="subtitle">Process window, sensitivity and optimum-point analysis from the backend simulation only</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={calculate} disabled={busy}>
            {busy ? 'Hesaplanıyor…' : 'Weld Lobe Hesapla'}
          </button>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Engineering context">
        <span className="ctx-chip accent">Authority: <strong>backend simulation</strong></span>
        <span className="ctx-chip">Method: <strong>process-window sweep</strong></span>
        <span className="ctx-chip">Curves: <strong>only when backend returns data</strong></span>
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
            <div className="panel-header"><h3>Engineering context</h3><span className="panel-meta">parameter range</span></div>
            <div className="panel-body">
            <div className="trace-block">
              <div className="trace-row"><span className="label">Material</span><span className="value">low/medium carbon steel · 1.0 mm</span></div>
              <div className="trace-row"><span className="label">Force</span><span className="value">3.0 kN</span></div>
              <div className="trace-row"><span className="label">Current sweep</span><span className="value">6.0 – 12.0 kA · step 0.5</span></div>
              <div className="trace-row"><span className="label">Time sweep</span><span className="value">8 – 18 cycles · step 1</span></div>
            </div>
            </div>
            <div className="panel-footer">Sweep definition only — no simulated curves.</div>
          </section>
          <section className="panel" aria-label="Process window workspace">
            <div className="panel-header"><h3>Process window</h3><span className="panel-meta">chart-ready</span></div>
            <div className="panel-body">
            <div className="chart-ready" role="status"><div className="chart-frame" aria-hidden="true"><div className="chart-axes" /><div className="chart-caption">Current × Time · safe-window frame</div></div><strong>No process-window data</strong><span>Process-window visualization becomes available after valid engineering input.</span><span className="empty-action">Next action: run the backend simulation.</span></div>
            </div>
            <div className="panel-footer">Curves render only from backend output.</div>
          </section>
        </div>
      )}

      {busy && (
        <div className="state-msg" role="status">
          <div className="spinner" aria-hidden="true" />
          <span>Lobe simülasyonu çalıştırılıyor…</span>
        </div>
      )}

      {result && !busy && (
        <div className="ws-grid-main">
          <section className="panel" aria-label="Process window summary">
            <div className="panel-header">
              <h3>Kaynak Penceresi Özeti</h3>
              <span className="panel-meta">Simülasyon</span>
            </div>
            <div className="panel-body">
            <div className="grid-2">
              <article className="metric-card state-ok">
                <span className="metric-label">Güvenli Nokta</span>
                <strong className="metric-value">{result.safe_count}</strong>
              </article>
              <article className="metric-card state-warn">
                <span className="metric-label">Uyarı Noktası</span>
                <strong className="metric-value">{result.warning_count}</strong>
              </article>
              <article className="metric-card state-danger">
                <span className="metric-label">Uygun Olmayan</span>
                <strong className="metric-value">{result.unsafe_count}</strong>
              </article>
              <article className="metric-card">
                <span className="metric-label">Optimum Nokta</span>
                <strong className="metric-value" style={{ fontSize: 'var(--fs-h4)' }}>
                  {result.optimum ? `${result.optimum.current_ka} kA / ${result.optimum.weld_cycles} cyc` : '—'}
                </strong>
              </article>
            </div>
            </div>
            <div className="panel-footer">Backend simulation counts only.</div>
          </section>

          <section className="panel" aria-label="Parametre Duyarlılığı">
            <div className="panel-header">
              <h3>Parametre Duyarlılığı</h3>
              <span className="panel-meta">Eksensel etki</span>
            </div>
            <div className="panel-body">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sıra</th>
                  <th>Parametre</th>
                  <th>Etki</th>
                  <th>Duyarlılık</th>
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
            <div className="panel-footer">Backend sensitivity output only.</div>
          </section>
        </div>
      )}
    </div>
  )
}

