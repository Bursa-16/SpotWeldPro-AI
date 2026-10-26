"""
test_mlr_rsm_engine.py — RSM-REGRESSION-ENGINE-01

MLR ve RSM motorlarının deterministik matematiksel doğrulaması.
Tüm test verileri analitik olarak türetilmiştir; gerçek metalografik
ölçüm içermez ve nugget çapı tahmin etmez (sadece motor doğrulaması).
"""
import math
import pytest

from app.domain.mlr_engine import (
    MLRRecord,
    MeasurementBasis,
    fit_mlr,
    predict_mlr,
)
from app.domain.rsm_engine import (
    RSMFactor,
    RSMOrder,
    fit_rsm,
    predict_rsm,
    n_terms,
)
from app.domain.model_catalog import MODEL_CATALOG, ModelGovernanceStatus


# ── Yardımcı ─────────────────────────────────────────────────────────────────

def _mlr_rec(current: float, force: float, nugget: float) -> MLRRecord:
    return MLRRecord(
        features={"current_ka": current, "force_kn": force},
        nugget_diameter_mm=nugget,
        source="analitik_test",
        measurement_basis=MeasurementBasis.SYNTHETIC,
    )


def _rsm_rec(x_val: float, nugget: float) -> dict:
    return {"features": {"x": x_val}, "nugget_diameter_mm": nugget}


def _rsm2_rec(x: float, z: float, nugget: float) -> dict:
    return {"features": {"x": x, "z": z}, "nugget_diameter_mm": nugget}


# ════════════════════════════════════════════════════════════════════════════
# A — MLR MOTOR TESTLERİ
# ════════════════════════════════════════════════════════════════════════════

