/**
 * P2-E Help Center tests.
 * Validates module coverage, bilingual content, examples, warnings, and
 * cross-references without requiring a DOM environment.
 */
import { describe, it, expect } from 'vitest'
import { HELP_MODULES, GLOSSARY } from '../HelpCenterPage'

const REQUIRED_MODULE_IDS = [
  'dashboard', 'projects', 'analysis', 'failure', 'engineering',
  'models', 'statistical',
  'energy-single', 'energy-multi', 'energy-dashboard',
  'energy-map', 'energy-scenario', 'energy-import',
]

const LANGS = ['tr', 'en'] as const

// HC-01: All required module IDs are present
describe('HC-01 module coverage', () => {
  const presentIds = HELP_MODULES.map(m => m.id)
  for (const id of REQUIRED_MODULE_IDS) {
    it(`module "${id}" is documented`, () => {
      expect(presentIds).toContain(id)
    })
  }
})

// HC-02: All modules have non-empty bilingual content
describe('HC-02 bilingual content completeness', () => {
  for (const m of HELP_MODULES) {
    describe(`[${m.id}]`, () => {
      for (const lang of LANGS) {
        it(`nav.${lang} is non-empty`, () => {
          expect(typeof m.nav[lang]).toBe('string')
          expect(m.nav[lang].length).toBeGreaterThan(0)
        })
        it(`title.${lang} is non-empty`, () => {
          expect(m.title[lang].length).toBeGreaterThan(0)
        })
        it(`purpose.${lang} is non-empty`, () => {
          expect(m.purpose[lang].length).toBeGreaterThan(0)
        })
        it(`steps.${lang} has at least 3 steps`, () => {
          expect(m.steps[lang].length).toBeGreaterThanOrEqual(3)
        })
        it(`steps.${lang} all non-empty`, () => {
          for (const s of m.steps[lang]) {
            expect(s.length).toBeGreaterThan(0)
          }
        })
      }
    })
  }
})

// HC-03: TR and EN steps are the same length (parity check)
describe('HC-03 step parity TR/EN', () => {
  for (const m of HELP_MODULES) {
    it(`[${m.id}] TR and EN step counts match`, () => {
      expect(m.steps.tr.length).toBe(m.steps.en.length)
    })
  }
})

// HC-04: Input fields have descriptions in both languages
describe('HC-04 input field bilingual descriptions', () => {
  for (const m of HELP_MODULES) {
    if (!m.inputs?.length) continue
    for (const f of m.inputs) {
      for (const lang of LANGS) {
        it(`[${m.id}] input "${f.name}" has desc.${lang}`, () => {
          expect(f.desc[lang].length).toBeGreaterThan(0)
        })
      }
    }
  }
})

// HC-05: Output fields have descriptions in both languages
describe('HC-05 output field bilingual descriptions', () => {
  for (const m of HELP_MODULES) {
    if (!m.outputs?.length) continue
    for (const o of m.outputs) {
      for (const lang of LANGS) {
        it(`[${m.id}] output "${o.name}" has desc.${lang}`, () => {
          expect(o.desc[lang].length).toBeGreaterThan(0)
        })
      }
    }
  }
})

// HC-06: Modules with examples have non-empty inputs and outputs
describe('HC-06 example completeness', () => {
  for (const m of HELP_MODULES) {
    if (!m.example) continue
    it(`[${m.id}] example label contains SYNTHETIC`, () => {
      expect(m.example!.label).toContain('SYNTHETIC')
    })
    it(`[${m.id}] example has at least 2 inputs`, () => {
      expect(m.example!.inputs.length).toBeGreaterThanOrEqual(2)
    })
    it(`[${m.id}] example has at least 1 output`, () => {
      expect(m.example!.outputs.length).toBeGreaterThanOrEqual(1)
    })
    for (const lang of LANGS) {
      it(`[${m.id}] example note.${lang} is non-empty`, () => {
        expect(m.example!.note[lang].length).toBeGreaterThan(0)
      })
    }
  }
})

// HC-07: Safety-critical modules have warnings
describe('HC-07 safety warnings present', () => {
  const safetyModules = ['failure', 'engineering', 'energy-single', 'energy-dashboard', 'energy-scenario', 'statistical']
  for (const id of safetyModules) {
    it(`[${id}] has warnings in TR`, () => {
      const m = HELP_MODULES.find(x => x.id === id)
      expect(m?.warnings?.tr.length).toBeGreaterThan(0)
    })
    it(`[${id}] has warnings in EN`, () => {
      const m = HELP_MODULES.find(x => x.id === id)
      expect(m?.warnings?.en.length).toBeGreaterThan(0)
    })
  }
})

// HC-08: TR and EN warning counts match
describe('HC-08 warning parity TR/EN', () => {
  for (const m of HELP_MODULES) {
    if (!m.warnings) continue
    it(`[${m.id}] TR/EN warning counts match`, () => {
      expect(m.warnings!.tr.length).toBe(m.warnings!.en.length)
    })
  }
})

// HC-09: Related module IDs all resolve to valid modules
describe('HC-09 cross-reference integrity', () => {
  const validIds = new Set(HELP_MODULES.map(m => m.id))
  for (const m of HELP_MODULES) {
    for (const rid of m.relatedIds) {
      it(`[${m.id}] relatedId "${rid}" resolves`, () => {
        expect(validIds.has(rid)).toBe(true)
      })
    }
  }
})

// HC-10: Each module has at least 2 tags
describe('HC-10 module tags', () => {
  for (const m of HELP_MODULES) {
    it(`[${m.id}] has at least 2 tags`, () => {
      expect(m.tags.length).toBeGreaterThanOrEqual(2)
    })
  }
})

// HC-11: Glossary completeness
describe('HC-11 glossary', () => {
  it('has at least 15 terms', () => {
    expect(GLOSSARY.length).toBeGreaterThanOrEqual(15)
  })
  for (const g of GLOSSARY) {
    for (const lang of LANGS) {
      it(`term "${g.term}" has def.${lang}`, () => {
        expect(g.def[lang].length).toBeGreaterThan(0)
      })
    }
  }
  it('all terms are unique', () => {
    const terms = GLOSSARY.map(g => g.term)
    const unique = new Set(terms)
    expect(unique.size).toBe(terms.length)
  })
})

// HC-12: Energy modules are all documented
describe('HC-12 energy module coverage', () => {
  const energyIds = ['energy-single', 'energy-multi', 'energy-dashboard', 'energy-map', 'energy-scenario', 'energy-import']
  for (const id of energyIds) {
    it(`energy module "${id}" documented`, () => {
      expect(HELP_MODULES.some(m => m.id === id)).toBe(true)
    })
  }
})

// HC-13: Diagrams only assigned to known types
describe('HC-13 diagram type integrity', () => {
  const VALID_DIAGRAMS = ['rsw', 'energy-window', 'weld-lobe', 'taguchi', 'multi-spot'] as const
  for (const m of HELP_MODULES) {
    if (!m.diagram) continue
    it(`[${m.id}] diagram type is valid`, () => {
      expect(VALID_DIAGRAMS).toContain(m.diagram)
    })
  }
})

// HC-14: Total module count
describe('HC-14 total modules', () => {
  it('documents at least 12 modules', () => {
    expect(HELP_MODULES.length).toBeGreaterThanOrEqual(12)
  })
})

// HC-15: No module has identical TR and EN title (translation actually differs)
describe('HC-15 translations are distinct', () => {
  for (const m of HELP_MODULES) {
    it(`[${m.id}] TR/EN titles differ`, () => {
      expect(m.title.tr).not.toBe(m.title.en)
    })
  }
})
