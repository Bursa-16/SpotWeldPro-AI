import { useState } from 'react'
import { Link } from 'react-router-dom'

export function DemoPage() {
  const [submitted, setSubmitted] = useState(false)

  if (submitted) {
    return (
      <div>
        <nav className="pub-topnav" aria-label="Ana gezinme">
          <Link className="pub-brand" to="/">
            <span className="brand-mark" aria-hidden="true">SW</span>
            <span>Spot&nbsp;Welding&nbsp;Parametre&nbsp;Analysis</span>
          </Link>
          <div className="pub-nav-links">
            <Link to="/">Ana Sayfa</Link>
            <Link to="/features">Özellikler</Link>
            <Link to="/how-it-works">Nasıl Kullanılır</Link>
            <Link to="/packages">Paketler</Link>
            <Link to="/demo" className="active">Demo</Link>
          </div>
        </nav>
        <main className="pub-main">
          <section className="pub-hero" aria-labelledby="demo-hero">
            <span className="eyebrow">Demo</span>
            <h1 id="demo-hero">Demo Talep Edin</h1>
            <p className="lead">
              SpotWeldPro AI'ı kendi üretim ortamınızda denemek için talebinizi ilettiniz.
            </p>
          </section>
          <section className="pub-section" aria-labelledby="ack-title">
            <h2 id="ack-title" className="pub-h2">Talebiniz Alındı</h2>
            <div className="pub-ack">
              <span className="pub-ack-title">✓ Alındı</span>
              <span>Demo talebiniz başarıyla alındı. Ekibimiz en kısa sürede sizinle iletişime geçecektir.</span>
            </div>
            <div className="pub-cta">
              <Link to="/features" className="btn btn-secondary btn-sm">Özellikleri İncele</Link>
              <Link to="/how-it-works" className="btn btn-secondary btn-sm">Nasıl Kullanılır</Link>
            </div>
          </section>
        </main>
        <footer className="pub-footer">
          Spot Welding Parametre Analysis · SpotWeldPro AI
        </footer>
      </div>
    )
  }

  return (
    <div>
      <nav className="pub-topnav" aria-label="Ana gezinme">
        <Link className="pub-brand" to="/">
          <span className="brand-mark" aria-hidden="true">SW</span>
          <span>Spot&nbsp;Welding&nbsp;Parametre&nbsp;Analysis</span>
        </Link>
        <div className="pub-nav-links">
          <Link to="/">Ana Sayfa</Link>
          <Link to="/features">Özellikler</Link>
          <Link to="/how-it-works">Nasıl Kullanılır</Link>
          <Link to="/packages">Paketler</Link>
          <Link to="/demo" className="active">Demo</Link>
        </div>
      </nav>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="demo-hero">
          <span className="eyebrow">Demo</span>
          <h1 id="demo-hero">Demo Talep Edin</h1>
          <p className="lead">
            SpotWeldPro AI'ı kendi üretim ortamınızda denemek için formu
            doldurun; ekibimiz en kısa sürede sizinle iletişime geçsin.
          </p>
        </section>

        <section className="pub-section" aria-labelledby="form-title">
          <h2 id="form-title" className="pub-h2">Demo Talebi</h2>
          <p className="pub-sub">
            Aşağıdaki formu doldurarak demo talebinizi bize iletin.
          </p>
          <form
            className="pub-card pub-form"
            style={{ maxWidth: '520px' }}
            onSubmit={(e) => {
              e.preventDefault()
              setSubmitted(true)
            }}
          >
            <div className="pub-form-field">
              <label htmlFor="demo-name">Ad Soyad</label>
              <input id="demo-name" type="text" required placeholder="Adınız Soyadınız" />
            </div>
            <div className="pub-form-field">
              <label htmlFor="demo-email">E-posta</label>
              <input id="demo-email" type="email" required placeholder="sirket@example.com" />
            </div>
            <div className="pub-form-field">
              <label htmlFor="demo-company">Şirket</label>
              <input id="demo-company" type="text" required placeholder="Şirket Adı" />
            </div>
            <button type="submit" className="btn btn-primary btn-sm">Talebi Gönder</button>
          </form>
        </section>
      </main>

      <footer className="pub-footer">
        Spot Welding Parametre Analysis · SpotWeldPro AI
      </footer>
    </div>
  )
}
