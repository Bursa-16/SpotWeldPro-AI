from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.domain.model_catalog import (
    CATALOG_BY_ID,
    MODEL_CATALOG,
    ModelGovernanceStatus,
    get_entry,
)
from app.schemas.model_catalog import CatalogEntryOut, ModelCatalogResponse, ValidationEvidenceOut

router = APIRouter(tags=["Model Catalog"])


def _entry_to_out(e) -> CatalogEntryOut:
    ve = None
    if e.validation_evidence is not None:
        ev = e.validation_evidence
        ve = ValidationEvidenceOut(
            n_train=ev.n_train,
            n_test=ev.n_test,
            rmse_mm=ev.rmse_mm,
            mae_mm=ev.mae_mm,
            bias_mm=ev.bias_mm,
            r2=ev.r2,
            dataset_name=ev.dataset_name,
            measurement_basis=ev.measurement_basis,
            notes_tr=ev.notes_tr,
            notes_en=ev.notes_en,
        )
    return CatalogEntryOut(
        model_id=e.model_id,
        version=e.version,
        name_tr=e.name_tr,
        name_en=e.name_en,
        model_basis=e.model_basis,
        capability_type=e.capability_type,
        governance_status=e.governance_status,
        measurement_target=e.measurement_target,
        supported_materials=list(e.supported_materials),
        thickness_range_mm=list(e.thickness_range_mm),
        mandatory_inputs=list(e.mandatory_inputs),
        optional_inputs=list(e.optional_inputs),
        uncertainty_supported=e.uncertainty_supported,
        router_active=e.router_active,
        not_available_reason_tr=e.not_available_reason_tr,
        not_available_reason_en=e.not_available_reason_en,
        validation_evidence=ve,
        rejection_reason_tr=e.rejection_reason_tr,
        rejection_reason_en=e.rejection_reason_en,
        notes_tr=e.notes_tr,
        notes_en=e.notes_en,
    )


@router.get("/model-catalog", response_model=ModelCatalogResponse)
def list_model_catalog() -> ModelCatalogResponse:
    """Tüm model katalog girdilerini döndürür."""
    entries = [_entry_to_out(e) for e in MODEL_CATALOG]
    return ModelCatalogResponse(total=len(entries), entries=entries)


@router.get("/model-catalog/{model_id}", response_model=CatalogEntryOut)
def get_model_catalog_entry(model_id: str) -> CatalogEntryOut:
    """Belirtilen model ID'sine ait katalog girdisini döndürür."""
    try:
        entry = get_entry(model_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "MODEL_NOT_FOUND",
                    "message": f"Model ID bulunamadı: {model_id!r}"},
        )
    return _entry_to_out(entry)


@router.post("/model-catalog/predict-guard/{model_id}")
def predict_guard(model_id: str):
    """
    REJECTED veya NOT_AVAILABLE model için tahmin isteği engellenir.
    Bu endpoint, üretim guard kontrolü için referans implementasyonudur.
    """
    blocked_statuses = {ModelGovernanceStatus.REJECTED, ModelGovernanceStatus.DEPRECATED}
    try:
        entry = get_entry(model_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "MODEL_NOT_FOUND",
                    "message": f"Model ID bulunamadı: {model_id!r}"},
        )
    if entry.governance_status in blocked_statuses:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "MODEL_REJECTED",
                "message": (
                    f"'{entry.name_tr}' modeli üretim tahmininde kullanılamaz. "
                    f"Durum: {entry.governance_status}. "
                    f"Neden: {entry.rejection_reason_tr or entry.not_available_reason_tr}"
                ),
            },
        )
    if entry.governance_status == ModelGovernanceStatus.NOT_AVAILABLE:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "MODEL_NOT_AVAILABLE",
                "message": (
                    f"'{entry.name_tr}' modeli henüz kullanılabilir değil. "
                    f"Durum: {entry.governance_status}. "
                    f"Neden: {entry.not_available_reason_tr}"
                ),
            },
        )
    if (entry.governance_status == ModelGovernanceStatus.EXPERIMENTAL
            and not entry.router_active):
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "MODEL_EXPERIMENTAL",
                "message": (
                    f"'{entry.name_tr}' modeli henüz üretim kullanımına açık değil. "
                    f"Durum: {entry.governance_status}. "
                    f"{entry.notes_tr or 'router_active=False — validasyon verisi bekleniyor.'}"
                ),
                "context": {
                    "message_en": (
                        f"'{entry.name_en}' is not yet available for production use. "
                        f"Status: {entry.governance_status}. "
                        f"{entry.notes_en or 'router_active=False — validation data required.'}"
                    ),
                    "model_id": model_id,
                    "router_active": entry.router_active,
                },
            },
        )
    return {"model_id": model_id, "governance_status": entry.governance_status,
            "message": "Bu model tahmin isteğine uygun görünüyor."}
