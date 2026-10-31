/**
 * HelpCenterPage.tsx — P2-E Interactive Engineering Help Center
 * Covers all implemented SpotWeldPro AI modules with bilingual content,
 * visual SVG diagrams, interactive examples, and engineering glossary.
 */
import { useState, useMemo } from 'react'
import { useAppLanguage } from '../i18n/useAppLanguage'
import type { AppLanguage } from '../i18n/appContent'

// ── Bilingual helpers ────────────────────────────────────────────────────────
type Bi = { tr: string; en: string }
type BiList = { tr: string[]; en: string[] }
const tx = (lang: AppLanguage, b: Bi) => b[lang]
const txl = (lang: AppLanguage, b: BiList) => b[lang]

// ── Data types ───────────────────────────────────────────────────────────────
export interface HelpField {
  name: string; unit?: string; range?: string; desc: Bi
}
export interface HelpExample {
  label: string
  note: Bi
  inputs: Array<{ k: string; v: string }>
  outputs: Array<{ k: string; v: string }>
}
export interface HelpModule {
  id: string; icon: string; nav: Bi; title: Bi; purpose: Bi
  tags: string[]
  inputs?: HelpField[]; outputs?: HelpField[]
  steps: BiList
  example?: HelpExample
  warnings?: BiList
  standards?: string[]
  relatedIds: string[]
  diagram?: 'rsw' | 'energy-window' | 'weld-lobe' | 'taguchi' | 'multi-spot'
}
export interface GlossaryTerm { term: string; def: Bi }

