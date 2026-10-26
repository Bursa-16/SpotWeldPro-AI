from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ValidationEvidenceOut(BaseModel):
    n_train: Optional[int] = None
    n_test: Optional[int] = None
    rmse_mm: Optional[float] = None
    mae_mm: Optional[float] = None
    bias_mm: Optional[float] = None
    r2: Optional[float] = None
    dataset_name: Optional[str] = None
    measurement_basis: Optional[str] = None
    notes_tr: Optional[str] = None
    notes_en: Optional[str] = None


class CatalogEntryOut(BaseModel):
    model_id: str
    version: str
    name_tr: str
    name_en: str
    model_basis: str
    capability_type: str
    governance_status: str
    measurement_target: str
    supported_materials: List[str]
    thickness_range_mm: List[float]
    mandatory_inputs: List[str]
    optional_inputs: List[str]
    uncertainty_supported: bool
    router_active: bool
    not_available_reason_tr: Optional[str] = None
    not_available_reason_en: Optional[str] = None
    validation_evidence: Optional[ValidationEvidenceOut] = None
    rejection_reason_tr: Optional[str] = None
    rejection_reason_en: Optional[str] = None
    notes_tr: str
    notes_en: str


class ModelCatalogResponse(BaseModel):
    total: int
    entries: List[CatalogEntryOut]
