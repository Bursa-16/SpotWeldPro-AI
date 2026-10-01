/**
 * APP-UX-01C-02: StackUpEditor
 *
 * Controlled component for configuring the weld stack-up.
 * Collects: stack_count (2T | 3T | 4T) and per-layer fields.
 *
 * ENGINEERING AUTHORITY RULE:
 * This component performs NO engineering calculations.
 * It only collects user input and emits it to the parent.
 *
 * Material ontology: no canonical list is available in the frontend.
 * material_family and material_subtype are free-text inputs.
 * Replace with <select> elements if a backend-driven list is added.
 */
import type { LayerInput } from '../../types/weld'
import { useAppLanguage } from '../../i18n/useAppLanguage'
import './engineering-ui.css'

type StackCount = '2T' | '3T' | '4T'

const STACK_OPTIONS: StackCount[] = ['2T', '3T', '4T']

const STACK_LAYER_COUNT: Record<StackCount, number> = {
  '2T': 2,
  '3T': 3,
  '4T': 4,
}

const EMPTY_LAYER: LayerInput = {
  material_family: '',
  material_subtype: '',
  thickness_mm: 0,
  coated: false,
}

export interface StackUpEditorProps {
  stackCount: StackCount
  layers: LayerInput[]
  onChange: (stackCount: StackCount, layers: LayerInput[]) => void
}

export function StackUpEditor({ stackCount, layers, onChange }: StackUpEditorProps) {
  const { t } = useAppLanguage()
  const targetCount = STACK_LAYER_COUNT[stackCount]

  function handleStackCountChange(next: StackCount) {
    const count = STACK_LAYER_COUNT[next]
    const nextLayers = Array.from({ length: count }, (_, i) => layers[i] ?? { ...EMPTY_LAYER })
    onChange(next, nextLayers)
  }

  function handleLayerChange(index: number, field: keyof LayerInput, value: string | number | boolean) {
    const nextLayers = layers.map((layer, i) =>
      i === index ? { ...layer, [field]: value } : layer
    )
    onChange(stackCount, nextLayers)
  }

  // Ensure layers array length matches stackCount
  const visibleLayers: LayerInput[] = Array.from(
    { length: targetCount },
    (_, i) => layers[i] ?? { ...EMPTY_LAYER }
  )

  return (
    <div className="eui-section">
      <p className="eui-section-title">{t.stackEditor.sectionTitle}</p>

      {/* Stack count selector */}
      <div>
        <p className="eui-label" id="stack-count-label">
          {t.stackEditor.stackCountLabel}
        </p>
        <div className="eui-stack-selector" role="group" aria-labelledby="stack-count-label">
          {STACK_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              className="eui-stack-btn"
              aria-pressed={stackCount === opt}
              onClick={() => handleStackCountChange(opt)}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Layer rows */}
      <div className="eui-layer-list">
        {visibleLayers.map((layer, idx) => {
          const layerNum = idx + 1
          const idPrefix = `layer-${layerNum}`
          return (
            <div key={idx} className="eui-layer-card">
              <p className="eui-layer-title">{t.stackEditor.layerPrefix} {layerNum}</p>
              <div className="eui-field-row">
                {/* material_family */}
                <div className="eui-field">
                  <label className="eui-label" htmlFor={`${idPrefix}-family`}>
                    {t.stackEditor.materialFamily}
                  </label>
                  <input
                    id={`${idPrefix}-family`}
                    type="text"
                    className="eui-input"
                    value={layer.material_family}
                    placeholder={t.stackEditor.materialFamilyPlaceholder}
                    onChange={(e) => handleLayerChange(idx, 'material_family', e.target.value)}
                    autoComplete="off"
                  />
                </div>
                {/* material_subtype */}
                <div className="eui-field">
                  <label className="eui-label" htmlFor={`${idPrefix}-subtype`}>
                    {t.stackEditor.materialSubtype}
                  </label>
                  <input
                    id={`${idPrefix}-subtype`}
                    type="text"
                    className="eui-input"
                    value={layer.material_subtype}
                    placeholder={t.stackEditor.materialSubtypePlaceholder}
                    onChange={(e) => handleLayerChange(idx, 'material_subtype', e.target.value)}
                    autoComplete="off"
                  />
                </div>
                {/* thickness_mm */}
                <div className="eui-field">
                  <label className="eui-label" htmlFor={`${idPrefix}-thickness`}>
                    {t.stackEditor.thickness}
                  </label>
                  <input
                    id={`${idPrefix}-thickness`}
                    type="number"
                    className="eui-input"
                    min={0}
                    step={0.1}
                    value={layer.thickness_mm === 0 ? '' : layer.thickness_mm}
                    placeholder="0.0"
                    onChange={(e) =>
                      handleLayerChange(
                        idx,
                        'thickness_mm',
                        e.target.value === '' ? 0 : parseFloat(e.target.value)
                      )
                    }
                  />
                </div>
                {/* coated */}
                <div className="eui-field" style={{ justifyContent: 'flex-end' }}>
                  <label className="eui-check-row" style={{ marginTop: 'auto', paddingBottom: '6px' }}>
                    <input
                      type="checkbox"
                      checked={layer.coated}
                      onChange={(e) => handleLayerChange(idx, 'coated', e.target.checked)}
                    />
                    <span className="eui-check-label">{t.stackEditor.coated}</span>
                  </label>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
