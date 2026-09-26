/**
 * PUBLIC-01B: Shared public-facing layout.
 * Holds lang state and provides LangContext.Provider so ALL child pages
 * re-render reactively when the language toggle fires — no independent
 * useState per page.
 */
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { LangContext, getInitialLang, persistLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'
import type { Lang } from '../i18n/publicContent'

interface Props {
  children: ReactNode
}

export function PublicLayout({ children }: Props) {
  const [lang, setLangState] = useState<Lang>(getInitialLang)
  const { pathname } = useLocation()
  const t = PUBLIC_CONTENT[lang]

  function setLang(next: Lang) {
    persistLang(next)
    setLangState(next)
  }

  return (
    <LangContext.Provider value={{ lang, setLang }}>
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
              style={{
                height: '32px',
                objectFit: 'contain',
                display: 'block',
                flexShrink: 0,
              }}
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
    </LangContext.Provider>
  )
}
