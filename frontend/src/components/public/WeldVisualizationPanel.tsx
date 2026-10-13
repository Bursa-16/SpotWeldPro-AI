/**
 * WeldVisualizationPanel — WEBSITE_DESIGN_02
 *
 * Four static SVG engineering visualizations for the public Features page.
 * PRESENTATIONAL ONLY — no engineering calculations, no model output.
 * All charts use illustrative example values only; none are computed results.
 * Physical validation is required regardless of any software analysis.
 *
 * Charts:
 *   1. Welding Current vs Nugget Diameter (scatter + trend band)
 *   2. Welding Lobe / Process Window (current vs time, 3 regions)
 *   3. Parameter Sensitivity (horizontal bar, relative only)
 *   4. Quality Risk Indicator (segmented scale)
 */

export interface VizStrings {
  sectionTitle: string
  sectionSub: string
  demoNote: string
  nuggetChart: {
    title: string
    xLabel: string
    yLabel: string
    threshLabel: string
    trendLabel: string
  }
  lobeChart: {
    title: string
    xLabel: string
    yLabel: string
    safeLabel: string
    insuffLabel: string
    expulsionLabel: string
    opLabel: string
  }
  sensChart: {
    title: string
    currentLabel: string
    timeLabel: string
    forceLabel: string
    tipLabel: string
  }
  riskChart: {
    title: string
    lowLabel: string
    mediumLabel: string
    highLabel: string
    indicatorLabel: string
    failureModeNote: string
  }
}