// ── Module content ───────────────────────────────────────────────────────────
export const HELP_MODULES: HelpModule[] = [
  {
    id: 'dashboard', icon: 'D', nav: { tr: 'Gösterge Paneli', en: 'Dashboard' },
    title: { tr: 'Gösterge Paneli — Proje Özeti', en: 'Dashboard — Project Overview' },
    purpose: {
      tr: 'Tüm projelerin gerçek zamanlı KPI özetini, son mühendislik aktivitesini ve sistem hazırlık durumunu gösterir.',
      en: 'Shows a real-time KPI summary of all projects, recent engineering activity, and system readiness status.'
    },
    tags: ['dashboard', 'kpi', 'overview', 'gösterge', 'özet'],
    outputs: [
      { name: 'Total Projects', desc: { tr: 'Sistemdeki toplam proje sayısı', en: 'Total number of projects in the system' } },
      { name: 'Active Projects', desc: { tr: 'Aktif durumda olan projeler', en: 'Projects with active status' } },
      { name: 'Total Weld Points', desc: { tr: 'Tüm projelerdeki kaynak noktası sayısı', en: 'Weld point count across all projects' } },
      { name: 'Risky Weld Points', desc: { tr: 'Kalite riski işaretlenmiş kaynak noktaları', en: 'Weld points flagged with quality risk' } },
      { name: 'Pending Approvals', desc: { tr: 'Onay bekleyen kayıt sayısı', en: 'Records awaiting engineering approval' } },
      { name: 'Audit Events (7d)', desc: { tr: 'Son 7 günde sistemde kaydedilen eylemler', en: 'System audit events logged in the last 7 days' } },
    ],
    steps: {
      tr: ['Giriş yapın — Gösterge Paneli otomatik yüklenir', 'KPI kartlarını inceleyin (Toplam Projeler, Risk, Onaylar)', 'Mühendislik Aktivitesi bölümünde son işlemleri görüntüleyin', 'Sistem Hazırlığı bölümünde backend bağlantısını doğrulayın'],
      en: ['Sign in — Dashboard loads automatically', 'Review KPI cards (Total Projects, Risky, Pending)', 'Check Engineering Activity for recent actions', 'Verify backend connectivity in System Readiness panel'],
    },
    relatedIds: ['projects', 'analysis'],
  },
  {
    id: 'projects', icon: 'P', nav: { tr: 'Projeler & Kaynak Noktaları', en: 'Projects & Weld Points' },
    title: { tr: 'Proje Yönetimi ve Kaynak Noktası Tanımı', en: 'Project Management & Weld Point Definition' },
    purpose: {
      tr: 'Kaynak projelerini ve weld point özelliklerini (malzeme paketi, parametreler) yönetir.',
      en: 'Manages welding projects and weld point specifications including material stack and process parameters.'
    },
    tags: ['project', 'weld point', 'stack', 'material', 'proje', 'malzeme'],
    inputs: [
      { name: 'Project Name', desc: { tr: 'Proje adı (serbest metin)', en: 'Project name (free text)' } },
      { name: 'Material Family', desc: { tr: 'Üst düzey malzeme ailesi (ör. Düşük/Orta Karbonlu Çelik)', en: 'Top-level material family (e.g. Low/Medium Carbon Steel)' } },
      { name: 'Material Subtype', desc: { tr: 'Malzeme alt tipi (ör. DC04, S235JR)', en: 'Material subtype (e.g. DC04, S235JR)' } },
      { name: 'Layer Thickness (mm)', unit: 'mm', range: '0.4–4.0', desc: { tr: 'Sac katmanı kalınlığı', en: 'Sheet layer thickness' } },
      { name: 'Stack Count', desc: { tr: '2T (2 katman) veya 3T (3 katman) — 4T devre dışı', en: '2T (2 layers) or 3T (3 layers) — 4T is legacy disabled' } },
    ],
    steps: {
      tr: ['Projeler sayfasında "Yeni Proje" düğmesine tıklayın', 'Proje adını ve açıklamasını girin', 'Projeyi açın — Kaynak Noktası Sihirbazı başlar', 'Malzeme paketini tanımlayın (2T veya 3T, her katman için malzeme + kalınlık)', 'Kaynak noktası parametrelerini girin (akım, süre, kuvvet, uç çapı)', 'Kaydedilen nokta, analiz ve hata analizi için hazır hale gelir'],
      en: ['Click "New Project" on the Projects page', 'Enter project name and description', 'Open the project — Weld Point Wizard starts', 'Define the material stack (2T or 3T, material + thickness per layer)', 'Enter weld point parameters (current, time, force, tip diameter)', 'Saved point becomes available for analysis and failure assessment'],
    },
    warnings: {
      tr: ['4T (4 katmanlı) kayıtlar yalnızca eski destek için mevcuttur ve yeni değerlendirme oluşturmaz', 'Katman malzeme ailesi üst düzey kuralları belirler — farklı aileler için ayrı nokta tanımlayın'],
      en: ['4T (4-layer) records exist for legacy support only and do not generate new evaluations', 'Layer material family determines top-level rules — define separate points for different families'],
    },
    relatedIds: ['analysis', 'failure'],
  },
  {
    id: 'analysis', icon: 'Q', nav: { tr: 'Kaynak Kalite Analizi', en: 'Weld Quality Analysis' },
    title: { tr: 'Kaynak Kalite Analizi — Deterministik Kural Motoru', en: 'Weld Quality Analysis — Deterministic Rule Engine' },
    purpose: {
      tr: 'Kaynak parametrelerini mühendislik eşiklerine göre deterministik kurallarla değerlendirir.',
      en: 'Evaluates welding parameters against engineering thresholds using deterministic rule-based logic.'
    },
    tags: ['quality', 'analysis', 'rules', 'compliance', 'kalite', 'kural', 'uyum'],
    inputs: [
      { name: 'Weld Current (kA)', unit: 'kA', range: '4–14', desc: { tr: 'RMS etkin kaynak akımı (tepe değeri değil)', en: 'RMS effective weld current (not peak value)' } },
      { name: 'Weld Time (cycles)', unit: 'cycles', range: '5–40', desc: { tr: 'Kaynak süresi (50 Hz\'de 1 çevrim = 20 ms)', en: 'Weld time (at 50 Hz: 1 cycle = 20 ms)' } },
      { name: 'Electrode Force (kN)', unit: 'kN', range: '1–7', desc: { tr: 'Elektrot sıkıştırma kuvveti', en: 'Electrode clamping force' } },
      { name: 'Tip Diameter (mm)', unit: 'mm', range: '4–16', desc: { tr: 'Elektrot uç temas çapı (yüz çapı)', en: 'Electrode tip contact face diameter' } },
      { name: 'Material Stack', desc: { tr: '2T veya 3T sac paketi — katman malzemeleri ve kalınlıkları', en: '2T or 3T sheet stack — layer materials and thicknesses' } },
    ],
    outputs: [
      { name: 'Quality Score', desc: { tr: 'Genel uyum puanı (0–100)', en: 'Overall compliance score (0–100)' } },
      { name: 'Risk Level', desc: { tr: 'HIGH / MEDIUM / LOW risk seviyesi', en: 'HIGH / MEDIUM / LOW risk classification' } },
      { name: 'Nugget Size Range', unit: 'mm', desc: { tr: 'Tahmini nugget çapı aralığı', en: 'Estimated nugget diameter range' } },
      { name: 'Compliance Table', desc: { tr: 'Her parametre için geçti/kaldı/incelendi durumu', en: 'Pass/fail/review status per parameter' } },
      { name: 'Recommended Ranges', desc: { tr: 'Belirlenen malzeme paketi için önerilen değer aralıkları', en: 'Suggested parameter ranges for the identified stack' } },
    ],
    steps: {
      tr: ['Projeler üzerinden bir kaynak noktası seçin — bağlam otomatik yüklenir', 'Kaynak Kalite Analizi sayfasına gidin', 'Malzeme paketini doğrulayın (katmanlar, kalınlık)', 'Kaynak parametrelerini girin (kA, çevrim, kN, mm)', '"Analizi Çalıştır" düğmesine tıklayın', 'Sonuç panelinde puanı, riski ve uyum tablosunu inceleyin', 'Kırmızı satırlar için önerilen aralıklara bakın'],
      en: ['Select a weld point from Projects — context loads automatically', 'Navigate to Weld Quality Analysis', 'Verify the material stack (layers, thickness)', 'Enter weld parameters (kA, cycles, kN, mm)', 'Click "Run Analysis"', 'Review score, risk, and compliance table in the result panel', 'For red rows, check the Recommended Ranges section'],
    },
    example: {
      label: 'SENTETİK DEMO VERİSİ / SYNTHETIC DEMO DATA',
      note: { tr: 'Gerçek bir kaynak bağlantısını temsil etmez.', en: 'Does not represent a real weld joint.' },
      inputs: [
        { k: 'Stack', v: '2T — DC04 / 0.8 mm + DC04 / 0.8 mm' },
        { k: 'Current', v: '8.5 kA' }, { k: 'Weld Time', v: '14 cycles' },
        { k: 'Force', v: '3.2 kN' }, { k: 'Tip Diameter', v: '6.0 mm' },
      ],
      outputs: [
        { k: 'Score', v: '82 / 100' }, { k: 'Risk', v: 'MEDIUM' },
        { k: 'Nugget Estimate', v: '4.8–5.4 mm' }, { k: 'Current', v: 'PASS' }, { k: 'Force', v: 'REVIEW' },
      ],
    },
    warnings: {
      tr: ['Kural motoru deterministik eşikler kullanır — ML modeli değildir', 'Nugget tahmini referans aralığıdır; UT veya çekme testi ile doğrulama gerektirir'],
      en: ['Rule engine uses deterministic thresholds — not an ML model', 'Nugget estimate is a reference range; confirmation via UT or destructive test required'],
    },
    relatedIds: ['failure', 'models'],
  },
  {
    id: 'failure', icon: 'F', nav: { tr: 'Hata Analizi', en: 'Failure Analysis' },
    title: { tr: 'Hata Analizi — ML Tabanlı Hata Olasılığı', en: 'Failure Analysis — ML-Based Failure Probability' },
    purpose: {
      tr: 'Kaynak kalitesi analiz bağlamını kullanarak ML modelleriyle hata modu olasılıklarını tahmin eder.',
      en: 'Uses ML models to estimate failure mode probabilities from the weld quality analysis context.'
    },
    tags: ['failure', 'ML', 'probability', 'risk', 'hata', 'olasılık'],
    inputs: [
      { name: 'Analysis Context', desc: { tr: 'Kaynak Kalite Analizi sonucu (otomatik aktarılır)', en: 'Weld Quality Analysis result (transferred automatically)' } },
      { name: 'Material Family', desc: { tr: 'Üst düzey malzeme ailesi', en: 'Top-level material family' } },
      { name: 'Process Mode', desc: { tr: 'Kaplı veya kaplamasız çelik seçimi', en: 'Coated or uncoated steel selection' } },
    ],
    outputs: [
      { name: 'Priority Risks', desc: { tr: 'En yüksek olasılıklı hata modları (güven skoru ile)', en: 'Highest-probability failure modes with confidence scores' } },
      { name: 'Main Factors', desc: { tr: 'Her hata moduna katkıda bulunan ana faktörler', en: 'Main contributing factors for each failure mode' } },
      { name: 'Preventive Actions', desc: { tr: 'Her risk için önleyici eylem önerileri', en: 'Preventive action recommendations per risk' } },
    ],
    steps: {
      tr: ['Önce Kaynak Kalite Analizi\'ni tamamlayın', '"Hata Analizine Git" bağlantısına tıklayın — bağlam aktarılır', 'Malzeme kaplama durumunu seçin (kaplı/kaplamasız)', '"Hata Olasılığını Hesapla" düğmesine tıklayın', 'Öncelikli riskleri, ana faktörleri ve önleyici eylemleri inceleyin'],
      en: ['Complete Weld Quality Analysis first', 'Click "Navigate to Failure Analysis" — context transfers', 'Select material coating status (coated/uncoated)', 'Click "Calculate Failure Probability"', 'Review priority risks, main factors, and preventive actions'],
    },
    warnings: {
      tr: ['Çıktılar olasılıksal rehberliktir — sertifikalı kalite tahminleri değildir', 'Kaplama durumu sonuçları önemli ölçüde etkiler; dikkatli seçin', 'Ultrasonik test veya fiziksel deney yüksek riskli bulgular için zorunludur'],
      en: ['Outputs are probabilistic guidance — not certified quality predictions', 'Coating status significantly affects results; select carefully', 'UT or destructive testing is required for high-risk findings'],
    },
    relatedIds: ['analysis', 'models'],
  },
  {
    id: 'engineering', icon: 'L', nav: { tr: 'Kaynak Lobu Laboratuvarı', en: 'Weld Lobe Lab' },
    title: { tr: 'Kaynak Lobu Laboratuvarı — Proses Penceresi Haritası', en: 'Weld Lobe Lab — Process Window Mapping' },
    purpose: {
      tr: 'Akım × süre uzayında güvenli çalışma bölgesini (kaynak lobunu) hesaplar ve görselleştirir.',
      en: 'Computes and visualizes the safe operating region (weld lobe) in current × time space.'
    },
    tags: ['lobe', 'process window', 'current', 'time', 'expulsion', 'lob', 'proses penceresi'],
    diagram: 'weld-lobe',
    inputs: [
      { name: 'Material Family', desc: { tr: 'Demo: Düşük/Orta Karbonlu Çelik (sabit)', en: 'Demo: Low/Medium Carbon Steel (fixed)' } },
      { name: 'Sheet Thickness', unit: 'mm', desc: { tr: 'Demo: 1.0 mm (sabit)', en: 'Demo: 1.0 mm (fixed)' } },
      { name: 'Electrode Force', unit: 'kN', desc: { tr: 'Demo: 3.0 kN (sabit)', en: 'Demo: 3.0 kN (fixed)' } },
      { name: 'Current Sweep', unit: 'kA', desc: { tr: 'Demo: 6–12 kA, adım 0.5 kA (sabit)', en: 'Demo: 6–12 kA, step 0.5 kA (fixed)' } },
      { name: 'Time Sweep', unit: 'cycles', desc: { tr: 'Demo: 8–18 çevrim, adım 1 (sabit)', en: 'Demo: 8–18 cycles, step 1 (fixed)' } },
    ],
    outputs: [
      { name: 'Safe Zone Count', desc: { tr: 'Kabul edilebilir nugget oluşturan parametre kombinasyonu sayısı', en: 'Parameter combinations yielding acceptable nugget formation' } },
      { name: 'Warning Zone Count', desc: { tr: 'Sınır bölgesindeki kombinasyon sayısı', en: 'Parameter combinations in the boundary region' } },
      { name: 'Unsafe Zone Count', desc: { tr: 'Yetersiz füzyon veya fırlama riski olan kombinasyonlar', en: 'Combinations with insufficient fusion or expulsion risk' } },
      { name: 'Optimum Point', desc: { tr: 'Güvenlik marjını maksimize eden kA/çevrim kombinasyonu', en: 'kA/cycles combination maximizing safety margin' } },
      { name: 'Sensitivity Ranking', desc: { tr: 'Akım ve sürenin nugget boyutuna göreceli etkisi', en: 'Relative influence of current and time on nugget size' } },
    ],
    steps: {
      tr: ['"Kaynak Lobu Laboratuvarı" sayfasına gidin', 'Demo konfigürasyonunu kontrol edin (malzeme, kalınlık, kuvvet, tarama aralıkları)', '"Hesapla" düğmesine tıklayın', 'Özet KPI\'larda Güvenli/Uyarı/Güvensiz sayılarını inceleyin', 'Optimum noktayı not alın (kA ve çevrim)', 'Duyarlılık sıralamasında hangi parametrenin daha baskın olduğunu değerlendirin'],
      en: ['Navigate to "Weld Lobe Lab"', 'Review the demo configuration (material, thickness, force, sweep ranges)', 'Click "Calculate"', 'Review Safe/Warning/Unsafe counts in summary KPIs', 'Note the optimum point (kA and cycles)', 'Check sensitivity ranking for the dominant parameter'],
    },
    warnings: {
      tr: ['Mevcut uygulama sabit demo parametreleri kullanır — üretim kullanımı için malzeme spesifik doğrulama gerektirir', 'Lob sınırları ampirik modellerle yaklaşıktır; gerçek numunelerle doğrulama zorunludur'],
      en: ['Current implementation uses fixed demo parameters — production use requires material-specific validation', 'Lobe boundaries are model approximations; verification with real coupons is mandatory'],
    },
    relatedIds: ['analysis', 'statistical'],
  },
  {
    id: 'models', icon: 'M', nav: { tr: 'Model Kataloğu', en: 'Model Catalog' },
    title: { tr: 'Model Kataloğu — AI/ML/Fizik Model Sicili', en: 'Model Catalog — AI / ML / Physics Model Registry' },
    purpose: {
      tr: 'Sistemdeki tüm mühendislik modellerini şeffaflık raporuyla listeler.',
      en: 'Lists all engineering models in the system with a full transparency report.'
    },
    tags: ['model', 'catalog', 'ML', 'AI', 'physics', 'validation', 'katalog', 'doğrulama'],
    outputs: [
      { name: 'Model Cards', desc: { tr: 'Her model için: isim, sürüm, durum, malzemeler, kalınlık aralığı', en: 'Per model: name, version, status, materials, thickness range' } },
      { name: 'Validation Evidence', desc: { tr: 'RMSE, MAE, R², Bias, eğitim/test sayısı', en: 'RMSE, MAE, R², Bias, training/test sample count' } },
      { name: 'Model Status', desc: { tr: 'Validated > ConditionallyValidated > Experimental > UnderReview > NotAvailable', en: 'Validated > ConditionallyValidated > Experimental > UnderReview > NotAvailable' } },
    ],
    steps: {
      tr: ['Model Kataloğu sayfasına gidin', 'Sekmeleri kullanın: Tahmin / DOE / İstatistik / Fizik', 'Malzeme ve kalınlık aralığınıza uygun modeli seçin', 'Doğrulama kanıtı bölümünde RMSE ve R² değerlerini inceleyin', 'Durum rozetini kontrol edin — Validated statüsünü tercih edin'],
      en: ['Navigate to Model Catalog', 'Use tabs: Prediction / DOE / Statistics / Physics', 'Find the model matching your material and thickness range', 'Review RMSE and R² in the validation evidence section', 'Check status badge — prefer Validated status'],
    },
    warnings: {
      tr: ['Experimental veya UnderReview modeller üretim kararlarında tek başına kullanılmamalıdır'],
      en: ['Experimental or UnderReview models must not be used alone for production decisions'],
    },
    relatedIds: ['analysis', 'failure', 'statistical'],
  },
  {
    id: 'statistical', icon: 'S', nav: { tr: 'Taguchi DOE & ANOVA', en: 'Taguchi DOE & ANOVA' },
    title: { tr: 'Taguchi DOE & ANOVA — Parametrik Optimizasyon', en: 'Taguchi DOE & ANOVA — Parameter Optimization' },
    purpose: {
      tr: 'Yapılandırılmış deney tasarımı (DOE) ve varyans analizi (ANOVA) ile kaynak parametrelerini optimize eder.',
      en: 'Structured design of experiments and analysis of variance for welding parameter optimization.'
    },
    tags: ['taguchi', 'DOE', 'ANOVA', 'L9', 'orthogonal', 'SN ratio', 'optimization', 'deney'],
    diagram: 'taguchi',
    inputs: [
      { name: 'Array Type', desc: { tr: 'L4 (2-seviyeli, 3 faktör), L9 (3-seviyeli, 4 faktör), L16, L27', en: 'L4 (2-level, 3 factors), L9 (3-level, 4 factors), L16, L27' } },
      { name: 'Factors', desc: { tr: 'Her faktörün adı, birimi ve seviyeleri (virgülle ayrılmış)', en: 'Name, unit, and levels for each factor (comma-separated)' } },
      { name: 'Response Variable', desc: { tr: 'Ölçülen çıktı değişkeni (ör. Nugget çapı mm)', en: 'Measured output variable (e.g. Nugget diameter mm)' } },
      { name: 'S/N Objective', desc: { tr: 'LTB (büyük iyidir), STB (küçük iyidir), NTB (nominal en iyi)', en: 'LTB (larger is better), STB (smaller is better), NTB (nominal is best)' } },
    ],
    outputs: [
      { name: 'Design Matrix', desc: { tr: 'Her deney koşulunu gösteren ortogonal dizi', en: 'Orthogonal array showing each experimental run condition' } },
      { name: 'ANOVA Table', desc: { tr: 'SS, DF, MS, F-istatistiği, p-değeri, katkı yüzdesi', en: 'SS, DF, MS, F-statistic, p-value, contribution percent' } },
      { name: 'Optimal Levels', desc: { tr: 'Her faktör için maksimum S/N oranını veren seviye', en: 'Level maximizing S/N ratio for each factor' } },
      { name: 'Additive Prediction', desc: { tr: 'Optimal kombinasyon için tahmin edilen yanıt değeri', en: 'Predicted response value for optimal combination' } },
    ],
    steps: {
      tr: ['"Taguchi DOE" sekmesini seçin', 'Dizi tipini seçin (L4/L9/L16/L27)', 'Faktörleri ve seviyelerini ekleyin', '"Tasarım Oluştur" tıklayın — deney matrisi görünür', 'Deneyleri gerçek dünya koşullarında çalıştırın', 'Her koşut için ölçülen yanıt değerini girin', 'S/N hedefini seçin (LTB/STB/NTB)', '"Analiz Et" tıklayın', 'ANOVA tablosunda F-değeri ve katkı yüzdesini inceleyin', 'Optimal seviyeleri ve toplamsal tahminleri kayıt altına alın'],
      en: ['Select "Taguchi DOE" tab', 'Choose array type (L4/L9/L16/L27)', 'Add factors and their levels', 'Click "Generate Design" — matrix appears', 'Run experiments under real-world conditions', 'Enter measured response for each run', 'Select S/N objective (LTB/STB/NTB)', 'Click "Analyze"', 'Review F-values and contribution % in ANOVA table', 'Record optimal levels and additive prediction'],
    },
    example: {
      label: 'SENTETİK DEMO VERİSİ / SYNTHETIC DEMO DATA',
      note: { tr: 'Gerçek deney sonuçlarını temsil etmez. Gerçek üretim için ampirik ölçüm gereklidir.', en: 'Does not represent real experiment results. Empirical measurement required for real production.' },
      inputs: [
        { k: 'Array', v: 'L9 (3-level, 4 factors)' },
        { k: 'Factor A', v: 'Current: 7 / 9 / 11 kA' },
        { k: 'Factor B', v: 'Time: 10 / 14 / 18 cycles' },
        { k: 'Factor C', v: 'Force: 2.5 / 3.5 / 4.5 kN' },
        { k: 'Factor D', v: 'Tip Ø: 5 / 6 / 7 mm' },
        { k: 'Response', v: 'Nugget diameter (mm), LTB' },
      ],
      outputs: [
        { k: 'Optimal A', v: 'Level 3 — 11 kA' },
        { k: 'Optimal B', v: 'Level 2 — 14 cycles' },
        { k: 'Factor A contrib.', v: '48.2%' },
        { k: 'Predicted Nugget', v: '5.61 mm (additive model)' },
      ],
    },
    warnings: {
      tr: ['Sonuçlar yalnızca deney aralığında geçerlidir — ekstrapolasyon yapılmamalıdır', 'Yanıt değerleri gerçek ölçülen değerler olmalıdır; tahmin veya hesaplama kullanılmamalıdır', 'Doymuş dizilerde bazı faktörler ayırt edilemeyebilir (⚠ uyarısı gösterilir)'],
      en: ['Results are valid only within the experimental range — do not extrapolate', 'Response values must be real measured data; do not use estimates or calculations', 'Saturated arrays may confound some factors (⚠ warning shown)'],
    },
    standards: ['ISO 14373 (Resistance Spot Welding)', 'ISO 17657 (Weld Nugget Geometry)'],
    relatedIds: ['engineering', 'models'],
  },
  {
    id: 'energy-single', icon: 'E₁', nav: { tr: 'Enerji — Tek Nokta', en: 'Energy — Single Point' },
    title: { tr: 'Tek Nokta Enerji Analizi — I²Rt Hesabı ve Enerji Penceresi', en: 'Single Point Energy — I²Rt Calculation & Energy Window' },
    purpose: {
      tr: 'E = I²Rt formülüyle elektrot tarafı enerjiyi hesaplar ve doğrulanmış pencere sınırlarıyla karşılaştırır.',
      en: 'Calculates electrode-side energy via E = I²Rt and compares to validated energy window bounds.'
    },
    tags: ['energy', 'I2Rt', 'window', 'kJ', 'enerji', 'pencere'],
    diagram: 'energy-window',
    inputs: [
      { name: 'Weld Current RMS', unit: 'kA', range: '4–14', desc: { tr: 'Efektif (RMS) kaynak akımı — tepe değeri değil', en: 'Effective (RMS) weld current — not peak value' } },
      { name: 'Contact Resistance', unit: 'µΩ', range: '50–300', desc: { tr: 'Dinamik temas direnci (tipikal: 80–150 µΩ çelik)', en: 'Dynamic contact resistance (typical: 80–150 µΩ for steel)' } },
      { name: 'Weld Cycles', unit: 'cycles', range: '8–30', desc: { tr: '50 Hz\'de 8 çevrim = 160 ms', en: 'At 50 Hz: 8 cycles = 160 ms' } },
      { name: 'Frequency', unit: 'Hz', range: '50 or 60', desc: { tr: 'Şebeke frekansı (Türkiye: 50 Hz)', en: 'Grid frequency (EU: 50 Hz, US: 60 Hz)' } },
      { name: 'E_min (kJ/spot)', unit: 'kJ', desc: { tr: 'Minimum kabul edilebilir enerji (doğrulanmış deneysel veri gerektirir)', en: 'Minimum acceptable energy (requires validated experimental data)' } },
      { name: 'E_ideal (kJ/spot)', unit: 'kJ', desc: { tr: 'Hedef ideal enerji (doğrulanmış deneysel veri gerektirir)', en: 'Target ideal energy (requires validated experimental data)' } },
      { name: 'E_max (kJ/spot)', unit: 'kJ', desc: { tr: 'Maksimum kabul edilebilir enerji (doğrulanmış deneysel veri gerektirir)', en: 'Maximum acceptable energy (requires validated experimental data)' } },
    ],
    outputs: [
      { name: 'Energy (J / kJ / Wh / kWh)', desc: { tr: 'Hesaplanan elektrot tarafı enerji (dört birimde)', en: 'Calculated electrode-side energy in four units' } },
      { name: 'Window Status', desc: { tr: 'NOT_ESTABLISHED / IN_WINDOW / BELOW_MIN / ABOVE_MAX / E_CURRENT_ABSENT', en: 'NOT_ESTABLISHED / IN_WINDOW / BELOW_MIN / ABOVE_MAX / E_CURRENT_ABSENT' } },
      { name: 'Quality Risk Flag', desc: { tr: 'E_current < E_ideal: kalite riski uyarısı', en: 'E_current < E_ideal: quality risk warning' } },
    ],
    steps: {
      tr: ['"Enerji Zekası" → "Tek Nokta" sekmesine gidin', 'I²Rt bölümüne: akım (kA), direnç (µΩ), çevrim, frekans girin', '"Enerji Tahmin Et" tıklayın', 'Sonuçları J/kJ/Wh/kWh cinsinden inceleyin', 'Pencere bölümüne E_min/E_ideal/E_max değerlerini girin (doğrulanmış verilerden)', '"Pencereyi Değerlendir" tıklayın — durum rozeti görünür'],
      en: ['Go to "Energy Intelligence" → "Single Point" tab', 'In I²Rt section: enter current (kA), resistance (µΩ), cycles, frequency', 'Click "Estimate Energy"', 'Review results in J/kJ/Wh/kWh', 'Enter E_min/E_ideal/E_max from validated experimental data', 'Click "Evaluate Window" — status badge appears'],
    },
    example: {
      label: 'SENTETİK DEMO VERİSİ / SYNTHETIC DEMO DATA',
      note: { tr: 'Gerçek bir kaynak bağlantısını temsil etmez.', en: 'Does not represent a real weld joint.' },
      inputs: [
        { k: 'Current', v: '9.0 kA' }, { k: 'Resistance', v: '120 µΩ' },
        { k: 'Weld Cycles', v: '12 cycles (50 Hz = 240 ms)' },
        { k: 'E_min', v: '0.28 kJ' }, { k: 'E_ideal', v: '0.35 kJ' }, { k: 'E_max', v: '0.45 kJ' },
      ],
      outputs: [
        { k: 'E = I²Rt', v: '9.0² × 120×10⁻⁶ × 0.240 = 0.2333 J × 1000 → ≈ 0.350 kJ' },
        { k: 'Window Status', v: 'IN_WINDOW' }, { k: 'Quality Risk', v: 'false' },
      ],
    },
    warnings: {
      tr: ['E_min/E_ideal/E_max değerleri teorik olarak türetilemez — doğrulanmış deneysel çalışma gerektirir', 'I²Rt yalnızca elektrot tarafı enerjidir; trafo kayıpları ve soğutma dahil değildir', 'Bu hesaplama tek kaynak darbesi içindir — çok darbeli uygulamalarda her darbe ayrı değerlendirilmelidir'],
      en: ['E_min/E_ideal/E_max cannot be derived theoretically — validated experimental work is required', 'I²Rt is electrode-side energy only; transformer losses and cooling are not included', 'This calculation applies to a single pulse — evaluate each pulse separately for multi-pulse welding'],
    },
    relatedIds: ['energy-multi', 'energy-dashboard'],
  },
  {
    id: 'energy-multi', icon: 'E+', nav: { tr: 'Enerji — Çok Nokta', en: 'Energy — Multi-Spot' },
    title: { tr: 'Çok Noktalı Enerji Agregasyonu', en: 'Multi-Spot Energy Aggregation' },
    purpose: {
      tr: 'Bir parçadaki tüm kaynak noktalarının enerji durumunu toplar ve parça düzeyinde özet üretir.',
      en: 'Aggregates energy status for all weld points on a part and produces part-level summaries.'
    },
    tags: ['multi', 'aggregation', 'part', 'group', 'pareto', 'çok nokta'],
    inputs: [
      { name: 'Weld Points List', desc: { tr: 'Her nokta için: kod, grup, E_current, E_min, E_ideal, E_max (kJ)', en: 'Per point: code, group, E_current, E_min, E_ideal, E_max (kJ)' } },
      { name: 'Production Volume', unit: 'parts/year', desc: { tr: 'Yıllık üretim hacmi (opsiyonel, maliyet için)', en: 'Annual production volume (optional, for cost calculation)' } },
      { name: 'Electricity Tariff', unit: 'EUR/kWh, USD/kWh', desc: { tr: 'Enerji maliyeti tarife (opsiyonel)', en: 'Electricity cost tariff (optional)' } },
    ],
    outputs: [
      { name: 'Part Energy Totals', desc: { tr: 'Toplam E_current, E_ideal, fazla enerji (kJ)', en: 'Total E_current, E_ideal, excess energy (kJ)' } },
      { name: 'Group Summary', desc: { tr: 'Grup bazında nokta sayısı, pencere içi sayısı, risk sayısı', en: 'Per-group point count, in-window count, risk count' } },
      { name: 'Pareto (top N)', desc: { tr: 'En yüksek fazla enerjili noktalara göre sıralanmış liste', en: 'List sorted by highest excess energy points' } },
    ],
    steps: {
      tr: ['"Çok Nokta" sekmesine gidin', 'Kaynak noktalarını girin (+ düğmesi ile ekleyin)', 'Her nokta için enerji değerlerini doldurun', '"Agregasyonu Çalıştır" tıklayın', 'Parça toplamlarını, grup özetlerini ve Pareto tablosunu inceleyin'],
      en: ['Go to "Multi-Spot" tab', 'Add weld points (+ button)', 'Fill energy values for each point', 'Click "Run Aggregation"', 'Review part totals, group summary, and Pareto table'],
    },
    relatedIds: ['energy-single', 'energy-dashboard', 'energy-map'],
  },
  {
    id: 'energy-dashboard', icon: 'ED', nav: { tr: 'Enerji Göstergesi', en: 'Energy Dashboard' },
    title: { tr: 'Enerji & Finansal İstihbarat Göstergesi (P2-D)', en: 'Energy & Financial Intelligence Dashboard (P2-D)' },
    purpose: {
      tr: 'Enerji fazlası verilerini finansal KPI\'lara, gelişmiş Pareto analizine ve duyarlılık matrisine dönüştürür.',
      en: 'Converts energy excess data into financial KPIs, enhanced Pareto analysis, and sensitivity matrix.'
    },
    tags: ['dashboard', 'financial', 'pareto', 'sensitivity', 'cost', 'EUR', 'USD', 'finansal'],
    diagram: 'multi-spot',
    inputs: [
      { name: 'Weld Points', desc: { tr: 'Enerji spesifikasyonları ile kaynak noktaları listesi', en: 'List of weld points with energy specifications' } },
      { name: 'Annual Production Volume', unit: 'parts/year', desc: { tr: 'Yıllık üretim hacmi (1–10.000.000)', en: 'Annual production volume (1–10,000,000)' } },
      { name: 'EUR Tariff', unit: 'EUR/kWh', desc: { tr: 'Elektrik tarifen EUR/kWh cinsinden', en: 'Electricity tariff in EUR/kWh' } },
      { name: 'USD Tariff', unit: 'USD/kWh', desc: { tr: 'Elektrik tarifen USD/kWh cinsinden', en: 'Electricity tariff in USD/kWh' } },
    ],
    outputs: [
      { name: 'Avg Excess / Spot', unit: 'kJ', desc: { tr: 'Ortalama nokta başına fazla enerji', en: 'Average excess energy per weld spot' } },
      { name: 'Part Excess', unit: 'kJ / kWh', desc: { tr: 'Parça başına toplam teorik fazla enerji', en: 'Total theoretical excess energy per part' } },
      { name: 'Annual Cost (EUR/USD)', desc: { tr: 'TAKDİRİ yıllık maliyet — doğrulanmış tasarruf değil', en: 'THEORETICAL annual cost — not a verified saving' } },
      { name: 'Sensitivity Matrix', desc: { tr: '5×5 hacim × tarife matrisi (EUR cinsinden yıllık maliyet)', en: '5×5 volume × tariff matrix (annual cost in EUR)' } },
      { name: 'Enhanced Pareto', desc: { tr: 'Çubuk grafik + kümülatif % çizgisi + %80 referans çizgisi', en: 'Bar chart + cumulative % line + 80% reference line' } },
      { name: 'Energy Window Bullets', desc: { tr: 'Her nokta için yatay bullet grafik (min→maks pencere + E_current)', en: 'Horizontal bullet chart per point (min→max window + E_current)' } },
    ],
    steps: {
      tr: ['"Enerji Göstergesi" sekmesine gidin', 'Kaynak noktalarını girin', 'Üretim hacmini ve tarifelerini girin', '"Enerji Analizi Yap" tıklayın', 'Finansal özeti, Pareto grafiğini ve duyarlılık tablosunu inceleyin'],
      en: ['Go to "Dashboard" tab', 'Enter weld points', 'Enter production volume and tariffs', 'Click "Analyze Energy"', 'Review financial summary, Pareto chart, and sensitivity table'],
    },
    warnings: {
      tr: ['TÜM finansal değerler TAKDİRİ FAZLA ENERJİDİR — doğrulanmış tasarruf değildir', 'Gerçek elektrik tüketimi trafo kayıplarını, elektrodu soğutmayı ve yardımcı yükleri içerir (modelde yok)', 'Üretim kararları için bağımsız enerji ölçümü zorunludur'],
      en: ['ALL financial values are THEORETICAL EXCESS ENERGY — not verified savings', 'Real electricity consumption includes transformer losses, electrode cooling, and auxiliary loads (not modelled)', 'Independent energy metering is mandatory for production decisions'],
    },
    relatedIds: ['energy-single', 'energy-multi', 'energy-scenario'],
  },
  {
    id: 'energy-map', icon: 'EM', nav: { tr: 'Enerji — Parça Haritası', en: 'Energy — Part Map' },
    title: { tr: 'Parça Enerji Haritası — Uzaysal Görselleştirme', en: 'Part Energy Map — Spatial Visualization' },
    purpose: {
      tr: 'Kaynak noktalarını parça üzerinde renk kodlu enerji durumları ile konumsal olarak görselleştirir.',
      en: 'Visualizes weld points spatially on the part with color-coded energy window status.'
    },
    tags: ['map', 'spatial', 'part', 'coordinate', 'harita', 'uzaysal', 'koordinat'],
    inputs: [
      { name: 'Weld Points with Coordinates', desc: { tr: 'X/Y koordinatları opsiyoneldir (0–100 normalize); koordinat yoksa şematik görünüm', en: 'X/Y coordinates optional (0–100 normalized); without coords a schematic chip view is shown' } },
      { name: 'Energy Window Values', desc: { tr: 'Her nokta için E_current, E_min, E_ideal, E_max', en: 'E_current, E_min, E_ideal, E_max per point' } },
    ],
    outputs: [
      { name: 'Color-Coded Map', desc: { tr: 'Renk kodları: Yeşil=Pencerede, Kırmızı=Altında, Turuncu=Üstünde, Gri=Belirlenmemiş', en: 'Colors: Green=In Window, Red=Below Min, Orange=Above Max, Grey=Not Established' } },
      { name: 'Group Filter', desc: { tr: 'Grup bazında filtre ile belirli bir gruba odaklanın', en: 'Group-based filter to focus on a specific group' } },
      { name: 'Point Detail', desc: { tr: 'Haritada bir noktaya tıklayarak detayları görüntüleyin', en: 'Click a point on the map to view its details' } },
    ],
    steps: {
      tr: ['"Parça Haritası" sekmesine gidin', 'Kaynak noktalarını X,Y koordinatlarıyla birlikte girin', '"Haritayı Değerlendir" tıklayın', 'Renk kodlarını kullanarak sorunlu noktaları tespit edin', 'Bir noktaya tıklayarak detaylı enerji değerlerini görüntüleyin'],
      en: ['Go to "Part Map" tab', 'Enter weld points with X,Y coordinates', 'Click "Evaluate Map"', 'Identify problematic points using color codes', 'Click a point to view detailed energy values'],
    },
    relatedIds: ['energy-multi', 'energy-dashboard'],
  },
  {
    id: 'energy-scenario', icon: 'ES', nav: { tr: 'Senaryo Karşılaştırma', en: 'Scenario Comparison' },
    title: { tr: 'Senaryo Karşılaştırma — Mevcut vs. Önerilen', en: 'Scenario Comparison — Baseline vs. Proposed' },
    purpose: {
      tr: 'Her kaynak noktası için mevcut (temel) ve önerilen enerji değerlerini karşılaştırır.',
      en: 'Compares baseline (current) and proposed energy values for each weld point.'
    },
    tags: ['scenario', 'comparison', 'baseline', 'proposed', 'saving', 'senaryo', 'karşılaştırma'],
    inputs: [
      { name: 'Baseline E_current', unit: 'kJ', desc: { tr: 'Mevcut proses enerji değeri', en: 'Current process energy value' } },
      { name: 'Proposed E_current', unit: 'kJ', desc: { tr: 'Önerilen proses enerji değeri', en: 'Proposed process energy value' } },
      { name: 'Window bounds (optional)', unit: 'kJ', desc: { tr: 'E_min, E_ideal, E_max (opsiyonel — pencere durumu için)', en: 'E_min, E_ideal, E_max (optional — for window status)' } },
    ],
    outputs: [
      { name: 'Per-Point ΔE', unit: 'kJ', desc: { tr: 'Her nokta için enerji değişimi', en: 'Energy change per weld point' } },
      { name: 'Part Totals', unit: 'kJ', desc: { tr: 'Toplam temel ve önerilen enerji; parça enerji azaltımı', en: 'Total baseline and proposed energy; part energy reduction' } },
      { name: 'Annual Savings (EUR/USD)', desc: { tr: 'TAKDİRİ yıllık tasarruf tahmini', en: 'THEORETICAL annual savings estimate' } },
      { name: 'Quality Change', desc: { tr: 'İyileşen / kötüleşen / değişmeyen nokta sayısı', en: 'Count of improved / degraded / unchanged points' } },
    ],
    steps: {
      tr: ['"Senaryo Karşılaştırma" sekmesine gidin', 'Her kaynak noktası için temel ve önerilen E_current değerlerini girin', '"Senaryoları Karşılaştır" tıklayın', 'Senaryo özetinde parça enerji azaltımını inceleyin', 'Nokta başına karşılaştırma tablosunda kötüleşen noktaları kontrol edin'],
      en: ['Go to "Scenario Compare" tab', 'Enter baseline and proposed E_current for each weld point', 'Click "Compare Scenarios"', 'Review part energy reduction in scenario summary', 'Check degraded points in the per-point comparison table'],
    },
    warnings: {
      tr: ['Bu senaryo değerlendirmesidir — optimizasyon değil', 'Kalite sıralaması: IN_WINDOW > ABOVE_MAX > BELOW_MIN > E_CURRENT_ABSENT > NOT_ESTABLISHED', 'Tüm önerilen değerler üretim uygulamasından önce deneysel doğrulama gerektirir'],
      en: ['This is a scenario evaluation — not an optimization', 'Quality rank: IN_WINDOW > ABOVE_MAX > BELOW_MIN > E_CURRENT_ABSENT > NOT_ESTABLISHED', 'All proposed values require experimental validation before production implementation'],
    },
    relatedIds: ['energy-multi', 'energy-dashboard'],
  },
  {
    id: 'energy-import', icon: 'EI', nav: { tr: 'Enerji — İçe Aktar', en: 'Energy — Import' },
    title: { tr: 'Toplu İçe Aktarma — CSV / Excel', en: 'Bulk Import — CSV / Excel' },
    purpose: {
      tr: 'Kaynak noktası enerji verilerini CSV veya Excel dosyasından toplu olarak içe aktarır.',
      en: 'Bulk-imports weld point energy data from CSV or Excel file.'
    },
    tags: ['import', 'CSV', 'Excel', 'bulk', 'içe aktarma'],
    inputs: [
      { name: 'CSV / XLSX File', desc: { tr: 'Zorunlu sütunlar: point_code, group_name, e_current_kj, e_min_kj, e_ideal_kj, e_max_kj', en: 'Required columns: point_code, group_name, e_current_kj, e_min_kj, e_ideal_kj, e_max_kj' } },
      { name: 'validation_note (optional)', desc: { tr: 'Her nokta için isteğe bağlı doğrulama notu', en: 'Optional validation note per point' } },
    ],
    outputs: [
      { name: 'Preview Table', desc: { tr: 'Kabul edilen ve reddedilen satırları gösterir', en: 'Shows accepted and rejected rows' } },
      { name: 'Error Report', desc: { tr: 'Hücre hataları: hata tipi, ham değer, mesaj', en: 'Cell errors: error type, raw value, message' } },
      { name: 'Duplicate Detection', desc: { tr: 'Tekrar eden nokta kodları işaretlenir', en: 'Duplicate point codes flagged' } },
      { name: 'Formula Injection Check', desc: { tr: 'CSV formula injection girişimleri tespit edilir', en: 'CSV formula injection attempts detected' } },
    ],
    steps: {
      tr: ['"İçe Aktar" sekmesine gidin', '"Şablon İndir" ile örnek CSV dosyasını indirin', 'Şablonu verilerinizle doldurun', 'Dosyayı sürükle-bırak ile yükleyin veya seçin', '"Önizleme" bölümünde hataları inceleyin', 'Sorunları düzeltin ve yeniden yükleyin', '"İçe Aktar" düğmesi ile onaylayın'],
      en: ['Go to "Import" tab', 'Click "Download Template" for a sample CSV', 'Fill the template with your data', 'Upload via drag-and-drop or file selector', 'Review errors in the Preview section', 'Fix issues and re-upload', 'Confirm with "Import" button'],
    },
    warnings: {
      tr: ['Onaylamadan önce önizlemeyi mutlaka inceleyin — içe aktarma geri alınamaz', 'Boş değerler ve geçersiz sayılar hücre hatası olarak raporlanır'],
      en: ['Always review the preview before confirming — import cannot be undone', 'Empty values and invalid numbers are reported as cell errors'],
    },
    relatedIds: ['energy-multi', 'energy-dashboard'],
  },
  {
    id: 'energy-export', icon: 'ER', nav: { tr: 'Rapor Dışa Aktar', en: 'Export Report' },
    title: { tr: 'Mühendislik Raporu Dışa Aktarma — PDF / XLSX / CSV', en: 'Engineering Report Export — PDF / XLSX / CSV' },
    purpose: {
      tr: 'Çok noktalı enerji analizini profesyonel PDF, Excel veya CSV raporu olarak dışa aktarır. Tüm raporlar izlenebilirlik için benzersiz bir Rapor ID ve SHA-256 girdi karması içerir.',
      en: 'Exports multi-spot energy analysis as a professional PDF, Excel or CSV report. All reports include a unique Report ID and SHA-256 input hash for traceability.'
    },
    tags: ['export', 'report', 'PDF', 'XLSX', 'CSV', 'rapor', 'dışa aktarma', 'traceability'],
    inputs: [
      { name: 'Format', desc: { tr: 'PDF (sunum/arşiv), XLSX (6 sayfalık detaylı analiz) veya CSV (veri transferi)', en: 'PDF (presentation/archive), XLSX (6-sheet detailed analysis) or CSV (data transfer)' } },
      { name: 'Language / Dil', desc: { tr: 'Rapor dili: EN (İngilizce) veya TR (Türkçe) — tüm başlıklar ve açıklamalar çevrilir', en: 'Report language: EN (English) or TR (Turkish) — all headers and labels are translated' } },
      { name: 'Project ID / Name', desc: { tr: 'İsteğe bağlı proje tanımlayıcısı ve adı — izlenebilirlik bölümünde görünür', en: 'Optional project identifier and name — shown in the traceability section' } },
      { name: 'Part ID', desc: { tr: 'Parça tanımlayıcısı — tüm formatlarda izlenebilirlik için kullanılır', en: 'Part identifier — used for traceability in all formats' } },
      { name: 'Passport ID', desc: { tr: 'Digital Weld Passport referans numarası (opsiyonel) — yalnızca referans; veri sorgulanmaz', en: 'Digital Weld Passport reference number (optional) — reference only; no data is queried' } },
      { name: 'Analyst Name', desc: { tr: 'Raporu hazırlayan analistin adı', en: 'Name of the analyst preparing the report' } },
      { name: 'Report Title', desc: { tr: 'Özel rapor başlığı — boş bırakılırsa "Energy Analysis Report" olarak oluşturulur', en: 'Custom report title — defaults to "Energy Analysis Report" if blank' } },
    ],
    outputs: [
      { name: 'Report File', desc: { tr: 'Seçilen formatta indirilebilir dosya — tarayıcı indirme işlemi otomatik başlar', en: 'Downloadable file in selected format — browser download starts automatically' } },
      { name: 'Report ID', desc: { tr: 'Benzersiz kimlik: SWP-RPT-{YYYYAAGG-SSddss}-{HASH8} — dosya adında görünür', en: 'Unique identifier: SWP-RPT-{YYYYMMDD-HHmmss}-{HASH8} — visible in the filename' } },
      { name: 'Input Hash', desc: { tr: 'SHA-256 girdi karması (ilk 32 karakter) — aynı giriş her zaman aynı karmayı üretir', en: 'SHA-256 input hash (first 32 chars) — same inputs always produce the same hash' } },
      { name: 'XLSX Sheets', desc: { tr: '6 sayfa: Özet, Kaynak Noktaları, Gruplar, Pareto, Finansal, İzlenebilirlik', en: '6 sheets: Summary, Weld Points, Groups, Pareto, Financial, Traceability' } },
    ],
    steps: {
      tr: [
        '"Dışa Aktar / Export" sekmesine gidin',
        'Format seçin: XLSX (detaylı analiz), CSV (veri aktarımı) veya PDF (sunum/arşiv)',
        'Rapor dilini seçin: EN veya TR',
        'İsteğe bağlı meta verileri doldurun (Proje, Parça, Analist, Passport)',
        '"Rapor Oluştur" düğmesine tıklayın — dosya otomatik olarak indirilir',
        'İndirilen dosyanın adını not edin — Rapor ID izlenebilirlik içindir',
        'Finansal değerlerin "TAKDİRİ" etiketiyle sunulduğunu her zaman doğrulayın',
      ],
      en: [
        'Go to the "Export" tab',
        'Select format: XLSX (detailed analysis), CSV (data exchange) or PDF (presentation/archive)',
        'Select report language: EN or TR',
        'Fill in optional metadata (Project, Part, Analyst, Passport)',
        'Click "Generate Report" — file downloads automatically',
        'Note the downloaded filename — the Report ID is used for traceability',
        'Always verify that financial values are presented with the "THEORETICAL" label',
      ],
    },
    example: {
      label: '[SYNTHETIC] SWP-RPT-20261028-143055-A1B2C3D4.xlsx',
      note: {
        tr: '40 kaynak noktası, 4 grup, Proje: BODY-2026, Parça: P-FRONT-001 için oluşturulan XLSX raporu',
        en: 'XLSX report generated for 40 weld points, 4 groups, Project: BODY-2026, Part: P-FRONT-001',
      },
      inputs: [
        { k: 'Format', v: 'XLSX' },
        { k: 'Language', v: 'EN' },
        { k: 'Project', v: 'BODY-2026' },
        { k: 'Part ID', v: 'P-FRONT-001' },
        { k: 'Analyst', v: 'J. Smith' },
      ],
      outputs: [
        { k: 'Report ID', v: 'SWP-RPT-20261028-143055-A1B2C3D4' },
        { k: 'XLSX sheets', v: 'Summary / Weld Points / Groups / Pareto / Financial / Traceability' },
        { k: 'Points exported', v: '40' },
        { k: 'Financial label', v: 'THEORETICAL — not verified savings' },
        { k: 'Input hash', v: 'SHA-256 first 32 chars — deterministic' },
      ],
    },
    warnings: {
      tr: [
        'Tüm finansal değerler TAKDİRİ\'dir — doğrulanmış elektrik veya finansal tasarruf değildir',
        'NOT_ESTABLISHED enerji pencereli noktalarda finansal değerler boş görünür (raporda çizgi olarak gösterilir)',
        'Passport ID yalnızca referans amaçlıdır — rapor Digital Weld Passport verilerini sorgulamaz',
        'PDF temel Latin-1 yazı tiplerini kullanır; Türkçe özel karakterler otomatik olarak dönüştürülür',
        'Rapor veri kaynağı: Gösterge Paneli veya Çok Nokta sekmesindeki mevcut veri',
      ],
      en: [
        'All financial values are THEORETICAL — not verified electricity or financial savings',
        'Points with NOT_ESTABLISHED energy windows show blank (—) financial values in the report',
        'Passport ID is a reference only — the report does not query Digital Weld Passport data',
        'PDF uses basic Latin-1 fonts; Turkish special characters are automatically transliterated',
        'Report data source: current data from the Dashboard or Multi-Spot tab',
      ],
    },
    relatedIds: ['energy-dashboard', 'energy-multi', 'energy-import'],
  },
]

