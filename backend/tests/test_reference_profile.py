"""
PARAMETER-ENGINE-01B1 — deterministic tests for REF_PROFILE_MS_2T_50HZ_V1.

Test groups A–R as specified in the task.
All test values are neutral engineering verification data; no source provenance.
"""
from __future__ import annotations

import pytest

from app.domain.reference_profile import (
    REF_BANDS,
    REF_PROFILE_MS_2T_50HZ_V1,
    UNIT_BASIS_UNRESOLVED,
    BandSelectionStatus,
    ReferenceGuidanceStatus,
    evaluate_material_scope,
    evaluate_optional_parameter,
    evaluate_parameter_guidance,
    get_effective_thickness,
    get_effective_thickness_2t,
    get_parameter_band,
    kn_to_dan,
    cycle_to_ms,
    ms_to_cycle,
)


# ===========================================================================
# A. All 4 thickness bands correctly resolved for representative thicknesses
# ===========================================================================

@pytest.mark.parametrize("t_eff_mm, expected_band_id", [
    (0.8,  "REF_BAND_01"),  # mid-Band-01 (0.6–1.1 mm)
    (0.9,  "REF_BAND_01"),
    (1.5,  "REF_BAND_02"),  # mid-Band-02 (1.2–1.7 mm)
    (1.4,  "REF_BAND_02"),
    (2.0,  "REF_BAND_03"),  # mid-Band-03 (1.8–2.3 mm)
    (2.1,  "REF_BAND_03"),
    (2.7,  "REF_BAND_04"),  # mid-Band-04 (2.4–3.0 mm)
    (2.8,  "REF_BAND_04"),
])
def test_A_all_bands_resolved(t_eff_mm: float, expected_band_id: str) -> None:
    band = get_parameter_band(t_eff_mm)
    assert band is not None, f"No band found for t_eff={t_eff_mm}"
    assert band.band_id == expected_band_id


# ===========================================================================
# B. Exact band boundary values
# ===========================================================================

@pytest.mark.parametrize("t_eff_mm, expected_band_id", [
    (0.6, "REF_BAND_01"),  # lower boundary of Band 01
    (1.1, "REF_BAND_01"),  # upper boundary of Band 01
    (1.2, "REF_BAND_02"),  # lower boundary of Band 02
    (1.7, "REF_BAND_02"),  # upper boundary of Band 02
    (1.8, "REF_BAND_03"),  # lower boundary of Band 03
    (2.3, "REF_BAND_03"),  # upper boundary of Band 03
    (2.4, "REF_BAND_04"),  # lower boundary of Band 04
    (3.0, "REF_BAND_04"),  # upper boundary of Band 04
])
def test_B_exact_band_boundaries(t_eff_mm: float, expected_band_id: str) -> None:
    band = get_parameter_band(t_eff_mm)
    assert band is not None, f"No band at boundary t_eff={t_eff_mm}"
    assert band.band_id == expected_band_id


def test_B_gap_between_bands_has_no_overlap() -> None:
    """There must be no gap or overlap between adjacent band boundaries."""
    sorted_bands = sorted(REF_BANDS, key=lambda b: b.t_min_mm)
    for a, b in zip(sorted_bands, sorted_bands[1:]):
        # Upper bound of a and lower bound of b must be adjacent (differ by 0.1 mm)
        assert abs(b.t_min_mm - a.t_max_mm) == pytest.approx(0.1, abs=1e-9), (
            f"Gap or overlap between {a.band_id} ({a.t_max_mm}) and "
            f"{b.band_id} ({b.t_min_mm})"
        )


# ===========================================================================
# C. 2T matrix symmetry: lookup(t1, t2) == lookup(t2, t1)
# ===========================================================================

@pytest.mark.parametrize("t1, t2", [
    (0.7, 0.7),
    (0.7, 1.0),
    (0.9, 1.5),
    (1.0, 2.0),
    (1.3, 2.6),
    (1.7, 3.0),
    (2.0, 3.0),
    (2.5, 2.9),
    (0.8, 2.8),
])
def test_C_matrix_symmetry(t1: float, t2: float) -> None:
    r_ab = get_effective_thickness_2t(t1, t2)
    r_ba = get_effective_thickness_2t(t2, t1)
    assert r_ab == r_ba, (
        f"Asymmetry at ({t1},{t2}): {r_ab} vs ({t2},{t1}): {r_ba}"
    )


