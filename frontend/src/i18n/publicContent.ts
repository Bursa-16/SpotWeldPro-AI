/**
 * PUBLIC-01B: Bilingual public content.
 * Architecture: one codebase · one engineering truth · two presentation languages (TR + EN).
 *
 * No fabricated data: no prices, quotas, SLA terms, customer names, reviews,
 * logos, case-study results, addresses, certifications, or team identities.
 * Tier names (Starter / Professional / Enterprise) are structural labels only.
 * Commercial action: "Demo Talep Et / Request Demo" → /demo.
 */
export type Lang = 'tr' | 'en'

export interface NavItem {
  to: string
  label: string
}

export interface Module {
  slug: string
  code: string
  name: string
  text: string
}

export interface Industry {
  name: string
  use: string
  need: string
  modules: string
}

export interface Tier {
  name: string
  tagline: string
  points: string[]
}

export interface Step {
  no: string
  title: string
  input: string
  system: string
  output: string
  next: string
}

export interface TrustNote {
  bold: string
  rest: string
}

export interface LangContent {
  brand: string
  brandMark: string
  nav: NavItem[]
  footer: string
  cta: {
    primary: string
    secondary: string
    tertiary: string
  }
  trustNote: TrustNote

  // Shared data arrays (consumed by multiple pages)
  modules: Module[]
  industries: Industry[]
  tiers: Tier[]
  steps: Step[]

  // Landing page strings
  landing: {
    eyebrow: string
    heroTitle: string
    heroSubtitle: string
    // Hero engineering simulation labels (PUBLIC-VISUAL-01, presentational only)
    heroSim: {
      exampleLabel: string
      currentLabel: string
      timeLabel: string
      forceLabel: string
      nuggetLabel: string
      processWindowLabel: string
      insufficientLabel: string
      safeLabel: string
      expulsionLabel: string
      upperElectrode: string
      lowerElectrode: string
      completeLabel: string
      currentValue: string
      timeValue: string
      forceValue: string
      nuggetValue: string
    }
    modulesTitle: string
    modulesSub: string
    moduleDetailBtn: string
    industriesTitle: string
    industriesSub: string
    industriesNeedLabel: string
    industriesModulesLabel: string
    packagesTitle: string
    packagesSub: string
    packagesCompareBtn: string
  }

  // Features page strings
  features: {
    eyebrow: string
    heroTitle: string
    heroSubtitle: string
    overviewTitle: string
    overviewSub: string
    flowBtn: string
    demoBtn: string
  }

  // How It Works page strings
  howItWorks: {
    eyebrow: string
    heroTitle: string
    heroSubtitle: string
    stepsTitle: string
    stepsSub: string
    inputLabel: string
    systemLabel: string
    outputLabel: string
    nextLabel: string
  }

  // Packages page strings
  packages: {
    eyebrow: string
    heroTitle: string
    heroSubtitle: string
    compareTitle: string
    compareSub: string
    ctaTitle: string
    demoBtn: string
    exploreBtn: string
  }

  // Demo page strings
  demo: {
    eyebrow: string
    heroTitle: string
    heroSubtitle: string
    formTitle: string
    formSub: string
    nameLabel: string
    namePlaceholder: string
    emailLabel: string
    emailPlaceholder: string
    companyLabel: string
    companyPlaceholder: string
    submitBtn: string
    ackHeroTitle: string
    ackHeroSubtitle: string
    ackTitle: string
    ackConfirm: string
    ackMessage: string
    exploreBtn: string
    howBtn: string
  }

  // Login page strings
  login: {
    ariaLabel: string
    note: string
    usernameLabel: string
    passwordLabel: string
    submitBusy: string
    submitIdle: string
    errorNetwork: string
    errorCredentials: string
  }
}