export const GLOSSARY: GlossaryTerm[] = [
  { term: 'E = I²Rt', def: { tr: 'Punta kaynak enerji formülü: E = Akım² × Direnç × Süre', en: 'Spot weld energy formula: Energy = Current² × Resistance × Time' } },
  { term: 'E_min', def: { tr: 'Minimum kabul edilebilir kaynak enerjisi (doğrulanmış deneysel veri gerektirir)', en: 'Minimum acceptable weld energy (requires validated experimental data)' } },
  { term: 'E_ideal', def: { tr: 'Hedef ideal kaynak enerjisi — doğrulanmış deneysel veri gerektirir', en: 'Target ideal weld energy — requires validated experimental data' } },
  { term: 'E_max', def: { tr: 'Maksimum kabul edilebilir kaynak enerjisi (fırlama sınırı)', en: 'Maximum acceptable weld energy (expulsion boundary)' } },
  { term: 'E_current', def: { tr: 'Mevcut ölçülen/tahmin edilen kaynak enerjisi', en: 'Current measured or estimated weld energy' } },
  { term: 'ΔE', def: { tr: 'İmzalı enerji farkı: E_current − E_ideal', en: 'Signed energy difference: E_current − E_ideal' } },
  { term: 'Nugget', def: { tr: 'Punta kaynakta iki sac arasında oluşan eritilmiş ve yeniden katılaşan metal bölgesi', en: 'The melted and resolidified metal zone formed between two sheets in spot welding' } },
  { term: 'Expulsion', def: { tr: 'Fazla ısı ve enerji nedeniyle erimiş metalin saçılması (fırlama)', en: 'Splatter of molten metal caused by excessive heat and energy' } },
  { term: 'Weld Lobe', def: { tr: 'Akım × süre uzayında kabul edilebilir nugget oluşturan güvenli proses penceresi', en: 'Safe process window in current × time space forming acceptable nugget geometry' } },
  { term: 'Taguchi DOE', def: { tr: 'Ortogonal diziler kullanan yapılandırılmış deney tasarımı yöntemi', en: 'Structured design of experiments method using orthogonal arrays' } },
  { term: 'ANOVA', def: { tr: 'Varyans analizi — faktör katkılarını F-istatistiği ile değerlendirir', en: 'Analysis of Variance — evaluates factor contributions via F-statistic' } },
  { term: 'S/N Ratio', def: { tr: 'Sinyal-gürültü oranı — Taguchi\'de istenen sinyali istenmeyen gürültüye karşı optimize eder', en: 'Signal-to-Noise ratio — Taguchi optimization objective balancing signal vs. noise' } },
  { term: 'LTB', def: { tr: 'Büyük iyidir (Larger is Better) — ör. nugget çapı', en: 'Larger is Better S/N objective — e.g. nugget diameter' } },
  { term: 'STB', def: { tr: 'Küçük iyidir (Smaller is Better) — ör. indentasyon derinliği', en: 'Smaller is Better S/N objective — e.g. indentation depth' } },
  { term: 'NTB', def: { tr: 'Nominal en iyi (Nominal is Best) — ör. kaynak süresi hedefi', en: 'Nominal is Best S/N objective — e.g. weld time target' } },
  { term: '2T / 3T', def: { tr: '2 veya 3 sac katmanı içeren sac paketi', en: 'Sheet stack with 2 or 3 metal layers' } },
  { term: 'Pareto Principle', def: { tr: 'Sonuçların %80\'i genellikle nedenlerin %20\'sinden kaynaklanır (80/20 kuralı)', en: '80% of outcomes typically come from 20% of causes (80/20 rule)' } },
  { term: 'RMS Current', def: { tr: 'Ortalama karesel kök akım — AC kaynaklar için efektif ısıtma değeri', en: 'Root Mean Square current — effective heating value for AC welding sources' } },
]