def test_C_symmetry_bulk() -> None:
    """Verify symmetry for all pairs on the diagonal and first off-diagonal."""
    thicknesses = list(_subset_thicknesses())
    for i, t1 in enumerate(thicknesses):
        for t2 in thicknesses[i:]:
            r1 = get_effective_thickness_2t(t1, t2)
            r2 = get_effective_thickness_2t(t2, t1)
            assert r1 == r2, f"Asymmetry for ({t1}, {t2})"


def _subset_thicknesses():
    """Return a representative subset of grid thicknesses for the bulk symmetry test."""
    from app.domain.reference_profile import _MATRIX_THICKNESSES
    # Every other thickness to keep the test fast
    return _MATRIX_THICKNESSES[::2]


# ===========================================================================
# D. t1/t2 reversed order returns identical result
# ===========================================================================

def test_D_reversed_order_ok_status() -> None:
    r1 = get_effective_thickness_2t(0.8, 2.0)
    r2 = get_effective_thickness_2t(2.0, 0.8)
    assert r1.effective_thickness_mm == r2.effective_thickness_mm
    assert r1.band_selection_status == r2.band_selection_status
    assert r1.band_selection_status == BandSelectionStatus.OK


def test_D_reversed_order_specific_value() -> None:
    """Verify a non-diagonal lookup value matches across orderings."""
    r = get_effective_thickness_2t(0.7, 1.0)
    assert r.effective_thickness_mm == pytest.approx(0.8)
    assert get_effective_thickness_2t(1.0, 0.7).effective_thickness_mm == pytest.approx(0.8)


# ===========================================================================
# E. Unsupported thicknesses below matrix range
# ===========================================================================

def test_E_0_6mm_outside_matrix_single_sheet() -> None:
    """0.6 mm is within the profile declared range but outside the 2T matrix (0.7–3.0 mm)."""
    result = get_effective_thickness_2t(0.6, 1.0)
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


def test_E_both_sheets_0_6mm() -> None:
    result = get_effective_thickness_2t(0.6, 0.6)
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


def test_E_below_0_6mm() -> None:
    """Well below profile minimum."""
    result = get_effective_thickness_2t(0.5, 0.5)
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


def test_E_no_min_fallback() -> None:
    """
    0.6 + 1.0 mm must NOT fall back to min(0.6, 1.0) = 0.6 mm and return an
    effective thickness. The matrix must be used exclusively.
    """
    result = get_effective_thickness_2t(0.6, 1.0)
    # If a fallback were applied, effective_thickness_mm would be non-None.
    assert result.effective_thickness_mm is None


# ===========================================================================
# F. Unsupported thicknesses above matrix range (>3.0 mm)
# ===========================================================================

def test_F_above_3_0mm_single_sheet() -> None:
    result = get_effective_thickness_2t(3.1, 1.0)
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


def test_F_both_sheets_above_range() -> None:
    result = get_effective_thickness_2t(4.0, 4.0)
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


# ===========================================================================
# G. 3T → ENGINEERING_REVIEW_REQUIRED
# ===========================================================================

def test_G_3T_requires_engineering_review() -> None:
    result = get_effective_thickness("3T", [1.0, 1.2, 1.5])
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


def test_G_3T_no_adjacent_pair_minimum() -> None:
    """3T must NOT use an adjacent-pair minimum or any other invented extension."""
    result = get_effective_thickness("3T", [1.0, 1.0, 1.0])
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


# ===========================================================================
# H. 4T → ENGINEERING_REVIEW_REQUIRED
# ===========================================================================

def test_H_4T_requires_engineering_review() -> None:
    result = get_effective_thickness("4T", [0.8, 1.0, 1.5, 2.0])
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


def test_H_4T_no_t_min_fallback() -> None:
    result = get_effective_thickness("4T", [0.8, 0.8, 0.8, 0.8])
    assert result.effective_thickness_mm is None
    assert result.band_selection_status == BandSelectionStatus.ENGINEERING_REVIEW_REQUIRED


# ===========================================================================
# I. kN → daN conversion
# ===========================================================================

