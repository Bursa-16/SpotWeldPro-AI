"""
test_model_catalog.py — NUGGET-MULTI-MODEL-IMPLEMENTATION-01

Model kataloğu doğrulama testleri:
  - Tüm 12 girdinin varlığı ve zorunlu alanları
  - Durum etiketleri doğruluğu
  - REJECTED modellerin predict-guard engeli
  - NOT_AVAILABLE modellerin predict-guard engeli
  - Taguchi/ANOVA'nın nugget tahmincisi olmadığı
  - OEM/4√t'nin tahmin değil referans eşiği olduğu
  - Uyumlu model seçim mantığı
  - TR/EN anahtar doluluğu
  - API endpoint yanıtları
"""
import pytest
from fastapi.testclient import TestClient

from app.domain.model_catalog import (
    CATALOG_BY_ID,
    MODEL_CATALOG,
    ModelCapabilityType,
    ModelGovernanceStatus,
    get_entry,
    get_reference_thresholds,
    list_eligible_predictors,
    list_predictors,
)
from app.main import app

client = TestClient(app)

# ── Beklenen tam katalog ID listesi ──────────────────────────────────────────
EXPECTED_IDS = {
    "oem_table",
    "literature_4sqrt_t",
    "weld_lobe_v0_9",
    "model4_doe_polynomial",
    "mlr_v1",
    "rsm_polynomial_v1",
    "taguchi_doe",
    "anova",
    "gpr_v1",
    "gbm_v1",
    "physics_hybrid_v1",
    "pinn_v1",
}


class TestCatalogCompleteness:
    def test_catalog_has_12_entries(self):
        assert len(MODEL_CATALOG) == 12

    def test_all_expected_ids_present(self):
        actual_ids = {e.model_id for e in MODEL_CATALOG}
        assert actual_ids == EXPECTED_IDS

    def test_no_duplicate_ids(self):
        ids = [e.model_id for e in MODEL_CATALOG]
        assert len(ids) == len(set(ids))

    def test_every_entry_has_required_fields(self):
        for e in MODEL_CATALOG:
            assert e.model_id, f"{e.model_id}: model_id boş"
            assert e.name_tr, f"{e.model_id}: name_tr boş"
            assert e.name_en, f"{e.model_id}: name_en boş"
            assert e.model_basis, f"{e.model_id}: model_basis boş"
            assert e.capability_type, f"{e.model_id}: capability_type boş"
            assert e.governance_status, f"{e.model_id}: governance_status boş"
            assert e.notes_tr, f"{e.model_id}: notes_tr boş"
            assert e.notes_en, f"{e.model_id}: notes_en boş"

    def test_get_entry_by_id(self):
        e = get_entry("oem_table")
        assert e.model_id == "oem_table"

    def test_get_entry_missing_raises(self):
        with pytest.raises(KeyError):
            get_entry("nonexistent_model_xyz")


class TestModelSemantics:
    """Kritik semantik kurallar."""

    def test_oem_is_reference_threshold_not_predictor(self):
        e = get_entry("oem_table")
        assert e.capability_type == ModelCapabilityType.REFERENCE_THRESHOLD
        assert e.measurement_target == "acceptance_criterion_mm"

    def test_4sqrt_t_is_reference_threshold_not_predictor(self):
        e = get_entry("literature_4sqrt_t")
        assert e.capability_type == ModelCapabilityType.REFERENCE_THRESHOLD
        assert e.measurement_target == "acceptance_criterion_mm"

    def test_taguchi_is_design_method_not_predictor(self):
        e = get_entry("taguchi_doe")
        assert e.capability_type == ModelCapabilityType.DESIGN_METHOD
        assert e.measurement_target == "n/a"
        assert "NUGGET TAHMINI YAPMAZ" in e.notes_tr
        assert "DOES NOT PREDICT NUGGET" in e.notes_en

    def test_anova_is_statistical_analysis_not_predictor(self):
        e = get_entry("anova")
        assert e.capability_type == ModelCapabilityType.STATISTICAL_ANALYSIS
        assert e.measurement_target == "n/a"
        assert "NUGGET TAHMINI YAPMAZ" in e.notes_tr

    def test_pinn_not_validated_despite_physics(self):
        e = get_entry("pinn_v1")
        assert e.governance_status == ModelGovernanceStatus.NOT_AVAILABLE
        assert "doğrulama anlamına gelmez" in e.not_available_reason_tr.lower() or \
               "does not mean validated" in e.not_available_reason_en.lower()

    def test_reference_thresholds_helper(self):
        refs = get_reference_thresholds()
        ids = {r.model_id for r in refs}
        assert "oem_table" in ids
        assert "literature_4sqrt_t" in ids
        assert "weld_lobe_v0_9" not in ids
        assert "model4_doe_polynomial" not in ids