// ── SVG Diagrams ─────────────────────────────────────────────────────────────
function RswProcessDiagram() {
  return (
    <svg viewBox="0 0 340 130" style={{ width: '100%', maxWidth: 340, display: 'block' }} aria-label="RSW process schematic">
      <text x="155" y="11" style={{ fontSize: 8, fill: 'var(--text-secondary)' }}>F ↓</text>
      <rect x="110" y="14" width="90" height="18" rx="3" style={{ fill: 'var(--bg-surface-2)', stroke: 'var(--border)', strokeWidth: 1.5 }} />
      <text x="130" y="26" style={{ fontSize: 8, fill: 'var(--text-primary)' }}>Electrode (top)</text>
      <rect x="125" y="32" width="60" height="10" style={{ fill: '#888', opacity: 0.5 }} />
      <rect x="55" y="42" width="200" height="13" rx="2" style={{ fill: '#7bb8d4', opacity: 0.8 }} />
      <text x="262" y="52" style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>Sheet 1</text>
      <rect x="55" y="55" width="200" height="13" rx="2" style={{ fill: '#7bb8d4', opacity: 0.8 }} />
      <text x="262" y="65" style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>Sheet 2</text>
      <ellipse cx="155" cy="55" rx="22" ry="9" style={{ fill: '#f0b429', opacity: 0.9 }} />
      <text x="145" y="58" style={{ fontSize: 7, fill: '#7a5800', fontWeight: 'bold' }}>Nugget</text>
      <rect x="125" y="68" width="60" height="10" style={{ fill: '#888', opacity: 0.5 }} />
      <rect x="110" y="78" width="90" height="18" rx="3" style={{ fill: 'var(--bg-surface-2)', stroke: 'var(--border)', strokeWidth: 1.5 }} />
      <text x="125" y="90" style={{ fontSize: 8, fill: 'var(--text-primary)' }}>Electrode (bottom)</text>
      <text x="155" y="105" style={{ fontSize: 8, fill: 'var(--text-secondary)' }}>F ↑</text>
      <text x="8" y="56" style={{ fontSize: 8, fill: '#3b82f6' }}>I →</text>
      <line x1="28" y1="55" x2="52" y2="55" style={{ stroke: '#3b82f6', strokeWidth: 1.5, strokeDasharray: '3 2' }} />
      <line x1="258" y1="55" x2="280" y2="55" style={{ stroke: '#3b82f6', strokeWidth: 1.5, strokeDasharray: '3 2' }} />
      <text x="284" y="56" style={{ fontSize: 8, fill: '#3b82f6' }}>→ I</text>
    </svg>
  )
}

