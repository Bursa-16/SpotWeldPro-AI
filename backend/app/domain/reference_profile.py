"""
Reference Profile: REF_PROFILE_MS_2T_50HZ_V1
Neutral 2T parameter foundation for mild steel, 50 Hz cycle basis.

No source provenance is encoded in this module.
Generic labels only: Reference Profile, Reference Band,
Engineering Review Required, Reference Parameter Range.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Status enumerations
# ---------------------------------------------------------------------------

class BandSelectionStatus(str, Enum):
    """Status for effective-thickness matrix lookup and band assignment."""
    OK = "OK"
    ENGINEERING_REVIEW_REQUIRED = "ENGINEERING_REVIEW_REQUIRED"


class ReferenceGuidanceStatus(str, Enum):
    """Reusable status model for parameter-level reference guidance."""
    WITHIN_REFERENCE_RANGE = "WITHIN_REFERENCE_RANGE"
    BELOW_REFERENCE_RANGE = "BELOW_REFERENCE_RANGE"
    ABOVE_REFERENCE_RANGE = "ABOVE_REFERENCE_RANGE"
    ENGINEERING_REVIEW_REQUIRED = "ENGINEERING_REVIEW_REQUIRED"
    UNIT_BASIS_UNRESOLVED = "UNIT_BASIS_UNRESOLVED"
    NOT_EVALUATED = "NOT_EVALUATED"


# Sentinel string returned by unit-conversion helpers when the profile
# cycle basis is unavailable (not a ReferenceGuidanceStatus enum value
# because it is returned in place of a numeric result).
UNIT_BASIS_UNRESOLVED = "UNIT_BASIS_UNRESOLVED"


# ---------------------------------------------------------------------------
# Domain data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReferenceProfile:
    profile_id: str
    cycle_basis_hz: int
    supported_stack_count: str
    supported_material_scope: str
    supported_thickness_min_mm: float
    supported_thickness_max_mm: float


@dataclass(frozen=True)
class ParameterBand:
    band_id: str
    t_min_mm: float
    t_max_mm: float
    force_min_dan: float
    force_max_dan: float
    current_min_ka: float
    current_max_ka: float
    cooling_time_min_ms: float
    cooling_time_max_ms: float
    recommended_tip_diameter_mm: float


@dataclass(frozen=True)
class EffectiveThicknessResult:
    effective_thickness_mm: Optional[float]
    band_selection_status: BandSelectionStatus


# ---------------------------------------------------------------------------
# Reference profile singleton — no proprietary provenance
# ---------------------------------------------------------------------------

REF_PROFILE_MS_2T_50HZ_V1: ReferenceProfile = ReferenceProfile(
    profile_id="REF_PROFILE_MS_2T_50HZ_V1",
    cycle_basis_hz=50,
    supported_stack_count="2T",
    supported_material_scope="mild steel reference scope",
    supported_thickness_min_mm=0.6,
    supported_thickness_max_mm=3.0,
)

# Internal authorized material family key — not surfaced in API-visible profile fields.
_MILD_STEEL_FAMILY: str = "Düşük / Orta Karbonlu Çelik"


# ---------------------------------------------------------------------------
# 2T effective-thickness matrix
#
# Source: verified engineering data (neutral reference).
# Covers 0.7–3.0 mm (24 discrete thickness values at 0.1 mm steps).
# 0.6 mm is within the profile declared range but outside this matrix.
# Lookup is symmetric and matrix-based only — no min(t1,t2) fallback,
# no extrapolation, no interpolation.
# ---------------------------------------------------------------------------

_MATRIX_THICKNESSES: Tuple[float, ...] = (
    0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6,
    1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6,
    2.7, 2.8, 2.9, 3.0,
)

# Lower-triangular rows indexed [row_idx][col_idx] where row_idx >= col_idx.
# Row i corresponds to _MATRIX_THICKNESSES[i]; it has i+1 entries.
_MATRIX_ROWS: Tuple[Tuple[float, ...], ...] = (
    # row 0 → t=0.7
    (0.7,),
    # row 1 → t=0.8
    (0.7, 0.8),
    # row 2 → t=0.9
    (0.7, 0.8, 0.9),
    # row 3 → t=1.0
    (0.8, 0.8, 0.9, 1.0),
    # row 4 → t=1.1
    (0.8, 0.9, 0.9, 1.0, 1.1),
    # row 5 → t=1.2
    (0.8, 0.9, 1.0, 1.0, 1.1, 1.2),
    # row 6 → t=1.3
    (0.8, 0.9, 1.0, 1.1, 1.1, 1.2, 1.3),
    # row 7 → t=1.4
    (0.8, 0.9, 1.0, 1.1, 1.2, 1.2, 1.3, 1.4),
    # row 8 → t=1.5
    (0.9, 0.9, 1.0, 1.1, 1.2, 1.3, 1.3, 1.4, 1.5),
    # row 9 → t=1.6
    (0.9, 1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.4, 1.5, 1.6),
    # row 10 → t=1.7
    (0.9, 1.0, 1.1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.5, 1.6, 1.7),
    # row 11 → t=1.8
    (0.9, 1.0, 1.1, 1.2, 1.2, 1.3, 1.4, 1.5, 1.6, 1.6, 1.7, 1.8),
    # row 12 → t=1.9
    (0.9, 1.0, 1.1, 1.2, 1.3, 1.3, 1.4, 1.5, 1.6, 1.7, 1.7, 1.8, 1.9),
    # row 13 → t=2.0
    (1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.4, 1.5, 1.6, 1.7, 1.8, 1.8, 1.9, 2.0),
    # row 14 → t=2.1
    (1.0, 1.1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.5, 1.6, 1.7, 1.8, 1.9, 1.9, 2.0, 2.1),
    # row 15 → t=2.2
    (1.0, 1.1, 1.2, 1.2, 1.3, 1.4, 1.5, 1.6, 1.6, 1.7, 1.8, 1.9, 2.0, 2.0, 2.1, 2.2),
    # row 16 → t=2.3
    (1.0, 1.1, 1.2, 1.3, 1.3, 1.4, 1.5, 1.6, 1.7, 1.7, 1.8, 1.9, 2.0, 2.1, 2.1, 2.2, 2.3),
    # row 17 → t=2.4
    (1.0, 1.1, 1.2, 1.3, 1.4, 1.4, 1.5, 1.6, 1.7, 1.8, 1.8, 1.9, 2.0, 2.1, 2.2, 2.2, 2.3, 2.4),
    # row 18 → t=2.5
    (1.1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.5, 1.6, 1.7, 1.8, 1.9, 1.9, 2.0, 2.1, 2.2, 2.3, 2.3, 2.4, 2.5),
    # row 19 → t=2.6
    (1.1, 1.2, 1.2, 1.3, 1.4, 1.5, 1.6, 1.6, 1.7, 1.8, 1.9, 2.0, 2.0, 2.1, 2.2, 2.3, 2.4, 2.4, 2.5, 2.6),
    # row 20 → t=2.7
    (1.1, 1.2, 1.3, 1.3, 1.4, 1.5, 1.6, 1.7, 1.7, 1.8, 1.9, 2.0, 2.1, 2.1, 2.2, 2.3, 2.4, 2.5, 2.5, 2.6, 2.7),
    # row 21 → t=2.8
    (1.1, 1.2, 1.3, 1.4, 1.4, 1.5, 1.6, 1.7, 1.8, 1.8, 1.9, 2.0, 2.1, 2.2, 2.2, 2.3, 2.4, 2.5, 2.6, 2.6, 2.7, 2.8),
    # row 22 → t=2.9
    (1.1, 1.2, 1.3, 1.4, 1.5, 1.5, 1.6, 1.7, 1.8, 1.9, 1.9, 2.0, 2.1, 2.2, 2.3, 2.3, 2.4, 2.5, 2.6, 2.7, 2.7, 2.8, 2.9),
    # row 23 → t=3.0
    (1.2, 1.2, 1.3, 1.4, 1.5, 1.6, 1.6, 1.7, 1.8, 1.9, 2.0, 2.0, 2.1, 2.2, 2.3, 2.4, 2.4, 2.5, 2.6, 2.7, 2.8, 2.8, 2.9, 3.0),
)

# Pre-built lookup table: (row_idx, col_idx) → effective_thickness_mm
_MATRIX_LOOKUP: dict = {
    (row_idx, col_idx): val
    for row_idx, row in enumerate(_MATRIX_ROWS)
    for col_idx, val in enumerate(row)
}

_THICKNESS_INDEX: dict = {t: i for i, t in enumerate(_MATRIX_THICKNESSES)}

# Tolerance for snapping a user-supplied float to the nearest 0.1 mm grid point.
# Must be < 0.05 so mid-points between grid values are never snapped.
_GRID_TOL: float = 1e-4


def _snap_to_grid(value: float) -> Optional[float]:
    """Return the nearest matrix grid thickness if within tolerance, else None."""
    for t in _MATRIX_THICKNESSES:
        if abs(value - t) <= _GRID_TOL:
            return t
    return None


def get_effective_thickness_2t(
    t1_mm: float,
    t2_mm: float,
    profile: ReferenceProfile = REF_PROFILE_MS_2T_50HZ_V1,
) -> EffectiveThicknessResult:
    """
    Matrix-based 2T effective thickness lookup.

    Properties guaranteed:
    - lookup(t1, t2) == lookup(t2, t1)  [symmetric]
    - No min(t1, t2) fallback
    - No extrapolation outside 0.7–3.0 mm
    - 0.6 mm (profile minimum) is outside the matrix → ENGINEERING_REVIEW_REQUIRED
    """
    g1 = _snap_to_grid(t1_mm)
    g2 = _snap_to_grid(t2_mm)

    if g1 is None or g2 is None:
        return EffectiveThicknessResult(
            effective_thickness_mm=None,
            band_selection_status=BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED,
        )

    i = _THICKNESS_INDEX[g1]
    j = _THICKNESS_INDEX[g2]
    # Canonical lower-triangular form: larger index is the row
    row, col = (i, j) if i >= j else (j, i)
    effective = _MATRIX_LOOKUP[(row, col)]
    return EffectiveThicknessResult(
        effective_thickness_mm=effective,
        band_selection_status=BandSelectionStatus.OK,
    )


def get_effective_thickness(
    stack_count: str,
    layers_mm: List[float],
    profile: ReferenceProfile = REF_PROFILE_MS_2T_50HZ_V1,
) -> EffectiveThicknessResult:
    """
    Stack-aware entry point for effective thickness.

    3T and 4T always return ENGINEERING_REVIEW_REQUIRED.
    No adjacent-pair minimum, no averaging, no interpolation across stack.
    """
    if stack_count in ("3T", "4T"):
        return EffectiveThicknessResult(
            effective_thickness_mm=None,
            band_selection_status=BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED,
        )
    if stack_count == "2T" and len(layers_mm) >= 2:
        return get_effective_thickness_2t(layers_mm[0], layers_mm[1], profile)
    return EffectiveThicknessResult(
        effective_thickness_mm=None,
        band_selection_status=BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED,
    )


# ---------------------------------------------------------------------------
# Parameter bands — verified engineering values, neutral provenance
# ---------------------------------------------------------------------------

REF_BANDS: Tuple[ParameterBand, ...] = (
    ParameterBand(
        band_id="REF_BAND_01",
        t_min_mm=0.6,
        t_max_mm=1.1,
        force_min_dan=180.0,   # daN, tip Ø6
        force_max_dan=230.0,
        current_min_ka=7.8,    # kA, tip Ø6
        current_max_ka=8.3,
        cooling_time_min_ms=120.0,
        cooling_time_max_ms=140.0,
        recommended_tip_diameter_mm=6.0,
    ),
    ParameterBand(
        band_id="REF_BAND_02",
        t_min_mm=1.2,
        t_max_mm=1.7,
        force_min_dan=240.0,   # daN, tip Ø6
        force_max_dan=290.0,
        current_min_ka=8.4,    # kA, tip Ø6
        current_max_ka=8.8,
        cooling_time_min_ms=140.0,
        cooling_time_max_ms=160.0,
        recommended_tip_diameter_mm=6.0,
    ),
    ParameterBand(
        band_id="REF_BAND_03",
        t_min_mm=1.8,
        t_max_mm=2.3,
        force_min_dan=320.0,   # daN, tip Ø8
        force_max_dan=370.0,
        current_min_ka=9.0,    # kA, tip Ø8
        current_max_ka=9.5,
        cooling_time_min_ms=180.0,
        cooling_time_max_ms=200.0,
        recommended_tip_diameter_mm=8.0,
    ),
    ParameterBand(
        band_id="REF_BAND_04",
        t_min_mm=2.4,
        t_max_mm=3.0,
        force_min_dan=380.0,   # daN, tip Ø8
        force_max_dan=440.0,
        current_min_ka=9.6,    # kA, tip Ø8
        current_max_ka=10.7,
        cooling_time_min_ms=200.0,
        cooling_time_max_ms=220.0,
        recommended_tip_diameter_mm=8.0,
    ),
)


def get_parameter_band(
    t_eff_mm: float,
    profile: ReferenceProfile = REF_PROFILE_MS_2T_50HZ_V1,
) -> Optional[ParameterBand]:
    """
    Return the reference parameter band for the given effective thickness,
    or None if the value is outside all defined band ranges.
    """
    for band in REF_BANDS:
        if band.t_min_mm - _GRID_TOL <= t_eff_mm <= band.t_max_mm + _GRID_TOL:
            return band
    return None


# ---------------------------------------------------------------------------
# Force unit conversion — Section 5
# ---------------------------------------------------------------------------

def kn_to_dan(force_kn: float) -> float:
    """
    Convert kilonewtons to decanewtons.
    Use exactly once at the evaluation boundary; never compare force_kn
    directly to daN-based reference limits.
    """
    return force_kn * 100.0


# ---------------------------------------------------------------------------
# Time-basis conversion helpers — Section 6
# ---------------------------------------------------------------------------

def cycle_to_ms(
    cycles: float,
    profile: Optional[ReferenceProfile],
) -> Union[float, str]:
    """
    Convert welding cycles to milliseconds using the profile's declared cycle basis.
    Returns the UNIT_BASIS_UNRESOLVED sentinel string if the profile is None.
    A 20 ms per-cycle constant is NOT assumed globally; it is derived from
    the profile's cycle_basis_hz.
    """
    if profile is None:
        return UNIT_BASIS_UNRESOLVED
    return cycles * (1000.0 / profile.cycle_basis_hz)


def ms_to_cycle(
    ms: float,
    profile: Optional[ReferenceProfile],
) -> Union[float, str]:
    """
    Convert milliseconds to welding cycles using the profile's declared cycle basis.
    Returns the UNIT_BASIS_UNRESOLVED sentinel string if the profile is None.
    """
    if profile is None:
        return UNIT_BASIS_UNRESOLVED
    return ms / (1000.0 / profile.cycle_basis_hz)


# ---------------------------------------------------------------------------
# Material scope evaluation — Section 9
# ---------------------------------------------------------------------------

def evaluate_material_scope(
    material_family: str,
    profile: ReferenceProfile = REF_PROFILE_MS_2T_50HZ_V1,
) -> ReferenceGuidanceStatus:
    """
    Check whether the material family is within the reference profile's
    authorized scope.

    Only mild steel is authorized for band-based parameter guidance.
    AHSS, galvanized, aluminum, and all other families require engineering review.
    The legacy +1 kA / +2 kA / 25–45 kA adjustments must NOT be presented
    as validated reference-profile guidance.
    """
    if material_family == _MILD_STEEL_FAMILY:
        return ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE
    return ReferenceGuidanceStatus.ENGINEERING_REVIEW_REQUIRED


# ---------------------------------------------------------------------------
# Parameter guidance evaluation — Section 10
# ---------------------------------------------------------------------------

def evaluate_parameter_guidance(
    value: float,
    lower: float,
    upper: float,
) -> ReferenceGuidanceStatus:
    """
    Compare a parameter value against a reference range [lower, upper].

    IMPORTANT: being outside the reference range does NOT automatically:
    - reduce a compliance score
    - cause FAIL
    - mark a weld NOK
    Guidance and compliance are separate concerns.
    """
    if value < lower:
        return ReferenceGuidanceStatus.BELOW_REFERENCE_RANGE
    if value > upper:
        return ReferenceGuidanceStatus.ABOVE_REFERENCE_RANGE
    return ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE


# ---------------------------------------------------------------------------
# P2-safe optional parameter guard — Section 11
# ---------------------------------------------------------------------------

def evaluate_optional_parameter(value: Optional[float]) -> ReferenceGuidanceStatus:
    """
    Guard for newly introduced optional request fields:
    approach_cycles, cooling_cycles, air_pressure_bar.

    Missing (None) means: not supplied / not evaluated.
    Never treats a missing value as an assumed ideal default.
    In 01B1 (P2 foundation), reference ranges for these parameters are
    not yet defined; both supplied and missing values return NOT_EVALUATED.
    """
    return ReferenceGuidanceStatus.NOT_EVALUATED
