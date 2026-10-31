/**
 * ENERGY-P2.1-ENGINEERING-UX-HARDENING — i18n regression tests.
 *
 * Verifies that all new and existing energy-module i18n keys are present,
 * non-empty, bilingual, and contain required engineering terminology.
 */
import { describe, it, expect } from 'vitest'

import type { AppContent } from '../../i18n/appContent'
import { APP_CONTENT } from '../../i18n/appContent'

const getLocales = (): { TR: AppContent; EN: AppContent } => ({
  TR: APP_CONTENT.tr,
  EN: APP_CONTENT.en,
})

// ENG-I18N-01: Required new keys exist and are non-empty
describe('ENG-I18N-01 new energy module keys present', () => {
  const newKeys: (keyof AppContent['energyModule'])[] = [
    'engLimitationsNote',
    'kwhConversionNote',
  ]
  for (const key of newKeys) {
    it(`TR energyModule.${key} is non-empty string`, () => {
      const { TR } = getLocales()
      const val = TR.energyModule[key] as string
      expect(typeof val).toBe('string')
      expect(val.length).toBeGreaterThan(20)
    })
    it(`EN energyModule.${key} is non-empty string`, () => {
      const { EN } = getLocales()
      const val = EN.energyModule[key] as string
      expect(typeof val).toBe('string')
      expect(val.length).toBeGreaterThan(20)
    })
    it(`TR and EN energyModule.${key} differ`, () => {
      const { TR, EN } = getLocales()
      expect(TR.energyModule[key]).not.toBe(EN.energyModule[key])
    })
  }
})

// ENG-I18N-02: engLimitationsNote contains required engineering terms
describe('ENG-I18N-02 engLimitationsNote engineering content', () => {
  it('TR contains I²Rt formula reference', () => {
    expect(getLocales().TR.energyModule.engLimitationsNote).toMatch(/I_RMS|I_rms/)
  })
  it('EN contains I²Rt formula reference', () => {
    expect(getLocales().EN.energyModule.engLimitationsNote).toMatch(/I_RMS|I_rms/)
  })
  it('TR mentions resistance unit µΩ', () => {
    expect(getLocales().TR.energyModule.engLimitationsNote).toMatch(/µΩ|uΩ/)
  })
  it('EN mentions resistance unit µΩ', () => {
    expect(getLocales().EN.energyModule.engLimitationsNote).toMatch(/µΩ|uΩ/)
  })
  it('TR mentions single-pulse scope', () => {
    expect(getLocales().TR.energyModule.engLimitationsNote).toMatch(/tek darbe|single.pulse/i)
  })
  it('EN mentions single-pulse scope', () => {
    expect(getLocales().EN.energyModule.engLimitationsNote).toMatch(/single.pulse/i)
  })
  it('TR mentions theoretical energy', () => {
    expect(getLocales().TR.energyModule.engLimitationsNote).toMatch(/teorik|theoretical/i)
  })
  it('EN mentions theoretical energy', () => {
    expect(getLocales().EN.energyModule.engLimitationsNote).toMatch(/theoretical/i)
  })
})

// ENG-I18N-03: kwhConversionNote contains kWh conversion and tariff context
describe('ENG-I18N-03 kwhConversionNote cost transparency', () => {
  it('TR contains kJ→kWh conversion', () => {
    expect(getLocales().TR.energyModule.kwhConversionNote).toMatch(/kJ.*kWh/i)
  })
  it('EN contains kJ→kWh conversion', () => {
    expect(getLocales().EN.energyModule.kwhConversionNote).toMatch(/kJ.*kWh/i)
  })
  it('TR mentions EUR/kWh tariff unit', () => {
    expect(getLocales().TR.energyModule.kwhConversionNote).toMatch(/EUR\/kWh/)
  })
  it('EN mentions EUR/kWh tariff unit', () => {
    expect(getLocales().EN.energyModule.kwhConversionNote).toMatch(/EUR\/kWh/)
  })
  it('TR mentions theoretical estimate', () => {
    expect(getLocales().TR.energyModule.kwhConversionNote).toMatch(/teorik/i)
  })
  it('EN mentions theoretical estimate', () => {
    expect(getLocales().EN.energyModule.kwhConversionNote).toMatch(/theoretical/i)
  })
})