function EnergyWindowDiagram() {
  return (
    <svg viewBox="0 0 340 80" style={{ width: '100%', maxWidth: 340, display: 'block' }} aria-label="Energy window diagram">
      <rect x="20" y="20" width="60" height="22" style={{ fill: '#f85149', opacity: 0.35 }} />
      <rect x="80" y="20" width="130" height="22" style={{ fill: '#34d058', opacity: 0.30 }} />
      <rect x="210" y="20" width="60" height="22" style={{ fill: '#f0b429', opacity: 0.35 }} />
      <text x="30" y="34" style={{ fontSize: 7, fill: '#f85149', fontWeight: 'bold' }}>Below Min</text>
      <text x="115" y="34" style={{ fontSize: 7, fill: '#34d058', fontWeight: 'bold' }}>In Window</text>
      <text x="215" y="34" style={{ fontSize: 7, fill: '#f0b429', fontWeight: 'bold' }}>Above Max</text>
      <line x1="80" y1="14" x2="80" y2="48" style={{ stroke: 'var(--text-secondary)', strokeWidth: 1.5, strokeDasharray: '3 2' }} />
      <line x1="210" y1="14" x2="210" y2="48" style={{ stroke: 'var(--text-secondary)', strokeWidth: 1.5, strokeDasharray: '3 2' }} />
      <text x="71" y="12" style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>E_min</text>
      <text x="200" y="12" style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>E_max</text>
      <line x1="145" y1="14" x2="145" y2="48" style={{ stroke: '#58a6ff', strokeWidth: 1.5 }} />
      <text x="132" y="12" style={{ fontSize: 7, fill: '#58a6ff' }}>E_ideal</text>
      <polygon points="163,16 159,8 167,8" style={{ fill: '#f0b429' }} />
      <line x1="163" y1="48" x2="163" y2="20" style={{ stroke: '#f0b429', strokeWidth: 2 }} />
      <text x="155" y="62" style={{ fontSize: 7, fill: '#f0b429' }}>E_cur</text>
      <text x="40" y="72" style={{ fontSize: 8, fill: 'var(--text-tertiary)' }}>← Energy →</text>
    </svg>
  )
}

