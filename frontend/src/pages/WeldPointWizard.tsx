import { FormEvent, useEffect, useState, useCallback } from 'react'
import { createWeldPoint, listWeldPoints } from '../api/client'
import type { Project, WeldPoint } from '../types/project'
import type { WeldAnalysisRequest } from '../types/weld'
import { WeldResultPanel } from '../components/engineering'
import { useAppLanguage } from '../i18n/useAppLanguage'
import {
  StackDefinitionPanel,
  makeEmptyLayer,
  type StackCount,
  type LayerDraft,
} from '../components/weld/StackDefinitionPanel'
import {
  WeldParameterPanel,
  makeEmptyParameters,
  type WeldParameterDraft,
} from '../components/weld/WeldParameterPanel'
import { ReferenceGuidancePanel } from '../components/weld/ReferenceGuidancePanel'
import type { TimeUnit } from '../components/weld/TimeInputField'
import { RISK_LEVEL_LABELS } from '../constants/riskLevel'

// ── Request builder ───────────────────────────────────────────────────────────

/**
 * Build a WeldAnalysisRequest from panel state.
 * Returns null if required fields are missing or invalid.
 * Never fabricates values — absent optional fields are omitted from payload.
 */
function buildRequest(
  stackCount: StackCount,
  layers: LayerDraft[],
  params: WeldParameterDraft,
): WeldAnalysisRequest | null {
  const layerCount = parseInt(stackCount[0], 10)
  const builtLayers = []
  for (let i = 0; i < layerCount; i++) {
    const l = layers[i]
    if (!l) return null
    const thickness = parseFloat(l.thickness_mm)
    if (!l.material_family || !l.material_subtype || isNaN(thickness) || thickness <= 0) return null
    builtLayers.push({
      material_family: l.material_family.trim(),
      material_subtype: l.material_subtype.trim(),
      thickness_mm: thickness,
      coated: l.coated,
    })
  }

  const current_ka      = parseFloat(params.current_ka)
  const force_kn        = parseFloat(params.force_kn)
  const tip_diameter_mm = parseFloat(params.tip_diameter_mm)
  const cooling_flow_lpm = parseFloat(params.cooling_flow_lpm)
  const cooling_temp_c  = parseFloat(params.cooling_temp_c)

  if (
    isNaN(current_ka) || isNaN(force_kn) || isNaN(tip_diameter_mm) ||
    isNaN(cooling_flow_lpm) || isNaN(cooling_temp_c) ||
    params.weld_cycles   === undefined ||
    params.squeeze_cycles === undefined ||
    params.hold_cycles   === undefined
  ) return null

  const layer1 = builtLayers[0]
  const req: WeldAnalysisRequest = {
    material_family:   layer1.material_family,
    material_subtype:  layer1.material_subtype,
    stack_count:       stackCount,
    layers:            builtLayers,
    current_ka,
    weld_cycles:       params.weld_cycles,
    force_kn,
    tip_diameter_mm,
    squeeze_cycles:    params.squeeze_cycles,
    hold_cycles:       params.hold_cycles,
    cooling_flow_lpm,
    cooling_temp_c,
    dc_current:        params.dc_current,
    adhesive:          params.adhesive,
    shunt_risk:        params.shunt_risk,
  }

  // Optional fields — omit when not provided (→ NOT_EVALUATED on backend)
  if (params.approach_cycles !== undefined) req.approach_cycles = params.approach_cycles
  if (params.cooling_cycles  !== undefined) req.cooling_cycles  = params.cooling_cycles
  const air = parseFloat(params.air_pressure_bar)
  if (!isNaN(air))                          req.air_pressure_bar = air

  return req
}

// ── Component ─────────────────────────────────────────────────────────────────

