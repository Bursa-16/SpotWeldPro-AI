"""
statistical_analysis.py — ANOVA motoru (SpotWeldPro AI).

KAPASITE: STATISTICAL_ANALYSIS
SEMANTİK: Faktör katkı paylarını ve istatistiksel anlamlılığı hesaplar.
  Bu modül nugget çapı TAHMİN ETMEZ; yanıt değerleri kullanıcının
  ölçtüğü gerçek verilerdir.

Desteklenen tasarımlar:
  one_way           — Tek faktörlü ANOVA (gruplar halinde gözlem)
  balanced_taguchi  — Dengeli ortogonal dizi ANOVA (L9/L27 çıktılarından)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional

import numpy as np
from scipy import stats as sp_stats


# ── Enum ────────────────────────────────────────────────────────────────────────

class ANOVADesignType(StrEnum):
    ONE_WAY          = "one_way"
    BALANCED_TAGUCHI = "balanced_taguchi"


# ── Veri tipleri ─────────────────────────────────────────────────────────────────

@dataclass
class ANOVARow:
    source: str
    ss: float
    df: int
    ms: Optional[float]
    f_statistic: Optional[float]
    p_value: Optional[float]
    contribution_pct: Optional[float]
    note: str = ""


@dataclass
class ANOVAResult:
    capability_type: str = "STATISTICAL_ANALYSIS"
    semantic_note: str = (
        "ANOVA faktör katkı yüzdelerini ve anlamlılığını hesaplar; "
        "nugget çapını tahmin etmez. Giriş değerleri kullanıcı tarafından "
        "ölçülen gerçek deney sonuçlarıdır."
    )
    design_type: str = "one_way"
    n_observations: int = 0
    grand_mean: float = 0.0
    table: list[ANOVARow] = field(default_factory=list)
    residual_df: int = 0
    rank_deficient: bool = False
    saturated: bool = False
    warnings: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _round_or_none(v: Optional[float], n: int = 6) -> Optional[float]:
    return round(v, n) if v is not None and not (isinstance(v, float) and np.isnan(v)) else None


# ── Tek faktörlü ANOVA ────────────────────────────────────────────────────────

def one_way_anova(
    groups: dict[str, list[float]],
    factor_name: str = "Factor",
    response_name: str = "Response",
) -> ANOVAResult:
    """
    Standart tek faktörlü ANOVA.

    Parameters
    ----------
    groups : dict[str, list[float]]
        Grup adı → gözlem değerleri listesi.
    factor_name : str
        ANOVA tablosundaki faktör satırının adı.
    response_name : str
        Yanıt değişkeninin adı (semantik kontrol kaydı için).

    Returns
    -------
    ANOVAResult
    """
    if len(groups) < 2:
        raise ValueError("Tek faktörlü ANOVA için en az 2 grup gerekli.")

    for name, vals in groups.items():
        if len(vals) == 0:
            raise ValueError(f"'{name}' grubu boş.")

    all_vals = [v for vals in groups.values() for v in vals]
    N = len(all_vals)
    k = len(groups)

    if N < k + 1:
        raise ValueError(
            f"Toplam gözlem sayısı ({N}) grup sayısından ({k}) fazla olmalı."
        )

    grand_mean = float(np.mean(all_vals))

    ss_between = float(sum(
        len(vals) * (float(np.mean(vals)) - grand_mean) ** 2
        for vals in groups.values()
    ))
    ss_within = float(sum(
        sum((v - float(np.mean(vals))) ** 2 for v in vals)
        for vals in groups.values()
    ))
    ss_total = ss_between + ss_within

    df_between = k - 1
    df_within = N - k

    if df_within < 1:
        raise ValueError(
            f"Grup içi serbestlik derecesi {df_within}; F-istatistiği hesaplanamaz. "
            "Her grupta en az 2 gözlem gerekli."
        )

    ms_between = ss_between / df_between
    ms_within  = ss_within  / df_within

    f_stat: Optional[float] = None
    p_val:  Optional[float] = None
    if ms_within > 0:
        f_stat = ms_between / ms_within
        p_val  = float(sp_stats.f.sf(f_stat, df_between, df_within))

    table: list[ANOVARow] = [
        ANOVARow(
            source=factor_name,
            ss=round(ss_between, 6),
            df=df_between,
            ms=_round_or_none(ms_between),
            f_statistic=_round_or_none(f_stat, 4),
            p_value=_round_or_none(p_val, 5),
            contribution_pct=round(ss_between / ss_total * 100, 2) if ss_total > 0 else None,
        ),
        ANOVARow(
            source="Hata (Error)",
            ss=round(ss_within, 6),
            df=df_within,
            ms=_round_or_none(ms_within),
            f_statistic=None,
            p_value=None,
            contribution_pct=round(ss_within / ss_total * 100, 2) if ss_total > 0 else None,
        ),
        ANOVARow(
            source="Toplam (Total)",
            ss=round(ss_total, 6),
            df=N - 1,
            ms=_round_or_none(ss_total / (N - 1)) if N > 1 else None,
            f_statistic=None,
            p_value=None,
            contribution_pct=100.0,
        ),
    ]

    warnings: list[str] = []
    if f_stat is None:
        warnings.append(
            "Grup içi varyans sıfır — tüm gruplar içinde gözlemler özdeş. "
            "F-istatistiği hesaplanamadı."
        )
    min_n = min(len(v) for v in groups.values())
    if min_n < 3:
        warnings.append(
            f"En küçük grup boyutu {min_n}; normallik varsayımı doğrulanamaz."
        )

    assumptions = [
        "Gözlemler bağımsız ve eşit dağılımdan geldiği varsayılır.",
        "Her grupta yaklaşık normallik beklenir (n<30 ise kritik).",
        "Varyans homojenliği (Levene veya Bartlett testi önerilir).",
    ]

    return ANOVAResult(
        design_type=ANOVADesignType.ONE_WAY,
        n_observations=N,
        grand_mean=round(grand_mean, 4),
        table=table,
        residual_df=df_within,
        rank_deficient=False,
        saturated=False,
        warnings=warnings,
        assumptions=assumptions,
    )


# ── Dengeli Taguchi ANOVA ─────────────────────────────────────────────────────

def balanced_taguchi_anova(
    oa: np.ndarray,
    factor_names: list[str],
    n_levels: int,
    responses: list[float],
) -> ANOVAResult:
    """
    Dengeli ortogonal dizi için ANOVA.

    Her faktör OA sütunlarına atanmıştır; her seviye eşit sayıda run içerir.
    Faktörler diziye tam atanırsa kalıntı df = 0 (doymuş tasarım); bu durumda
    F ve p değerleri hesaplanamaz.

    Parameters
    ----------
    oa : np.ndarray
        Ortogonal dizi matrisi (run × sütun), 1-tabanlı seviye kodlarıyla.
    factor_names : list[str]
        Her faktörün adı (OA sütunlarıyla aynı sıra).
    n_levels : int
        Dizi seviye sayısı (tüm faktörler aynı seviye sayısına sahip).
    responses : list[float]
        Her run için tek ölçüm değeri.
    """
    y = np.array(responses, dtype=float)
    n_runs = len(y)
    n_factors = len(factor_names)

    if oa.shape[0] != n_runs:
        raise ValueError(
            f"OA satır sayısı ({oa.shape[0]}) ile yanıt sayısı ({n_runs}) eşleşmiyor."
        )
    if oa.shape[1] < n_factors:
        raise ValueError(
            f"OA {oa.shape[1]} sütun içeriyor; {n_factors} faktör için yeterli değil."
        )

    grand_mean = float(np.mean(y))
    ss_total = float(np.sum((y - grand_mean) ** 2))
    df_total = n_runs - 1
    df_factor = n_levels - 1

    table: list[ANOVARow] = []
    ss_factors: list[float] = []

    for col_idx, fname in enumerate(factor_names):
        ss_f = 0.0
        for lv in range(1, n_levels + 1):
            mask = oa[:, col_idx] == lv
            n_lv = int(np.sum(mask))
            if n_lv == 0:
                continue
            mean_lv = float(np.mean(y[mask]))
            ss_f += n_lv * (mean_lv - grand_mean) ** 2
        ss_factors.append(ss_f)
        ms_f = ss_f / df_factor if df_factor > 0 else float("nan")
        table.append(ANOVARow(
            source=fname,
            ss=round(ss_f, 6),
            df=df_factor,
            ms=_round_or_none(ms_f),
            f_statistic=None,  # doldurulacak
            p_value=None,
            contribution_pct=round(ss_f / ss_total * 100, 2) if ss_total > 0 else None,
        ))

    ss_error = ss_total - sum(ss_factors)
    df_error = df_total - n_factors * df_factor
    saturated = df_error <= 0

    note_err = ""
    if saturated:
        note_err = (
            "Doymuş tasarım: kalıntı df ≤ 0. F ve p değerleri hesaplanamaz."
        )
    elif df_error < 2:
        note_err = f"Kalıntı df = {df_error} — p-değeri güvenilirliği düşük."

    ms_error: Optional[float] = None
    if df_error > 0:
        ms_error = ss_error / df_error

    # F ve p değerlerini doldur
    for row in table:
        if ms_error is not None and ms_error > 0 and not saturated:
            f_val = (row.ms or 0.0) / ms_error
            p_val = float(sp_stats.f.sf(f_val, row.df, df_error))
            row.f_statistic = round(f_val, 4)
            row.p_value     = round(p_val, 5)

    table.append(ANOVARow(
        source="Hata (Error)",
        ss=round(ss_error, 6),
        df=max(df_error, 0),
        ms=_round_or_none(ms_error),
        f_statistic=None,
        p_value=None,
        contribution_pct=round(ss_error / ss_total * 100, 2) if ss_total > 0 else None,
        note=note_err,
    ))
    table.append(ANOVARow(
        source="Toplam (Total)",
        ss=round(ss_total, 6),
        df=df_total,
        ms=_round_or_none(ss_total / df_total) if df_total > 0 else None,
        f_statistic=None,
        p_value=None,
        contribution_pct=100.0,
    ))

    warnings: list[str] = []
    if saturated:
        warnings.append(
            "Doymuş tasarım: ANOVA hata terimi tahmin edilemez. "
            "Daha az faktör atayın veya daha büyük ortogonal dizi kullanın."
        )
    if ss_error < 0:
        warnings.append(
            "Faktör SS toplamı toplam SS'yi aşıyor — veri tutarsızlığı olabilir."
        )

    return ANOVAResult(
        design_type=ANOVADesignType.BALANCED_TAGUCHI,
        n_observations=n_runs,
        grand_mean=round(grand_mean, 4),
        table=table,
        residual_df=max(df_error, 0),
        rank_deficient=False,
        saturated=saturated,
        warnings=warnings,
        assumptions=[
            "Dengeli dizi: her seviye her faktör için eşit tekrar sayısına sahip.",
            "Faktörler arasında etkileşim olmadığı varsayılır (katkılı model).",
            "Tekrarsız tasarımda hata terimi sıfır veya çok küçük olabilir.",
        ],
    )
