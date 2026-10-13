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
  const f = t.footerSection
  const c = t.contact
  const isLoggedIn = Boolean(localStorage.getItem('access_token'))

  function isActive(to: string) {
    if (to.startsWith('/#')) return false
    return pathname === to
  }

  return (
    <div>
      <nav
        className="pub-topnav"
        aria-label={lang === 'tr' ? 'Ana gezinme' : 'Main navigation'}
      >
        <Link className="pub-brand" to="/">
          <img
            src={`${import.meta.env.BASE_URL}spotweldpro-logo.png`}
            alt="SpotWeldPro AI"
            className="pub-brand-logo"
          />
        </Link>
        <div className="pub-nav-links">
          {t.nav.map((n) => (
            n.to.startsWith('/#')
              ? <a key={n.to} href={n.to}>{n.label}</a>
              : (
                <Link
                  key={n.to}
                  to={n.to}
                  className={isActive(n.to) ? 'active' : undefined}
                >
                  {n.label}
                </Link>
              )
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

      {/* ── Full footer ─────────────────────────────────────── */}
      <footer className="pub-footer-full">
        <div className="pub-footer-grid">

          {/* Brand column */}
          <div className="pub-footer-brand">
            <img src={`${import.meta.env.BASE_URL}spotweldpro-logo.png`} alt="SpotWeldPro AI" className="pub-footer-logo" />
            <p className="pub-footer-tagline">{f.tagline}</p>
          </div>

          {/* Product navigation column */}
          <div className="pub-footer-col">
            <h3 className="pub-footer-col-title">{f.navTitle}</h3>
            <ul className="pub-footer-links">
              {t.nav.filter(n => !n.to.startsWith('/#')).map((n) => (
                <li key={n.to}>
                  <Link to={n.to}>{n.label}</Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Capabilities column */}
          <div className="pub-footer-col">
            <h3 className="pub-footer-col-title">{f.capTitle}</h3>
            <ul className="pub-footer-links">
              {t.modules.slice(0, 5).map((m) => (
                <li key={m.slug}>
                  <Link to={'/features#' + m.slug}>{m.name}</Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact column */}
          <div className="pub-footer-col">
            <h3 className="pub-footer-col-title">{f.contactTitle}</h3>
            <ul className="pub-footer-links pub-footer-contact">
              <li>
                <strong>{c.person1.name}</strong>
                <a href="mailto:cekic.ilhan@gmail.com">cekic.ilhan@gmail.com</a>
                <a href="https://www.linkedin.com/in/ilhan-cekic-212b4a4a/" target="_blank" rel="noopener noreferrer">
                  {c.linkedinLabel} ↗
                </a>
              </li>
              <li style={{ marginTop: 'var(--sp-3)' }}>
                <strong>{c.person2.name}</strong>
                <a href="mailto:koray.tokol@outlook.com">koray.tokol@outlook.com</a>
                <a href="https://www.linkedin.com/in/koray-tokol/" target="_blank" rel="noopener noreferrer">
                  {c.linkedinLabel} ↗
                </a>
              </li>
            </ul>
          </div>

        </div>
        <div className="pub-footer-bottom">
          <span>{f.copyright}</span>
          <span className="pub-footer-login">
            {isLoggedIn
              ? <Link to="/app">{lang === 'tr' ? 'Uygulamaya Git' : 'Go to App'}</Link>
              : <Link to="/login">{t.cta.tertiary}</Link>
            }
          </span>
        </div>
      </footer>
    </div>
  )
}
