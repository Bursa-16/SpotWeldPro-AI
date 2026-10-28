"""
reports.py — Pydantic schemas for P2-F Engineering Report API.
"""

from __future__ import annotations

import hashlib
import json
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class WeldPointEnergySpecIn(BaseModel):
    point_code: str = Field(min_length=1, max_length=80)
    group_name: str = Field(default="DEFAULT", max_length=80)
    e_current_kj: Optional[float] = Field(default=None, gt=0)
    e_min_kj: Optional[float] = Field(default=None, gt=0)
    e_ideal_kj: Optional[float] = Field(default=None, gt=0)
    e_max_kj: Optional[float] = Field(default=None, gt=0)


class EnergyReportRequest(BaseModel):
    """Request body for all three report formats (CSV / XLSX / PDF)."""

    # Energy data (same as DashboardRequest)
    points: List[WeldPointEnergySpecIn] = Field(min_length=1, max_length=200)
    production_volume_annual: Optional[int] = Field(default=None, gt=0, le=10_000_000)
    tariff_eur_per_kwh: Optional[float] = Field(default=None, gt=0)
    tariff_usd_per_kwh: Optional[float] = Field(default=None, gt=0)
    pareto_top_n: int = Field(default=50, ge=1, le=200)

    # Report metadata
    project_id: Optional[str] = Field(default=None, max_length=120)
    project_name: Optional[str] = Field(default=None, max_length=200)
    part_id: Optional[str] = Field(default=None, max_length=120)
    passport_id: Optional[str] = Field(default=None, max_length=120)
    report_language: Literal["en", "tr"] = Field(default="en")
    analyst_name: Optional[str] = Field(default=None, max_length=200)
    report_title: Optional[str] = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _compute_input_hash(self) -> "EnergyReportRequest":
        payload = self.model_dump(
            include={"points", "production_volume_annual", "tariff_eur_per_kwh",
                     "tariff_usd_per_kwh", "pareto_top_n"},
            mode="json",
        )
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        # Store hash on a private attribute accessed by the API
        object.__setattr__(self, "_input_hash", digest[:32])
        return self

    @property
    def input_hash(self) -> str:
        return getattr(self, "_input_hash", "UNKNOWN")
