import { useState, useEffect } from 'react'
import client from '../api/client'
import { useAppLanguage } from '../i18n/useAppLanguage'
import './ModelCatalogPage.css'

// ── Types ─────────────────────────────────────────────────────────────────────
type ValidationEvidence = {
  n_train: number | null
  n_test: number | null
  rmse_mm: number | null
  mae_mm: number | null
  bias_mm: number | null
  r2: number | null
  dataset_name: string | null
  measurement_basis: string | null
  notes_tr: string | null
  notes_en: string | null
}

type CatalogEntry = {
  model_id: string
  version: string
  name_tr: string
  name_en: string
  model_basis: string
  capability_type: string
  governance_status: string
  measurement_target: string
  supported_materials: string[]
  thickness_range_mm: number[]
  mandatory_inputs: string[]
  optional_inputs: string[]
  uncertainty_supported: boolean
  router_active: boolean
  not_available_reason_tr: string | null
  not_available_reason_en: string | null
  validation_evidence: ValidationEvidence | null
  rejection_reason_tr: string | null
  rejection_reason_en: string | null
  notes_tr: string
  notes_en: string
}

type Tab = 'prediction' | 'doe' | 'statistics' | 'physics'

// ── Helpers ───────────────────────────────────────────────────────────────────
const CAPABILITY_TO_TAB: Record<string, Tab> = {
  NUGGET_PREDICTOR:     'prediction',
  REFERENCE_THRESHOLD:  'prediction',
  DESIGN_METHOD:        'doe',
  STATISTICAL_ANALYSIS: 'statistics',
  PHYSICS_SIMULATION:   'physics',
}

function statusColor(s: string): string {
  switch (s) {
    case 'VALIDATED':               return 'mc-badge mc-badge--validated'
    case 'CONDITIONALLY_VALIDATED': return 'mc-badge mc-badge--conditional'
    case 'EXPERIMENTAL':            return 'mc-badge mc-badge--experimental'
    case 'UNDER_REVIEW':            return 'mc-badge mc-badge--review'
    case 'NOT_AVAILABLE':           return 'mc-badge mc-badge--na'
    case 'REJECTED':                return 'mc-badge mc-badge--rejected'
    case 'DEPRECATED':              return 'mc-badge mc-badge--deprecated'
    default:                        return 'mc-badge mc-badge--na'
  }
}

function statusLabel(
  s: string,
  p: ReturnType<typeof useAppLanguage>['t']['modelCatalogPage'],
): string {
  switch (s) {
    case 'VALIDATED':               return p.statusValidated
    case 'CONDITIONALLY_VALIDATED': return p.statusConditionallyValidated
    case 'EXPERIMENTAL':            return p.statusExperimental
    case 'UNDER_REVIEW':            return p.statusUnderReview
    case 'NOT_AVAILABLE':           return p.statusNotAvailable
    case 'REJECTED':                return p.statusRejected
    case 'DEPRECATED':              return p.statusDeprecated
    default:                        return s
  }
}

function capabilityLabel(
  c: string,
  p: ReturnType<typeof useAppLanguage>['t']['modelCatalogPage'],
): string {
  switch (c) {
    case 'NUGGET_PREDICTOR':     return p.capabilityNuggetPredictor
    case 'REFERENCE_THRESHOLD':  return p.capabilityReferenceThreshold
    case 'DESIGN_METHOD':        return p.capabilityDesignMethod
    case 'STATISTICAL_ANALYSIS': return p.capabilityStatisticalAnalysis
    case 'PHYSICS_SIMULATION':   return p.capabilityPhysicsSimulation
    default:                     return c
  }
}

function measurementTargetLabel(
  t: string,
  p: ReturnType<typeof useAppLanguage>['t']['modelCatalogPage'],
): string {
  if (t === 'nugget_diameter_mm') return p.measurementTargetNugget
  if (t === 'acceptance_criterion_mm') return p.measurementTargetCriterion
  return p.measurementTargetNa
}

