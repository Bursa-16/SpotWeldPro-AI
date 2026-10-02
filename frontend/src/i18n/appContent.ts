/**
 * APP-I18N-01A: Authenticated app string dictionary — TR / EN.
 *
 * Rules:
 * - UI presentation text only.
 * - DO NOT include: API field names, internal IDs, engineering units,
 *   2T / 3T / 4T, kA, kN, mm, canonical backend enum values.
 * - Canonical backend values (HIGH / MEDIUM / LOW) are mapped here
 *   for display only; the internal value never changes.
 */

export type AppLanguage = 'tr' | 'en'

export interface AppContent {
  topbar: {
    signOut: string
  }
  nav: {
    groups: Record<string, string>
    items: Record<string, string>
  }
  analysisPage: {
    kicker: string
    title: string
    subtitle: string
    runAnalysis: string
    analyzing: string
    authorityChip: string
    stackChip: string
    materialChip: string
    totalThicknessChip: string
    engineeringInputs: string
    engineeringInputsMeta: string
    weldingParameters: string
    currentKa: string
    weldTime: string
    electrodeForce: string
    tipDiameter: string
    engineeringResult: string
    noResultTitle: string
    noResultHint: string
    noResultAction: string
    evaluating: string
    inputsFooter: string
    resultFooter: string
    traceabilityTitle: string
    traceabilityMeta: string
    traceabilityMaterial: string
    traceabilityStack: string
    traceabilityTotalThickness: string
    traceabilityCurrentMode: string
    traceabilitySelectedModel: string
    traceabilityCompliance: string
    traceabilityParamRevision: string
    traceabilityRuleRevision: string
    traceabilityEvalId: string
    traceabilityEvidenceSource: string
    traceabilityApprovalState: string
    traceabilityReadiness: string
    traceabilityFooter: string
    backendUnavailableTitle: string
    /** CE-04-C1: this string is fixed — do not translate the error text. */
    backendUnavailableText: string
  }
  stackEditor: {
    sectionTitle: string
    stackCountLabel: string
    layerPrefix: string
    materialFamily: string
    materialFamilyPlaceholder: string
    materialSubtype: string
    materialSubtypePlaceholder: string
    thickness: string
    coated: string
  }
  advancedPanel: {
    title: string
    squeezeCycles: string
    holdCycles: string
    coolingFlow: string
    coolingTemp: string
    dcCurrent: string
    adhesive: string
    shuntRisk: string
  }
  resultPanel: {
    empty: string
    score: string
    risk: string
    nuggetMin: string
    nuggetOpt: string
    modelPrediction: string
    margin: string
    complianceSummary: string
    complianceScore: string
    totalRules: string
    passed: string
    failed: string
    review: string
    risks: string
    actions: string
    recommendedRanges: string
    rangeParam: string
    rangeMin: string
    rangeMax: string
    rangeUnit: string
    rangeCurrent: string
    rangeStatus: string
    modelResults: string
    complianceConflicts: string
    conflictWinner: string
    conflictChallenger: string
  }
  dashboardPage: {
    kicker: string
    kickerData: string
    title: string
    subtitle: string
    loading: string
    errorTitle: string
    /** CE-04-C1: this string is fixed — do not translate the error text. */
    errorText: string
    // Card labels
    totalProjects: string
    activeProjects: string
    totalWeldPoints: string
    riskyWeldPoints: string
    pendingApprovals: string
    rejectedApprovals: string
    users: string
    auditEvents: string
    // Card sub-labels
    engineeringReview: string
    noReview: string
    awaitingDecision: string
    // Panel headers
    engineeringActivity: string
    engineeringActivityMeta: string
    systemReadiness: string
    systemReadinessMeta: string
    // Trace row labels
    projects: string
    weldPoints: string
    approvals: string
    backend: string
    auditEvents7d: string
    // Trace row connectors
    total: string
    active: string
    risky: string
    pending: string
    rejected: string
    connected: string
    // Panel footers
    activityFooter: string
    readinessFooter: string
  }
  /** Display mapping for canonical backend role codes. */
  roleLabels: Record<string, string>
  stackDefinition: {
    sectionTitle: string
    stackCountLabel: string
    layerPrefix: string
    materialFamily: string
    materialFamilyPlaceholder: string
    materialSubtype: string
    materialSubtypePlaceholder: string
    thickness: string
    coated: string
    engineeringReviewRequired: string
  }
  parameterPanel: {
    sectionTitle: string
    groupElectrical: string
    groupForce: string
    groupTime: string
    groupCooling: string
    currentKa: string
    forceKn: string
    forceDaN: string
    tipDiameter: string
    airPressure: string
    weldTime: string
    squeezeTime: string
    holdTime: string
    approachTime: string
    coolingTime: string
    coolingFlow: string
    coolingTemp: string
    dcCurrent: string
    adhesive: string
    shuntRisk: string
    unitCycle: string
    unitMs: string
    unitToggleLabel: string
    unitBasisUnresolved: string
    cycleEqMs: string
    runAnalysis: string
    analyzing: string
  }
  referenceGuidancePanel: {
    sectionTitle: string
    referenceProfile: string
    referenceBand: string
    effectiveThickness: string
    parameterRange: string
    engineeringReviewRequired: string
    outsideRangeWarning: string
    notEvaluated: string
    withinRange: string
    belowRange: string
    aboveRange: string
    unitBasisUnresolved: string
    noReferenceFound: string
    rangeParam: string
    rangeMin: string
    rangeMax: string
    rangeUnit: string
    rangeStatus: string
    guidanceInfoNote: string
  }
  /** Display mapping for canonical backend risk level values. */
  riskLabels: Record<string, string>
}

