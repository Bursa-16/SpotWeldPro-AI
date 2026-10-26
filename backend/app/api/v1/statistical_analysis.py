"""
statistical_analysis.py — Taguchi DOE ve ANOVA API endpoint'leri.

KAPASITE: DESIGN_METHOD (Taguchi) + STATISTICAL_ANALYSIS (ANOVA)
SEMANTİK: Tasarım ve istatistik araçları; nugget çapı tahmini değil.

Endpoint'ler:
  POST /statistical-analysis/taguchi/design   — Ortogonal dizi tasarımı oluştur
  POST /statistical-analysis/taguchi/analyze  — Sonuçları analiz et (S/N + ANOVA)
  POST /statistical-analysis/anova            — Bağımsız gruplar tek faktörlü ANOVA
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_permission
from app.domain import taguchi as taguchi_domain
from app.domain import statistical_analysis as anova_domain
from app.models.entities import User
from app.schemas.statistical_analysis import (
    ANOVAAnalyzeRequest,
    ANOVAAnalyzeResponse,
    ANOVARowOut,
    TaguchiAnalyzeRequest,
    TaguchiAnalyzeResponse,
    TaguchiDesignRequest,
    TaguchiDesignResponse,
    ExperimentRunOut,
    FactorEffectOut,
    LevelEffectOut,
    OptimalSettingOut,
)

router = APIRouter(
    prefix="/statistical-analysis",
    tags=["Statistical Analysis"],
)


def _require_weld_read() -> User:
    return Depends(require_permission("weld:read"))


# ── Taguchi DOE: Tasarım ──────────────────────────────────────────────────────

@router.post("/taguchi/design", response_model=TaguchiDesignResponse)
def taguchi_design(
    payload: TaguchiDesignRequest,
    _user: User = Depends(require_permission("weld:read")),
) -> TaguchiDesignResponse:
    """
    Ortogonal dizi deney matrisini oluşturur.

    Yanıt değerleri içermez; sadece run planını döndürür.
    Kullanıcı gerçek deneyleri yaptıktan sonra /taguchi/analyze çağırır.
    """
    factors = [
        taguchi_domain.FactorSpec(
            name=f.name,
            unit=f.unit,
            levels=tuple(f.levels),
        )
        for f in payload.factors
    ]
    try:
        design = taguchi_domain.generate_design(payload.array_type, factors)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return TaguchiDesignResponse(
        array_type=design.array_type,
        runs=design.runs,
        n_factors=design.n_factors,
        levels_per_factor=design.levels_per_factor,
        degrees_of_freedom=design.degrees_of_freedom,
        residual_df=design.residual_df,
        saturated=design.saturated,
        experiment_matrix=[
            ExperimentRunOut(
                run_number=run.run_number,
                factor_values=run.factor_values,
            )
            for run in design.experiment_matrix
        ],
        warnings=design.warnings,
    )


# ── Taguchi DOE: Analiz ───────────────────────────────────────────────────────

@router.post("/taguchi/analyze", response_model=TaguchiAnalyzeResponse)
def taguchi_analyze(
    payload: TaguchiAnalyzeRequest,
    _user: User = Depends(require_permission("weld:read")),
) -> TaguchiAnalyzeResponse:
    """
    Kullanıcı tarafından ölçülen deney sonuçlarını analiz eder.

    ÖNEMLI: `responses` alanındaki değerler kullanıcının gerçek deneyden
    ölçtüğü veriler olmalıdır. Bu endpoint nugget çapı tahmin etmez.

    Döndürülenler:
    - Ana etkiler (her faktör için seviye ortalamaları ve S/N oranları)
    - Optimal seviyeler (S/N bazlı)
    - Katkılı model tahmini (etkileşim yok varsayımıyla)
    - Dengeli ANOVA tablosu (SS, df, MS, F, p, katkı %)
    """
    factors = [
        taguchi_domain.FactorSpec(
            name=f.name,
            unit=f.unit,
            levels=tuple(f.levels),
        )
        for f in payload.factors
    ]
    try:
        result = taguchi_domain.analyze(
            array_type=payload.array_type,
            factors=factors,
            responses=payload.responses,
            sn_objective=payload.sn_objective,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return TaguchiAnalyzeResponse(
        capability_type=result.capability_type,
        semantic_note=result.semantic_note,
        array_type=result.array_type,
        n_runs=result.n_runs,
        n_factors=result.n_factors,
        sn_objective=result.sn_objective,
        grand_mean_response=result.grand_mean_response,
        grand_mean_sn=result.grand_mean_sn,
        factor_effects=[
            FactorEffectOut(
                factor_name=fe.factor_name,
                unit=fe.unit,
                levels=[
                    LevelEffectOut(
                        level_index=le.level_index,
                        level_value=le.level_value,
                        mean_response=le.mean_response,
                        sn_ratio=le.sn_ratio,
                    )
                    for le in fe.levels
                ],
                delta_response=fe.delta_response,
                delta_sn=fe.delta_sn,
                rank_response=fe.rank_response,
                rank_sn=fe.rank_sn,
            )
            for fe in result.factor_effects
        ],
        optimal_settings=[
            OptimalSettingOut(
                factor_name=os_.factor_name,
                unit=os_.unit,
                optimal_level_index=os_.optimal_level_index,
                optimal_level_value=os_.optimal_level_value,
            )
            for os_ in result.optimal_settings
        ],
        additive_prediction=result.additive_prediction,
        additive_prediction_note=result.additive_prediction_note,
        anova_table=[
            ANOVARowOut(
                source=row.source,
                ss=row.ss,
                df=row.df,
                ms=row.ms,
                f_statistic=row.f_statistic,
                p_value=row.p_value,
                contribution_pct=row.contribution_pct,
                note=row.note,
            )
            for row in result.anova_table
        ],
        warnings=result.warnings,
    )


# ── Bağımsız Gruplar ANOVA ────────────────────────────────────────────────────

@router.post("/anova", response_model=ANOVAAnalyzeResponse)
def anova_analyze(
    payload: ANOVAAnalyzeRequest,
    _user: User = Depends(require_permission("weld:read")),
) -> ANOVAAnalyzeResponse:
    """
    Bağımsız gruplar için tek faktörlü ANOVA.

    ÖNEMLI: `groups[*].values` alanındaki değerler kullanıcının ölçtüğü
    gerçek veriler olmalıdır. Bu endpoint nugget çapı tahmin etmez.

    Döndürülenler:
    - ANOVA tablosu (SS, df, MS, F, p, katkı %)
    - Kalıntı serbestlik derecesi
    - Doymuş tasarım ve eksik sıra uyarıları
    """
    groups: dict[str, list[float]] = {
        g.group_name: g.values
        for g in payload.groups
    }
    if len(groups) < len(payload.groups):
        raise HTTPException(
            status_code=422,
            detail="Grup adları benzersiz olmalı.",
        )
    try:
        result = anova_domain.one_way_anova(
            groups=groups,
            factor_name=payload.factor_name,
            response_name=payload.response_variable,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ANOVAAnalyzeResponse(
        capability_type=result.capability_type,
        semantic_note=result.semantic_note,
        design_type=result.design_type,
        n_observations=result.n_observations,
        grand_mean=result.grand_mean,
        table=[
            ANOVARowOut(
                source=row.source,
                ss=row.ss,
                df=row.df,
                ms=row.ms,
                f_statistic=row.f_statistic,
                p_value=row.p_value,
                contribution_pct=row.contribution_pct,
                note=row.note,
            )
            for row in result.table
        ],
        residual_df=result.residual_df,
        rank_deficient=result.rank_deficient,
        saturated=result.saturated,
        warnings=result.warnings,
        assumptions=result.assumptions,
    )
