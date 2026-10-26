"""
model_catalog.py — SpotWeldPro AI çok modelli nugget tahmin kataloğu.

Her model için: kimlik, yönetişim durumu, kapasite tipi, girdi sözleşmesi,
geçerlilik alanı ve doğrulama kanıtı sabit olarak tanımlanır.

ÖNEMLI ANLAM KURALLARI:
  - REFERENCE_THRESHOLD : Ölçülen nugget çapı tahmini DEĞİL; OEM/standart kabul kriteri.
  - DESIGN_METHOD       : Taguchi / RSM tasarım fazı — nugget tahmini yapmaz.
  - STATISTICAL_ANALYSIS: ANOVA — faktör analizi aracıdır, öngörücü değildir.
  - NUGGET_PREDICTOR    : Metalografik veya kaliper ölçüme karşı doğrulanabilir çap tahmini.
  - REJECTED modellar   : Üretim öngörüsünde hiçbir zaman kullanılamaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import List, Optional


class ModelCapabilityType(StrEnum):
    NUGGET_PREDICTOR     = "NUGGET_PREDICTOR"
    REFERENCE_THRESHOLD  = "REFERENCE_THRESHOLD"
    DESIGN_METHOD        = "DESIGN_METHOD"
    STATISTICAL_ANALYSIS = "STATISTICAL_ANALYSIS"
    PHYSICS_SIMULATION   = "PHYSICS_SIMULATION"


class ModelGovernanceStatus(StrEnum):
    NOT_AVAILABLE           = "NOT_AVAILABLE"
    EXPERIMENTAL            = "EXPERIMENTAL"
    UNDER_REVIEW            = "UNDER_REVIEW"
    CONDITIONALLY_VALIDATED = "CONDITIONALLY_VALIDATED"
    VALIDATED               = "VALIDATED"
    REJECTED                = "REJECTED"
    DEPRECATED              = "DEPRECATED"


class ModelBasis(StrEnum):
    OEM_TABLE              = "OEM_TABLE"
    DERIVED_CRITERION      = "DERIVED_CRITERION"
    LINEAR_REGRESSION      = "LINEAR_REGRESSION"
    POLYNOMIAL_REGRESSION  = "POLYNOMIAL_REGRESSION"
    RSM_POLYNOMIAL         = "RSM_POLYNOMIAL"
    EMPIRICAL_POWER_LAW    = "EMPIRICAL_POWER_LAW"
    TAGUCHI_DOE            = "TAGUCHI_DOE"
    ANOVA                  = "ANOVA"
    GAUSSIAN_PROCESS       = "GAUSSIAN_PROCESS"
    GRADIENT_BOOSTING      = "GRADIENT_BOOSTING"
    PHYSICS_HYBRID         = "PHYSICS_HYBRID"
    NEURAL_PINN            = "NEURAL_PINN"


@dataclass(frozen=True)
class ValidationEvidence:
    n_train: Optional[int] = None
    n_test: Optional[int] = None
    rmse_mm: Optional[float] = None
    mae_mm: Optional[float] = None
    bias_mm: Optional[float] = None
    r2: Optional[float] = None
    dataset_name: Optional[str] = None
    measurement_basis: Optional[str] = None
    notes_tr: Optional[str] = None
    notes_en: Optional[str] = None


@dataclass(frozen=True)
class CatalogEntry:
    model_id: str
    version: str
    name_tr: str
    name_en: str
    model_basis: str
    capability_type: str
    governance_status: str
    measurement_target: str
    supported_materials: tuple
    thickness_range_mm: tuple
    mandatory_inputs: tuple
    optional_inputs: tuple
    uncertainty_supported: bool
    router_active: bool
    not_available_reason_tr: Optional[str]
    not_available_reason_en: Optional[str]
    validation_evidence: Optional[ValidationEvidence]
    rejection_reason_tr: Optional[str]
    rejection_reason_en: Optional[str]
    notes_tr: str
    notes_en: str


MODEL_CATALOG: List[CatalogEntry] = [

    # ── M01: OEM Referans Tablosu ────────────────────────────────────────────
    CatalogEntry(
        model_id="oem_table",
        version="1.0",
        name_tr="OEM Referans Tablosu",
        name_en="OEM Reference Table",
        model_basis=ModelBasis.OEM_TABLE,
        capability_type=ModelCapabilityType.REFERENCE_THRESHOLD,
        governance_status=ModelGovernanceStatus.VALIDATED,
        measurement_target="acceptance_criterion_mm",
        supported_materials=("Düşük / Orta Karbonlu Çelik",),
        thickness_range_mm=(0.5, 2.75),
        mandatory_inputs=("thickness_mm",),
        optional_inputs=(),
        uncertainty_supported=False,
        router_active=True,
        not_available_reason_tr=None,
        not_available_reason_en=None,
        validation_evidence=ValidationEvidence(
            measurement_basis="oem_criterion",
            notes_tr="13 noktalı kalınlık tablosu; interpolasyon ile dmin ve dopt verir. "
                     "Ölçülen nugget çapı değildir — OEM standart kabul kriteri.",
            notes_en="13-point thickness table; interpolates dmin and dopt. "
                     "Not a measured nugget diameter — OEM acceptance criterion.",
        ),
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="engine.py::interp() — yalnızca düşük/orta karbonlu çelik için etkin. "
                 "Tahmin değil; referans eşiği.",
        notes_en="engine.py::interp() — active for mild steel only. "
                 "Not a prediction; a reference threshold.",
    ),

    # ── M02: 4√t Literatür Kriteri ──────────────────────────────────────────
    CatalogEntry(
        model_id="literature_4sqrt_t",
        version="1.0",
        name_tr="4√t Literatür Kriteri",
        name_en="4√t Literature Criterion",
        model_basis=ModelBasis.DERIVED_CRITERION,
        capability_type=ModelCapabilityType.REFERENCE_THRESHOLD,
        governance_status=ModelGovernanceStatus.VALIDATED,
        measurement_target="acceptance_criterion_mm",
        supported_materials=("Tümü",),
        thickness_range_mm=(0.3, 10.0),
        mandatory_inputs=("thickness_mm",),
        optional_inputs=(),
        uncertainty_supported=False,
        router_active=True,
        not_available_reason_tr=None,
        not_available_reason_en=None,
        validation_evidence=ValidationEvidence(
            measurement_basis="oem_criterion",
            notes_tr="Yayımlanan standart minimum nugget kriteri. "
                     "Ölçülen çap değildir; malzeme- ve kalınlık-bağımsız alt sınır.",
            notes_en="Published standard minimum nugget criterion. "
                     "Not a measured diameter; material- and thickness-independent lower bound.",
        ),
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="models.py::literature_4sqrt_t() — tüm malzemelere uygulanabilir. "
                 "Tahmin değil; destekleyici minimum kriter.",
        notes_en="models.py::literature_4sqrt_t() — applicable to all materials. "
                 "Not a prediction; supplementary minimum criterion.",
    ),

    # ── M03: Weld Lobe Surrogat v0.9 ────────────────────────────────────────
    CatalogEntry(
        model_id="weld_lobe_v0_9",
        version="0.9",
        name_tr="Weld Lobe Surrogat v0.9",
        name_en="Weld Lobe Surrogate v0.9",
        model_basis=ModelBasis.EMPIRICAL_POWER_LAW,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.REJECTED,
        measurement_target="nugget_diameter_mm",
        supported_materials=("Düşük / Orta Karbonlu Çelik", "Paslanmaz Çelik",
                             "AHSS / UHSS / PHS", "Galvanizli / Kaplamalı Çelik",
                             "Alüminyum Alaşımları"),
        thickness_range_mm=(0.3, 10.0),
        mandatory_inputs=("material_family", "thickness_mm", "current_ka",
                          "weld_cycles", "force_kn"),
        optional_inputs=(),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr=None,
        not_available_reason_en=None,
        validation_evidence=ValidationEvidence(
            n_train=0,
            n_test=9,
            rmse_mm=11.34,
            mae_mm=10.66,
            bias_mm=10.66,
            r2=-276.6,
            dataset_name="Khuenkaew 2019 (Metals 9, 710) — 9 satır, SUS316L+SUS425, 1.5mm",
            measurement_basis="metallographic",
            notes_tr="Pilot değerlendirme: R²=−276.6; model ortalama tahminden 277× daha kötü. "
                     "Zaman üssü 0.45 >> gözlenen ~0.04–0.08. Patlama mekanizması yok. "
                     "Ölçek sabiti 0.24 kalibre edilmemiş (gözlenen ≈0.090).",
            notes_en="Pilot evaluation: R²=−276.6; model is 277× worse than mean prediction. "
                     "Time exponent 0.45 >> observed ~0.04–0.08. No expulsion mechanism. "
                     "Scale constant 0.24 uncalibrated (observed ≈0.090).",
        ),
        rejection_reason_tr="WELD-LOBE-ROOT-CAUSE-01 pilot değerlendirmesi: RMSE=11.34mm, "
                            "bias=+10.66mm, R²=−276.6 (9 Khuenkaew satırı). "
                            "Zaman üssü ve ölçek sabiti gerçek davranıştan kopuk. "
                            "Üretim nugget tahmini için kullanılamaz.",
        rejection_reason_en="WELD-LOBE-ROOT-CAUSE-01 pilot evaluation: RMSE=11.34mm, "
                            "bias=+10.66mm, R²=−276.6 (9 Khuenkaew rows). "
                            "Time exponent and scale constant disconnected from real behavior. "
                            "Cannot be used for production nugget prediction.",
        notes_tr="weld_lobe.py::estimate_nugget() — doğrulama için REDDEDILDI. "
                 "Bölge görselleştirmesi askıya alındı. Tarihsel başvuru için korunuyor.",
        notes_en="weld_lobe.py::estimate_nugget() — REJECTED for validation. "
                 "Zone visualization suspended. Preserved for historical reference.",
    ),

    # ── M04: Model-4 DOE Polinom ─────────────────────────────────────────────
    CatalogEntry(
        model_id="model4_doe_polynomial",
        version="4.0-experimental",
        name_tr="Model-4 DOE Polinom",
        name_en="Model-4 DOE Polynomial",
        model_basis=ModelBasis.RSM_POLYNOMIAL,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.EXPERIMENTAL,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("Current_kA", "Force_kN", "Time_cycle",
                          "Cooling_cycle", "Sequence_cycle",
                          "Holding_cycle", "SheetThick_mm"),
        optional_inputs=(),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr="API router devre dışı (main.py'e kayıtlı değil). "
                                "Cooling, Sequence ve Holding girdileri mevcut 806-kayıt "
                                "doğrulama veri setinde yapısal olarak eksik; "
                                "doğrulama şu an mümkün değil.",
        not_available_reason_en="API router disabled (not registered in main.py). "
                                "Cooling, Sequence and Holding inputs are structurally absent "
                                "from the 806-record validation dataset; "
                                "validation is not currently possible.",
        validation_evidence=ValidationEvidence(
            notes_tr="model4_full.json: kesim noktası=−70.3, 27 terim, 7 değişken. "
                     "Kalibrasyon veri seti belgelenmemiş. Doğrulama durumu: "
                     "'Experimental — requires calibration'.",
            notes_en="model4_full.json: intercept=−70.3, 27 terms, 7 variables. "
                     "Calibration dataset undocumented. Validation status: "
                     "'Experimental — requires calibration'.",
        ),
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="optimization_service.py::model4_predict() — kA→A (×1000) ve kN→daN (×100) "
                 "birim dönüşümü uygulandı. Router aktive etmek için G-V1..G-V7 kapılarını geç.",
        notes_en="optimization_service.py::model4_predict() — unit conversion kA→A (×1000) "
                 "and kN→daN (×100) applied. Pass gates G-V1..G-V7 to activate router.",
    ),

    # ── M05: Çoklu Doğrusal Regresyon ───────────────────────────────────────
    CatalogEntry(
        model_id="mlr_v1",
        version="1.0-experimental",
        name_tr="Çoklu Doğrusal Regresyon",
        name_en="Multiple Linear Regression",
        model_basis=ModelBasis.LINEAR_REGRESSION,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.EXPERIMENTAL,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("current_ka", "weld_cycles", "force_kn", "thickness_mm",
                          "material_family"),
        optional_inputs=("tip_diameter_mm", "frequency_hz"),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr=None,
        not_available_reason_en=None,
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="mlr_engine.py::fit_mlr() + predict_mlr() — OLS; doğrusal ekstrapolasyon; "
                 "patlama bölgesinde güvenilmez. router_active=False; "
                 "G-D1..G-D4 + G-M3 geçilmeden üretim aktivasyonu yok.",
        notes_en="mlr_engine.py::fit_mlr() + predict_mlr() — OLS; linear extrapolation; "
                 "unreliable in expulsion zone. router_active=False; "
                 "G-D1..G-D4 + G-M3 required for production activation.",
    ),

    # ── M06: Polinom Regresyon (RSM) ─────────────────────────────────────────
    CatalogEntry(
        model_id="rsm_polynomial_v1",
        version="1.0-experimental",
        name_tr="Polinom Regresyon (RSM)",
        name_en="Polynomial Regression (RSM)",
        model_basis=ModelBasis.RSM_POLYNOMIAL,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.EXPERIMENTAL,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("current_ka", "weld_cycles", "force_kn", "thickness_mm",
                          "material_family"),
        optional_inputs=("tip_diameter_mm", "frequency_hz"),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr=None,
        not_available_reason_en=None,
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="rsm_engine.py::fit_rsm() + predict_rsm() — ikinci dereceden polinom; "
                 "CCD/BBD verisi ile kalibrasyon gerekli. router_active=False; "
                 "G-D1..G-D4 + G-M3 geçilmeden üretim aktivasyonu yok.",
        notes_en="rsm_engine.py::fit_rsm() + predict_rsm() — second-order polynomial; "
                 "CCD/BBD calibration data required. router_active=False; "
                 "G-D1..G-D4 + G-M3 required for production activation.",
    ),

    # ── M07: Taguchi DOE ──────────────────────────────────────────────────────
    CatalogEntry(
        model_id="taguchi_doe",
        version="N/A",
        name_tr="Taguchi DOE",
        name_en="Taguchi Design of Experiments",
        model_basis=ModelBasis.TAGUCHI_DOE,
        capability_type=ModelCapabilityType.DESIGN_METHOD,
        governance_status=ModelGovernanceStatus.NOT_AVAILABLE,
        measurement_target="n/a",
        supported_materials=("Tümü",),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("factors_and_levels",),
        optional_inputs=("response_variable", "objective"),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr="Henüz geliştirilmedi. L9/L18/L27 ortogonal dizi üretici "
                                "ve S/N oranı hesaplayıcı gerekli.",
        not_available_reason_en="Not yet developed. L9/L18/L27 orthogonal array generator "
                                "and S/N ratio calculator required.",
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="NUGGET TAHMINI YAPMAZ. Parametre seviyelerini optimize eder; "
                 "kullanıcı deneyleri yürütür ve nugget ölçümlerini girer.",
        notes_en="DOES NOT PREDICT NUGGET. Optimizes parameter levels; "
                 "user runs experiments and enters nugget measurements.",
    ),

    # ── M08: ANOVA ────────────────────────────────────────────────────────────
    CatalogEntry(
        model_id="anova",
        version="N/A",
        name_tr="ANOVA (Varyans Analizi)",
        name_en="ANOVA (Analysis of Variance)",
        model_basis=ModelBasis.ANOVA,
        capability_type=ModelCapabilityType.STATISTICAL_ANALYSIS,
        governance_status=ModelGovernanceStatus.NOT_AVAILABLE,
        measurement_target="n/a",
        supported_materials=("Tümü",),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("experiment_data_table",),
        optional_inputs=("confidence_level",),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr="Henüz geliştirilmedi. Taguchi/RSM deney sonuçları giriş olarak gerekli.",
        not_available_reason_en="Not yet developed. Taguchi/RSM experiment results required as input.",
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="NUGGET TAHMINI YAPMAZ. Faktör katkılarını (SS, F değeri, p değeri, "
                 "katkı %) hesaplar; hangi parametrenin önemli olduğunu gösterir.",
        notes_en="DOES NOT PREDICT NUGGET. Computes factor contributions "
                 "(SS, F-value, p-value, contribution %); shows which parameters matter.",
    ),

    # ── M09: Gaussian Süreç Regresyonu ──────────────────────────────────────
    CatalogEntry(
        model_id="gpr_v1",
        version="N/A",
        name_tr="Gaussian Süreç Regresyonu (GPR)",
        name_en="Gaussian Process Regression (GPR)",
        model_basis=ModelBasis.GAUSSIAN_PROCESS,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.NOT_AVAILABLE,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("current_ka", "weld_cycles", "force_kn", "thickness_mm",
                          "material_family"),
        optional_inputs=("tip_diameter_mm", "frequency_hz"),
        uncertainty_supported=True,
        router_active=False,
        not_available_reason_tr="Kalibre edilmedi. Minimum 15 metalografik kayıt gerekli "
                                "(eğitim kaynağından bağımsız test seti ile). "
                                "scikit-learn bağımlılığı onay bekliyor.",
        not_available_reason_en="Not calibrated. Minimum 15 metallographic records required "
                                "(with independent test set from different source). "
                                "scikit-learn dependency pending approval.",
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="Küçük veri setleri için ideal. Güven aralığı (±σ) üretir. "
                 "Matérn 5/2 çekirdeği önerilir. Faz 2 öncelikli model adayı.",
        notes_en="Ideal for small datasets. Produces confidence interval (±σ). "
                 "Matérn 5/2 kernel recommended. Phase 2 priority model candidate.",
    ),

    # ── M10: Gradient Boosting ───────────────────────────────────────────────
    CatalogEntry(
        model_id="gbm_v1",
        version="N/A",
        name_tr="Gradient Boosting (GBM)",
        name_en="Gradient Boosting (GBM)",
        model_basis=ModelBasis.GRADIENT_BOOSTING,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.NOT_AVAILABLE,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("current_ka", "weld_cycles", "force_kn", "thickness_mm",
                          "material_family"),
        optional_inputs=("tip_diameter_mm", "frequency_hz", "coating_type"),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr="Kalibre edilmedi. Minimum 200 çeşitli kayıt gerekli. "
                                "Şu an yalnızca 9 tam uyumlu metalografik kayıt mevcut. "
                                "Mevcut Mendeley gücü (495 kayıt) force klamp bölgesinde "
                                "— force etkisi öğrenilemez.",
        not_available_reason_en="Not calibrated. Minimum 200 diverse records required. "
                                "Currently only 9 fully eligible metallographic records exist. "
                                "Existing Mendeley power (495 records) in force clamp zone "
                                "— force effect cannot be learned.",
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="Alan dışı ekstrapolasyon tehlikeli — OOD tespiti zorunlu. "
                 "SHAP analizi ile kısmen açıklanabilir. Faz 3 modeli.",
        notes_en="Out-of-domain extrapolation dangerous — OOD detection mandatory. "
                 "Partially explainable via SHAP analysis. Phase 3 model.",
    ),

    # ── M11: Fizik-Bilgili Hibrit ────────────────────────────────────────────
    CatalogEntry(
        model_id="physics_hybrid_v1",
        version="N/A",
        name_tr="Fizik-Bilgili Hibrit Model",
        name_en="Physics-Informed Hybrid Model",
        model_basis=ModelBasis.PHYSICS_HYBRID,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.NOT_AVAILABLE,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("current_ka", "weld_cycles", "force_kn", "thickness_mm",
                          "material_family"),
        optional_inputs=("tip_diameter_mm", "frequency_hz", "dynamic_energy_j"),
        uncertainty_supported=True,
        router_active=False,
        not_available_reason_tr="Uzun vadeli araştırma aşaması. Termal model öncülü "
                                "(Rogeon tipi: d ∝ (I²·t/F)^0.33) + GPR artık terimi. "
                                "Minimum 20 metalografik kayıt gerekli.",
        not_available_reason_en="Long-term research phase. Thermal model prior "
                                "(Rogeon-type: d ∝ (I²·t/F)^0.33) + GPR residual term. "
                                "Minimum 20 metallographic records required.",
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="Fizik öncülü ekstrapolasyon güvenliğini artırır. "
                 "Güven aralığı üretir. Faz 4 araştırma modeli.",
        notes_en="Physics prior improves extrapolation safety. "
                 "Produces confidence interval. Phase 4 research model.",
    ),

    # ── M12: PINN ────────────────────────────────────────────────────────────
    CatalogEntry(
        model_id="pinn_v1",
        version="N/A",
        name_tr="Fizik-Bilgili Sinir Ağı (PINN)",
        name_en="Physics-Informed Neural Network (PINN)",
        model_basis=ModelBasis.NEURAL_PINN,
        capability_type=ModelCapabilityType.NUGGET_PREDICTOR,
        governance_status=ModelGovernanceStatus.NOT_AVAILABLE,
        measurement_target="nugget_diameter_mm",
        supported_materials=(),
        thickness_range_mm=(0.0, 0.0),
        mandatory_inputs=("current_ka", "weld_cycles", "force_kn", "thickness_mm",
                          "material_family"),
        optional_inputs=("tip_diameter_mm", "frequency_hz", "dynamic_energy_j",
                         "electrode_geometry"),
        uncertainty_supported=False,
        router_active=False,
        not_available_reason_tr="Araştırma prototip aşaması. PyTorch bağımlılığı onay bekliyor. "
                                "Fizik denklemlerinin dahil edilmesi doğrulama anlamına gelmez. "
                                "Ayrı mikro-servis mimarisi gerektirir.",
        not_available_reason_en="Research prototype phase. PyTorch dependency pending approval. "
                                "Including physics equations does not mean validated. "
                                "Requires separate micro-service architecture.",
        validation_evidence=None,
        rejection_reason_tr=None,
        rejection_reason_en=None,
        notes_tr="PINN fizik kurallarını kayıp fonksiyonuna ekler; bu tek başına "
                 "doğrulama sağlamaz. Bağımsız deney verisiyle test zorunludur. "
                 "Faz 4 araştırma modeli.",
        notes_en="PINN includes physics constraints in the loss function; this alone "
                 "does not constitute validation. Independent experimental test mandatory. "
                 "Phase 4 research model.",
    ),
]

# Sabit set olarak erişim kolaylığı için
CATALOG_BY_ID: dict[str, CatalogEntry] = {e.model_id: e for e in MODEL_CATALOG}


def get_entry(model_id: str) -> CatalogEntry:
    if model_id not in CATALOG_BY_ID:
        raise KeyError(f"Model ID bulunamadı: {model_id!r}")
    return CATALOG_BY_ID[model_id]


def list_predictors() -> List[CatalogEntry]:
    """Yalnızca NUGGET_PREDICTOR tipindeki modelleri döndürür."""
    return [e for e in MODEL_CATALOG
            if e.capability_type == ModelCapabilityType.NUGGET_PREDICTOR]


def list_eligible_predictors(*, governance_statuses: tuple | None = None) -> List[CatalogEntry]:
    """
    Üretim isteğine dahil edilebilir modelleri döndürür.
    REJECTED ve DEPRECATED modeller hiçbir zaman döndürülmez.
    """
    blocked = {ModelGovernanceStatus.REJECTED, ModelGovernanceStatus.DEPRECATED}
    allowed = governance_statuses or (
        ModelGovernanceStatus.VALIDATED,
        ModelGovernanceStatus.CONDITIONALLY_VALIDATED,
        ModelGovernanceStatus.EXPERIMENTAL,
    )
    return [
        e for e in MODEL_CATALOG
        if e.capability_type == ModelCapabilityType.NUGGET_PREDICTOR
        and e.governance_status not in blocked
        and e.governance_status in allowed
    ]


def get_reference_thresholds() -> List[CatalogEntry]:
    """OEM ve literatür referans eşiklerini döndürür."""
    return [e for e in MODEL_CATALOG
            if e.capability_type == ModelCapabilityType.REFERENCE_THRESHOLD]
