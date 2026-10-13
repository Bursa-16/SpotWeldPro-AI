/**
 * SpotWeldHeroSimulation — PUBLIC-VISUAL-01
 *
 * Animated SVG visualization of resistance spot welding.
 * PRESENTATIONAL ONLY: no engineering calculations, no model predictions.
 * All values shown are labeled as example/demo — they are not computed results.
 *
 * Animation states:
 *   0 idle       – electrodes apart, gap visible
 *   1 approach   – upper electrode descends toward sheet stack
 *   2 force      – electrodes clamp; force arrows visible
 *   3 current    – current flow lines appear
 *   4 nugget     – weld nugget grows at sheet interface
 *   5 complete   – nugget at target size, result shown
 */

import { useState, useEffect, useRef } from 'react'

export interface HeroSimStrings {
  exampleLabel: string
  currentLabel: string
  timeLabel: string
  forceLabel: string
  nuggetLabel: string
  processWindowLabel: string
  insufficientLabel: string
  safeLabel: string
  expulsionLabel: string
  upperElectrode: string
  lowerElectrode: string
  completeLabel: string
  currentValue: string
  timeValue: string
  forceValue: string
  nuggetValue: string
}

interface Props {
  sim: HeroSimStrings
}

const CYCLE_MS = [1400, 900, 900, 1200, 1600, 2200] // ms per state

