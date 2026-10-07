/**
 * QUALITY-01B: Visual Weld Inspector — SpotWeldPro AI
 *
 * GOVERNANCE (QUALITY-01B):
 *   VISUAL_INSPECTOR_PERSISTENCE = NONE
 *   No backend writes of any kind.
 *   NORMAL_WELD does NOT automatically mean engineering PASS.
 *   No APPROVED / VALIDATED / PRODUCTION_APPROVED status is generated.
 *   3-sheet stacks remain ENGINEERING_REVIEW_REQUIRED.
 *   Selection state is session-local (useState only).
 *
 * ARTWORK:
 *   All schematics are original SpotWeldPro AI artwork (inline SVG).
 *   No OEM / customer photographs, diagrams, or acceptance values.
 *
 * TAXONOMY (frozen, QUALITY-01B — exactly 10 canonical codes):
 *   NORMAL_WELD | STICK_WELD | NO_WELD | UNDERSIZED_WELD | EXPULSION
 *   SURFACE_HOLE | SURFACE_CRACK | EXCESSIVE_INDENTATION | EDGE_WELD | DISTORTION
 */

import { useState } from 'react'
import { useAppLanguage } from '../../i18n/useAppLanguage'

// ── Frozen defect taxonomy — MUST NOT be altered ────────────────────────────
export type WeldDefectCode =
  | 'NORMAL_WELD'
  | 'STICK_WELD'
  | 'NO_WELD'
  | 'UNDERSIZED_WELD'
  | 'EXPULSION'
  | 'SURFACE_HOLE'
  | 'SURFACE_CRACK'
  | 'EXCESSIVE_INDENTATION'
  | 'EDGE_WELD'
  | 'DISTORTION'

const ALL_CODES: WeldDefectCode[] = [
  'NORMAL_WELD',
  'STICK_WELD',
  'NO_WELD',
  'UNDERSIZED_WELD',
  'EXPULSION',
  'SURFACE_HOLE',
  'SURFACE_CRACK',
  'EXCESSIVE_INDENTATION',
  'EDGE_WELD',
  'DISTORTION',
]

// ── Original SpotWeldPro AI color palette ───────────────────────────────────
// All artwork is original — not derived from OEM/customer content.
const ART = {
  bg:              '#0f172a',
  sheetFill:       '#1e2d4a',
  sheetStroke:     '#3b5280',
  electrodeFill:   '#374151',
  electrodeStroke: '#6b7280',
  nuggetFill:      '#1e3a8a',
  nuggetStroke:    '#3b82f6',
  nuggetHalo:      '#93c5fd',
  warnStroke:      '#f59e0b',
  dangerStroke:    '#ef4444',
  dim:             '#4b5563',
} as const

// ── SVG cross-section layout constants ──────────────────────────────────────
// ViewBox: 140 × 88
//   Electrode top:    x=54 y=2  w=32 h=10 rx=2
//   Sheet top:        x=8  y=12 w=124 h=15   (surface y=12, base y=27)
//   Weld zone:        y=27 → y=61  cx=70 cy=44
//   Sheet bottom:     x=8  y=61 w=124 h=15   (top y=61, base y=76)
//   Electrode bottom: x=54 y=76 w=32 h=10 rx=2

// ── Original SpotWeldPro AI SVG artwork ─────────────────────────────────────

/** NORMAL_WELD — full symmetric nugget, proper fusion across both sheets */
function SvgNormalWeld() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Full nugget — symmetric, spans full weld zone */}
      <ellipse cx="70" cy="44" rx="17" ry="12" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5"/>
      {/* Fusion boundary lines */}
      <line x1="53" y1="27" x2="53" y2="61" stroke={ART.nuggetHalo} strokeWidth="0.7" opacity="0.35"/>
      <line x1="87" y1="27" x2="87" y2="61" stroke={ART.nuggetHalo} strokeWidth="0.7" opacity="0.35"/>
    </svg>
  )
}

/**
 * STICK_WELD — small / localized apparent joining region.
 * Visually distinct from NO_WELD: has a visible but minimal nugget.
 * TR: Soğuk Punta / Yetersiz Birleşme  EN: Stick Weld (Cold Weld)
 */