export const PUBLIC_CONTENT: Record<Lang, LangContent> = {
  // ─────────────────────────────────────────────────────────────
  // TURKISH
  // ─────────────────────────────────────────────────────────────
  tr: {
    brand: 'SpotWeldPro AI',
    brandMark: 'SW',
    nav: [
      { to: '/', label: 'Ana Sayfa' },
      { to: '/features', label: 'Özellikler' },
      { to: '/how-it-works', label: 'Nasıl Kullanılır' },
      { to: '/packages', label: 'Paketler' },
      { to: '/demo', label: 'Demo' },
    ],
    footer: 'SpotWeldPro AI',
    cta: {
      primary: 'Demo Talep Et',
      secondary: 'Özellikleri İncele',
      tertiary: 'Giriş Yap',
    },
    trustNote: {
      bold: 'AI açıklama ve mühendislik bağlamı sağlar;',
      rest: ' nihai karar deterministik mühendislik kurallarına dayanır.',
    },

    modules: [
      {
        slug: 'command-center',
        code: 'CC',
        name: 'Komuta Merkezi',
        text: 'Tüm hat genelinde kaynak kalitesi, makine duruşu ve risk özetini tek ekranda izleyin.',
      },
      {
        slug: 'weld-quality',
        code: 'WQ',
        name: 'Kaynak Kalite Analizi',
        text: 'Nugget çapı, minimum kabul sınırı ve fışkırma (expulsion) riskine göre kaynağı değerlendirin.',
      },
      {
        slug: 'weld-lobe',
        code: 'WL',
        name: 'Kaynak Lobu Laboratuvarı',
        text: 'Proses penceresini (weld lobe) görselleştirin; akım–süre–kuvvet bölgesini inceleyin.',
      },
      {
        slug: 'failure-analysis',
        code: 'FA',
        name: 'Hata Analizi',
        text: 'Olası hata modlarını ve birincil katkı faktörlerini risk önceliyle sıralayın.',
      },
      {
        slug: 'projects',
        code: 'PW',
        name: 'Projeler ve Kaynak Noktaları',
        text: 'Projeleri, kaynak noktalarını ve parça–istasyon–robot bağlamını yönetin.',
      },
      {
        slug: 'traceability',
        code: 'TR',
        name: 'İzlenebilirlik / Geçmiş',
        text: 'Analiz geçmişini, karar gerekçelerini ve mühendislik kuralı referanslarını koruyun.',
      },
      {
        slug: 'ai-explanation',
        code: 'AI',
        name: 'AI Açıklama',
        text: 'AI, karmaşık sonuçları mühendislik bağlamıyla açıklar; karar kuralları deterministiktir.',
      },
    ],

    industries: [
      {
        name: 'Otomotiv',
        use: 'Yapısal gövde ve şase bağlantılarında yüksek adetli nokta kaynağı.',
        need: 'Tutarlı nugget kalitesi ve parça bazlı izlenebilirlik.',
        modules: 'Weld Quality Analysis · Traceability',
      },
      {
        name: 'Beyaz Eşya',
        use: 'İnce saç panellerin seri kaynağında döngü süresi kontrolü.',
        need: 'Dar proses penceresinde hızlı parametre doğrulaması.',
        modules: 'Weld Lobe Lab',
      },
      {
        name: 'Savunma',
        use: 'Yüksek kritiklikteki bağlantılarda tam doğrulanmış parametreler.',
        need: 'Kural tabanlı doğrulama ve eksiksiz denetim izi.',
        modules: 'Traceability · Projects & Weld Points',
      },
      {
        name: 'Raylı Sistemler',
        use: 'Araç gövdesi ve alt yapı birleşimlerinde uzun süreli dayanım.',
        need: 'Minimum nugget kanıtı ve partide raporlanabilirlik.',
        modules: 'Command Center · Failure Analysis',
      },
      {
        name: 'Makine İmalatı',
        use: 'Karmaşık parça kombinasyonlarında kaynak penceresinin yeniden kurulması.',
        need: 'Yeni malzeme girişlerinde proses penceresinin haritalanması.',
        modules: 'Weld Lobe Lab',
      },
      {
        name: 'Sac Metal Üretimi',
        use: 'Farklı kalınlık ve kaplama kombinasyonlarında tutarlı kalite.',
        need: 'Malzeme yığınına göre parametre hassasiyeti.',
        modules: 'Weld Quality Analysis · Projects',
      },
    ],

    tiers: [
      {
        name: 'Starter',
        tagline: 'Tek hat, temel değerlendirme.',
        points: ['Weld Quality Analysis', 'Proses penceresi özeti', 'Temel raporlama'],
      },
      {
        name: 'Professional',
        tagline: 'Mühendislik ekibi için tam çalışma alanı.',
        points: ['Weld Lobe Lab', 'Failure Analysis', 'Proje & kaynak noktası yönetimi'],
      },
      {
        name: 'Enterprise',
        tagline: 'Çok tesisli, tam izlenebilirlik.',
        points: ['Tam denetim izi', 'Çok tesis yönetimi', 'Kurumsal entegrasyonlar'],
      },
    ],

    steps: [
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
        system: 'Operating window incelemesi ve parametre doğrulama.',
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
    ],

    landing: {
      eyebrow: 'SpotWeldPro AI · Engineering Workstation',
      heroTitle: 'Nokta Kaynak Parametre Analizi',
      heroSubtitle:
        'Deterministik mühendislik kuralları ile kaynak kalitesini doğrulayın;'
        + ' deney tasarımı ve hata analizi ile prosesi yönetin.',
      heroSim: {
        exampleLabel: 'Örnek Proses',
        currentLabel: 'Kaynak Akımı',
        timeLabel: 'Kaynak Süresi',
        forceLabel: 'Elektrot Kuvveti',
        nuggetLabel: 'Çekirdek Çapı',
        processWindowLabel: 'Proses Penceresi',
        insufficientLabel: 'Yetersiz',
        safeLabel: 'Güvenli Pencere',
        expulsionLabel: 'Fışkırma Riski',
        upperElectrode: 'Üst Elektrot',
        lowerElectrode: 'Alt Elektrot',
        completeLabel: 'Örnek Tamamlandı',
        currentValue: '9.2 kA',
        timeValue: '14 cyc',
        forceValue: '3.5 kN',
        nuggetValue: '5.4 mm',
      },
      modulesTitle: 'Modüller',
      modulesSub: 'Bir modülü incelemek için Özellikler sayfasındaki detayı görüntüleyin.',
      moduleDetailBtn: 'Detayı Gör',
      industriesTitle: 'Sektör Kullanım Senaryoları',
      industriesSub:
        'Kendi üretim bağlamınızı seçin; tipik kullanım, ihtiyaç ve ilgili modülleri görün.',
      industriesNeedLabel: 'İhtiyaç:',
      industriesModulesLabel: 'Modüller:',
      packagesTitle: 'Paketler',
      packagesSub: 'Detaylı karşılaştırma için Paketler sayfasını açın.',
      packagesCompareBtn: 'Paket Karşılaştırması',
    },

    features: {
      eyebrow: 'Özellikler',
      heroTitle: 'SpotWeldPro AI Modülleri',
      heroSubtitle:
        'Kaynak kalitesi, proses penceresi, optimizasyon ve izlenebilirlik'
        + ' için deterministik mühendislik kuralları ve AI destekli açıklama.',
      overviewTitle: 'Modüllere Genel Bakış',
      overviewSub:
        'Her modül, kaynağın fiziksel modeline dayalı hesaplama yapar.'
        + ' AI yalnızca açıklama ve özet sağlar;'
        + ' nihai karar her zaman deterministik kurallara dayanır.',
      flowBtn: 'Akışı Gör',
      demoBtn: 'Demo Talep Et',
    },

    howItWorks: {
      eyebrow: 'Mühendislik Akışı',
      heroTitle: 'Bağlamdan İzlenebilir Sonuça',
      heroSubtitle:
        'OEM / Tier-1 üretim, kalite ve mühendislik ekipleri için altı adımlık'
        + ' mühendislik akışı: bağlam, malzeme, parametre, analiz, optimizasyon, izlenebilirlik.',
      stepsTitle: 'Altı Adımlık Mühendislik Süreci',
      stepsSub:
        'Her adım, kullanıcı girişini alır, mühendislik kuralları ile değerlendirir'
        + ' ve izlenebilir bir çıktı üretir.',
      inputLabel: 'Giriş',
      systemLabel: 'Sistem Değerlendirmesi',
      outputLabel: 'Mühendislik Çıktısı',
      nextLabel: 'Sonraki →',
    },

    packages: {
      eyebrow: 'Paketler',
      heroTitle: 'Üretim İhtiyacınıza Uygun Paketi Seçin',
      heroSubtitle:
        "Starter'dan Enterprise'a kadar ihtiyacınıza uygun pakete başlayın."
        + ' Tüm paketler temel mühendislik kurallarını içerir.',
      compareTitle: 'Paket Karşılaştırması',
      compareSub: 'Detaylı bilgi için satış ekibimizle iletişime geçin.',
      ctaTitle: 'Hemen Başlayın',
      demoBtn: 'Demo Talep Et',
      exploreBtn: 'Özellikleri İncele',
    },

    demo: {
      eyebrow: 'Demo',
      heroTitle: 'Demo Talep Edin',
      heroSubtitle:
        "SpotWeldPro AI'ı kendi üretim ortamınızda denemek için formu"
        + ' doldurun; ekibimiz en kısa sürede sizinle iletişime geçsin.',
      formTitle: 'Demo Talebi',
      formSub: 'Aşağıdaki formu doldurarak demo talebinizi bize iletin.',
      nameLabel: 'Ad Soyad',
      namePlaceholder: 'Adınız Soyadınız',
      emailLabel: 'E-posta',
      emailPlaceholder: 'sirket@example.com',
      companyLabel: 'Şirket',
      companyPlaceholder: 'Şirket Adı',
      submitBtn: 'Talebi Gönder',
      ackHeroTitle: 'Demo Talep Edin',
      ackHeroSubtitle:
        "SpotWeldPro AI'ı kendi üretim ortamınızda denemek için talebinizi ilettiniz.",
      ackTitle: 'Talebiniz Alındı',
      ackConfirm: '✓ Alındı',
      ackMessage:
        'Demo talebiniz başarıyla alındı. Ekibimiz en kısa sürede sizinle iletişime geçecektir.',
      exploreBtn: 'Özellikleri İncele',
      howBtn: 'Nasıl Kullanılır',
    },

    login: {
      ariaLabel: 'Kurumsal giriş',
      note: 'Kurumsal giriş — resistance spot welding mühendislik zekası',
      usernameLabel: 'Kullanıcı Adı',
      passwordLabel: 'Şifre',
      submitBusy: 'Giriş yapılıyor…',
      submitIdle: 'Giriş Yap',
      errorNetwork:
        'Backend bağlantısı yok. Mühendislik verisi yüklenemedi; API servisini doğrulayın ve tekrar deneyin.',
      errorCredentials: 'Kullanıcı adı veya şifre hatalı.',
    },
  },

  // ─────────────────────────────────────────────────────────────
  // ENGLISH
  // ─────────────────────────────────────────────────────────────
  en: {
    brand: 'SpotWeldPro AI',
    brandMark: 'SW',
    nav: [
      { to: '/', label: 'Home' },
      { to: '/features', label: 'Features' },
      { to: '/how-it-works', label: 'How It Works' },
      { to: '/packages', label: 'Packages' },
      { to: '/demo', label: 'Demo' },
    ],
    footer: 'SpotWeldPro AI',
    cta: {
      primary: 'Request Demo',
      secondary: 'Explore Features',
      tertiary: 'Sign In',
    },
    trustNote: {
      bold: 'AI provides explanation and engineering context;',
      rest: ' the final decision is always based on deterministic engineering rules.',
    },

    modules: [
      {
        slug: 'command-center',
        code: 'CC',
        name: 'Command Center',
        text: 'Monitor weld quality, machine downtime, and risk summary across the entire line on one screen.',
      },
      {
        slug: 'weld-quality',
        code: 'WQ',
        name: 'Weld Quality Analysis',
        text: 'Evaluate welds against nugget diameter, minimum acceptance threshold, and expulsion risk.',
      },
      {
        slug: 'weld-lobe',
        code: 'WL',
        name: 'Weld Lobe Lab',
        text: 'Visualize the process window (weld lobe); examine the current–time–force region.',
      },
      {
        slug: 'failure-analysis',
        code: 'FA',
        name: 'Failure Analysis',
        text: 'Rank probable failure modes and primary contributing factors by risk priority.',
      },
      {
        slug: 'projects',
        code: 'PW',
        name: 'Projects & Weld Points',
        text: 'Manage projects, weld points, and part–station–robot context.',
      },
      {
        slug: 'traceability',
        code: 'TR',
        name: 'Traceability / History',
        text: 'Preserve analysis history, decision rationale, and engineering rule references.',
      },
      {
        slug: 'ai-explanation',
        code: 'AI',
        name: 'AI Explanation',
        text: 'AI explains complex results with engineering context; decision rules are deterministic.',
      },
    ],

    industries: [
      {
        name: 'Automotive',
        use: 'High-volume spot welding on structural body and chassis joints.',
        need: 'Consistent nugget quality and part-level traceability.',
        modules: 'Weld Quality Analysis · Traceability',
      },
      {
        name: 'White Goods',
        use: 'Cycle time control in high-speed welding of thin sheet panels.',
        need: 'Fast parameter validation within a narrow process window.',
        modules: 'Weld Lobe Lab',
      },
      {
        name: 'Defense',
        use: 'Fully verified parameters on high-criticality joints.',
        need: 'Rule-based validation and complete audit trail.',
        modules: 'Traceability · Projects & Weld Points',
      },
      {
        name: 'Rail Systems',
        use: 'Long-term durability on body and underframe joints.',
        need: 'Minimum nugget evidence and batch-level reportability.',
        modules: 'Command Center · Failure Analysis',
      },
      {
        name: 'Machine Manufacturing',
        use: 'Rebuilding the weld window for complex part combinations.',
        need: 'Mapping the process window for new material introductions.',
        modules: 'Weld Lobe Lab',
      },
      {
        name: 'Sheet Metal Production',
        use: 'Consistent quality across varying thickness and coating combinations.',
        need: 'Parameter sensitivity per material stack.',
        modules: 'Weld Quality Analysis · Projects',
      },
    ],

    tiers: [
      {
        name: 'Starter',
        tagline: 'Single line, essential assessment.',
        points: ['Weld Quality Analysis', 'Process window summary', 'Basic reporting'],
      },
      {
        name: 'Professional',
        tagline: 'Full workspace for engineering teams.',
        points: ['Weld Lobe Lab', 'Failure Analysis', 'Project & weld point management'],
      },
      {
        name: 'Enterprise',
        tagline: 'Multi-facility, full traceability.',
        points: ['Full audit trail', 'Multi-facility management', 'Enterprise integrations'],
      },
    ],

    steps: [
      {
        no: '01',
        title: 'Project / Application Context',
        input: 'Project, line/station and weld point selection.',
        system: 'Context is validated; relevant engineering rules are matched.',
        output: 'Weld point context ready for analysis.',
        next: 'Material and sheet information',
      },
      {
        no: '02',
        title: 'Material and Sheet Information',
        input: 'Sheet thicknesses, material class, stack structure.',
        system: 'Stack compatibility and thickness limits are checked.',
        output: 'Validated material/stack context.',
        next: 'Welding parameters',
      },
      {
        no: '03',
        title: 'Welding Parameters',
        input: 'Welding current (kA), weld time, electrode force (kN).',
        system: 'Parameters are evaluated against engineering limits.',
        output: 'Parameter status: within / outside limits.',
        next: 'Analysis and engineering checks',
      },
      {
        no: '04',
        title: 'Analysis and Engineering Checks',
        input: 'Validated context + parameter set.',
        system: 'Quality assessment, process window position, risk check.',
        output: 'Weld quality result and engineering interpretation.',
        next: 'Process window / optimization',
      },
      {
        no: '05',
        title: 'Process Window / Optimization',
        input: 'Analysis result + targets.',
        system: 'Operating window review, DOE/optimization proposal.',
        output: 'Current vs recommended delta and proposed parameter.',
        next: 'Result, validation and traceability',
      },
      {
        no: '06',
        title: 'Result, Validation and Traceability',
        input: 'Proposed parameter + engineering approval.',
        system: 'Result record: analysis ID, timestamp, parameter set, evidence reference.',
        output: 'Traceable engineering result and report.',
        next: 'New analysis or validation flow',
      },
    ],

    landing: {
      eyebrow: 'SpotWeldPro AI · Engineering Workstation',
      heroTitle: 'Spot Welding Parameter Analysis',
      heroSubtitle:
        'Verify weld quality with deterministic engineering rules;'
        + ' manage the process with design of experiments and failure analysis.',
      heroSim: {
        exampleLabel: 'Example Process',
        currentLabel: 'Welding Current',
        timeLabel: 'Weld Time',
        forceLabel: 'Electrode Force',
        nuggetLabel: 'Nugget Diameter',
        processWindowLabel: 'Process Window',
        insufficientLabel: 'Insufficient',
        safeLabel: 'Safe Window',
        expulsionLabel: 'Expulsion Risk',
        upperElectrode: 'Upper Electrode',
        lowerElectrode: 'Lower Electrode',
        completeLabel: 'Example Complete',
        currentValue: '9.2 kA',
        timeValue: '14 cyc',
        forceValue: '3.5 kN',
        nuggetValue: '5.4 mm',
      },
      modulesTitle: 'Modules',
      modulesSub: 'View the details on the Features page to explore a module.',
      moduleDetailBtn: 'View Details',
      industriesTitle: 'Industry Use Cases',
      industriesSub:
        'Select your manufacturing context; see typical usage, requirements, and relevant modules.',
      industriesNeedLabel: 'Need:',
      industriesModulesLabel: 'Modules:',
      packagesTitle: 'Packages',
      packagesSub: 'Open the Packages page for a detailed comparison.',
      packagesCompareBtn: 'Compare Packages',
    },

    features: {
      eyebrow: 'Features',
      heroTitle: 'SpotWeldPro AI Modules',
      heroSubtitle:
        'Deterministic engineering rules and AI-assisted explanation for weld quality,'
        + ' process window, optimization, and traceability.',
      overviewTitle: 'Module Overview',
      overviewSub:
        'Each module performs calculations based on the physical model of the weld.'
        + ' AI provides explanation and summary only;'
        + ' the final decision is always based on deterministic rules.',
      flowBtn: 'View Flow',
      demoBtn: 'Request Demo',
    },

    howItWorks: {
      eyebrow: 'Engineering Flow',
      heroTitle: 'From Context to Traceable Result',
      heroSubtitle:
        'Six-step engineering flow for OEM / Tier-1 production, quality, and engineering teams:'
        + ' context, material, parameters, analysis, optimization, traceability.',
      stepsTitle: 'Six-Step Engineering Process',
      stepsSub:
        'Each step takes user input, evaluates it against engineering rules,'
        + ' and produces a traceable output.',
      inputLabel: 'Input',
      systemLabel: 'System Evaluation',
      outputLabel: 'Engineering Output',
      nextLabel: 'Next →',
    },

    packages: {
      eyebrow: 'Packages',
      heroTitle: 'Choose the Package That Fits Your Production Needs',
      heroSubtitle:
        'Start with the package that fits your needs, from Starter to Enterprise.'
        + ' All packages include core engineering rules.',
      compareTitle: 'Package Comparison',
      compareSub: 'Contact our sales team for detailed information.',
      ctaTitle: 'Get Started',
      demoBtn: 'Request Demo',
      exploreBtn: 'Explore Features',
    },

    demo: {
      eyebrow: 'Demo',
      heroTitle: 'Request a Demo',
      heroSubtitle:
        'Fill in the form to try SpotWeldPro AI in your own production environment;'
        + ' our team will get in touch as soon as possible.',
      formTitle: 'Demo Request',
      formSub: 'Fill in the form below to submit your demo request.',
      nameLabel: 'Full Name',
      namePlaceholder: 'Your Full Name',
      emailLabel: 'Email',
      emailPlaceholder: 'company@example.com',
      companyLabel: 'Company',
      companyPlaceholder: 'Company Name',
      submitBtn: 'Submit Request',
      ackHeroTitle: 'Request a Demo',
      ackHeroSubtitle:
        'Your request to try SpotWeldPro AI in your own production environment has been submitted.',
      ackTitle: 'Request Received',
      ackConfirm: '✓ Received',
      ackMessage:
        'Your demo request has been successfully received. Our team will contact you as soon as possible.',
      exploreBtn: 'Explore Features',
      howBtn: 'How It Works',
    },

    login: {
      ariaLabel: 'Sign in',
      note: 'Enterprise login — engineering intelligence for resistance spot welding',
      usernameLabel: 'Username',
      passwordLabel: 'Password',
      submitBusy: 'Signing in…',
      submitIdle: 'Sign In',
      errorNetwork:
        'No backend connection. Engineering data could not be loaded; verify the API service and retry.',
      errorCredentials: 'Incorrect username or password.',
    },
  },
}