// ENG-I18N-04: Dashboard module new keys
describe('ENG-I18N-04 dashboardModule new keys', () => {
  const dashKeys: (keyof AppContent['dashboardModule'])[] = [
    'theoreticalCostNote',
    'unitEurYear',
    'unitUsdYear',
  ]
  for (const key of dashKeys) {
    it(`TR dashboardModule.${key} is non-empty`, () => {
      const val = getLocales().TR.dashboardModule[key] as string
      expect(typeof val).toBe('string')
      expect(val.length).toBeGreaterThan(0)
    })
    it(`EN dashboardModule.${key} is non-empty`, () => {
      const val = getLocales().EN.dashboardModule[key] as string
      expect(typeof val).toBe('string')
      expect(val.length).toBeGreaterThan(0)
    })
    it(`TR and EN dashboardModule.${key} differ`, () => {
      const { TR, EN } = getLocales()
      expect(TR.dashboardModule[key]).not.toBe(EN.dashboardModule[key])
    })
  }
})

// ENG-I18N-05: Existing keys are unchanged (regression guard)
describe('ENG-I18N-05 existing key regression', () => {
  it('TR multiPulseNote unchanged', () => {
    expect(getLocales().TR.energyModule.multiPulseNote).toContain('tek kaynak darbesi')
  })
  it('EN multiPulseNote unchanged', () => {
    expect(getLocales().EN.energyModule.multiPulseNote).toContain('single welding pulse')
  })
  it('TR labelCurrentKaHint unchanged', () => {
    expect(getLocales().TR.energyModule.labelCurrentKaHint).toContain('RMS')
  })
  it('EN labelCurrentKaHint unchanged', () => {
    expect(getLocales().EN.energyModule.labelCurrentKaHint).toContain('RMS welding current')
  })
  it('TR governanceNote unchanged', () => {
    expect(getLocales().TR.energyModule.governanceNote).toContain('E = I_RMS² × R × t')
  })
  it('EN governanceNote unchanged', () => {
    expect(getLocales().EN.energyModule.governanceNote).toContain('E = I_RMS² × R × t')
  })
  it('TR evaluationNote does not claim validated optimization algorithm', () => {
    const note = getLocales().TR.scenarioModule.evaluationNote
    // TR uses uppercase Turkish İ — match the actual word form
    expect(note).toMatch(/SENARYO|DEĞERLENDİRME|evaluation/i)
    expect(note).not.toMatch(/doğrulanmış optimizasyon algoritması/)
  })
  it('EN evaluationNote does not claim validated optimization algorithm', () => {
    const note = getLocales().EN.scenarioModule.evaluationNote
    expect(note).toMatch(/EVALUATION/i)
    expect(note).not.toMatch(/validated optimization algorithm/)
  })
})

// ENG-I18N-06: Unit transparency — tariff labels include currency + unit
describe('ENG-I18N-06 tariff label unit clarity', () => {
  it('TR labelTariffEur contains EUR/kWh', () => {
    expect(getLocales().TR.energyModule.labelTariffEur).toMatch(/EUR\/kWh/i)
  })
  it('EN labelTariffEur contains EUR/kWh', () => {
    expect(getLocales().EN.energyModule.labelTariffEur).toMatch(/EUR\/kWh/i)
  })
  it('TR unitEurYear contains EUR', () => {
    expect(getLocales().TR.dashboardModule.unitEurYear).toMatch(/EUR/)
  })
  it('EN unitEurYear contains EUR', () => {
    expect(getLocales().EN.dashboardModule.unitEurYear).toMatch(/EUR/)
  })
})