function SvgStickWeld() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Very small, localized nugget — cold weld characteristic */}
      <ellipse cx="70" cy="44" rx="5" ry="3.5" fill={ART.nuggetFill} stroke={ART.nuggetHalo} strokeWidth="1.5"/>
      {/* Incomplete fusion gap indicators — dashed lines showing unfused zones */}
      <line x1="55" y1="27" x2="66" y2="41" stroke={ART.dim} strokeWidth="0.9" strokeDasharray="2,2" opacity="0.8"/>
      <line x1="85" y1="27" x2="74" y2="41" stroke={ART.dim} strokeWidth="0.9" strokeDasharray="2,2" opacity="0.8"/>
      <line x1="55" y1="61" x2="66" y2="47" stroke={ART.dim} strokeWidth="0.9" strokeDasharray="2,2" opacity="0.8"/>
      <line x1="85" y1="61" x2="74" y2="47" stroke={ART.dim} strokeWidth="0.9" strokeDasharray="2,2" opacity="0.8"/>
    </svg>
  )
}

/**
 * NO_WELD — no apparent joining region.
 * Visually distinct from STICK_WELD: sheets are completely unfused, no nugget present.
 */
function SvgNoWeld() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* No nugget — only a dashed interface line showing the unfused boundary */}
      <line x1="8" y1="44" x2="132" y2="44" stroke={ART.dim} strokeWidth="1.2" strokeDasharray="5,4"/>
      {/* Open-gap chevrons emphasising separation — no material bridge */}
      <polyline points="63,37 70,44 63,51" fill="none" stroke={ART.dim} strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="77,37 70,44 77,51" fill="none" stroke={ART.dim} strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

/** UNDERSIZED_WELD — nugget visible but smaller than minimum expected diameter */
function SvgUndersizedWeld() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Expected size boundary (dashed amber) */}
      <ellipse cx="70" cy="44" rx="17" ry="12" fill="none" stroke={ART.warnStroke} strokeWidth="1" strokeDasharray="3,2.5" opacity="0.55"/>
      {/* Actual nugget — clearly smaller than the expected boundary */}
      <ellipse cx="70" cy="44" rx="8" ry="6" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5"/>
    </svg>
  )
}

/** EXPULSION — nugget with expelled material splatter marks at weld boundary */
function SvgExpulsion() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Main nugget */}
      <ellipse cx="70" cy="44" rx="15" ry="10" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5"/>
      {/* Expulsion splatter — original SpotWeldPro AI artwork */}
      <circle cx="49" cy="37" r="2.2" fill={ART.warnStroke} opacity="0.9"/>
      <circle cx="91" cy="37" r="1.8" fill={ART.warnStroke} opacity="0.9"/>
      <circle cx="92" cy="52" r="2.4" fill={ART.warnStroke} opacity="0.85"/>
      <circle cx="47" cy="52" r="1.7" fill={ART.warnStroke} opacity="0.85"/>
      <line x1="85" y1="35" x2="94" y2="27" stroke={ART.warnStroke} strokeWidth="1.2" opacity="0.8" strokeLinecap="round"/>
      <line x1="55" y1="53" x2="44" y2="61" stroke={ART.warnStroke} strokeWidth="1.2" opacity="0.8" strokeLinecap="round"/>
      <line x1="88" y1="53" x2="100" y2="61" stroke={ART.warnStroke} strokeWidth="1.1" opacity="0.7" strokeLinecap="round"/>
    </svg>
  )
}

/** SURFACE_HOLE — visible void / crater on top sheet surface */
function SvgSurfaceHole() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Underlying nugget (faded — defect is at surface) */}
      <ellipse cx="70" cy="44" rx="17" ry="12" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5" opacity="0.45"/>
      {/* Surface hole / crater on top sheet */}
      <ellipse cx="70" cy="17" rx="7" ry="5" fill={ART.bg} stroke={ART.dangerStroke} strokeWidth="1.5"/>
      <ellipse cx="70" cy="17" rx="4" ry="3" fill={ART.bg} opacity="0.85"/>
    </svg>
  )
}

