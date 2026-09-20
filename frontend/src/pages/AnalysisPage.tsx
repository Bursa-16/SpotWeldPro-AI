import { useMemo, useState } from 'react'
import { analyzeWeld } from '../api/client'
import type { WeldAnalysisRequest, WeldAnalysisResponse, LayerInput } from '../types/weld'
import type { ReactNode } from 'react'
const baseLayer: LayerInput = { material_family: 'Düşük / Orta Karbonlu Çelik', material_subtype: 'Düşük karbonlu çelik', thickness_mm: 1, coated: false }
const base: WeldAnalysisRequest = { ...baseLayer, stack_count: '2T', layers: [{ ...baseLayer }, { ...baseLayer }], current_ka: 8, weld_cycles: 12, force_kn: 3, tip_diameter_mm: 6, squeeze_cycles: 15, hold_cycles: 15, cooling_flow_lpm: 6, cooling_temp_c: 20, dc_current: true, adhesive: false, shunt_risk: false }

function riskState(risk: string): 'ok' | 'warn' | 'danger' {
  const r = risk.toLowerCase()
  if (r.includes('yüksek') || r.includes('high')) return 'danger'
  if (r.includes('orta') || r.includes('medium') || r.includes('review')) return 'warn'
  return 'ok'
}

function statusBadge(status: string): 'ok' | 'warn' | 'danger' | 'neutral' {
  const s = status.toLowerCase()
  if (s.includes('uygun de') || s.includes('not compliant') || s.includes('fail')) return 'danger'
  if (s.includes('düşük') || s.includes('yüksek') || s.includes('review')) return 'warn'
  if (s.includes('uygun')) return 'ok'
  return 'neutral'
}

const PRIMARY_FIELDS: Array<[string, keyof WeldAnalysisRequest, string]> = [
  ['Akım (kA)', 'current_ka', 'kA'],
  ['Kaynak süresi', 'weld_cycles', 'çevrim'],
  ['Kuvvet (kN)', 'force_kn', 'kN'],
  ['Squeeze süresi', 'squeeze_cycles', 'çevrim'],
  ['Hold / Soğutma', 'hold_cycles', 'çevrim'],
  ['Uç çapı', 'tip_diameter_mm', 'mm'],
]

