"""
statistical_analysis.py — Taguchi DOE ve ANOVA Pydantic şemaları.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Ortak ─────────────────────────────────────────────────────────────────────

class FactorLevelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Faktör adı (boşluk kullanılabilir)")
    unit: str = Field(..., description="Birimi, örn. 'kA', 'cycles', 'kN'")
    levels: list[float] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="Faktör seviyeleri (2–4 değer; dizi tipine göre doğrulanır)",
    )

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Faktör adı boş olamaz.")
        return v.strip()


# ── Taguchi Design ─────────────────────────────────────────────────────────────

class TaguchiDesignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    array_type: str = Field(
        ...,
        description="Ortogonal dizi tipi: L4, L9, L16 veya L27",
        pattern="^(L4|L9|L16|L27)$",
    )
    factors: list[FactorLevelSpec] = Field(
        ...,
        min_length=1,
        description="Faktörler ve seviyeleri (dizi kapasitesiyle uyumlu olmalı)",
    )


class ExperimentRunOut(BaseModel):
    run_number: int
    factor_values: dict[str, float]


class TaguchiDesignResponse(BaseModel):
    array_type: str
    runs: int
    n_factors: int
    levels_per_factor: int
    degrees_of_freedom: dict[str, int]
    residual_df: int
    saturated: bool
    experiment_matrix: list[ExperimentRunOut]
    warnings: list[str]


# ── Taguchi Analyze ────────────────────────────────────────────────────────────

class TaguchiAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    array_type: str = Field(
        ...,
        pattern="^(L4|L9|L16|L27)$",
    )
    factors: list[FactorLevelSpec] = Field(..., min_length=1)
    sn_objective: str = Field(
        ...,
        description=(
            "S/N hedef formülü: 'larger_is_better' | 'smaller_is_better' | 'nominal_is_best'"
        ),
        pattern="^(larger_is_better|smaller_is_better|nominal_is_best)$",
    )
    responses: list[float] = Field(
        ...,
        min_length=1,
        description=(
            "Her run için ölçülen yanıt değerleri (sırayla). "
            "ZORUNLU: Bunlar kullanıcı tarafından ölçülmüş gerçek deney sonuçlarıdır; "
            "model tahmini değil."
        ),
    )
    response_variable: str = Field(
        default="response",
        description="Yanıt değişkeninin adı, örn. 'nugget_diameter_mm'",
    )
    response_unit: str = Field(
        default="",
        description="Yanıt birim, örn. 'mm'",
    )


class LevelEffectOut(BaseModel):
    level_index: int
    level_value: float
    mean_response: float
    sn_ratio: float


class FactorEffectOut(BaseModel):
    factor_name: str
    unit: str
    levels: list[LevelEffectOut]
    delta_response: float
    delta_sn: float
    rank_response: int
    rank_sn: int


class OptimalSettingOut(BaseModel):
    factor_name: str
    unit: str
    optimal_level_index: int
    optimal_level_value: float


class ANOVARowOut(BaseModel):
    source: str
    ss: float
    df: int
    ms: Optional[float]
    f_statistic: Optional[float]
    p_value: Optional[float]
    contribution_pct: Optional[float]
    note: str = ""


class TaguchiAnalyzeResponse(BaseModel):
    capability_type: str
    semantic_note: str
    array_type: str
    n_runs: int
    n_factors: int
    sn_objective: str
    grand_mean_response: float
    grand_mean_sn: float
    factor_effects: list[FactorEffectOut]
    optimal_settings: list[OptimalSettingOut]
    additive_prediction: Optional[float]
    additive_prediction_note: str
    anova_table: list[ANOVARowOut]
    warnings: list[str]


# ── One-way ANOVA ──────────────────────────────────────────────────────────────

class ANOVAGroupData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_name: str = Field(..., description="Grup adı (örn. malzeme türü, proses seviyesi)")
    values: list[float] = Field(
        ...,
        min_length=1,
        description=(
            "Bu gruba ait ölçüm değerleri. "
            "ZORUNLU: Kullanıcı tarafından ölçülmüş gerçek değerler; model tahmini değil."
        ),
    )

    @field_validator("group_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Grup adı boş olamaz.")
        return v.strip()


class ANOVAAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factor_name: str = Field(
        default="Factor",
        description="Analiz edilen faktörün adı (ANOVA tablosunda görünür)",
    )
    response_variable: str = Field(
        default="response",
        description="Yanıt değişkeninin adı",
    )
    response_unit: str = Field(
        default="",
        description="Yanıt birim",
    )
    groups: list[ANOVAGroupData] = Field(
        ...,
        min_length=2,
        description="En az 2 grup gerekli",
    )


class ANOVAAnalyzeResponse(BaseModel):
    capability_type: str
    semantic_note: str
    design_type: str
    n_observations: int
    grand_mean: float
    table: list[ANOVARowOut]
    residual_df: int
    rank_deficient: bool
    saturated: bool
    warnings: list[str]
    assumptions: list[str]