// ── Sub-components ────────────────────────────────────────────────────────────
function SemanticDisclaimer({
  capabilityType,
  p,
}: {
  capabilityType: string
  p: ReturnType<typeof useAppLanguage>['t']['modelCatalogPage']
}) {
  let msg: string | null = null
  if (capabilityType === 'REFERENCE_THRESHOLD') msg = p.disclaimerReferenceThreshold
  else if (capabilityType === 'DESIGN_METHOD')        msg = p.disclaimerDesignMethod
  else if (capabilityType === 'STATISTICAL_ANALYSIS') msg = p.disclaimerStatisticalAnalysis
  else if (capabilityType === 'PHYSICS_SIMULATION')   msg = p.disclaimerPhysicsSimulation
  if (!msg) return null
  return (
    <div className="mc-disclaimer" role="note" aria-label="Semantic disclaimer">
      <span className="mc-disclaimer-icon" aria-hidden="true">ℹ</span>
      {msg}
    </div>
  )
}

function ValidationEvidencePanel({
  ev,
  lang,
  p,
}: {
  ev: ValidationEvidence
  lang: string
  p: ReturnType<typeof useAppLanguage>['t']['modelCatalogPage']
}) {
  const notes = lang === 'tr' ? ev.notes_tr : ev.notes_en
  const hasMetrics = ev.rmse_mm != null || ev.mae_mm != null || ev.r2 != null
  return (
    <div className="mc-evidence">
      <div className="mc-evidence-title">{p.evidenceTitle}</div>
      {!hasMetrics && (
        <div className="mc-evidence-empty">{p.noMetricsNotice}</div>
      )}
      {hasMetrics && (
        <dl className="mc-metrics">
          {ev.rmse_mm != null && (
            <>
              <dt>{p.evidenceRmse}</dt>
              <dd className="mc-metric-value mc-metric--warn">{ev.rmse_mm.toFixed(2)} mm</dd>
            </>
          )}
          {ev.mae_mm != null && (
            <>
              <dt>{p.evidenceMae}</dt>
              <dd className="mc-metric-value">{ev.mae_mm.toFixed(2)} mm</dd>
            </>
          )}
          {ev.bias_mm != null && (
            <>
              <dt>{p.evidenceBias}</dt>
              <dd className="mc-metric-value">{ev.bias_mm > 0 ? '+' : ''}{ev.bias_mm.toFixed(2)} mm</dd>
            </>
          )}
          {ev.r2 != null && (
            <>
              <dt>{p.evidenceR2}</dt>
              <dd className={`mc-metric-value${ev.r2 < 0 ? ' mc-metric--error' : ''}`}>
                {ev.r2.toFixed(2)}
              </dd>
            </>
          )}
          {ev.n_train != null && (
            <>
              <dt>{p.evidenceNTrain}</dt>
              <dd className="mc-metric-value">{ev.n_train}</dd>
            </>
          )}
          {ev.n_test != null && (
            <>
              <dt>{p.evidenceNTest}</dt>
              <dd className="mc-metric-value">{ev.n_test}</dd>
            </>
          )}
        </dl>
      )}
      {ev.dataset_name && (
        <div className="mc-evidence-dataset">{p.evidenceDataset}: {ev.dataset_name}</div>
      )}
      {ev.measurement_basis && (
        <div className="mc-evidence-basis">{p.evidenceMeasurementBasis}: {ev.measurement_basis}</div>
      )}
      {notes && <div className="mc-evidence-notes">{notes}</div>}
    </div>
  )
}

