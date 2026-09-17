import { Link } from 'react-router-dom'
import { useState } from 'react'

const FEATURES = [
  { slug: 'command-center', code: 'CC', name: 'Command Center', text: 'TÃ¼m hat genelinde kaynak kalitesi, makine duruÅŸu ve risk Ã¶zetini tek ekranda izleyin.' },
  { slug: 'weld-quality', code: 'WQ', name: 'Weld Quality Analysis', text: 'Nugget Ã§apÄ±, minimum kabul sÄ±nÄ±rÄ± ve fÄ±ÅŸkÄ±rma (expulsion) riskine gÃ¶re kaynaÄŸÄ± deÄŸerlendirin.' },
  { slug: 'weld-lobe', code: 'WL', name: 'Weld Lobe Lab', text: 'Proses penceresini (weld lobe) gÃ¶rselleÅŸtirin; akÄ±mâ€“sÃ¼reâ€“kuvvet bÃ¶lgesini inceleyin.' },
  { slug: 'doe-optimization', code: 'DO', name: 'DOE Optimization', text: 'Deney tasarÄ±mÄ± ile parametre uzayÄ±nÄ± tarayÄ±p hedef nugget Ã§apÄ±na en yakÄ±n bÃ¶lgeyi bulun.' },
  { slug: 'failure-analysis', code: 'FA', name: 'Failure Analysis', text: 'OlasÄ± hata modlarÄ±nÄ± ve birincil katkÄ± faktÃ¶rlerini risk Ã¶nceliÄŸiyle sÄ±ralayÄ±n.' },
  { slug: 'projects', code: 'PW', name: 'Projects & Weld Points', text: 'Projeleri, kaynak noktalarÄ±nÄ± ve parÃ§aâ€“istasyonâ€“robot baÄŸlamÄ±nÄ± yÃ¶netin.' },
  { slug: 'traceability', code: 'TR', name: 'Traceability / History', text: 'Analiz geÃ§miÅŸini, karar gerekÃ§elerini ve mÃ¼hendislik kuralÄ± referanslarÄ±nÄ± koruyun.' },
  { slug: 'ai-explanation', code: 'AI', name: 'AI Explanation', text: 'AI, karmaÅŸÄ±k sonuÃ§larÄ± mÃ¼hendislik baÄŸlamÄ±yla aÃ§Ä±klar; karar kurallarÄ± deterministiktir.' },
]
const INDUSTRIES = [
  { name: 'Otomotiv', use: 'YapÄ±sal gÃ¶vde ve ÅŸase baÄŸlantÄ±larÄ±nda yÃ¼ksek adetli nokta kaynaÄŸÄ±.', need: 'TutarlÄ± nugget kalitesi ve parÃ§a bazlÄ± izlenebilirlik.', modules: 'Weld Quality Analysis Â· Traceability' },
  { name: 'Beyaz EÅŸya', use: 'Ä°nce saÃ§ panellerin seri kaynaÄŸÄ±nda dÃ¶ngÃ¼ sÃ¼resi kontrolÃ¼.', need: 'Dar proses penceresinde hÄ±zlÄ± parametre doÄŸrulamasÄ±.', modules: 'Weld Lobe Lab Â· DOE Optimization' },
  { name: 'Savunma', use: 'YÃ¼ksek kritiklikteki baÄŸlantÄ±larda tam doÄŸrulanmÄ±ÅŸ parametreler.', need: 'Kural tabanlÄ± doÄŸrulama ve eksiksiz denetim izi.', modules: 'Traceability Â· Projects & Weld Points' },
  { name: 'RaylÄ± Sistemler', use: 'AraÃ§ gÃ¶vdesi ve alt yapÄ± birleÅŸimlerinde uzun sÃ¼reli dayanÄ±m.', need: 'Minimum nugget kanÄ±tÄ± ve partide raporlanabilirlik.', modules: 'Command Center Â· Failure Analysis' },
  { name: 'Makine Ä°malatÄ±', use: 'KarmaÅŸÄ±k parÃ§a kombinasyonlarÄ±nda kaynak penceresinin yeniden kurulmasÄ±.', need: 'Yeni malzeme giriÅŸlerinde proses penceresinin haritalanmasÄ±.', modules: 'Weld Lobe Lab Â· DOE Optimization' },
  { name: 'Sac Metal Ãœretimi', use: 'FarklÄ± kalÄ±nlÄ±k ve kaplama kombinasyonlarÄ±nda tutarlÄ± kalite.', need: 'Malzeme yÄ±ÄŸÄ±nÄ±na gÃ¶re parametre hassasiyeti.', modules: 'Weld Quality Analysis Â· Projects' },
]

