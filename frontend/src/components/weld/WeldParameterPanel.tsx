/**
 * PARAMETER-ENGINE-01B2: Weld parameter input panel.
 *
 * Groups:
 *   A. Electrical / Welding:  current_ka, dc_current
 *   B. Force / Electrode:     force_kn, tip_diameter_mm, air_pressure_bar
 *   C. Time Parameters:       weld_cycles, squeeze_cycles, hold_cycles,
 *                             approach_cycles, cooling_cycles
 *   D. Cooling / Machine:     cooling_flow_lpm, cooling_temp_c,
 *                             adhesive, shunt_risk
 *
 * All time fields use TimeInputField for dual cycle/ms support.
 * Optional fields (approach_cycles, cooling_cycles, air_pressure_bar)
 * default to undefined → NOT_EVALUATED (never silently default).
 */
import React from 'react'
import type { AppContent } from '../../i18n/appContent'
import { TimeInputField, type TimeUnit } from './TimeInputField'

export interface WeldParameterDraft {
  current_ka: string
  force_kn: string
  tip_diameter_mm: string
  air_pressure_bar: string     // optional; '' = not provided
  weld_cycles: number | undefined
  squeeze_cycles: number | undefined
  hold_cycles: number | undefined
  approach_cycles: number | undefined  // optional
  cooling_cycles: number | undefined   // optional
  cooling_flow_lpm: string
  cooling_temp_c: string
  dc_current: boolean
  adhesive: boolean
  shunt_risk: boolean
}

export function makeEmptyParameters(): WeldParameterDraft {
  return {
    current_ka: '',
    force_kn: '',
    tip_diameter_mm: '',
    air_pressure_bar: '',
    weld_cycles: undefined,
    squeeze_cycles: undefined,
    hold_cycles: undefined,
    approach_cycles: undefined,
    cooling_cycles: undefined,
    cooling_flow_lpm: '',
    cooling_temp_c: '',
    dc_current: true,
    adhesive: false,
    shunt_risk: false,
  }
}

export interface WeldParameterPanelProps {
  t: AppContent['parameterPanel']
  params: WeldParameterDraft
  timeUnit: TimeUnit
  onTimeUnitChange: (unit: TimeUnit) => void
  onChange: (params: WeldParameterDraft) => void
}

