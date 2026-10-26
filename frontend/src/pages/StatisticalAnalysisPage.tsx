import { useState, useId } from 'react'
import { useAppLanguage } from '../i18n/useAppLanguage'
import {
  taguchiDesign, taguchiAnalyze, anovaAnalyze,
  type TaguchiDesignResponse, type TaguchiAnalyzeResponse,
  type ANOVAAnalyzeResponse, type ANOVARowOut, type FactorEffectOut,
} from '../api/statisticalAnalysis'

// ── Types ──────────────────────────────────────────────────────────────────────
type Tab = 'taguchi' | 'anova'
type TaguchiStep = 'config' | 'designed' | 'analyzed'

interface FactorDraft {
  name: string
  unit: string
  levelsRaw: string
}

interface GroupDraft {
  name: string
  valuesRaw: string
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function parseLevels(raw: string): number[] {
  return raw.split(',').map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n))
}

function parseValues(raw: string): number[] {
  return raw.split(',').map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n))
}

function fmtNum(v: number | null | undefined, decimals = 4): string {
  if (v == null) return '—'
  return v.toFixed(decimals)
}

function pLabel(p: number | null | undefined): string {
  if (p == null) return '—'
  if (p < 0.001) return '< 0.001'
  return p.toFixed(3)
}

function arrayCapacity(at: string): { levels: number; maxFactors: number } {
  switch (at) {
    case 'L4':  return { levels: 2, maxFactors: 3 }
    case 'L9':  return { levels: 3, maxFactors: 4 }
    case 'L16': return { levels: 2, maxFactors: 15 }
    case 'L27': return { levels: 3, maxFactors: 13 }
    default:    return { levels: 2, maxFactors: 3 }
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────────
function ANOVATable({ rows, p }: {
  rows: ANOVARowOut[]
  p: ReturnType<typeof useAppLanguage>['t']['statisticalPage']
}) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="stat-table" aria-label={p.anovaTableTitle}>
        <thead>
          <tr>
            <th>{p.colSource}</th>
            <th style={{ textAlign: 'right' }}>{p.colSS}</th>
            <th style={{ textAlign: 'right' }}>{p.colDF}</th>
            <th style={{ textAlign: 'right' }}>{p.colMS}</th>
            <th style={{ textAlign: 'right' }}>{p.colF}</th>
            <th style={{ textAlign: 'right' }}>{p.colP}</th>
            <th style={{ textAlign: 'right' }}>{p.colPct}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={row.source.startsWith('Toplam') || row.source.startsWith('Total') ? 'stat-total-row' : ''}>
              <td>{row.source}{row.note ? <span className="stat-note" title={row.note}> ⚠</span> : null}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{fmtNum(row.ss, 3)}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{row.df}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{fmtNum(row.ms, 4)}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{fmtNum(row.f_statistic, 3)}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{pLabel(row.p_value)}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{row.contribution_pct != null ? row.contribution_pct.toFixed(1) + '%' : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main Effect SVG Charts ─────────────────────────────────────────────────────
function MainEffectChart({ fe, p }: {
  fe: FactorEffectOut
  p: ReturnType<typeof useAppLanguage>['t']['statisticalPage']
}) {
  const W = 260, H = 130, PL = 48, PR = 12, PT = 14, PB = 36
  const chartW = W - PL - PR
  const chartH = H - PT - PB

  const snValues = fe.levels.map((l) => l.sn_ratio).filter((v) => isFinite(v))
  if (snValues.length === 0) return null

  const minSN = Math.min(...snValues)
  const maxSN = Math.max(...snValues)
  const range = maxSN - minSN || 1
  const pad = range * 0.15

  const toX = (idx: number) => PL + (idx / Math.max(fe.levels.length - 1, 1)) * chartW
  const toY = (sn: number) => PT + (1 - (sn - (minSN - pad)) / (range + 2 * pad)) * chartH

  const validLevels = fe.levels.filter((l) => isFinite(l.sn_ratio))
  const points = validLevels.map((l, i) => `${toX(i)},${toY(l.sn_ratio)}`).join(' ')

  const tickCount = 4
  const yTicks = Array.from({ length: tickCount }, (_, i) => {
    const val = minSN - pad + (i / (tickCount - 1)) * (range + 2 * pad)
    return { y: toY(val), val }
  })

  return (
    <div className="stat-chart-wrap">
      <div className="stat-chart-title">{fe.factor_name} {fe.unit ? `(${fe.unit})` : ''}</div>
      <svg width={W} height={H} aria-label={`${p.mainEffectTitle} — ${fe.factor_name}`}>
        {/* Y-axis ticks */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={PL - 4} y1={t.y} x2={PL} y2={t.y} stroke="var(--border-strong)" strokeWidth="1" />
            <text x={PL - 6} y={t.y + 4} textAnchor="end" fontSize="9" fill="var(--text-tertiary)">
              {t.val.toFixed(1)}
            </text>
          </g>
        ))}
        {/* Axes */}
        <line x1={PL} y1={PT} x2={PL} y2={PT + chartH} stroke="var(--border-strong)" strokeWidth="1" />
        <line x1={PL} y1={PT + chartH} x2={PL + chartW} y2={PT + chartH} stroke="var(--border-strong)" strokeWidth="1" />
        {/* Y-axis label */}
        <text
          x={10} y={PT + chartH / 2}
          textAnchor="middle" fontSize="9" fill="var(--text-secondary)"
          transform={`rotate(-90, 10, ${PT + chartH / 2})`}
        >
          {p.snAxisLabel}
        </text>
        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        {/* Points + X labels */}
        {validLevels.map((l, i) => (
          <g key={i}>
            <circle cx={toX(i)} cy={toY(l.sn_ratio)} r="4" fill="var(--accent)" />
            <text
              x={toX(i)} y={PT + chartH + 14}
              textAnchor="middle" fontSize="9" fill="var(--text-secondary)"
            >
              {l.level_value}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}

// ── Taguchi Tab ────────────────────────────────────────────────────────────────
function TaguchiTab() {
  const { t } = useAppLanguage()
  const p = t.statisticalPage
  const uid = useId()

  const [arrayType, setArrayType] = useState('L9')
  const [factors, setFactors] = useState<FactorDraft[]>([
    { name: '', unit: '', levelsRaw: '' },
    { name: '', unit: '', levelsRaw: '' },
    { name: '', unit: '', levelsRaw: '' },
  ])
  const [step, setStep] = useState<TaguchiStep>('config')
  const [design, setDesign] = useState<TaguchiDesignResponse | null>(null)
  const [responses, setResponses] = useState<string[]>([])
  const [snObjective, setSnObjective] = useState('larger_is_better')
  const [responseVar, setResponseVar] = useState('response')
  const [responseUnit, setResponseUnit] = useState('')
  const [result, setResult] = useState<TaguchiAnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cap = arrayCapacity(arrayType)

  function resetAll() {
    setStep('config')
    setDesign(null)
    setResult(null)
    setResponses([])
    setError(null)
  }

  function handleArrayChange(at: string) {
    setArrayType(at)
    resetAll()
    const c = arrayCapacity(at)
    setFactors((prev) => {
      const trimmed = prev.slice(0, c.maxFactors)
      const levLen = c.levels
      return trimmed.map((f) => {
        const lvs = parseLevels(f.levelsRaw)
        if (lvs.length === levLen) return f
        return { ...f, levelsRaw: '' }
      })
    })
  }

  function updateFactor(i: number, key: keyof FactorDraft, val: string) {
    setFactors((prev) => prev.map((f, idx) => idx === i ? { ...f, [key]: val } : f))
  }

  function addFactor() {
    const c = arrayCapacity(arrayType)
    if (factors.length >= c.maxFactors) return
    setFactors((prev) => [...prev, { name: '', unit: '', levelsRaw: '' }])
  }

  function removeFactor(i: number) {
    if (factors.length <= 1) return
    setFactors((prev) => prev.filter((_, idx) => idx !== i))
  }

  async function handleGenerateDesign() {
    setError(null)
    const validFactors = factors.filter((f) => f.name.trim() && parseLevels(f.levelsRaw).length === cap.levels)
    if (validFactors.length < 1) {
      setError(`Her faktörün adı ve tam olarak ${cap.levels} seviyesi olmalı.`)
      return
    }
    setLoading(true)
    try {
      const resp = await taguchiDesign({
        array_type: arrayType,
        factors: validFactors.map((f) => ({
          name: f.name.trim(),
          unit: f.unit.trim(),
          levels: parseLevels(f.levelsRaw),
        })),
      })
      setDesign(resp)
      setResponses(Array(resp.runs).fill(''))
      setStep('designed')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? String(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleAnalyze() {
    if (!design) return
    setError(null)
    const responseNums = responses.map((r) => parseFloat(r))
    if (responseNums.some((v) => isNaN(v))) {
      setError('Tüm run değerleri sayısal olmalı.')
      return
    }
    const validFactors = factors.filter((f) => f.name.trim() && parseLevels(f.levelsRaw).length === cap.levels)
    setLoading(true)
    try {
      const resp = await taguchiAnalyze({
        array_type: arrayType,
        factors: validFactors.map((f) => ({
          name: f.name.trim(),
          unit: f.unit.trim(),
          levels: parseLevels(f.levelsRaw),
        })),
        sn_objective: snObjective,
        responses: responseNums,
        response_variable: responseVar.trim() || 'response',
        response_unit: responseUnit.trim(),
      })
      setResult(resp)
      setStep('analyzed')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="stat-tab-content">
      {/* Governance notice */}
      <div className="stat-governance-note" role="note">
        <span aria-hidden="true">ℹ</span> {p.governanceNote}
      </div>

      {/* Setup panel */}
      <div className="panel">
        <div className="panel-header">
          <h3>{p.taguchiSetupTitle}</h3>
          <span className="panel-meta">{p.taguchiSetupMeta}</span>
        </div>
        <div className="panel-body">
          {/* Array type */}
          <div className="field">
            <label htmlFor={uid + '-at'}>{p.arrayTypeLabel}</label>
            <div className="stat-array-btns" role="group" aria-label={p.arrayTypeLabel}>
              {(['L4', 'L9', 'L16', 'L27'] as const).map((at) => (
                <button
                  key={at}
                  type="button"
                  className={'btn btn-sm' + (arrayType === at ? ' btn-primary' : ' btn-secondary')}
                  onClick={() => handleArrayChange(at)}
                >
                  {at}
                </button>
              ))}
            </div>
            <span className="field-unit">
              {cap.levels} seviye / maks. {cap.maxFactors} faktör
            </span>
          </div>

          {/* Factors */}
          <div>
            <div className="stat-section-label">{p.factorsTitle}</div>
            {factors.map((f, i) => (
              <div key={i} className="stat-factor-row">
                <div className="form-grid" style={{ flex: 1 }}>
                  <div className="field">
                    <label htmlFor={uid + '-fn-' + i}>{p.factorNameLabel}</label>
                    <input
                      id={uid + '-fn-' + i}
                      type="text"
                      value={f.name}
                      placeholder="örn. Akım"
                      onChange={(e) => updateFactor(i, 'name', e.target.value)}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={uid + '-fu-' + i}>{p.factorUnitLabel}</label>
                    <input
                      id={uid + '-fu-' + i}
                      type="text"
                      value={f.unit}
                      placeholder="kA"
                      onChange={(e) => updateFactor(i, 'unit', e.target.value)}
                    />
                  </div>
                  <div className="field" style={{ flex: 2 }}>
                    <label htmlFor={uid + '-fl-' + i}>
                      {p.factorLevelsLabel}
                      <span className="field-unit" style={{ marginLeft: 6 }}>({cap.levels} değer)</span>
                    </label>
                    <input
                      id={uid + '-fl-' + i}
                      type="text"
                      value={f.levelsRaw}
                      placeholder={p.factorLevelsHint}
                      onChange={(e) => updateFactor(i, 'levelsRaw', e.target.value)}
                    />
                  </div>
                </div>
                {factors.length > 1 && (
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary stat-remove-btn"
                    onClick={() => removeFactor(i)}
                    aria-label={p.removeFactor}
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            {factors.length < cap.maxFactors && (
              <button type="button" className="btn btn-sm btn-secondary" onClick={addFactor}>
                + {p.addFactor}
              </button>
            )}
          </div>

          {error && <div className="field-error" role="alert">{error}</div>}

          <div className="stat-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleGenerateDesign}
              disabled={loading}
            >
              {loading ? p.generating : p.generateDesign}
            </button>
            {step !== 'config' && (
              <button type="button" className="btn btn-secondary" onClick={resetAll}>
                {p.resetBtn}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Experiment matrix */}
      {design && (
        <div className="panel">
          <div className="panel-header">
            <h3>{p.matrixTitle}</h3>
            <span className="panel-meta">{p.matrixMeta} — {design.array_type} ({design.runs} run)</span>
          </div>
          <div className="panel-body">
            {design.saturated && (
              <div className="badge warn" role="alert">{p.saturatedWarning}</div>
            )}
            <div style={{ overflowX: 'auto' }}>
              <table className="stat-table">
                <thead>
                  <tr>
                    <th>{p.colRun}</th>
                    {Object.keys(design.experiment_matrix[0]?.factor_values ?? {}).map((k) => (
                      <th key={k} style={{ textAlign: 'right' }}>{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {design.experiment_matrix.map((run) => (
                    <tr key={run.run_number}>
                      <td>{run.run_number}</td>
                      {Object.values(run.factor_values).map((v, j) => (
                        <td key={j} style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{v}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {design.warnings.map((w, i) => (
              <div key={i} className="badge warn">{w}</div>
            ))}
          </div>
        </div>
      )}

      {/* Response entry */}
      {design && step !== 'config' && (
        <div className="panel">
          <div className="panel-header">
            <h3>{p.responseTitle}</h3>
            <span className="panel-meta">{p.responseMeta}</span>
          </div>
          <div className="panel-body">
            <div className="form-grid">
              <div className="field">
                <label htmlFor={uid + '-snobj'}>{p.snObjectiveLabel}</label>
                <select
                  id={uid + '-snobj'}
                  value={snObjective}
                  onChange={(e) => setSnObjective(e.target.value)}
                >
                  <option value="larger_is_better">{p.snLtb}</option>
                  <option value="smaller_is_better">{p.snStb}</option>
                  <option value="nominal_is_best">{p.snNtb}</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor={uid + '-rvar'}>{p.responseVarLabel}</label>
                <input
                  id={uid + '-rvar'}
                  type="text"
                  value={responseVar}
                  placeholder="response"
                  onChange={(e) => setResponseVar(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor={uid + '-runit'}>{p.responseUnitLabel}</label>
                <input
                  id={uid + '-runit'}
                  type="text"
                  value={responseUnit}
                  placeholder="mm"
                  onChange={(e) => setResponseUnit(e.target.value)}
                />
              </div>
            </div>

            <div className="stat-responses-grid">
              {responses.map((val, i) => (
                <div key={i} className="field stat-response-field">
                  <label htmlFor={uid + '-resp-' + i}>Run {i + 1}</label>
                  <input
                    id={uid + '-resp-' + i}
                    type="number"
                    step="any"
                    value={val}
                    onChange={(e) => setResponses((prev) => prev.map((v, idx) => idx === i ? e.target.value : v))}
                  />
                </div>
              ))}
            </div>

            {error && <div className="field-error" role="alert">{error}</div>}

            <div className="stat-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? p.analyzing : p.analyzeBtn}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Analysis results */}
      {result && step === 'analyzed' && (
        <>
          <div className="panel">
            <div className="panel-header">
              <h3>{p.resultsTitle}</h3>
              <span className="panel-meta">{p.resultsMeta}</span>
            </div>
            <div className="panel-body">
              <div className="stat-summary-row">
                <div className="stat-kv"><span className="stat-kv-label">{p.grandMeanResponse}</span><span className="stat-kv-value">{fmtNum(result.grand_mean_response, 4)}</span></div>
                <div className="stat-kv"><span className="stat-kv-label">{p.grandMeanSN}</span><span className="stat-kv-value">{fmtNum(result.grand_mean_sn, 4)} dB</span></div>
                {result.additive_prediction != null && (
                  <div className="stat-kv"><span className="stat-kv-label">{p.additivePrediction}</span><span className="stat-kv-value">{fmtNum(result.additive_prediction, 4)}</span></div>
                )}
              </div>
              {result.additive_prediction_note && (
                <div className="badge info" style={{ alignSelf: 'flex-start' }}>{result.additive_prediction_note}</div>
              )}
            </div>
          </div>

          {/* Optimal settings */}
          <div className="panel">
            <div className="panel-header">
              <h3>{p.optimalTitle}</h3>
            </div>
            <div className="panel-body">
              <div className="stat-optimal-grid">
                {result.optimal_settings.map((os, i) => (
                  <div key={i} className="stat-optimal-card">
                    <div className="stat-optimal-name">{os.factor_name}</div>
                    <div className="stat-optimal-val">{os.optimal_level_value} {os.unit}</div>
                    <div className="stat-optimal-meta">{p.levelLabel} {os.optimal_level_index}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main effect charts */}
          <div className="panel">
            <div className="panel-header">
              <h3>{p.mainEffectTitle}</h3>
              <span className="panel-meta">{p.mainEffectMeta}</span>
            </div>
            <div className="panel-body">
              <div className="stat-charts-row">
                {result.factor_effects.map((fe, i) => (
                  <MainEffectChart key={i} fe={fe} p={p} />
                ))}
              </div>
            </div>
          </div>

          {/* ANOVA table */}
          <div className="panel">
            <div className="panel-header">
              <h3>{p.anovaTableTitle}</h3>
              <span className="panel-meta">{p.anovaMeta}</span>
            </div>
            <div className="panel-body">
              <ANOVATable rows={result.anova_table} p={p} />
            </div>
          </div>

          {result.warnings.length > 0 && (
            <div className="panel">
              <div className="panel-body">
                {result.warnings.map((w, i) => (
                  <div key={i} className="badge warn">{w}</div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ── ANOVA Tab ──────────────────────────────────────────────────────────────────
function AnovaTab() {
  const { t } = useAppLanguage()
  const p = t.statisticalPage
  const uid = useId()

  const [factorName, setFactorName] = useState('')
  const [responseVar, setResponseVar] = useState('response')
  const [responseUnit, setResponseUnit] = useState('')
  const [groups, setGroups] = useState<GroupDraft[]>([
    { name: '', valuesRaw: '' },
    { name: '', valuesRaw: '' },
  ])
  const [result, setResult] = useState<ANOVAAnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function addGroup() {
    setGroups((prev) => [...prev, { name: '', valuesRaw: '' }])
  }

  function removeGroup(i: number) {
    if (groups.length <= 2) return
    setGroups((prev) => prev.filter((_, idx) => idx !== i))
  }

  function updateGroup(i: number, key: keyof GroupDraft, val: string) {
    setGroups((prev) => prev.map((g, idx) => idx === i ? { ...g, [key]: val } : g))
  }

  async function handleRunAnova() {
    setError(null)
    const validGroups = groups.filter((g) => g.name.trim() && parseValues(g.valuesRaw).length > 0)
    if (validGroups.length < 2) {
      setError('En az 2 geçerli grup gerekli (ad + değerler).')
      return
    }
    setLoading(true)
    try {
      const resp = await anovaAnalyze({
        factor_name: factorName.trim() || 'Factor',
        response_variable: responseVar.trim() || 'response',
        response_unit: responseUnit.trim(),
        groups: validGroups.map((g) => ({
          group_name: g.name.trim(),
          values: parseValues(g.valuesRaw),
        })),
      })
      setResult(resp)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="stat-tab-content">
      <div className="stat-governance-note" role="note">
        <span aria-hidden="true">ℹ</span> {p.governanceNote}
      </div>

      {/* Setup panel */}
      <div className="panel">
        <div className="panel-header">
          <h3>{p.anovaSetupTitle}</h3>
          <span className="panel-meta">{p.anovaSetupMeta}</span>
        </div>
        <div className="panel-body">
          <div className="form-grid">
            <div className="field">
              <label htmlFor={uid + '-afn'}>{p.anovaFactorName}</label>
              <input
                id={uid + '-afn'}
                type="text"
                value={factorName}
                placeholder="Material"
                onChange={(e) => setFactorName(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor={uid + '-arv'}>{p.anovaResponseVar}</label>
              <input
                id={uid + '-arv'}
                type="text"
                value={responseVar}
                placeholder="response"
                onChange={(e) => setResponseVar(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor={uid + '-aru'}>{p.anovaResponseUnit}</label>
              <input
                id={uid + '-aru'}
                type="text"
                value={responseUnit}
                placeholder="mm"
                onChange={(e) => setResponseUnit(e.target.value)}
              />
            </div>
          </div>

          <div>
            <div className="stat-section-label">{p.anovaGroupsTitle}</div>
            {groups.map((g, i) => (
              <div key={i} className="stat-factor-row">
                <div className="form-grid" style={{ flex: 1 }}>
                  <div className="field">
                    <label htmlFor={uid + '-gn-' + i}>{p.groupNameLabel}</label>
                    <input
                      id={uid + '-gn-' + i}
                      type="text"
                      value={g.name}
                      placeholder="DP600"
                      onChange={(e) => updateGroup(i, 'name', e.target.value)}
                    />
                  </div>
                  <div className="field" style={{ flex: 2 }}>
                    <label htmlFor={uid + '-gv-' + i}>{p.groupValuesLabel}</label>
                    <input
                      id={uid + '-gv-' + i}
                      type="text"
                      value={g.valuesRaw}
                      placeholder={p.groupValuesHint}
                      onChange={(e) => updateGroup(i, 'valuesRaw', e.target.value)}
                    />
                  </div>
                </div>
                {groups.length > 2 && (
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary stat-remove-btn"
                    onClick={() => removeGroup(i)}
                    aria-label={p.removeGroup}
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="btn btn-sm btn-secondary" onClick={addGroup}>
              + {p.addGroup}
            </button>
          </div>

          {error && <div className="field-error" role="alert">{error}</div>}

          <div className="stat-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleRunAnova}
              disabled={loading}
            >
              {loading ? p.analyzing : p.runAnovaBtn}
            </button>
          </div>
        </div>
      </div>

      {/* ANOVA Results */}
      {result && (
        <>
          <div className="panel">
            <div className="panel-header">
              <h3>{p.anovaResultsTitle}</h3>
              <span className="panel-meta">{p.anovaResultsMeta}</span>
            </div>
            <div className="panel-body">
              <div className="stat-summary-row">
                <div className="stat-kv">
                  <span className="stat-kv-label">{p.anovaGrandMean}</span>
                  <span className="stat-kv-value">{fmtNum(result.grand_mean, 4)} {responseUnit}</span>
                </div>
                <div className="stat-kv">
                  <span className="stat-kv-label">n</span>
                  <span className="stat-kv-value">{result.n_observations}</span>
                </div>
              </div>
              <ANOVATable rows={result.table} p={p} />
            </div>
          </div>

          {result.warnings.length > 0 && (
            <div className="panel">
              <div className="panel-body">
                {result.warnings.map((w, i) => (
                  <div key={i} className="badge warn">{w}</div>
                ))}
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-header">
              <h3>{p.anovaAssumptionsTitle}</h3>
            </div>
            <div className="panel-body">
              <ul className="stat-assumptions">
                {result.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────
export function StatisticalAnalysisPage() {
  const { t } = useAppLanguage()
  const p = t.statisticalPage
  const [tab, setTab] = useState<Tab>('taguchi')

  return (
    <div className="page-root">
      <div className="page-header">
        <div>
          <div className="page-kicker">{p.kicker}</div>
          <h1>{p.title}</h1>
          <p className="subtitle">{p.subtitle}</p>
        </div>
      </div>

      <div className="stat-tabs" role="tablist" aria-label={p.title}>
        <button
          role="tab"
          aria-selected={tab === 'taguchi'}
          className={'stat-tab-btn' + (tab === 'taguchi' ? ' active' : '')}
          onClick={() => setTab('taguchi')}
        >
          {p.tabTaguchi}
        </button>
        <button
          role="tab"
          aria-selected={tab === 'anova'}
          className={'stat-tab-btn' + (tab === 'anova' ? ' active' : '')}
          onClick={() => setTab('anova')}
        >
          {p.tabAnova}
        </button>
      </div>

      {tab === 'taguchi' && <TaguchiTab />}
      {tab === 'anova' && <AnovaTab />}
    </div>
  )
}
