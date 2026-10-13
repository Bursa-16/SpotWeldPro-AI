/**
 * PUBLIC-01B: Shared public-facing layout.
 * Pure consumer of LangContext — state lives in PublicLangProvider (App.tsx).
 * Calls useLang() so the toggle button propagates through the single
 * shared provider, causing all page-level consumers to re-render reactively.
 * APP-I18N-03-R7: removed own useState / LangContext.Provider (was shadowing
 * PublicLangProvider and breaking hero/content language switching).
 */
import { Link, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

interface Props {
  children: ReactNode
}

export function PublicLayout({ children }: Props) {
  const { lang, setLang } = useLang()
  const { pathname } = useLocation()
  const t = PUBLIC_CONTENT[lang]

  return (
    <div>
      <nav
        className="pub-topnav"
        aria-label={lang === 'tr' ? 'Ana gezinme' : 'Main navigation'}
      >
        <Link className="pub-brand" to="/">
          <img
            src="/spotweldpro-logo.png"
            alt="SpotWeldPro AI"
            className="pub-brand-logo"
          />
        </Link>
        <div className="pub-nav-links">
          {t.nav.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className={pathname === n.to ? 'active' : undefined}
            >
              {n.label}
            </Link>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setLang(lang === 'tr' ? 'en' : 'tr')}
          aria-label={lang === 'tr' ? 'Switch to English' : "Türkçe'ye geç"}
          style={{
            marginLeft: 'auto',
            fontSize: 'var(--fs-xs)',
            color: 'var(--text-secondary)',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r-sm)',
            padding: '3px 10px',
            cursor: 'pointer',
            fontFamily: 'var(--font-sans)',
            letterSpacing: '0.06em',
            fontWeight: 600,
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          {t.langToggle}
        </button>
      </nav>

      {children}

      <footer className="pub-footer">
        {t.footer}
      </footer>
    </div>
  )
}
