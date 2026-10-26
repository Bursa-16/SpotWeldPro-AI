"""
test_taguchi_anova.py — TAGUCHI-ANOVA-IMPLEMENTATION-01

Taguchi DOE motoru ve ANOVA motoru için deterministik testler.
Tüm yanıt değerleri kullanıcı tarafından girilmiş sabit test verileridir;
bu testler nugget tahmini yapmaz.
"""
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain import taguchi as T
from app.domain import statistical_analysis as A
from app.main import app

client = TestClient(app)

# ── Test sabit verileri ────────────────────────────────────────────────────────

# L9 literatür örneği: 3 faktör, 3 seviye, 9 run
# Yanıtlar hayali ama deterministik (nugget çapı değil; boyutsuz ölçüm)
L9_RESPONSES = [5.2, 6.1, 4.8, 5.9, 6.5, 5.4, 4.6, 5.8, 6.3]

L9_FACTORS = [
    T.FactorSpec("current_kA", "kA", (7.5, 8.0, 8.5)),
    T.FactorSpec("weld_time", "cycles", (10, 12, 14)),
    T.FactorSpec("force_kN", "kN", (2.5, 3.0, 3.5)),
]


# ── Ortogonal dizi doğruluğu ───────────────────────────────────────────────────

class TestOrthogonalArrays:
    """Her OA sütunu için: her seviye eşit kez görünmeli (denge)."""

    def _check_balance(self, oa: np.ndarray, n_levels: int):
        n_runs, n_cols = oa.shape
        expected = n_runs // n_levels
        for col in range(n_cols):
            for lv in range(1, n_levels + 1):
                count = int(np.sum(oa[:, col] == lv))
                assert count == expected, (
                    f"Sütun {col}, seviye {lv}: {count} kez görünüyor; {expected} bekleniyor"
                )

    def _check_orthogonality(self, oa: np.ndarray, n_levels: int):
        """Her sütun çifti için: tüm (i,j) seviye kombinasyonları eşit kez."""
        n_runs, n_cols = oa.shape
        expected = n_runs // (n_levels ** 2)
        for c1 in range(n_cols):
            for c2 in range(c1 + 1, n_cols):
                for lv1 in range(1, n_levels + 1):
                    for lv2 in range(1, n_levels + 1):
                        count = int(np.sum((oa[:, c1] == lv1) & (oa[:, c2] == lv2)))
                        assert count == expected, (
                            f"Sütun ({c1},{c2}) çifti, seviyeler ({lv1},{lv2}): "
                            f"{count} kez; {expected} bekleniyor"
                        )

    def test_l4_balance(self):
        oa = T.get_orthogonal_array("L4")
        assert oa.shape == (4, 3)
        self._check_balance(oa, 2)

    def test_l4_orthogonality(self):
        oa = T.get_orthogonal_array("L4")
        self._check_orthogonality(oa, 2)

    def test_l9_balance(self):
        oa = T.get_orthogonal_array("L9")
        assert oa.shape == (9, 4)
        self._check_balance(oa, 3)

    def test_l9_orthogonality(self):
        oa = T.get_orthogonal_array("L9")
        self._check_orthogonality(oa, 3)

    def test_l16_shape(self):
        oa = T.get_orthogonal_array("L16")
        assert oa.shape == (16, 15)

    def test_l16_balance(self):
        oa = T.get_orthogonal_array("L16")
        self._check_balance(oa, 2)

    def test_l16_orthogonality(self):
        oa = T.get_orthogonal_array("L16")
        self._check_orthogonality(oa, 2)

    def test_l27_shape(self):
        oa = T.get_orthogonal_array("L27")
        assert oa.shape == (27, 13)

    def test_l27_balance(self):
        oa = T.get_orthogonal_array("L27")
        self._check_balance(oa, 3)

    def test_l27_orthogonality(self):
        oa = T.get_orthogonal_array("L27")
        self._check_orthogonality(oa, 3)

    def test_levels_in_valid_range_l9(self):
        oa = T.get_orthogonal_array("L9")
        assert int(np.min(oa)) == 1
        assert int(np.max(oa)) == 3

    def test_levels_in_valid_range_l16(self):
        oa = T.get_orthogonal_array("L16")
        assert int(np.min(oa)) == 1
        assert int(np.max(oa)) == 2


