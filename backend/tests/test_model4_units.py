"""
test_model4_units.py — MODEL4-UNIT-FIX-01

Birim dönüşüm sözleşmesi:
  Model4Input / ValidationRow → kA ve kN cinsinden girer
  OptimizationService._to_model4_units() → A ve daN'a çevirir
  PolynomialModel.predict() → A ve daN cinsinden değerleri kullanır

Kapsam: dönüşüm köprüsü, sınır doğruluğu, çift dönüşüm koruması,
        mevcut API devre-dışı durumu.
"""
import pytest
from app.application.optimization_service import OptimizationService


# ── Ortak test girdisi ────────────────────────────────────────────────────────
_INPUT_KA_KN = {
    "Current": 8.0,      # kA
    "Force": 3.5,        # kN
    "Time": 12.0,        # çevrim
    "Cooling": 2.0,      # çevrim
    "Sequence": 1.0,     # çevrim
    "Holding": 3.0,      # çevrim
    "SheetThick": 1.5,   # mm
}

_INPUT_A_DAN = {
    "Current": 8000.0,   # A  (8 kA × 1000)
    "Force": 350.0,      # daN (3.5 kN × 100)
    "Time": 12.0,
    "Cooling": 2.0,
    "Sequence": 1.0,
    "Holding": 3.0,
    "SheetThick": 1.5,
}


@pytest.fixture(scope="module")
def svc():
    return OptimizationService()


# ── F-01 / F-02: Dönüşüm köprüsü ────────────────────────────────────────────

class TestToModel4Units:
    """_to_model4_units(): her birim dönüşümünün doğruluğu."""

    def test_current_8ka_to_8000a(self, svc):
        """8 kA → 8000 A (×1000)."""
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Current"] == pytest.approx(8000.0)

    def test_force_3_5kn_to_350dan(self, svc):
        """3,5 kN → 350 daN (×100; 1 kN = 100 daN)."""
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Force"] == pytest.approx(350.0)

    def test_time_cycles_unchanged(self, svc):
        """Zaman çevrimleri dönüştürülmez."""
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Time"] == pytest.approx(12.0)

    def test_cooling_cycles_unchanged(self, svc):
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Cooling"] == pytest.approx(2.0)

    def test_sequence_cycles_unchanged(self, svc):
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Sequence"] == pytest.approx(1.0)

    def test_holding_cycles_unchanged(self, svc):
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Holding"] == pytest.approx(3.0)

    def test_thickness_mm_unchanged(self, svc):
        """Kalınlık mm cinsinden değişmez."""
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["SheetThick"] == pytest.approx(1.5)

    def test_original_dict_not_mutated(self, svc):
        """Girdi sözlüğü yan etki içermemelidir."""
        inp = dict(_INPUT_KA_KN)
        svc._to_model4_units(inp)
        assert inp["Current"] == pytest.approx(8.0)
        assert inp["Force"] == pytest.approx(3.5)


# ── F-06: Çift dönüşüm koruması ──────────────────────────────────────────────

class TestNoDoubleConversion:
    """Köprü iki kez çağrılınca ikinci geçiş farklı (yanlış) değer üretir.
    Bu, dönüşümün akış içinde yalnızca bir kez uygulanması gerektiğini kanıtlar."""

    def test_double_conversion_differs(self, svc):
        once = svc._to_model4_units(dict(_INPUT_KA_KN))
        twice = svc._to_model4_units(once)
        # İkinci geçiş 8000 × 1000 = 8_000_000 üretir — tekli geçişten farklı
        assert twice["Current"] != pytest.approx(8000.0)
        assert twice["Force"]   != pytest.approx(350.0)

    def test_single_conversion_correct(self, svc):
        """Tek dönüşüm A ve daN değerlerini doğru üretir."""
        result = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert result["Current"] == pytest.approx(8000.0)
        assert result["Force"]   == pytest.approx(350.0)


# ── F-03: Fiziksel tutarlılık ─────────────────────────────────────────────────

class TestPhysicalEquivalence:
    """Aynı fiziksel nokta kA/kN veya A/daN olarak verildiğinde
    predict() aynı nugget sonucunu üretmelidir."""

    def test_ka_kn_equals_a_dan_after_conversion(self, svc):
        converted = svc._to_model4_units(dict(_INPUT_KA_KN))
        assert converted == pytest.approx(_INPUT_A_DAN)

    def test_predict_consistent_after_conversion(self, svc):
        converted = svc._to_model4_units(dict(_INPUT_KA_KN))
        result_from_converted = svc.model4.predict(converted)
        result_from_direct_a_dan = svc.model4.predict(_INPUT_A_DAN)
        assert result_from_converted == pytest.approx(result_from_direct_a_dan)


# ── F-04: kA girdisi negatif sonuç üretir (dönüşüm öncesi) ───────────────────

class TestUnitMismatchDetection:
    """Dönüşüm uygulanmadan kA geçirilirse negatif nugget üretilir.
    Bu, birim uyumsuzluğunun gözlemlenebilir etkisini belgeler."""

    def test_raw_ka_kn_produces_nonphysical_result(self, svc):
        """kA/kN olduğu gibi geçirilirse lineer akım katkısı çok küçük kalır."""
        raw_result = svc.model4.predict(_INPUT_KA_KN)
        correct_result = svc.model4.predict(_INPUT_A_DAN)
        # İki sonuç birbirinden büyük ölçüde farklı olmalıdır
        assert abs(raw_result - correct_result) > 50.0

    def test_conversion_moves_current_term(self, svc):
        """Dönüşümün Current katsayısına etkisi: 0.01390 × (8000-8) = 111.1 mm fark."""
        raw_result = svc.model4.predict(_INPUT_KA_KN)
        converted = svc._to_model4_units(dict(_INPUT_KA_KN))
        corrected_result = svc.model4.predict(converted)
        delta = corrected_result - raw_result
        # Current terimi katkısı: 0.01390 × (8000-8) ≈ 111 mm;
        # Force terimi katkısı: -0.1678 × (350-3.5) ≈ -58 mm
        # Net delta yaklaşık 50-60 mm civarında olmalı
        assert delta > 40.0


# ── F-07: Mevcut 404 davranışı değişmedi ─────────────────────────────────────

class TestOptimizationRoutesStillDisabled:
    """Optimizasyon router'ı hâlâ main.py'de kayıtlı değil."""

    @pytest.mark.parametrize("path", [
        "/api/v1/optimization/model4/predict",
        "/api/v1/optimization/doe",
        "/api/v1/optimization/ensemble",
        "/api/v1/optimization/model4/validate",
    ])
    def test_route_returns_404(self, client, path):
        r = client.post(path, json={})
        assert r.status_code == 404, f"{path} hâlâ 404 döndürmeli"
