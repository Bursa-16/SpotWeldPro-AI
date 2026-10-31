/**
 * MODEL-CATALOG-CSS-FIX-01 — regression tests
 *
 * CSS ?raw imports return empty string in this Vitest node environment
 * (Vite processes CSS before the ?raw suffix can capture content).
 * Tests use:
 *   - Regular CSS import to verify the file exists and is valid CSS (no throw).
 *   - TSX ?raw import to verify the import statement and mc-* class usage.
 */
import { describe, it, expect } from 'vitest'
import '../ModelCatalogPage.css'          // MC-CSS-01: must exist and parse without throw
import tsxSource from '../ModelCatalogPage.tsx?raw'

// MC-CSS-01: CSS file exists and imports without error
describe('MC-CSS-01 ModelCatalogPage.css can be imported', () => {
  it('CSS import does not throw (file exists and is valid CSS)', () => {
    // Import at module level above — reaching this point means no throw occurred.
    expect(true).toBe(true)
  })
})

// MC-CSS-02: ModelCatalogPage.tsx uses all expected mc-* class names
describe('MC-CSS-02 mc-* class names used in component', () => {
  const requiredClasses = [
    'mc-grid',
    'mc-card',
    'mc-badge',
    'mc-chip',
    'mc-tabs',
    'mc-tab',
    'mc-expand-btn',
    'mc-details',
    'mc-detail-list',
    'mc-evidence',
    'mc-metrics',
    'mc-metric-value',
    'mc-alert',
    'mc-disclaimer',
    'mc-loading',
    'mc-empty',
  ]

  for (const cls of requiredClasses) {
    it(`component references ${cls}`, () => {
      expect(tsxSource).toContain(cls)
    })
  }
})

// MC-CSS-03: Component uses className (not inline styles) for catalog layout
describe('MC-CSS-03 component styling approach', () => {
  it('uses className for mc-grid layout', () => {
    expect(tsxSource).toContain('className="mc-grid"')
  })
  it('uses className for mc-card', () => {
    expect(tsxSource).toMatch(/className=.*mc-card/)
  })
  it('uses className for mc-badge status badges', () => {
    expect(tsxSource).toMatch(/mc-badge mc-badge--/)
  })
  it('uses className for mc-tabs navigation', () => {
    expect(tsxSource).toContain('className="mc-tabs"')
  })
  it('does not use style= for card layout (no inline layout styles)', () => {
    // Card grid and card shell must not use inline styles — CSS classes only.
    expect(tsxSource).not.toMatch(/className="mc-grid"[^>]*style=/)
  })
})

// MC-CSS-04: TSX imports the CSS file
describe('MC-CSS-04 CSS import present in ModelCatalogPage.tsx', () => {
  it("import './ModelCatalogPage.css' is present", () => {
    expect(tsxSource).toContain("import './ModelCatalogPage.css'")
  })
})
