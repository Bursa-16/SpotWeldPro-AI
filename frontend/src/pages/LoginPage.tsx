import { useState } from 'react'
import { login } from '../api/client'

type Props = { onLogin: () => void }

/* Demo username prefilled for the public demo experience.
   Authentication is decided exclusively by the backend.
   Password is intentionally NOT prefilled. */
const DEMO_USERNAME = 'demo'


export function LoginPage({ onLogin }: Props) {
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
          <label htmlFor="login-username">Kullanıcı Adı</label>
          <input id="login-username" type="text" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} />
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

