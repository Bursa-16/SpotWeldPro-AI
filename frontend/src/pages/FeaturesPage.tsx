import { Link } from 'react-router-dom'

export function FeaturesPage() {
  return (
    <div>
      <nav className="pub-topnav" aria-label="Ana gezinme">
        <Link className="pub-brand" to="/">
          <span className="brand-mark" aria-hidden="true">SW</span>
          <span>Spot&nbsp;Welding&nbsp;Parametre&nbsp;Analysis</span>
        </Link>
        <div className="pub-nav-links">
          <Link to="/">Ana Sayfa</Link>
          <Link to="/features" className="active">Özellikler</Link>
          <Link to="/how-it-works">Nasıl Kullanılır</Link>
          <Link to="/packages">Paketler</Link>
          <Link to="/demo">Demo</Link>
        </div>
      </nav>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="features-hero">
          <span className="eyebrow">Özellikler</span>
          <h1 id="features-hero">SpotWeldPro AI Modülleri</h1>
          <p className="lead">
            Kaynak kalitesi, proses penceresi, optimizasyon ve izlenebilirlik
            için deterministik mühendislik kuralları ve AI destekli açıklama.
          </p>
        </section>

        <section className="pub-section" aria-labelledby="overview-title">
          <h2 id="overview-title" className="pub-h2">Modüllere Genel Bakış</h2>
          <p className="pub-sub">
            Her modül, kaynağın fiziksel modeline dayalı hesaplama yapar.
            AI yalnızca açıklama ve özet sağlar; nihai karar her zaman
            deterministik kurallara dayanır.
          </p>
          <div className="pub-card-grid">
            {[
              {
                slug: 'command-center',
                code: 'CC',
                name: 'Command Center',
                text: 'Tüm hat genelinde kaynak kalitesi, makine duruşu ve risk özetini tek ekranda izleyin.',
              },
              {
                slug: 'weld-quality',
                code: 'WQ',
                name: 'Weld Quality Analysis',
                text: 'Nugget çapı, minimum kabul sınırı ve fışkırma riskine göre kaynağı değerlendirin.',
              },
              {
                slug: 'weld-lobe',
                code: 'WL',
                name: 'Weld Lobe Lab',
                text: 'Proses penceresini görselleştirin; akım, süre ve kuvvet bölgesini inceleyin.',
              },
              {
                slug: 'doe-optimization',
                code: 'DO',
                name: 'DOE Optimization',
                text: 'Deney tasarımı ile parametre uzayını tarayıp hedef nugget çapına en yakın bölgeyi bulun.',
              },
              {
                slug: 'failure-analysis',
                code: 'FA',
                name: 'Failure Analysis',
                text: 'Olası hata modlarını ve birincil katkı faktörlerini risk önceliğiyle sıralayın.',
              },
              {
                slug: 'projects',
                code: 'PW',
                name: 'Projects & Weld Points',
                text: 'Projeleri, kaynak noktalarını ve parça–istasyon–robot bağlamını yönetin.',
              },
              {
                slug: 'traceability',
                code: 'TR',
                name: 'Traceability / History',
                text: 'Analiz geçmişini, karar gerekçelerini ve mühendislik kuralı referanslarını koruyun.',
              },
              {
                slug: 'ai-explanation',
                code: 'AI',
                name: 'AI Explanation',
                text: 'AI, karmaşık sonuçları mühendislik bağlamıyla açıklar; karar kuralları deterministiktir.',
              },
            ].map((m) => (
              <article key={m.slug} id={m.slug} className="pub-card">
                <div className="pub-icon" aria-hidden="true">{m.code}</div>
                <h3 style={{ fontSize: 'var(--fs-h4)' }}>{m.name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>{m.text}</p>
                <div className="pub-card-action">
                  {m.slug === 'ai-explanation' ? (
                    <Link to="/how-it-works" className="btn btn-secondary btn-sm">Akışı Gör</Link>
                  ) : (
                    <Link to="/demo" className="btn btn-secondary btn-sm">Demo Talep Et</Link>
                  )}
                </div>
              </article>
            ))}
          </div>
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