/* ── Turkish ─────────────────────────────────────────────────────────── */
const TR: AppContent = {
  topbar: {
    signOut: 'Çıkış Yap',
  },
  nav: {
    groups: {
      dash: 'SpotWeldPro AI',
      work: 'ÇALIŞMA',
      analysis: 'ANALİZ',
    },
    items: {
      dashboard: 'Gösterge Paneli',
      projects: 'Projeler ve Kaynak Noktaları',
      engineering: 'Kaynak Lobu Laboratuvarı',
      analysis: 'Kaynak Kalite Analizi',
      failure: 'Hata Analizi',
    },
  },
  analysisPage: {
    kicker: 'Üretim · Nokta Kaynak Parametre Analizi',
    title: 'Kaynak Kalite Analizi',
    subtitle: 'Kural tabanlı nokta kaynak değerlendirmesi — model desteği ile deterministik limitler',
    runAnalysis: 'Analizi Çalıştır',
    analyzing: 'Analiz ediliyor…',
    authorityChip: 'Otorite: deterministik kurallar',
    stackChip: 'Sac Paketi',
    materialChip: 'Malzeme',
    totalThicknessChip: 'Toplam kalınlık',
    engineeringInputs: 'Mühendislik Girdileri',
    engineeringInputsMeta: 'sac paketi · parametreler',
    weldingParameters: 'Kaynak Parametreleri',
    currentKa: 'Kaynak Akımı (kA)',
    weldTime: 'Kaynak Süresi (çevrim)',
    electrodeForce: 'Elektrot Kuvveti (kN)',
    tipDiameter: 'Elektrot Uç Çapı (mm)',
    engineeringResult: 'Mühendislik Sonucu',
    noResultTitle: 'Henüz analiz sonucu yok',
    noResultHint:
      'Yönetilen mühendislik sonucunu oluşturmak için analizi çalıştırın. ' +
      'İlk backend değerlendirmesinden önce boş durum beklenmektedir.',
    noResultAction: 'Sonraki adım: Mevcut parametre setiyle analizi çalıştırın.',
    evaluating: 'Yönetilen kurallar değerlendiriliyor…',
    inputsFooter:
      'Girdiler yalnızca backend deterministik kuralları tarafından değerlendirilir. ' +
      'Üst düzey malzeme Katman 1\'e göre belirlenir.',
    resultFooter: 'İzlenebilirlik: yalnızca backend deterministik çıktı.',
    traceabilityTitle: 'İzlenebilirlik',
    traceabilityMeta: 'yönetilen bağlam',
    traceabilityMaterial: 'Malzeme (Katman 1)',
    traceabilityStack: 'Sac Paketi',
    traceabilityTotalThickness: 'Toplam kalınlık',
    traceabilityCurrentMode: 'Akım modu',
    traceabilitySelectedModel: 'Seçilen model',
    traceabilityCompliance: 'Uyum durumu',
    traceabilityParamRevision: 'Parametre revizyonu',
    traceabilityRuleRevision: 'Kural revizyonu',
    traceabilityEvalId: 'Değerlendirme kimliği',
    traceabilityEvidenceSource: 'Kanıt kaynağı',
    traceabilityApprovalState: 'Onay durumu',
    traceabilityReadiness: 'Hazır olma durumu',
    traceabilityFooter:
      'Yönetilen tanımlayıcılar, kayıt/kanıt entegrasyonu tamamlandığında doldurulacaktır. ' +
      'Hiçbir değer uydurmaz.',
    backendUnavailableTitle: 'Backend bağlantısı kullanılamıyor',
    backendUnavailableText:
      'Engineering data could not be loaded. Verify the API service and retry.',
  },
  dashboardPage: {
    kicker: 'KOMUTA MERKEZİ',
    kickerData: 'Genel Bakış · Nokta Kaynak Parametre Analizi',
    title: 'Komuta Merkezi',
    subtitle: 'Üretim kalitesi ve mühendislik genel görünümü',
    loading: 'Komuta merkezi yükleniyor…',
    errorTitle: 'Backend bağlantısı kullanılamıyor',
    errorText:
      'Engineering data could not be loaded. Verify the API service and retry.',
    totalProjects: 'Toplam Proje',
    activeProjects: 'Aktif Proje',
    totalWeldPoints: 'Toplam Kaynak Noktası',
    riskyWeldPoints: 'Riskli Kaynak Noktası',
    pendingApprovals: 'Bekleyen Onay',
    rejectedApprovals: 'Reddedilen Onay',
    users: 'Kullanıcı',
    auditEvents: 'Denetim Olayı (7 g)',
    engineeringReview: 'mühendislik incelemesi gerekli',
    noReview: 'inceleme gerekmez',
    awaitingDecision: 'insan kararı bekleniyor',
    engineeringActivity: 'Mühendislik aktivitesi',
    engineeringActivityMeta: 'güncel backend durumu',
    systemReadiness: 'Sistem hazırlığı',
    systemReadinessMeta: 'bağlantı',
    projects: 'Projeler',
    weldPoints: 'Kaynak noktaları',
    approvals: 'Onaylar',
    backend: 'Backend',
    auditEvents7d: 'Denetim olayları (7 g)',
    total: 'toplam',
    active: 'aktif',
    risky: 'riskli',
    pending: 'bekleyen',
    rejected: 'reddedilen',
    connected: 'bağlı',
    activityFooter: 'Yalnızca canlı backend sayıları — örnekleme yok.',
    readinessFooter: 'Denetim destekli izlenebilirlik bağlamı.',
  },
  roleLabels: {
    SYSTEM_ADMIN:           'Sistem Yöneticisi',
    PROCESS_ENGINEER:       'Proses Mühendisi',
    QUALITY_ENGINEER:       'Kalite Mühendisi',
    MANUFACTURING_ENGINEER: 'Üretim Mühendisi',
    MAINTENANCE:            'Bakım',
    OPERATOR:               'Operatör',
    READ_ONLY:              'Salt Okunur',
    CUSTOMER:               'Müşteri',
  },
  stackEditor: {
    sectionTitle: 'Sac Paketi Konfigürasyonu',
    stackCountLabel: 'Sac Adedi',
    layerPrefix: 'Katman',
    materialFamily: 'Malzeme Ailesi',
    materialFamilyPlaceholder: 'ör. DP, IF, AHSS',
    materialSubtype: 'Malzeme Alt Tipi',
    materialSubtypePlaceholder: 'ör. DP600, DP780',
    thickness: 'Kalınlık (mm)',
    coated: 'Kaplamalı',
  },
  advancedPanel: {
    title: 'Gelişmiş Ekipman',
    squeezeCycles: 'Sıkıştırma çevrimi',
    holdCycles: 'Tutma çevrimi',
    coolingFlow: 'Soğutma debisi (L/dak)',
    coolingTemp: 'Soğutma sıcaklığı (°C)',
    dcCurrent: 'DC akım',
    adhesive: 'Yapıştırıcı bağlantı',
    shuntRisk: 'Şönt riski',
  },
  resultPanel: {
    empty: 'Analiz sonucu bekleniyor…',
    score: 'Skor',
    risk: 'Risk',
    nuggetMin: 'Nugget min (mm)',
    nuggetOpt: 'Nugget opt (mm)',
    modelPrediction: 'Model tahmini (mm)',
    margin: 'Marj (mm)',
    complianceSummary: 'Uyum özeti',
    complianceScore: 'Skor',
    totalRules: 'Toplam kural',
    passed: 'Geçti',
    failed: 'Başarısız',
    review: 'İnceleme',
    risks: 'Riskler',
    actions: 'Önerilen aksiyonlar',
    recommendedRanges: 'Önerilen aralıklar',
    rangeParam: 'Parametre',
    rangeMin: 'Min',
    rangeMax: 'Maks',
    rangeUnit: 'Birim',
    rangeCurrent: 'Mevcut',
    rangeStatus: 'Durum',
    modelResults: 'Model sonuçları',
    complianceConflicts: 'Kural çakışmaları',
    conflictWinner: 'Kazanan',
    conflictChallenger: 'Rakip',
  },
  stackDefinition: {
    sectionTitle: 'Malzeme Yığını Tanımı',
    stackCountLabel: 'Kat Sayısı',
    layerPrefix: 'Kat',
    materialFamily: 'Malzeme Ailesi',
    materialFamilyPlaceholder: 'ör. mild_steel',
    materialSubtype: 'Malzeme Alt Tipi',
    materialSubtypePlaceholder: 'ör. IF',
    thickness: 'Kalınlık (mm)',
    coated: 'Kaplı',
    engineeringReviewRequired: 'Bu konfigürasyon mühendislik incelemesi gerektirir.',
  },
  parameterPanel: {
    sectionTitle: 'Kaynak Parametreleri',
    groupElectrical: 'Elektrik / Kaynak',
    groupForce: 'Kuvvet / Elektrot',
    groupTime: 'Zaman Parametreleri',
    groupCooling: 'Soğutma / Makine Koşulları',
    currentKa: 'Akım (kA)',
    forceKn: 'Kuvvet (kN)',
    forceDaN: 'Kuvvet (daN)',
    tipDiameter: 'Uç Çapı (mm)',
    airPressure: 'Hava Basıncı (bar)',
    weldTime: 'Kaynak Süresi',
    squeezeTime: 'Sıkıştırma Süresi',
    holdTime: 'Tutma Süresi',
    approachTime: 'Yaklaşma Süresi',
    coolingTime: 'Soğutma Süresi',
    coolingFlow: 'Soğutma Debisi (L/dk)',
    coolingTemp: 'Soğutma Sıcaklığı (°C)',
    dcCurrent: 'DC Akım',
    adhesive: 'Yapıştırıcı',
    shuntRisk: 'Şant Riski',
    unitCycle: 'Çevrim',
    unitMs: 'ms',
    unitToggleLabel: 'Zaman Birimi',
    unitBasisUnresolved: 'Birim belirsiz',
    cycleEqMs: '1 çevrim = 20 ms (50 Hz)',
    runAnalysis: 'Analiz Et ve Kaydet',
    analyzing: 'Analiz ediliyor…',
  },
  referenceGuidancePanel: {
    sectionTitle: 'Referans Kılavuzu',
    referenceProfile: 'Referans Profili',
    referenceBand: 'Referans Bandı',
    effectiveThickness: 'Efektif Kalınlık',
    parameterRange: 'Parametre Aralığı',
    engineeringReviewRequired: 'Mühendislik incelemesi gerekli.',
    outsideRangeWarning: 'İdeal seçim limitleri dışına çıktınız.',
    notEvaluated: 'Değerlendirilmedi',
    withinRange: 'Aralık İçinde',
    belowRange: 'Aralığın Altında',
    aboveRange: 'Aralığın Üzerinde',
    unitBasisUnresolved: 'Birim belirsiz',
    noReferenceFound: 'Bu konfigürasyon için referans profili bulunamadı.',
    rangeParam: 'Parametre',
    rangeMin: 'Min',
    rangeMax: 'Maks',
    rangeUnit: 'Birim',
    rangeStatus: 'Durum',
    guidanceInfoNote: 'Referans kılavuzu yalnızca bilgi amaçlıdır. Uyum değerlendirmesini veya riski etkilemez.',
  },
  riskLabels: {
    HIGH: 'Yüksek',
    MEDIUM: 'Orta',
    LOW: 'Düşük',
  },
}

