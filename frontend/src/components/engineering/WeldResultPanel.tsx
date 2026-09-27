/**
 * APP-UX-01C-02: WeldResultPanel
 *
 * Display-only component that renders a WeldAnalysisResponse from the backend.
 * Shows: score, risk_level, nugget targets, model prediction, compliance summary,
 * risks[], actions[], recommended_ranges[], model_results[], compliance_results[],
 * compliance_conflicts[].
 *
 * ENGINEERING AUTHORITY RULE:
 * This component performs NO engineering calculations.
 * All displayed values come directly from the backend response.
 *
 * Margin (selected_prediction_mm − nugget_min_mm) is arithmetic presentation
 * ONLY and is shown ONLY when both values are present and non-null.
 *
 * risk_level label resolves via RISK_LEVEL_LABELS; falls back to raw string.
 */
import type { WeldAnalysisResponse } from '../../types/weld'
import { RISK_LEVEL_LABELS } from '../../constants/riskLevel'
import './engineering-ui.css'

export interface WeldResultPanelProps {
  result: WeldAnalysisResponse | null
}

function riskClass(level: string): string {
  const key = level.toUpperCase()
  if (key === 'HIGH')   return 'eui-risk-high'
  if (key === 'MEDIUM') return 'eui-risk-medium'
  if (key === 'LOW')    return 'eui-risk-low'
  return ''
}

function fmt(v: number | null | undefined, decimals = 2): string {
  if (v == null) return '—'
  return v.toFixed(decimals)
}

