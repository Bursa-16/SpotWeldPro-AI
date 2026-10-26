"""
mlr_engine.py — Çoklu Doğrusal Regresyon motoru (SpotWeldPro AI).

KAPASITE: NUGGET_PREDICTOR
YÖNETİŞİM: EXPERIMENTAL — router_active=False
SEMANTİK: Ölçülen nugget çapını sayısal girdilerden tahmin eder.
  Katsayılar daima kullanıcının sağladığı metalografik veri setinden fit edilir.
  Sabit katsayı yoktur.

Matematiksel temel
------------------
OLS  : β̂ = argmin ‖y − Xβ‖₂²  →  scipy.linalg.lstsq (pivotlanmış QR/SVD)
Koşul sayısı : κ = σ_max / σ_min  >  1 000  → rank_deficient=True
VIF  : VIF_j = 1 / (1 − R²_j),  R²_j  ←  X_j ~ diğer sütunlar regresyonu
Cook's D : D_i = r_i² · h_ii / (p · s² · (1 − h_ii)²)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional

import numpy as np
from scipy import linalg as sp_linalg


CAPABILITY_TYPE     = "NUGGET_PREDICTOR"
GOVERNANCE_STATUS   = "EXPERIMENTAL"
ROUTER_ACTIVE       = False
CONDITION_THRESHOLD = 1_000.0
VIF_THRESHOLD       = 10.0
_COOKS_SCALE        = 4.0      # Cook's D eşiği: 4/N (N küçükse muhafazakâr)


# ── Enumerator ────────────────────────────────────────────────────────────────

class MeasurementBasis(StrEnum):
    METALLOGRAPHIC = "metallographic"
    CALIPER        = "caliper"
    LITERATURE     = "literature"
    SIMULATED      = "simulated"
    SYNTHETIC      = "synthetic"


# ── Veri tipleri ──────────────────────────────────────────────────────────────

@dataclass
class MLRRecord:
    """Tek bir eğitim gözlemi."""
    features: dict[str, float]
    nugget_diameter_mm: float
    source: str
    measurement_basis: MeasurementBasis = MeasurementBasis.METALLOGRAPHIC
    material_family: str = ""
    thickness_mm: Optional[float] = None
    notes: str = ""


@dataclass
class MLRDiagnostics:
    condition_number: float
    rank_deficient: bool
    effective_rank: int
    vif: dict[str, float]
    cooks_d: list[float]
    influential_indices: list[int]
    high_vif_features: list[str]


@dataclass
class MLRFit:
    """Fit edilmiş MLR modeli — sabit katsayı yoktur."""
    capability_type: str = CAPABILITY_TYPE
    governance_status: str = GOVERNANCE_STATUS
    router_active: bool = ROUTER_ACTIVE
    feature_names: list[str] = field(default_factory=list)
    intercept: float = 0.0
    coefficients: dict[str, float] = field(default_factory=dict)
    n_obs: int = 0
    n_features: int = 0
    residual_df: int = 0
    rmse_mm: float = 0.0
    mae_mm: float = 0.0
    bias_mm: float = 0.0
    r2: float = 0.0
    r2_adjusted: Optional[float] = None
    s2: float = 0.0
    diagnostics: Optional[MLRDiagnostics] = None
    warnings: list[str] = field(default_factory=list)
    domain_min: dict[str, float] = field(default_factory=dict)
    domain_max: dict[str, float] = field(default_factory=dict)


@dataclass
class MLRPrediction:
    predicted_nugget_mm: float
    uncertainty_mm: Optional[float]
    in_domain: bool
    extrapolated_features: list[str]
    warnings: list[str] = field(default_factory=list)


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _hat_diagonal(X: np.ndarray) -> np.ndarray:
    """H matrisinin köşegen elemanları: h_ii = Σ_k Q[i,k]²."""
    try:
        Q, _ = np.linalg.qr(X, mode="reduced")
        return np.sum(Q ** 2, axis=1)
    except Exception:
        return np.zeros(X.shape[0])


def _compute_vif(X_no_intercept: np.ndarray, feature_names: list[str]) -> dict[str, float]:
    """VIF_j = 1 / (1 − R²_j) — R²_j: X_j'nin diğerlerine regresyon R²'si."""
    n, _ = X_no_intercept.shape
    vif: dict[str, float] = {}
    for j, name in enumerate(feature_names):
        y_j = X_no_intercept[:, j]
        others = np.delete(X_no_intercept, j, axis=1)
        X_oth = np.column_stack([np.ones(n), others])
        b, _, rank, _ = sp_linalg.lstsq(X_oth, y_j)
        if rank < X_oth.shape[1]:
            vif[name] = float("inf")
            continue
        y_hat = X_oth @ b
        ss_res = float(np.sum((y_j - y_hat) ** 2))
        ss_tot = float(np.sum((y_j - np.mean(y_j)) ** 2))
        r2_j = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
        vif[name] = 1.0 / (1.0 - r2_j) if r2_j < 1.0 else float("inf")
    return vif


def _cooks_distance(
    h: np.ndarray,
    residuals: np.ndarray,
    p: int,
    s2: float,
) -> list[float]:
    """D_i ≈ r_i² · h_ii / (p · s² · (1 − h_ii)²)."""
    if s2 <= 0 or p <= 0:
        return [0.0] * len(residuals)
    result = []
    for i, r in enumerate(residuals):
        hi = float(h[i])
        denom = p * s2 * (1.0 - hi) ** 2
        result.append(float(r ** 2 * hi / denom) if denom > 0 else 0.0)
    return result


# ── Ana fonksiyonlar ──────────────────────────────────────────────────────────

def fit_mlr(
    records: list[MLRRecord],
    feature_names: list[str],
) -> MLRFit:
    """
    Verilen kayıtlardan OLS ile MLR modeli fit eder.

    Raises
    ------
    ValueError : Eksik özellik, geçersiz hedef veya N < p + 1 durumunda.
    """
    if len(records) < 2:
        raise ValueError("Fit için en az 2 gözlem gerekli.")
    if not feature_names:
        raise ValueError("En az bir özellik adı belirtilmeli.")

    n = len(records)
    p = len(feature_names) + 1  # +1 intercept
    warnings_: list[str] = []

    if n < p + 1:
        raise ValueError(
            f"N={n} gözlem, {p} parametre için yetersiz; en az N={p + 1} gerekli."
        )

    # ─ Matris oluştur ─
    X_raw = np.zeros((n, len(feature_names)), dtype=float)
    y = np.zeros(n, dtype=float)

    for i, rec in enumerate(records):
        nug = rec.nugget_diameter_mm
        if not math.isfinite(nug) or nug <= 0:
            raise ValueError(
                f"Kayıt {i}: nugget_diameter_mm={nug!r} geçersiz; "
                "ölçülen pozitif değer gerekli."
            )
        y[i] = nug
        for j, fname in enumerate(feature_names):
            v = rec.features.get(fname)
            if v is None:
                raise ValueError(f"Kayıt {i}: '{fname}' özelliği eksik.")
            fv = float(v)
            if not math.isfinite(fv):
                raise ValueError(f"Kayıt {i}: '{fname}'={v} sonsuz/NaN değer.")
            X_raw[i, j] = fv

    # ─ Tekrar kontrolü ─
    unique_x = {tuple(X_raw[i]) for i in range(n)}
    if len(unique_x) < n:
        warnings_.append(
            f"Tekrar eden girdi satırı: {n - len(unique_x)} kopya. "
            "Veri sızıntısı riski değerlendirilmeli."
        )

    # ─ OLS ─
    X = np.column_stack([np.ones(n), X_raw])
    beta, _, rank, sv = sp_linalg.lstsq(X, y)

    kappa = float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf")
    rank_deficient = (rank < p) or (kappa > CONDITION_THRESHOLD)
    if rank_deficient:
        warnings_.append(
            f"Rank eksikliği: efektif rank={rank}, beklenen={p}, κ={kappa:.1f}. "
            "Çoklu bağıntı şüphesi."
        )

    # ─ Artıklar ve metrikler ─
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

    # ─ VIF ─
    vif = _compute_vif(X_raw, feature_names)
    high_vif = [f for f, v in vif.items() if v > VIF_THRESHOLD]
    if high_vif:
        warnings_.append(
            f"Yüksek VIF (>{VIF_THRESHOLD}): {high_vif}. "
            "Özellik seçimi veya ridge regresyonu değerlendirin."
        )

    # ─ Cook's D ─
    h = _hat_diagonal(X)
    cooks = _cooks_distance(h, residuals, p, s2)
    thresh = _COOKS_SCALE / n
    influential = [i for i, d in enumerate(cooks) if d > thresh]
    if influential:
        warnings_.append(
            f"Etkili gözlem(ler) (Cook's D > {thresh:.3f}): indeks {influential}."
        )

    diagnostics = MLRDiagnostics(
        condition_number=round(kappa, 2),
        rank_deficient=rank_deficient,
        effective_rank=int(rank),
        vif=vif,
        cooks_d=[round(d, 6) for d in cooks],
        influential_indices=influential,
        high_vif_features=high_vif,
    )

    domain_min = {fn: float(np.min(X_raw[:, j])) for j, fn in enumerate(feature_names)}
    domain_max = {fn: float(np.max(X_raw[:, j])) for j, fn in enumerate(feature_names)}

    return MLRFit(
        feature_names=list(feature_names),
        intercept=round(float(beta[0]), 8),
        coefficients={fn: round(float(beta[j + 1]), 8) for j, fn in enumerate(feature_names)},
        n_obs=n,
        n_features=len(feature_names),
        residual_df=residual_df,
        rmse_mm=round(rmse, 6),
        mae_mm=round(float(np.mean(np.abs(residuals))), 6),
        bias_mm=round(float(np.mean(residuals)), 6),
        r2=round(r2, 6),
        r2_adjusted=round(r2_adjusted, 6) if r2_adjusted is not None else None,
        s2=round(s2, 8),
        diagnostics=diagnostics,
        warnings=warnings_,
        domain_min=domain_min,
        domain_max=domain_max,
    )


def predict_mlr(fit: MLRFit, features: dict[str, float]) -> MLRPrediction:
    """
    Fit edilmiş MLR modeli ile tahmin üretir.

    Returns
    -------
    MLRPrediction : Tahmin, belirsizlik (±RMSE) ve alan durumu.
    """
    warnings_: list[str] = []
    extrapolated: list[str] = []

    for fname in fit.feature_names:
        v = features.get(fname)
        if v is None:
            raise ValueError(f"Tahmin için '{fname}' özelliği eksik.")
        fv = float(v)
        if not math.isfinite(fv):
            raise ValueError(f"'{fname}'={v} sonsuz/NaN değer.")
        if fv < fit.domain_min[fname] or fv > fit.domain_max[fname]:
            extrapolated.append(fname)

    prediction = fit.intercept + sum(
        fit.coefficients[fn] * float(features[fn])
        for fn in fit.feature_names
    )

    if extrapolated:
        warnings_.append(
            f"EXTRAPOLATION_WARNING: {extrapolated} eğitim alanı dışında. "
            "Doğrusal extrapolasyon patlama bölgesinde fiziksel olarak yanlış olabilir."
        )
    if prediction <= 0:
        warnings_.append(
            f"Tahmin ≤ 0 ({prediction:.4f} mm); fiziksel geçerliliği yok. "
            "Girdi alanı kontrol edilmeli."
        )

    uncertainty = fit.rmse_mm if fit.residual_df > 0 and fit.rmse_mm > 0 else None

    return MLRPrediction(
        predicted_nugget_mm=round(prediction, 4),
        uncertainty_mm=round(uncertainty, 4) if uncertainty is not None else None,
        in_domain=len(extrapolated) == 0,
        extrapolated_features=extrapolated,
        warnings=warnings_,
    )
