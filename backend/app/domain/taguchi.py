"""
taguchi.py — Taguchi Deney Tasarımı motoru (SpotWeldPro AI).

KAPASITE: DESIGN_METHOD
SEMANTİK: Ortogonal dizi tasarlar ve ölçülen yanıtları analiz eder.
  Bu modül nugget çapı TAHMİN ETMEZ; yanıt değerleri her zaman
  kullanıcının gerçek deneyden ölçtüğü verilerdir.

Desteklenen diziler:
  L4  (2-seviye, en fazla  3 faktör,  4 run)
  L9  (3-seviye, en fazla  4 faktör,  9 run)
  L16 (2-seviye, en fazla 15 faktör, 16 run)
  L27 (3-seviye, en fazla 13 faktör, 27 run)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional

import numpy as np


# ── Enum tanımları ────────────────────────────────────────────────────────────

class SNObjective(StrEnum):
    LARGER_IS_BETTER  = "larger_is_better"
    SMALLER_IS_BETTER = "smaller_is_better"
    NOMINAL_IS_BEST   = "nominal_is_best"


class ArrayType(StrEnum):
    L4  = "L4"
    L9  = "L9"
    L16 = "L16"
    L27 = "L27"


# ── Dizi özellikleri ──────────────────────────────────────────────────────────

ARRAY_SPECS: dict[str, dict] = {
    "L4":  {"levels": 2, "max_factors": 3,  "runs": 4},
    "L9":  {"levels": 3, "max_factors": 4,  "runs": 9},
    "L16": {"levels": 2, "max_factors": 15, "runs": 16},
    "L27": {"levels": 3, "max_factors": 13, "runs": 27},
}


# ── Sabit küçük diziler ───────────────────────────────────────────────────────

_L4_MATRIX = np.array([
    [1, 1, 1],
    [1, 2, 2],
    [2, 1, 2],
    [2, 2, 1],
], dtype=np.int8)

_L9_MATRIX = np.array([
    [1, 1, 1, 1],
    [1, 2, 2, 2],
    [1, 3, 3, 3],
    [2, 1, 2, 3],
    [2, 2, 3, 1],
    [2, 3, 1, 2],
    [3, 1, 3, 2],
    [3, 2, 1, 3],
    [3, 3, 2, 1],
], dtype=np.int8)


def _make_l16() -> np.ndarray:
    """L16(2^15): GF(2) parite inşasıyla 16 run × 15 sütun."""
    result = np.empty((16, 15), dtype=np.int8)
    for j in range(1, 16):
        for i in range(16):
            result[i, j - 1] = bin(i & j).count("1") % 2 + 1
    return result


def _make_l27() -> np.ndarray:
    """
    L27(3^13): GF(3) nokta çarpımı inşasıyla 27 run × 13 sütun.
    13 sütun, GF(3)^3 uzayının 13 tek boyutlu alt uzayına karşılık gelir.
    """
    generators = [
        (1, 0, 0), (0, 1, 0), (0, 0, 1),
        (1, 1, 0), (1, 2, 0),
        (1, 0, 1), (1, 0, 2),
        (0, 1, 1), (0, 1, 2),
        (1, 1, 1), (1, 1, 2), (1, 2, 1), (1, 2, 2),
    ]
    result = np.empty((27, 13), dtype=np.int8)
    run = 0
    for a in range(3):
        for b in range(3):
            for c in range(3):
                for j, (p, q, r) in enumerate(generators):
                    result[run, j] = (a * p + b * q + c * r) % 3 + 1
                run += 1
    return result


_ARRAY_CACHE: dict[str, np.ndarray] = {}


def get_orthogonal_array(array_type: str) -> np.ndarray:
    if array_type not in _ARRAY_CACHE:
        if array_type == "L4":
            _ARRAY_CACHE[array_type] = _L4_MATRIX
        elif array_type == "L9":
            _ARRAY_CACHE[array_type] = _L9_MATRIX
        elif array_type == "L16":
            _ARRAY_CACHE[array_type] = _make_l16()
        elif array_type == "L27":
            _ARRAY_CACHE[array_type] = _make_l27()
        else:
            raise ValueError(f"Bilinmeyen dizi tipi: {array_type!r}")
    return _ARRAY_CACHE[array_type]


# ── Domain veri tipleri ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class FactorSpec:
    name: str
    unit: str
    levels: tuple[float, ...]


@dataclass(frozen=True)
class ExperimentRun:
    run_number: int
    factor_values: dict[str, float]


@dataclass
class TaguchiDesign:
    array_type: str
    runs: int
    n_factors: int
    levels_per_factor: int
    degrees_of_freedom: dict[str, int]
    residual_df: int
    saturated: bool
    experiment_matrix: list[ExperimentRun]
    warnings: list[str]


@dataclass(frozen=True)
class LevelEffect:
    level_index: int
    level_value: float
    mean_response: float
    sn_ratio: float


@dataclass
class FactorEffect:
    factor_name: str
    unit: str
    levels: list[LevelEffect]
    delta_response: float
    delta_sn: float
    rank_response: int
    rank_sn: int


@dataclass
class OptimalSetting:
    factor_name: str
    unit: str
    optimal_level_index: int
    optimal_level_value: float


@dataclass
class TaguchiANOVARow:
    source: str
    ss: float
    df: int
    ms: float
    f_statistic: Optional[float]
    p_value: Optional[float]
    contribution_pct: Optional[float]
    note: str = ""


@dataclass
class TaguchiAnalysisResult:
    capability_type: str = "DESIGN_METHOD"
    semantic_note: str = (
        "Taguchi analizi parametre seviylerini optimize eder; nugget çapını tahmin etmez. "
        "Yanıt değerleri kullanıcı tarafından ölçülen gerçek deney sonuçlarıdır."
    )
    array_type: str = "L9"
    n_runs: int = 0
    n_factors: int = 0
    sn_objective: str = "larger_is_better"
    grand_mean_response: float = 0.0
    grand_mean_sn: float = 0.0
    factor_effects: list[FactorEffect] = field(default_factory=list)
    optimal_settings: list[OptimalSetting] = field(default_factory=list)
    additive_prediction: Optional[float] = None
    additive_prediction_note: str = ""
    anova_table: list[TaguchiANOVARow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ── Doğrulama ─────────────────────────────────────────────────────────────────

def validate_design_inputs(
    array_type: str,
    factors: list[FactorSpec],
) -> list[str]:
    """Doğrulama hatası listesi döndürür; boş liste = geçerli."""
    errors: list[str] = []
    if array_type not in ARRAY_SPECS:
        errors.append(f"Geçersiz dizi tipi: {array_type!r}. Geçerli: L4, L9, L16, L27.")
        return errors
    spec = ARRAY_SPECS[array_type]
    n_factors = len(factors)
    expected_levels = spec["levels"]
    if n_factors == 0:
        errors.append("En az 1 faktör gerekli.")
    if n_factors > spec["max_factors"]:
        errors.append(
            f"{array_type} dizisi en fazla {spec['max_factors']} faktörü destekler; "
            f"{n_factors} faktör girildi."
        )
    names = [f.name for f in factors]
    if len(names) != len(set(names)):
        errors.append("Faktör isimleri benzersiz olmalı.")
    for f in factors:
        if len(f.levels) != expected_levels:
            errors.append(
                f"'{f.name}': {len(f.levels)} seviye girildi; "
                f"{array_type} {expected_levels} seviye gerektirir."
            )
        if len(set(f.levels)) != len(f.levels):
            errors.append(f"'{f.name}': tekrar eden seviye değerleri.")
    return errors


# ── Deney tasarımı oluşturma ──────────────────────────────────────────────────

def generate_design(
    array_type: str,
    factors: list[FactorSpec],
) -> TaguchiDesign:
    """Ortogonal dizi deney matrisini oluşturur."""
    errors = validate_design_inputs(array_type, factors)
    if errors:
        raise ValueError("; ".join(errors))

    spec = ARRAY_SPECS[array_type]
    oa = get_orthogonal_array(array_type)
    n_runs: int = spec["runs"]
    n_levels: int = spec["levels"]
    n_factors = len(factors)

    df_factors = {f.name: n_levels - 1 for f in factors}
    df_total = n_runs - 1
    residual_df = df_total - sum(df_factors.values())
    saturated = residual_df == 0

    warnings: list[str] = []
    if saturated:
        warnings.append(
            f"{array_type} dizisinde {n_factors} faktörle kalıntı serbestlik derecesi "
            f"sıfırdır (doymuş tasarım). ANOVA için hata varyansı tahmin edilemez."
        )
    elif residual_df < 2:
        warnings.append(
            f"Kalıntı serbestlik derecesi {residual_df} — hata ve etki güvenilir biçimde "
            f"ayrıştırılamaz. Daha büyük dizi veya daha az faktör önerilir."
        )

    matrix: list[ExperimentRun] = []
    for run_idx in range(n_runs):
        fv: dict[str, float] = {}
        for col_idx, f in enumerate(factors):
            level_code = int(oa[run_idx, col_idx])
            fv[f.name] = f.levels[level_code - 1]
        matrix.append(ExperimentRun(run_number=run_idx + 1, factor_values=fv))

    return TaguchiDesign(
        array_type=array_type,
        runs=n_runs,
        n_factors=n_factors,
        levels_per_factor=n_levels,
        degrees_of_freedom=df_factors,
        residual_df=residual_df,
        saturated=saturated,
        experiment_matrix=matrix,
        warnings=warnings,
    )


# ── S/N oranı hesaplama ───────────────────────────────────────────────────────

def compute_sn(responses: list[float], objective: str) -> float:
    """
    Tek run için S/N oranını hesaplar (tekrar yoksa tek değer).
    Formüller: LTB = 20·log10(y),  STB = -20·log10(y),
               NTB = 10·log10(ȳ²/s²) — en az 2 tekrar gerekli.
    """
    n = len(responses)
    if n == 0:
        raise ValueError("S/N hesaplama için en az 1 yanıt değeri gerekli.")
    y = np.array(responses, dtype=float)

    if objective == SNObjective.LARGER_IS_BETTER:
        if np.any(y <= 0):
            raise ValueError(
                "Büyük-daha-iyi S/N için tüm yanıt değerleri sıfırdan büyük olmalı."
            )
        return float(-10.0 * np.log10(np.mean(1.0 / (y ** 2))))

    if objective == SNObjective.SMALLER_IS_BETTER:
        if np.any(y < 0):
            raise ValueError(
                "Küçük-daha-iyi S/N için yanıt değerleri negatif olmamalı."
            )
        return float(-10.0 * np.log10(np.mean(y ** 2)))

    # NOMINAL_IS_BEST
    if n < 2:
        raise ValueError(
            "Nominal-en-iyi S/N için en az 2 tekrarlı ölçüm gerekli (varyans tahmini)."
        )
    mean_y = float(np.mean(y))
    var_y = float(np.var(y, ddof=1))
    if var_y <= 0:
        raise ValueError(
            "Nominal-en-iyi S/N: varyans sıfır — tüm yanıtlar aynı değer."
        )
    return float(10.0 * np.log10((mean_y ** 2) / var_y))


# ── Taguchi ANOVA (dengeli tasarım) ──────────────────────────────────────────

def _taguchi_anova_table(
    oa: np.ndarray,
    y: np.ndarray,
    factors: list[FactorSpec],
    n_levels: int,
) -> list[TaguchiANOVARow]:
    """
    Dengeli ortogonal dizi için ANOVA tablosu.
    Her run tek ölçüm içeriyorsa hata terimi sıfır veya havuzlamayı gerektirir.
    """
    from scipy import stats as sp_stats

    n_runs = len(y)
    grand_mean = float(np.mean(y))
    ss_total = float(np.sum((y - grand_mean) ** 2))
    df_total = n_runs - 1

    rows: list[TaguchiANOVARow] = []
    ss_factors = []

    for col_idx, f in enumerate(factors):
        ss_f = 0.0
        for lv in range(1, n_levels + 1):
            mask = oa[:, col_idx] == lv
            n_lv = int(np.sum(mask))
            mean_lv = float(np.mean(y[mask]))
            ss_f += n_lv * (mean_lv - grand_mean) ** 2
        df_f = n_levels - 1
        ms_f = ss_f / df_f
        ss_factors.append(ss_f)
        rows.append(TaguchiANOVARow(
            source=f.name,
            ss=round(ss_f, 6),
            df=df_f,
            ms=round(ms_f, 6),
            f_statistic=None,  # filled after error row
            p_value=None,
            contribution_pct=round(ss_f / ss_total * 100, 2) if ss_total > 0 else None,
        ))

    ss_error = ss_total - sum(ss_factors)
    df_error = df_total - sum(n_levels - 1 for _ in factors)

    note_error = ""
    if df_error <= 0:
        note_error = (
            "Doymuş tasarım: hata serbestlik derecesi ≤ 0. "
            "F ve p değerleri hesaplanamaz."
        )
    elif df_error < 2:
        note_error = f"Hata df={df_error} — p-değeri güvenilirliği düşük."

    ms_error = ss_error / df_error if df_error > 0 else float("nan")

    # F ve p değerlerini doldur
    for row in rows:
        if df_error > 0 and ms_error > 0 and not np.isnan(ms_error):
            f_val = row.ms / ms_error
            p_val = float(sp_stats.f.sf(f_val, row.df, df_error))
            row.f_statistic = round(f_val, 4)
            row.p_value = round(p_val, 5)

    rows.append(TaguchiANOVARow(
        source="Hata (Error)",
        ss=round(ss_error, 6),
        df=max(df_error, 0),
        ms=round(ms_error, 6) if not np.isnan(ms_error) else None,
        f_statistic=None,
        p_value=None,
        contribution_pct=round(ss_error / ss_total * 100, 2) if ss_total > 0 else None,
        note=note_error,
    ))
    rows.append(TaguchiANOVARow(
        source="Toplam (Total)",
        ss=round(ss_total, 6),
        df=df_total,
        ms=round(ss_total / df_total, 6) if df_total > 0 else None,
        f_statistic=None,
        p_value=None,
        contribution_pct=100.0,
    ))
    return rows


# ── Ana analiz fonksiyonu ─────────────────────────────────────────────────────

def analyze(
    array_type: str,
    factors: list[FactorSpec],
    responses: list[float],
    sn_objective: str,
) -> TaguchiAnalysisResult:
    """
    Taguchi deney sonuçlarını analiz eder.
    - Ana etkileri ve S/N oranlarını hesaplar.
    - Optimal seviyeleri belirler.
    - Katkılı model tahmini (etkileşim yok varsayımıyla) hesaplar.
    - Dengeli ANOVA tablosu ekler.

    ÖNEMLI: Bu fonksiyon nugget çapı tahmin etmez.
    'responses' parametresi kullanıcının ölçtüğü gerçek değerleri içermelidir.
    """
    errors = validate_design_inputs(array_type, factors)
    if errors:
        raise ValueError("; ".join(errors))

    spec = ARRAY_SPECS[array_type]
    n_runs: int = spec["runs"]
    n_levels: int = spec["levels"]

    if len(responses) != n_runs:
        raise ValueError(
            f"{array_type} {n_runs} run yanıtı bekliyor; {len(responses)} girildi."
        )

    oa = get_orthogonal_array(array_type)
    y = np.array(responses, dtype=float)
    n_factors = len(factors)

    grand_mean = float(np.mean(y))

    # Her run için S/N (tek tekrar, LTB/STB uygulanabilir)
    sn_per_run: list[float] = []
    sn_error: Optional[str] = None
    for r in responses:
        try:
            sn_per_run.append(compute_sn([r], sn_objective))
        except ValueError as e:
            sn_per_run.append(float("nan"))
            sn_error = str(e)

    sn_arr = np.array(sn_per_run, dtype=float)
    grand_mean_sn = float(np.nanmean(sn_arr))

    # Ana etkiler
    factor_effects: list[FactorEffect] = []
    for col_idx, f in enumerate(factors):
        level_effs: list[LevelEffect] = []
        for lv in range(1, n_levels + 1):
            mask = oa[:, col_idx] == lv
            mean_resp = float(np.mean(y[mask]))
            mean_sn = float(np.nanmean(sn_arr[mask]))
            level_effs.append(LevelEffect(
                level_index=lv,
                level_value=f.levels[lv - 1],
                mean_response=round(mean_resp, 4),
                sn_ratio=round(mean_sn, 4),
            ))
        delta_resp = max(le.mean_response for le in level_effs) - min(le.mean_response for le in level_effs)
        delta_sn = max(le.sn_ratio for le in level_effs) - min(le.sn_ratio for le in level_effs)
        factor_effects.append(FactorEffect(
            factor_name=f.name,
            unit=f.unit,
            levels=level_effs,
            delta_response=round(delta_resp, 4),
            delta_sn=round(delta_sn, 4),
            rank_response=0,
            rank_sn=0,
        ))

    sorted_resp = sorted(range(n_factors), key=lambda i: -factor_effects[i].delta_response)
    sorted_sn   = sorted(range(n_factors), key=lambda i: -factor_effects[i].delta_sn)
    for rank, idx in enumerate(sorted_resp):
        factor_effects[idx].rank_response = rank + 1
    for rank, idx in enumerate(sorted_sn):
        factor_effects[idx].rank_sn = rank + 1

    # Optimal seviyeler (en yüksek S/N)
    optimal_settings: list[OptimalSetting] = []
    for fe in factor_effects:
        best_lv = max(fe.levels, key=lambda le: le.sn_ratio)
        optimal_settings.append(OptimalSetting(
            factor_name=fe.factor_name,
            unit=fe.unit,
            optimal_level_index=best_lv.level_index,
            optimal_level_value=best_lv.level_value,
        ))

    # Katkılı model tahmini
    additive_pred = grand_mean + sum(
        max(fe.levels, key=lambda le: le.sn_ratio).mean_response - grand_mean
        for fe in factor_effects
    )

    # ANOVA tablosu
    anova_rows = _taguchi_anova_table(oa, y, factors, n_levels)

    # Uyarılar
    warnings: list[str] = []
    df_total = n_runs - 1
    residual_df = df_total - n_factors * (n_levels - 1)
    if residual_df <= 0:
        warnings.append(
            "Doymuş tasarım: kalıntı df ≤ 0. F ve p değerleri hesaplanamaz."
        )
    elif residual_df < 2:
        warnings.append(f"Kalıntı df = {residual_df} — istatistiksel güç düşük.")
    if sn_error:
        warnings.append(f"S/N hesaplama uyarısı: {sn_error}")

    return TaguchiAnalysisResult(
        array_type=array_type,
        n_runs=n_runs,
        n_factors=n_factors,
        sn_objective=sn_objective,
        grand_mean_response=round(grand_mean, 4),
        grand_mean_sn=round(grand_mean_sn, 4),
        factor_effects=factor_effects,
        optimal_settings=optimal_settings,
        additive_prediction=round(additive_pred, 4),
        additive_prediction_note=(
            "Katkılı model: faktörlerin bağımsız etki ettiğini varsayar. "
            "Etkileşim var ise tahmin sapabilir. Doğrulama deneyi zorunludur."
        ),
        anova_table=anova_rows,
        warnings=warnings,
    )