export function WeldPointWizard({ project, onBack }: { project: Project; onBack: () => void }) {
  const { t } = useAppLanguage()

  const [points,    setPoints]    = useState<WeldPoint[]>([])
  const [pointCode, setPointCode] = useState('W001')
  const [partNo,    setPartNo]    = useState('')
  const [message,   setMessage]   = useState('')
  const [busy,      setBusy]      = useState(false)

  // Stack state — no silent defaults
  const [stackCount, setStackCount] = useState<StackCount>('2T')
  const [layers, setLayers] = useState<LayerDraft[]>([makeEmptyLayer(), makeEmptyLayer()])

  // Parameter state — all undefined/empty
  const [params, setParams] = useState<WeldParameterDraft>(makeEmptyParameters)

  // Time unit display mode
  const [timeUnit, setTimeUnit] = useState<TimeUnit>('cycle')

  // Last analysis result (from saved weld point)
  const [lastResult, setLastResult] = useState<WeldPoint['analysis_result'] | null>(null)

  async function refresh() { setPoints(await listWeldPoints(project.id)) }
  useEffect(() => { refresh().catch(() => setMessage('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.')) }, [project.id])

  const handleStackCountChange = useCallback((sc: StackCount) => {
    setStackCount(sc)
    const n = parseInt(sc[0], 10)
    setLayers((prev) => {
      if (prev.length === n) return prev
      if (prev.length < n) return [...prev, ...Array.from({ length: n - prev.length }, makeEmptyLayer)]
      return prev.slice(0, n)
    })
    setLastResult(null)
  }, [])

  const handleLayerChange = useCallback((index: number, layer: LayerDraft) => {
    setLayers((prev) => { const next = [...prev]; next[index] = layer; return next })
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    const req = buildRequest(stackCount, layers, params)
    if (!req) return
    setBusy(true)
    try {
      const created = await createWeldPoint(project.id, {
        point_code: pointCode, part_no: partNo, criticality: 'Standart', analysis_input: req,
      })
      setMessage(`Kaydedildi: ${created.point_code} — skor %${created.analysis_result.score.toFixed(0)}`)
      setLastResult(created.analysis_result)
      await refresh()
    } catch (err) {
      setMessage('Backend connection unavailable. Engineering data could not be saved. Verify the API service and retry.')
    } finally { setBusy(false) }
  }

  const canSubmit = buildRequest(stackCount, layers, params) !== null && !busy

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
        <form className="panel" onSubmit={submit} aria-label="Weld point entry" noValidate>
          <div className="panel-header"><h3>Weld-point parameters</h3><span className="panel-meta">step 1 · definition</span></div>
          <div className="panel-body">
            <div className="ws-zone-label">Point identity ┬À welding parameters</div>
            <div className="grid-2">
              <div className="field"><label htmlFor="wp-code">Nokta ID</label><input id="wp-code" value={pointCode} onChange={(e) => setPointCode(e.target.value)} required /></div>
              <div className="field"><label htmlFor="wp-part">Parça No</label><input id="wp-part" value={partNo} onChange={(e) => setPartNo(e.target.value)} placeholder="ör. P-1092" /></div>
            </div>

            {/* Stack definition — replaces silent baseInput defaults */}
            <StackDefinitionPanel
              t={t.stackDefinition}
              stackCount={stackCount}
              layers={layers}
              onStackCountChange={handleStackCountChange}
              onLayerChange={handleLayerChange}
            />

            {/* Parameter inputs — all 13 supported fields, dual cycle/ms */}
            <WeldParameterPanel
              t={t.parameterPanel}
              params={params}
              timeUnit={timeUnit}
              onTimeUnitChange={setTimeUnit}
              onChange={setParams}
            />

            <div style={{ marginTop: 'var(--sp-4)' }}>
              <button className="btn btn-primary" type="submit" disabled={!canSubmit}>
                {busy ? t.parameterPanel.analyzing : 'Analiz Et ve Kaydet'}
              </button>
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
                    <td><span className={`badge ${p.analysis_result.risk_level === 'LOW' ? 'ok' : 'warn'}`}>{RISK_LEVEL_LABELS[p.analysis_result.risk_level] ?? p.analysis_result.risk_level}</span></td>
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