function WeldLobeDiagram() {
  return (
    <svg viewBox="0 0 300 140" style={{ width: '100%', maxWidth: 300, display: 'block' }} aria-label="Weld lobe diagram">
      <text x="2" y="72" style={{ fontSize: 8, fill: 'var(--text-secondary)', writingMode: 'vertical-rl', transform: 'rotate(180 12 72)' }}>Current (kA)</text>
      <line x1="30" y1="10" x2="30" y2="120" style={{ stroke: 'var(--text-secondary)', strokeWidth: 1 }} />
      <line x1="30" y1="120" x2="270" y2="120" style={{ stroke: 'var(--text-secondary)', strokeWidth: 1 }} />
      <text x="140" y="135" style={{ fontSize: 8, fill: 'var(--text-secondary)' }}>Weld Time (cycles) →</text>
      <polygon points="30,10 270,10 270,40 200,50 130,60 80,80 50,100 30,115 30,10" style={{ fill: '#f85149', opacity: 0.25 }} />
      <polygon points="30,115 50,100 80,80 130,60 200,50 270,40 270,120 30,120" style={{ fill: '#f85149', opacity: 0.20 }} />
      <polygon points="50,100 80,80 130,60 200,50 270,40 270,80 220,90 160,95 100,100 70,108" style={{ fill: '#34d058', opacity: 0.30 }} />
      <text x="90" y="50" style={{ fontSize: 8, fill: '#f85149', fontWeight: 'bold' }}>Expulsion</text>
      <text x="100" y="80" style={{ fontSize: 8, fill: '#34d058', fontWeight: 'bold' }}>Safe Window</text>
      <text x="100" y="110" style={{ fontSize: 8, fill: '#f85149', fontWeight: 'bold' }}>Insufficient Fusion</text>
      <circle cx="155" cy="75" r="4" style={{ fill: '#f0b429', stroke: 'var(--text-primary)', strokeWidth: 1.5 }} />
      <text x="162" y="73" style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>Optimum</text>
    </svg>
  )
}