/** SURFACE_CRACK — zigzag crack line on top sheet surface */
function SvgSurfaceCrack() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Underlying nugget (faded) */}
      <ellipse cx="70" cy="44" rx="17" ry="12" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5" opacity="0.45"/>
      {/* Surface crack — original zigzag artwork on top sheet */}
      <path
        d="M56 14 L63 20 L58 23 L67 16 L73 21 L78 15 L84 20"
        fill="none"
        stroke={ART.dangerStroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** EXCESSIVE_INDENTATION — deep electrode impression visible on both sheet surfaces */
function SvgExcessiveIndentation() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      {/* Top electrode — driven deeper */}
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Top sheet with excessive indentation — concave surface */}
      <rect x="8" y="12" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <path d="M54 12 Q70 22 86 12" fill={ART.bg} stroke={ART.warnStroke} strokeWidth="1.3"/>
      {/* Bottom sheet with excessive indentation */}
      <rect x="8" y="61" width="124" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <path d="M54 76 Q70 66 86 76" fill={ART.bg} stroke={ART.warnStroke} strokeWidth="1.3"/>
      {/* Bottom electrode */}
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Nugget */}
      <ellipse cx="70" cy="44" rx="17" ry="12" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5"/>
      {/* Depth indicator arrows */}
      <line x1="70" y1="2" x2="70" y2="22" stroke={ART.warnStroke} strokeWidth="1.5" strokeLinecap="round" opacity="0.8"/>
      <line x1="70" y1="86" x2="70" y2="66" stroke={ART.warnStroke} strokeWidth="1.5" strokeLinecap="round" opacity="0.8"/>
    </svg>
  )
}

/** EDGE_WELD — nugget positioned at/near the sheet edge; sheets show a defined edge boundary */
function SvgEdgeWeld() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      {/* Shortened sheets showing the flange edge */}
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      <rect x="8" y="12" width="76" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="8" y="61" width="76" height="15" fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"/>
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Edge boundary line */}
      <line x1="84" y1="7" x2="84" y2="81" stroke={ART.warnStroke} strokeWidth="1.5" strokeDasharray="4,3" opacity="0.75"/>
      {/* Nugget — partially beyond the sheet edge */}
      <ellipse cx="76" cy="44" rx="15" ry="10" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5"/>
    </svg>
  )
}

/** DISTORTION — sheets show angular warping / bending post-weld */
function SvgDistortion() {
  return (
    <svg viewBox="0 0 140 88" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="54" y="2" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Top sheet — warped upward at left, downward at right */}
      <rect
        x="8" y="12" width="124" height="15"
        fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"
        transform="rotate(-5 70 19)"
      />
      {/* Bottom sheet — warped in opposite direction */}
      <rect
        x="8" y="61" width="124" height="15"
        fill={ART.sheetFill} stroke={ART.sheetStroke} strokeWidth="1" rx="1"
        transform="rotate(5 70 68)"
      />
      <rect x="54" y="76" width="32" height="10" rx="2" fill={ART.electrodeFill} stroke={ART.electrodeStroke} strokeWidth="1"/>
      {/* Nugget at center */}
      <ellipse cx="70" cy="44" rx="16" ry="11" fill={ART.nuggetFill} stroke={ART.nuggetStroke} strokeWidth="1.5"/>
      {/* Distortion direction arcs */}
      <path d="M16 10 Q12 19 16 27" fill="none" stroke={ART.warnStroke} strokeWidth="1.3" strokeLinecap="round" opacity="0.8"/>
      <path d="M124 61 Q128 68 124 75" fill="none" stroke={ART.warnStroke} strokeWidth="1.3" strokeLinecap="round" opacity="0.8"/>
    </svg>
  )
}

// ── Defect SVG dispatcher ───────────────────────────────────────────────────
function DefectSvg({ code }: { code: WeldDefectCode }) {
  switch (code) {
    case 'NORMAL_WELD':            return <SvgNormalWeld />
    case 'STICK_WELD':             return <SvgStickWeld />
    case 'NO_WELD':                return <SvgNoWeld />
    case 'UNDERSIZED_WELD':        return <SvgUndersizedWeld />
    case 'EXPULSION':              return <SvgExpulsion />
    case 'SURFACE_HOLE':           return <SvgSurfaceHole />
    case 'SURFACE_CRACK':          return <SvgSurfaceCrack />
    case 'EXCESSIVE_INDENTATION':  return <SvgExcessiveIndentation />
    case 'EDGE_WELD':              return <SvgEdgeWeld />
    case 'DISTORTION':             return <SvgDistortion />
  }
}