function ModelCard({
  entry,
  lang,
  p,
}: {
  entry: CatalogEntry
  lang: string
  p: ReturnType<typeof useAppLanguage>['t']['modelCatalogPage']
}) {
  const [expanded, setExpanded] = useState(false)
  const isRejected = entry.governance_status === 'REJECTED'
  const isNotAvailable = entry.governance_status === 'NOT_AVAILABLE'
  const isDisabled = isRejected || isNotAvailable

  const name = lang === 'tr' ? entry.name_tr : entry.name_en
  const notes = lang === 'tr' ? entry.notes_tr : entry.notes_en
  const notAvailableReason = lang === 'tr'
    ? entry.not_available_reason_tr
    : entry.not_available_reason_en
  const rejectionReason = lang === 'tr'
    ? entry.rejection_reason_tr
    : entry.rejection_reason_en

  return (
    <article
      className={`mc-card${isDisabled ? ' mc-card--disabled' : ''}`}
      aria-disabled={isDisabled}
    >
      <div className="mc-card-header">
        <div className="mc-card-title-row">
          <span className={statusColor(entry.governance_status)} role="status">
            {statusLabel(entry.governance_status, p)}
          </span>
          <h3 className="mc-card-name">{name}</h3>
        </div>
        <div className="mc-card-meta-row">
          <span className="mc-chip mc-chip--capability">
            {capabilityLabel(entry.capability_type, p)}
          </span>
          <span className="mc-chip mc-chip--target">
            {measurementTargetLabel(entry.measurement_target, p)}
          </span>
          {entry.uncertainty_supported && (
            <span className="mc-chip mc-chip--uncertainty">±σ</span>
          )}
          {!entry.router_active && (
            <span className="mc-chip mc-chip--disabled" title={p.routerDisabledNotice}>API ✕</span>
          )}
        </div>
      </div>

      <SemanticDisclaimer capabilityType={entry.capability_type} p={p} />

      {isRejected && rejectionReason && (
        <div className="mc-alert mc-alert--rejected" role="alert">
          <strong>{p.rejectedNotice}</strong>
          <p>{rejectionReason}</p>
        </div>
      )}

      {isNotAvailable && notAvailableReason && (
        <div className="mc-alert mc-alert--na">
          <strong>{p.notAvailableNotice}</strong>
          <p>{notAvailableReason}</p>
        </div>
      )}

      <button
        className="mc-expand-btn"
        aria-expanded={expanded}
        aria-controls={`mc-details-${entry.model_id}`}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? '▴ ' : '▾ '}{p.cardNotes}
      </button>

      {expanded && (
        <div id={`mc-details-${entry.model_id}`} className="mc-details">
          <dl className="mc-detail-list">
            <dt>{p.cardVersion}</dt>
            <dd>{entry.version}</dd>

            <dt>{p.cardBasis}</dt>
            <dd>{entry.model_basis}</dd>

            {entry.supported_materials.length > 0 && (
              <>
                <dt>{p.cardMaterials}</dt>
                <dd>{entry.supported_materials.join(', ')}</dd>
              </>
            )}

            {(entry.thickness_range_mm[0] > 0 || entry.thickness_range_mm[1] > 0) && (
              <>
                <dt>{p.cardThicknessRange}</dt>
                <dd>{entry.thickness_range_mm[0]}–{entry.thickness_range_mm[1]} mm</dd>
              </>
            )}

            {entry.mandatory_inputs.length > 0 && (
              <>
                <dt>{p.cardMandatoryInputs}</dt>
                <dd>{entry.mandatory_inputs.join(', ')}</dd>
              </>
            )}

            {entry.optional_inputs.length > 0 && (
              <>
                <dt>{p.cardOptionalInputs}</dt>
                <dd>{entry.optional_inputs.join(', ')}</dd>
              </>
            )}

            <dt>{p.cardUncertainty}</dt>
            <dd>{entry.uncertainty_supported ? '✓' : '—'}</dd>

            <dt>{p.cardRouterActive}</dt>
            <dd>{entry.router_active ? 'Active' : p.routerDisabledNotice}</dd>
          </dl>

          {notes && (
            <div className="mc-detail-notes">
              <div className="mc-detail-notes-label">{p.cardNotes}</div>
              <p>{notes}</p>
            </div>
          )}

          {entry.validation_evidence && (
            <ValidationEvidencePanel
              ev={entry.validation_evidence}
              lang={lang}
              p={p}
            />
          )}
        </div>
      )}
    </article>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function ModelCatalogPage() {
  const { lang, t } = useAppLanguage()
  const p = t.modelCatalogPage

  const [entries, setEntries] = useState<CatalogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('prediction')

  useEffect(() => {
    setLoading(true)
    setError('')
    client
      .get('/model-catalog')
      .then((res) => setEntries(res.data.entries ?? []))
      .catch(() => setError(p.errorText))
      .finally(() => setLoading(false))
  }, [])

  const TABS: { id: Tab; label: string }[] = [
    { id: 'prediction', label: p.tabPrediction },
    { id: 'doe',        label: p.tabDoe },
    { id: 'statistics', label: p.tabStatistics },
    { id: 'physics',    label: p.tabPhysics },
  ]

  const visible = entries.filter(
    (e) => (CAPABILITY_TO_TAB[e.capability_type] ?? 'prediction') === tab,
  )

  return (
    <div className="page active">
      <div className="ws-kicker">{p.kicker}</div>
      <header className="page-header">
        <div>
          <h1>{p.title}</h1>
          <p className="subtitle">{p.subtitle}</p>
        </div>
      </header>

      <div className="ws-context-bar" aria-label="Model catalog context">
        <span className="ctx-chip accent">
          {lang === 'tr' ? 'Toplam' : 'Total'}: <strong>{entries.length}</strong>
        </span>
        <span className="ctx-chip">
          {lang === 'tr' ? 'Doğrulanmış' : 'Validated'}:{' '}
          <strong>
            {entries.filter((e) => e.governance_status === 'VALIDATED').length}
          </strong>
        </span>
        <span className="ctx-chip">
          {lang === 'tr' ? 'Reddedildi' : 'Rejected'}:{' '}
          <strong className="mc-count--rejected">
            {entries.filter((e) => e.governance_status === 'REJECTED').length}
          </strong>
        </span>
        <span className="ctx-chip">
          {lang === 'tr' ? 'Mevcut Değil' : 'Not Available'}:{' '}
          <strong>
            {entries.filter((e) => e.governance_status === 'NOT_AVAILABLE').length}
          </strong>
        </span>
      </div>

      {error && (
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">{p.errorTitle}</div>
            <div className="alert-text">{error}</div>
          </div>
        </div>
      )}

      {loading && !error && (
        <div className="mc-loading" aria-live="polite">{p.loadingText}</div>
      )}

      {!loading && !error && (
        <>
          {/* Tab navigation */}
          <nav className="mc-tabs" role="tablist" aria-label="Model catalog tabs">
            {TABS.map((tb) => (
              <button
                key={tb.id}
                role="tab"
                aria-selected={tab === tb.id}
                aria-controls={`mc-panel-${tb.id}`}
                className={'mc-tab' + (tab === tb.id ? ' mc-tab--active' : '')}
                onClick={() => setTab(tb.id)}
              >
                {tb.label}
                <span className="mc-tab-count">
                  {entries.filter(
                    (e) => (CAPABILITY_TO_TAB[e.capability_type] ?? 'prediction') === tb.id,
                  ).length}
                </span>
              </button>
            ))}
          </nav>

          {/* Tab disclaimer for non-predictor tabs */}
          {tab === 'doe' && (
            <div className="mc-tab-notice" role="note">
              {lang === 'tr'
                ? 'DOE ve optimizasyon araçları nugget tahmini yapmaz; parametre seviyelerini ve deney düzenlerini optimize eder.'
                : 'DOE and optimization tools do not predict nugget diameter; they optimize parameter levels and experiment layouts.'}
            </div>
          )}
          {tab === 'statistics' && (
            <div className="mc-tab-notice" role="note">
              {lang === 'tr'
                ? 'İstatistik analiz araçları nugget tahmini yapmaz; faktör katkılarını ölçer.'
                : 'Statistical analysis tools do not predict nugget diameter; they measure factor contributions.'}
            </div>
          )}

          {/* Model cards */}
          <div
            id={`mc-panel-${tab}`}
            role="tabpanel"
            aria-labelledby={`mc-tab-${tab}`}
            className="mc-grid"
          >
            {visible.length === 0 && (
              <p className="mc-empty">
                {lang === 'tr' ? 'Bu kategoride model yok.' : 'No models in this category.'}
              </p>
            )}
            {visible.map((e) => (
              <ModelCard key={e.model_id} entry={e} lang={lang} p={p} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