/* ── English ─────────────────────────────────────────────────────────── */
const EN: AppContent = {
  topbar: {
    signOut: 'Sign out',
  },
  nav: {
    groups: {
      dash: 'SpotWeldPro AI',
      work: 'WORK',
      analysis: 'ANALYSIS',
    },
    items: {
      dashboard: 'Dashboard',
      projects: 'Projects & Weld Points',
      engineering: 'Weld Lobe Lab',
      analysis: 'Weld Quality Analysis',
      failure: 'Failure Analysis',
    },
  },
  analysisPage: {
    kicker: 'Production · Spot Welding Parameter Analysis',
    title: 'Weld Quality Analysis',
    subtitle:
      'Rule-governed spot weld evaluation — deterministic limits with model support',
    runAnalysis: 'Run analysis',
    analyzing: 'Analyzing…',
    authorityChip: 'Authority: deterministic rules',
    stackChip: 'Stack',
    materialChip: 'Material',
    totalThicknessChip: 'Total thickness',
    engineeringInputs: 'Engineering inputs',
    engineeringInputsMeta: 'stack · parameters',
    weldingParameters: 'Welding parameters',
    currentKa: 'Current (kA)',
    weldTime: 'Weld time (cycles)',
    electrodeForce: 'Electrode force (kN)',
    tipDiameter: 'Tip diameter (mm)',
    engineeringResult: 'Engineering result',
    noResultTitle: 'No analysis result yet',
    noResultHint:
      'Run analysis to generate the governed engineering result. ' +
      'Empty state is expected before the first backend evaluation.',
    noResultAction: 'Next action: Run analysis with the current parameter set.',
    evaluating: 'Evaluating governed rules…',
    inputsFooter:
      'Inputs are evaluated by backend deterministic rules only. Top-level material follows Layer 1.',
    resultFooter: 'Traceability: backend deterministic output only.',
    traceabilityTitle: 'Traceability',
    traceabilityMeta: 'governed context',
    traceabilityMaterial: 'Material (Layer 1)',
    traceabilityStack: 'Stack',
    traceabilityTotalThickness: 'Total thickness',
    traceabilityCurrentMode: 'Current mode',
    traceabilitySelectedModel: 'Selected model',
    traceabilityCompliance: 'Compliance status',
    traceabilityParamRevision: 'Parameter revision',
    traceabilityRuleRevision: 'Rule revision',
    traceabilityEvalId: 'Evaluation ID',
    traceabilityEvidenceSource: 'Evidence source',
    traceabilityApprovalState: 'Approval state',
    traceabilityReadiness: 'Readiness',
    traceabilityFooter:
      'Governed identifiers populate as registry/evidence integration lands. No values are fabricated.',
    backendUnavailableTitle: 'Backend connection unavailable',
    backendUnavailableText:
      'Engineering data could not be loaded. Verify the API service and retry.',
  },
  dashboardPage: {
    kicker: 'COMMAND CENTER',
    kickerData: 'Overview · Spot Welding Parametre Analysis',
    title: 'Command Center',
    subtitle: 'Production quality and engineering overview',
    loading: 'Loading command center…',
    errorTitle: 'Backend connection unavailable',
    errorText:
      'Engineering data could not be loaded. Verify the API service and retry.',
    totalProjects: 'Total Projects',
    activeProjects: 'Active Projects',
    totalWeldPoints: 'Total Weld Points',
    riskyWeldPoints: 'Risky Weld Points',
    pendingApprovals: 'Pending Approvals',
    rejectedApprovals: 'Rejected Approvals',
    users: 'Users',
    auditEvents: 'Audit Events (7 d)',
    engineeringReview: 'engineering review required',
    noReview: 'no review required',
    awaitingDecision: 'awaiting human decision',
    engineeringActivity: 'Engineering activity',
    engineeringActivityMeta: 'current backend state',
    systemReadiness: 'System readiness',
    systemReadinessMeta: 'connection',
    projects: 'Projects',
    weldPoints: 'Weld points',
    approvals: 'Approvals',
    backend: 'Backend',
    auditEvents7d: 'Audit events (7 d)',
    total: 'total',
    active: 'active',
    risky: 'risky',
    pending: 'pending',
    rejected: 'rejected',
    connected: 'connected',
    activityFooter: 'Live backend counts only — no sampled metrics.',
    readinessFooter: 'Audit-backed traceability context.',
  },
  roleLabels: {
    SYSTEM_ADMIN:           'System Admin',
    PROCESS_ENGINEER:       'Process Engineer',
    QUALITY_ENGINEER:       'Quality Engineer',
    MANUFACTURING_ENGINEER: 'Manufacturing Engineer',
    MAINTENANCE:            'Maintenance',
    OPERATOR:               'Operator',
    READ_ONLY:              'Read Only',
    CUSTOMER:               'Customer',
  },
  stackEditor: {
    sectionTitle: 'Stack-Up Configuration',
    stackCountLabel: 'Stack count',
    layerPrefix: 'Layer',
    materialFamily: 'Material family',
    materialFamilyPlaceholder: 'e.g. DP, IF, AHSS',
    materialSubtype: 'Material subtype',
    materialSubtypePlaceholder: 'e.g. DP600, DP780',
    thickness: 'Thickness (mm)',
    coated: 'Coated',
  },
  advancedPanel: {
    title: 'Advanced Equipment',
    squeezeCycles: 'Squeeze cycles',
    holdCycles: 'Hold cycles',
    coolingFlow: 'Cooling flow (L/min)',
    coolingTemp: 'Cooling temp (°C)',
    dcCurrent: 'DC current',
    adhesive: 'Adhesive bonding',
    shuntRisk: 'Shunt risk',
  },
  resultPanel: {
    empty: 'No analysis result yet…',
    score: 'Score',
    risk: 'Risk',
    nuggetMin: 'Nugget min (mm)',
    nuggetOpt: 'Nugget opt (mm)',
    modelPrediction: 'Model prediction (mm)',
    margin: 'Margin (mm)',
    complianceSummary: 'Compliance summary',
    complianceScore: 'Score',
    totalRules: 'Total rules',
    passed: 'Passed',
    failed: 'Failed',
    review: 'Review',
    risks: 'Risks',
    actions: 'Recommended actions',
    recommendedRanges: 'Recommended ranges',
    rangeParam: 'Parameter',
    rangeMin: 'Min',
    rangeMax: 'Max',
    rangeUnit: 'Unit',
    rangeCurrent: 'Current',
    rangeStatus: 'Status',
    modelResults: 'Model results',
    complianceConflicts: 'Rule conflicts',
    conflictWinner: 'Winner',
    conflictChallenger: 'Challenger',
  },
  stackDefinition: {
    sectionTitle: 'Material Stack Definition',
    stackCountLabel: 'Layer Count',
    layerPrefix: 'Layer',
    materialFamily: 'Material Family',
    materialFamilyPlaceholder: 'e.g. mild_steel',
    materialSubtype: 'Material Subtype',
    materialSubtypePlaceholder: 'e.g. IF',
    thickness: 'Thickness (mm)',
    coated: 'Coated',
    engineeringReviewRequired: 'This configuration requires engineering review.',
  },
  parameterPanel: {
    sectionTitle: 'Weld Parameters',
    groupElectrical: 'Electrical / Welding',
    groupForce: 'Force / Electrode',
    groupTime: 'Time Parameters',
    groupCooling: 'Cooling / Machine Conditions',
    currentKa: 'Current (kA)',
    forceKn: 'Force (kN)',
    forceDaN: 'Force (daN)',
    tipDiameter: 'Tip Diameter (mm)',
    airPressure: 'Air Pressure (bar)',
    weldTime: 'Weld Time',
    squeezeTime: 'Squeeze Time',
    holdTime: 'Hold Time',
    approachTime: 'Approach Time',
    coolingTime: 'Cooling Time',
    coolingFlow: 'Cooling Flow (L/min)',
    coolingTemp: 'Cooling Temperature (°C)',
    dcCurrent: 'DC Current',
    adhesive: 'Adhesive',
    shuntRisk: 'Shunt Risk',
    unitCycle: 'Cycle',
    unitMs: 'ms',
    unitToggleLabel: 'Time Unit',
    unitBasisUnresolved: 'Unit unresolved',
    cycleEqMs: '1 cycle = 20 ms (50 Hz)',
    runAnalysis: 'Analyze and Save',
    analyzing: 'Analyzing…',
  },
  referenceGuidancePanel: {
    sectionTitle: 'Reference Guidance',
    referenceProfile: 'Reference Profile',
    referenceBand: 'Reference Band',
    effectiveThickness: 'Effective Thickness',
    parameterRange: 'Parameter Range',
    engineeringReviewRequired: 'Engineering review required.',
    outsideRangeWarning: 'You are outside the recommended parameter range.',
    notEvaluated: 'Not Evaluated',
    withinRange: 'Within Range',
    belowRange: 'Below Range',
    aboveRange: 'Above Range',
    unitBasisUnresolved: 'Unit unresolved',
    noReferenceFound: 'No reference profile found for this configuration.',
    rangeParam: 'Parameter',
    rangeMin: 'Min',
    rangeMax: 'Max',
    rangeUnit: 'Unit',
    rangeStatus: 'Status',
    guidanceInfoNote: 'Reference guidance is informational only. It does not affect compliance evaluation or risk.',
  },
  riskLabels: {
    HIGH: 'High',
    MEDIUM: 'Medium',
    LOW: 'Low',
  },
}

export const APP_CONTENT: Record<AppLanguage, AppContent> = { tr: TR, en: EN }
