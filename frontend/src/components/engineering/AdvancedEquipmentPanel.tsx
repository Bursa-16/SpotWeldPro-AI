/**
 * APP-UX-01C-02: AdvancedEquipmentPanel
 *
 * Collapsible controlled component for advanced weld equipment parameters.
 * Exposes only fields the backend actually supports:
 *   squeeze_cycles, hold_cycles, cooling_flow_lpm, cooling_temp_c,
 *   dc_current, adhesive, shunt_risk
 *
 * ENGINEERING AUTHORITY RULE:
 * This component performs NO engineering calculations.
 * It only collects user input and emits it to the parent.
 *
 * Intentionally omitted (no backend support):
 *   - shunt_distance_mm
 *   - tip geometry variants beyond tip_diameter_mm (in parent)
 *   - unsupported force profiles
 *   - pulse scheduling / multi-pulse current
 */
import { useId } from 'react'
import { useAppLanguage } from '../../i18n/useAppLanguage'
import './engineering-ui.css'

export interface AdvancedEquipmentValues {
  squeeze_cycles: number
  hold_cycles: number
  cooling_flow_lpm: number
  cooling_temp_c: number
  dc_current: boolean
  adhesive: boolean
  shunt_risk: boolean
}

export interface AdvancedEquipmentPanelProps {
  open: boolean
  values: AdvancedEquipmentValues
  onToggle: () => void
  onChange: (values: AdvancedEquipmentValues) => void
}

export function AdvancedEquipmentPanel({
  open,
  values,
  onToggle,
  onChange,
}: AdvancedEquipmentPanelProps) {
  const bodyId = useId()
  const { t } = useAppLanguage()

  function handleNumber(field: keyof AdvancedEquipmentValues, raw: string) {
    const parsed = raw === '' ? 0 : parseFloat(raw)
    onChange({ ...values, [field]: isNaN(parsed) ? 0 : parsed })
  }

  function handleBool(field: keyof AdvancedEquipmentValues, checked: boolean) {
    onChange({ ...values, [field]: checked })
  }

  return (
    <div className="eui-panel">
      <button
        type="button"
        className="eui-panel-toggle"
        aria-expanded={open}
        aria-controls={bodyId}
        onClick={onToggle}
      >
        <span>{t.advancedPanel.title}</span>
        <span className="eui-panel-chevron" data-open={open ? 'true' : 'false'} aria-hidden="true">
          ▼
        </span>
      </button>

      {open && (
        <div id={bodyId} className="eui-panel-body">

          {/* ── Timing cycles ────────────────────────────────── */}
          <div className="eui-field-row">
            <div className="eui-field">
              <label className="eui-label" htmlFor="adv-squeeze-cycles">
                {t.advancedPanel.squeezeCycles}
              </label>
              <input
                id="adv-squeeze-cycles"
                type="number"
                className="eui-input"
                min={0}
                step={1}
                value={values.squeeze_cycles === 0 ? '' : values.squeeze_cycles}
                placeholder="0"
                onChange={(e) => handleNumber('squeeze_cycles', e.target.value)}
              />
            </div>

            <div className="eui-field">
              <label className="eui-label" htmlFor="adv-hold-cycles">
                {t.advancedPanel.holdCycles}
              </label>
              <input
                id="adv-hold-cycles"
                type="number"
                className="eui-input"
                min={0}
                step={1}
                value={values.hold_cycles === 0 ? '' : values.hold_cycles}
                placeholder="0"
                onChange={(e) => handleNumber('hold_cycles', e.target.value)}
              />
            </div>
          </div>

          {/* ── Cooling ──────────────────────────────────────── */}
          <div className="eui-field-row">
            <div className="eui-field">
              <label className="eui-label" htmlFor="adv-cooling-flow">
                {t.advancedPanel.coolingFlow}
              </label>
              <input
                id="adv-cooling-flow"
                type="number"
                className="eui-input"
                min={0}
                step={0.1}
                value={values.cooling_flow_lpm === 0 ? '' : values.cooling_flow_lpm}
                placeholder="0.0"
                onChange={(e) => handleNumber('cooling_flow_lpm', e.target.value)}
              />
            </div>

            <div className="eui-field">
              <label className="eui-label" htmlFor="adv-cooling-temp">
                {t.advancedPanel.coolingTemp}
              </label>
              <input
                id="adv-cooling-temp"
                type="number"
                className="eui-input"
                step={0.5}
                value={values.cooling_temp_c === 0 ? '' : values.cooling_temp_c}
                placeholder="0.0"
                onChange={(e) => handleNumber('cooling_temp_c', e.target.value)}
              />
            </div>
          </div>

          {/* ── Boolean flags ────────────────────────────────── */}
          <div className="eui-field-row">
            <div className="eui-field">
              <label className="eui-check-row">
                <input
                  type="checkbox"
                  checked={values.dc_current}
                  onChange={(e) => handleBool('dc_current', e.target.checked)}
                />
                <span className="eui-check-label">{t.advancedPanel.dcCurrent}</span>
              </label>
            </div>

            <div className="eui-field">
              <label className="eui-check-row">
                <input
                  type="checkbox"
                  checked={values.adhesive}
                  onChange={(e) => handleBool('adhesive', e.target.checked)}
                />
                <span className="eui-check-label">{t.advancedPanel.adhesive}</span>
              </label>
            </div>

            <div className="eui-field">
              <label className="eui-check-row">
                <input
                  type="checkbox"
                  checked={values.shunt_risk}
                  onChange={(e) => handleBool('shunt_risk', e.target.checked)}
                />
                <span className="eui-check-label">{t.advancedPanel.shuntRisk}</span>
              </label>
            </div>
          </div>

        </div>
      )}
    </div>
  )
}