// ── Visual Weld Inspector component ────────────────────────────────────────
export function VisualWeldInspector() {
  const { t } = useAppLanguage()
  const c = t.visualWeldInspector

  // Session-local selection — no backend write, no persistence
  const [selected, setSelected] = useState<WeldDefectCode | null>(null)

  function handleSelect(code: WeldDefectCode) {
    setSelected((prev) => (prev === code ? null : code))
  }

  return (
    <section className="panel" aria-label={c.sectionTitle}>
      <div className="panel-header">
        <h3>{c.sectionTitle}</h3>
        <span className="panel-meta">{c.meta}</span>
      </div>

      <div className="panel-body">
        {/* Governance notice — no acceptance output generated */}
        <p className="notice" role="note" style={{ marginBottom: 'var(--sp-4)', fontSize: 'var(--fs-xs)' }}>
          {c.governanceNotice}
        </p>

        {/* Defect tile grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(124px, 1fr))',
            gap: 'var(--sp-3)',
          }}
        >
          {ALL_CODES.map((code) => {
            const isSelected = selected === code
            return (
              <button
                key={code}
                type="button"
                aria-pressed={isSelected}
                onClick={() => handleSelect(code)}
                style={{
                  background: isSelected ? 'var(--surface-raised, #1e2d4a)' : 'var(--surface-1, #111827)',
                  border: isSelected
                    ? '2px solid var(--accent, #3b82f6)'
                    : '1px solid var(--border, #2d3748)',
                  borderRadius: 'var(--radius, 6px)',
                  padding: 'var(--sp-2)',
                  cursor: 'pointer',
                  color: 'var(--text-primary, #f1f5f9)',
                  textAlign: 'center',
                  transition: 'border-color 0.15s, background 0.15s',
                }}
              >
                <div
                  style={{
                    background: ART.bg,
                    borderRadius: '4px',
                    marginBottom: 'var(--sp-1)',
                    padding: '4px',
                    lineHeight: 0,
                  }}
                >
                  <DefectSvg code={code} />
                </div>
                <span
                  style={{
                    display: 'block',
                    fontSize: 'var(--fs-xs, 0.72rem)',
                    lineHeight: 1.3,
                    fontWeight: isSelected ? 600 : 400,
                  }}
                >
                  {c.defectLabels[code] ?? code}
                </span>
              </button>
            )
          })}
        </div>

        {/* Detail panel — visible only when a defect is selected */}
        {selected !== null && (
          <div
            className="trace-block"
            style={{ marginTop: 'var(--sp-4)' }}
            role="region"
            aria-label={c.selectionDetailLabel}
          >
            <div className="trace-row">
              <span className="label">{c.selectedDefect}</span>
              <span className="value">{c.defectLabels[selected] ?? selected}</span>
            </div>
            <div className="trace-row">
              <span className="label">{c.canonicalCode}</span>
              <span className="value" style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: 'var(--fs-xs)' }}>
                {selected}
              </span>
            </div>
            {selected === 'NORMAL_WELD' && (
              <div className="trace-row">
                <span className="label">{c.normalWeldNotice}</span>
                <span className="value" style={{ color: 'var(--color-warn, #f59e0b)' }}>
                  {c.normalWeldNoticeValue}
                </span>
              </div>
            )}
            {/* Four-field model — OBSERVATION / VISUAL_ASSESSMENT / REQUIRED_VERIFICATION / ENGINEERING_STATUS */}
            <div className="trace-row">
              <span className="label">{c.observation}</span>
              <span className="value">{c.defectObservation[selected] ?? '—'}</span>
            </div>
            <div className="trace-row">
              <span className="label">{c.visualAssessment}</span>
              <span className="value">{c.defectVisualAssessment[selected] ?? '—'}</span>
            </div>
            <div className="trace-row">
              <span className="label">{c.requiredVerification}</span>
              <span className="value" style={{ color: 'var(--text-tertiary, #6b7280)' }}>
                {c.additionalVerificationRequired}
              </span>
            </div>
            <div className="trace-row">
              <span className="label">{c.engineeringStatus}</span>
              <span className="value" style={{ color: 'var(--text-tertiary, #6b7280)' }}>
                {c.engineeringAcceptanceNotEvaluated}
              </span>
            </div>
            <div className="trace-row">
              <span className="label">{c.sessionScope}</span>
              <span className="value" style={{ color: 'var(--text-tertiary, #6b7280)' }}>
                {c.sessionScopeValue}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="panel-footer">{c.footer}</div>
    </section>
  )
}
