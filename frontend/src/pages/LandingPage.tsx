import { Link } from 'react-router-dom'
import { useState } from 'react'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

export function LandingPage() {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang]
  const l = t.landing
  const [openIndustry, setOpenIndustry] = useState(0)

  return (
    <PublicLayout>
      <header className="pub-hero">
        <div className="pub-hero-grid">
          <div>
            <div className="eyebrow">{l.eyebrow}</div>
            <h1>{l.heroTitle}</h1>
            <p className="lead">{l.heroSubtitle}</p>
            <div className="pub-cta">
              <Link to="/demo" className="btn btn-primary">{t.cta.primary}</Link>
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
          <h2 id="features-title" className="pub-h2">{l.modulesTitle}</h2>
          <p className="pub-sub">{l.modulesSub}</p>
          <div className="pub-card-grid">
            {t.modules.map((f) => (
              <article key={f.slug} className="pub-card">
                <div className="pub-icon" aria-hidden="true">{f.code}</div>
                <h3 style={{ fontSize: 'var(--fs-h4)' }}>{f.name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>{f.text}</p>
                <Link to={'/features#' + f.slug} className="btn btn-secondary btn-sm">
                  {l.moduleDetailBtn}
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="pub-section" aria-labelledby="industry-title">
          <h2 id="industry-title" className="pub-h2">{l.industriesTitle}</h2>
          <p className="pub-sub">{l.industriesSub}</p>
          <div className="pub-card-grid">
            {t.industries.map((ind, i) => (
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
                    <span className="pub-note">{l.industriesNeedLabel} {ind.need}</span>
                    <br />
                    <span className="pub-note">{l.industriesModulesLabel} {ind.modules}</span>
                  </span>
                )}
              </button>
            ))}
          </div>
        </section>

        <section className="pub-section" aria-labelledby="packages-title">
          <h2 id="packages-title" className="pub-h2">{l.packagesTitle}</h2>
          <p className="pub-sub">{l.packagesSub}</p>
          <div className="pub-card-grid">
            {t.tiers.map((p) => (
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
            <Link to="/packages" className="btn btn-secondary">{l.packagesCompareBtn}</Link>
          </p>
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
