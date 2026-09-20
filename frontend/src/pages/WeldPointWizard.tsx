import { FormEvent, useEffect, useState } from 'react'
import { createWeldPoint, listWeldPoints } from '../api/client'
import type { Project, WeldPoint } from '../types/project'
import type { WeldAnalysisRequest } from '../types/weld'

const baseInput: WeldAnalysisRequest = {
  material_family: 'Düşük / Orta Karbonlu Çelik',
  material_subtype: 'Düşük karbonlu çelik',
  stack_count: '2T',
  layers: [
    { material_family: 'Düşük / Orta Karbonlu Çelik', material_subtype: 'Düşük karbonlu çelik', thickness_mm: 1, coated: false },
    { material_family: 'Düşük / Orta Karbonlu Çelik', material_subtype: 'Düşük karbonlu çelik', thickness_mm: 1, coated: false },
  ],
  current_ka: 8, weld_cycles: 12, force_kn: 3, tip_diameter_mm: 6,
  squeeze_cycles: 15, hold_cycles: 15, cooling_flow_lpm: 6, cooling_temp_c: 20,
  dc_current: true, adhesive: false, shunt_risk: false,
}

export function WeldPointWizard({ project, onBack }: { project: Project; onBack: () => void }) {
  const [points, setPoints] = useState<WeldPoint[]>([])
  const [pointCode, setPointCode] = useState('W001')
  const [partNo, setPartNo] = useState('')
  const [input, setInput] = useState(baseInput)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function refresh() { setPoints(await listWeldPoints(project.id)) }
  useEffect(() => { refresh().catch(() => setMessage('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.')) }, [project.id])

  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true)
    try {
      const created = await createWeldPoint(project.id, {
        point_code: pointCode, part_no: partNo, criticality: 'Standart', analysis_input: input,
      })
      setMessage(`Kaydedildi: ${created.point_code} — skor %${created.analysis_result.score.toFixed(0)}`)
      await refresh()
    } catch {
      setMessage('Backend connection unavailable. Engineering data could not be saved. Verify the API service and retry.')
    } finally { setBusy(false) }
  }

  return (
    <div className="page active">
      <div className="ws-kicker">Production · Spot Welding Parametre Analysis</div>
      <header className="page-header">
        <div>
          <h1>{project.project_code} — {project.project_name}</h1>
          <p className="subtitle">Weld-point definition workspace · project context preserved</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary btn-sm" onClick={onBack}>← Projelere Dön</button>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Project context">
        <span className="ctx-chip accent">Project: <strong>{project.project_code}</strong></span>
        <span className="ctx-chip">Status: <strong>{project.status}</strong></span>
        <span className="ctx-chip">Customer: <strong>{project.customer || '—'}</strong></span>
      </div>
      {message && <div className="alert info" role="status"><div><div className="alert-text">{message}</div></div></div>}
      <div className="ws-grid-main">
        <form className="panel" onSubmit={submit} aria-label="Weld point entry">
          <div className="panel-header"><h3>Weld-point parameters</h3><span className="panel-meta">step 1 · definition</span></div>
          <div className="panel-body">
          <div className="ws-zone-label">Point identity · welding parameters</div>
          <div className="grid-2">
            <div className="field"><label htmlFor="wp-code">Nokta ID</label><input id="wp-code" value={pointCode} onChange={(e) => setPointCode(e.target.value)} required /></div>
            <div className="field"><label htmlFor="wp-part">Parça No</label><input id="wp-part" value={partNo} onChange={(e) => setPartNo(e.target.value)} placeholder="ör. P-1092" /></div>
            <div className="field"><label htmlFor="wp-ka">Akım (kA)</label><input id="wp-ka" type="number" value={input.current_ka} onChange={(e) => setInput({ ...input, current_ka: Number(e.target.value) })} /></div>
            <div className="field"><label htmlFor="wp-cyc">Süre (cyc)</label><input id="wp-cyc" type="number" value={input.weld_cycles} onChange={(e) => setInput({ ...input, weld_cycles: Number(e.target.value) })} /></div>
            <div className="field"><label htmlFor="wp-kn">Kuvvet (kN)</label><input id="wp-kn" type="number" value={input.force_kn} onChange={(e) => setInput({ ...input, force_kn: Number(e.target.value) })} /></div>
          </div>
          <div style={{ marginTop: 'var(--sp-4)' }}>
            <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Kaydediliyor…' : 'Analiz Et ve Kaydet'}</button>
          </div>
          </div>
          <div className="panel-footer">Backend evaluation runs on save; project context preserved.</div>
        </form>

        <section className="panel" aria-label="Registered weld points">
          <div className="panel-header">
            <h3>Registered weld points</h3>
            <span className="panel-meta">{points.length} point(s)</span>
          </div>
          <div className="panel-body">
          <div className="ws-zone-label">Step 2 · traceability · backend evaluations only</div>
          {points.length === 0 ? (
            <div className="ws-empty" role="status"><span className="empty-glyph" aria-hidden="true">WP</span><strong>No weld points registered</strong><span className="ws-empty-hint">No weld points are registered for this project yet. Define the first point using the adjacent form.</span><span className="empty-action">Next action: define and save the first weld point.</span></div>
          ) : (
            <table className="data-table">
              <thead>
                <tr><th>Nokta ID</th><th>Parça No</th><th>Skor</th><th>Risk</th><th>Rev.</th></tr>
              </thead>
              <tbody>
                {points.map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{p.point_code}</td>
                    <td>{p.part_no || '—'}</td>
                    <td className="mono">%{p.analysis_result.score.toFixed(0)}</td>
                    <td><span className={`badge ${p.analysis_result.risk_level.toLowerCase().includes('düşük') ? 'ok' : 'warn'}`}>{p.analysis_result.risk_level}</span></td>
                    <td className="mono">{p.version_no}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          </div>
          <div className="panel-footer">Only backend-evaluated weld points are listed.</div>
        </section>
      </div>
    </div>
  )
}

