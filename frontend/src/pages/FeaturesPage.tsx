import { Link } from 'react-router-dom'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

export function FeaturesPage() {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang]
  const f = t.features

  return (
    <PublicLayout>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="features-hero">
          <span className="eyebrow">{f.eyebrow}</span>
          <h1 id="features-hero">{f.heroTitle}</h1>
          <p className="lead">{f.heroSubtitle}</p>
        </section>

        <section className="pub-section" aria-labelledby="overview-title">
          <h2 id="overview-title" className="pub-h2">{f.overviewTitle}</h2>
          <p className="pub-sub">{f.overviewSub}</p>
          <div className="pub-card-grid">
            {t.modules.map((m) => (
              <article key={m.slug} id={m.slug} className="pub-card">
                <div className="pub-icon" aria-hidden="true">{m.code}</div>
                <h3 style={{ fontSize: 'var(--fs-h4)' }}>{m.name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>{m.text}</p>
                <div className="pub-card-action">
                  {m.slug === 'ai-explanation' ? (
                    <Link to="/how-it-works" className="btn btn-secondary btn-sm">
                      {f.flowBtn}
                    </Link>
                  ) : (
                    <Link to="/demo" className="btn btn-secondary btn-sm">
                      {f.demoBtn}
                    </Link>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="pub-trust" role="note">
          <span className="pub-icon" aria-hidden="true">i</span>
          <span>
            <b>{t.trustNote.bold}</b>{t.trustNote.rest}
          </span>
        </aside>
      </main>
    </PublicLayout>
  )
}