export function AnalysisPage() {
  const [p, setP] = useState<WeldAnalysisRequest>(base)
  const [r, setR] = useState<WeldAnalysisResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const totalThickness = useMemo(() => p.layers.reduce((sum, l) => sum + (Number(l.thickness_mm) || 0), 0), [p.layers])

  function setStack(n: 2 | 3 | 4) {
    setP((prev) => {
      const layers = [...prev.layers]
      while (layers.length < n) layers.push({ ...(layers[layers.length - 1] ?? baseLayer) })
      return { ...prev, stack_count: `${n}T` as WeldAnalysisRequest['stack_count'], layers: layers.slice(0, n) }
    })
  }

  function setLayer(i: number, patch: Partial<LayerInput>) {
    setP((prev) => {
      const layers = prev.layers.map((l, li) => (li === i ? { ...l, ...patch } : l))
      const next: WeldAnalysisRequest = { ...prev, layers }
      if (i === 0 && (patch.material_family || patch.material_subtype)) {
        if (patch.material_family) next.material_family = patch.material_family
        if (patch.material_subtype) next.material_subtype = patch.material_subtype
      }
      return next
    })
  }

  async function run() {
    try {
      setBusy(true); setErr(''); setR(await analyzeWeld(p))
    } catch {
      setErr('Engineering data could not be loaded. Verify the API service and retry.')
    } finally {
      setBusy(false)
    }
  }

  function num(key: keyof WeldAnalysisRequest, label: string, unit: string): ReactNode {
    return (
      <div className="field" key={key}>
        <label>{label} <span className="field-unit">{unit}</span></label>
        <input type="number" value={p[key] as number} onChange={(e) => setP({ ...p, [key]: Number(e.target.value) })} />
      </div>
    )
  }

  function check(key: 'dc_current' | 'adhesive' | 'shunt_risk', label: string): ReactNode {
    return (
      <label className="check-row" key={key}>
        <input type="checkbox" checked={p[key]} onChange={(e) => setP({ ...p, [key]: e.target.checked })} />
        <span>{label}</span>
      </label>
    )
  }
  return <div className="page active">
    <div className="ws-kicker">Production · Spot Welding Parametre Analysis</div>
    <header className="page-header">
      <div>
        <h1>Weld Quality Analysis</h1>
        <p className="subtitle">Rule-governed spot weld evaluation — deterministic limits with model support</p>
      </div>
      <div className="page-actions"><button className="btn btn-primary" onClick={run} disabled={busy}>{busy?'Analyzing…':'Run analysis'}</button></div>
    </header>
    <div className="ws-context-bar" aria-label="Engineering context">
      <span className="ctx-chip accent">Authority: <strong>deterministic rules</strong></span>
      <span className="ctx-chip">Stack: <strong>{p.stack_count}</strong></span>
      <span className="ctx-chip">Material: <strong>{p.material_family}</strong></span>
      <span className="ctx-chip">Total thickness: <strong>{totalThickness.toFixed(2)} mm</strong></span>
    </div>
    {err && <div className="alert danger" role="alert"><div><div className="alert-title">Backend connection unavailable</div><div className="alert-text">{err}</div></div></div>}
    <div className="anx-grid">
      <section className="panel" aria-label="Engineering inputs">
        <div className="panel-header"><h3>Engineering inputs</h3><span className="panel-meta">stack · parameters</span></div>
        <div className="panel-body">
          <div className="ws-zone-label">A · Stack &amp; material</div>
          <div className="seg-group" role="group" aria-label="Stack count">
            {(['2T', '3T', '4T'] as const).map((sc) => (
              <button
                type="button"
                key={sc}
                className={'seg-btn' + (p.stack_count === sc ? ' active' : '')}
                aria-pressed={p.stack_count === sc}
                onClick={() => setStack(Number(sc[0]) as 2 | 3 | 4)}
              >{sc}</button>
            ))}
          </div>
          <div className="sheet-stack">
            {p.layers.map((layer, i) => (
              <div className="sheet-card" key={i}>
                <div className="sheet-head"><span>Sheet {i + 1}</span>{i === 0 && <span className="sheet-tag">primary</span>}</div>
                <div className="sheet-fields">
                  <div className="field"><label>Malzeme ailesi</label><input value={layer.material_family} onChange={(e) => setLayer(i, { material_family: e.target.value })} /></div>
                  <div className="field"><label>Malzeme alt tipi</label><input value={layer.material_subtype} onChange={(e) => setLayer(i, { material_subtype: e.target.value })} /></div>
                  <div className="field"><label>Kalınlık <span className="field-unit">mm</span></label><input type="number" step="0.1" min="0" value={layer.thickness_mm} onChange={(e) => setLayer(i, { thickness_mm: Number(e.target.value) })} /></div>
                  <label className="check-row"><input type="checkbox" checked={layer.coated} onChange={(e) => setLayer(i, { coated: e.target.checked })} /><span>Kaplamalı</span></label>
                </div>
              </div>
            ))}
          </div>
          <div className="total-stack">
            <span>Total stack thickness</span>
            <strong>{totalThickness.toFixed(2)} mm</strong>
          </div>
          <div className="ws-zone-label">B · Primary welding parameters</div>
          <div className="param-grid">
            {PRIMARY_FIELDS.map(([label, key, unit]) => num(key, label, unit))}
          </div>
          <div className="pulse-row" role="note">
            <span>Pulse / Sequence</span>
            <span className="badge neutral">Planned — backend extension required</span>
          </div>
          <details className="adv-details">
            <summary>Advanced process context <span className="adv-hint">cooling · mode · adhesive · shunt</span></summary>
            <div className="adv-body">
              <div className="param-grid">
                {num('cooling_flow_lpm', 'Soğutma debisi', 'L/dk')}
                {num('cooling_temp_c', 'Soğutma suyu sıcaklığı', '°C')}
              </div>
              <div className="check-grid">
                {check('dc_current', 'DC akım modu')}
                {check('adhesive', 'Yapıştırıcı mevcut')}
                {check('shunt_risk', 'Shunt riski')}
              </div>
            </div>
          </details>
        </div>
        <div className="panel-footer">Inputs are evaluated by backend deterministic rules only. Top-level material follows Sheet 1.</div>
      </section>
      <section className="panel" aria-label="Engineering result">
        <div className="panel-header"><h3>Engineering result</h3>{r && <span className={`badge ${riskState(r.risk_level)}`}>{r.risk_level}</span>}</div>
        <div className="panel-body">
        <div className="ws-zone-label">Engineering evaluation · result · traceability</div>
        {!r && !busy && <div className="ws-empty" role="status"><span className="empty-glyph" aria-hidden="true">RQ</span><strong>No analysis result yet</strong><span className="ws-empty-hint">Run analysis to generate the governed engineering result. Empty state is expected before the first backend evaluation.</span><span className="empty-action">Next action: Run analysis with the current parameter set.</span></div>}
        {busy && <div className="state-msg" role="status"><div className="spinner" aria-hidden="true"/><span>Evaluating governed rules…</span></div>}
        {r && !busy && <>
          <div className="grid-2">
            <article className="metric-card"><span className="metric-label">Quality score</span><strong className="metric-value">%{r.score.toFixed(0)}</strong></article>
            <article className="metric-card"><span className="metric-label">Norm compliance</span><strong className="metric-value">%{r.compliance_summary.score.toFixed(0)}</strong></article>
            <article className="metric-card"><span className="metric-label">Target nugget</span><strong className="metric-value">{r.nugget_opt_mm.toFixed(2)}<span className="metric-unit"> mm</span></strong><span className="metric-sub">min {r.nugget_min_mm.toFixed(2)} mm</span></article>
            <article className="metric-card"><span className="metric-label">Prediction</span><strong className="metric-value">{r.selected_prediction_mm!=null ? <>{r.selected_prediction_mm.toFixed(2)}<span className="metric-unit"> mm</span></> : '—'}</strong></article>
          </div>
          {r.selected_model && <div className="trace-block" style={{marginTop:'var(--sp-3)'}}>
            <div className="trace-row"><span className="label">Model / rule basis</span><span className="value">{r.selected_model}</span></div>
            <div className="trace-row"><span className="label">Rules evaluated</span><span className="value">{r.compliance_summary.passed??0} passed / {r.compliance_summary.failed??0} failed / {r.compliance_summary.review??0} review</span></div>
          </div>}
          {r.risks.length>0 && <div style={{marginTop:'var(--sp-4)'}}>
            <div className="panel-header"><h3>Risk findings</h3></div>
            {r.risks.map(x=><div className="alert warn" key={x.title}><div className="alert-body"><div className="alert-title">{x.title}</div><div className="alert-text">{x.detail}</div></div></div>)}
          </div>}
          {r.actions.length > 0 && <div style={{ marginTop: 'var(--sp-2)' }}>
            <div className="panel-header"><h3>Recommended actions</h3></div>
            <ul className="action-list">{r.actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
          </div>}
          {r.recommended_ranges && r.recommended_ranges.length > 0 && (
            <div style={{ marginTop: 'var(--sp-4)' }}>
              <div className="panel-header"><h3>Recommended ranges</h3><span className="panel-meta">governed</span></div>
              <table className="data-table">
                <thead><tr><th>Parametre</th><th>Mevcut</th><th>Önerilen aralık</th><th>Durum</th></tr></thead>
                <tbody>
                  {r.recommended_ranges.map((row, i) => (
                    <tr key={i}>
                      <td>{row.Parametre}</td>
                      <td className="mono">{row.Mevcut} {row.Birim}</td>
                      <td className="mono">{row['Önerilen Min']} – {row['Önerilen Maks']} {row.Birim}</td>
                      <td><span className={`badge ${statusBadge(row.Durum)}`}>{row.Durum}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {r.compliance_results && r.compliance_results.length > 0 && (
            <div style={{ marginTop: 'var(--sp-4)' }}>
              <div className="panel-header"><h3>Rule compliance detail</h3><span className="panel-meta">{r.compliance_results.length} rule(s)</span></div>
              <div className="rule-rows">
                {r.compliance_results.map((row, i) => (
                  <div className="rule-row" key={i}>
                    <span className={`badge ${statusBadge(row.status)}`}>{row.status}</span>
                    <span className="rule-name">{row.rule_name}</span>
                    <span className="rule-detail">{row.parameter} · {row.actual_value} → {row.expected}</span>
                    <span className="rule-src">{row.source_name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {r.compliance_conflicts && r.compliance_conflicts.length > 0 && (
            <div style={{ marginTop: 'var(--sp-4)' }}>
              {r.compliance_conflicts.map((c, i) => (
                <div className="alert warn" key={i}>
                  <div className="alert-body">
                    <div className="alert-title">Rule conflict: {c.parameter}</div>
                    <div className="alert-text">{c.winner_source} esas alındı — {c.challenger_source} ile çakışma. {c.decision}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {r.model_results && r.model_results.length > 0 && (
            <div style={{ marginTop: 'var(--sp-4)' }}>
              <div className="panel-header"><h3>Model evaluation</h3><span className="panel-meta">model registry</span></div>
              <table className="data-table">
                <thead><tr><th>Model</th><th>Prediction</th></tr></thead>
                <tbody>
                  {r.model_results.map((m, i) => (
                    <tr key={i}>
                      <td>{m.model_name ?? '—'}</td>
                      <td className="mono">{m.prediction_mm != null ? `${Number(m.prediction_mm).toFixed(2)} mm` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>}
        </div>
        <div className="panel-footer">Traceability: backend deterministic output only.</div>
      </section>
      <aside className="panel anx-inspector" aria-label="Traceability and governed context">
        <div className="panel-header"><h3>Traceability</h3><span className="panel-meta">governed context</span></div>
        <div className="panel-body">
          <div className="inspector-row"><span>Analysis model</span><strong>{p.material_family} · {p.material_subtype}</strong></div>
          <div className="inspector-row"><span>Stack</span><strong>{p.stack_count} · {p.layers.map((l) => l.thickness_mm).join(' + ')} mm</strong></div>
          <div className="inspector-row"><span>Total thickness</span><strong className="mono">{totalThickness.toFixed(2)} mm</strong></div>
          <div className="inspector-row"><span>Current mode</span><strong>{p.dc_current ? 'DC' : 'AC'}</strong></div>
          <div className="inspector-row"><span>Selected model</span><strong className="mono">{r?.selected_model ?? '—'}</strong></div>
          <div className="inspector-row"><span>Compliance status</span><strong>{r ? `${r.compliance_summary.passed ?? 0}P / ${r.compliance_summary.failed ?? 0}F · %${r.compliance_summary.score.toFixed(0)}` : '—'}</strong></div>
          <div className="inspector-sep" />
          <div className="inspector-row muted"><span>Parameter revision</span><strong>—</strong></div>
          <div className="inspector-row muted"><span>Rule revision</span><strong>—</strong></div>
          <div className="inspector-row muted"><span>Evaluation ID</span><strong>—</strong></div>
          <div className="inspector-row muted"><span>Evidence source</span><strong>—</strong></div>
          <div className="inspector-row muted"><span>Approval state</span><strong>—</strong></div>
          <div className="inspector-row muted"><span>Readiness</span><strong>—</strong></div>
        </div>
        <div className="panel-footer">Governed identifiers populate as registry/evidence integration lands. No values are fabricated.</div>
      </aside>
    </div>
  </div>
}
