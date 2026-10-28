/**
 * EnergyPage.tsx — Multi-Spot Energy & Cost Intelligence dashboard.
 * P1 + P2-A + P2-B (scenario) + P2-D (dashboard) — MASTER-ENERGY-OPTIMIZATION-01.
 *
 * Tabs:
 *   single   — single weld-point I²Rt estimate + five KPI indicators
 *   multi    — multi-spot table, group summaries, pareto chart, annual cost
 *   dashboard— P2-D: Pareto, financial summary, sensitivity matrix
 *   map      — interactive part map with optional X/Y coordinates (P2-A)
 *   scenario — baseline vs proposed scenario comparison (P2-B/P2-C)
 *   import   — CSV import with formula-injection protection
 *   help     — contextual engineering help
 */

import { useState, useId, useRef } from 'react'
import { useAppLanguage } from '../i18n/useAppLanguage'
import {
  energyEstimate, energyWindow, energyCost, energyAggregate,
  energyImportPreview, energyImportPreviewFile, energyScenarioCompare, energyDashboard,
  downloadEnergyReport,
  type EnergyI2RTResponse, type EnergyWindowResponse, type CostIntelligenceResult,
  type MultiSpotAggregationResponse, type WeldPointEnergySpecIn,
  type WeldPointWindowRow, type ImportPreviewResponse, type EnergyWindowStatus,
  type ScenarioComparisonResponse, type DashboardResponse,
  type ReportFormat,
} from '../api/energy'

// ── Types ─────────────────────────────────────────────────────────────────────
type Tab = 'single' | 'multi' | 'dashboard' | 'map' | 'scenario' | 'import' | 'export' | 'help'

interface SingleForm {
  current_ka: string
  resistance_micro_ohm: string
  weld_cycles: string
  frequency_hz: string
  e_current_kj: string
  e_min_kj: string
  e_ideal_kj: string
  e_max_kj: string
}

interface MultiRow {
  id: string
  point_code: string
  group_name: string
  e_current_kj: string
  e_min_kj: string
  e_ideal_kj: string
  e_max_kj: string
}

interface MapRow {
  id: string
  point_code: string
  group_name: string
  e_current_kj: string
  e_min_kj: string
  e_ideal_kj: string
  e_max_kj: string
  x: string
  y: string
}

interface ScenarioRow {
  id: string
  point_code: string
  group_name: string
  e_min_kj: string
  e_ideal_kj: string
  e_max_kj: string
  baseline_e_current_kj: string
  proposed_e_current_kj: string
}

interface CostForm {
  production_volume_annual: string
  tariff_eur_per_kwh: string
  tariff_usd_per_kwh: string
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function n(s: string): number | null {
  const v = parseFloat(s)
  return isNaN(v) || v < 0 ? null : v
}

function fmt(v: number | null | undefined, dp = 4): string {
  if (v == null) return '—'
  return v.toFixed(dp)
}

function uid(): string {
  return Math.random().toString(36).slice(2, 9)
}

// ── Status colors ─────────────────────────────────────────────────────────────
// CSS vars work for HTML elements; for SVG fill attributes use STATUS_HEX
const STATUS_COLOR: Record<EnergyWindowStatus, string> = {
  NOT_ESTABLISHED: 'var(--text-tertiary)',
  IN_WINDOW: 'var(--ok)',
  BELOW_MIN: 'var(--danger)',
  ABOVE_MAX: 'var(--warn)',
  E_CURRENT_ABSENT: 'var(--info)',
}

const STATUS_HEX: Record<EnergyWindowStatus, string> = {
  NOT_ESTABLISHED: '#6b7689',
  IN_WINDOW:       '#34d058',
  BELOW_MIN:       '#f85149',
  ABOVE_MAX:       '#f0b429',
  E_CURRENT_ABSENT:'#58a6ff',
}

function StatusBadge({ status, label }: { status: EnergyWindowStatus; label: string }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 3,
      fontSize: 'var(--fs-xs)',
      fontWeight: 600,
      letterSpacing: '0.03em',
      background: STATUS_COLOR[status] + '22',
      color: STATUS_COLOR[status],
      border: `1px solid ${STATUS_COLOR[status]}44`,
    }}>
      {label}
    </span>
  )
}

// ── KPI card ──────────────────────────────────────────────────────────────────
function KpiCard({
  label, value, unit, accent, note,
}: {
  label: string
  value: string
  unit: string
  accent?: string
  note?: string
}) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: `1px solid ${accent ?? 'var(--border)'}`,
      borderRadius: 'var(--r-lg)',
      padding: 'var(--sp-4) var(--sp-5)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-1)',
      minWidth: 0,
    }}>
      <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', letterSpacing: '0.04em', fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: 'var(--fs-h2)', fontWeight: 700, color: accent ?? 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
        {value}
      </div>
      <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)' }}>{unit}</div>
      {note && <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--warn)', marginTop: 2 }}>{note}</div>}
    </div>
  )
}

// ── Help tooltip ──────────────────────────────────────────────────────────────
function HelpIcon({ text }: { text: string }) {
  const [open, setOpen] = useState(false)
  return (
    <span style={{ position: 'relative', display: 'inline-block', marginLeft: 4 }}>
      <button
        type="button"
        style={{
          background: 'none', border: '1px solid var(--border)',
          borderRadius: '50%', width: 16, height: 16,
          fontSize: 10, cursor: 'pointer', color: 'var(--text-tertiary)',
          lineHeight: 1, padding: 0,
        }}
        aria-label="Help"
        onClick={() => setOpen(!open)}
      >?</button>
      {open && (
        <div style={{
          position: 'absolute', bottom: '120%', left: 0, zIndex: 100,
          background: 'var(--bg-surface-3)', border: '1px solid var(--border-strong)',
          borderRadius: 'var(--r-md)', padding: 'var(--sp-3)',
          width: 260, fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)',
          lineHeight: 1.5, boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
        }}>
          {text}
          <button
            type="button"
            style={{ display: 'block', marginTop: 6, fontSize: 10, cursor: 'pointer',
              background: 'none', border: 'none', color: 'var(--text-tertiary)' }}
            onClick={() => setOpen(false)}
          >✕ Kapat / Close</button>
        </div>
      )}
    </span>
  )
}

// ── Inline bar chart (SVG) ────────────────────────────────────────────────────
function EnergyBarChart({
  e_min, e_ideal, e_current, e_max
}: {
  e_min: number | null; e_ideal: number | null;
  e_current: number | null; e_max: number | null;
}) {
  const vals = [e_min, e_ideal, e_current, e_max].filter((v): v is number => v != null)
  if (vals.length === 0) return null
  const maxVal = Math.max(...vals) * 1.15
  const W = 320, H = 100, barW = 44, gap = 20, left = 48

  const bars: { label: string; val: number; color: string }[] = [
    { label: 'E_min', val: e_min ?? 0, color: 'var(--info)' },
    { label: 'E_ideal', val: e_ideal ?? 0, color: 'var(--ok)' },
    { label: 'E_cur', val: e_current ?? 0, color: 'var(--accent)' },
    { label: 'E_max', val: e_max ?? 0, color: 'var(--warn)' },
  ]

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} aria-label="Energy comparison bar chart"
      style={{ overflow: 'visible', display: 'block', margin: '0 auto' }}>
      {/* Axis */}
      <line x1={left} y1={4} x2={left} y2={H - 20} stroke="var(--border)" strokeWidth={1} />
      <line x1={left} y1={H - 20} x2={W - 10} y2={H - 20} stroke="var(--border)" strokeWidth={1} />
      {bars.map((b, i) => {
        const x = left + i * (barW + gap) + 4
        const bh = b.val > 0 ? ((b.val / maxVal) * (H - 30)) : 0
        const y = H - 20 - bh
        return (
          <g key={b.label}>
            <rect x={x} y={y} width={barW} height={bh} fill={b.color} opacity={0.8} rx={2} />
            <text x={x + barW / 2} y={H - 6} textAnchor="middle"
              fontSize={9} fill="var(--text-secondary)">{b.label}</text>
            <text x={x + barW / 2} y={y - 3} textAnchor="middle"
              fontSize={8} fill="var(--text-primary)">{b.val.toFixed(3)}</text>
          </g>
        )
      })}
    </svg>
  )
}

// ── Pareto chart ──────────────────────────────────────────────────────────────
function ParetoChart({ rows }: { rows: { point_code: string; e_excess_potential_kj: number | null }[] }) {
  const data = rows.filter(r => (r.e_excess_potential_kj ?? 0) > 0)
  if (data.length === 0) return <div style={{ color: 'var(--text-tertiary)', fontSize: 'var(--fs-sm)' }}>—</div>

  const W = 400, H = 120, barW = Math.min(36, Math.floor((W - 60) / data.length) - 4)
  const maxVal = Math.max(...data.map(r => r.e_excess_potential_kj ?? 0))
  const total = data.reduce((s, r) => s + (r.e_excess_potential_kj ?? 0), 0)
  let cumPct = 0

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W, display: 'block' }}
      aria-label="Energy excess pareto chart">
      {data.map((r, i) => {
        const x = 50 + i * (barW + 4)
        const bh = ((r.e_excess_potential_kj ?? 0) / maxVal) * (H - 40)
        const y = H - 26 - bh
        const pct = (r.e_excess_potential_kj ?? 0) / total
        cumPct += pct
        const cx = x + barW / 2
        const cy2 = H - 26 - cumPct * (H - 40)
        return (
          <g key={r.point_code}>
            <rect x={x} y={y} width={barW} height={bh} fill="var(--accent)" opacity={0.75} rx={2} />
            {i > 0 && (
              <line
                x1={x - 2} y1={cy2 + (1 - cumPct + pct) * (H - 40) * 0 + 0}
                x2={cx} y2={cy2}
                stroke="var(--info)" strokeWidth={1.5}
              />
            )}
            <circle cx={cx} cy={cy2} r={3} fill="var(--info)" />
            <text x={cx} y={H - 12} textAnchor="middle" fontSize={7}
              fill="var(--text-tertiary)">{r.point_code.slice(-6)}</text>
          </g>
        )
      })}
      <line x1={50} y1={4} x2={50} y2={H - 26} stroke="var(--border)" strokeWidth={1} />
      <line x1={50} y1={H - 26} x2={W - 10} y2={H - 26} stroke="var(--border)" strokeWidth={1} />
    </svg>
  )
}

// ── P2-D: Enhanced Pareto chart (full width, with cumulative % line) ──────────
function EnhancedParetoChart({
  rows,
}: {
  rows: { point_code: string; e_excess_kj: number | null; pct_of_total_excess: number | null; cumulative_pct: number | null; window_status: EnergyWindowStatus }[]
}) {
  const data = rows.filter(r => (r.e_excess_kj ?? 0) > 0 || r.e_excess_kj === 0)
  const withExcess = data.filter(r => (r.e_excess_kj ?? 0) > 0)
  if (data.length === 0) return <div style={{ color: 'var(--text-tertiary)', fontSize: 'var(--fs-sm)' }}>— Hesaplanabilir fazla enerji yok / No calculable excess —</div>

  const W = 580, H = 160
  const left = 52, right = 40, bottom = 32, top = 12
  const chartW = W - left - right
  const chartH = H - bottom - top
  const n = data.length
  const barW = Math.min(40, Math.floor(chartW / n) - 3)

  const maxExcess = Math.max(...data.map(r => r.e_excess_kj ?? 0)) * 1.12 || 1

  const points80: { x: number; y: number }[] = []
  data.forEach((r, i) => {
    const cx = left + i * (barW + (chartW / n - barW)) + barW / 2
    const cy = top + chartH - ((r.cumulative_pct ?? 0) / 100) * chartH
    points80.push({ x: cx, y: cy })
  })

  const y80line = top + chartH - 0.8 * chartH

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W, display: 'block', overflow: 'visible' }}
      aria-label="Enhanced energy excess Pareto chart">
      {/* Axes */}
      <line x1={left} y1={top} x2={left} y2={top + chartH} stroke="var(--border)" strokeWidth={1} />
      <line x1={left} y1={top + chartH} x2={W - right} y2={top + chartH} stroke="var(--border)" strokeWidth={1} />
      {/* Right Y axis */}
      <line x1={W - right} y1={top} x2={W - right} y2={top + chartH} stroke="var(--border)" strokeDasharray="3 3" strokeWidth={1} />
      {/* 80% reference line */}
      <line x1={left} y1={y80line} x2={W - right} y2={y80line}
        stroke="var(--warn)" strokeDasharray="5 3" strokeWidth={1.5} opacity={0.7} />
      <text x={left + 4} y={y80line - 3} fontSize={8} fill="var(--warn)" opacity={0.85}>80%</text>

      {/* Bars */}
      {data.map((r, i) => {
        const bh = ((r.e_excess_kj ?? 0) / maxExcess) * chartH
        const x = left + i * (chartW / n) + (chartW / n - barW) / 2
        const y = top + chartH - bh
        return (
          <g key={r.point_code}>
            <rect x={x} y={y} width={barW} height={bh}
              fill={STATUS_HEX[r.window_status]} opacity={0.8} rx={2} />
            <text x={x + barW / 2} y={top + chartH + 14} textAnchor="middle"
              fontSize={7} fill="var(--text-tertiary)">{r.point_code.slice(-7)}</text>
            {bh > 12 && (
              <text x={x + barW / 2} y={y + 10} textAnchor="middle"
                fontSize={7} fill="white">{(r.e_excess_kj ?? 0).toFixed(3)}</text>
            )}
          </g>
        )
      })}

      {/* Cumulative % line */}
      {points80.length > 1 && (
        <polyline
          points={points80.map(p => `${p.x},${p.y}`).join(' ')}
          fill="none" stroke="var(--info)" strokeWidth={2} strokeLinejoin="round"
        />
      )}
      {points80.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} fill="var(--info)" />
      ))}

      {/* Right Y axis % labels */}
      {[0, 25, 50, 75, 100].map(pct => {
        const yp = top + chartH - (pct / 100) * chartH
        return (
          <g key={pct}>
            <text x={W - right + 4} y={yp + 3} fontSize={7} fill="var(--text-tertiary)">{pct}%</text>
          </g>
        )
      })}

      {/* Left Y axis kJ label */}
      <text x={6} y={top + chartH / 2} fontSize={7} fill="var(--text-tertiary)"
        transform={`rotate(-90 6 ${top + chartH / 2})`} textAnchor="middle">kJ</text>
      {/* Right Y label */}
      <text x={W - 8} y={top + chartH / 2} fontSize={7} fill="var(--info)"
        transform={`rotate(90 ${W - 8} ${top + chartH / 2})`} textAnchor="middle">Cum%</text>

      {/* Legend */}
      <circle cx={left + 12} cy={top + chartH + 26} r={3} fill="var(--info)" />
      <text x={left + 18} y={top + chartH + 29} fontSize={7} fill="var(--text-tertiary)">Kümülatif / Cumulative %</text>
      <rect x={left + 110} y={top + chartH + 23} width={8} height={6} fill="var(--warn)" opacity={0.7} />
      <text x={left + 122} y={top + chartH + 29} fontSize={7} fill="var(--text-tertiary)">%80 referans / 80% reference</text>
    </svg>
  )
}

