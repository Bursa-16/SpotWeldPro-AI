import { PublicLayout } from '../components/PublicLayout'
import { useLang } from '../i18n/useLang'
import { PUBLIC_CONTENT } from '../i18n/publicContent'

export function HowItWorksPage() {
  const { lang } = useLang()
  const t = PUBLIC_CONTENT[lang]
  const h = t.howItWorks

  return (
    <PublicLayout>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="hiw-hero">
          <span className="eyebrow">{h.eyebrow}</span>
          <h1 id="hiw-hero">{h.heroTitle}</h1>
          <p className="lead">{h.heroSubtitle}</p>
        </section>

        <section className="pub-section" aria-labelledby="steps-title">
          <h2 id="steps-title" className="pub-h2">{h.stepsTitle}</h2>
          <p className="pub-sub">{h.stepsSub}</p>
          <div className="pub-steps">
            {t.steps.map((s) => (
              <article className="pub-step" key={s.no}>
                <div className="pub-step-no">{s.no}</div>
                <div className="pub-step-body">
                  <h3>{s.title}</h3>
                  <div className="pub-step-row">
                    <span className="pub-step-label">{h.inputLabel}</span>
                    <span className="pub-step-val">{s.input}</span>
                  </div>
                  <div className="pub-step-row">
                    <span className="pub-step-label">{h.systemLabel}</span>
                    <span className="pub-step-val">{s.system}</span>
                  </div>
                  <div className="pub-step-row">
                    <span className="pub-step-label">{h.outputLabel}</span>
                    <span className="pub-step-val">{s.output}</span>
                  </div>
                  <div className="pub-step-next">{h.nextLabel} {s.next}</div>
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
