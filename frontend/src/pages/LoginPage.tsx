import { useState } from 'react'
import { login, extractErrorCode } from '../api/client'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

type Props = { onLogin: () => void }

// DEMO_MODE: enabled only when VITE_DEMO_MODE=true is set at Render build time.
// In development and all other environments this is always false.
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

// Public demo credentials — not a security boundary.
// These are baked into the bundle only when DEMO_MODE=true.
const DEMO_USERNAME = 'demo'
const DEMO_PASSWORD = DEMO_MODE ? 'A1234' : ''

/* Spot-welding process stage labels — engineering display only */
const PROCESS_STAGES = {
  tr: ['Yaklaşma', 'Sıkma', 'Çekirdek Oluşumu', 'Soğuma', 'Uzaklaşma'],
  en: ['Approach', 'Squeeze', 'Nugget Formation', 'Cooling', 'Retract'],
} as const

export function LoginPage({ onLogin }: Props) {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang].login
  const [username, setUsername] = useState(DEMO_USERNAME)
  const [password, setPassword] = useState(DEMO_PASSWORD)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit() {
    setError('')
    setBusy(true)
    try {
      await login(username, password)
      onLogin()
    } catch (err) {
      const errorCode = extractErrorCode(err)
      setError(
        errorCode === 'NETWORK_ERROR'
          ? t.errorNetwork
          : t.errorCredentials
      )
    } finally {
      setBusy(false)
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter') submit()
  }

  const stages = PROCESS_STAGES[lang]

  /* LOGIN-UX-FINAL-01: centered card → compact process strip below */
  return (
    <PublicLayout>
      <main className="login-pro-wrap">

        {/* ── 1. PRIMARY: login card ── */}
        <section className="login-pro-card" aria-label={t.ariaLabel}>
          <img
            src={`${import.meta.env.BASE_URL}spotweldpro-logo.png`}
            alt="SpotWeldPro AI"
            className="login-card-logo"
          />
          <p className="login-pro-subtitle">{t.note}</p>

          {DEMO_MODE && (
            <div
              className="login-pro-demo-banner"
              role="status"
              aria-label={t.demoBannerTitle}
              style={{
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--r-sm)',
                padding: '8px 12px',
                marginBottom: '12px',
                fontSize: 'var(--fs-xs)',
                color: 'var(--text-secondary)',
                textAlign: 'center',
              }}
            >
              <strong style={{ color: 'var(--accent)', marginRight: '6px' }}>
                {t.demoBannerTitle}
              </strong>
              {t.demoBannerText}
            </div>
          )}

          <div className="login-pro-fields">
            <div className="login-pro-field">
              <label htmlFor="login-username">{t.usernameLabel}</label>
              <input
                id="login-username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={handleKey}
                data-testid="login-username"
              />
            </div>
            <div className="login-pro-field">
              <label htmlFor="login-password">{t.passwordLabel}</label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={handleKey}
                data-testid="login-password"
              />
            </div>
          </div>

          {error && (
            <div className="login-pro-alert" role="alert" aria-live="polite">
              <span className="login-pro-alert-icon" aria-hidden="true">!</span>
              <span className="login-pro-alert-text">{error}</span>
            </div>
          )}

          <button
            className="btn btn-primary login-pro-submit"
            onClick={submit}
            disabled={busy}
            data-testid="login-submit"
          >
            {busy ? t.submitBusy : DEMO_MODE ? t.submitDemo : t.submitIdle}
          </button>
        </section>

        {/* ── 2. SECONDARY: compact 5-step welding process strip ── */}
        <div className="login-pro-visual" aria-hidden="true">
          <img
            src={`${import.meta.env.BASE_URL}spotweld-hero.png`}
            alt=""
            className="login-pro-visual-img"
          />
          <div className="login-pro-stages">
            {stages.map((s) => (
              <span key={s} className="login-pro-stage">{s}</span>
            ))}
          </div>
        </div>

      </main>
    </PublicLayout>
  )
}
