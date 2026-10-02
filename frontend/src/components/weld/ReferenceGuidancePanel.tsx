/**
 * PARAMETER-ENGINE-01B2: Reference guidance panel.
 *
 * Displays backend-returned reference profile context:
 *   reference_profile_id, effective_thickness_mm, selected_band, band_selection_status
 *
 * Guidance is informational only.
 * Does NOT affect score, risk level, compliance, or NOK status.
 * Frontend must not duplicate or invent engineering range tables.
 * Rows for data not yet returned by backend are hidden, not stubbed.
 *
 * Guidance statuses mapped:
 *   WITHIN_REFERENCE_RANGE
 *   BELOW_REFERENCE_RANGE
 *   ABOVE_REFERENCE_RANGE
 *   ENGINEERING_REVIEW_REQUIRED
 *   UNIT_BASIS_UNRESOLVED
 *   NOT_EVALUATED
 */
import React from 'react'
import type { WeldAnalysisResponse } from '../../types/weld'
import type { AppContent } from '../../i18n/appContent'

export type GuidanceStatus =
  | 'WITHIN_REFERENCE_RANGE'
  | 'BELOW_REFERENCE_RANGE'
  | 'ABOVE_REFERENCE_RANGE'
  | 'ENGINEERING_REVIEW_REQUIRED'
  | 'UNIT_BASIS_UNRESOLVED'
  | 'NOT_EVALUATED'

export interface ReferenceRangeRow {
  param: string
  min?: number | null
  max?: number | null
  unit?: string | null
  status: GuidanceStatus
}

export interface ReferenceGuidancePanelProps {
  t: AppContent['referenceGuidancePanel']
  response: Pick<
    WeldAnalysisResponse,
    'reference_profile_id' | 'effective_thickness_mm' | 'selected_band' | 'band_selection_status'
  >
  /** Optional range rows provided by backend. Frontend never fabricates these. */
  rangeRows?: ReferenceRangeRow[]
}

function statusLabel(
  status: GuidanceStatus,
  t: AppContent['referenceGuidancePanel'],
): string {
  switch (status) {
    case 'WITHIN_REFERENCE_RANGE':       return t.withinRange
    case 'BELOW_REFERENCE_RANGE':        return t.belowRange
    case 'ABOVE_REFERENCE_RANGE':        return t.aboveRange
    case 'ENGINEERING_REVIEW_REQUIRED':  return t.engineeringReviewRequired
    case 'UNIT_BASIS_UNRESOLVED':        return t.unitBasisUnresolved
    case 'NOT_EVALUATED':
    default:                             return t.notEvaluated
  }
}

function statusClassName(status: GuidanceStatus): string {
  switch (status) {
    case 'WITHIN_REFERENCE_RANGE':       return 'rgp-status rgp-status--ok'
    case 'BELOW_REFERENCE_RANGE':
    case 'ABOVE_REFERENCE_RANGE':        return 'rgp-status rgp-status--warn'
    case 'ENGINEERING_REVIEW_REQUIRED':  return 'rgp-status rgp-status--review'
    case 'UNIT_BASIS_UNRESOLVED':        return 'rgp-status rgp-status--unresolved'
    case 'NOT_EVALUATED':
    default:                             return 'rgp-status rgp-status--neutral'
  }
}

export function ReferenceGuidancePanel({
  t,
  response,
  rangeRows,
}: ReferenceGuidancePanelProps): React.ReactElement | null {
  const {
    reference_profile_id,
    effective_thickness_mm,
    selected_band,
    band_selection_status,
  } = response

  // If backend returned nothing meaningful, show minimal notice
  const hasProfile = !!reference_profile_id

  // Outside-range warning: any row that is BELOW or ABOVE
  const hasOutsideRange = (rangeRows ?? []).some(
    (r) => r.status === 'BELOW_REFERENCE_RANGE' || r.status === 'ABOVE_REFERENCE_RANGE',
  )

  return (
    <section className="reference-guidance-panel" aria-label={t.sectionTitle}>
      <h3 className="reference-guidance-panel__title">{t.sectionTitle}</h3>

      {/* Informational note — guidance does not affect compliance */}
      <p className="reference-guidance-panel__info-note">{t.guidanceInfoNote}</p>

      {/* No profile found */}
      {!hasProfile && (
        <p className="reference-guidance-panel__no-profile">{t.noReferenceFound}</p>
      )}

      {/* Profile metadata */}
      {hasProfile && (
        <dl className="reference-guidance-panel__meta">
          <div className="reference-guidance-panel__meta-row">
            <dt>{t.referenceProfile}</dt>
            <dd>{reference_profile_id}</dd>
          </div>
          {effective_thickness_mm != null && (
            <div className="reference-guidance-panel__meta-row">
              <dt>{t.effectiveThickness}</dt>
              <dd>{effective_thickness_mm} mm</dd>
            </div>
          )}
          {selected_band != null && (
            <div className="reference-guidance-panel__meta-row">
              <dt>{t.referenceBand}</dt>
              <dd>{selected_band}</dd>
            </div>
          )}
          {band_selection_status === 'ENGINEERING_REVIEW_REQUIRED' && (
            <div className="reference-guidance-panel__review-notice" role="status">
              {t.engineeringReviewRequired}
            </div>
          )}
        </dl>
      )}

      {/* Outside-range warning */}
      {hasProfile && hasOutsideRange && (
        <div className="reference-guidance-panel__outside-warning" role="alert">
          {t.outsideRangeWarning}
        </div>
      )}

      {/* Range table — only rows the backend provided */}
      {hasProfile && rangeRows && rangeRows.length > 0 && (
        <table className="reference-guidance-panel__range-table">
          <thead>
            <tr>
              <th>{t.rangeParam}</th>
              <th>{t.rangeMin}</th>
              <th>{t.rangeMax}</th>
              <th>{t.rangeUnit}</th>
              <th>{t.rangeStatus}</th>
            </tr>
          </thead>
          <tbody>
            {rangeRows.map((row, i) => (
              <tr key={i}>
                <td>{row.param}</td>
                <td>{row.min ?? '—'}</td>
                <td>{row.max ?? '—'}</td>
                <td>{row.unit ?? '—'}</td>
                <td>
                  <span className={statusClassName(row.status)}>
                    {statusLabel(row.status, t)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