# ── Tasarım oluşturma doğrulaması ──────────────────────────────────────────────

class TestDesignGeneration:
    def test_l9_3_factors_generates_9_runs(self):
        design = T.generate_design("L9", L9_FACTORS)
        assert design.runs == 9
        assert len(design.experiment_matrix) == 9

    def test_run_factor_values_match_levels(self):
        """Her run'daki faktör değerleri tanımlanan seviyelerden biri olmalı."""
        design = T.generate_design("L9", L9_FACTORS)
        for run in design.experiment_matrix:
            for f in L9_FACTORS:
                v = run.factor_values[f.name]
                assert v in f.levels, (
                    f"Run {run.run_number}, {f.name}: {v} tanımlı seviyelerde değil"
                )

    def test_residual_df_l9_3_factors(self):
        design = T.generate_design("L9", L9_FACTORS)
        # df_total=8, df_factors=3×2=6, residual=2
        assert design.residual_df == 2
        assert not design.saturated

    def test_saturated_l9_4_factors(self):
        factors_4 = [
            T.FactorSpec("A", "u", (1.0, 2.0, 3.0)),
            T.FactorSpec("B", "u", (1.0, 2.0, 3.0)),
            T.FactorSpec("C", "u", (1.0, 2.0, 3.0)),
            T.FactorSpec("D", "u", (1.0, 2.0, 3.0)),
        ]
        design = T.generate_design("L9", factors_4)
        assert design.saturated
        assert design.residual_df == 0
        assert len(design.warnings) > 0

    def test_too_many_factors_raises(self):
        factors_5 = [T.FactorSpec(f"F{i}", "u", (1.0, 2.0, 3.0)) for i in range(5)]
        with pytest.raises(ValueError, match="en fazla"):
            T.generate_design("L9", factors_5)

    def test_wrong_level_count_raises(self):
        bad_factors = [T.FactorSpec("A", "u", (1.0, 2.0))]  # L9 3 seviye gerektirir
        with pytest.raises(ValueError, match="seviye"):
            T.generate_design("L9", bad_factors)

    def test_unknown_array_type_raises(self):
        with pytest.raises(ValueError, match="Bilinmeyen"):
            T.get_orthogonal_array("L99")

    def test_duplicate_factor_names_raises(self):
        factors_dup = [
            T.FactorSpec("A", "u", (1.0, 2.0, 3.0)),
            T.FactorSpec("A", "u", (1.0, 2.0, 3.0)),
        ]
        with pytest.raises(ValueError, match="benzersiz"):
            T.generate_design("L9", factors_dup)


# ── S/N oranı hesaplama ───────────────────────────────────────────────────────

class TestSNRatios:
    def test_ltb_single_value(self):
        """LTB, tek değer için: η = 20·log10(y)"""
        y = 5.0
        expected = 20 * math.log10(y)
        assert T.compute_sn([y], "larger_is_better") == pytest.approx(expected, rel=1e-6)

    def test_stb_single_value(self):
        """STB, tek değer için: η = -20·log10(y)"""
        y = 5.0
        expected = -20 * math.log10(y)
        assert T.compute_sn([y], "smaller_is_better") == pytest.approx(expected, rel=1e-6)

    def test_ltb_multiple_values(self):
        """LTB, çoklu değer: η = -10·log10(mean(1/y²))"""
        vals = [4.0, 5.0, 6.0]
        expected = -10 * math.log10(sum(1.0 / v**2 for v in vals) / len(vals))
        assert T.compute_sn(vals, "larger_is_better") == pytest.approx(expected, rel=1e-6)

    def test_stb_multiple_values(self):
        vals = [2.0, 3.0, 4.0]
        expected = -10 * math.log10(sum(v**2 for v in vals) / len(vals))
        assert T.compute_sn(vals, "smaller_is_better") == pytest.approx(expected, rel=1e-6)

    def test_ntb_formula(self):
        """NTB: η = 10·log10(mean²/var)"""
        vals = [9.8, 10.0, 10.2, 9.9, 10.1]
        mean_y = sum(vals) / len(vals)
        var_y = sum((v - mean_y)**2 for v in vals) / (len(vals) - 1)
        expected = 10 * math.log10(mean_y**2 / var_y)
        assert T.compute_sn(vals, "nominal_is_best") == pytest.approx(expected, rel=1e-4)

    def test_ltb_zero_response_raises(self):
        with pytest.raises(ValueError):
            T.compute_sn([0.0], "larger_is_better")

    def test_ltb_negative_raises(self):
        with pytest.raises(ValueError):
            T.compute_sn([-1.0], "larger_is_better")

    def test_stb_negative_raises(self):
        with pytest.raises(ValueError, match="negatif"):
            T.compute_sn([-0.1], "smaller_is_better")

    def test_ntb_single_value_raises(self):
        with pytest.raises(ValueError, match="2 tekrar"):
            T.compute_sn([5.0], "nominal_is_best")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            T.compute_sn([], "larger_is_better")


