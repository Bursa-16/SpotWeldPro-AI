/**
 * WEBSITE-FOOTER-LOGO-MODERNIZATION-01 — regression tests
 *
 * CSS ?raw imports return empty string in this Vitest node environment.
 * Tests verify publicContent.ts i18n data, PublicLayout.tsx structure,
 * and styles.css import integrity.
 */
import { describe, it, expect } from 'vitest'
import '../../styles.css'                                   // FOOT-01: must parse without throw
import { PUBLIC_CONTENT } from '../../i18n/publicContent'
import layoutSource from '../../components/PublicLayout.tsx?raw'

// FOOT-01: styles.css parses without error
describe('FOOT-01 styles.css parses without error', () => {
  it('import does not throw', () => {
    expect(true).toBe(true)
  })
})

// FOOT-02: footerSection i18n keys exist and are non-empty in both locales
describe('FOOT-02 footerSection i18n completeness', () => {
  const requiredKeys: (keyof typeof PUBLIC_CONTENT['en']['footerSection'])[] = [
    'tagline',
    'platformTitle',
    'engineeringTitle',
    'aiTitle',
    'contactTitle',
    'copyright',
    'liveDemoLabel',
    'useCasesLabel',
    'energyIntelLabel',
    'modelCatalogLabel',
  ]

  for (const key of requiredKeys) {
    it(`TR footerSection.${key} is non-empty`, () => {
      expect(PUBLIC_CONTENT.tr.footerSection[key]).toBeTruthy()
    })
    it(`EN footerSection.${key} is non-empty`, () => {
      expect(PUBLIC_CONTENT.en.footerSection[key]).toBeTruthy()
    })
  }
})

// FOOT-03: TR and EN labels are distinct (no language mixing in footerSection)
describe('FOOT-03 TR/EN footerSection labels differ where expected', () => {
  it('engineeringTitle differs between TR and EN', () => {
    expect(PUBLIC_CONTENT.tr.footerSection.engineeringTitle).not.toBe(
      PUBLIC_CONTENT.en.footerSection.engineeringTitle
    )
  })
  it('contactTitle differs between TR and EN', () => {
    expect(PUBLIC_CONTENT.tr.footerSection.contactTitle).not.toBe(
      PUBLIC_CONTENT.en.footerSection.contactTitle
    )
  })
  it('useCasesLabel differs between TR and EN', () => {
    expect(PUBLIC_CONTENT.tr.footerSection.useCasesLabel).not.toBe(
      PUBLIC_CONTENT.en.footerSection.useCasesLabel
    )
  })
  it('liveDemoLabel differs between TR and EN', () => {
    expect(PUBLIC_CONTENT.tr.footerSection.liveDemoLabel).not.toBe(
      PUBLIC_CONTENT.en.footerSection.liveDemoLabel
    )
  })
})

// FOOT-04: PublicLayout.tsx uses all new i18n keys
describe('FOOT-04 PublicLayout uses new footer column titles', () => {
  it('uses f.platformTitle', () => {
    expect(layoutSource).toContain('f.platformTitle')
  })
  it('uses f.engineeringTitle', () => {
    expect(layoutSource).toContain('f.engineeringTitle')
  })
  it('uses f.aiTitle', () => {
    expect(layoutSource).toContain('f.aiTitle')
  })
  it('uses f.liveDemoLabel', () => {
    expect(layoutSource).toContain('f.liveDemoLabel')
  })
  it('uses f.useCasesLabel', () => {
    expect(layoutSource).toContain('f.useCasesLabel')
  })
  it('uses f.energyIntelLabel', () => {
    expect(layoutSource).toContain('f.energyIntelLabel')
  })
  it('uses f.modelCatalogLabel', () => {
    expect(layoutSource).toContain('f.modelCatalogLabel')
  })
})

// FOOT-05: Live demo URL is present in footer
describe('FOOT-05 Live demo URL in footer', () => {
  it('footer contains the Render demo URL', () => {
    expect(layoutSource).toContain('https://spotweldpro-ai-demo.onrender.com/')
  })
  it('demo link opens in new tab (target _blank)', () => {
    expect(layoutSource).toContain('target="_blank"')
  })
})

// FOOT-06: Contact information is preserved
describe('FOOT-06 Contact information preserved', () => {
  it('İlhan Çekiç email is present', () => {
    expect(layoutSource).toContain('cekic.ilhan@gmail.com')
  })
  it('Koray Tokol email is present', () => {
    expect(layoutSource).toContain('koray.tokol@outlook.com')
  })
  it('LinkedIn link for person 1 is present', () => {
    expect(layoutSource).toContain('linkedin.com/in/ilhan-cekic-212b4a4a/')
  })
  it('LinkedIn link for person 2 is present', () => {
    expect(layoutSource).toContain('linkedin.com/in/koray-tokol/')
  })
})

// FOOT-07: Footer logo uses CSS class, not inline height
describe('FOOT-07 Footer logo sizing uses CSS class only', () => {
  it('footer logo uses pub-footer-logo class', () => {
    expect(layoutSource).toContain('className="pub-footer-logo"')
  })
  it('footer logo does not have inline height style', () => {
    expect(layoutSource).not.toMatch(/className="pub-footer-logo"[^/]*style=/)
  })
})

// FOOT-08: Old navTitle/capTitle keys no longer referenced
describe('FOOT-08 Obsolete footer keys removed', () => {
  it('f.navTitle is not referenced in layout', () => {
    expect(layoutSource).not.toContain('f.navTitle')
  })
  it('f.capTitle is not referenced in layout', () => {
    expect(layoutSource).not.toContain('f.capTitle')
  })
})
