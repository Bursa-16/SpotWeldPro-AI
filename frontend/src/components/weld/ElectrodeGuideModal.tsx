/**
 * ELECTRODE-GUIDE-01: Electrode Geometry Guide modal — informational UX only.
 *
 * SECURITY CONTRACT:
 *   - INFORMATIONAL UX ONLY. Does not read or write any engineering parameter.
 *   - tip_diameter_mm field is NOT accessed here.
 *   - No numeric diameter recommendations. No automatic parameter selection.
 *   - No OEM tables. No acceptance thresholds. No proprietary values.
 *   - No third-party reference artwork copied.
 *   - NEW_NUMERIC_ENGINEERING_AUTHORITY=NO
 *   - THIRD_PARTY_REFERENCE_ARTWORK_COPIED=NO
 */
import React from 'react'
import type { AppContent } from '../../i18n/appContent'

export interface ElectrodeGuideModalProps {
  t: AppContent['electrodeGuide']
  onClose: () => void
}

export function ElectrodeGuideModal({ t, onClose }: ElectrodeGuideModalProps): React.ReactElement {
  const dialogRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    dialogRef.current?.focus()
  }, [])

  React.useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div
      className="eg-overlay"
      role="presentation"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        ref={dialogRef}
        className="eg-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="eg-title"
        tabIndex={-1}
      >
        {/* Header */}
        <div className="eg-modal__header">
          <div>
            <h2 id="eg-title" className="eg-modal__title">{t.title}</h2>
            <p className="eg-modal__subtitle">{t.subtitle}</p>
          </div>
          <button
            type="button"
            className="eg-modal__close"
            onClick={onClose}
            aria-label={t.closeLabel}
          >
            ✕
          </button>
        </div>

        <div className="eg-modal__body">
          {/* Face Geometry */}
          <section className="eg-section" aria-labelledby="eg-geometry">
            <h3 id="eg-geometry" className="eg-section__title">{t.geometryTitle}</h3>

            <div className="eg-subsection">
              <h4 className="eg-subsection__title">{t.faceProfileTitle}</h4>
              <ul className="eg-list">
                <li className="eg-list__item">
                  <div className="eg-face eg-face--flat" aria-hidden="true" />
                  <span>{t.faceProfileFlat}</span>
                </li>
                <li className="eg-list__item">
                  <div className="eg-face eg-face--radius" aria-hidden="true" />
                  <span>{t.faceProfileRadius}</span>
                </li>
                <li className="eg-list__item">
                  <div className="eg-face eg-face--bevel" aria-hidden="true" />
                  <span>{t.faceProfileBevel}</span>
                </li>
              </ul>
            </div>

            <div className="eg-subsection">
              <h4 className="eg-subsection__title">{t.bodyFormTitle}</h4>
              <ul className="eg-list eg-list--horizontal">
                <li className="eg-list__item">{t.bodyFormStraight}</li>
                <li className="eg-list__item">{t.bodyFormOffset}</li>
                <li className="eg-list__item">{t.bodyFormAngled}</li>
              </ul>
            </div>

            <div className="eg-subsection">
              <h4 className="eg-subsection__title">{t.capTypeTitle}</h4>
              <ul className="eg-list eg-list--horizontal">
                <li className="eg-list__item">{t.capTypeStandard}</li>
                <li className="eg-list__item">{t.capTypeExtended}</li>
                <li className="eg-list__item">{t.capTypeMushroom}</li>
              </ul>
            </div>
          </section>

          {/* Electrode Material */}
          <section className="eg-section" aria-labelledby="eg-material">
            <h3 id="eg-material" className="eg-section__title">{t.materialTitle}</h3>
            <ul className="eg-list eg-list--vertical">
              <li className="eg-list__item">{t.materialCopper}</li>
              <li className="eg-list__item">{t.materialCuCrZr}</li>
              <li className="eg-list__item">{t.materialCuZrComp}</li>
            </ul>
          </section>

          {/* Maintenance Indicators */}
          <section className="eg-section" aria-labelledby="eg-maintenance">
            <h3 id="eg-maintenance" className="eg-section__title">{t.maintenanceTitle}</h3>
            <ul className="eg-list eg-list--vertical">
              <li className="eg-list__item">{t.maintenanceDress}</li>
              <li className="eg-list__item">{t.maintenancePeeling}</li>
              <li className="eg-list__item">{t.maintenanceExpansion}</li>
            </ul>
          </section>

          {/* Manual entry hint */}
          <div className="eg-hint">
            <strong>{t.diameterId}:</strong> {t.enterDiameterHint}
          </div>

          {/* Info note */}
          <p className="eg-info-note">{t.infoNote}</p>
        </div>

        {/* Footer */}
        <div className="eg-modal__footer">
          <button type="button" className="eg-modal__close-btn" onClick={onClose}>
            {t.closeLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