class TestGovernanceStatuses:
    def test_weld_lobe_is_rejected(self):
        e = get_entry("weld_lobe_v0_9")
        assert e.governance_status == ModelGovernanceStatus.REJECTED

    def test_weld_lobe_has_rejection_evidence(self):
        e = get_entry("weld_lobe_v0_9")
        assert e.rejection_reason_tr is not None
        assert "RMSE" in e.rejection_reason_tr
        assert e.validation_evidence is not None
        assert e.validation_evidence.rmse_mm == pytest.approx(11.34, abs=0.1)
        assert e.validation_evidence.r2 == pytest.approx(-276.6, abs=1.0)

    def test_model4_is_experimental(self):
        e = get_entry("model4_doe_polynomial")
        assert e.governance_status == ModelGovernanceStatus.EXPERIMENTAL
        assert e.router_active is False

    def test_oem_is_validated(self):
        e = get_entry("oem_table")
        assert e.governance_status == ModelGovernanceStatus.VALIDATED

    def test_4sqrt_t_is_validated(self):
        e = get_entry("literature_4sqrt_t")
        assert e.governance_status == ModelGovernanceStatus.VALIDATED

    def test_gpr_is_not_available(self):
        e = get_entry("gpr_v1")
        assert e.governance_status == ModelGovernanceStatus.NOT_AVAILABLE
        assert e.uncertainty_supported is True

    def test_gbm_requires_200_records(self):
        e = get_entry("gbm_v1")
        assert e.governance_status == ModelGovernanceStatus.NOT_AVAILABLE
        assert "200" in (e.not_available_reason_tr or "")


class TestEligibilityFilters:
    def test_rejected_not_in_eligible_predictors(self):
        eligible = list_eligible_predictors()
        ids = {e.model_id for e in eligible}
        assert "weld_lobe_v0_9" not in ids

    def test_not_available_in_eligible_with_experimental(self):
        eligible = list_eligible_predictors(governance_statuses=(
            ModelGovernanceStatus.EXPERIMENTAL,
        ))
        ids = {e.model_id for e in eligible}
        assert "model4_doe_polynomial" in ids

    def test_predictors_excludes_reference_and_tools(self):
        preds = list_predictors()
        pred_ids = {e.model_id for e in preds}
        assert "oem_table" not in pred_ids
        assert "literature_4sqrt_t" not in pred_ids
        assert "taguchi_doe" not in pred_ids
        assert "anova" not in pred_ids

    def test_reference_thresholds_not_in_predictors(self):
        preds = list_predictors()
        for p in preds:
            assert p.capability_type == ModelCapabilityType.NUGGET_PREDICTOR

    def test_no_rejected_in_default_eligible(self):
        eligible = list_eligible_predictors()
        for e in eligible:
            assert e.governance_status != ModelGovernanceStatus.REJECTED


class TestNoFakeMetrics:
    """Doğrulama kanıtı olmayan modellerde metrik uydurmama."""

    @pytest.mark.parametrize("model_id", [
        "mlr_v1", "rsm_polynomial_v1", "gpr_v1", "gbm_v1",
        "physics_hybrid_v1", "pinn_v1", "taguchi_doe", "anova",
    ])
    def test_no_fake_metrics_on_not_available(self, model_id):
        e = get_entry(model_id)
        ev = e.validation_evidence
        assert ev is None or (
            ev.rmse_mm is None and ev.r2 is None and ev.mae_mm is None
        ), f"{model_id}: Sahte metrikler bulundu"


class TestTrEnCompleteness:
    """Her modelin TR ve EN metinleri dolu olmalı."""

    def test_all_tr_names_non_empty(self):
        for e in MODEL_CATALOG:
            assert e.name_tr.strip(), f"{e.model_id}: name_tr boş"

    def test_all_en_names_non_empty(self):
        for e in MODEL_CATALOG:
            assert e.name_en.strip(), f"{e.model_id}: name_en boş"

    def test_all_notes_tr_non_empty(self):
        for e in MODEL_CATALOG:
            assert e.notes_tr.strip(), f"{e.model_id}: notes_tr boş"

    def test_all_notes_en_non_empty(self):
        for e in MODEL_CATALOG:
            assert e.notes_en.strip(), f"{e.model_id}: notes_en boş"

    def test_not_available_reason_bilingual(self):
        for e in MODEL_CATALOG:
            if e.not_available_reason_tr is not None:
                assert e.not_available_reason_en is not None, \
                    f"{e.model_id}: TR neden var ama EN neden yok"

    def test_rejection_reason_bilingual(self):
        for e in MODEL_CATALOG:
            if e.rejection_reason_tr is not None:
                assert e.rejection_reason_en is not None, \
                    f"{e.model_id}: TR red nedeni var ama EN red nedeni yok"


