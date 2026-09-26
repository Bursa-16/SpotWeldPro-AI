import { Link } from 'react-router-dom'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

export function PackagesPage() {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang]
  const p = t.packages

  return (
    <PublicLayout>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="packages-hero">
          <span className="eyebrow">{p.eyebrow}</span>
          <h1 id="packages-hero">{p.heroTitle}</h1>
          <p className="lead">{p.heroSubtitle}</p>
        </section>

        <section className="pub-section" aria-labelledby="compare-title">
          <h2 id="compare-title" className="pub-h2">{p.compareTitle}</h2>
          <p className="pub-sub">{p.compareSub}</p>
          <div className="pub-card-grid">
            {t.tiers.map((tier) => (
              <article
                key={tier.name}
                className={'pub-card' + (tier.name === 'Professional' ? ' recommended' : '')}
              >
                <b style={{ fontSize: 'var(--fs-h4)' }}>{tier.name}</b>
                <span className="pub-note">{tier.tagline}</span>
                <ul className="action-list">
                  {tier.points.map((pt) => <li key={pt}>{pt}</li>)}
                </ul>
                <div className="pub-card-action">
                  {tier.name === 'Professional' ? (
                    <Link to="/demo" className="btn btn-primary btn-sm">{p.demoBtn}</Link>
                  ) : (
                    <Link to="/demo" className="btn btn-secondary btn-sm">{p.demoBtn}</Link>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="pub-section" aria-labelledby="cta-title">
          <h2 id="cta-title" className="pub-h2">{p.ctaTitle}</h2>
          <div className="pub-cta">
            <Link to="/demo" className="btn btn-primary btn-sm">{p.demoBtn}</Link>
            <Link to="/features" className="btn btn-secondary btn-sm">{p.exploreBtn}</Link>
          </div>
        </section>
      </main>
    </PublicLayout>
  )
}
