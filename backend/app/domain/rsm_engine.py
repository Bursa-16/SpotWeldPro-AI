"""
rsm_engine.py — Yanıt Yüzeyi Metodolojisi motoru (SpotWeldPro AI).

KAPASITE: NUGGET_PREDICTOR
YÖNETİŞİM: EXPERIMENTAL — router_active=False
SEMANTİK: İkinci dereceden polinom yanıt yüzeyi — lineer, karesel ve etkileşim.
  Katsayılar daima kullanıcının sağladığı deney verisinden fit edilir.
  Sabit katsayı yoktur.

Model formu (k faktör, tam ikinci derece)
-----------------------------------------
  ŷ = β₀ + Σᵢβᵢxᵢ + Σᵢβᵢᵢxᵢ² + Σᵢ<ⱼβᵢⱼxᵢxⱼ
  Terim sayısı: 1 + k(k+3)/2

Kodlama (isteğe bağlı, veriden otomatik)
  x_coded = (x_physical − center) / scale
  center = (x_max + x_min) / 2
  scale  = (x_max − x_min) / 2

Extrapolasyon tanımı
  x_physical < domain_min  veya  x_physical > domain_max  →  OUT_OF_DOMAIN
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import combinations
from typing import Optional

import numpy as np
from scipy import linalg as sp_linalg


CAPABILITY_TYPE     = "NUGGET_PREDICTOR"
GOVERNANCE_STATUS   = "EXPERIMENTAL"
ROUTER_ACTIVE       = False
CONDITION_THRESHOLD = 1_000.0


# ── Enumerator ────────────────────────────────────────────────────────────────

class RSMOrder(StrEnum):
    FIRST  = "first"   # yalnızca lineer terimler
    SECOND = "second"  # lineer + karesel + etkileşim


# ── Veri tipleri ──────────────────────────────────────────────────────────────

@dataclass
class RSMFactor:
    """Tek bir RSM faktörünün tanımı."""
    name: str
    unit: str
    center: Optional[float] = None   # None → veriden otomatik
    scale: Optional[float] = None    # None → veriden otomatik


@dataclass
class RSMFit:
    """Fit edilmiş RSM modeli — sabit katsayı yoktur."""
    capability_type: str = CAPABILITY_TYPE
    governance_status: str = GOVERNANCE_STATUS
    router_active: bool = ROUTER_ACTIVE
    order: str = RSMOrder.SECOND
    factor_names: list[str] = field(default_factory=list)
    factor_units: dict[str, str] = field(default_factory=dict)
    centers: dict[str, float] = field(default_factory=dict)
    scales: dict[str, float] = field(default_factory=dict)
    term_labels: list[str] = field(default_factory=list)
    coefficients: list[float] = field(default_factory=list)
    n_obs: int = 0
    n_terms: int = 0
    residual_df: int = 0
    rmse_mm: float = 0.0
    mae_mm: float = 0.0
    bias_mm: float = 0.0
    r2: float = 0.0
    r2_adjusted: Optional[float] = None
    condition_number: float = 0.0
    rank_deficient: bool = False
    effective_rank: int = 0
    warnings: list[str] = field(default_factory=list)
    domain_min: dict[str, float] = field(default_factory=dict)
    domain_max: dict[str, float] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    measurement_bases: list[str] = field(default_factory=list)


@dataclass
class RSMPrediction:
    predicted_nugget_mm: float
    in_domain: bool
    extrapolated_factors: list[str]
    coded_distances: dict[str, float]   # |x_coded|; > 1.0 → eğitim kolu dışı
    warnings: list[str] = field(default_factory=list)


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _term_labels(factor_names: list[str], order: RSMOrder) -> list[str]:
    labels = ["intercept"]
    labels += list(factor_names)
    if order == RSMOrder.SECOND:
        labels += [f"{fn}^2" for fn in factor_names]
        labels += [f"{fi}*{fj}" for fi, fj in combinations(factor_names, 2)]
    return labels


def n_terms(k: int, order: RSMOrder) -> int:
    """k faktör için toplam terim sayısı."""
    if order == RSMOrder.FIRST:
        return 1 + k
    return 1 + k + k + k * (k - 1) // 2


def _design_row(x_coded: list[float], order: RSMOrder) -> list[float]:
    """Kodlanmış x vektöründen tek tasarım matrisi satırı üretir."""
    row: list[float] = [1.0] + list(x_coded)
    if order == RSMOrder.SECOND:
        row += [xi ** 2 for xi in x_coded]
        row += [x_coded[i] * x_coded[j] for i, j in combinations(range(len(x_coded)), 2)]
    return row


def _code(
    values: dict[str, float],
    factor_names: list[str],
    centers: dict[str, float],
    scales: dict[str, float],
) -> list[float]:
    coded = []
    for fn in factor_names:
        sc = scales[fn]
        coded.append((values[fn] - centers[fn]) / sc if sc != 0 else 0.0)
    return coded


# ── Ana fonksiyonlar ──────────────────────────────────────────────────────────

def fit_rsm(
    records: list[dict],
    factors: list[RSMFactor],
    order: RSMOrder = RSMOrder.SECOND,
) -> RSMFit:
    """
    Deney kayıtlarından RSM modeli fit eder.

    Parameters
    ----------
    records : Her biri {"features": {faktör_adı: değer},
                        "nugget_diameter_mm": float, ...} içeren liste.
    factors : RSMFactor tanımları.
    order   : FIRST (lineer) veya SECOND (tam ikinci derece).

    Raises
    ------
    ValueError : Eksik alan, geçersiz hedef veya yetersiz N durumunda.
    """
    if not factors:
        raise ValueError("En az bir faktör tanımlanmalı.")
    if len(records) < 2:
        raise ValueError("Fit için en az 2 kayıt gerekli.")

    factor_names = [f.name for f in factors]
    k = len(factor_names)
    p = n_terms(k, order)
    n = len(records)
    warnings_: list[str] = []

    if n < p + 1:
        raise ValueError(
            f"N={n} kayıt, {p} terim için yetersiz; en az N={p + 1} gerekli."
        )

    # ─ Ham veri ─
    X_phys = np.zeros((n, k), dtype=float)
    y = np.zeros(n, dtype=float)

    for i, rec in enumerate(records):
        nug = rec.get("nugget_diameter_mm")
        if nug is None or not math.isfinite(float(nug)) or float(nug) <= 0:
            raise ValueError(
                f"Kayıt {i}: nugget_diameter_mm={nug!r} eksik/geçersiz."
            )
        y[i] = float(nug)
        for j, fn in enumerate(factor_names):
            v = rec.get("features", {}).get(fn)
            if v is None:
                raise ValueError(f"Kayıt {i}: '{fn}' faktörü eksik.")
            fv = float(v)
            if not math.isfinite(fv):
                raise ValueError(f"Kayıt {i}: '{fn}'={v} sonsuz/NaN.")
            X_phys[i, j] = fv

    # ─ Tekrar kontrolü ─
    unique_x = {tuple(X_phys[i]) for i in range(n)}
    if len(unique_x) < n:
        warnings_.append(
            f"Tekrar eden deney koşulu: {n - len(unique_x)} kopya. "
            "Veri sızıntısı riski değerlendirilmeli."
        )

    # ─ Proveniyet ─
    sources = sorted({str(rec.get("source", "unknown")) for rec in records})
    measurement_bases = sorted({str(rec.get("measurement_basis", "unknown")) for rec in records})

    # ─ Merkez ve ölçek ─
    centers: dict[str, float] = {}
    scales: dict[str, float] = {}
    domain_min: dict[str, float] = {}
    domain_max: dict[str, float] = {}

    for j, fac in enumerate(factors):
        col = X_phys[:, j]
        lo, hi = float(np.min(col)), float(np.max(col))
        domain_min[fac.name] = lo
        domain_max[fac.name] = hi
        centers[fac.name] = fac.center if fac.center is not None else (lo + hi) / 2.0
        sc = fac.scale if fac.scale is not None else (hi - lo) / 2.0
        if sc == 0.0:
            sc = 1.0
            warnings_.append(
                f"'{fac.name}' faktörü sabit ({lo:.4g}); ölçek=1 olarak ayarlandı."
            )
        scales[fac.name] = sc

    # ─ Tasarım matrisi ─
    rows = []
    for i in range(n):
        x_phys = {fn: X_phys[i, j] for j, fn in enumerate(factor_names)}
        x_coded = _code(x_phys, factor_names, centers, scales)
        rows.append(_design_row(x_coded, order))

    X = np.array(rows, dtype=float)
    labels = _term_labels(factor_names, order)

    # ─ OLS ─
    beta, _, rank, sv = sp_linalg.lstsq(X, y)
    kappa = float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf")
    rank_deficient = (rank < p) or (kappa > CONDITION_THRESHOLD)

    if rank_deficient:
        warnings_.append(
            f"Rank eksikliği: efektif rank={rank}, beklenen={p}, κ={kappa:.1f}. "
            "Tasarım noktaları yetersiz veya faktörler bağımlı olabilir."
        )

    # ─ Metrikler ─
    y_hat = X @ beta
    residuals = y - y_hat
    ss_res = float(np.dot(residuals, residuals))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    residual_df = n - p
    s2 = ss_res / residual_df if residual_df > 0 else 0.0
    rmse = math.sqrt(s2) if s2 >= 0 else 0.0
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    r2_adjusted = (
        1.0 - (1.0 - r2) * (n - 1) / (n - p)
        if residual_df > 0 and ss_tot > 0
        else None
    )

    return RSMFit(
        order=str(order),
        factor_names=factor_names,
        factor_units={f.name: f.unit for f in factors},
        centers=centers,
        scales=scales,
        term_labels=labels,
        coefficients=[round(float(b), 8) for b in beta],
        n_obs=n,
        n_terms=p,
        residual_df=residual_df,
        rmse_mm=round(rmse, 6),
        mae_mm=round(float(np.mean(np.abs(residuals))), 6),
        bias_mm=round(float(np.mean(residuals)), 6),
        r2=round(r2, 6),
        r2_adjusted=round(r2_adjusted, 6) if r2_adjusted is not None else None,
        condition_number=round(kappa, 2),
        rank_deficient=rank_deficient,
        effective_rank=int(rank),
        warnings=warnings_,
        domain_min=domain_min,
        domain_max=domain_max,
        sources=sources,
        measurement_bases=measurement_bases,
    )


def predict_rsm(fit: RSMFit, features: dict[str, float]) -> RSMPrediction:
    """
    Fit edilmiş RSM modeli ile tahmin üretir.

    Returns
    -------
    RSMPrediction : Tahmin, alan durumu ve extrapolasyon bilgisi.
    """
    warnings_: list[str] = []
    extrapolated: list[str] = []
    coded_distances: dict[str, float] = {}

    order = RSMOrder(fit.order)

    for fn in fit.factor_names:
        v = features.get(fn)
        if v is None:
            raise ValueError(f"Tahmin için '{fn}' faktörü eksik.")
        fv = float(v)
        if not math.isfinite(fv):
            raise ValueError(f"'{fn}'={v} sonsuz/NaN.")
        sc = fit.scales[fn]
        x_c = (fv - fit.centers[fn]) / sc if sc != 0 else 0.0
        coded_distances[fn] = round(abs(x_c), 4)
        if fv < fit.domain_min[fn] or fv > fit.domain_max[fn]:
            extrapolated.append(fn)

    x_coded = _code(features, fit.factor_names, fit.centers, fit.scales)
    design_row = np.array(_design_row(x_coded, order), dtype=float)
    prediction = float(np.dot(fit.coefficients, design_row))

    if extrapolated:
        warnings_.append(
            f"EXTRAPOLATION_WARNING: {extrapolated} eğitim alanı dışında. "
            "Karesel terimler uzak noktalarda güvenilmez değerler verir."
        )
    if prediction <= 0:
        warnings_.append(
            f"Tahmin ≤ 0 ({prediction:.4f} mm); fiziksel geçerliliği yok."
        )

    return RSMPrediction(
        predicted_nugget_mm=round(prediction, 4),
        in_domain=len(extrapolated) == 0,
        extrapolated_factors=extrapolated,
        coded_distances=coded_distances,
        warnings=warnings_,
    )
