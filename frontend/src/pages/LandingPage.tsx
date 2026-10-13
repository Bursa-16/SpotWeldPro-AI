import { Link } from 'react-router-dom'
import { useState } from 'react'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'
import { WeldVisualizationPanel } from '../components/public/WeldVisualizationPanel'

export function LandingPage() {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang]
  const l = t.landing
  const c = t.contact
  const [openIndustry, setOpenIndustry] = useState(0)
  const isLoggedIn = Boolean(localStorage.getItem('access_token'))

  return (
    <PublicLayout>
      {/* ── Hero ──────────────────────────────────────────────── */}
      <header className="pub-hero land-hero">
        <div className="land-hero-inner">
          <div className="land-hero-text">
            <div className="eyebrow">{l.eyebrow}</div>
            <h1 className="land-h1">{l.heroTitle}</h1>
            <p className="lead">{l.heroSubtitle}</p>
            <div className="pub-cta land-cta">
              {isLoggedIn
                ? <Link to="/app" className="btn btn-primary">{lang === 'tr' ? 'Uygulamaya Git' : 'Go to App'}</Link>
                : <Link to="/demo" className="btn btn-primary">{t.cta.primary}</Link>
              }
              <Link to="/features" className="btn btn-secondary">{t.cta.secondary}</Link>
            </div>
          </div>
          <aside className="land-preview" aria-label={l.heroSim.panelAriaLabel}>
            <div className="land-preview-head">
              <span className="land-preview-title">{l.heroSim.panelHeading}</span>
              <span className="badge accent">{l.heroSim.panelBadge}</span>
            </div>
            <div className="land-preview-fields">
              <div className="land-field"><span className="land-field-lbl">{l.heroSim.panelCurrent}</span><span className="land-field-val">9.2 kA</span></div>
              <div className="land-field"><span className="land-field-lbl">{l.heroSim.panelTime}</span><span className="land-field-val">14 cyc</span></div>
              <div className="land-field"><span className="land-field-lbl">{l.heroSim.panelForce}</span><span className="land-field-val">3.5 kN</span></div>
              <div className="land-field"><span className="land-field-lbl">{l.heroSim.panelTip}</span><span className="land-field-val">16 mm</span></div>
            </div>
            <div className="land-preview-tags">
              <span className="ctx-chip">{l.heroSim.panelTraceLabel}: <strong>{l.heroSim.panelTraceValue}</strong></span>
              <span className="ctx-chip accent">{l.heroSim.panelStateLabel}: <strong>{l.heroSim.panelStateValue}</strong></span>
            </div>
            <div className="land-preview-note">{l.heroSim.exampleLabel}</div>
          </aside>
        </div>
      </header>

      <main className="pub-main">

        {/* ── Quality value proposition ────────────────────────── */}
        <section className="pub-section land-quality-section" aria-labelledby="quality-title">
          <h2 id="quality-title" className="pub-h2">{l.qualityTitle}</h2>
          <p className="pub-sub">{l.qualitySub}</p>
          <ul className="land-quality-grid">
            {l.qualityItems.map((item) => (
              <li key={item} className="land-quality-item">
                <span className="land-quality-icon" aria-hidden="true">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* ── Module overview ───────────────────────────────────── */}
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

        {/* ── Engineering visualizations preview ───────────────── */}
        <section className="pub-section" aria-labelledby="viz-preview-title">
          <WeldVisualizationPanel v={t.features.viz} />
        </section>

        {/* ── Industry use cases ────────────────────────────────── */}
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

        {/* ── Packages preview ──────────────────────────────────── */}
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

        {/* ── How It Works teaser ───────────────────────────────── */}
        <section className="pub-section land-hiw-teaser" aria-labelledby="hiw-teaser-title">
          <div className="land-hiw-inner">
            <div>
              <div className="eyebrow">{t.howItWorks.eyebrow}</div>
              <h2 id="hiw-teaser-title" className="pub-h2">{t.howItWorks.heroTitle}</h2>
              <p className="pub-sub">{t.howItWorks.heroSubtitle}</p>
              <Link to="/how-it-works" className="btn btn-secondary">{lang === 'tr' ? 'Akışı Gör' : 'View Flow'}</Link>
            </div>
            <ol className="land-steps-mini">
              {t.steps.slice(0, 3).map((s) => (
                <li key={s.no} className="land-step-mini">
                  <span className="land-step-no">{s.no}</span>
                  <span className="land-step-title">{s.title}</span>
                </li>
              ))}
              <li className="land-step-mini land-step-more">
                <span className="land-step-no">…</span>
                <Link to="/how-it-works" style={{ color: 'var(--accent)', fontSize: 'var(--fs-body)', textDecoration: 'none' }}>
                  {lang === 'tr' ? '+ 3 adım daha' : '+ 3 more steps'}
                </Link>
              </li>
            </ol>
          </div>
        </section>

        {/* ── Trust note ────────────────────────────────────────── */}
        <aside className="pub-trust" role="note">
          <span className="pub-icon" aria-hidden="true">i</span>
          <span>
            <b>{t.trustNote.bold}</b>{t.trustNote.rest}
          </span>
        </aside>

        {/* ── Contact section ───────────────────────────────────── */}
        <section id="contact" className="pub-section land-contact-section" aria-labelledby="contact-title">
          <h2 id="contact-title" className="pub-h2">{l.contactTitle}</h2>
          <p className="pub-sub">{l.contactSub}</p>
          <div className="land-contact-grid">
            <article className="land-contact-card">
              <div className="land-contact-avatar" aria-hidden="true">İÇ</div>
              <div className="land-contact-info">
                <strong className="land-contact-name">{c.person1.name}</strong>
                <span className="land-contact-role">{c.person1.role}</span>
                <a href="mailto:cekic.ilhan@gmail.com" className="land-contact-link">
                  <span className="land-contact-label">{c.emailLabel}:</span> cekic.ilhan@gmail.com
                </a>
                <a href="tel:+905495967940" className="land-contact-link">
                  <span className="land-contact-label">{c.phoneLabel}:</span> +90 549 596 79 40
                </a>
                <a href="https://www.linkedin.com/in/ilhan-cekic-212b4a4a/" target="_blank" rel="noopener noreferrer" className="land-contact-link">
                  <span className="land-contact-label">{c.linkedinLabel}:</span> linkedin.com/in/ilhan-cekic-212b4a4a
                </a>
              </div>
            </article>
            <article className="land-contact-card">
              <div className="land-contact-avatar" aria-hidden="true">KT</div>
              <div className="land-contact-info">
                <strong className="land-contact-name">{c.person2.name}</strong>
                <span className="land-contact-role">{c.person2.role}</span>
                <a href="mailto:koray.tokol@outlook.com" className="land-contact-link">
                  <span className="land-contact-label">{c.emailLabel}:</span> koray.tokol@outlook.com
                </a>
                <a href="tel:+905414421934" className="land-contact-link">
                  <span className="land-contact-label">{c.phoneLabel}:</span> +90 541 442 19 34
                </a>
                <a href="https://www.linkedin.com/in/koray-tokol/" target="_blank" rel="noopener noreferrer" className="land-contact-link">
                  <span className="land-contact-label">{c.linkedinLabel}:</span> linkedin.com/in/koray-tokol
                </a>
              </div>
            </article>
          </div>
          <p className="land-contact-location">
            <span className="land-contact-label">{l.locationLabel}:</span> {l.location}
          </p>
          <p className="land-contact-approval-note" role="note">{l.contactApprovalNote}</p>
        </section>

        {/* ── Demo CTA ──────────────────────────────────────────── */}
        <section className="pub-section land-demo-cta" aria-labelledby="demo-cta-title">
          <h2 id="demo-cta-title" className="pub-h2">{t.cta.primary}</h2>
          <p className="pub-sub">
            {lang === 'tr'
              ? 'SpotWeldPro AI\'ı kendi üretim ortamınızda deneyin.'
              : 'Try SpotWeldPro AI in your own production environment.'}
          </p>
          <div className="pub-cta">
            {isLoggedIn
              ? <Link to="/app" className="btn btn-primary">{lang === 'tr' ? 'Uygulamaya Git' : 'Go to App'}</Link>
              : <Link to="/demo" className="btn btn-primary">{t.cta.primary}</Link>
            }
            <Link to="/features" className="btn btn-secondary">{t.cta.secondary}</Link>
          </div>
        </section>

      </main>
    </PublicLayout>
  )
}
