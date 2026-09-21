import { useState } from 'react'
import { login } from '../api/client'

type Props = { onLogin: () => void }

/* Prefilled development credentials — form defaults ONLY.
   Authentication is decided exclusively by the backend. */
const DEFAULT_EMAIL = 'admin@spotwelding.example'
const DEFAULT_PASSWORD = 'ChangeMe123!'

export function LoginPage({ onLogin }: Props) {
  const [email, setEmail] = useState(DEFAULT_EMAIL)
  const [password, setPassword] = useState(DEFAULT_PASSWORD)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit() {
    setError('')
    setBusy(true)
    try {
      await login(email, password)
      onLogin()
    } catch (err) {
      const backendResponded = (err as { response?: unknown })?.response !== undefined
      setError(
        backendResponded
          ? 'E-posta veya şifre hatalı.'
          : 'Backend bağlantısı yok. Mühendislik verisi yüklenemedi; API servisini doğrulayın ve tekrar deneyin.'
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-wrap">
      <section className="login-panel" aria-label="Sign in">
        <div className="brand-row">
          <div className="brand-mark" aria-hidden="true">SW</div>
          <span>SpotWeldPro&nbsp;AI</span>
        </div>
        <p className="login-note">Kurumsal giriş — engineering intelligence for resistance spot welding</p>
        <div className="login-field">
          <label htmlFor="login-email">E-posta</label>
          <input id="login-email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="login-field">
          <label htmlFor="login-password">Şifre</label>
          <input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? 'Giriş yapılıyor…' : 'Giriş Yap'}
        </button>
        {error && <p className="login-error" role="alert">{error}</p>}
      </section>
    </main>
  )
}