// ── P2-D: Per-point energy window bullet chart ────────────────────────────────
function EnergyWindowBulletChart({
  rows,
}: {
  rows: { point_code: string; e_min_kj: number | null; e_ideal_kj: number | null; e_max_kj: number | null; e_current_kj: number | null; window_status: EnergyWindowStatus }[]
}) {
  if (rows.length === 0) return null
  const allVals = rows.flatMap(r => [r.e_min_kj, r.e_ideal_kj, r.e_max_kj, r.e_current_kj]).filter((v): v is number => v != null)
  if (allVals.length === 0) return <div style={{ color: 'var(--text-tertiary)', fontSize: 'var(--fs-sm)' }}>— Yeterli veri yok / Insufficient data —</div>

  const domainMax = Math.max(...allVals) * 1.1 || 1
  const ROW_H = 26, LABEL_W = 72, BAR_MAX_W = 320, H = rows.length * ROW_H + 28
  const W = LABEL_W + BAR_MAX_W + 8

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W, display: 'block', overflow: 'visible' }}
      aria-label="Per-point energy window bullet chart">
      {/* Column header */}
      <text x={LABEL_W + BAR_MAX_W / 2} y={12} textAnchor="middle"
        fontSize={8} fill="var(--text-tertiary)">kJ / spot</text>

      {rows.map((r, i) => {
        const y = 18 + i * ROW_H
        const bh = 12
        const scl = (v: number | null) => v != null ? Math.min((v / domainMax) * BAR_MAX_W, BAR_MAX_W) : 0

        const xMin = scl(r.e_min_kj)
        const xMax = scl(r.e_max_kj)
        const xIdeal = scl(r.e_ideal_kj)
        const xCur = scl(r.e_current_kj)

        return (
          <g key={r.point_code}>
            {/* Row bg */}
            <rect x={0} y={y - 2} width={W} height={ROW_H - 2} fill={i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent'} />
            {/* Point label */}
            <text x={LABEL_W - 4} y={y + bh / 2 + 3} textAnchor="end"
              fontSize={8} fill="var(--text-secondary)" fontFamily="var(--font-mono)">{r.point_code.slice(-9)}</text>
            {/* Window band (min→max) */}
            {r.e_min_kj != null && r.e_max_kj != null && (
              <rect x={LABEL_W + xMin} y={y + 2} width={Math.max(0, xMax - xMin)} height={bh - 4}
                fill="rgba(255,255,255,0.06)" stroke="var(--border)" strokeWidth={0.5} rx={1} />
            )}
            {/* Current bar */}
            {r.e_current_kj != null && (
              <rect x={LABEL_W} y={y} width={xCur} height={bh}
                fill={STATUS_HEX[r.window_status]} opacity={0.75} rx={2} />
            )}
            {/* Ideal marker */}
            {r.e_ideal_kj != null && (
              <line x1={LABEL_W + xIdeal} y1={y - 2} x2={LABEL_W + xIdeal} y2={y + bh + 2}
                stroke={STATUS_HEX.IN_WINDOW} strokeWidth={1.5} />
            )}
            {/* Min/Max tick markers */}
            {r.e_min_kj != null && (
              <line x1={LABEL_W + xMin} y1={y + 2} x2={LABEL_W + xMin} y2={y + bh - 2}
                stroke={STATUS_HEX.E_CURRENT_ABSENT} strokeWidth={1} strokeDasharray="2 2" />
            )}
            {r.e_max_kj != null && (
              <line x1={LABEL_W + xMax} y1={y + 2} x2={LABEL_W + xMax} y2={y + bh - 2}
                stroke={STATUS_HEX.ABOVE_MAX} strokeWidth={1} strokeDasharray="2 2" />
            )}
            {/* Value label */}
            {r.e_current_kj != null && (
              <text x={LABEL_W + xCur + 3} y={y + bh / 2 + 3}
                fontSize={7} fill="var(--text-secondary)">{r.e_current_kj.toFixed(3)}</text>
            )}
          </g>
        )
      })}

      {/* Legend */}
      <g transform={`translate(${LABEL_W}, ${18 + rows.length * ROW_H + 4})`}>
        <rect x={0} y={0} width={8} height={6} fill={STATUS_HEX.IN_WINDOW} opacity={0.75} />
        <text x={11} y={6} fontSize={7} fill="var(--text-tertiary)">E_cur (renk=durum)</text>
        <line x1={70} y1={0} x2={70} y2={8} stroke={STATUS_HEX.IN_WINDOW} strokeWidth={1.5} />
        <text x={74} y={6} fontSize={7} fill="var(--text-tertiary)">E_ideal</text>
        <rect x={104} y={1} width={20} height={4} fill="rgba(255,255,255,0.06)" stroke="var(--border)" strokeWidth={0.5} />
        <text x={128} y={6} fontSize={7} fill="var(--text-tertiary)">Pencere / Window</text>
      </g>
    </svg>
  )
}

