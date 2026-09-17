import { Link } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Ana Sayfa' },
  { to: '/features', label: 'Özellikler' },
  { to: '/how-it-works', label: 'Nasıl Kullanılır' },
  { to: '/packages', label: 'Paketler' },
  { to: '/demo', label: 'Demo' },
]

const STEPS = [
  {
    no: '01',
    title: 'Proje / Uygulama Bağlamı',
    input: 'Proje, hat/istasyon ve kaynak noktası seçimi.',
    system: 'Bağlam doğrulanır; ilgili mühendislik kuralları eşleştirilir.',
    output: 'Analize hazır kaynak noktası bağlamı.',
    next: 'Malzeme ve sac bilgileri',
  },
  {
    no: '02',
    title: 'Malzeme ve Sac Bilgileri',
    input: 'Sac kalınlıkları, malzeme sınıfı, yığın (stack) yapısı.',
    system: 'Yığın uyumluluğu ve kalınlık limitleri kontrol edilir.',
    output: 'Doğrulanmış malzeme/yığın bağlamı.',
    next: 'Kaynak parametreleri',
  },
  {
    no: '03',
    title: 'Kaynak Parametreleri',
    input: 'Welding current (kA), weld time, electrode force (kN).',
    system: 'Parametreler mühendislik limitlerine karşı değerlendirilir.',
    output: 'Parametre durumu: limit içi / dışı.',
    next: 'Analiz ve mühendislik kontrolleri',
  },
  {
    no: '04',
    title: 'Analiz ve Mühendislik Kontrolleri',
    input: 'Doğrulanmış bağlam + parametre seti.',
    system: 'Kalite değerlendirmesi, proses penceresi konumu, risk kontrolü.',
    output: 'Kaynak kalitesi sonucu ve mühendislik yorumu.',
    next: 'Proses penceresi / optimizasyon',
  },
  {
    no: '05',
    title: 'Proses Penceresi / Optimizasyon',
    input: 'Analiz sonucu + hedefler.',
    system: 'Operating window incelemesi, DOE/optimizasyon önerisi.',
    output: 'Current vs recommended delta ve önerilen parametre.',
    next: 'Sonuç, doğrulama ve izlenebilirlik',
  },
  {
    no: '06',
    title: 'Sonuç, Doğrulama ve İzlenebilirlik',
    input: 'Önerilen parametre + mühendislik onayı.',
    system: 'Sonuç kaydı: analiz ID, zaman damgası, parametre seti, kanıt referansı.',
    output: 'İzlenebilir mühendislik sonucu ve rapor.',
    next: 'Yeni analiz veya doğrulama akışı',
  },
]

export function HowItWorksPage() {
  return (
    <div>
      <nav className="pub-topnav" aria-label="Ana gezinme">
        <Link className="pub-brand" to="/">
          <span className="brand-mark" aria-hidden="true">SW</span>
          <span>Spot&nbsp;Welding&nbsp;Parametre&nbsp;Analysis</span>
        </Link>
        <div className="pub-nav-links">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to} className={n.to === '/how-it-works' ? 'active' : ''}>
              {n.label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="pub-main">
        <section className="pub-hero" aria-labelledby="hiw-hero">
          <span className="eyebrow">Mühendislik Akışı</span>
          <h1 id="hiw-hero">Bağlamdan İzlenebilir Sonuça</h1>
          <p className="lead">
            OEM / Tier-1 üretim, kalite ve mühendislik ekipleri için altı adımlık
            mühendislik akışı: bağlam, malzeme, parametre, analiz, optimizasyon, izlenebilirlik.
          </p>
        </section>

        <section className="pub-section" aria-labelledby="steps-title">
          <h2 id="steps-title" className="pub-h2">Altı Adımlık Mühendislik Süreci</h2>
          <p className="pub-sub">
            Her adım, kullanıcı girişini alır, mühendislik kuralları ile değerlendirir
            ve izlenebilir bir çıktı üretir.
          </p>
          <div className="pub-steps">
            {STEPS.map((s) => (
              <article className="pub-step" key={s.no}>
                <div className="pub-step-no">{s.no}</div>
                <div className="pub-step-body">
                  <h3>{s.title}</h3>
                  <div className="pub-step-row">
                    <span className="pub-step-label">Giriş</span>
                    <span className="pub-step-val">{s.input}</span>
                  </div>
                  <div className="pub-step-row">
                    <span className="pub-step-label">Sistem Değerlendirmesi</span>
                    <span className="pub-step-val">{s.system}</span>
                  </div>
                  <div className="pub-step-row">
                    <span className="pub-step-label">Mühendislik Çıktısı</span>
                    <span className="pub-step-val">{s.output}</span>
                  </div>
                  <div className="pub-step-next">Sonraki → {s.next}</div>
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
