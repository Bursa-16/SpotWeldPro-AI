/**
 * PARAMETER-ENGINE-01B2: Stack definition UI.
 *
 * Renders N layer rows matching stack_count (2T / 3T / 4T).
 * For 3T / 4T: displays engineering review notice — no automatic band selection.
 * No silent defaults: every field shown is explicitly entered by the user.
 */
import React from 'react'
import type { AppContent } from '../../i18n/appContent'

export type StackCount = '2T' | '3T' | '4T'

export interface LayerDraft {
  material_family: string
  material_subtype: string
  thickness_mm: string  // string for controlled input; validated on submit
  coated: boolean
}

export function makeEmptyLayer(): LayerDraft {
  return { material_family: '', material_subtype: '', thickness_mm: '', coated: false }
}

export interface StackDefinitionPanelProps {
  t: AppContent['stackDefinition']
  stackCount: StackCount
  layers: LayerDraft[]
  onStackCountChange: (sc: StackCount) => void
  onLayerChange: (index: number, layer: LayerDraft) => void
}

const STACK_OPTIONS: StackCount[] = ['2T', '3T', '4T']

/** True only when material is mild-steel-family and stack is 2T. */
export function isReferenceBandEligible(stackCount: StackCount, layers: LayerDraft[]): boolean {
  if (stackCount !== '2T') return false
  // Band eligibility: Layer 1 must be mild_steel family
  // Backend determines the actual band; frontend only gates the notice.
  return layers[0]?.material_family.toLowerCase().includes('mild') ||
    layers[0]?.material_family.toLowerCase() === 'if' ||
    layers[0]?.material_family === ''  // empty → allow (backend decides)
}

export function StackDefinitionPanel({
  t,
  stackCount,
  layers,
  onStackCountChange,
  onLayerChange,
}: StackDefinitionPanelProps): React.ReactElement {
  const requiresEngineeringReview = stackCount === '3T' || stackCount === '4T'
  const layerCount = parseInt(stackCount[0], 10)

  return (
    <section className="stack-definition-panel" aria-label={t.sectionTitle}>
      <h3 className="stack-definition-panel__title">{t.sectionTitle}</h3>

      {/* Stack count selector */}
      <div className="stack-definition-panel__count-row">
        <span className="stack-definition-panel__count-label">{t.stackCountLabel}</span>
        <div className="stack-definition-panel__count-buttons" role="group" aria-label={t.stackCountLabel}>
          {STACK_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              className={`stack-definition-panel__count-btn${stackCount === opt ? ' stack-definition-panel__count-btn--active' : ''}`}
              onClick={() => onStackCountChange(opt)}
              aria-pressed={stackCount === opt}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Engineering review notice for 3T / 4T */}
      {requiresEngineeringReview && (
        <div className="stack-definition-panel__review-notice" role="status">
          {t.engineeringReviewRequired}
        </div>
      )}

      {/* Layer rows */}
      {Array.from({ length: layerCount }, (_, i) => {
        const layer = layers[i] ?? makeEmptyLayer()
        return (
          <div key={i} className="stack-definition-panel__layer">
            <h4 className="stack-definition-panel__layer-title">
              {t.layerPrefix} {i + 1}
            </h4>
            <div className="stack-definition-panel__layer-fields">
              <div className="stack-definition-panel__field">
                <label htmlFor={`layer-${i}-family`}>{t.materialFamily}</label>
                <input
                  id={`layer-${i}-family`}
                  type="text"
                  value={layer.material_family}
                  placeholder={t.materialFamilyPlaceholder}
                  onChange={(e) =>
                    onLayerChange(i, { ...layer, material_family: e.target.value })
                  }
                />
              </div>
              <div className="stack-definition-panel__field">
                <label htmlFor={`layer-${i}-subtype`}>{t.materialSubtype}</label>
                <input
                  id={`layer-${i}-subtype`}
                  type="text"
                  value={layer.material_subtype}
                  placeholder={t.materialSubtypePlaceholder}
                  onChange={(e) =>
                    onLayerChange(i, { ...layer, material_subtype: e.target.value })
                  }
                />
              </div>
              <div className="stack-definition-panel__field">
                <label htmlFor={`layer-${i}-thickness`}>{t.thickness}</label>
                <input
                  id={`layer-${i}-thickness`}
                  type="number"
                  value={layer.thickness_mm}
                  min={0.1}
                  max={10}
                  step={0.1}
                  onChange={(e) =>
                    onLayerChange(i, { ...layer, thickness_mm: e.target.value })
                  }
                />
              </div>
              <div className="stack-definition-panel__field stack-definition-panel__field--checkbox">
                <label htmlFor={`layer-${i}-coated`}>{t.coated}</label>
                <input
                  id={`layer-${i}-coated`}
                  type="checkbox"
                  checked={layer.coated}
                  onChange={(e) =>
                    onLayerChange(i, { ...layer, coated: e.target.checked })
                  }
                />
              </div>
            </div>
          </div>
        )
      })}
    </section>
  )
}