export function WeldParameterPanel({
  t,
  params,
  timeUnit,
  onTimeUnitChange,
  onChange,
}: WeldParameterPanelProps): React.ReactElement {
  const set = <K extends keyof WeldParameterDraft>(key: K, value: WeldParameterDraft[K]) =>
    onChange({ ...params, [key]: value })

  return (
    <section className="weld-parameter-panel" aria-label={t.sectionTitle}>
      <div className="weld-parameter-panel__header">
        <h3 className="weld-parameter-panel__title">{t.sectionTitle}</h3>
        {/* Unit toggle */}
        <div className="weld-parameter-panel__unit-toggle" role="group" aria-label={t.unitToggleLabel}>
          <span className="weld-parameter-panel__unit-label">{t.unitToggleLabel}:</span>
          <button
            type="button"
            className={`weld-parameter-panel__unit-btn${timeUnit === 'cycle' ? ' weld-parameter-panel__unit-btn--active' : ''}`}
            onClick={() => onTimeUnitChange('cycle')}
            aria-pressed={timeUnit === 'cycle'}
          >
            {t.unitCycle}
          </button>
          <button
            type="button"
            className={`weld-parameter-panel__unit-btn${timeUnit === 'ms' ? ' weld-parameter-panel__unit-btn--active' : ''}`}
            onClick={() => onTimeUnitChange('ms')}
            aria-pressed={timeUnit === 'ms'}
          >
            {t.unitMs}
          </button>
        </div>
      </div>

      {/* A. Electrical / Welding */}
      <fieldset className="weld-parameter-panel__group">
        <legend>{t.groupElectrical}</legend>
        <div className="weld-parameter-panel__field">
          <label htmlFor="param-current-ka">{t.currentKa}</label>
          <input
            id="param-current-ka"
            type="number"
            value={params.current_ka}
            min={0}
            max={100}
            step={0.1}
            onChange={(e) => set('current_ka', e.target.value)}
          />
        </div>
        <div className="weld-parameter-panel__field weld-parameter-panel__field--checkbox">
          <label htmlFor="param-dc-current">{t.dcCurrent}</label>
          <input
            id="param-dc-current"
            type="checkbox"
            checked={params.dc_current}
            onChange={(e) => set('dc_current', e.target.checked)}
          />
        </div>
      </fieldset>

      {/* B. Force / Electrode */}
      <fieldset className="weld-parameter-panel__group">
        <legend>{t.groupForce}</legend>
        <div className="weld-parameter-panel__field">
          <label htmlFor="param-force-kn">{t.forceKn}</label>
          <input
            id="param-force-kn"
            type="number"
            value={params.force_kn}
            min={0}
            max={50}
            step={0.01}
            onChange={(e) => set('force_kn', e.target.value)}
          />
        </div>
        <div className="weld-parameter-panel__field">
          <label htmlFor="param-tip-dia">{t.tipDiameter}</label>
          <input
            id="param-tip-dia"
            type="number"
            value={params.tip_diameter_mm}
            min={0.1}
            max={50}
            step={0.1}
            onChange={(e) => set('tip_diameter_mm', e.target.value)}
          />
        </div>
        <div className="weld-parameter-panel__field">
          <label htmlFor="param-air-pressure">{t.airPressure}</label>
          <input
            id="param-air-pressure"
            type="number"
            value={params.air_pressure_bar}
            min={0}
            max={20}
            step={0.1}
            placeholder="—"
            onChange={(e) => set('air_pressure_bar', e.target.value)}
          />
        </div>
      </fieldset>

      {/* C. Time Parameters */}
      <fieldset className="weld-parameter-panel__group">
        <legend>{t.groupTime}</legend>
        <TimeInputField
          label={t.weldTime}
          valueCycles={params.weld_cycles}
          onChange={(v) => set('weld_cycles', v)}
          unit={timeUnit}
          labelCycle={t.unitCycle}
          labelMs={t.unitMs}
          labelUnresolved={t.unitBasisUnresolved}
          cycleEqMsHint={t.cycleEqMs}
          min={0}
          max={500}
        />
        <TimeInputField
          label={t.squeezeTime}
          valueCycles={params.squeeze_cycles}
          onChange={(v) => set('squeeze_cycles', v)}
          unit={timeUnit}
          labelCycle={t.unitCycle}
          labelMs={t.unitMs}
          labelUnresolved={t.unitBasisUnresolved}
          cycleEqMsHint={t.cycleEqMs}
          min={0}
          max={500}
        />
        <TimeInputField
          label={t.holdTime}
          valueCycles={params.hold_cycles}
          onChange={(v) => set('hold_cycles', v)}
          unit={timeUnit}
          labelCycle={t.unitCycle}
          labelMs={t.unitMs}
          labelUnresolved={t.unitBasisUnresolved}
          cycleEqMsHint={t.cycleEqMs}
          min={0}
          max={500}
        />
        <TimeInputField
          label={t.approachTime}
          valueCycles={params.approach_cycles}
          onChange={(v) => set('approach_cycles', v)}
          unit={timeUnit}
          labelCycle={t.unitCycle}
          labelMs={t.unitMs}
          labelUnresolved={t.unitBasisUnresolved}
          cycleEqMsHint={t.cycleEqMs}
          min={0}
          max={500}
        />
        <TimeInputField
          label={t.coolingTime}
          valueCycles={params.cooling_cycles}
          onChange={(v) => set('cooling_cycles', v)}
          unit={timeUnit}
          labelCycle={t.unitCycle}
          labelMs={t.unitMs}
          labelUnresolved={t.unitBasisUnresolved}
          cycleEqMsHint={t.cycleEqMs}
          min={0}
          max={500}
        />
      </fieldset>

      {/* D. Cooling / Machine Conditions */}
      <fieldset className="weld-parameter-panel__group">
        <legend>{t.groupCooling}</legend>
        <div className="weld-parameter-panel__field">
          <label htmlFor="param-cooling-flow">{t.coolingFlow}</label>
          <input
            id="param-cooling-flow"
            type="number"
            value={params.cooling_flow_lpm}
            min={0}
            max={100}
            step={0.1}
            onChange={(e) => set('cooling_flow_lpm', e.target.value)}
          />
        </div>
        <div className="weld-parameter-panel__field">
          <label htmlFor="param-cooling-temp">{t.coolingTemp}</label>
          <input
            id="param-cooling-temp"
            type="number"
            value={params.cooling_temp_c}
            min={0}
            max={100}
            step={0.1}
            onChange={(e) => set('cooling_temp_c', e.target.value)}
          />
        </div>
        <div className="weld-parameter-panel__field weld-parameter-panel__field--checkbox">
          <label htmlFor="param-adhesive">{t.adhesive}</label>
          <input
            id="param-adhesive"
            type="checkbox"
            checked={params.adhesive}
            onChange={(e) => set('adhesive', e.target.checked)}
          />
        </div>
        <div className="weld-parameter-panel__field weld-parameter-panel__field--checkbox">
          <label htmlFor="param-shunt-risk">{t.shuntRisk}</label>
          <input
            id="param-shunt-risk"
            type="checkbox"
            checked={params.shunt_risk}
            onChange={(e) => set('shunt_risk', e.target.checked)}
          />
        </div>
      </fieldset>
    </section>
  )
}