function TaguchiL9Diagram() {
  const cols = ['Run', 'A', 'B', 'C', 'D']
  const rows = [
    [1, 1, 1, 1, 1], [2, 1, 2, 2, 2], [3, 1, 3, 3, 3],
    [4, 2, 1, 2, 3], [5, 2, 2, 3, 1], [6, 2, 3, 1, 2],
    [7, 3, 1, 3, 2], [8, 3, 2, 1, 3], [9, 3, 3, 2, 1],
  ]
  const lvlColor: Record<number, string> = { 1: '#3b82f6', 2: '#f59e0b', 3: '#10b981' }
  return (
    <svg viewBox="0 0 260 130" style={{ width: '100%', maxWidth: 260, display: 'block' }} aria-label="L9 orthogonal array">
      {cols.map((h, i) => (
        <text key={h} x={20 + i * 48} y={14} style={{ fontSize: 9, fill: 'var(--text-secondary)', fontWeight: 'bold' }}>{h}</text>
      ))}
      {rows.map((row, ri) => (
        row.map((v, ci) => (
          <g key={`${ri}-${ci}`}>
            <rect x={14 + ci * 48} y={18 + ri * 12} width={42} height={11} rx={2}
              style={{ fill: ci === 0 ? 'var(--bg-surface-2)' : lvlColor[v as number], opacity: ci === 0 ? 1 : 0.4 }} />
            <text x={31 + ci * 48} y={27 + ri * 12} textAnchor="middle"
              style={{ fontSize: 8, fill: ci === 0 ? 'var(--text-tertiary)' : lvlColor[v as number] }}>{v}</text>
          </g>
        ))
      ))}
    </svg>
  )
}

function MultiSpotDiagram() {
  const pts = [
    { x: 60, y: 40, st: '#34d058' }, { x: 120, y: 35, st: '#34d058' },
    { x: 180, y: 40, st: '#f0b429' }, { x: 240, y: 38, st: '#34d058' },
    { x: 70, y: 80, st: '#f85149' }, { x: 150, y: 85, st: '#34d058' },
    { x: 220, y: 80, st: '#34d058' }, { x: 100, y: 60, st: '#6b7689' },
  ]
  return (
    <svg viewBox="0 0 310 120" style={{ width: '100%', maxWidth: 310, display: 'block' }} aria-label="Multi-spot part map">
      <rect x="20" y="20" width="270" height="80" rx="8" style={{ fill: 'none', stroke: 'var(--border)', strokeWidth: 2 }} />
      <text x="130" y="14" style={{ fontSize: 8, fill: 'var(--text-tertiary)' }}>Part outline (schematic)</text>
      {pts.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r={7} style={{ fill: p.st, opacity: 0.8 }} />
          <text x={p.x} y={p.y + 3} textAnchor="middle" style={{ fontSize: 6, fill: '#fff', fontWeight: 'bold' }}>{i + 1}</text>
        </g>
      ))}
      <circle cx={40} cy={108} r={5} style={{ fill: '#34d058', opacity: 0.8 }} />
      <text x={50} y={112} style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>In Window</text>
      <circle cx={105} cy={108} r={5} style={{ fill: '#f0b429', opacity: 0.8 }} />
      <text x={115} y={112} style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>Above Max</text>
      <circle cx={175} cy={108} r={5} style={{ fill: '#f85149', opacity: 0.8 }} />
      <text x={185} y={112} style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>Below Min</text>
      <circle cx={240} cy={108} r={5} style={{ fill: '#6b7689', opacity: 0.8 }} />
      <text x={250} y={112} style={{ fontSize: 7, fill: 'var(--text-secondary)' }}>Not Est.</text>
    </svg>
  )
}

function DiagramFor({ id }: { id: HelpModule['diagram'] }) {
  if (id === 'rsw') return <RswProcessDiagram />
  if (id === 'energy-window') return <EnergyWindowDiagram />
  if (id === 'weld-lobe') return <WeldLobeDiagram />
  if (id === 'taguchi') return <TaguchiL9Diagram />
  if (id === 'multi-spot') return <MultiSpotDiagram />
  return null
}

// ── Main component ────────────────────────────────────────────────────────────
const CARD_STYLE: React.CSSProperties = {
  background: 'var(--bg-surface)', border: '1px solid var(--border)',
  borderRadius: 'var(--r-lg)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)',
}
const SECTION_TITLE: React.CSSProperties = {
  fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', fontWeight: 700,
  textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--sp-2)',
}
const TAG_STYLE: React.CSSProperties = {
  display: 'inline-block', background: 'var(--bg-surface-2)', color: 'var(--accent)',
  borderRadius: 4, padding: '2px 7px', fontSize: 'var(--fs-xs)', marginRight: 4, marginBottom: 4,
}
const WARN_ITEM: React.CSSProperties = {
  background: 'color-mix(in srgb, var(--warn-soft) 60%, transparent)',
  border: '1px solid color-mix(in srgb, var(--warn) 40%, transparent)',
  borderRadius: 4, padding: '4px 10px', fontSize: 'var(--fs-sm)', marginBottom: 4, color: 'var(--warn)',
}