export function WeldResultPanel({ result }: WeldResultPanelProps) {
  if (!result) {
    return (
      <div className="eui-result-empty">
        Analiz sonucu bekleniyor…
      </div>
    )
  }

  const riskLabel = RISK_LEVEL_LABELS[result.risk_level.toUpperCase()] ?? result.risk_level

  // Arithmetic margin — only when both backend values are present
  const showMargin =
    result.selected_prediction_mm != null && result.nugget_min_mm != null
  const margin = showMargin
    ? (result.selected_prediction_mm as number) - result.nugget_min_mm
    : null

  return (
    <div className="eui-section">

      {/* ── Core metrics ───────────────────────────────────── */}
      <div className="eui-result-grid">
        <div className="eui-stat-card">
          <div className="eui-stat-label">Skor</div>
          <div className="eui-stat-value">{fmt(result.score, 1)}</div>
        </div>

        <div className="eui-stat-card">
          <div className="eui-stat-label">Risk</div>
          <div className={`eui-stat-value ${riskClass(result.risk_level)}`}>
            {riskLabel}
          </div>
        </div>

        <div className="eui-stat-card">
          <div className="eui-stat-label">Nugget min (mm)</div>
          <div className="eui-stat-value">{fmt(result.nugget_min_mm)}</div>
        </div>

        <div className="eui-stat-card">
          <div className="eui-stat-label">Nugget opt (mm)</div>
          <div className="eui-stat-value">{fmt(result.nugget_opt_mm)}</div>
        </div>

        {result.selected_prediction_mm != null && (
          <div className="eui-stat-card">
            <div className="eui-stat-label">Model tahmini (mm)</div>
            <div className="eui-stat-value">{fmt(result.selected_prediction_mm)}</div>
          </div>
        )}

        {showMargin && (
          <div className="eui-stat-card">
            <div className="eui-stat-label">Marj (mm)</div>
            <div className={`eui-stat-value ${margin != null && margin < 0 ? 'eui-risk-high' : ''}`}>
              {fmt(margin)}
            </div>
          </div>
        )}
      </div>

      {/* ── Model tag ─────────────────────────────────────── */}
      {result.selected_model && (
        <div>
          <span className="eui-model-tag">{result.selected_model}</span>
        </div>
      )}

      {/* ── Compliance summary ────────────────────────────── */}
      {result.compliance_summary && (
        <div className="eui-stat-card">
          <div className="eui-stat-label" style={{ marginBottom: '8px' }}>
            Uyum özeti
          </div>
          <div className="eui-result-grid">
            <div>
              <div className="eui-stat-label">Skor</div>
              <div className="eui-stat-value">{fmt(result.compliance_summary.score, 1)}</div>
            </div>
            {result.compliance_summary.total_rules != null && (
              <div>
                <div className="eui-stat-label">Toplam kural</div>
                <div className="eui-stat-value">{result.compliance_summary.total_rules}</div>
              </div>
            )}
            {result.compliance_summary.passed != null && (
              <div>
                <div className="eui-stat-label">Geçti</div>
                <div className="eui-stat-value eui-risk-low">{result.compliance_summary.passed}</div>
              </div>
            )}
            {result.compliance_summary.failed != null && (
              <div>
                <div className="eui-stat-label">Başarısız</div>
                <div className="eui-stat-value eui-risk-high">{result.compliance_summary.failed}</div>
              </div>
            )}
            {result.compliance_summary.review != null && (
              <div>
                <div className="eui-stat-label">İnceleme</div>
                <div className="eui-stat-value eui-risk-medium">{result.compliance_summary.review}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Risks ─────────────────────────────────────────── */}
      {result.risks && result.risks.length > 0 && (
        <div>
          <p className="eui-section-title">Riskler</p>
          <ul className="eui-list">
            {result.risks.map((r, i) => (
              <li key={i} className="eui-list-item">
                <strong>{r.title}</strong>
                {r.detail}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Actions ───────────────────────────────────────── */}
      {result.actions && result.actions.length > 0 && (
        <div>
          <p className="eui-section-title">Önerilen aksiyonlar</p>
          <ul className="eui-list">
            {result.actions.map((a, i) => (
              <li key={i} className="eui-list-item">{a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Recommended ranges ────────────────────────────── */}
      {result.recommended_ranges && result.recommended_ranges.length > 0 && (
        <div>
          <p className="eui-section-title">Önerilen aralıklar</p>
          <table className="eui-range-table">
            <thead>
              <tr>
                <th>Parametre</th>
                <th>Min</th>
                <th>Maks</th>
                <th>Birim</th>
                <th>Mevcut</th>
                <th>Durum</th>
              </tr>
            </thead>
            <tbody>
              {result.recommended_ranges.map((row, i) => (
                <tr key={i}>
                  <td>{row.Parametre}</td>
                  <td>{fmt(row['Önerilen Min'])}</td>
                  <td>{fmt(row['Önerilen Maks'])}</td>
                  <td>{row.Birim}</td>
                  <td>{fmt(row.Mevcut)}</td>
                  <td>{row.Durum}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Model results ─────────────────────────────────── */}
      {result.model_results && result.model_results.length > 0 && (
        <div>
          <p className="eui-section-title">Model sonuçları</p>
          <ul className="eui-list">
            {result.model_results.map((m, i) => (
              <li key={i} className="eui-list-item">
                {m.model_name && <strong>{m.model_name}</strong>}
                {m.prediction_mm != null && (
                  <span> {fmt(m.prediction_mm)} mm</span>
                )}
                {m.validation_status && (
                  <span style={{ marginLeft: '8px' }}>
                    <span className="eui-model-tag">{m.validation_status}</span>
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Compliance conflicts ───────────────────────────── */}
      {result.compliance_conflicts && result.compliance_conflicts.length > 0 && (
        <div>
          <p className="eui-section-title">Kural çakışmaları</p>
          <ul className="eui-list">
            {result.compliance_conflicts.map((c, i) => (
              <li key={i} className="eui-list-item">
                <strong>{c.parameter}</strong>
                {` — Kazanan: ${c.winner_rule} (${c.winner_source})`}
                {` | Rakip: ${c.challenger_rule} (${c.challenger_source})`}
                {c.decision && <span>{` → ${c.decision}`}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  )
}