// ── P2-D: Sensitivity matrix table ────────────────────────────────────────────
function SensitivityTable({
  sensitivity,
  selectedVolume,
  selectedTariffEur,
  labelVolume,
  labelTariff,
  labelNote,
}: {
  sensitivity: { production_volume: number; tariff_eur_per_kwh: number; cost_eur: number | null }[]
  selectedVolume?: number | null
  selectedTariffEur?: number | null
  labelVolume: string
  labelTariff: string
  labelNote: string
}) {
  if (sensitivity.length === 0) return null

  const volumes = [...new Set(sensitivity.map(r => r.production_volume))].sort((a, b) => a - b)
  const tariffs = [...new Set(sensitivity.map(r => r.tariff_eur_per_kwh))].sort((a, b) => a - b)

  const cell = (vol: number, t: number) =>
    sensitivity.find(r => r.production_volume === vol && r.tariff_eur_per_kwh === t)?.cost_eur ?? null

  const maxCost = Math.max(...sensitivity.map(r => r.cost_eur ?? 0))

  return (
    <div>
      <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginBottom: 6 }}>{labelNote}</div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', fontSize: 'var(--fs-xs)', fontFamily: 'var(--font-mono)', width: '100%' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={{ padding: '4px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>
                {labelVolume}
              </th>
              {tariffs.map(t => (
                <th key={t} style={{
                  padding: '4px 8px', textAlign: 'right', color: 'var(--text-tertiary)', fontWeight: 600,
                  fontFamily: 'var(--font-sans)',
                  background: selectedTariffEur === t ? 'var(--accent-soft)' : undefined,
                }}>
                  {t.toFixed(2)}
                </th>
              ))}
            </tr>
            <tr>
              <td colSpan={tariffs.length + 1} style={{ padding: '2px 8px', fontSize: 'var(--fs-xs)', color: 'var(--accent)', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                EUR/kWh →
              </td>
            </tr>
          </thead>
          <tbody>
            {volumes.map(vol => (
              <tr key={vol} style={{
                borderBottom: '1px solid var(--border)',
                background: selectedVolume === vol ? 'var(--accent-soft)' : undefined,
              }}>
                <td style={{ padding: '4px 8px', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)' }}>
                  {vol.toLocaleString()}
                </td>
                {tariffs.map(t => {
                  const v = cell(vol, t)
                  const intensity = v != null && maxCost > 0 ? v / maxCost : 0
                  const isSelected = selectedVolume === vol && selectedTariffEur === t
                  return (
                    <td key={t} style={{
                      padding: '4px 8px', textAlign: 'right',
                      background: isSelected
                        ? 'var(--accent)'
                        : v != null
                          ? `rgba(240, 180, 41, ${intensity * 0.35})`
                          : undefined,
                      color: isSelected ? 'white' : v == null ? 'var(--text-tertiary)' : 'var(--text-primary)',
                      fontWeight: isSelected ? 700 : 400,
                    }}>
                      {v != null ? v.toFixed(2) : '—'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Part map SVG ─────────────────────────────────────────────────────────────
function PartMapSvg({
  apiRows, mapRows, selected, onSelect, groupFilter,
}: {
  apiRows: WeldPointWindowRow[]
  mapRows: MapRow[]
  selected: string | null
  onSelect: (code: string) => void
  groupFilter: string
}) {
  const W = 440, H = 290, PR = 11
  const coordMap = new Map(
    mapRows
      .filter(r => r.x.trim() !== '' && r.y.trim() !== '')
      .map(r => [r.point_code, { x: parseFloat(r.x), y: parseFloat(r.y) }] as const)
      .filter(([, c]) => !isNaN(c.x) && !isNaN(c.y))
  )
  const visible = apiRows.filter(r =>
    (groupFilter === '' || r.group_name === groupFilter) && coordMap.has(r.point_code)
  )
  if (visible.length === 0) return null

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%"
      style={{ maxWidth: W, display: 'block', cursor: 'default', borderRadius: 6 }}
      aria-label="Part energy status map">
      <rect x={0} y={0} width={W} height={H} rx={6}
        style={{ fill: 'var(--bg-surface-2)', stroke: 'var(--border)', strokeWidth: '1' }} />
      {[20, 40, 60, 80].map(pct => {
        const gx = 20 + (pct / 100) * (W - 40)
        const gy = 16 + (pct / 100) * (H - 32)
        return (
          <g key={pct}>
            <line x1={gx} y1={16} x2={gx} y2={H - 16}
              style={{ stroke: 'var(--border)', strokeWidth: '0.5', opacity: '0.6' }} />
            <line x1={20} y1={gy} x2={W - 20} y2={gy}
              style={{ stroke: 'var(--border)', strokeWidth: '0.5', opacity: '0.6' }} />
          </g>
        )
      })}
      {visible.map(row => {
        const coord = coordMap.get(row.point_code)!
        const cx = 20 + (coord.x / 100) * (W - 40)
        const cy = 16 + (coord.y / 100) * (H - 32)
        const hex = STATUS_HEX[row.window_status]
        const isSel = row.point_code === selected
        const lbl = row.point_code.length > 6 ? row.point_code.slice(-5) : row.point_code
        return (
          <g key={row.point_code} onClick={() => onSelect(row.point_code)} style={{ cursor: 'pointer' }}>
            {isSel && (
              <circle cx={cx} cy={cy} r={PR + 6} fill="none" stroke={hex} strokeWidth={2} opacity={0.5} />
            )}
            <circle cx={cx} cy={cy} r={PR}
              fill={hex + '33'} stroke={hex} strokeWidth={isSel ? 2.5 : 1.5} />
            {(row.e_excess_potential_kj ?? 0) > 0 && (
              <circle cx={cx + PR - 2} cy={cy - PR + 2} r={4} fill="#f0b429" />
            )}
            <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
              fontSize={8} fontWeight={600} fill={hex}
              style={{ pointerEvents: 'none', fontFamily: 'monospace', userSelect: 'none' }}>
              {lbl}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

// ── Schematic fallback (no coordinates) ──────────────────────────────────────
function SchematicFallback({
  apiRows, selected, onSelect, groupFilter,
}: {
  apiRows: WeldPointWindowRow[]
  selected: string | null
  onSelect: (code: string) => void
  groupFilter: string
}) {
  const visible = apiRows.filter(r => groupFilter === '' || r.group_name === groupFilter)
  const groups = [...new Set(visible.map(r => r.group_name))]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
      {groups.map(gName => (
        <div key={gName}>
          <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: 6, letterSpacing: '0.06em' }}>
            {gName.toUpperCase()}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {visible.filter(r => r.group_name === gName).map(row => {
              const hex = STATUS_HEX[row.window_status]
              const isSel = row.point_code === selected
              return (
                <button key={row.point_code} type="button" onClick={() => onSelect(row.point_code)}
                  style={{
                    padding: '4px 10px', borderRadius: 'var(--r-md)',
                    border: `2px solid ${hex}`,
                    background: isSel ? hex + '33' : hex + '11',
                    color: hex, fontSize: 'var(--fs-xs)',
                    fontWeight: isSel ? 700 : 500, cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                    outline: isSel ? `2px solid ${hex}` : 'none',
                    outlineOffset: 2,
                  }}>
                  {row.point_code}
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Scenario deviation bar chart ──────────────────────────────────────────────
function DeviationBarChart({
  points,
}: {
  points: { point_code: string; baseline_e_current_kj: number | null; proposed_e_current_kj: number | null; baseline_window_status: string; proposed_window_status: string }[]
}) {
  const filtered = points.filter(p => p.baseline_e_current_kj != null || p.proposed_e_current_kj != null)
  if (filtered.length === 0) return null
  const all = filtered.flatMap(p => [p.baseline_e_current_kj ?? 0, p.proposed_e_current_kj ?? 0]).filter(v => v > 0)
  if (all.length === 0) return null
  const maxVal = Math.max(...all) * 1.12
  const W = 480, H = 130
  const barW = Math.min(20, Math.floor((W - 60) / (filtered.length * 2 + filtered.length - 1)) - 1)
  const gap = Math.floor(barW * 0.4)
  const groupGap = Math.floor(barW * 1.6)
  const left = 44

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W, display: 'block' }}
      aria-label="Baseline vs proposed energy deviation bar chart">
      <line x1={left} y1={4} x2={left} y2={H - 24} style={{ stroke: 'var(--border)', strokeWidth: '1' }} />
      <line x1={left} y1={H - 24} x2={W - 8} y2={H - 24} style={{ stroke: 'var(--border)', strokeWidth: '1' }} />
      {filtered.map((p, i) => {
        const bHex = STATUS_HEX[p.baseline_window_status as EnergyWindowStatus] ?? '#6b7689'
        const pHex = STATUS_HEX[p.proposed_window_status as EnergyWindowStatus] ?? '#6b7689'
        const x0 = left + i * (barW * 2 + gap + groupGap) + 4
        const bh = ((p.baseline_e_current_kj ?? 0) / maxVal) * (H - 30)
        const ph = ((p.proposed_e_current_kj ?? 0) / maxVal) * (H - 30)
        const lbl = p.point_code.length > 7 ? p.point_code.slice(-6) : p.point_code
        return (
          <g key={p.point_code}>
            <rect x={x0} y={H - 24 - bh} width={barW} height={bh} fill={bHex + 'bb'} rx={2} />
            <rect x={x0 + barW + gap} y={H - 24 - ph} width={barW} height={ph} fill={pHex} rx={2} />
            <text x={x0 + barW + gap / 2} y={H - 10} textAnchor="middle" fontSize={7}
              style={{ fill: 'var(--text-tertiary)' }}>{lbl}</text>
          </g>
        )
      })}
      <text x={left - 2} y={8} textAnchor="end" fontSize={7} style={{ fill: 'var(--text-tertiary)' }}>kJ</text>
    </svg>
  )
}

// ── Section panel ─────────────────────────────────────────────────────────────
function Panel({ title, children, accent }: { title: string; children: React.ReactNode; accent?: string }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: `1px solid ${accent ?? 'var(--border)'}`,
      borderRadius: 'var(--r-lg)',
      padding: 'var(--sp-5)',
      marginBottom: 'var(--sp-4)',
    }}>
      <h3 style={{ marginBottom: 'var(--sp-3)', color: accent ?? 'var(--text-primary)' }}>{title}</h3>
      {children}
    </div>
  )
}

// ── Input row ─────────────────────────────────────────────────────────────────
function FieldRow({
  label, value, onChange, type = 'number', min, step, placeholder, help,
}: {
  label: string; value: string; onChange: (v: string) => void;
  type?: string; min?: string; step?: string; placeholder?: string; help?: string;
}) {
  const id = useId()
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label htmlFor={id} style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}>
        {label}{help && <HelpIcon text={help} />}
      </label>
      <input
        id={id} type={type} value={value}
        min={min} step={step} placeholder={placeholder ?? ''}
        onChange={e => onChange(e.target.value)}
        style={{
          background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
          borderRadius: 'var(--r-md)', padding: '5px 8px',
          color: 'var(--text-primary)', fontSize: 'var(--fs-body)',
          fontFamily: 'var(--font-mono)',
        }}
      />
    </div>
  )
}

// ── Disclaimer banner ─────────────────────────────────────────────────────────
function DisclaimerBanner({ text }: { text: string }) {
  return (
    <div style={{
      background: 'var(--warn-soft)', border: '1px solid var(--warn)',
      borderRadius: 'var(--r-md)', padding: 'var(--sp-3) var(--sp-4)',
      fontSize: 'var(--fs-xs)', color: 'var(--warn)', marginTop: 'var(--sp-3)',
    }}>
      ⚠ {text}
    </div>
  )
}

// ── Main page component ────────────────────────────────────────────────────────
export function EnergyPage() {
  const { t } = useAppLanguage()
  const p = t.energyModule
  const pm = t.partMap
  const sm = t.scenarioModule
  const dm = t.dashboardModule
  const rm = t.reportModule
  const [tab, setTab] = useState<Tab>('single')

  // Single-point state
  const [singleForm, setSingleForm] = useState<SingleForm>({
    current_ka: '8.3', resistance_micro_ohm: '120', weld_cycles: '16', frequency_hz: '50',
    e_current_kj: '', e_min_kj: '', e_ideal_kj: '', e_max_kj: '',
  })
  const [estimateResult, setEstimateResult] = useState<EnergyI2RTResponse | null>(null)
  const [windowResult, setWindowResult] = useState<EnergyWindowResponse | null>(null)
  const [costResult, setCostResult] = useState<CostIntelligenceResult | null>(null)
  const [singleLoading, setSingleLoading] = useState(false)
  const [singleError, setSingleError] = useState('')

  const [costForm, setCostForm] = useState<CostForm>({
    production_volume_annual: '100000', tariff_eur_per_kwh: '0.18', tariff_usd_per_kwh: '0.19',
  })

  // Multi-spot state
  const [multiRows, setMultiRows] = useState<MultiRow[]>([
    { id: uid(), point_code: 'WP-001', group_name: 'Group-A', e_current_kj: '0.40', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
    { id: uid(), point_code: 'WP-002', group_name: 'Group-A', e_current_kj: '0.38', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
    { id: uid(), point_code: 'WP-003', group_name: 'Group-B', e_current_kj: '0.55', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
  ])
  const [multiCostForm, setMultiCostForm] = useState<CostForm>({
    production_volume_annual: '200000', tariff_eur_per_kwh: '0.18', tariff_usd_per_kwh: '0.19',
  })
  const [aggrResult, setAggrResult] = useState<MultiSpotAggregationResponse | null>(null)
  const [multiLoading, setMultiLoading] = useState(false)
  const [multiError, setMultiError] = useState('')

  // Scenario state (P2-B)
  const [scenRows, setScenarRows] = useState<ScenarioRow[]>([
    { id: uid(), point_code: 'WP-001', group_name: 'Group-A', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42', baseline_e_current_kj: '0.40', proposed_e_current_kj: '0.35' },
    { id: uid(), point_code: 'WP-002', group_name: 'Group-A', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42', baseline_e_current_kj: '0.55', proposed_e_current_kj: '0.38' },
    { id: uid(), point_code: 'WP-003', group_name: 'Group-B', e_min_kj: '0.30', e_ideal_kj: '0.38', e_max_kj: '0.48', baseline_e_current_kj: '0.20', proposed_e_current_kj: '0.40' },
  ])
  const [scenCostForm, setScenCostForm] = useState<CostForm>({
    production_volume_annual: '200000', tariff_eur_per_kwh: '0.18', tariff_usd_per_kwh: '0.19',
  })
  const [scenResult, setScenResult] = useState<ScenarioComparisonResponse | null>(null)
  const [scenLoading, setScenLoading] = useState(false)
  const [scenError, setScenError] = useState('')

  // Dashboard state (P2-D)
  const [dashRows, setDashRows] = useState<MultiRow[]>([
    { id: uid(), point_code: 'WP-001', group_name: 'Group-A', e_current_kj: '0.55', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
    { id: uid(), point_code: 'WP-002', group_name: 'Group-A', e_current_kj: '0.40', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
    { id: uid(), point_code: 'WP-003', group_name: 'Group-B', e_current_kj: '0.30', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
    { id: uid(), point_code: 'WP-004', group_name: 'Group-B', e_current_kj: '0.48', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42' },
  ])
  const [dashCostForm, setDashCostForm] = useState<CostForm>({
    production_volume_annual: '200000', tariff_eur_per_kwh: '0.18', tariff_usd_per_kwh: '0.22',
  })
  const [dashResult, setDashResult] = useState<DashboardResponse | null>(null)
  const [dashLoading, setDashLoading] = useState(false)
  const [dashError, setDashError] = useState('')

  // Map state (P2-A)
  const [mapRows, setMapRows] = useState<MapRow[]>([
    { id: uid(), point_code: 'WP-001', group_name: 'Group-A', e_current_kj: '0.40', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42', x: '25', y: '30' },
    { id: uid(), point_code: 'WP-002', group_name: 'Group-A', e_current_kj: '0.38', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42', x: '65', y: '30' },
    { id: uid(), point_code: 'WP-003', group_name: 'Group-B', e_current_kj: '0.55', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42', x: '25', y: '72' },
    { id: uid(), point_code: 'WP-004', group_name: 'Group-B', e_current_kj: '', e_min_kj: '0.28', e_ideal_kj: '0.32', e_max_kj: '0.42', x: '65', y: '72' },
  ])
  const [mapCostForm, setMapCostForm] = useState<CostForm>({
    production_volume_annual: '200000', tariff_eur_per_kwh: '0.18', tariff_usd_per_kwh: '0.19',
  })
  const [mapResult, setMapResult] = useState<MultiSpotAggregationResponse | null>(null)
  const [mapLoading, setMapLoading] = useState(false)
  const [mapError, setMapError] = useState('')
  const [selectedCode, setSelectedCode] = useState<string | null>(null)
  const [groupFilter, setGroupFilter] = useState('')

  // Import state
  const [csvText, setCsvText] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<ImportPreviewResponse | null>(null)
  const [importLoading, setImportLoading] = useState(false)
  const [importError, setImportError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  // Export state (P2-F)
  const [exportFormat, setExportFormat] = useState<ReportFormat>('xlsx')
  const [exportLang, setExportLang] = useState<'en' | 'tr'>('en')
  const [exportProjectId, setExportProjectId] = useState('')
  const [exportProjectName, setExportProjectName] = useState('')
  const [exportPartId, setExportPartId] = useState('')
  const [exportPassportId, setExportPassportId] = useState('')
  const [exportAnalyst, setExportAnalyst] = useState('')
  const [exportTitle, setExportTitle] = useState('')
  const [exportLoading, setExportLoading] = useState(false)
  const [exportError, setExportError] = useState('')
  const [exportSuccess, setExportSuccess] = useState('')

  // ── Single: estimate + window + optional cost ──────────────────────────────
  async function runSingle() {
    setSingleLoading(true)
    setSingleError('')
    setEstimateResult(null)
    setWindowResult(null)
    setCostResult(null)
    try {
      const est = await energyEstimate({
        current_ka: parseFloat(singleForm.current_ka),
        resistance_micro_ohm: parseFloat(singleForm.resistance_micro_ohm),
        weld_cycles: parseFloat(singleForm.weld_cycles),
        frequency_hz: parseFloat(singleForm.frequency_hz),
      })
      setEstimateResult(est)

      const win = await energyWindow({
        e_current_kj: n(singleForm.e_current_kj) ?? est.energy_kj,
        e_min_kj: n(singleForm.e_min_kj),
        e_ideal_kj: n(singleForm.e_ideal_kj),
        e_max_kj: n(singleForm.e_max_kj),
      })
      setWindowResult(win)

      if (
        n(singleForm.e_ideal_kj) != null &&
        n(costForm.production_volume_annual) != null
      ) {
        const eCur = n(singleForm.e_current_kj) ?? est.energy_kj
        const eIdeal = n(singleForm.e_ideal_kj)!
        if (eCur > 0 && eIdeal > 0) {
          const cost = await energyCost({
            e_current_kj: eCur,
            e_ideal_kj: eIdeal,
            spots_per_part: 1,
            production_volume_annual: parseInt(costForm.production_volume_annual),
            tariff_eur_per_kwh: parseFloat(costForm.tariff_eur_per_kwh),
            tariff_usd_per_kwh: parseFloat(costForm.tariff_usd_per_kwh),
          })
          setCostResult(cost)
        }
      }
    } catch (e: unknown) {
      setSingleError(e instanceof Error ? e.message : 'API error')
    } finally {
      setSingleLoading(false)
    }
  }

  // ── Multi: aggregate ───────────────────────────────────────────────────────
  async function runMulti() {
    setMultiLoading(true)
    setMultiError('')
    setAggrResult(null)
    try {
      const specs: WeldPointEnergySpecIn[] = multiRows.map(r => ({
        point_code: r.point_code || 'UNNAMED',
        group_name: r.group_name || 'DEFAULT',
        e_current_kj: n(r.e_current_kj),
        e_min_kj: n(r.e_min_kj),
        e_ideal_kj: n(r.e_ideal_kj),
        e_max_kj: n(r.e_max_kj),
      }))
      const res = await energyAggregate({
        points: specs,
        production_volume_annual: parseInt(multiCostForm.production_volume_annual) || undefined,
        tariff_eur_per_kwh: parseFloat(multiCostForm.tariff_eur_per_kwh) || undefined,
        tariff_usd_per_kwh: parseFloat(multiCostForm.tariff_usd_per_kwh) || undefined,
        pareto_top_n: 10,
      })
      setAggrResult(res)
    } catch (e: unknown) {
      setMultiError(e instanceof Error ? e.message : 'API error')
    } finally {
      setMultiLoading(false)
    }
  }

  function addRow() {
    setMultiRows(prev => [...prev, {
      id: uid(), point_code: `WP-${String(prev.length + 1).padStart(3, '0')}`,
      group_name: 'Group-A', e_current_kj: '', e_min_kj: '', e_ideal_kj: '', e_max_kj: '',
    }])
  }

  function updateRow(id: string, field: keyof MultiRow, val: string) {
    setMultiRows(prev => prev.map(r => r.id === id ? { ...r, [field]: val } : r))
  }

  function removeRow(id: string) {
    setMultiRows(prev => prev.filter(r => r.id !== id))
  }

  // ── Scenario (P2-B) ───────────────────────────────────────────────────────
  async function runScenario() {
    setScenLoading(true)
    setScenError('')
    setScenResult(null)
    try {
      const res = await energyScenarioCompare({
        points: scenRows.map(r => ({
          point_code: r.point_code || 'UNNAMED',
          group_name: r.group_name || 'DEFAULT',
          e_min_kj: n(r.e_min_kj),
          e_ideal_kj: n(r.e_ideal_kj),
          e_max_kj: n(r.e_max_kj),
          baseline_e_current_kj: n(r.baseline_e_current_kj),
          proposed_e_current_kj: n(r.proposed_e_current_kj),
        })),
        production_volume_annual: parseInt(scenCostForm.production_volume_annual) || undefined,
        tariff_eur_per_kwh: parseFloat(scenCostForm.tariff_eur_per_kwh) || undefined,
        tariff_usd_per_kwh: parseFloat(scenCostForm.tariff_usd_per_kwh) || undefined,
      })
      setScenResult(res)
    } catch (e: unknown) {
      setScenError(e instanceof Error ? e.message : 'API error')
    } finally {
      setScenLoading(false)
    }
  }

  function addScenRow() {
    setScenarRows(prev => [...prev, {
      id: uid(), point_code: `WP-${String(prev.length + 1).padStart(3, '0')}`,
      group_name: 'Group-A', e_min_kj: '', e_ideal_kj: '', e_max_kj: '',
      baseline_e_current_kj: '', proposed_e_current_kj: '',
    }])
  }

  function updateScenRow(id: string, field: keyof ScenarioRow, val: string) {
    setScenarRows(prev => prev.map(r => r.id === id ? { ...r, [field]: val } : r))
  }

  function removeScenRow(id: string) {
    setScenarRows(prev => prev.filter(r => r.id !== id))
  }

  // ── Dashboard (P2-D) ──────────────────────────────────────────────────────
  async function runDashboard() {
    setDashLoading(true)
    setDashError('')
    setDashResult(null)
    try {
      const specs: WeldPointEnergySpecIn[] = dashRows.map(r => ({
        point_code: r.point_code || 'UNNAMED',
        group_name: r.group_name || 'DEFAULT',
        e_current_kj: n(r.e_current_kj),
        e_min_kj: n(r.e_min_kj),
        e_ideal_kj: n(r.e_ideal_kj),
        e_max_kj: n(r.e_max_kj),
      }))
      const res = await energyDashboard({
        points: specs,
        production_volume_annual: parseInt(dashCostForm.production_volume_annual) || undefined,
        tariff_eur_per_kwh: parseFloat(dashCostForm.tariff_eur_per_kwh) || undefined,
        tariff_usd_per_kwh: parseFloat(dashCostForm.tariff_usd_per_kwh) || undefined,
        pareto_top_n: 50,
      })
      setDashResult(res)
    } catch (e: unknown) {
      setDashError(e instanceof Error ? e.message : 'API error')
    } finally {
      setDashLoading(false)
    }
  }

  function addDashRow() {
    setDashRows(prev => [...prev, {
      id: uid(), point_code: `WP-${String(prev.length + 1).padStart(3, '0')}`,
      group_name: 'Group-A', e_current_kj: '', e_min_kj: '', e_ideal_kj: '', e_max_kj: '',
    }])
  }

  function updateDashRow(id: string, field: keyof MultiRow, val: string) {
    setDashRows(prev => prev.map(r => r.id === id ? { ...r, [field]: val } : r))
  }

  function removeDashRow(id: string) {
    setDashRows(prev => prev.filter(r => r.id !== id))
  }

  // ── Map (P2-A) ────────────────────────────────────────────────────────────
  async function runMap() {
    setMapLoading(true)
    setMapError('')
    setMapResult(null)
    setSelectedCode(null)
    try {
      const specs: WeldPointEnergySpecIn[] = mapRows.map(r => ({
        point_code: r.point_code || 'UNNAMED',
        group_name: r.group_name || 'DEFAULT',
        e_current_kj: n(r.e_current_kj),
        e_min_kj: n(r.e_min_kj),
        e_ideal_kj: n(r.e_ideal_kj),
        e_max_kj: n(r.e_max_kj),
      }))
      const res = await energyAggregate({
        points: specs,
        production_volume_annual: parseInt(mapCostForm.production_volume_annual) || undefined,
        tariff_eur_per_kwh: parseFloat(mapCostForm.tariff_eur_per_kwh) || undefined,
        tariff_usd_per_kwh: parseFloat(mapCostForm.tariff_usd_per_kwh) || undefined,
      })
      setMapResult(res)
    } catch (e: unknown) {
      setMapError(e instanceof Error ? e.message : 'API error')
    } finally {
      setMapLoading(false)
    }
  }

  function addMapRow() {
    setMapRows(prev => [...prev, {
      id: uid(), point_code: `WP-${String(prev.length + 1).padStart(3, '0')}`,
      group_name: 'Group-A', e_current_kj: '', e_min_kj: '', e_ideal_kj: '', e_max_kj: '', x: '', y: '',
    }])
  }

  function updateMapRow(id: string, field: keyof MapRow, val: string) {
    setMapRows(prev => prev.map(r => r.id === id ? { ...r, [field]: val } : r))
  }

  function removeMapRow(id: string) {
    setMapRows(prev => prev.filter(r => r.id !== id))
  }

  // ── Import ─────────────────────────────────────────────────────────────────
  async function runImportPreview() {
    if (!selectedFile && !csvText.trim()) {
      setImportError('Dosya seçin veya CSV yapıştırın / Select a file or paste CSV')
      return
    }
    setImportLoading(true)
    setImportError('')
    setImportResult(null)
    try {
      let res: ImportPreviewResponse
      if (selectedFile) {
        res = await energyImportPreviewFile(selectedFile)
      } else {
        res = await energyImportPreview({ csv_text: csvText })
      }
      setImportResult(res)
    } catch (e: unknown) {
      setImportError(e instanceof Error ? e.message : 'API error')
    } finally {
      setImportLoading(false)
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const isXlsx = file.name.toLowerCase().endsWith('.xlsx')
    if (isXlsx) {
      setSelectedFile(file)
      setCsvText('')
    } else {
      setSelectedFile(null)
      const reader = new FileReader()
      reader.onload = ev => { setCsvText(ev.target?.result as string ?? '') }
      reader.readAsText(file, 'utf-8')
    }
  }

  function downloadTemplate() {
    const url = '/api/v1/energy/import/template'
    const a = document.createElement('a')
    a.href = url
    a.download = 'energy_import_template.csv'
    a.click()
  }

  // ── P2-F: Export handler ──────────────────────────────────────────────────
  async function runExport() {
    const sourceRows = dashRows.length > 0 ? dashRows : multiRows
    if (sourceRows.length === 0) {
      setExportError('No weld points to export. Add points in the Multi or Dashboard tab first.')
      return
    }
    setExportLoading(true)
    setExportError('')
    setExportSuccess('')
    try {
      const dashCost = dashCostForm
      const req = {
        points: sourceRows.map(r => ({
          point_code: r.point_code,
          group_name: r.group_name,
          e_current_kj: n(r.e_current_kj),
          e_min_kj: n(r.e_min_kj),
          e_ideal_kj: n(r.e_ideal_kj),
          e_max_kj: n(r.e_max_kj),
        })),
        production_volume_annual: n(dashCost.production_volume_annual) != null
          ? Math.round(n(dashCost.production_volume_annual)!) : undefined,
        tariff_eur_per_kwh: n(dashCost.tariff_eur_per_kwh) ?? undefined,
        tariff_usd_per_kwh: n(dashCost.tariff_usd_per_kwh) ?? undefined,
        project_id: exportProjectId || undefined,
        project_name: exportProjectName || undefined,
        part_id: exportPartId || undefined,
        passport_id: exportPassportId || undefined,
        report_language: exportLang,
        analyst_name: exportAnalyst || undefined,
        report_title: exportTitle || undefined,
      }
      const { filename } = await downloadEnergyReport(req, exportFormat)
      setExportSuccess(`${rm.successPrefix} ${filename}`)
    } catch (e: unknown) {
      setExportError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setExportLoading(false)
    }
  }

  // ── Status label helper ────────────────────────────────────────────────────
  function statusLabel(s: string): string {
    const map: Record<string, string> = {
      NOT_ESTABLISHED: p.statusNotEstablished,
      IN_WINDOW: p.statusInWindow,
      BELOW_MIN: p.statusBelowMin,
      ABOVE_MAX: p.statusAboveMax,
      E_CURRENT_ABSENT: p.statusCurrentAbsent,
    }
    return map[s] ?? s
  }

  const tabStyle = (active: boolean) => ({
    padding: '6px 16px',
    cursor: 'pointer',
    border: '1px solid var(--border)',
    borderRadius: 'var(--r-md)',
    background: active ? 'var(--accent-soft)' : 'transparent',
    color: active ? 'var(--accent)' : 'var(--text-secondary)',
    fontWeight: active ? 600 : 400,
    fontSize: 'var(--fs-sm)',
    borderColor: active ? 'var(--accent)' : 'var(--border)',
  })

  const grid2 = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-3)' } as const
  const grid5 = { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 'var(--sp-3)', marginBottom: 'var(--sp-4)' } as const

  return (
    <div style={{ padding: 'var(--sp-5) var(--sp-6)', maxWidth: 1100, margin: '0 auto' }}>
      {/* Page header */}
      <div className="page-header" style={{ marginBottom: 'var(--sp-5)' }}>
        <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--accent)', letterSpacing: '0.08em', marginBottom: 4, fontWeight: 600 }}>
          {p.kicker}
        </div>
        <h1>{p.title}</h1>
        <p className="subtitle">{p.subtitle}</p>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 'var(--sp-5)', flexWrap: 'wrap' }}>
        {(['single', 'multi', 'dashboard', 'map', 'scenario', 'import', 'export', 'help'] as Tab[]).map(t => (
          <button key={t} type="button" style={tabStyle(tab === t)} onClick={() => setTab(t)}>
            {{ single: 'Tek Nokta / Single', multi: 'Çok Nokta / Multi', dashboard: dm.tabLabel, map: 'Parça Haritası / Part Map', scenario: sm.tabLabel, import: 'İçe Aktar / Import', export: rm.tabLabel, help: 'Yardım / Help' }[t]}
          </button>
        ))}
      </div>

      {/* ── Single-point tab ────────────────────────────────────────────── */}
      {tab === 'single' && (
        <>
          <Panel title="I²Rt Enerji Hesabı">
            <div style={grid2}>
              <FieldRow label={p.labelCurrentKa} value={singleForm.current_ka}
                onChange={v => setSingleForm(f => ({ ...f, current_ka: v }))}
                step="0.1" min="0" help={p.labelCurrentKaHint} />
              <FieldRow label={p.labelResistanceUohm} value={singleForm.resistance_micro_ohm}
                onChange={v => setSingleForm(f => ({ ...f, resistance_micro_ohm: v }))}
                step="1" min="0" />
              <FieldRow label={p.labelWeldCycles} value={singleForm.weld_cycles}
                onChange={v => setSingleForm(f => ({ ...f, weld_cycles: v }))}
                step="1" min="1" />
              <FieldRow label={p.labelFrequencyHz} value={singleForm.frequency_hz}
                onChange={v => setSingleForm(f => ({ ...f, frequency_hz: v }))}
                step="1" min="1" />
            </div>
          </Panel>

          <Panel title="Enerji Penceresi / Energy Window">
            <div style={grid2}>
              <FieldRow label={p.labelECurrentKj + ' (boş → hesaplanan / empty → computed)'}
                value={singleForm.e_current_kj}
                onChange={v => setSingleForm(f => ({ ...f, e_current_kj: v }))}
                placeholder="boş bırakın / leave blank"
                step="0.001" min="0" />
              <FieldRow label={p.labelEMinKj + ' (opsiyonel)'}
                value={singleForm.e_min_kj}
                onChange={v => setSingleForm(f => ({ ...f, e_min_kj: v }))}
                placeholder="boş → NOT_ESTABLISHED"
                step="0.001" min="0"
                help="E_min ancak doğrulanmış deney verisi varsa girilmelidir. / E_min only when validated by experiment." />
              <FieldRow label={p.labelEIdealKj + ' (opsiyonel)'}
                value={singleForm.e_ideal_kj}
                onChange={v => setSingleForm(f => ({ ...f, e_ideal_kj: v }))}
                placeholder="boş → NOT_ESTABLISHED"
                step="0.001" min="0" />
              <FieldRow label={p.labelEMaxKj + ' (opsiyonel)'}
                value={singleForm.e_max_kj}
                onChange={v => setSingleForm(f => ({ ...f, e_max_kj: v }))}
                placeholder="boş → NOT_ESTABLISHED"
                step="0.001" min="0" />
            </div>
          </Panel>

          <Panel title="Maliyet / Cost">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-3)' }}>
              <FieldRow label={p.labelVolumeAnnual} value={costForm.production_volume_annual}
                onChange={v => setCostForm(f => ({ ...f, production_volume_annual: v }))}
                step="1000" min="1" />
              <FieldRow label={p.labelTariffEur} value={costForm.tariff_eur_per_kwh}
                onChange={v => setCostForm(f => ({ ...f, tariff_eur_per_kwh: v }))}
                step="0.01" min="0" />
              <FieldRow label={p.labelTariffUsd} value={costForm.tariff_usd_per_kwh}
                onChange={v => setCostForm(f => ({ ...f, tariff_usd_per_kwh: v }))}
                step="0.01" min="0" />
            </div>
          </Panel>

          <button
            type="button"
            className="btn btn-primary"
            onClick={runSingle}
            disabled={singleLoading}
            style={{ marginBottom: 'var(--sp-5)' }}
          >
            {singleLoading ? '…' : p.btnEstimate}
          </button>

          {singleError && (
            <div style={{ color: 'var(--danger)', marginBottom: 'var(--sp-3)', fontSize: 'var(--fs-sm)' }}>
              {p.errorTitle}: {singleError}
            </div>
          )}

          {estimateResult && (
            <>
              <div style={grid5}>
                <KpiCard label={p.indicatorEMin} value={windowResult?.e_min_kj != null ? fmt(windowResult.e_min_kj, 4) : '—'} unit={p.unitKjSpot} accent="var(--info)" />
                <KpiCard label={p.indicatorEIdeal} value={windowResult?.e_ideal_kj != null ? fmt(windowResult.e_ideal_kj, 4) : '—'} unit={p.unitKjSpot} accent="var(--ok)" />
                <KpiCard label={p.indicatorEMax} value={windowResult?.e_max_kj != null ? fmt(windowResult.e_max_kj, 4) : '—'} unit={p.unitKjSpot} accent="var(--warn)" />
                <KpiCard
                  label={p.indicatorECurrent}
                  value={windowResult?.e_current_kj != null ? fmt(windowResult.e_current_kj, 4) : fmt(estimateResult.energy_kj, 4)}
                  unit={p.unitKjSpot}
                  accent="var(--accent)"
                />
                <KpiCard
                  label={p.indicatorDeltaE}
                  value={windowResult?.delta_e_signed_kj != null ? fmt(windowResult.delta_e_signed_kj, 4) : '—'}
                  unit={p.unitKjSpot}
                  accent={
                    windowResult?.delta_e_signed_kj == null ? undefined :
                    windowResult.delta_e_signed_kj > 0 ? 'var(--warn)' :
                    windowResult.delta_e_signed_kj < 0 ? 'var(--danger)' : 'var(--ok)'
                  }
                  note={windowResult?.quality_risk_flag ? p.qualityRiskWarning : undefined}
                />
              </div>

              {windowResult && (
                <Panel title="Enerji Karşılaştırma / Energy Comparison">
                  <div style={{ display: 'flex', gap: 'var(--sp-6)', flexWrap: 'wrap', alignItems: 'flex-start' }}>
                    <EnergyBarChart
                      e_min={windowResult.e_min_kj}
                      e_ideal={windowResult.e_ideal_kj}
                      e_current={windowResult.e_current_kj}
                      e_max={windowResult.e_max_kj}
                    />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>Durum / Status:</span>
                        <StatusBadge status={windowResult.window_status as EnergyWindowStatus} label={statusLabel(windowResult.window_status)} />
                      </div>
                      {windowResult.window_status === 'NOT_ESTABLISHED' && (
                        <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', maxWidth: 280 }}>
                          {p.notEstablishedHint}
                        </div>
                      )}
                      <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>
                        E_current (hesaplanan): <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{fmt(estimateResult.energy_kj, 4)} kJ</span>
                      </div>
                      <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
                        = {fmt(estimateResult.current_ka)} kA × {fmt(estimateResult.resistance_micro_ohm)} µΩ × {fmt(estimateResult.time_s, 4)} s
                      </div>
                      {windowResult.e_margin_upper_kj != null && (
                        <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>
                          Üst marj / Upper margin: <span style={{ fontFamily: 'var(--font-mono)' }}>{fmt(windowResult.e_margin_upper_kj, 4)} kJ</span>
                        </div>
                      )}
                      {windowResult.e_margin_lower_kj != null && (
                        <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>
                          Alt marj / Lower margin: <span style={{ fontFamily: 'var(--font-mono)' }}>{fmt(windowResult.e_margin_lower_kj, 4)} kJ</span>
                        </div>
                      )}
                    </div>
                  </div>
                </Panel>
              )}

              {costResult && (
                <Panel title={p.resultCostTitle}>
                  <div style={grid2}>
                    <KpiCard label={p.costPerSpot} value={fmt(costResult.delta_e_spot_kwh * 1000, 4)} unit="Wh/punta" />
                    <KpiCard label={p.costAnnual + ' EUR'} value={fmt(costResult.cost_diff_eur_annual, 2)} unit="EUR/yıl" accent="var(--ok)" />
                    <KpiCard label={p.costPer1000Parts + ' EUR'} value={fmt(costResult.cost_diff_eur_per_1000_parts, 2)} unit="EUR / 1.000 parça" />
                    <KpiCard label={p.costAnnual + ' USD'} value={fmt(costResult.cost_diff_usd_annual, 2)} unit="USD/yıl" accent="var(--info)" />
                  </div>
                  <DisclaimerBanner text={costResult.disclaimer} />
                </Panel>
              )}

              <Panel title="I²Rt Hesap Detayı / Calculation Detail" accent="var(--border)">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-2)', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                  <span>E = {fmt(estimateResult.energy_j, 2)} J</span>
                  <span>= {fmt(estimateResult.energy_kj, 4)} kJ</span>
                  <span>= {fmt(estimateResult.energy_wh, 6)} Wh</span>
                  <span>= {fmt(estimateResult.energy_kwh, 8)} kWh</span>
                  <span>t = {fmt(estimateResult.time_s, 4)} s</span>
                  <span>f = {fmt(estimateResult.frequency_hz)} Hz</span>
                </div>
                <details style={{ marginTop: 'var(--sp-3)' }}>
                  <summary style={{ cursor: 'pointer', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
                    Varsayımlar / Assumptions ({estimateResult.assumptions.length})
                  </summary>
                  <ul style={{ marginTop: 8, paddingLeft: 16, fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', lineHeight: 1.7 }}>
                    {estimateResult.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                  </ul>
                </details>
              </Panel>
            </>
          )}
        </>
      )}

      {/* ── Multi-spot tab ───────────────────────────────────────────────── */}
      {tab === 'multi' && (
        <>
          <Panel title="Kaynak Noktaları / Weld Points">
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Nokta Kodu', 'Grup', 'E_cur (kJ)', 'E_min (kJ)', 'E_ideal (kJ)', 'E_max (kJ)', ''].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {multiRows.map(row => (
                    <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      {(['point_code', 'group_name', 'e_current_kj', 'e_min_kj', 'e_ideal_kj', 'e_max_kj'] as const).map(f => (
                        <td key={f} style={{ padding: '4px 6px' }}>
                          <input
                            type={f.startsWith('e_') ? 'number' : 'text'}
                            value={row[f]}
                            onChange={e => updateRow(row.id, f, e.target.value)}
                            step={f.startsWith('e_') ? '0.001' : undefined}
                            min={f.startsWith('e_') ? '0' : undefined}
                            style={{
                              background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
                              borderRadius: 3, padding: '3px 6px', color: 'var(--text-primary)',
                              fontSize: 'var(--fs-sm)', width: f === 'point_code' ? 90 : f === 'group_name' ? 80 : 70,
                              fontFamily: 'var(--font-mono)',
                            }}
                          />
                        </td>
                      ))}
                      <td style={{ padding: '4px 6px' }}>
                        <button type="button" onClick={() => removeRow(row.id)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 'var(--fs-xs)' }}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button type="button" onClick={addRow}
              style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--fs-sm)', color: 'var(--accent)', background: 'none', border: '1px dashed var(--accent)', borderRadius: 'var(--r-md)', padding: '4px 12px', cursor: 'pointer' }}>
              + Nokta Ekle / Add Point
            </button>
          </Panel>

          <Panel title="Üretim & Tarife / Production & Tariff">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-3)' }}>
              <FieldRow label={p.labelVolumeAnnual} value={multiCostForm.production_volume_annual}
                onChange={v => setMultiCostForm(f => ({ ...f, production_volume_annual: v }))} step="1000" min="1" />
              <FieldRow label={p.labelTariffEur} value={multiCostForm.tariff_eur_per_kwh}
                onChange={v => setMultiCostForm(f => ({ ...f, tariff_eur_per_kwh: v }))} step="0.01" min="0" />
              <FieldRow label={p.labelTariffUsd} value={multiCostForm.tariff_usd_per_kwh}
                onChange={v => setMultiCostForm(f => ({ ...f, tariff_usd_per_kwh: v }))} step="0.01" min="0" />
            </div>
          </Panel>

          <button type="button" className="btn btn-primary" onClick={runMulti} disabled={multiLoading}
            style={{ marginBottom: 'var(--sp-4)' }}>
            {multiLoading ? '…' : p.btnEvaluateWindow}
          </button>

          {multiError && <div style={{ color: 'var(--danger)', marginBottom: 'var(--sp-3)', fontSize: 'var(--fs-sm)' }}>{multiError}</div>}

          {aggrResult && (
            <>
              {/* Part KPI summary */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--sp-3)', marginBottom: 'var(--sp-4)' }}>
                <KpiCard label="Toplam E_current / Part" value={fmt(aggrResult.part_e_current_total_kj, 3)} unit="kJ" accent="var(--accent)" />
                <KpiCard label="Toplam E_excess / Part" value={fmt(aggrResult.part_e_excess_total_kj, 3)} unit="kJ" accent="var(--warn)" />
                <KpiCard label="Yıllık Enerji Farkı" value={fmt(aggrResult.annual_e_excess_total_kwh, 1)} unit="kWh/yıl" accent="var(--info)" />
                <KpiCard label="Yıllık Maliyet EUR" value={fmt(aggrResult.annual_cost_eur, 2)} unit="EUR/yıl" accent="var(--ok)" />
              </div>

              {/* Status summary chips */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 'var(--sp-4)' }}>
                <StatusBadge status="IN_WINDOW" label={`${aggrResult.part_points_in_window} ${p.statusInWindow}`} />
                <StatusBadge status="BELOW_MIN" label={`${aggrResult.part_points_below_min} ${p.statusBelowMin}`} />
                <StatusBadge status="ABOVE_MAX" label={`${aggrResult.part_points_above_max} ${p.statusAboveMax}`} />
                <StatusBadge status="NOT_ESTABLISHED" label={`${aggrResult.part_points_not_established} ${p.statusNotEstablished}`} />
              </div>

              {/* Per-point table */}
              <Panel title="Nokta Bazlı Sonuçlar / Per-Point Results">
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border)' }}>
                        {['Nokta', 'Grup', 'E_cur', 'E_min', 'E_ideal', 'E_max', 'ΔE', 'Fazla', 'Durum'].map(h => (
                          <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {aggrResult.rows.map((row, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: row.quality_risk_flag ? 'var(--danger-soft)' : row.out_of_window ? 'var(--warn-soft)' : undefined }}>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{row.point_code}</td>
                          <td style={{ padding: '4px 8px', color: 'var(--text-secondary)' }}>{row.group_name}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(row.e_current_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--info)' }}>{fmt(row.e_min_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--ok)' }}>{fmt(row.e_ideal_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--warn)' }}>{fmt(row.e_max_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: row.delta_e_signed_kj != null && row.delta_e_signed_kj > 0 ? 'var(--warn)' : row.delta_e_signed_kj != null && row.delta_e_signed_kj < 0 ? 'var(--danger)' : undefined }}>
                            {row.delta_e_signed_kj != null ? (row.delta_e_signed_kj >= 0 ? '+' : '') + fmt(row.delta_e_signed_kj, 3) : '—'}
                          </td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--warn)' }}>{fmt(row.e_excess_potential_kj, 3)}</td>
                          <td style={{ padding: '4px 8px' }}>
                            <StatusBadge status={row.window_status} label={statusLabel(row.window_status)} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              {/* Group summaries */}
              {aggrResult.groups.length > 1 && (
                <Panel title="Grup Özeti / Group Summary">
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                          {['Grup', 'Nokta', 'E_cur Toplam', 'E_ideal Toplam', 'ΔE Toplam', 'Fazla Toplam', 'Pencere İçi', 'Risk'].map(h => (
                            <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {aggrResult.groups.map((g, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                            <td style={{ padding: '4px 8px', fontWeight: 600 }}>{g.group_name}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{g.point_count}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{fmt(g.e_current_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--ok)' }}>{fmt(g.e_ideal_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{g.delta_total_kj != null ? (g.delta_total_kj >= 0 ? '+' : '') + fmt(g.delta_total_kj, 3) : '—'}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--warn)' }}>{fmt(g.e_excess_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px' }}>{g.points_in_window} / {g.point_count}</td>
                            <td style={{ padding: '4px 8px', color: g.points_quality_risk > 0 ? 'var(--danger)' : 'var(--ok)' }}>{g.points_quality_risk}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Panel>
              )}

              {/* Pareto chart */}
              {aggrResult.pareto_by_excess.length > 0 && (
                <Panel title="Enerji Fazlası Pareto / Energy Excess Pareto (Top 10)">
                  <ParetoChart rows={aggrResult.pareto_by_excess} />
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginTop: 8 }}>
                    Turuncu çubuk: enerji fazlası kJ/punta. Mavi çizgi: kümülatif %. / Orange bar: excess kJ/spot. Blue line: cumulative %.
                  </div>
                </Panel>
              )}

              <DisclaimerBanner text={aggrResult.disclaimer} />
            </>
          )}
        </>
      )}

      {/* ── Scenario comparison tab (P2-B) ──────────────────────────────── */}
      {tab === 'scenario' && (
        <>
          <div style={{ background: 'var(--warn-soft)', border: '1px solid var(--warn)', borderRadius: 'var(--r-md)', padding: 'var(--sp-3) var(--sp-4)', marginBottom: 'var(--sp-4)', fontSize: 'var(--fs-xs)', color: 'var(--warn)' }}>
            ⚠ {sm.evaluationNote}
          </div>

          <Panel title={sm.panelPoints}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Nokta Kodu', 'Grup', 'E_min (kJ)', 'E_ideal (kJ)', 'E_max (kJ)', sm.labelBaseline, sm.labelProposed, ''].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {scenRows.map(row => (
                    <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      {(['point_code', 'group_name', 'e_min_kj', 'e_ideal_kj', 'e_max_kj', 'baseline_e_current_kj', 'proposed_e_current_kj'] as const).map(f => (
                        <td key={f} style={{ padding: '4px 6px' }}>
                          <input
                            type={f === 'point_code' || f === 'group_name' ? 'text' : 'number'}
                            value={row[f]}
                            onChange={e => updateScenRow(row.id, f, e.target.value)}
                            step={f !== 'point_code' && f !== 'group_name' ? '0.001' : undefined}
                            min={f !== 'point_code' && f !== 'group_name' ? '0' : undefined}
                            style={{
                              background: f === 'baseline_e_current_kj' ? 'var(--bg-surface-2)' : f === 'proposed_e_current_kj' ? 'color-mix(in srgb, var(--bg-surface-2) 70%, var(--accent-soft))' : 'var(--bg-surface-2)',
                              border: `1px solid ${f === 'proposed_e_current_kj' ? 'var(--accent)' : 'var(--border)'}`,
                              borderRadius: 3, padding: '3px 6px', color: 'var(--text-primary)',
                              fontSize: 'var(--fs-sm)',
                              width: f === 'point_code' ? 90 : f === 'group_name' ? 80 : 72,
                              fontFamily: 'var(--font-mono)',
                            }}
                          />
                        </td>
                      ))}
                      <td style={{ padding: '4px 6px' }}>
                        <button type="button" onClick={() => removeScenRow(row.id)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 'var(--fs-xs)' }}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button type="button" onClick={addScenRow}
              style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--fs-sm)', color: 'var(--accent)', background: 'none', border: '1px dashed var(--accent)', borderRadius: 'var(--r-md)', padding: '4px 12px', cursor: 'pointer' }}>
              + Nokta Ekle / Add Point
            </button>
          </Panel>

          <Panel title="Üretim & Tarife / Production & Tariff">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-3)' }}>
              <FieldRow label={p.labelVolumeAnnual} value={scenCostForm.production_volume_annual}
                onChange={v => setScenCostForm(f => ({ ...f, production_volume_annual: v }))} step="1000" min="1" />
              <FieldRow label={p.labelTariffEur} value={scenCostForm.tariff_eur_per_kwh}
                onChange={v => setScenCostForm(f => ({ ...f, tariff_eur_per_kwh: v }))} step="0.01" min="0" />
              <FieldRow label={p.labelTariffUsd} value={scenCostForm.tariff_usd_per_kwh}
                onChange={v => setScenCostForm(f => ({ ...f, tariff_usd_per_kwh: v }))} step="0.01" min="0" />
            </div>
          </Panel>

          <button type="button" className="btn btn-primary" onClick={runScenario} disabled={scenLoading}
            style={{ marginBottom: 'var(--sp-4)' }}>
            {scenLoading ? '…' : sm.btnCompare}
          </button>

          {scenError && <div style={{ color: 'var(--danger)', marginBottom: 'var(--sp-3)', fontSize: 'var(--fs-sm)' }}>{scenError}</div>}

          {scenResult && (
            <>
              {/* Summary KPIs */}
              <Panel title={sm.panelSummary}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--sp-3)', marginBottom: 'var(--sp-3)' }}>
                  <KpiCard label="Mevcut Pencere İçi / Baseline In-Window"
                    value={String(scenResult.baseline_points_in_window)}
                    unit={`/ ${scenResult.points.length} nokta`} />
                  <KpiCard label="Önerilen Pencere İçi / Proposed In-Window"
                    value={String(scenResult.proposed_points_in_window)}
                    unit={`/ ${scenResult.points.length} nokta`}
                    accent={scenResult.proposed_points_in_window > scenResult.baseline_points_in_window ? 'var(--ok)' : undefined} />
                  <KpiCard label="Yıllık Tasarruf / Annual Saving EUR"
                    value={scenResult.annual_cost_saving_eur != null ? fmt(scenResult.annual_cost_saving_eur, 2) : '—'}
                    unit="EUR/yıl"
                    accent={scenResult.annual_cost_saving_eur != null && scenResult.annual_cost_saving_eur > 0 ? 'var(--ok)' : undefined} />
                  <KpiCard label="Parça Enerji Farkı / Part Energy Change"
                    value={scenResult.part_e_reduction_kj != null ? (scenResult.part_e_reduction_kj >= 0 ? '−' : '+') + fmt(Math.abs(scenResult.part_e_reduction_kj), 4) : '—'}
                    unit="kJ/parça"
                    accent={scenResult.part_e_reduction_kj != null && scenResult.part_e_reduction_kj > 0 ? 'var(--ok)' : 'var(--warn)'} />
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {scenResult.total_improved > 0 && (
                    <StatusBadge status="IN_WINDOW" label={`${scenResult.total_improved} ${sm.improvedLabel}`} />
                  )}
                  {scenResult.total_degraded > 0 && (
                    <StatusBadge status="BELOW_MIN" label={`${scenResult.total_degraded} ${sm.degradedLabel}`} />
                  )}
                </div>
              </Panel>

              {/* Deviation chart */}
              <Panel title={sm.panelDeviationChart}>
                <DeviationBarChart points={scenResult.points} />
                <div style={{ display: 'flex', gap: 16, marginTop: 'var(--sp-2)', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
                  <span>▓ Mevcut / Baseline (faded)</span>
                  <span>▓ Önerilen / Proposed (solid, renk=durum)</span>
                </div>
              </Panel>

              {/* Per-point comparison table */}
              <Panel title={sm.panelPerPoint}>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--border)' }}>
                        {['Nokta', 'Grup', 'Mevcut E_cur', 'Mevcut Durum', 'Önerilen E_cur', 'Önerilen Durum', sm.colChange, 'Kalite'].map(h => (
                          <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {scenResult.points.map((pr, i) => {
                        const qualityColor = pr.quality_improved ? 'var(--ok-soft)' : pr.quality_degraded ? 'var(--danger-soft)' : undefined
                        return (
                          <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: qualityColor }}>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{pr.point_code}</td>
                            <td style={{ padding: '4px 8px', color: 'var(--text-secondary)' }}>{pr.group_name}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(pr.baseline_e_current_kj, 4)}</td>
                            <td style={{ padding: '4px 8px' }}>
                              <StatusBadge status={pr.baseline_window_status as EnergyWindowStatus} label={statusLabel(pr.baseline_window_status)} />
                            </td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(pr.proposed_e_current_kj, 4)}</td>
                            <td style={{ padding: '4px 8px' }}>
                              <StatusBadge status={pr.proposed_window_status as EnergyWindowStatus} label={statusLabel(pr.proposed_window_status)} />
                            </td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: pr.e_change_kj != null && pr.e_change_kj < 0 ? 'var(--ok)' : pr.e_change_kj != null && pr.e_change_kj > 0 ? 'var(--warn)' : undefined }}>
                              {pr.e_change_kj != null ? (pr.e_change_kj >= 0 ? '+' : '') + fmt(pr.e_change_kj, 4) : '—'}
                            </td>
                            <td style={{ padding: '4px 8px' }}>
                              {pr.quality_improved
                                ? <span style={{ color: 'var(--ok)', fontWeight: 600, fontSize: 'var(--fs-xs)' }}>{sm.improvedLabel}</span>
                                : pr.quality_degraded
                                ? <span style={{ color: 'var(--danger)', fontWeight: 600, fontSize: 'var(--fs-xs)' }}>{sm.degradedLabel}</span>
                                : <span style={{ color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)' }}>{sm.noChangeLabel}</span>}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </Panel>

              {/* Group comparison */}
              {scenResult.groups.length > 0 && (
                <Panel title={sm.panelGroups}>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                          {['Grup', 'Nokta', 'Mevcut E (kJ)', 'Önerilen E (kJ)', 'Azalma (kJ)', 'Mevcut IW', 'Önerilen IW', sm.colImproved, sm.colDegraded].map(h => (
                            <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {scenResult.groups.map((g, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                            <td style={{ padding: '4px 8px', fontWeight: 600 }}>{g.group_name}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{g.point_count}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(g.baseline_e_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{fmt(g.proposed_e_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: g.e_reduction_kj != null && g.e_reduction_kj > 0 ? 'var(--ok)' : 'var(--warn)' }}>
                              {g.e_reduction_kj != null ? (g.e_reduction_kj >= 0 ? '−' : '+') + fmt(Math.abs(g.e_reduction_kj), 3) : '—'}
                            </td>
                            <td style={{ padding: '4px 8px' }}>{g.baseline_in_window} / {g.point_count}</td>
                            <td style={{ padding: '4px 8px', color: g.proposed_in_window > g.baseline_in_window ? 'var(--ok)' : undefined }}>{g.proposed_in_window} / {g.point_count}</td>
                            <td style={{ padding: '4px 8px', color: 'var(--ok)' }}>{g.improved_count}</td>
                            <td style={{ padding: '4px 8px', color: g.degraded_count > 0 ? 'var(--danger)' : undefined }}>{g.degraded_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Panel>
              )}

              {/* Warnings */}
              {scenResult.points.some(pr => pr.warnings.length > 0) && (
                <Panel title={sm.warningsTitle} accent="var(--warn)">
                  {scenResult.points.flatMap(pr => pr.warnings).map((w, i) => (
                    <div key={i} style={{ fontSize: 'var(--fs-xs)', color: 'var(--warn)', marginBottom: 4 }}>⚠ {w}</div>
                  ))}
                </Panel>
              )}

              <DisclaimerBanner text={scenResult.disclaimer} />
            </>
          )}

          <Panel title={sm.helpTitle}>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, fontFamily: 'var(--font-sans)' }}>
              {sm.helpBody}
            </pre>
          </Panel>
        </>
      )}

      {/* ── Import tab ──────────────────────────────────────────────────── */}
      {tab === 'import' && (
        <>
          <Panel title="İçe Aktarma Şablonu / Import Template">
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--sp-3)', lineHeight: 1.6 }}>
              Önce şablonu indirin, doldurun (.csv veya .xlsx olarak kaydedin) ve aşağıya yükleyin veya yapıştırın. /
              Download the template, fill it in (save as .csv or .xlsx), then upload or paste below.
            </p>
            <button type="button" className="btn" onClick={downloadTemplate}>
              ⬇ energy_import_template.csv
            </button>
          </Panel>

          <Panel title="CSV / XLSX Yükle / Upload CSV or XLSX">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', flexWrap: 'wrap' }}>
                <input
                  type="file"
                  ref={fileRef}
                  accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                <button type="button" className="btn"
                  onClick={() => fileRef.current?.click()}>
                  📂 Dosya Seç / Choose File (.csv / .xlsx)
                </button>
                {selectedFile && (
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--ok)', fontFamily: 'var(--font-mono)' }}>
                    ✓ {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                )}
              </div>
              {!selectedFile && (
                <textarea
                  value={csvText}
                  onChange={e => { setCsvText(e.target.value); setSelectedFile(null) }}
                  rows={10}
                  placeholder="CSV içeriğini buraya yapıştırın / Paste CSV content here…"
                  style={{
                    background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
                    borderRadius: 'var(--r-md)', padding: 'var(--sp-3)',
                    color: 'var(--text-primary)', fontSize: 'var(--fs-sm)',
                    fontFamily: 'var(--font-mono)', resize: 'vertical',
                    width: '100%',
                  }}
                />
              )}
            </div>
          </Panel>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', marginBottom: 'var(--sp-4)' }}>
            <button type="button" className="btn btn-primary" onClick={runImportPreview} disabled={importLoading}>
              {importLoading ? '…' : 'Önizle / Preview'}
            </button>
            <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
              Veritabanına yazmadan önce doğrulama yapılır. / Validates without writing to database.
            </span>
          </div>

          {importError && <div style={{ color: 'var(--danger)', marginBottom: 'var(--sp-3)' }}>{importError}</div>}

          {importResult && (
            <>
              {importResult.formula_injection_detected && (
                <div style={{
                  background: 'var(--danger-soft)', border: '1px solid var(--danger)',
                  borderRadius: 'var(--r-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)',
                }}>
                  <strong style={{ color: 'var(--danger)' }}>⛔ Formül Enjeksiyonu Tespit Edildi / Formula Injection Detected</strong>
                  <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginTop: 4 }}>
                    Hücreler: {importResult.formula_injection_cells.join(', ')}<br />
                    Bu içe aktarma engellenmiştir. / This import is blocked.
                  </p>
                </div>
              )}

              <div style={{ display: 'flex', gap: 'var(--sp-4)', marginBottom: 'var(--sp-4)', flexWrap: 'wrap' }}>
                <KpiCard label="Toplam Satır" value={String(importResult.total_rows)} unit="satır" />
                <KpiCard label="Kabul" value={String(importResult.accepted_count)} unit="satır" accent="var(--ok)" />
                <KpiCard label="Reddedilen" value={String(importResult.rejected_count)} unit="satır" accent={importResult.rejected_count > 0 ? 'var(--danger)' : undefined} />
              </div>

              {importResult.errors.length > 0 && (
                <Panel title="Hatalar / Errors" accent="var(--danger)">
                  {importResult.errors.slice(0, 20).map((e, i) => (
                    <div key={i} style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>
                      <span style={{ color: 'var(--danger)', fontWeight: 600 }}>[{e.error_type}]</span> {e.message}
                    </div>
                  ))}
                </Panel>
              )}

              <Panel title="Önizleme / Preview Rows">
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border)' }}>
                        {['#', 'Nokta', 'Grup', 'E_cur', 'E_min', 'E_ideal', 'E_max', 'Not', 'Durum'].map(h => (
                          <th key={h} style={{ padding: '5px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {importResult.preview_rows.map(row => (
                        <tr key={row.row_number} style={{
                          borderBottom: '1px solid var(--border)',
                          background: row.accepted ? undefined : 'var(--danger-soft)',
                        }}>
                          <td style={{ padding: '4px 8px', color: 'var(--text-tertiary)' }}>{row.row_number}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{row.point_code}</td>
                          <td style={{ padding: '4px 8px' }}>{row.group_name}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(row.e_current_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(row.e_min_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(row.e_ideal_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(row.e_max_kj, 3)}</td>
                          <td style={{ padding: '4px 8px', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>{row.validation_note ?? ''}</td>
                          <td style={{ padding: '4px 8px' }}>
                            {row.accepted
                              ? <span style={{ color: 'var(--ok)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>✓ Kabul</span>
                              : <span style={{ color: 'var(--danger)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>✕ Red</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!importResult.has_blocking_errors && importResult.accepted_count > 0 && (
                  <div style={{
                    marginTop: 'var(--sp-4)', padding: 'var(--sp-3)',
                    background: 'var(--ok-soft)', border: '1px solid var(--ok)',
                    borderRadius: 'var(--r-md)', fontSize: 'var(--fs-sm)', color: 'var(--ok)',
                  }}>
                    ✓ {importResult.accepted_count} satır doğrulandı. Veritabanına yazmak için bağımsız onay gereklidir. /
                    {importResult.accepted_count} rows validated. A separate explicit confirmation is required before writing to database.
                  </div>
                )}
              </Panel>
            </>
          )}
        </>
      )}

      {/* ── Dashboard tab (P2-D) ────────────────────────────────────────── */}
      {tab === 'dashboard' && (
        <>
          {/* Engineering warning banner */}
          <div style={{ background: 'var(--warn-soft)', border: '1px solid var(--warn)', borderRadius: 'var(--r-md)', padding: 'var(--sp-3) var(--sp-4)', marginBottom: 'var(--sp-4)', fontSize: 'var(--fs-xs)', color: 'var(--warn)' }}>
            ⚠ {dm.disclaimerTitle}: Tüm değerler TAKDİRİ FAZLA ENERJİDİR — doğrulanmış elektrik veya finansal tasarruf değildir. / All values are THEORETICAL EXCESS ENERGY — not verified electricity or financial savings.
          </div>

          <Panel title={dm.panelPoints}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Nokta / Point', 'Grup / Group', 'E_min (kJ)', 'E_ideal (kJ)', 'E_max (kJ)', 'E_cur (kJ)', ''].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dashRows.map(row => (
                    <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      {(['point_code', 'group_name', 'e_min_kj', 'e_ideal_kj', 'e_max_kj', 'e_current_kj'] as const).map(f => (
                        <td key={f} style={{ padding: '4px 6px' }}>
                          <input
                            type={f === 'point_code' || f === 'group_name' ? 'text' : 'number'}
                            value={row[f]}
                            onChange={e => updateDashRow(row.id, f, e.target.value)}
                            step={f !== 'point_code' && f !== 'group_name' ? '0.001' : undefined}
                            min={f !== 'point_code' && f !== 'group_name' ? '0' : undefined}
                            style={{
                              background: f === 'e_current_kj' ? 'color-mix(in srgb, var(--bg-surface-2) 70%, var(--accent-soft))' : 'var(--bg-surface-2)',
                              border: `1px solid ${f === 'e_current_kj' ? 'var(--accent)' : 'var(--border)'}`,
                              borderRadius: 3, padding: '3px 6px', color: 'var(--text-primary)',
                              fontSize: 'var(--fs-sm)', width: f === 'point_code' ? 90 : f === 'group_name' ? 80 : 74,
                              fontFamily: 'var(--font-mono)',
                            }}
                          />
                        </td>
                      ))}
                      <td style={{ padding: '4px 6px' }}>
                        <button type="button" onClick={() => removeDashRow(row.id)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 'var(--fs-xs)' }}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button type="button" onClick={addDashRow}
              style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--fs-sm)', color: 'var(--accent)', background: 'none', border: '1px dashed var(--accent)', borderRadius: 'var(--r-md)', padding: '4px 12px', cursor: 'pointer' }}>
              + Nokta Ekle / Add Point
            </button>
          </Panel>

          <Panel title="Üretim & Tarife / Production & Tariff">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-3)' }}>
              <FieldRow label={p.labelVolumeAnnual} value={dashCostForm.production_volume_annual}
                onChange={v => setDashCostForm(f => ({ ...f, production_volume_annual: v }))} step="1000" min="1" />
              <FieldRow label={p.labelTariffEur} value={dashCostForm.tariff_eur_per_kwh}
                onChange={v => setDashCostForm(f => ({ ...f, tariff_eur_per_kwh: v }))} step="0.01" min="0" />
              <FieldRow label={p.labelTariffUsd} value={dashCostForm.tariff_usd_per_kwh}
                onChange={v => setDashCostForm(f => ({ ...f, tariff_usd_per_kwh: v }))} step="0.01" min="0" />
            </div>
          </Panel>

          <button type="button" className="btn btn-primary" onClick={runDashboard} disabled={dashLoading}
            style={{ marginBottom: 'var(--sp-4)' }}>
            {dashLoading ? '…' : dm.btnAnalyze}
          </button>

          {dashError && <div style={{ color: 'var(--danger)', marginBottom: 'var(--sp-3)', fontSize: 'var(--fs-sm)' }}>{dashError}</div>}

          {dashResult && (
            <>
              {/* Financial KPI cards */}
              <Panel title={dm.panelFinancial}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--sp-3)', marginBottom: 'var(--sp-3)' }}>
                  <KpiCard label={dm.labelAvgExcessSpot}
                    value={dashResult.financial.avg_excess_per_spot_kj != null ? fmt(dashResult.financial.avg_excess_per_spot_kj, 4) : '—'}
                    unit="kJ / kaynak noktası" />
                  <KpiCard label={dm.labelPartExcess}
                    value={dashResult.financial.part_excess_kj != null ? fmt(dashResult.financial.part_excess_kj, 4) : '—'}
                    unit="kJ / parça" />
                  <KpiCard label={dm.labelPer1000}
                    value={dashResult.financial.per_1000_parts_excess_kwh != null ? fmt(dashResult.financial.per_1000_parts_excess_kwh, 4) : '—'}
                    unit="kWh / 1000 parça" />
                  <KpiCard label={dm.labelAnnualExcess}
                    value={dashResult.financial.annual_excess_kwh != null ? fmt(dashResult.financial.annual_excess_kwh, 2) : '—'}
                    unit="kWh / yıl" />
                  <KpiCard label={dm.labelAnnualCostEur}
                    value={dashResult.financial.annual_cost_eur != null ? fmt(dashResult.financial.annual_cost_eur, 2) : '—'}
                    unit="EUR / yıl (TAKDİRİ)"
                    accent={dashResult.financial.annual_cost_eur != null && dashResult.financial.annual_cost_eur > 0 ? 'var(--warn)' : undefined}
                    note="Teorik — doğrulanmış tasarruf değil" />
                  <KpiCard label={dm.labelAnnualCostUsd}
                    value={dashResult.financial.annual_cost_usd != null ? fmt(dashResult.financial.annual_cost_usd, 2) : '—'}
                    unit="USD / yıl (TAKDİRİ)"
                    note="Teorik — doğrulanmış tasarruf değil" />
                </div>
                <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginTop: 8 }}>
                  Parça başı toplam: {fmt(dashResult.financial.part_excess_kwh, 6)} kWh&nbsp;|&nbsp;
                  {dashResult.financial.production_volume_annual?.toLocaleString() ?? '—'} parça/yıl&nbsp;|&nbsp;
                  EUR tarife: {dashResult.financial.tariff_eur_per_kwh ?? '—'} EUR/kWh&nbsp;|&nbsp;
                  USD tarife: {dashResult.financial.tariff_usd_per_kwh ?? '—'} USD/kWh
                </div>
                {dashResult.financial.part_excess_kj === null && (
                  <div style={{
                    marginTop: 'var(--sp-3)',
                    padding: 'var(--sp-3) var(--sp-4)',
                    background: 'var(--bg-surface-2)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--r-md)',
                    fontSize: 'var(--fs-xs)',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.6,
                  }}>
                    <strong style={{ color: 'var(--warn)' }}>
                      ℹ Finansal özet kullanılamıyor / Financial summary unavailable
                    </strong>
                    <div style={{ marginTop: 4 }}>
                      TR: Bir veya daha fazla kaynak noktasında enerji penceresi (E_min / E_ideal / E_max) belirlenmemiştir.
                      Finansal toplamlar yalnızca tüm noktalar için enerji penceresi tanımlandığında hesaplanır.
                      Kaynak noktaları tablosunda eksik değerleri girin.
                    </div>
                    <div style={{ marginTop: 2 }}>
                      EN: One or more weld points have NOT_ESTABLISHED energy windows (E_min / E_ideal / E_max missing).
                      Financial totals are calculated only when all points have a defined energy window.
                      Enter missing values in the weld points table above.
                    </div>
                  </div>
                )}
              </Panel>

              {/* Enhanced Pareto chart */}
              <Panel title={dm.panelPareto}>
                <EnhancedParetoChart rows={dashResult.pareto_detailed} />
                <div style={{ display: 'flex', gap: 12, marginTop: 'var(--sp-2)', flexWrap: 'wrap' }}>
                  {dashResult.pareto_detailed.slice(0, 3).map(pr => (
                    <div key={pr.point_code} style={{ fontSize: 'var(--fs-xs)', background: 'var(--bg-surface-2)', border: '1px solid var(--border)', borderRadius: 4, padding: '3px 8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{pr.point_code}</span>
                      {' '}— {fmt(pr.e_excess_kj, 4)} kJ&nbsp;
                      <span style={{ color: 'var(--warn)' }}>({pr.pct_of_total_excess?.toFixed(1)}%)</span>
                    </div>
                  ))}
                </div>

                {/* Pareto detail table */}
                <div style={{ marginTop: 'var(--sp-3)', overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-xs)' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border)' }}>
                        {['Nokta', 'Grup', dm.colExcess, dm.colPct, dm.colCumulative, 'Durum'].map(h => (
                          <th key={h} style={{ padding: '4px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {dashResult.pareto_detailed.map((pr, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                          <td style={{ padding: '3px 8px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{pr.point_code}</td>
                          <td style={{ padding: '3px 8px', color: 'var(--text-secondary)' }}>{pr.group_name}</td>
                          <td style={{ padding: '3px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(pr.e_excess_kj, 4)}</td>
                          <td style={{ padding: '3px 8px', fontFamily: 'var(--font-mono)', color: (pr.pct_of_total_excess ?? 0) > 20 ? 'var(--warn)' : undefined }}>
                            {pr.pct_of_total_excess != null ? pr.pct_of_total_excess.toFixed(1) + '%' : '—'}
                          </td>
                          <td style={{ padding: '3px 8px', fontFamily: 'var(--font-mono)' }}>
                            {pr.cumulative_pct != null ? pr.cumulative_pct.toFixed(1) + '%' : '—'}
                          </td>
                          <td style={{ padding: '3px 8px' }}>
                            <StatusBadge status={pr.window_status} label={statusLabel(pr.window_status)} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              {/* Energy window bullet chart */}
              <Panel title={dm.panelWindowChart}>
                <EnergyWindowBulletChart rows={dashResult.rows} />
              </Panel>

              {/* Sensitivity analysis */}
              <Panel title={dm.panelSensitivity}>
                <SensitivityTable
                  sensitivity={dashResult.sensitivity}
                  selectedVolume={dashResult.financial.production_volume_annual}
                  selectedTariffEur={dashResult.financial.tariff_eur_per_kwh}
                  labelVolume={dm.sensiVolume}
                  labelTariff={dm.sensiTariffEur}
                  labelNote={dm.sensiNote}
                />
              </Panel>

              {/* Group summary */}
              {dashResult.groups.length > 0 && (
                <Panel title={dm.panelGroups}>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                          {['Grup', 'Nokta', 'E_cur (kJ)', 'E_ideal (kJ)', 'Fazla (kJ)', 'Pencere İçi', 'Risk'].map(h => (
                            <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {dashResult.groups.map((g, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                            <td style={{ padding: '4px 8px', fontWeight: 600 }}>{g.group_name}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{g.point_count}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(g.e_current_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)' }}>{fmt(g.e_ideal_total_kj, 3)}</td>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', color: (g.e_excess_total_kj ?? 0) > 0 ? 'var(--warn)' : undefined }}>
                              {fmt(g.e_excess_total_kj, 3)}
                            </td>
                            <td style={{ padding: '4px 8px' }}>{g.points_in_window} / {g.point_count}</td>
                            <td style={{ padding: '4px 8px', color: g.points_quality_risk > 0 ? 'var(--danger)' : undefined }}>
                              {g.points_quality_risk}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Panel>
              )}

              <DisclaimerBanner text={dashResult.dashboard_disclaimer} />
            </>
          )}

          <Panel title={dm.helpTitle}>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, fontFamily: 'var(--font-sans)' }}>
              {dm.helpBody}
            </pre>
          </Panel>
        </>
      )}

      {/* ── Part map tab (P2-A) ─────────────────────────────────────────── */}
      {tab === 'map' && (
        <>
          <Panel title={pm.panelWeldPoints}>
            <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginBottom: 'var(--sp-3)', lineHeight: 1.6 }}>
              {pm.coordsNote}
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Nokta Kodu', 'Grup', 'E_cur (kJ)', 'E_min (kJ)', 'E_ideal (kJ)', 'E_max (kJ)', pm.labelX, pm.labelY, ''].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {mapRows.map(row => (
                    <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      {(['point_code', 'group_name', 'e_current_kj', 'e_min_kj', 'e_ideal_kj', 'e_max_kj'] as const).map(f => (
                        <td key={f} style={{ padding: '4px 6px' }}>
                          <input
                            type={f.startsWith('e_') ? 'number' : 'text'}
                            value={row[f]}
                            onChange={e => updateMapRow(row.id, f, e.target.value)}
                            step={f.startsWith('e_') ? '0.001' : undefined}
                            min={f.startsWith('e_') ? '0' : undefined}
                            style={{
                              background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
                              borderRadius: 3, padding: '3px 6px', color: 'var(--text-primary)',
                              fontSize: 'var(--fs-sm)', width: f === 'point_code' ? 90 : f === 'group_name' ? 80 : 70,
                              fontFamily: 'var(--font-mono)',
                            }}
                          />
                        </td>
                      ))}
                      {(['x', 'y'] as const).map(f => (
                        <td key={f} style={{ padding: '4px 6px' }}>
                          <input
                            type="number" value={row[f]}
                            onChange={e => updateMapRow(row.id, f, e.target.value)}
                            min="0" max="100" step="1" placeholder="—"
                            style={{
                              background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
                              borderRadius: 3, padding: '3px 6px', color: 'var(--text-primary)',
                              fontSize: 'var(--fs-sm)', width: 50, fontFamily: 'var(--font-mono)',
                            }}
                          />
                        </td>
                      ))}
                      <td style={{ padding: '4px 6px' }}>
                        <button type="button" onClick={() => removeMapRow(row.id)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 'var(--fs-xs)' }}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button type="button" onClick={addMapRow}
              style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--fs-sm)', color: 'var(--accent)', background: 'none', border: '1px dashed var(--accent)', borderRadius: 'var(--r-md)', padding: '4px 12px', cursor: 'pointer' }}>
              + Nokta Ekle / Add Point
            </button>
          </Panel>

          <Panel title="Üretim & Tarife / Production & Tariff">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--sp-3)' }}>
              <FieldRow label={p.labelVolumeAnnual} value={mapCostForm.production_volume_annual}
                onChange={v => setMapCostForm(f => ({ ...f, production_volume_annual: v }))} step="1000" min="1" />
              <FieldRow label={p.labelTariffEur} value={mapCostForm.tariff_eur_per_kwh}
                onChange={v => setMapCostForm(f => ({ ...f, tariff_eur_per_kwh: v }))} step="0.01" min="0" />
              <FieldRow label={p.labelTariffUsd} value={mapCostForm.tariff_usd_per_kwh}
                onChange={v => setMapCostForm(f => ({ ...f, tariff_usd_per_kwh: v }))} step="0.01" min="0" />
            </div>
          </Panel>

          <button type="button" className="btn btn-primary" onClick={runMap} disabled={mapLoading}
            style={{ marginBottom: 'var(--sp-4)' }}>
            {mapLoading ? '…' : pm.btnEvaluate}
          </button>

          {mapError && (
            <div style={{ color: 'var(--danger)', marginBottom: 'var(--sp-3)', fontSize: 'var(--fs-sm)' }}>{mapError}</div>
          )}

          {mapResult && (
            <>
              {/* Group filter chips */}
              {mapResult.groups.length > 1 && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 'var(--sp-4)', alignItems: 'center' }}>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginRight: 4 }}>Filtre / Filter:</span>
                  {[{ id: '', label: pm.filterAll }, ...mapResult.groups.map(g => ({ id: g.group_name, label: g.group_name }))].map(opt => (
                    <button key={opt.id} type="button" onClick={() => setGroupFilter(opt.id)}
                      style={{
                        padding: '3px 10px', borderRadius: 'var(--r-md)',
                        border: `1px solid ${groupFilter === opt.id ? 'var(--accent)' : 'var(--border)'}`,
                        background: groupFilter === opt.id ? 'var(--accent-soft)' : 'transparent',
                        color: groupFilter === opt.id ? 'var(--accent)' : 'var(--text-secondary)',
                        fontSize: 'var(--fs-xs)', cursor: 'pointer', fontWeight: groupFilter === opt.id ? 600 : 400,
                      }}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}

              {/* Map or schematic */}
              <Panel title={pm.panelMap}>
                {(() => {
                  const coordMap = new Map(
                    mapRows
                      .filter(r => r.x.trim() !== '' && r.y.trim() !== '')
                      .map(r => [r.point_code, { x: parseFloat(r.x), y: parseFloat(r.y) }] as const)
                      .filter(([, c]) => !isNaN(c.x) && !isNaN(c.y))
                  )
                  const hasCoords = mapResult.rows.some(r =>
                    (groupFilter === '' || r.group_name === groupFilter) && coordMap.has(r.point_code)
                  )
                  return hasCoords ? (
                    <PartMapSvg
                      apiRows={mapResult.rows}
                      mapRows={mapRows}
                      selected={selectedCode}
                      onSelect={setSelectedCode}
                      groupFilter={groupFilter}
                    />
                  ) : (
                    <>
                      <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginBottom: 'var(--sp-3)' }}>
                        {pm.schemFallback}
                      </div>
                      <SchematicFallback
                        apiRows={mapResult.rows}
                        selected={selectedCode}
                        onSelect={setSelectedCode}
                        groupFilter={groupFilter}
                      />
                    </>
                  )
                })()}

                {/* Legend */}
                <div style={{ marginTop: 'var(--sp-4)', borderTop: '1px solid var(--border)', paddingTop: 'var(--sp-3)' }}>
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: 6 }}>
                    {pm.legendTitle}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                    {(Object.keys(STATUS_HEX) as EnergyWindowStatus[]).map(s => (
                      <span key={s} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 'var(--fs-xs)' }}>
                        <span style={{ width: 10, height: 10, borderRadius: '50%', background: STATUS_HEX[s], display: 'inline-block', flexShrink: 0 }} />
                        <span style={{ color: 'var(--text-secondary)' }}>{statusLabel(s)}</span>
                      </span>
                    ))}
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 'var(--fs-xs)' }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#f0b429', display: 'inline-block', flexShrink: 0 }} />
                      <span style={{ color: 'var(--text-secondary)' }}>E_excess &gt; 0</span>
                    </span>
                  </div>
                </div>
              </Panel>

              {/* Selected point KPIs */}
              {selectedCode && (() => {
                const selRow = mapResult.rows.find(r => r.point_code === selectedCode)
                if (!selRow) return null
                return (
                  <Panel title={`${pm.panelSelected}: ${selRow.point_code}`} accent="var(--accent)">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--sp-3)' }}>
                      <StatusBadge status={selRow.window_status} label={statusLabel(selRow.window_status)} />
                      {selRow.quality_risk_flag && (
                        <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--danger)' }}>⚠ {p.qualityRiskWarning}</span>
                      )}
                    </div>
                    <div style={grid5}>
                      <KpiCard label={p.indicatorEMin} value={fmt(selRow.e_min_kj, 4)} unit={p.unitKjSpot} accent="var(--info)" />
                      <KpiCard label={p.indicatorEIdeal} value={fmt(selRow.e_ideal_kj, 4)} unit={p.unitKjSpot} accent="var(--ok)" />
                      <KpiCard label={p.indicatorEMax} value={fmt(selRow.e_max_kj, 4)} unit={p.unitKjSpot} accent="var(--warn)" />
                      <KpiCard label={p.indicatorECurrent} value={fmt(selRow.e_current_kj, 4)} unit={p.unitKjSpot} accent="var(--accent)" />
                      <KpiCard
                        label={p.indicatorDeltaE}
                        value={selRow.delta_e_signed_kj != null
                          ? (selRow.delta_e_signed_kj >= 0 ? '+' : '') + fmt(selRow.delta_e_signed_kj, 4)
                          : '—'}
                        unit={p.unitKjSpot}
                        accent={selRow.delta_e_signed_kj != null && selRow.delta_e_signed_kj > 0 ? 'var(--warn)'
                          : selRow.delta_e_signed_kj != null && selRow.delta_e_signed_kj < 0 ? 'var(--danger)'
                          : undefined}
                      />
                    </div>
                  </Panel>
                )
              })()}

              {!selectedCode && (
                <div style={{ color: 'var(--text-tertiary)', fontSize: 'var(--fs-sm)', marginBottom: 'var(--sp-4)', textAlign: 'center', padding: 'var(--sp-4)', border: '1px dashed var(--border)', borderRadius: 'var(--r-md)' }}>
                  {pm.noPointSelected}
                </div>
              )}

              <DisclaimerBanner text={mapResult.disclaimer} />
            </>
          )}

          <Panel title="Parça Haritası Yardım / Part Map Help">
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, fontFamily: 'var(--font-sans)' }}>{
`Parça Haritası, çok noktalı kaynak enerji durumunu parça üzerinde gösterir.

X/Y koordinatları isteğe bağlıdır (0–100 yüzde). Girilmezse nokta listesi şematik chip görünümünde sunulur.

Renk kodlaması:
  Yeşil  — IN_WINDOW: Enerji penceresi içinde
  Kırmızı — BELOW_MIN: Minimum enerjinin altında (kalite riski)
  Turuncu — ABOVE_MAX: Maksimum enerjinin üstünde (fazla enerji)
  Mavi   — E_CURRENT_ABSENT: Mevcut enerji girilmedi
  Gri    — NOT_ESTABLISHED: Enerji penceresi belirlenmedi

Sarı nokta (●): E_excess > 0 — fazla enerji var demektir.
Bir noktaya tıklayarak beş KPI göstergesini görüntüleyebilirsiniz.

Part Map shows multi-spot weld energy status on the part schematic.
X/Y coordinates (0–100 %) are optional. Without them a schematic chip view is shown.
Click any point to see its five KPI indicators.`
            }</pre>
          </Panel>
        </>
      )}

      {/* ── Export tab (P2-F) ───────────────────────────────────────────── */}
      {tab === 'export' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
          <Panel title={rm.title}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-sm)', marginBottom: 'var(--sp-3)' }}>{rm.subtitle}</p>

            {/* Format + Language */}
            <div style={{ display: 'flex', gap: 'var(--sp-4)', flexWrap: 'wrap', marginBottom: 'var(--sp-3)' }}>
              <div style={{ flex: '1 1 200px' }}>
                <label style={{ display: 'block', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 4 }}>{rm.formatLabel}</label>
                <select value={exportFormat} onChange={e => setExportFormat(e.target.value as ReportFormat)}
                  style={{ width: '100%', padding: '6px 8px', background: 'var(--surface)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)', fontSize: 'var(--fs-sm)' }}>
                  <option value="xlsx">{rm.formatXLSX}</option>
                  <option value="csv">{rm.formatCSV}</option>
                  <option value="pdf">{rm.formatPDF}</option>
                </select>
              </div>
              <div style={{ flex: '1 1 140px' }}>
                <label style={{ display: 'block', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 4 }}>{rm.langLabel}</label>
                <select value={exportLang} onChange={e => setExportLang(e.target.value as 'en' | 'tr')}
                  style={{ width: '100%', padding: '6px 8px', background: 'var(--surface)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)', fontSize: 'var(--fs-sm)' }}>
                  <option value="en">English</option>
                  <option value="tr">Türkçe</option>
                </select>
              </div>
            </div>

            {/* Scope label */}
            <div style={{ marginBottom: 'var(--sp-3)', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>
              <strong>{rm.scopeLabel}:</strong> {rm.scopePart} ({(dashRows.length > 0 ? dashRows : multiRows).length} pts)
            </div>

            {/* Optional metadata */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 'var(--sp-3)', marginBottom: 'var(--sp-4)' }}>
              {([
                [rm.metaProjectId, exportProjectId, setExportProjectId],
                [rm.metaProjectName, exportProjectName, setExportProjectName],
                [rm.metaPartId, exportPartId, setExportPartId],
                [rm.metaPassportId, exportPassportId, setExportPassportId],
                [rm.metaAnalyst, exportAnalyst, setExportAnalyst],
                [rm.metaReportTitle, exportTitle, setExportTitle],
              ] as [string, string, (v: string) => void][]).map(([label, val, setter]) => (
                <div key={label}>
                  <label style={{ display: 'block', fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 3 }}>{label}</label>
                  <input value={val} onChange={e => setter(e.target.value)}
                    style={{ width: '100%', padding: '5px 8px', background: 'var(--surface)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)', fontSize: 'var(--fs-sm)', boxSizing: 'border-box' }}
                  />
                </div>
              ))}
            </div>

            {/* Generate button */}
            <button type="button" disabled={exportLoading} onClick={runExport}
              style={{ padding: '10px 20px', background: exportLoading ? 'var(--border)' : 'var(--accent)', color: 'var(--on-accent, #fff)', border: 'none', borderRadius: 'var(--r-sm)', cursor: exportLoading ? 'not-allowed' : 'pointer', fontSize: 'var(--fs-sm)', fontWeight: 600 }}>
              {exportLoading ? rm.generating : rm.btnGenerate}
            </button>

            {exportError && <div style={{ marginTop: 'var(--sp-3)', color: 'var(--danger)', fontSize: 'var(--fs-sm)' }}>{exportError}</div>}
            {exportSuccess && <div style={{ marginTop: 'var(--sp-3)', color: 'var(--success, #22c55e)', fontSize: 'var(--fs-sm)' }}>{exportSuccess}</div>}
          </Panel>

          {/* Disclaimer */}
          <Panel title="Disclaimer">
            <p style={{ color: 'var(--warn)', fontSize: 'var(--fs-sm)', fontWeight: 600, marginBottom: 'var(--sp-2)' }}>{rm.disclaimer}</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-sm)' }}>{rm.passportNote}</p>
          </Panel>
        </div>
      )}

      {/* ── Help tab ────────────────────────────────────────────────────── */}
      {tab === 'help' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
          <Panel title="Mühendislik Yardım Merkezi / Engineering Help Center">
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-body)', lineHeight: 1.7 }}>
              <p>{p.governanceNote}</p>
            </div>
          </Panel>

          {[
            {
              title: 'I²Rt Enerji Formülü / I²Rt Energy Formula',
              body: 'E = I_rms² × R × t\n\nI_rms: kaynak kontrolörü RMS setpoint değeri (kA). DC/MFDC için I_mean ≈ I_rms.\nR: temas direnci (µΩ) — sabit değer varsayımı.\nt = N_cycle / f (saniye cinsinden kaynak süresi)\n\nSonuç J, kJ, Wh ve kWh olarak döndürülür. Elektrot tarafı enerji; şebeke tarafı kayıplar dahil değildir.',
            },
            {
              title: 'Beş Gösterge / Five Indicators',
              body: 'A. E_min — Hesaplanan Minimum Enerji: Kaynak penceresinin alt sınırı. Sadece doğrulanmış deney verisiyle belirlenebilir.\nB. E_ideal — Hesaplanan İdeal Enerji: Hedef enerji değeri. E_min ≤ E_ideal ≤ E_max şartı.\nC. E_max — Hesaplanan Maksimum Enerji: Üst sınır.\nD. E_current — Firmanın Mevcut Enerjisi: Üretimde kullanılan gerçek değer.\nE. ΔE — Fark: E_current − E_ideal (işaretli). Fazla = max(0, ΔE).',
            },
            {
              title: 'NOT_ESTABLISHED Kuralı',
              body: 'E_min, E_ideal ve E_max asla tahmin edilmez veya üretilmez. Bu değerleri girebilmek için:\n• Dokumentasyonlu üretim deneyleri\n• İşlenmiş kaynak lobu (sıçrama / yetersiz çekirdek sınırları)\n• Doğrulanmış proses penceresi verisi\ngereklidir. Yoksa sistem NOT_ESTABLISHED döndürür.',
            },
            {
              title: 'Maliyet Hesabı Uyarısı / Cost Disclaimer',
              body: p.costDisclaimer,
            },
            {
              title: 'CSV Formül Enjeksiyonu Koruması / Formula Injection Protection',
              body: "Herhangi bir hücre değeri =, +, @, | veya DDE( ile başlıyorsa güvenlik riski olarak işaretlenir ve içe aktarma engellenir. Bu kural tüm sütunlar için geçerlidir. Meşru negatif sayılar sayısal sütunlarda (e_current_kj vb.) float dönüşümüyle doğrulanır.",
            },
            {
              title: 'Örnek Parametreler / Example Parameters',
              body: '1.5 mm galvanizli çelik, MFDC 1000 Hz:\n  Akım: 8.3 kA RMS\n  Direnç: 120 µΩ\n  Kaynak süresi: 16 çevrim / 1000 Hz = 16 ms\n  E = (8300)² × 120e-6 × 0.016 = 131.9 J = 0.132 kJ/punta\n\nE_min/E_ideal/E_max için bu değeri doğrudan kullanmayın — lobu analizi ve deneysel doğrulama gereklidir.',
            },
          ].map(item => (
            <Panel key={item.title} title={item.title}>
              <pre style={{
                whiteSpace: 'pre-wrap', fontSize: 'var(--fs-sm)',
                color: 'var(--text-secondary)', lineHeight: 1.7, fontFamily: 'var(--font-sans)',
              }}>{item.body}</pre>
            </Panel>
          ))}
        </div>
      )}
    </div>
  )
}