const PACKAGES = [
  { name: 'Starter', tagline: 'Tek hat, temel deÄŸerlendirme.', points: ['Weld Quality Analysis', 'Proses penceresi Ã¶zeti', 'Temel raporlama'] },
  { name: 'Professional', tagline: 'MÃ¼hendislik ekibi iÃ§in tam Ã§alÄ±ÅŸma alanÄ±.', points: ['Weld Lobe Lab + DOE Optimization', 'Failure Analysis', 'Proje & kaynak noktasÄ± yÃ¶netimi'] },
  { name: 'Enterprise', tagline: 'Ã‡ok tesisli, tam izlenebilirlik.', points: ['Tam denetim izi', 'Ã‡ok tesis yÃ¶netimi', 'Kurumsal entegrasyonlar'] },
]
export function LandingPage() {
  const [openIndustry, setOpenIndustry] = useState(0)

  return (
    <div>
      <nav className="pub-topnav" aria-label="Ana gezinme">
        <Link className="pub-brand" to="/">
          <span className="brand-mark" aria-hidden="true">SW</span>
          <span>Spot&nbsp;Welding&nbsp;Parametre&nbsp;Analysis</span>
        </Link>
        <div className="pub-nav-links">
          <Link to="/" className="active">Ana Sayfa</Link>
          <Link to="/features">Özellikler</Link>
          <Link to="/how-it-works">Nasıl Çalışır</Link>
          <Link to="/packages">Paketler</Link>
          <Link to="/demo">Demo</Link>
          <Link to="/login">Giriş</Link>
        </div>
      </nav>

      <header className="pub-hero">
        <div className="pub-hero-grid">
          <div>
            <div className="eyebrow">SpotWeldPro AI · Engineering Workstation</div>
            <h1>Nokta Kaynak Parametre Analizi</h1>
            <p className="lead">Deterministik mühendislik kuralları ile kaynak kalitesini doğrulayın; deney tasarımı ve hata analizi ile prosesi yönetin.</p>
            <div className="pub-cta">
              <Link to="/demo" className="btn btn-primary">Demoyu Aç</Link>
              <Link to="/login" className="pub-link-cta">Giriş Yap →</Link>
            </div>
          </div>
          <aside className="hero-preview" aria-label="Engineering product preview">
            <div className="hero-preview-head">
              <span>Engineering Inputs</span>
              <span className="badge accent">Deterministic Rule Check</span>
            </div>
            <div className="hero-preview-grid">
              <div className="hero-field"><span>Current</span><span className="hero-field-val">— kA</span></div>
              <div className="hero-field"><span>Time</span><span className="hero-field-val">— cyc</span></div>
              <div className="hero-field"><span>Force</span><span className="hero-field-val">— kN</span></div>
              <div className="hero-field"><span>Tip</span><span className="hero-field-val">— mm</span></div>
            </div>
            <div className="hero-window" aria-hidden="true">
              <span>Process Window</span>
              <div className="hero-window-frame" />
            </div>
            <div className="hero-preview-foot">
              <span className="ctx-chip">Traceability: <strong>audit-backed</strong></span>
              <span className="ctx-chip accent">State: <strong>Awaiting analysis</strong></span>
            </div>
          </aside>
        </div>
      </header>

      <main className="pub-main">
        <section className="pub-section" aria-labelledby="features-title">
          <h2 id="features-title" className="pub-h2">Modüller</h2>
          <p className="pub-sub">Bir modülü incelemek için Özellikler sayfasındaki detayı görüntüleyin.</p>
          <div className="pub-card-grid">
            {FEATURES.map((f) => (
              <article key={f.slug} className="pub-card">
                <div className="pub-icon" aria-hidden="true">{f.code}</div>
                <h3 style={{ fontSize: 'var(--fs-h4)' }}>{f.name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>{f.text}</p>
                <Link to={'/features#' + f.slug} className="btn btn-secondary btn-sm">Detayı Gör</Link>
              </article>
            ))}
          </div>
        </section>

        <section className="pub-section" aria-labelledby="industry-title">
          <h2 id="industry-title" className="pub-h2">Sektör Kullanım Senaryoları</h2>
          <p className="pub-sub">Kendi üretim bağlamınızı seçin; tipik kullanım, ihtiyaç ve ilgili modülleri görün.</p>
          <div className="pub-card-grid">
            {INDUSTRIES.map((ind, i) => (
              <button
                key={ind.name}
                type="button"
                className={'pub-industry-card' + (openIndustry === i ? ' open' : '')}
                onClick={() => setOpenIndustry(openIndustry === i ? -1 : i)}
              >
                <b>{ind.name}</b>
                <span className="pub-note">{ind.use}</span>
                {openIndustry === i && (
                  <span style={{ display: 'block' }}>
                    <span className="pub-note">İhtiyaç: {ind.need}</span>
                    <br />
                    <span className="pub-note">Modüller: {ind.modules}</span>
                  </span>
                )}
              </button>
            ))}
          </div>
        </section>

        <section className="pub-section" aria-labelledby="packages-title">
          <h2 id="packages-title" className="pub-h2">Paketler</h2>
          <p className="pub-sub">Detaylı karşılaştırma için Paketler sayfasını açın.</p>
          <div className="pub-card-grid">
            {PACKAGES.map((p) => (
              <article key={p.name} className="pub-pkg-mini">
                <b style={{ fontSize: 'var(--fs-h4)' }}>{p.name}</b>
                <span className="pub-note">{p.tagline}</span>
                <ul className="action-list">
                  {p.points.map((pt) => <li key={pt}>{pt}</li>)}
                </ul>
              </article>
            ))}
          </div>
          <p style={{ marginTop: 'var(--sp-3)' }}>
            <Link to="/packages" className="btn btn-secondary">Paket Karşılaştırması</Link>
          </p>
        </section>
        <aside className="pub-trust" role="note">
          <span className="pub-icon" aria-hidden="true">i</span>
          <span>
            <b>AI açıklama ve mühendislik bağlamı sağlar;</b>
            {' '}nihai karar deterministik mühendislik kurallarına dayanır.
          </span>
        </aside>
      </main>

      <footer className="pub-footer">
        Spot Welding Parametre Analysis · SpotWeldPro AI
      </footer>
    </div>
  )
}