class TestMLRPerfectFit:
    """
    Analitik veri: y = 1.0 + 2.0·current + 0.5·force
    2×3 ortogonal faktöriyel tasarım → VIF=1, RMSE≈0, R²≈1.
    """
    RECORDS = [
        _mlr_rec(5.0, 2.0, 12.0),    # 1 + 10 + 1.0
        _mlr_rec(7.0, 2.0, 16.0),    # 1 + 14 + 1.0
        _mlr_rec(9.0, 2.0, 20.0),    # 1 + 18 + 1.0
        _mlr_rec(5.0, 4.0, 13.0),    # 1 + 10 + 2.0
        _mlr_rec(7.0, 4.0, 17.0),    # 1 + 14 + 2.0
        _mlr_rec(9.0, 4.0, 21.0),    # 1 + 18 + 2.0
    ]
    FEATURES = ["current_ka", "force_kn"]

    def test_rmse_near_zero(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.rmse_mm < 1e-6

    def test_r2_near_one(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.r2 > 0.9999

    def test_intercept(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert abs(fit.intercept - 1.0) < 1e-6

    def test_coefficient_current(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert abs(fit.coefficients["current_ka"] - 2.0) < 1e-6

    def test_coefficient_force(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert abs(fit.coefficients["force_kn"] - 0.5) < 1e-6

    def test_governance(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.governance_status == "EXPERIMENTAL"
        assert fit.router_active is False
        assert fit.capability_type == "NUGGET_PREDICTOR"

    def test_residual_df(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.residual_df == 6 - 3  # N - p

    def test_vif_near_one(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.diagnostics is not None
        for fname, v in fit.diagnostics.vif.items():
            assert math.isfinite(v), f"{fname} VIF sonsuz"
            assert v < 2.0, f"{fname} VIF={v:.2f} — ortogonal tasarımda beklenmeyen çoklu bağıntı"


class TestMLRPrediction:
    """Fit edilmiş model ile tahmin ve extrapolasyon tespiti."""

    RECORDS = [
        _mlr_rec(5.0, 2.0, 12.0),
        _mlr_rec(7.0, 2.0, 16.0),
        _mlr_rec(9.0, 2.0, 20.0),
        _mlr_rec(5.0, 4.0, 13.0),
        _mlr_rec(7.0, 4.0, 17.0),
        _mlr_rec(9.0, 4.0, 21.0),
    ]
    FEATURES = ["current_ka", "force_kn"]

    def test_in_domain_prediction(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        pred = predict_mlr(fit, {"current_ka": 7.0, "force_kn": 3.0})
        assert pred.in_domain is True
        assert abs(pred.predicted_nugget_mm - 16.5) < 1e-3   # 1 + 14 + 1.5

    def test_extrapolation_detected(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        pred = predict_mlr(fit, {"current_ka": 15.0, "force_kn": 3.0})
        assert pred.in_domain is False
        assert "current_ka" in pred.extrapolated_features

    def test_missing_feature_raises(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        with pytest.raises(ValueError, match="force_kn"):
            predict_mlr(fit, {"current_ka": 7.0})


class TestMLRRankDeficiency:
    """feature2 = 2 · feature1 → tam kolinearite → rank eksikliği."""

    def _collinear_records(self) -> list[MLRRecord]:
        vals = [(5.0, 10.0, 12.0), (7.0, 14.0, 16.0), (9.0, 18.0, 20.0),
                (6.0, 12.0, 14.0)]
        return [
            MLRRecord(
                features={"current_ka": c, "force_kn": f},
                nugget_diameter_mm=y,
                source="kolinearite_test",
                measurement_basis=MeasurementBasis.SYNTHETIC,
            )
            for c, f, y in vals
        ]

    def test_rank_deficient_flagged(self):
        recs = self._collinear_records()
        fit = fit_mlr(recs, ["current_ka", "force_kn"])
        assert fit.diagnostics is not None
        assert bool(fit.diagnostics.rank_deficient) is True

    def test_warning_emitted(self):
        recs = self._collinear_records()
        fit = fit_mlr(recs, ["current_ka", "force_kn"])
        assert any("rank" in w.lower() or "bağıntı" in w.lower() for w in fit.warnings)


class TestMLRValidation:
    """Girdi doğrulama: geçersiz hedef, eksik özellik, yetersiz N."""

    def test_negative_nugget_raises(self):
        with pytest.raises(ValueError, match="nugget_diameter_mm"):
            fit_mlr(
                [_mlr_rec(5.0, 2.0, -1.0), _mlr_rec(7.0, 2.0, 16.0),
                 _mlr_rec(9.0, 2.0, 20.0), _mlr_rec(5.0, 4.0, 14.0)],
                ["current_ka", "force_kn"],
            )

    def test_insufficient_n_raises(self):
        with pytest.raises(ValueError, match="N="):
            fit_mlr(
                [_mlr_rec(5.0, 2.0, 12.0), _mlr_rec(7.0, 2.0, 16.0)],
                ["current_ka", "force_kn"],
            )

    def test_missing_feature_in_record_raises(self):
        recs = [
            MLRRecord(features={"current_ka": 5.0}, nugget_diameter_mm=12.0,
                      source="test", measurement_basis=MeasurementBasis.SYNTHETIC),
            MLRRecord(features={"current_ka": 7.0}, nugget_diameter_mm=16.0,
                      source="test", measurement_basis=MeasurementBasis.SYNTHETIC),
            MLRRecord(features={"current_ka": 9.0}, nugget_diameter_mm=20.0,
                      source="test", measurement_basis=MeasurementBasis.SYNTHETIC),
            MLRRecord(features={"current_ka": 5.0}, nugget_diameter_mm=14.0,
                      source="test", measurement_basis=MeasurementBasis.SYNTHETIC),
        ]
        with pytest.raises(ValueError, match="force_kn"):
            fit_mlr(recs, ["current_ka", "force_kn"])


# ════════════════════════════════════════════════════════════════════════════
# B — RSM MOTOR TESTLERİ
# ════════════════════════════════════════════════════════════════════════════

class TestRSMTermCount:
    """n_terms() formülü: 1 + k(k+3)/2."""

    def test_k1_second(self):
        assert n_terms(1, RSMOrder.SECOND) == 3   # intercept + x + x²

    def test_k2_second(self):
        assert n_terms(2, RSMOrder.SECOND) == 6   # 1 + 2 + 2 + 1

    def test_k5_second(self):
        assert n_terms(5, RSMOrder.SECOND) == 21  # 1 + 5(5+3)/2 = 1+20

    def test_k3_first(self):
        assert n_terms(3, RSMOrder.FIRST) == 4    # intercept + 3 lineer


class TestRSMSingleFactorQuadratic:
    """
    Analitik veri: y = 4x² − 3x + 1
    x ∈ {−2,−1,0,1,2,3} → 6 nokta, 3 terim → df=3, RMSE≈0, R²≈1.
    """
    XY = [(-2.0, 23.0), (-1.0, 8.0), (0.0, 1.0), (1.0, 2.0), (2.0, 11.0), (3.0, 28.0)]
    FACTOR = [RSMFactor("x", "birim")]

    def _records(self):
        return [_rsm_rec(x, y) for x, y in self.XY]

    def test_rmse_near_zero(self):
        fit = fit_rsm(self._records(), self.FACTOR)
        assert fit.rmse_mm < 1e-6

    def test_r2_near_one(self):
        fit = fit_rsm(self._records(), self.FACTOR)
        assert fit.r2 > 0.9999

    def test_residual_df(self):
        fit = fit_rsm(self._records(), self.FACTOR)
        assert fit.residual_df == 6 - 3

    def test_governance(self):
        fit = fit_rsm(self._records(), self.FACTOR)
        assert fit.governance_status == "EXPERIMENTAL"
        assert fit.router_active is False


class TestRSMExtrapolation:
    """x=10 → eğitim alanı [−2, 3] dışında → in_domain=False."""
    XY = [(-2.0, 23.0), (-1.0, 8.0), (0.0, 1.0), (1.0, 2.0), (2.0, 11.0), (3.0, 28.0)]
    FACTOR = [RSMFactor("x", "birim")]

    def _fit(self):
        return fit_rsm([_rsm_rec(x, y) for x, y in self.XY], self.FACTOR)

    def test_in_domain(self):
        fit = self._fit()
        pred = predict_rsm(fit, {"x": 1.5})
        assert pred.in_domain is True

    def test_extrapolation_detected(self):
        fit = self._fit()
        pred = predict_rsm(fit, {"x": 10.0})
        assert pred.in_domain is False
        assert "x" in pred.extrapolated_factors
        assert any("EXTRAPOLATION" in w for w in pred.warnings)

    def test_negative_extrapolation_detected(self):
        fit = self._fit()
        pred = predict_rsm(fit, {"x": -5.0})
        assert pred.in_domain is False


class TestRSMInsufficientN:
    """N < n_terms + 1 → ValueError."""

    def test_raises_on_small_n(self):
        factors = [RSMFactor("x", "kA"), RSMFactor("z", "kN")]
        # k=2, second-order → n_terms=6 → gerekli N ≥ 7
        records = [_rsm2_rec(float(i), float(i), 5.0 + i) for i in range(5)]
        with pytest.raises(ValueError, match="N="):
            fit_rsm(records, factors)


class TestRSMValidation:
    """Eksik faktör ve geçersiz hedef doğrulaması."""

    FACTOR = [RSMFactor("x", "birim")]
    BASE = [_rsm_rec(float(i), float(i ** 2 + 1)) for i in range(7)]

    def test_missing_factor_raises(self):
        fit = fit_rsm(self.BASE, self.FACTOR)
        with pytest.raises(ValueError, match="'x'"):
            predict_rsm(fit, {})

    def test_zero_nugget_raises(self):
        bad = [{"features": {"x": 1.0}, "nugget_diameter_mm": 0.0}]
        with pytest.raises(ValueError, match="nugget_diameter_mm"):
            fit_rsm(bad + self.BASE, self.FACTOR)


class TestRSMConstantFactor:
    """Sabit faktör → ölçek=1 uyarısı verir; fit yine çalışır."""

    def test_constant_factor_warning(self):
        # x sabit: tüm değerler 3.0
        records = [
            {"features": {"x": 3.0, "z": float(i)}, "nugget_diameter_mm": float(i + 5)}
            for i in range(8)
        ]
        factors = [RSMFactor("x", "kA"), RSMFactor("z", "kN")]
        fit = fit_rsm(records, factors)
        assert any("sabit" in w.lower() or "scale" in w.lower() for w in fit.warnings)


# ════════════════════════════════════════════════════════════════════════════
# C — YÖNETİŞİM VE KATALOG TESTLERİ
# ════════════════════════════════════════════════════════════════════════════

class TestGovernanceCatalog:
    """Katalog girdilerinin EXPERIMENTAL ve router_active=False olduğunu doğrula."""

    def _entry(self, model_id: str):
        return next((e for e in MODEL_CATALOG if e.model_id == model_id), None)

    def test_mlr_governance_experimental(self):
        e = self._entry("mlr_v1")
        assert e is not None
        assert e.governance_status == ModelGovernanceStatus.EXPERIMENTAL

    def test_mlr_router_inactive(self):
        e = self._entry("mlr_v1")
        assert e.router_active is False

    def test_mlr_version(self):
        e = self._entry("mlr_v1")
        assert e.version == "1.0-experimental"

    def test_rsm_governance_experimental(self):
        e = self._entry("rsm_polynomial_v1")
        assert e is not None
        assert e.governance_status == ModelGovernanceStatus.EXPERIMENTAL

    def test_rsm_router_inactive(self):
        e = self._entry("rsm_polynomial_v1")
        assert e.router_active is False

    def test_rsm_version(self):
        e = self._entry("rsm_polynomial_v1")
        assert e.version == "1.0-experimental"

    def test_model4_unchanged(self):
        """Model-4 durumu değiştirilmemiş olmalı."""
        e = self._entry("model4_doe_polynomial")
        assert e.governance_status == ModelGovernanceStatus.EXPERIMENTAL
        assert e.router_active is False

    def test_weld_lobe_still_rejected(self):
        """Weld Lobe hâlâ REJECTED olmalı."""
        e = self._entry("weld_lobe_v0_9")
        assert e.governance_status == ModelGovernanceStatus.REJECTED
        assert e.router_active is False

    def test_taguchi_capability_unchanged(self):
        """Taguchi DESIGN_METHOD olarak kalmalı."""
        from app.domain.model_catalog import ModelCapabilityType
        e = self._entry("taguchi_doe")
        assert e.capability_type == ModelCapabilityType.DESIGN_METHOD

    def test_anova_capability_unchanged(self):
        """ANOVA STATISTICAL_ANALYSIS olarak kalmalı."""
        from app.domain.model_catalog import ModelCapabilityType
        e = self._entry("anova")
        assert e.capability_type == ModelCapabilityType.STATISTICAL_ANALYSIS

    def test_mlr_not_available_reason_cleared(self):
        e = self._entry("mlr_v1")
        assert e.not_available_reason_tr is None
        assert e.not_available_reason_en is None

    def test_rsm_not_available_reason_cleared(self):
        e = self._entry("rsm_polynomial_v1")
        assert e.not_available_reason_tr is None
        assert e.not_available_reason_en is None


# ════════════════════════════════════════════════════════════════════════════
# C2 — HARDENING-01: M-01, M-02, M-03 TESTLERİ
# ════════════════════════════════════════════════════════════════════════════

class TestMLRAdjustedR2:
    """M-01: MLR düzeltilmiş R² (adjusted R²)."""

    RECORDS = [
        _mlr_rec(5.0, 2.0, 12.0),
        _mlr_rec(7.0, 2.0, 16.0),
        _mlr_rec(9.0, 2.0, 20.0),
        _mlr_rec(5.0, 4.0, 13.0),
        _mlr_rec(7.0, 4.0, 17.0),
        _mlr_rec(9.0, 4.0, 21.0),
    ]
    FEATURES = ["current_ka", "force_kn"]

    def test_r2_adjusted_present(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert hasattr(fit, "r2_adjusted")
        assert fit.r2_adjusted is not None

    def test_r2_adjusted_near_one_for_perfect_fit(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.r2_adjusted > 0.9999

    def test_r2_adjusted_le_r2(self):
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        assert fit.r2_adjusted <= fit.r2 + 1e-9

    def test_r2_adjusted_formula(self):
        """R²_adj = 1 − (1−R²)*(N−1)/(N−p); N=6, p=3 → df_res=3."""
        fit = fit_mlr(self.RECORDS, self.FEATURES)
        n, p = fit.n_obs, fit.n_features + 1
        expected = 1.0 - (1.0 - fit.r2) * (n - 1) / (n - p)
        assert abs(fit.r2_adjusted - expected) < 1e-9


class TestRSMAdjustedR2:
    """M-01: RSM düzeltilmiş R²."""

    XY = [(-2.0, 23.0), (-1.0, 8.0), (0.0, 1.0), (1.0, 2.0), (2.0, 11.0), (3.0, 28.0)]
    FACTOR = [RSMFactor("x", "birim")]

    def test_r2_adjusted_present(self):
        fit = fit_rsm([_rsm_rec(x, y) for x, y in self.XY], self.FACTOR)
        assert hasattr(fit, "r2_adjusted")
        assert fit.r2_adjusted is not None

    def test_r2_adjusted_near_one_for_perfect_fit(self):
        fit = fit_rsm([_rsm_rec(x, y) for x, y in self.XY], self.FACTOR)
        assert fit.r2_adjusted > 0.9999

    def test_r2_adjusted_le_r2(self):
        fit = fit_rsm([_rsm_rec(x, y) for x, y in self.XY], self.FACTOR)
        assert fit.r2_adjusted <= fit.r2 + 1e-9

    def test_r2_adjusted_formula(self):
        """R²_adj = 1 − (1−R²)*(N−1)/(N−p); N=6, p=3 (1+k+k²=3 for k=1 second)."""
        fit = fit_rsm([_rsm_rec(x, y) for x, y in self.XY], self.FACTOR)
        n, p = fit.n_obs, fit.n_terms
        expected = 1.0 - (1.0 - fit.r2) * (n - 1) / (n - p)
        assert abs(fit.r2_adjusted - expected) < 1e-9


class TestRSMDuplicateDetection:
    """M-02: RSM tekrar eden deney koşulu tespiti."""

    FACTOR = [RSMFactor("x", "birim")]

    def test_duplicate_triggers_warning(self):
        records = [
            _rsm_rec(1.0, 4.0),
            _rsm_rec(2.0, 9.0),
            _rsm_rec(3.0, 16.0),
            _rsm_rec(4.0, 25.0),
            _rsm_rec(5.0, 36.0),
            _rsm_rec(6.0, 49.0),
            _rsm_rec(1.0, 4.0),  # tam kopya
        ]
        fit = fit_rsm(records, self.FACTOR)
        assert any("tekrar" in w.lower() or "kopya" in w.lower() for w in fit.warnings)

    def test_unique_records_no_duplicate_warning(self):
        records = [_rsm_rec(float(i), float(i ** 2 + 1)) for i in range(7)]
        fit = fit_rsm(records, self.FACTOR)
        assert not any("tekrar" in w.lower() or "kopya" in w.lower() for w in fit.warnings)


class TestRSMProvenance:
    """M-03: RSM kayıt proveniyet alanları."""

    FACTOR = [RSMFactor("x", "birim")]

    def _records_with_source(self):
        recs = [_rsm_rec(float(i), float(i ** 2 + 1)) for i in range(7)]
        for i, r in enumerate(recs):
            r["source"] = "laboratory_A" if i < 4 else "literature_B"
            r["measurement_basis"] = "metallographic" if i < 4 else "literature"
        return recs

    def test_sources_populated(self):
        fit = fit_rsm(self._records_with_source(), self.FACTOR)
        assert "laboratory_A" in fit.sources
        assert "literature_B" in fit.sources

    def test_measurement_bases_populated(self):
        fit = fit_rsm(self._records_with_source(), self.FACTOR)
        assert "metallographic" in fit.measurement_bases
        assert "literature" in fit.measurement_bases

    def test_missing_provenance_defaults_to_unknown(self):
        """Kayıtta source/measurement_basis yoksa 'unknown' döner."""
        records = [_rsm_rec(float(i), float(i ** 2 + 1)) for i in range(7)]
        fit = fit_rsm(records, self.FACTOR)
        assert "unknown" in fit.sources
        assert "unknown" in fit.measurement_bases

    def test_sources_sorted(self):
        fit = fit_rsm(self._records_with_source(), self.FACTOR)
        assert fit.sources == sorted(fit.sources)

    def test_sources_unique(self):
        fit = fit_rsm(self._records_with_source(), self.FACTOR)
        assert len(fit.sources) == len(set(fit.sources))


# ════════════════════════════════════════════════════════════════════════════
# D — MEVcut HESAPLAMALAR DEĞİŞMEDİ
# ════════════════════════════════════════════════════════════════════════════

class TestExistingCalculationsUnchanged:
    """OEM ve literatür modelleri hâlâ doğru çalışıyor."""

    def test_oem_table_validated(self):
        from app.domain.model_catalog import ModelGovernanceStatus
        e = next(e for e in MODEL_CATALOG if e.model_id == "oem_table")
        assert e.governance_status == ModelGovernanceStatus.VALIDATED
        assert e.router_active is True

    def test_4sqrt_t_validated(self):
        from app.domain.model_catalog import ModelGovernanceStatus
        e = next(e for e in MODEL_CATALOG if e.model_id == "literature_4sqrt_t")
        assert e.governance_status == ModelGovernanceStatus.VALIDATED

    def test_polynomial_model_predict_unchanged(self):
        """polynomial_model.py predict() değiştirilmedi."""
        from app.domain.polynomial_model import PolynomialModel, PolynomialTerm
        m = PolynomialModel(
            name="test", intercept=1.0, variables=["x"], units={"x": "mm"},
            terms=[PolynomialTerm(coefficient=2.0, factors=[{"variable": "x", "power": 1}])],
            validation_status="test",
        )
        assert abs(m.predict({"x": 5.0}) - 11.0) < 1e-9

    def test_model_validation_thresholds_unchanged(self):
        """model_validation.py eşikleri değişmedi: RMSE≤0.35 → Validated."""
        from app.domain.model_validation import validate_model
        predictor = lambda row: row["actual_nugget_mm"] + 0.1  # sabit +0.1mm hata
        rows = [{"actual_nugget_mm": float(i)} for i in range(1, 20)]
        result = validate_model(rows, predictor)
        assert result["status"] == "Validated"
        assert abs(result["rmse_mm"] - 0.1) < 1e-9
