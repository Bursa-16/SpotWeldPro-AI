import { useState } from 'react'
import { login, extractErrorCode } from '../api/client'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

type Props = { onLogin: () => void }

/* Demo username prefilled for the public demo experience.
   Authentication is decided exclusively by the backend.
   Password is intentionally NOT prefilled. */
const DEMO_USERNAME = 'demo'

/* Spot-welding process stage labels — engineering display only */
const PROCESS_STAGES = {
  tr: ['Yaklaşma', 'Sıkma', 'Çekirdek Oluşumu', 'Soğuma', 'Uzaklaşma'],
  en: ['Approach', 'Squeeze', 'Nugget Formation', 'Cooling', 'Retract'],
} as const

export function LoginPage({ onLogin }: Props) {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang].login
  const [username, setUsername] = useState(DEMO_USERNAME)
  const [password, setPassword] = useState('')
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
            src="/spotweldpro-logo.png"
            alt="SpotWeldPro AI"
            className="login-card-logo"
          />
          <p className="login-pro-subtitle">{t.note}</p>

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
          >
            {busy ? t.submitBusy : t.submitIdle}
          </button>
        </section>

        {/* ── 2. SECONDARY: compact 5-step welding process strip ── */}
        <div className="login-pro-visual" aria-hidden="true">
          <img
            src="/spotweld-hero.png"
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