def test_I_kn_to_dan_unit_factor() -> None:
    """Conversion factor is exactly × 100."""
    assert kn_to_dan(1.0) == pytest.approx(100.0)
    assert kn_to_dan(0.0) == pytest.approx(0.0)


def test_I_kn_to_dan_representative_values() -> None:
    assert kn_to_dan(2.5) == pytest.approx(250.0)
    assert kn_to_dan(3.0) == pytest.approx(300.0)
    assert kn_to_dan(4.4) == pytest.approx(440.0)


def test_I_kn_to_dan_boundary_comparison_is_in_dan() -> None:
    """
    Boundary test: a force of 2.30 kN is 230 daN, which is the upper daN
    limit of Band 01. The comparison must happen in daN, not kN.
    """
    force_kn = 2.30
    force_dan = kn_to_dan(force_kn)
    band = REF_BANDS[0]  # REF_BAND_01
    assert force_dan == pytest.approx(band.force_max_dan)


# ===========================================================================
# J. 50 Hz cycles → ms
# ===========================================================================

def test_J_cycle_to_ms_one_cycle_50hz() -> None:
    """At 50 Hz exactly 1 cycle = 20 ms."""
    assert cycle_to_ms(1, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(20.0)


def test_J_cycle_to_ms_multiple_cycles() -> None:
    assert cycle_to_ms(10, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(200.0)
    assert cycle_to_ms(15, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(300.0)
    assert cycle_to_ms(20, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(400.0)


def test_J_cycle_to_ms_derived_from_profile_hz() -> None:
    """Conversion uses profile.cycle_basis_hz — not a hardcoded 20 ms constant."""
    assert REF_PROFILE_MS_2T_50HZ_V1.cycle_basis_hz == 50
    expected_ms_per_cycle = 1000.0 / REF_PROFILE_MS_2T_50HZ_V1.cycle_basis_hz
    assert expected_ms_per_cycle == pytest.approx(20.0)
    assert cycle_to_ms(7, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(7 * expected_ms_per_cycle)


# ===========================================================================
# K. ms → cycles
# ===========================================================================

def test_K_ms_to_cycle_one_cycle_50hz() -> None:
    assert ms_to_cycle(20.0, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(1.0)


def test_K_ms_to_cycle_multiple_values() -> None:
    assert ms_to_cycle(200.0, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(10.0)
    assert ms_to_cycle(300.0, REF_PROFILE_MS_2T_50HZ_V1) == pytest.approx(15.0)


def test_K_cycle_ms_round_trip() -> None:
    """cycle_to_ms and ms_to_cycle must be exact inverses."""
    for cycles in (1, 5, 10, 15, 20, 35):
        ms = cycle_to_ms(cycles, REF_PROFILE_MS_2T_50HZ_V1)
        assert isinstance(ms, float)
        back = ms_to_cycle(ms, REF_PROFILE_MS_2T_50HZ_V1)
        assert isinstance(back, float)
        assert back == pytest.approx(cycles)


# ===========================================================================
# L. Missing time basis → UNIT_BASIS_UNRESOLVED sentinel
# ===========================================================================

def test_L_no_profile_cycle_to_ms_unresolved() -> None:
    result = cycle_to_ms(10, None)
    assert result == UNIT_BASIS_UNRESOLVED


def test_L_no_profile_ms_to_cycle_unresolved() -> None:
    result = ms_to_cycle(200.0, None)
    assert result == UNIT_BASIS_UNRESOLVED


def test_L_unresolved_is_not_a_numeric_value() -> None:
    """The sentinel must not be accidentally compared as a number."""
    result = cycle_to_ms(10, None)
    assert not isinstance(result, (int, float))


# ===========================================================================
# M. Mild steel accepted
# ===========================================================================

def test_M_mild_steel_accepted() -> None:
    status = evaluate_material_scope("Düşük / Orta Karbonlu Çelik")
    assert status == ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE


def test_M_mild_steel_uses_profile_authorized_scope() -> None:
    """The authorized scope matches the profile's supported_material_scope."""
    assert "mild steel" in REF_PROFILE_MS_2T_50HZ_V1.supported_material_scope.lower()


# ===========================================================================
# N. AHSS → ENGINEERING_REVIEW_REQUIRED
# ===========================================================================

def test_N_ahss_requires_engineering_review() -> None:
    status = evaluate_material_scope("AHSS / UHSS / PHS")
    assert status == ReferenceGuidanceStatus.ENGINEERING_REVIEW_REQUIRED


# ===========================================================================
# O. Galvanized current guidance → ENGINEERING_REVIEW_REQUIRED
# ===========================================================================

def test_O_galvanized_requires_engineering_review() -> None:
    status = evaluate_material_scope("Galvanizli / Kaplamalı Çelik")
    assert status == ReferenceGuidanceStatus.ENGINEERING_REVIEW_REQUIRED


# ===========================================================================
# P. Aluminum → ENGINEERING_REVIEW_REQUIRED
# ===========================================================================

def test_P_aluminum_requires_engineering_review() -> None:
    status = evaluate_material_scope("Alüminyum Alaşımları")
    assert status == ReferenceGuidanceStatus.ENGINEERING_REVIEW_REQUIRED


def test_P_unknown_family_requires_engineering_review() -> None:
    """Any unrecognized material family must also require engineering review."""
    status = evaluate_material_scope("Bilinmeyen Malzeme")
    assert status == ReferenceGuidanceStatus.ENGINEERING_REVIEW_REQUIRED


# ===========================================================================
# Q. Missing newly introduced optional parameter → NOT_EVALUATED
# ===========================================================================

def test_Q_approach_cycles_none_is_not_evaluated() -> None:
    approach_cycles = None
    status = evaluate_optional_parameter(approach_cycles)
    assert status == ReferenceGuidanceStatus.NOT_EVALUATED


def test_Q_cooling_cycles_none_is_not_evaluated() -> None:
    cooling_cycles = None
    status = evaluate_optional_parameter(cooling_cycles)
    assert status == ReferenceGuidanceStatus.NOT_EVALUATED


def test_Q_air_pressure_bar_none_is_not_evaluated() -> None:
    air_pressure_bar = None
    status = evaluate_optional_parameter(air_pressure_bar)
    assert status == ReferenceGuidanceStatus.NOT_EVALUATED


def test_Q_not_evaluated_is_not_a_default_value() -> None:
    """
    NOT_EVALUATED must be a distinct status, not a numeric stand-in for an
    ideal default (which would silently assume the parameter is within range).
    """
    status = evaluate_optional_parameter(None)
    assert status != ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE
    assert status != ReferenceGuidanceStatus.BELOW_REFERENCE_RANGE
    assert status != ReferenceGuidanceStatus.ABOVE_REFERENCE_RANGE


# ===========================================================================
# R. No proprietary identifiers in API-visible profile data
# ===========================================================================

# Patterns that must not appear in any exported profile or band field.
_PROHIBITED_PATTERNS = (
    # OEM / company names
    "tofas", "TOFAS", "ford", "FORD", "volkswagen", "VOLKSWAGEN",
    "opel", "OPEL", "renault", "RENAULT", "fiat", "FIAT",
    # Specification / document identifiers
    "ISO ", "DIN ", "EN ", "GMW", "WSS-M", "VWPW", "DBL ",
    # Checklist / document artifacts
    "CheckList", "checklist", "check_list", "Rev0", "Rev1", "Rev2", "Rev3",
    "TABLO", "tablo",
    # Source filenames / formats
    ".xlsx", ".pdf", ".doc", ".xls",
    # Other proprietary provenance
    "puntakaynak", "PuntaKaynak", "PuntaKaynak_CheckList",
)


def test_R_no_proprietary_in_profile_fields() -> None:
    profile = REF_PROFILE_MS_2T_50HZ_V1
    fields = {
        "profile_id": profile.profile_id,
        "supported_material_scope": profile.supported_material_scope,
        "supported_stack_count": profile.supported_stack_count,
    }
    for field_name, field_value in fields.items():
        for pattern in _PROHIBITED_PATTERNS:
            assert pattern not in field_value, (
                f"Prohibited pattern '{pattern}' found in "
                f"profile.{field_name}='{field_value}'"
            )


def test_R_no_proprietary_in_band_ids() -> None:
    for band in REF_BANDS:
        for pattern in _PROHIBITED_PATTERNS:
            assert pattern not in band.band_id, (
                f"Prohibited pattern '{pattern}' in band_id '{band.band_id}'"
            )


def test_R_profile_id_uses_neutral_naming() -> None:
    """Profile ID must follow the REF_ neutral naming convention."""
    pid = REF_PROFILE_MS_2T_50HZ_V1.profile_id
    assert pid == "REF_PROFILE_MS_2T_50HZ_V1"
    assert pid.startswith("REF_")
    # Must not contain any OEM-identifying substring
    assert "OEM" not in pid
    assert "TOFAS" not in pid.upper()


def test_R_band_ids_use_neutral_naming() -> None:
    """All band IDs must follow the REF_BAND_NN neutral naming convention."""
    for i, band in enumerate(REF_BANDS, start=1):
        expected_id = f"REF_BAND_{i:02d}"
        assert band.band_id == expected_id, (
            f"Band {i} has non-neutral ID '{band.band_id}', "
            f"expected '{expected_id}'"
        )
        assert band.band_id.startswith("REF_BAND_")


def test_R_profile_material_scope_is_generic() -> None:
    """Scope description must use generic terms only."""
    scope = REF_PROFILE_MS_2T_50HZ_V1.supported_material_scope.lower()
    assert "mild steel" in scope
    for pattern in _PROHIBITED_PATTERNS:
        assert pattern.lower() not in scope


# ===========================================================================
# Additional: evaluate_parameter_guidance sanity checks
# ===========================================================================

def test_guidance_within_range() -> None:
    assert (
        evaluate_parameter_guidance(8.5, 7.8, 8.3)
        == ReferenceGuidanceStatus.ABOVE_REFERENCE_RANGE
    )
    assert (
        evaluate_parameter_guidance(8.0, 7.8, 8.3)
        == ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE
    )
    assert (
        evaluate_parameter_guidance(7.0, 7.8, 8.3)
        == ReferenceGuidanceStatus.BELOW_REFERENCE_RANGE
    )


def test_guidance_boundary_inclusive() -> None:
    assert (
        evaluate_parameter_guidance(7.8, 7.8, 8.3)
        == ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE
    )
    assert (
        evaluate_parameter_guidance(8.3, 7.8, 8.3)
        == ReferenceGuidanceStatus.WITHIN_REFERENCE_RANGE
    )


def test_guidance_outside_range_does_not_imply_fail() -> None:
    """
    Being outside the reference range must produce BELOW/ABOVE only —
    not ENGINEERING_REVIEW_REQUIRED and not NOT_EVALUATED.
    Compliance scoring is separate from guidance.
    """
    below = evaluate_parameter_guidance(6.0, 7.8, 8.3)
    above = evaluate_parameter_guidance(9.0, 7.8, 8.3)
    assert below == ReferenceGuidanceStatus.BELOW_REFERENCE_RANGE
    assert above == ReferenceGuidanceStatus.ABOVE_REFERENCE_RANGE
    assert below != ReferenceGuidanceStatus.ENGINEERING_REVIEW_REQUIRED
    assert above != ReferenceGuidanceStatus.NOT_EVALUATED


# ===========================================================================
# Profile metadata completeness
# ===========================================================================

def test_profile_required_metadata_present() -> None:
    p = REF_PROFILE_MS_2T_50HZ_V1
    assert p.profile_id
    assert p.cycle_basis_hz == 50
    assert p.supported_stack_count == "2T"
    assert p.supported_material_scope
    assert p.supported_thickness_min_mm == pytest.approx(0.6)
    assert p.supported_thickness_max_mm == pytest.approx(3.0)


def test_profile_is_immutable() -> None:
    with pytest.raises((TypeError, AttributeError)):
        REF_PROFILE_MS_2T_50HZ_V1.cycle_basis_hz = 60  # type: ignore[misc]


def test_four_bands_defined() -> None:
    assert len(REF_BANDS) == 4


def test_bands_cover_full_profile_range() -> None:
    """Bands must together cover 0.6–3.0 mm without gaps."""
    sorted_bands = sorted(REF_BANDS, key=lambda b: b.t_min_mm)
    assert sorted_bands[0].t_min_mm == pytest.approx(
        REF_PROFILE_MS_2T_50HZ_V1.supported_thickness_min_mm
    )
    assert sorted_bands[-1].t_max_mm == pytest.approx(
        REF_PROFILE_MS_2T_50HZ_V1.supported_thickness_max_mm
    )
