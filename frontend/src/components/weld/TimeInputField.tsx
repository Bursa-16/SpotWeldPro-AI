/**
 * PARAMETER-ENGINE-01B2: Dual-unit time input (cycles / ms).
 *
 * Reference basis: 50 Hz → 1 cycle = 20 ms.
 * Backend is cycle-canonical. ms conversion is display/entry only.
 * No Math.round(): fractional cycles are preserved (150 ms → 7.5 cycles).
 *
 * When cycleMs is undefined the field shows UNIT_BASIS_UNRESOLVED.
 */
import React from 'react'

/** Fixed basis at 50 Hz. */
export const CYCLE_MS = 20

export type TimeUnit = 'cycle' | 'ms'

export interface TimeInputFieldProps {
  /** i18n label, e.g. "Weld time" */
  label: string
  /** Current value in cycles (the canonical unit). */
  valueCycles: number | undefined
  /** Called with new value in cycles whenever the user edits. */
  onChange: (cycles: number | undefined) => void
  /** Active unit mode for the whole panel. */
  unit: TimeUnit
  /** i18n: "Cycles" */
  labelCycle: string
  /** i18n: "ms" */
  labelMs: string
  /** i18n: "UNIT_BASIS_UNRESOLVED" — shown when unit basis cannot resolve */
  labelUnresolved: string
  /** i18n: "{n} cycles = {m} ms" display hint template — receives formatted string */
  cycleEqMsHint?: string
  disabled?: boolean
  min?: number
  max?: number
}

export function TimeInputField({
  label,
  valueCycles,
  onChange,
  unit,
  labelCycle,
  labelMs,
  labelUnresolved,
  cycleEqMsHint,
  disabled = false,
  min = 0,
  max = 500,
}: TimeInputFieldProps): React.ReactElement {
  // Derive display value from canonical cycles value
  const displayValue: string = React.useMemo(() => {
    if (valueCycles === undefined) return ''
    if (unit === 'cycle') return String(valueCycles)
    // ms mode: cycles * 20
    return String(valueCycles * CYCLE_MS)
  }, [valueCycles, unit])

  // Derive display hint: "7 cycles = 140 ms" or "140 ms = 7 cycles"
  const hint: string | null = React.useMemo(() => {
    if (valueCycles === undefined || !cycleEqMsHint) return null
    const ms = valueCycles * CYCLE_MS
    if (unit === 'cycle') {
      return `${valueCycles} ${labelCycle} = ${ms} ${labelMs}`
    }
    return `${ms} ${labelMs} = ${valueCycles} ${labelCycle}`
  }, [valueCycles, unit, labelCycle, labelMs, cycleEqMsHint])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.trim()
    if (raw === '') {
      onChange(undefined)
      return
    }
    const parsed = parseFloat(raw)
    if (isNaN(parsed)) return
    if (unit === 'cycle') {
      onChange(parsed)
    } else {
      // ms → cycles: divide by 20, preserve fractional
      onChange(parsed / CYCLE_MS)
    }
  }

  const unitLabel = unit === 'cycle' ? labelCycle : labelMs
  const displayMin = unit === 'cycle' ? min : min * CYCLE_MS
  const displayMax = unit === 'cycle' ? max : max * CYCLE_MS
  const step = unit === 'cycle' ? 1 : CYCLE_MS

  return (
    <div className="time-input-field">
      <label className="time-input-field__label">
        {label}
        <span className="time-input-field__unit-badge">{unitLabel}</span>
      </label>
      <input
        type="number"
        className="time-input-field__input"
        value={displayValue}
        onChange={handleChange}
        disabled={disabled}
        min={displayMin}
        max={displayMax}
        step={step}
        placeholder={labelUnresolved}
      />
      {hint && (
        <span className="time-input-field__hint">{hint}</span>
      )}
    </div>
  )
}