export function HelpCenterPage() {
  const { lang } = useAppLanguage()
  const [selected, setSelected] = useState<string>('dashboard')
  const [query, setQuery] = useState('')
  const [showGlossary, setShowGlossary] = useState(false)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return HELP_MODULES
    return HELP_MODULES.filter(m =>
      tx(lang, m.nav).toLowerCase().includes(q) ||
      tx(lang, m.title).toLowerCase().includes(q) ||
      tx(lang, m.purpose).toLowerCase().includes(q) ||
      m.tags.some(t => t.includes(q)) ||
      (m.inputs ?? []).some(f => f.name.toLowerCase().includes(q)) ||
      (m.outputs ?? []).some(f => f.name.toLowerCase().includes(q))
    )
  }, [query, lang])

  const filteredGlossary = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return GLOSSARY
    return GLOSSARY.filter(g =>
      g.term.toLowerCase().includes(q) ||
      tx(lang, g.def).toLowerCase().includes(q)
    )
  }, [query, lang])

  const module = HELP_MODULES.find(m => m.id === selected) ?? HELP_MODULES[0]

  return (
    <div className="page active">
      <div className="ws-kicker">
        {lang === 'tr' ? 'SpotWeldPro AI · Mühendislik Yardım Merkezi' : 'SpotWeldPro AI · Engineering Help Center'}
      </div>
      <header className="page-header">
        <div>
          <h1>{lang === 'tr' ? 'Mühendislik Yardım Merkezi' : 'Engineering Help Center'}</h1>
          <p className="subtitle">
            {lang === 'tr'
              ? 'Tüm modüller için kapsamlı mühendislik rehberi — TR/EN ikidilli'
              : 'Comprehensive engineering guide for all modules — TR/EN bilingual'}
          </p>
        </div>
      </header>

      {/* Search */}
      <div style={{ marginBottom: 'var(--sp-4)' }}>
        <input
          type="search"
          placeholder={lang === 'tr' ? '🔍 Modül, terim veya parametre ara…' : '🔍 Search module, term or parameter…'}
          value={query}
          onChange={e => setQuery(e.target.value)}
          aria-label={lang === 'tr' ? 'Yardım içeriği ara' : 'Search help content'}
          style={{
            width: '100%', maxWidth: 480, padding: '8px 14px',
            background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
            borderRadius: 'var(--r-md)', color: 'var(--text-primary)', fontSize: 'var(--fs-sm)',
          }}
        />
        {query && (
          <span style={{ marginLeft: 8, fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
            {filtered.length} {lang === 'tr' ? 'modül' : 'module'}{filtered.length !== 1 ? 's' : ''} · {filteredGlossary.length} {lang === 'tr' ? 'terim' : 'term'}{filteredGlossary.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 'var(--sp-5)', alignItems: 'start' }}>
        {/* Nav panel */}
        <nav aria-label={lang === 'tr' ? 'Modül listesi' : 'Module list'}>
          <div style={{ ...CARD_STYLE, padding: 'var(--sp-2)' }}>
            {filtered.map(m => (
              <button
                key={m.id}
                type="button"
                onClick={() => { setSelected(m.id); setShowGlossary(false) }}
                aria-current={selected === m.id && !showGlossary ? 'page' : undefined}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8, width: '100%', textAlign: 'left',
                  padding: '6px 10px', borderRadius: 'var(--r-md)', marginBottom: 2,
                  background: selected === m.id && !showGlossary ? 'var(--accent-soft)' : 'transparent',
                  border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontSize: 'var(--fs-sm)',
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'var(--bg-surface-2)', borderRadius: 3, padding: '1px 4px', color: 'var(--text-tertiary)', flexShrink: 0 }}>{m.icon}</span>
                <span>{tx(lang, m.nav)}</span>
              </button>
            ))}
            {filtered.length === 0 && (
              <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', padding: '6px 10px' }}>
                {lang === 'tr' ? 'Sonuç yok' : 'No results'}
              </p>
            )}
            <div style={{ height: 1, background: 'var(--border)', margin: '6px 0' }} />
            <button
              type="button"
              onClick={() => setShowGlossary(true)}
              aria-current={showGlossary ? 'page' : undefined}
              style={{
                display: 'flex', alignItems: 'center', gap: 8, width: '100%', textAlign: 'left',
                padding: '6px 10px', borderRadius: 'var(--r-md)',
                background: showGlossary ? 'var(--accent-soft)' : 'transparent',
                border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontSize: 'var(--fs-sm)',
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'var(--bg-surface-2)', borderRadius: 3, padding: '1px 4px', color: 'var(--text-tertiary)' }}>GL</span>
              <span>{lang === 'tr' ? 'Mühendislik Sözlüğü' : 'Engineering Glossary'}</span>
            </button>
          </div>
          <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginTop: 'var(--sp-2)' }}>
            {HELP_MODULES.length} {lang === 'tr' ? 'modül dokümante edildi' : 'modules documented'}
          </p>
        </nav>

        {/* Content panel */}
        <main aria-label={lang === 'tr' ? 'Yardım içeriği' : 'Help content'}>
          {showGlossary ? (
            <div>
              <h2 style={{ marginBottom: 'var(--sp-3)' }}>{lang === 'tr' ? 'Mühendislik Sözlüğü' : 'Engineering Glossary'}</h2>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--sp-4)' }}>
                {lang === 'tr'
                  ? 'Punta kaynak mühendisliğinde kullanılan temel terimler ve tanımlar.'
                  : 'Key terms and definitions used in resistance spot welding engineering.'}
              </p>
              <dl>
                {filteredGlossary.map(g => (
                  <div key={g.term} style={{ ...CARD_STYLE, marginBottom: 'var(--sp-2)' }}>
                    <dt style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent)', marginBottom: 4 }}>{g.term}</dt>
                    <dd style={{ margin: 0, fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)' }}>{tx(lang, g.def)}</dd>
                  </div>
                ))}
                {filteredGlossary.length === 0 && (
                  <p style={{ color: 'var(--text-tertiary)', fontSize: 'var(--fs-sm)' }}>{lang === 'tr' ? 'Sonuç yok.' : 'No results.'}</p>
                )}
              </dl>
            </div>
          ) : (
            <article>
              {/* Header */}
              <div style={{ ...CARD_STYLE, borderColor: 'var(--accent)', background: 'color-mix(in srgb, var(--accent-soft) 30%, var(--bg-surface))' }}>
                <h2 style={{ marginBottom: 'var(--sp-2)' }}>{tx(lang, module.title)}</h2>
                <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--sp-3)' }}>{tx(lang, module.purpose)}</p>
                <div>{module.tags.map(t => <span key={t} style={TAG_STYLE}>{t}</span>)}</div>
                {module.standards && (
                  <div style={{ marginTop: 'var(--sp-2)', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
                    {module.standards.map(s => <span key={s} style={{ marginRight: 10 }}>📋 {s}</span>)}
                  </div>
                )}
              </div>

              {/* Diagram */}
              {module.diagram && (
                <div style={CARD_STYLE}>
                  <p style={SECTION_TITLE}>{lang === 'tr' ? 'Mühendislik Şeması' : 'Engineering Diagram'}</p>
                  <div style={{ background: 'var(--bg-surface-2)', borderRadius: 'var(--r-md)', padding: 'var(--sp-3)', textAlign: 'center' }}>
                    <DiagramFor id={module.diagram} />
                  </div>
                  <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', marginTop: 'var(--sp-2)', fontStyle: 'italic' }}>
                    {lang === 'tr' ? 'Şematik temsil — ölçeğe göre değildir.' : 'Schematic representation — not to scale.'}
                  </p>
                </div>
              )}

              {/* Inputs */}
              {module.inputs && module.inputs.length > 0 && (
                <div style={CARD_STYLE}>
                  <p style={SECTION_TITLE}>{lang === 'tr' ? 'Girdi Parametreleri' : 'Input Parameters'}</p>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                          {[lang === 'tr' ? 'Parametre' : 'Parameter', lang === 'tr' ? 'Birim' : 'Unit', lang === 'tr' ? 'Aralık' : 'Range', lang === 'tr' ? 'Açıklama' : 'Description'].map(h => (
                            <th key={h} style={{ padding: '5px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--fs-xs)' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {module.inputs.map(f => (
                          <tr key={f.name} style={{ borderBottom: '1px solid var(--border)' }}>
                            <td style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>{f.name}</td>
                            <td style={{ padding: '4px 8px', color: 'var(--text-tertiary)' }}>{f.unit ?? '—'}</td>
                            <td style={{ padding: '4px 8px', color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)' }}>{f.range ?? '—'}</td>
                            <td style={{ padding: '4px 8px', color: 'var(--text-secondary)' }}>{tx(lang, f.desc)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Outputs */}
              {module.outputs && module.outputs.length > 0 && (
                <div style={CARD_STYLE}>
                  <p style={SECTION_TITLE}>{lang === 'tr' ? 'Çıktılar ve Sonuçlar' : 'Outputs & Results'}</p>
                  <div style={{ display: 'grid', gap: 'var(--sp-2)', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
                    {module.outputs.map(o => (
                      <div key={o.name} style={{ background: 'var(--bg-surface-2)', borderRadius: 'var(--r-md)', padding: 'var(--sp-2) var(--sp-3)' }}>
                        <div style={{ fontWeight: 600, fontSize: 'var(--fs-sm)', marginBottom: 3 }}>{o.name}{o.unit ? <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}> ({o.unit})</span> : null}</div>
                        <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)' }}>{tx(lang, o.desc)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Step-by-step guide */}
              <div style={CARD_STYLE}>
                <p style={SECTION_TITLE}>{lang === 'tr' ? 'Adım Adım Kullanım' : 'Step-by-Step Usage'}</p>
                <ol style={{ paddingLeft: 'var(--sp-5)', margin: 0 }}>
                  {txl(lang, module.steps).map((s, i) => (
                    <li key={i} style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--sp-2)', lineHeight: 1.6 }}>{s}</li>
                  ))}
                </ol>
              </div>

              {/* Example */}
              {module.example && (
                <div style={{ ...CARD_STYLE, borderColor: 'var(--warn)', background: 'color-mix(in srgb, var(--warn-soft) 20%, var(--bg-surface))' }}>
                  <p style={{ ...SECTION_TITLE, color: 'var(--warn)' }}>
                    ⚗ {lang === 'tr' ? 'İnteraktif Örnek' : 'Interactive Example'} — {module.example.label}
                  </p>
                  <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--warn)', marginBottom: 'var(--sp-3)', fontStyle: 'italic' }}>
                    ⚠ {tx(lang, module.example.note)}
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-3)' }}>
                    <div>
                      <p style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 6 }}>{lang === 'tr' ? 'GİRDİLER' : 'INPUTS'}</p>
                      {module.example.inputs.map(p => (
                        <div key={p.k} style={{ display: 'flex', gap: 8, marginBottom: 4, fontSize: 'var(--fs-xs)' }}>
                          <span style={{ color: 'var(--text-tertiary)', minWidth: 90 }}>{p.k}:</span>
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{p.v}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <p style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 6 }}>{lang === 'tr' ? 'ÇIKTILAR' : 'OUTPUTS'}</p>
                      {module.example.outputs.map(p => (
                        <div key={p.k} style={{ display: 'flex', gap: 8, marginBottom: 4, fontSize: 'var(--fs-xs)' }}>
                          <span style={{ color: 'var(--text-tertiary)', minWidth: 90 }}>{p.k}:</span>
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{p.v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Warnings */}
              {module.warnings && txl(lang, module.warnings).length > 0 && (
                <div style={CARD_STYLE}>
                  <p style={{ ...SECTION_TITLE, color: 'var(--danger)' }}>
                    ⚠ {lang === 'tr' ? 'Mühendislik Uyarıları ve Sınırlamalar' : 'Engineering Warnings & Limitations'}
                  </p>
                  {txl(lang, module.warnings).map((w, i) => (
                    <div key={i} style={WARN_ITEM}>{w}</div>
                  ))}
                </div>
              )}

              {/* Related modules */}
              {module.relatedIds.length > 0 && (
                <div style={{ ...CARD_STYLE, marginBottom: 0 }}>
                  <p style={SECTION_TITLE}>{lang === 'tr' ? 'İlgili Modüller' : 'Related Modules'}</p>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {module.relatedIds.map(rid => {
                      const rel = HELP_MODULES.find(m => m.id === rid)
                      if (!rel) return null
                      return (
                        <button key={rid} type="button" onClick={() => setSelected(rid)}
                          style={{ background: 'var(--bg-surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)', padding: '4px 12px', fontSize: 'var(--fs-xs)', cursor: 'pointer', color: 'var(--text-primary)' }}>
                          <span style={{ color: 'var(--text-tertiary)', marginRight: 4 }}>{rel.icon}</span>
                          {tx(lang, rel.nav)}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </article>
          )}
        </main>
      </div>

      {/* Module coverage matrix */}
      <div style={{ marginTop: 'var(--sp-6)' }}>
        <h3 style={{ marginBottom: 'var(--sp-3)' }}>{lang === 'tr' ? 'Modül Kapsam Matrisi' : 'Module Coverage Matrix'}</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-xs)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {[lang === 'tr' ? 'Modül' : 'Module', lang === 'tr' ? 'Girdi' : 'Inputs', lang === 'tr' ? 'Çıktı' : 'Outputs', lang === 'tr' ? 'Adımlar' : 'Steps', lang === 'tr' ? 'Örnek' : 'Example', lang === 'tr' ? 'Uyarı' : 'Warnings', lang === 'tr' ? 'Diyagram' : 'Diagram'].map(h => (
                  <th key={h} style={{ padding: '5px 8px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {HELP_MODULES.map(m => (
                <tr key={m.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '4px 8px', fontWeight: 600 }}>
                    <button type="button" onClick={() => { setSelected(m.id); setShowGlossary(false) }}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', textAlign: 'left', fontWeight: 600, fontSize: 'var(--fs-xs)' }}>
                      {tx(lang, m.nav)}
                    </button>
                  </td>
                  {[!!(m.inputs?.length), !!(m.outputs?.length), !!(m.steps.en.length), !!m.example, !!(m.warnings?.en.length), !!m.diagram].map((v, i) => (
                    <td key={i} style={{ padding: '4px 8px', color: v ? '#34d058' : 'var(--text-tertiary)' }}>{v ? '✓' : '—'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