export function SpotWeldHeroSimulation({ sim }: Props) {
  const prefersReduced = typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false

  // Show final state immediately when motion is reduced
  const [state, setState] = useState<number>(prefersReduced ? 5 : 0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (prefersReduced) { setState(5); return }

    function advance(s: number) {
      const next = (s + 1) % 6
      timerRef.current = setTimeout(() => {
        setState(next)
        advance(next)
      }, CYCLE_MS[s])
    }
    advance(state)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const clamped   = state >= 1   // electrode touching sheet
  const force     = state >= 2   // force arrows
  const current   = state >= 3   // current flow
  const nuggetPct = state === 4 ? 0.6 : state >= 5 ? 1 : 0
  const done      = state === 5

  // SVG dimensions
  const W = 320
  const H = 280

  // Electrode geometry
  const elecBodyW = 84
  const elecBodyH = 30
  const elecTipW  = 48
  const elecTipH  = 18
  const elecCX    = W / 2
  const gap       = clamped ? 0 : 28  // gap between electrode tip and sheet

  // Sheet stack (fixed)
  const sheetY     = 130
  const sheet1H    = 12
  const sheet2H    = 12
  const sheetX     = 58
  const sheetW     = W - 116
  const interfaceY = sheetY + sheet1H

  // Upper electrode — moves down when clamped
  const upperBodyY  = sheetY - gap - elecTipH - elecBodyH
  const upperTipY   = sheetY - gap - elecTipH

  // Lower electrode — fixed
  const lowerTipY  = sheetY + sheet1H + sheet2H
  const lowerBodyY = lowerTipY + elecTipH

  // Nugget ellipse
  const nuggetRX = nuggetPct * 30
  const nuggetRY = nuggetPct * 9

  // Current path x-positions (three parallel lines)
  const currentLines = [elecCX - 14, elecCX, elecCX + 14]

  const transitionStyle = prefersReduced
    ? {}
    : { transition: 'transform 0.6s cubic-bezier(0.4,0,0.2,1), opacity 0.4s ease' }

  return (
    <div className="sw-hero-sim">
      {/* ── Header badge ── */}
      <div className="sw-sim-head">
        <span className="sw-sim-label">{sim.exampleLabel}</span>
        <span className={'sw-sim-badge' + (done ? ' ok' : '')}>
          {done ? sim.completeLabel : sim.currentLabel + ' · ' + sim.timeLabel}
        </span>
      </div>

      {/* ── Main SVG ── */}
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        aria-hidden="true"
        className="sw-sim-svg"
      >
        <defs>
          {/* Copper gradient for electrodes */}
          <linearGradient id="swCopperV" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stopColor="#7a4a1e" />
            <stop offset="30%"  stopColor="#c8763a" />
            <stop offset="60%"  stopColor="#e09248" />
            <stop offset="100%" stopColor="#9e5c25" />
          </linearGradient>
          <linearGradient id="swCopperTip" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#c8763a" />
            <stop offset="100%" stopColor="#8a4e1e" />
          </linearGradient>
          {/* Steel sheet gradient */}
          <linearGradient id="swSteel1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#4a5568" />
            <stop offset="100%" stopColor="#2d3748" />
          </linearGradient>
          <linearGradient id="swSteel2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#2d3748" />
            <stop offset="100%" stopColor="#1a202c" />
          </linearGradient>
          {/* Nugget glow */}
          <radialGradient id="swNugget" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#ffd05a" stopOpacity="0.95" />
            <stop offset="40%"  stopColor="#e8923a" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#c0520a" stopOpacity="0.0" />
          </radialGradient>
          <filter id="swGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* ── Upper electrode ── */}
        <g style={prefersReduced ? {} : { transition: 'transform 0.6s cubic-bezier(0.4,0,0.2,1)' }}
           transform={`translate(0,0)`}>
          {/* Body cylinder */}
          <rect
            x={elecCX - elecBodyW / 2}
            y={upperBodyY}
            width={elecBodyW}
            height={elecBodyH}
            rx="4"
            fill="url(#swCopperV)"
            stroke="#5a3010"
            strokeWidth="0.8"
          />
          {/* Tapered tip */}
          <path
            d={`M ${elecCX - elecBodyW / 2} ${upperBodyY + elecBodyH}
                L ${elecCX - elecTipW / 2} ${upperTipY + elecTipH}
                L ${elecCX + elecTipW / 2} ${upperTipY + elecTipH}
                L ${elecCX + elecBodyW / 2} ${upperBodyY + elecBodyH} Z`}
            fill="url(#swCopperTip)"
            stroke="#5a3010"
            strokeWidth="0.8"
          />
          {/* Tip cap (dome) */}
          <ellipse
            cx={elecCX}
            cy={upperTipY + elecTipH}
            rx={elecTipW / 2}
            ry="4"
            fill="#9e5c25"
          />
        </g>

        {/* ── Sheet stack ── */}
        {/* Sheet 1 (top) */}
        <rect x={sheetX} y={sheetY} width={sheetW} height={sheet1H}
              fill="url(#swSteel1)" stroke="#556070" strokeWidth="0.6" rx="1" />
        {/* Sheet 2 (bottom) */}
        <rect x={sheetX} y={sheetY + sheet1H} width={sheetW} height={sheet2H}
              fill="url(#swSteel2)" stroke="#445060" strokeWidth="0.6" rx="1" />

        {/* ── Weld nugget (grows at interface) ── */}
        {nuggetPct > 0 && (
          <ellipse
            cx={elecCX}
            cy={interfaceY}
            rx={nuggetRX}
            ry={nuggetRY}
            fill="url(#swNugget)"
            filter="url(#swGlow)"
            style={prefersReduced ? {} : { transition: 'rx 0.8s ease, ry 0.8s ease' }}
          />
        )}

        {/* ── Lower electrode ── */}
        <g>
          {/* Tip dome */}
          <ellipse
            cx={elecCX}
            cy={lowerTipY}
            rx={elecTipW / 2}
            ry="4"
            fill="#9e5c25"
          />
          {/* Tapered tip */}
          <path
            d={`M ${elecCX - elecTipW / 2} ${lowerTipY}
                L ${elecCX - elecBodyW / 2} ${lowerBodyY}
                L ${elecCX + elecBodyW / 2} ${lowerBodyY}
                L ${elecCX + elecTipW / 2} ${lowerTipY} Z`}
            fill="url(#swCopperTip)"
            stroke="#5a3010"
            strokeWidth="0.8"
          />
          {/* Body cylinder */}
          <rect
            x={elecCX - elecBodyW / 2}
            y={lowerBodyY}
            width={elecBodyW}
            height={elecBodyH}
            rx="4"
            fill="url(#swCopperV)"
            stroke="#5a3010"
            strokeWidth="0.8"
          />
        </g>

        {/* ── Force arrows ── */}
        {force && (
          <>
            {/* Down arrow (upper) */}
            <g opacity={force ? 1 : 0} style={transitionStyle}>
              <line x1={elecCX - 24} y1={upperBodyY - 16} x2={elecCX - 24} y2={upperBodyY - 4}
                    stroke="#58a6ff" strokeWidth="1.5" markerEnd="url(#arrowDown)" />
              <line x1={elecCX + 24} y1={upperBodyY - 16} x2={elecCX + 24} y2={upperBodyY - 4}
                    stroke="#58a6ff" strokeWidth="1.5" markerEnd="url(#arrowDown)" />
              <text x={elecCX} y={upperBodyY - 20} textAnchor="middle"
                    fontSize="7" fill="#58a6ff" fontFamily="var(--font-mono)">
                {sim.forceLabel}
              </text>
            </g>
            {/* Up arrow (lower) */}
            <g opacity={force ? 1 : 0} style={transitionStyle}>
              <line x1={elecCX - 24} y1={lowerBodyY + elecBodyH + 16} x2={elecCX - 24} y2={lowerBodyY + elecBodyH + 4}
                    stroke="#58a6ff" strokeWidth="1.5" markerEnd="url(#arrowUp)" />
              <line x1={elecCX + 24} y1={lowerBodyY + elecBodyH + 16} x2={elecCX + 24} y2={lowerBodyY + elecBodyH + 4}
                    stroke="#58a6ff" strokeWidth="1.5" markerEnd="url(#arrowUp)" />
            </g>
          </>
        )}

        {/* Arrow marker defs */}
        <defs>
          <marker id="arrowDown" markerWidth="6" markerHeight="6" refX="3" refY="5" orient="auto">
            <path d="M1,1 L3,5 L5,1" fill="none" stroke="#58a6ff" strokeWidth="1.2" />
          </marker>
          <marker id="arrowUp" markerWidth="6" markerHeight="6" refX="3" refY="1" orient="auto">
            <path d="M1,5 L3,1 L5,5" fill="none" stroke="#58a6ff" strokeWidth="1.2" />
          </marker>
        </defs>

        {/* ── Current flow lines ── */}
        {current && currentLines.map((x, i) => (
          <line
            key={i}
            x1={x} y1={upperTipY + elecTipH + 2}
            x2={x} y2={lowerTipY - 2}
            stroke="#f0b429"
            strokeWidth="1.2"
            strokeDasharray="3 3"
            opacity="0.7"
            style={prefersReduced ? {} : {
              strokeDashoffset: 0,
              animation: 'swCurrentFlow 0.6s linear infinite'
            }}
          />
        ))}

        {/* ── Electrode labels ── */}
        <text x={sheetX - 6} y={upperTipY + elecTipH / 2 + 3} textAnchor="end"
              fontSize="7.5" fill="#6b7689" fontFamily="var(--font-sans)">
          {sim.upperElectrode}
        </text>
        <text x={sheetX - 6} y={lowerTipY + elecTipH / 2 + 3} textAnchor="end"
              fontSize="7.5" fill="#6b7689" fontFamily="var(--font-sans)">
          {sim.lowerElectrode}
        </text>

        {/* ── Interface line (dashed) ── */}
        <line x1={sheetX} y1={interfaceY} x2={sheetX + sheetW} y2={interfaceY}
              stroke="#333c4b" strokeWidth="0.8" strokeDasharray="4 4" />
      </svg>

      {/* ── Parameter chips (example values) ── */}
      <div className="sw-sim-params">
        <div className="sw-sim-chip">
          <span className="sw-chip-label">{sim.currentLabel}</span>
          <span className="sw-chip-val">{sim.currentValue}</span>
        </div>
        <div className="sw-sim-chip">
          <span className="sw-chip-label">{sim.timeLabel}</span>
          <span className="sw-chip-val">{sim.timeValue}</span>
        </div>
        <div className="sw-sim-chip">
          <span className="sw-chip-label">{sim.forceLabel}</span>
          <span className="sw-chip-val">{sim.forceValue}</span>
        </div>
        <div className={'sw-sim-chip' + (done ? ' highlight' : '')}>
          <span className="sw-chip-label">{sim.nuggetLabel}</span>
          <span className="sw-chip-val">{done ? sim.nuggetValue : '—'}</span>
        </div>
      </div>

      {/* ── Process window mini chart ── */}
      <div className="sw-sim-window">
        <span className="sw-window-label">{sim.processWindowLabel}</span>
        <ProcessWindowChart
          sim={sim}
          opActive={current || done}
          prefersReduced={prefersReduced}
        />
      </div>

      <style>{`
        @keyframes swCurrentFlow {
          to { stroke-dashoffset: -12; }
        }
      `}</style>
    </div>
  )
}

/* ────────────────────────────────────────────────────────────
   Process Window Mini Chart
   X = Weld Time  Y = Welding Current
   Three regions: insufficient / safe / expulsion risk
   Operating point marker animates subtly in safe zone.
   DEMO ONLY — no backend data, no engineering classification.
──────────────────────────────────────────────────────────── */
function ProcessWindowChart({
  sim,
  opActive,
  prefersReduced,
}: {
  sim: HeroSimStrings
  opActive: boolean
  prefersReduced: boolean
}) {
  // SVG coordinates: x=time (right), y=current (up = smaller y)
  // viewBox: 0 0 160 90
  const W = 160, H = 80
  const px = (x: number) => 10 + x * (W - 20)  // 0–1 to pixel
  const py = (y: number) => H - 8 - y * (H - 16) // 0–1 (bottom) to pixel

  // Region polygons (simplified lobe shape)
  // Insufficient fusion: below the lower lobe boundary
  const insuffPts = [
    [0, 0], [1, 0], [1, 0.3], [0.7, 0.45], [0.4, 0.48], [0.15, 0.42], [0, 0.35],
  ].map(([x, y]) => `${px(x)},${py(y)}`).join(' ')

  // Safe window
  const safePts = [
    [0, 0.35], [0.15, 0.42], [0.4, 0.48], [0.7, 0.45], [1, 0.3],
    [1, 0.72], [0.7, 0.80], [0.35, 0.78], [0.1, 0.68], [0, 0.58],
  ].map(([x, y]) => `${px(x)},${py(y)}`).join(' ')

  // Expulsion risk: above the upper lobe boundary
  const expPts = [
    [0, 0.58], [0.1, 0.68], [0.35, 0.78], [0.7, 0.80], [1, 0.72],
    [1, 1], [0, 1],
  ].map(([x, y]) => `${px(x)},${py(y)}`).join(' ')

  // Operating point (in safe zone)
  const opX = px(0.48)
  const opY = py(0.60)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" aria-hidden="true" className="sw-window-svg">
      {/* Regions */}
      <polygon points={insuffPts} fill="rgba(88,166,255,0.12)" />
      <polygon points={safePts}   fill="rgba(52,208,88,0.14)" />
      <polygon points={expPts}    fill="rgba(248,81,73,0.12)" />

      {/* Region boundaries */}
      <polyline
        points={[
          [0, 0.35], [0.15, 0.42], [0.4, 0.48], [0.7, 0.45], [1, 0.3],
        ].map(([x, y]) => `${px(x)},${py(y)}`).join(' ')}
        fill="none" stroke="rgba(88,166,255,0.35)" strokeWidth="1"
      />
      <polyline
        points={[
          [0, 0.58], [0.1, 0.68], [0.35, 0.78], [0.7, 0.80], [1, 0.72],
        ].map(([x, y]) => `${px(x)},${py(y)}`).join(' ')}
        fill="none" stroke="rgba(248,81,73,0.35)" strokeWidth="1"
      />

      {/* Axes */}
      <line x1={px(0)} y1={py(0)} x2={px(1)} y2={py(0)} stroke="#333c4b" strokeWidth="0.8" />
      <line x1={px(0)} y1={py(0)} x2={px(0)} y2={py(1)} stroke="#333c4b" strokeWidth="0.8" />

      {/* Region labels */}
      <text x={px(0.5)} y={py(0.12)} textAnchor="middle" fontSize="6.5" fill="rgba(88,166,255,0.6)"
            fontFamily="var(--font-sans)">{sim.insufficientLabel}</text>
      <text x={px(0.5)} y={py(0.55)} textAnchor="middle" fontSize="7" fill="rgba(52,208,88,0.75)"
            fontFamily="var(--font-sans)" fontWeight="600">{sim.safeLabel}</text>
      <text x={px(0.5)} y={py(0.90)} textAnchor="middle" fontSize="6.5" fill="rgba(248,81,73,0.6)"
            fontFamily="var(--font-sans)">{sim.expulsionLabel}</text>

      {/* Operating point */}
      {opActive && (
        <>
          <circle cx={opX} cy={opY} r="5" fill="rgba(52,208,88,0.2)" stroke="#34d058"
                  strokeWidth="1.2"
                  style={prefersReduced ? {} : { animation: 'swOpPulse 2s ease-in-out infinite' }} />
          <circle cx={opX} cy={opY} r="2.5" fill="#34d058" />
        </>
      )}

      <style>{`
        @keyframes swOpPulse {
          0%, 100% { r: 5; opacity: 0.8; }
          50% { r: 8; opacity: 0.3; }
        }
      `}</style>
    </svg>
  )
}