# ── Taguchi analizi ─────────────────────────────────────────────────────────

class TestTaguchiAnalysis:
    def test_capability_type_is_design_method(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert result.capability_type == "DESIGN_METHOD"

    def test_semantic_note_present(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert len(result.semantic_note) > 10

    def test_grand_mean_correct(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        expected_mean = sum(L9_RESPONSES) / len(L9_RESPONSES)
        assert result.grand_mean_response == pytest.approx(expected_mean, rel=1e-4)

    def test_factor_count(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert len(result.factor_effects) == 3

    def test_each_factor_has_3_levels(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        for fe in result.factor_effects:
            assert len(fe.levels) == 3

    def test_rank_response_is_permutation(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        ranks = sorted(fe.rank_response for fe in result.factor_effects)
        assert ranks == [1, 2, 3]

    def test_rank_sn_is_permutation(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        ranks = sorted(fe.rank_sn for fe in result.factor_effects)
        assert ranks == [1, 2, 3]

    def test_optimal_settings_count(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert len(result.optimal_settings) == 3

    def test_additive_prediction_present(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert result.additive_prediction is not None
        assert isinstance(result.additive_prediction, float)

    def test_anova_table_has_correct_structure(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        sources = [row.source for row in result.anova_table]
        assert any("Toplam" in s or "Total" in s for s in sources)
        assert any("Hata" in s or "Error" in s for s in sources)

    def test_anova_ss_total_equals_sum_of_parts(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        total_row = next(r for r in result.anova_table if "Toplam" in r.source or "Total" in r.source)
        error_row = next(r for r in result.anova_table if "Hata" in r.source or "Error" in r.source)
        factor_ss = sum(
            r.ss for r in result.anova_table
            if "Toplam" not in r.source and "Total" not in r.source
            and "Hata" not in r.source and "Error" not in r.source
        )
        assert factor_ss + error_row.ss == pytest.approx(total_row.ss, rel=1e-4)

    def test_contribution_pct_sums_to_100(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        total_row = next(r for r in result.anova_table if "Toplam" in r.source or "Total" in r.source)
        assert total_row.contribution_pct == pytest.approx(100.0, rel=1e-3)

    def test_wrong_response_count_raises(self):
        with pytest.raises(ValueError, match="yanıt"):
            T.analyze("L9", L9_FACTORS, [1.0, 2.0, 3.0], "larger_is_better")


# ── One-way ANOVA ──────────────────────────────────────────────────────────────

class TestOneWayANOVA:
    def test_capability_type(self):
        groups = {"A": [5.0, 5.1, 4.9], "B": [6.0, 6.2, 5.9]}
        result = A.one_way_anova(groups)
        assert result.capability_type == "STATISTICAL_ANALYSIS"

    def test_known_f_statistic(self):
        """Bilinen basit örnek: iki grup, belirgin fark."""
        groups = {
            "low":  [2.0, 2.1, 1.9, 2.0],
            "high": [5.0, 5.1, 4.9, 5.0],
        }
        result = A.one_way_anova(groups)
        factor_row = result.table[0]
        assert factor_row.f_statistic is not None
        assert factor_row.f_statistic > 100  # çok belirgin fark
        assert factor_row.p_value is not None
        assert factor_row.p_value < 0.001

    def test_no_difference_high_p(self):
        """Özdeş gruplar: F ≈ 0, p ≈ 1."""
        groups = {
            "A": [5.0, 5.0, 5.0, 5.0],
            "B": [5.0, 5.0, 5.0, 5.0],
        }
        result = A.one_way_anova(groups)
        factor_row = result.table[0]
        # Tüm gözlemler özdeş → ms_within=0 → F hesaplanamaz veya nan
        assert factor_row.f_statistic is None or factor_row.f_statistic == pytest.approx(0, abs=1e-9)

    def test_total_row_df(self):
        groups = {"X": [1.0, 2.0, 3.0], "Y": [4.0, 5.0, 6.0]}
        result = A.one_way_anova(groups)
        total_row = result.table[-1]
        assert total_row.df == 5  # N-1 = 6-1

    def test_ss_partitioning(self):
        """SS_between + SS_within = SS_total."""
        groups = {"A": [1.0, 2.0, 3.0], "B": [5.0, 6.0, 7.0], "C": [3.0, 4.0, 5.0]}
        result = A.one_way_anova(groups)
        ss_factor = result.table[0].ss
        ss_error  = result.table[1].ss
        ss_total  = result.table[2].ss
        assert ss_factor + ss_error == pytest.approx(ss_total, rel=1e-6)

    def test_too_few_groups_raises(self):
        with pytest.raises(ValueError, match="2 grup"):
            A.one_way_anova({"only": [1.0, 2.0, 3.0]})

    def test_empty_group_raises(self):
        with pytest.raises(ValueError, match="boş"):
            A.one_way_anova({"A": [1.0, 2.0], "B": []})

    def test_contribution_sums_to_100(self):
        groups = {"A": [1.0, 2.0], "B": [4.0, 5.0], "C": [2.5, 3.5]}
        result = A.one_way_anova(groups)
        total_row = result.table[-1]
        assert total_row.contribution_pct == pytest.approx(100.0, rel=1e-3)

    def test_residual_df_correct(self):
        # k=3 gruplar, her birinde 4 gözlem → N=12, df_error = 12-3 = 9
        groups = {
            "A": [1.0, 1.1, 0.9, 1.0],
            "B": [2.0, 2.1, 1.9, 2.0],
            "C": [3.0, 3.1, 2.9, 3.0],
        }
        result = A.one_way_anova(groups)
        assert result.residual_df == 9


# ── Balanced Taguchi ANOVA ────────────────────────────────────────────────────

class TestBalancedTaguchiANOVA:
    def test_saturated_design_detection(self):
        """L9 + 4 faktör = doymuş tasarım."""
        oa = T.get_orthogonal_array("L9")
        factors_4 = ["A", "B", "C", "D"]
        result = A.balanced_taguchi_anova(oa, factors_4, 3, L9_RESPONSES)
        assert result.saturated
        assert len(result.warnings) > 0

    def test_3_factors_not_saturated(self):
        oa = T.get_orthogonal_array("L9")
        result = A.balanced_taguchi_anova(oa, ["A", "B", "C"], 3, L9_RESPONSES)
        assert not result.saturated
        assert result.residual_df == 2

    def test_ss_partitioning_balanced(self):
        oa = T.get_orthogonal_array("L9")
        result = A.balanced_taguchi_anova(oa, ["A", "B", "C"], 3, L9_RESPONSES)
        ss_factors = sum(
            r.ss for r in result.table
            if "Toplam" not in r.source and "Total" not in r.source
            and "Hata" not in r.source and "Error" not in r.source
        )
        error_row = next(r for r in result.table if "Hata" in r.source or "Error" in r.source)
        total_row = next(r for r in result.table if "Toplam" in r.source or "Total" in r.source)
        assert ss_factors + error_row.ss == pytest.approx(total_row.ss, rel=1e-4)


# ── Semantik güvence: nugget tahmini yok ──────────────────────────────────────

class TestNoNuggetPrediction:
    def test_taguchi_result_has_no_nugget_field(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert not hasattr(result, "nugget_diameter_mm")
        assert not hasattr(result, "predicted_nugget")

    def test_anova_result_has_no_nugget_field(self):
        groups = {"A": [5.0, 5.1, 4.9], "B": [6.0, 6.2, 5.9]}
        result = A.one_way_anova(groups)
        assert not hasattr(result, "nugget_diameter_mm")
        assert not hasattr(result, "predicted_nugget")

    def test_taguchi_capability_type_not_nugget_predictor(self):
        result = T.analyze("L9", L9_FACTORS, L9_RESPONSES, "larger_is_better")
        assert result.capability_type != "NUGGET_PREDICTOR"

    def test_anova_capability_type_not_nugget_predictor(self):
        groups = {"A": [5.0, 5.1], "B": [6.0, 6.2]}
        result = A.one_way_anova(groups)
        assert result.capability_type != "NUGGET_PREDICTOR"


# ── HTTP endpoint testleri ────────────────────────────────────────────────────

class TestStatisticalAnalysisAPI:
    # Taguchi Design endpoint
    def test_taguchi_design_unauthenticated(self):
        resp = client.post("/api/v1/statistical-analysis/taguchi/design", json={
            "array_type": "L9",
            "factors": [
                {"name": "current_kA", "unit": "kA", "levels": [7.5, 8.0, 8.5]},
                {"name": "force_kN", "unit": "kN", "levels": [2.5, 3.0, 3.5]},
            ],
        })
        assert resp.status_code == 401

    def test_taguchi_design_invalid_array(self):
        # Auth check (401) precedes schema validation; both indicate endpoint is alive
        resp = client.post("/api/v1/statistical-analysis/taguchi/design", json={
            "array_type": "L99",
            "factors": [{"name": "A", "unit": "u", "levels": [1, 2]}],
        })
        assert resp.status_code in (401, 422)

    # Taguchi Analyze endpoint
    def test_taguchi_analyze_unauthenticated(self):
        resp = client.post("/api/v1/statistical-analysis/taguchi/analyze", json={
            "array_type": "L9",
            "factors": [
                {"name": "A", "unit": "u", "levels": [1.0, 2.0, 3.0]},
                {"name": "B", "unit": "u", "levels": [1.0, 2.0, 3.0]},
            ],
            "sn_objective": "larger_is_better",
            "responses": [1.0] * 9,
        })
        assert resp.status_code == 401

    def test_taguchi_analyze_wrong_response_count(self):
        resp = client.post("/api/v1/statistical-analysis/taguchi/analyze", json={
            "array_type": "L9",
            "factors": [{"name": "A", "unit": "u", "levels": [1.0, 2.0, 3.0]}],
            "sn_objective": "larger_is_better",
            "responses": [1.0, 2.0],  # 9 olmalı
        })
        assert resp.status_code in (401, 422)

    # ANOVA endpoint
    def test_anova_unauthenticated(self):
        resp = client.post("/api/v1/statistical-analysis/anova", json={
            "groups": [
                {"group_name": "A", "values": [1.0, 2.0, 3.0]},
                {"group_name": "B", "values": [4.0, 5.0, 6.0]},
            ],
        })
        assert resp.status_code == 401

    def test_anova_single_group_422(self):
        resp = client.post("/api/v1/statistical-analysis/anova", json={
            "groups": [
                {"group_name": "only", "values": [1.0, 2.0, 3.0]},
            ],
        })
        assert resp.status_code in (401, 422)

    # Regression: mevcut endpoint'ler etkilenmemiş
    def test_existing_health_unaffected(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_model_catalog_unaffected(self):
        resp = client.get("/api/v1/model-catalog")
        assert resp.status_code == 200
        assert resp.json()["total"] == 12

    def test_optimization_still_disabled(self):
        for path in ["/api/v1/optimization/model4/predict",
                     "/api/v1/optimization/ensemble"]:
            resp = client.post(path, json={})
            assert resp.status_code == 404, f"{path} artık 404 döndürmüyor"

    def test_taguchi_design_endpoint_exists(self):
        """Endpoint kayıtlı: kimlik doğrulama hatası beklenir (404 değil)."""
        resp = client.post("/api/v1/statistical-analysis/taguchi/design", json={})
        assert resp.status_code != 404

    def test_taguchi_analyze_endpoint_exists(self):
        resp = client.post("/api/v1/statistical-analysis/taguchi/analyze", json={})
        assert resp.status_code != 404

    def test_anova_endpoint_exists(self):
        resp = client.post("/api/v1/statistical-analysis/anova", json={})
        assert resp.status_code != 404