/* ─────────────────────────────────────────────────────────────────
   1. Welding Current vs Nugget Diameter
   Example scatter with illustrative trend band.
   X = welding current (kA), Y = nugget diameter (mm).
───────────────────────────────────────────────────────────────── */
function NuggetCurrentChart({ labels }: { labels: VizStrings['nuggetChart'] }) {
  const W = 220, H = 140
  const PAD = { t: 20, r: 14, b: 34, l: 38 }
  const cw = W - PAD.l - PAD.r
  const ch = H - PAD.t - PAD.b

  // X range: 6–12 kA  Y range: 3–9 mm
  const xMin = 6, xMax = 12
  const yMin = 3, yMax = 9
  const px = (x: number) => PAD.l + ((x - xMin) / (xMax - xMin)) * cw
  const py = (y: number) => PAD.t + ch - ((y - yMin) / (yMax - yMin)) * ch

  // Illustrative trend band (upper + lower boundary)
  const upperBand = [[6, 4.2], [7, 4.9], [8, 5.7], [9, 6.4], [10, 7.0], [11, 7.5], [12, 8.0]]
  const lowerBand = [[6, 3.2], [7, 3.8], [8, 4.5], [9, 5.1], [10, 5.7], [11, 6.2], [12, 6.8]]
  const bandPoints = [
    ...upperBand.map(([x, y]) => `${px(x)},${py(y)}`),
    ...[...lowerBand].reverse().map(([x, y]) => `${px(x)},${py(y)}`),
  ].join(' ')
  const trendLine = upperBand.map(([x, y], i) => {
    const mx = (upperBand[i][0] + lowerBand[i][0]) / 2
    const my = (y + lowerBand[i][1]) / 2
    return `${px(mx)},${py(my)}`
  }).join(' ')

  // Minimum acceptance threshold: 4.5 mm
  const threshY = py(4.5)

  // Example scatter points (illustrative only)
  const dots = [
    [6.5, 3.6], [7.0, 4.1], [7.5, 4.6], [7.8, 4.9],
    [8.2, 5.3], [8.5, 5.6], [9.0, 6.1], [9.2, 6.3],
    [9.5, 6.5], [10.0, 6.9], [10.5, 7.2], [11.0, 7.4],
  ]

  // X axis ticks
  const xTicks = [7, 8, 9, 10, 11]
  const yTicks = [4, 5, 6, 7, 8]

  return (
    <div className="viz-chart-wrap">
      <div className="viz-chart-title">{labels.title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" aria-hidden="true" className="viz-svg">
        {/* Trend band */}
        <polygon points={bandPoints} fill="rgba(52,208,88,0.10)" />
        <polyline points={trendLine} fill="none" stroke="rgba(52,208,88,0.45)" strokeWidth="1.2" strokeDasharray="4 2" />

        {/* Threshold line */}
        <line x1={PAD.l} y1={threshY} x2={PAD.l + cw} y2={threshY}
              stroke="rgba(248,81,73,0.45)" strokeWidth="1" strokeDasharray="3 3" />
        <text x={PAD.l + 2} y={threshY - 3} fontSize="6" fill="rgba(248,81,73,0.7)"
              fontFamily="var(--font-mono)">{labels.threshLabel}</text>

        {/* Scatter dots */}
        {dots.map(([x, y], i) => (
          <circle key={i} cx={px(x)} cy={py(y)} r="2.5"
                  fill="rgba(88,166,255,0.7)" stroke="rgba(88,166,255,0.9)" strokeWidth="0.5" />
        ))}

        {/* Axes */}
        <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={PAD.t + ch} stroke="#334" strokeWidth="0.8" />
        <line x1={PAD.l} y1={PAD.t + ch} x2={PAD.l + cw} y2={PAD.t + ch} stroke="#334" strokeWidth="0.8" />

        {/* X ticks + labels */}
        {xTicks.map(v => (
          <g key={v}>
            <line x1={px(v)} y1={PAD.t + ch} x2={px(v)} y2={PAD.t + ch + 3} stroke="#445" strokeWidth="0.6" />
            <text x={px(v)} y={PAD.t + ch + 10} textAnchor="middle" fontSize="6.5"
                  fill="#5a6880" fontFamily="var(--font-mono)">{v}</text>
          </g>
        ))}

        {/* Y ticks + labels */}
        {yTicks.map(v => (
          <g key={v}>
            <line x1={PAD.l - 3} y1={py(v)} x2={PAD.l} y2={py(v)} stroke="#445" strokeWidth="0.6" />
            <text x={PAD.l - 5} y={py(v) + 2.5} textAnchor="end" fontSize="6.5"
                  fill="#5a6880" fontFamily="var(--font-mono)">{v}</text>
          </g>
        ))}

        {/* Axis labels */}
        <text x={PAD.l + cw / 2} y={H - 4} textAnchor="middle" fontSize="7"
              fill="#6b7689" fontFamily="var(--font-sans)">{labels.xLabel}</text>
        <text x={8} y={PAD.t + ch / 2} textAnchor="middle" fontSize="7"
              fill="#6b7689" fontFamily="var(--font-sans)"
              transform={`rotate(-90, 8, ${PAD.t + ch / 2})`}>{labels.yLabel}</text>

        {/* Trend label */}
        <text x={px(11)} y={py(7.2) - 6} textAnchor="end" fontSize="6"
              fill="rgba(52,208,88,0.7)" fontFamily="var(--font-sans)">{labels.trendLabel}</text>
      </svg>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────
   2. Welding Lobe / Process Window
   X = weld time (cycles), Y = welding current (kA), 3 regions.
───────────────────────────────────────────────────────────────── */
function WeldLobeChart({ labels }: { labels: VizStrings['lobeChart'] }) {
  const W = 220, H = 140
  const PAD = { t: 20, r: 14, b: 34, l: 38 }
  const cw = W - PAD.l - PAD.r
  const ch = H - PAD.t - PAD.b

  const xMin = 8, xMax = 20   // cycles
  const yMin = 6, yMax = 12   // kA
  const px = (x: number) => PAD.l + ((x - xMin) / (xMax - xMin)) * cw
  const py = (y: number) => PAD.t + ch - ((y - yMin) / (yMax - yMin)) * ch

  // Lower lobe boundary (insufficient → safe)
  const lowerBoundary = [[8, 7.0], [10, 6.8], [12, 6.7], [14, 6.8], [16, 7.0], [18, 7.4], [20, 8.0]]
  // Upper lobe boundary (safe → expulsion)
  const upperBoundary = [[8, 9.8], [10, 10.2], [12, 10.4], [14, 10.3], [16, 10.0], [18, 9.6], [20, 9.0]]

  const insuffPts = [
    ...lowerBoundary.map(([x, y]) => `${px(x)},${py(y)}`),
    `${px(xMax)},${py(yMin)}`, `${px(xMin)},${py(yMin)}`,
  ].join(' ')

  const safePts = [
    ...lowerBoundary.map(([x, y]) => `${px(x)},${py(y)}`),
    ...[...upperBoundary].reverse().map(([x, y]) => `${px(x)},${py(y)}`),
  ].join(' ')

  const expPts = [
    ...upperBoundary.map(([x, y]) => `${px(x)},${py(y)}`),
    `${px(xMax)},${py(yMax)}`, `${px(xMin)},${py(yMax)}`,
  ].join(' ')

  // Operating point (in safe zone)
  const opX = px(13), opY = py(8.5)
  const xTicks = [10, 12, 14, 16, 18]
  const yTicks = [7, 8, 9, 10, 11]

  return (
    <div className="viz-chart-wrap">
      <div className="viz-chart-title">{labels.title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" aria-hidden="true" className="viz-svg">
        {/* Regions */}
        <polygon points={insuffPts} fill="rgba(88,166,255,0.10)" />
        <polygon points={safePts}   fill="rgba(52,208,88,0.12)" />
        <polygon points={expPts}    fill="rgba(248,81,73,0.10)" />

        {/* Region boundaries */}
        <polyline
          points={lowerBoundary.map(([x, y]) => `${px(x)},${py(y)}`).join(' ')}
          fill="none" stroke="rgba(88,166,255,0.4)" strokeWidth="1.2"
        />
        <polyline
          points={upperBoundary.map(([x, y]) => `${px(x)},${py(y)}`).join(' ')}
          fill="none" stroke="rgba(248,81,73,0.4)" strokeWidth="1.2"
        />

        {/* Region labels — safe label positioned above operating point to avoid overlap */}
        <text x={px(14)} y={py(6.5) - 2} textAnchor="middle" fontSize="6.5"
              fill="rgba(88,166,255,0.65)" fontFamily="var(--font-sans)">{labels.insuffLabel}</text>
        <text x={px(9.5)} y={py(9.2)} textAnchor="middle" fontSize="7" fontWeight="600"
              fill="rgba(52,208,88,0.8)" fontFamily="var(--font-sans)">{labels.safeLabel}</text>
        <text x={px(14)} y={py(10.8) - 2} textAnchor="middle" fontSize="6.5"
              fill="rgba(248,81,73,0.65)" fontFamily="var(--font-sans)">{labels.expulsionLabel}</text>

        {/* Operating point */}
        <circle cx={opX} cy={opY} r="6" fill="rgba(52,208,88,0.15)" stroke="#34d058" strokeWidth="1" />
        <circle cx={opX} cy={opY} r="2.5" fill="#34d058" />
        <text x={opX + 8} y={opY - 4} fontSize="6" fill="#34d058"
              fontFamily="var(--font-sans)">{labels.opLabel}</text>

        {/* Axes */}
        <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={PAD.t + ch} stroke="#334" strokeWidth="0.8" />
        <line x1={PAD.l} y1={PAD.t + ch} x2={PAD.l + cw} y2={PAD.t + ch} stroke="#334" strokeWidth="0.8" />

        {xTicks.map(v => (
          <g key={v}>
            <line x1={px(v)} y1={PAD.t + ch} x2={px(v)} y2={PAD.t + ch + 3} stroke="#445" strokeWidth="0.6" />
            <text x={px(v)} y={PAD.t + ch + 10} textAnchor="middle" fontSize="6.5"
                  fill="#5a6880" fontFamily="var(--font-mono)">{v}</text>
          </g>
        ))}
        {yTicks.map(v => (
          <g key={v}>
            <line x1={PAD.l - 3} y1={py(v)} x2={PAD.l} y2={py(v)} stroke="#445" strokeWidth="0.6" />
            <text x={PAD.l - 5} y={py(v) + 2.5} textAnchor="end" fontSize="6.5"
                  fill="#5a6880" fontFamily="var(--font-mono)">{v}</text>
          </g>
        ))}

        <text x={PAD.l + cw / 2} y={H - 4} textAnchor="middle" fontSize="7"
              fill="#6b7689" fontFamily="var(--font-sans)">{labels.xLabel}</text>
        <text x={8} y={PAD.t + ch / 2} textAnchor="middle" fontSize="7"
              fill="#6b7689" fontFamily="var(--font-sans)"
              transform={`rotate(-90, 8, ${PAD.t + ch / 2})`}>{labels.yLabel}</text>
      </svg>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────
   3. Parameter Sensitivity — horizontal bar chart (relative, illustrative)
───────────────────────────────────────────────────────────────── */
function SensitivityChart({ labels }: { labels: VizStrings['sensChart'] }) {
  const bars = [
    { label: labels.currentLabel, rel: 0.82 },
    { label: labels.timeLabel,    rel: 0.61 },
    { label: labels.forceLabel,   rel: 0.44 },
    { label: labels.tipLabel,     rel: 0.36 },
  ]
  const W = 220, H = 140
  const PAD = { t: 20, r: 16, b: 20, l: 72 }
  const cw = W - PAD.l - PAD.r
  const rowH = (H - PAD.t - PAD.b) / bars.length

  return (
    <div className="viz-chart-wrap">
      <div className="viz-chart-title">{labels.title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" aria-hidden="true" className="viz-svg">
        {bars.map((b, i) => {
          const y = PAD.t + i * rowH
          const barH = rowH * 0.52
          const barW = b.rel * cw
          const barY = y + (rowH - barH) / 2
          const opacity = 0.65 + b.rel * 0.30

          return (
            <g key={b.label}>
              {/* Label */}
              <text x={PAD.l - 6} y={barY + barH / 2 + 3} textAnchor="end" fontSize="7.5"
                    fill="#8b95a8" fontFamily="var(--font-sans)">{b.label}</text>
              {/* Background track */}
              <rect x={PAD.l} y={barY} width={cw} height={barH} rx="2"
                    fill="rgba(88,166,255,0.06)" />
              {/* Bar */}
              <rect x={PAD.l} y={barY} width={barW} height={barH} rx="2"
                    fill={`rgba(88,166,255,${opacity})`} />
              {/* Value label */}
              <text x={PAD.l + barW + 4} y={barY + barH / 2 + 3} fontSize="7"
                    fill="rgba(88,166,255,0.8)" fontFamily="var(--font-mono)">
                {Math.round(b.rel * 100)}
              </text>
            </g>
          )
        })}

        {/* X axis */}
        <line x1={PAD.l} y1={H - PAD.b} x2={PAD.l + cw} y2={H - PAD.b}
              stroke="#334" strokeWidth="0.6" />
      </svg>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────
   4. Quality Risk Indicator — segmented scale (LOW / MEDIUM / HIGH)
───────────────────────────────────────────────────────────────── */
function RiskIndicator({ labels }: { labels: VizStrings['riskChart'] }) {
  const W = 220, H = 140
  const segments = [
    { label: labels.lowLabel,    color: 'rgba(52,208,88,0.75)',   active: true  },
    { label: labels.mediumLabel, color: 'rgba(250,173,20,0.65)',  active: false },
    { label: labels.highLabel,   color: 'rgba(248,81,73,0.65)',   active: false },
  ]
  const segW = 54, segH = 24, gap = 6
  const totalW = segments.length * segW + (segments.length - 1) * gap
  const startX = (W - totalW) / 2
  const segY = 54

  return (
    <div className="viz-chart-wrap">
      <div className="viz-chart-title">{labels.title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" aria-hidden="true" className="viz-svg">
        {/* Indicator label */}
        <text x={W / 2} y={38} textAnchor="middle" fontSize="8" fontWeight="600"
              fill="#8b95a8" fontFamily="var(--font-sans)">{labels.indicatorLabel}</text>

        {segments.map((s, i) => {
          const x = startX + i * (segW + gap)
          return (
            <g key={s.label}>
              <rect x={x} y={segY} width={segW} height={segH} rx="3"
                    fill={s.active ? s.color : 'rgba(255,255,255,0.04)'}
                    stroke={s.active ? s.color : 'rgba(255,255,255,0.08)'}
                    strokeWidth="0.8" />
              <text x={x + segW / 2} y={segY + segH / 2 + 3.5} textAnchor="middle"
                    fontSize="7.5" fontWeight={s.active ? '700' : '400'}
                    fill={s.active ? '#111' : '#4a5568'}
                    fontFamily="var(--font-sans)">{s.label}</text>
              {/* Active marker */}
              {s.active && (
                <polygon
                  points={`${x + segW / 2 - 5},${segY - 6} ${x + segW / 2 + 5},${segY - 6} ${x + segW / 2},${segY - 1}`}
                  fill={s.color}
                />
              )}
            </g>
          )
        })}

        {/* Horizontal connector line */}
        <line x1={startX + segW / 2} y1={segY + segH / 2}
              x2={startX + totalW - segW / 2} y2={segY + segH / 2}
              stroke="rgba(255,255,255,0.08)" strokeWidth="1" />

        {/* Failure mode count hint */}
        <text x={W / 2} y={segY + segH + 18} textAnchor="middle" fontSize="7"
              fill="#5a6880" fontFamily="var(--font-sans)">{labels.failureModeNote}</text>

        {/* Axis scale */}
        <line x1={startX} y1={segY + segH + 28} x2={startX + totalW} y2={segY + segH + 28}
              stroke="#334" strokeWidth="0.6" />
        <line x1={startX} y1={segY + segH + 28} x2={startX} y2={segY + segH + 33}
              stroke="#445" strokeWidth="0.6" />
        <line x1={startX + totalW} y1={segY + segH + 28} x2={startX + totalW} y2={segY + segH + 33}
              stroke="#445" strokeWidth="0.6" />
        <text x={startX} y={segY + segH + 40} textAnchor="middle" fontSize="6"
              fill="#4a5568" fontFamily="var(--font-sans)">0</text>
        <text x={startX + totalW} y={segY + segH + 40} textAnchor="middle" fontSize="6"
              fill="#4a5568" fontFamily="var(--font-sans)">100</text>
        <text x={startX + totalW / 2} y={segY + segH + 40} textAnchor="middle" fontSize="6"
              fill="#4a5568" fontFamily="var(--font-sans)">%</text>
      </svg>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────
   Main panel export
───────────────────────────────────────────────────────────────── */
export function WeldVisualizationPanel({ v }: { v: VizStrings }) {
  return (
    <section className="viz-panel pub-section" aria-labelledby="viz-section-title">
      <h2 id="viz-section-title" className="pub-h2">{v.sectionTitle}</h2>
      <p className="pub-sub">{v.sectionSub}</p>

      <div className="viz-grid">
        <NuggetCurrentChart labels={v.nuggetChart} />
        <WeldLobeChart      labels={v.lobeChart} />
        <SensitivityChart   labels={v.sensChart} />
        <RiskIndicator      labels={v.riskChart} />
      </div>

      <p className="viz-demo-note">{v.demoNote}</p>
    </section>
  )
}
