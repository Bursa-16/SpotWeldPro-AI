import { Link } from 'react-router-dom'

const PACKAGES = [
  {
    name: 'Starter',
    tagline: 'Tek hat, temel değerlendirme.',
    points: ['Weld Quality Analysis', 'Proses penceresi özeti', 'Temel raporlama'],
  },
  {
    name: 'Professional',
    tagline: 'Mühendislik ekibi için tam çalışma alanı.',
    points: ['Weld Lobe Lab + DOE Optimization', 'Failure Analysis', 'Proje & kaynak noktası yönetimi'],
  },
  {
    name: 'Enterprise',
    tagline: 'Çok tesisli, tam izlenebilirlik.',
    points: ['Tam denetim izi', 'Çok tesis yönetimi', 'Kurumsal entegrasyonlar'],
  },
]

export function PackagesPage() {
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
          <Link to="/packages" className="active">Paketler</Link>
          <Link to="/demo">Demo</Link>
        </div>
      </nav>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="packages-hero">
          <span className="eyebrow">Paketler</span>
          <h1 id="packages-hero">Üretim İhtiyacınıza Uygun Paketinizi Seçin</h1>
          <p className="lead">
            Starter'dan Enterprise'a kadar ihtiyacınıza uygun pakete başlayın.
            Tüm paketler temel mühendislik kurallarını içerir.
          </p>
        </section>

        <section className="pub-section" aria-labelledby="compare-title">
          <h2 id="compare-title" className="pub-h2">Paket Karşılaştırması</h2>
          <p className="pub-sub">
            Detaylı bilgi için satış ekibimizle iletişime geçin.
          </p>
          <div className="pub-card-grid">
            {PACKAGES.map((p) => (
              <article key={p.name} className={'pub-card' + (p.name === 'Professional' ? ' recommended' : '')}>
                <b style={{ fontSize: 'var(--fs-h4)' }}>{p.name}</b>
                <span className="pub-note">{p.tagline}</span>
                <ul className="action-list">
                  {p.points.map((pt) => <li key={pt}>{pt}</li>)}
                </ul>
                <div className="pub-card-action">
                  {p.name === 'Professional' ? (
                    <Link to="/demo" className="btn btn-primary btn-sm">Demo Talep Et</Link>
                  ) : (
                    <Link to="/demo" className="btn btn-secondary btn-sm">Demo Talep Et</Link>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="pub-section" aria-labelledby="cta-title">
          <h2 id="cta-title" className="pub-h2">Hemen Başlayın</h2>
          <div className="pub-cta">
            <Link to="/demo" className="btn btn-primary btn-sm">Demo Talep Et</Link>
            <Link to="/features" className="btn btn-secondary btn-sm">Özellikleri İncele</Link>
          </div>
        </section>
      </main>

      <footer className="pub-footer">
        Spot Welding Parametre Analysis · SpotWeldPro AI
      </footer>
    </div>
  )
}
