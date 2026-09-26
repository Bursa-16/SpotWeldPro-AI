import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

export function DemoPage() {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang]
  const d = t.demo
  const [submitted, setSubmitted] = useState(false)

  if (submitted) {
    return (
      <PublicLayout>
        <main className="pub-main">
          <section className="pub-hero" aria-labelledby="demo-ty-hero">
            <span className="eyebrow">{d.eyebrow}</span>
            <h1 id="demo-ty-hero">{d.ackHeroTitle}</h1>
            <p className="lead">{d.ackHeroSubtitle}</p>
          </section>
          <section className="pub-section" aria-labelledby="ack-title">
            <h2 id="ack-title" className="pub-h2">{d.ackTitle}</h2>
            <div className="pub-ack">
              <span className="pub-ack-title">{d.ackConfirm}</span>
              <span>{d.ackMessage}</span>
            </div>
            <div className="pub-cta">
              <Link to="/features" className="btn btn-secondary btn-sm">
                {d.exploreBtn}
              </Link>
              <Link to="/how-it-works" className="btn btn-secondary btn-sm">
                {d.howBtn}
              </Link>
            </div>
          </section>
        </main>
      </PublicLayout>
    )
  }

  return (
    <PublicLayout>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="demo-hero">
          <span className="eyebrow">{d.eyebrow}</span>
          <h1 id="demo-hero">{d.heroTitle}</h1>
          <p className="lead">{d.heroSubtitle}</p>
        </section>

        <section className="pub-section" aria-labelledby="form-title">
          <h2 id="form-title" className="pub-h2">{d.formTitle}</h2>
          <p className="pub-sub">{d.formSub}</p>
          <form
            className="pub-card pub-form"
            style={{ maxWidth: '520px' }}
            onSubmit={(e) => {
              e.preventDefault()
              setSubmitted(true)
            }}
          >
            <div className="pub-form-field">
              <label htmlFor="demo-name">{d.nameLabel}</label>
              <input id="demo-name" type="text" required placeholder={d.namePlaceholder} />
            </div>
            <div className="pub-form-field">
              <label htmlFor="demo-email">{d.emailLabel}</label>
              <input id="demo-email" type="email" required placeholder={d.emailPlaceholder} />
            </div>
            <div className="pub-form-field">
              <label htmlFor="demo-company">{d.companyLabel}</label>
              <input id="demo-company" type="text" required placeholder={d.companyPlaceholder} />
            </div>
            <button type="submit" className="btn btn-primary btn-sm">{d.submitBtn}</button>
          </form>
        </section>
      </main>
    </PublicLayout>
  )
}
