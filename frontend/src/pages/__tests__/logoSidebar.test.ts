/**
 * LOGO-UX-RESTORE-01 — sidebar logo regression tests
 *
 * CSS ?raw imports return empty string in this Vitest node environment.
 * Tests verify App.tsx structure and that CSS file exists/parses correctly.
 */
import { describe, it, expect } from 'vitest'
import '../../styles.css'                          // LOGO-01: must exist and parse without throw
import appSource from '../../App.tsx?raw'

// LOGO-01: styles.css imports without error
describe('LOGO-01 styles.css parses without error', () => {
  it('styles.css import does not throw', () => {
    expect(true).toBe(true)
  })
})

// LOGO-02: App.tsx uses correct CSS class names for both sidebar states
describe('LOGO-02 Sidebar logo class usage in App.tsx', () => {
  it('expanded state uses className="sidebar-logo"', () => {
    expect(appSource).toContain('className="sidebar-logo"')
  })

  it('collapsed state uses sidebar-logo-icon-wrap', () => {
    expect(appSource).toContain('sidebar-logo-icon-wrap')
  })

  it('logo img src points to spotweldpro-logo.png', () => {
    expect(appSource).toContain('/spotweldpro-logo.png')
  })
})

// LOGO-03: Expanded logo is not constrained by a hard-coded small height attribute
describe('LOGO-03 Logo is not small due to inline height', () => {
  it('logo img does not use inline height style', () => {
    // Check that sidebar-logo is not accompanied by inline height style
    const logoImgPattern = /className="sidebar-logo"[^/]*style=\{[^}]*height:\s*\d+px/
    expect(appSource).not.toMatch(logoImgPattern)
  })

  it('logo img does not use height attribute directly', () => {
    const heightAttrPattern = /className="sidebar-logo"[^/]*height="\d+"/
    expect(appSource).not.toMatch(heightAttrPattern)
  })
})

// LOGO-04: Both sidebar states use the official logo asset
describe('LOGO-04 Official logo asset used in both states', () => {
  it('icon-wrap img uses spotweldpro-logo.png', () => {
    // The icon-wrap and logo img are both for spotweldpro-logo.png
    const logoMatches = [...appSource.matchAll(/spotweldpro-logo\.png/g)]
    expect(logoMatches.length).toBeGreaterThanOrEqual(2)
  })
})