class TestAPIEndpoints:
    def test_list_catalog_returns_12(self):
        resp = client.get("/api/v1/model-catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 12
        assert len(data["entries"]) == 12

    def test_get_oem_entry(self):
        resp = client.get("/api/v1/model-catalog/oem_table")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_id"] == "oem_table"
        assert data["capability_type"] == "REFERENCE_THRESHOLD"
        assert data["governance_status"] == "VALIDATED"

    def test_get_weld_lobe_entry(self):
        resp = client.get("/api/v1/model-catalog/weld_lobe_v0_9")
        assert resp.status_code == 200
        data = resp.json()
        assert data["governance_status"] == "REJECTED"
        assert data["router_active"] is False
        assert data["validation_evidence"]["rmse_mm"] is not None

    def test_get_missing_model_404(self):
        resp = client.get("/api/v1/model-catalog/does_not_exist")
        assert resp.status_code == 404

    def test_predict_guard_rejected_returns_422(self):
        resp = client.post("/api/v1/model-catalog/predict-guard/weld_lobe_v0_9")
        assert resp.status_code == 422
        data = resp.json()
        # GovernedAPIError handler maps detail dict to top-level error_code
        assert data["error_code"] == "MODEL_REJECTED"

    def test_predict_guard_not_available_returns_422(self):
        resp = client.post("/api/v1/model-catalog/predict-guard/gpr_v1")
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "MODEL_NOT_AVAILABLE"

    def test_predict_guard_experimental_inactive_returns_422(self):
        """EXPERIMENTAL + router_active=False → 422 MODEL_EXPERIMENTAL."""
        resp = client.post("/api/v1/model-catalog/predict-guard/model4_doe_polynomial")
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "MODEL_EXPERIMENTAL"

    def test_predict_guard_mlr_returns_422_experimental(self):
        resp = client.post("/api/v1/model-catalog/predict-guard/mlr_v1")
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "MODEL_EXPERIMENTAL"

    def test_predict_guard_rsm_returns_422_experimental(self):
        resp = client.post("/api/v1/model-catalog/predict-guard/rsm_polynomial_v1")
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "MODEL_EXPERIMENTAL"

    def test_predict_guard_experimental_has_tr_message(self):
        """message alanı Türkçe içerik içermeli."""
        resp = client.post("/api/v1/model-catalog/predict-guard/mlr_v1")
        assert resp.status_code == 422
        data = resp.json()
        assert "üretim" in data["message"].lower() or "deneysel" in data["message"].lower() \
               or "router_active" in data["message"].lower()

    def test_predict_guard_experimental_has_en_message(self):
        """detail.message_en alanı İngilizce içerik içermeli."""
        resp = client.post("/api/v1/model-catalog/predict-guard/mlr_v1")
        assert resp.status_code == 422
        data = resp.json()
        assert data["detail"] is not None
        assert "message_en" in data["detail"]
        msg_en = data["detail"]["message_en"]
        assert "production" in msg_en.lower() or "router_active" in msg_en.lower()

    def test_predict_guard_validated_still_passes(self):
        """VALIDATED + router_active=True → 200 OK."""
        resp = client.post("/api/v1/model-catalog/predict-guard/oem_table")
        assert resp.status_code == 200
        data = resp.json()
        assert data["governance_status"] == "VALIDATED"

    def test_predict_guard_missing_model_404(self):
        resp = client.post("/api/v1/model-catalog/predict-guard/no_such_model")
        assert resp.status_code == 404

    def test_all_entries_have_model_id(self):
        resp = client.get("/api/v1/model-catalog")
        data = resp.json()
        for entry in data["entries"]:
            assert entry["model_id"], "model_id boş"
            assert entry["name_tr"], "name_tr boş"
            assert entry["name_en"], "name_en boş"

    def test_no_null_fabricated_metrics(self):
        """Doğrulama kanıtı olmayan modellerde rmse_mm sıfır olmamalı."""
        resp = client.get("/api/v1/model-catalog")
        data = resp.json()
        for entry in data["entries"]:
            ev = entry.get("validation_evidence")
            if ev is not None and ev.get("rmse_mm") is not None:
                assert ev["rmse_mm"] != 0.0, \
                    f"{entry['model_id']}: rmse_mm=0 sahte değer"


class TestExistingScreensNotRegressed:
    """Mevcut endpoint'lerin bozulmadığını doğrula."""

    def test_health_still_works(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_weld_analysis_route_exists(self):
        resp = client.post("/api/v1/weld-analysis", json={})
        assert resp.status_code in (400, 422)

    def test_failure_probability_route_exists(self):
        resp = client.post("/api/v1/failure-probability/analyze", json={})
        # 401 = route exists but requires auth; 422 = unprocessable; both confirm route is registered
        assert resp.status_code in (400, 401, 422)

    def test_optimization_still_disabled(self):
        for path in ["/api/v1/optimization/model4/predict",
                     "/api/v1/optimization/optimize",
                     "/api/v1/optimization/ensemble",
                     "/api/v1/optimization/validate"]:
            resp = client.post(path, json={})
            assert resp.status_code == 404, f"{path} artık 404 döndürmüyor"
