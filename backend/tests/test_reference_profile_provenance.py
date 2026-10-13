"""
Tests for SOURCE_REGISTRY provenance foundation — 02E-A.

Scope: SourceCellRef dataclass, six status constants, and the two
       initial F10 source records.

What is NOT tested here (covered by test_reference_profile.py):
  - ParameterBand structure and attributes
  - REF_BANDS contents
  - Matrix lookup logic (get_effective_thickness*, get_parameter_band)
  - Material scope / optional-parameter evaluation
  - API-visible profile/band field content

Engineering guard invariants tested here:
  - Geometry mapping remains UNVERIFIED for all current entries
  - Engineering approval remains PENDING for all current entries
  - No entry grants production parameter authority
  - No force/current recommendation is activated through this registry
  - Provenance is NOT exposed in WeldAnalysisResponse-facing data

Avoid tautological tests: constants are tested against literal expected
values, not against each other.
"""
from __future__ import annotations

import pytest
from types import MappingProxyType

from app.domain.reference_profile import (
    SOURCE_CELL_VERIFIED,
    SOURCE_CELL_UNVERIFIED,
    GEOMETRY_MAPPING_UNVERIFIED,
    GEOMETRY_MAPPING_CONFIRMED,
    ENGINEERING_APPROVAL_PENDING,
    ENGINEERING_APPROVAL_GRANTED,
    SOURCE_REGISTRY,
    SourceCellRef,
    # Existing public symbols — imported to verify they still exist and are
    # unchanged (structural smoke-test; values asserted in test_reference_profile.py)
    ParameterBand,
    REF_BANDS,
    get_effective_thickness,
    get_effective_thickness_2t,
    get_parameter_band,
)


# ---------------------------------------------------------------------------
# A. Status constant identity (literal strings, not tautological cross-checks)
# ---------------------------------------------------------------------------

class TestStatusConstants:
    def test_source_cell_verified_value(self):
        assert SOURCE_CELL_VERIFIED == "SOURCE_CELL_VERIFIED"

    def test_source_cell_unverified_value(self):
        assert SOURCE_CELL_UNVERIFIED == "SOURCE_CELL_UNVERIFIED"

    def test_geometry_mapping_unverified_value(self):
        assert GEOMETRY_MAPPING_UNVERIFIED == "GEOMETRY_MAPPING_UNVERIFIED"

    def test_geometry_mapping_confirmed_value(self):
        assert GEOMETRY_MAPPING_CONFIRMED == "GEOMETRY_MAPPING_CONFIRMED"

    def test_engineering_approval_pending_value(self):
        assert ENGINEERING_APPROVAL_PENDING == "ENGINEERING_APPROVAL_PENDING"

    def test_engineering_approval_granted_value(self):
        assert ENGINEERING_APPROVAL_GRANTED == "ENGINEERING_APPROVAL_GRANTED"

    def test_all_six_constants_are_strings(self):
        for const in (
            SOURCE_CELL_VERIFIED,
            SOURCE_CELL_UNVERIFIED,
            GEOMETRY_MAPPING_UNVERIFIED,
            GEOMETRY_MAPPING_CONFIRMED,
            ENGINEERING_APPROVAL_PENDING,
            ENGINEERING_APPROVAL_GRANTED,
        ):
            assert isinstance(const, str)

    def test_all_six_constants_are_distinct(self):
        constants = [
            SOURCE_CELL_VERIFIED,
            SOURCE_CELL_UNVERIFIED,
            GEOMETRY_MAPPING_UNVERIFIED,
            GEOMETRY_MAPPING_CONFIRMED,
            ENGINEERING_APPROVAL_PENDING,
            ENGINEERING_APPROVAL_GRANTED,
        ]
        assert len(set(constants)) == 6

    def test_verification_pair_not_equal(self):
        assert SOURCE_CELL_VERIFIED != SOURCE_CELL_UNVERIFIED

    def test_geometry_pair_not_equal(self):
        assert GEOMETRY_MAPPING_UNVERIFIED != GEOMETRY_MAPPING_CONFIRMED

    def test_approval_pair_not_equal(self):
        assert ENGINEERING_APPROVAL_PENDING != ENGINEERING_APPROVAL_GRANTED


# ---------------------------------------------------------------------------
# B. SourceCellRef dataclass — frozen, structural, value equality, hashable
# ---------------------------------------------------------------------------

_MINIMAL_KWARGS = dict(
    workbook_filename="test.xlsx",
    workbook_sha256="abc123",
    worksheet_name="Sheet1",
    cell_address="A1",
    raw_value="1.0",
    original_unit="kA",
    source_column_header="Col",
    cell_verification_status=SOURCE_CELL_UNVERIFIED,
    geometry_mapping_status=GEOMETRY_MAPPING_UNVERIFIED,
    engineering_approval_status=ENGINEERING_APPROVAL_PENDING,
)


class TestSourceCellRef:
    def test_is_dataclass_instance(self):
        ref = SourceCellRef(**_MINIMAL_KWARGS)
        import dataclasses
        assert dataclasses.is_dataclass(ref)

    def test_is_frozen(self):
        ref = SourceCellRef(**_MINIMAL_KWARGS)
        with pytest.raises((AttributeError, TypeError)):
            ref.raw_value = "mutated"  # type: ignore[misc]

    def test_frozen_rejects_mutation_of_existing_field(self):
        """Re-assigning any field via normal attribute syntax must raise."""
        ref = SourceCellRef(**_MINIMAL_KWARGS)
        with pytest.raises((AttributeError, TypeError)):
            ref.workbook_filename = "mutated"  # type: ignore[misc]

    def test_value_equality(self):
        ref_a = SourceCellRef(**_MINIMAL_KWARGS)
        ref_b = SourceCellRef(**_MINIMAL_KWARGS)
        assert ref_a == ref_b

    def test_value_inequality_on_field_difference(self):
        ref_a = SourceCellRef(**_MINIMAL_KWARGS)
        ref_b = SourceCellRef(**{**_MINIMAL_KWARGS, "raw_value": "999"})
        assert ref_a != ref_b

    def test_is_hashable(self):
        ref = SourceCellRef(**_MINIMAL_KWARGS)
        h = hash(ref)
        assert isinstance(h, int)

    def test_hashable_equal_objects_have_equal_hash(self):
        ref_a = SourceCellRef(**_MINIMAL_KWARGS)
        ref_b = SourceCellRef(**_MINIMAL_KWARGS)
        assert hash(ref_a) == hash(ref_b)

    def test_usable_as_dict_key(self):
        ref = SourceCellRef(**_MINIMAL_KWARGS)
        d = {ref: "ok"}
        assert d[ref] == "ok"

    def test_ten_fields_accessible(self):
        ref = SourceCellRef(**_MINIMAL_KWARGS)
        assert ref.workbook_filename == "test.xlsx"
        assert ref.workbook_sha256 == "abc123"
        assert ref.worksheet_name == "Sheet1"
        assert ref.cell_address == "A1"
        assert ref.raw_value == "1.0"
        assert ref.original_unit == "kA"
        assert ref.source_column_header == "Col"
        assert ref.cell_verification_status == SOURCE_CELL_UNVERIFIED
        assert ref.geometry_mapping_status == GEOMETRY_MAPPING_UNVERIFIED
        assert ref.engineering_approval_status == ENGINEERING_APPROVAL_PENDING


# ---------------------------------------------------------------------------
# C. SOURCE_REGISTRY type and immutability
# ---------------------------------------------------------------------------

class TestSourceRegistryImmutability:
    def test_is_mapping_proxy(self):
        assert isinstance(SOURCE_REGISTRY, MappingProxyType)

    def test_set_item_raises(self):
        fake_ref = SourceCellRef(**_MINIMAL_KWARGS)
        with pytest.raises(TypeError):
            SOURCE_REGISTRY[("Sheet1", "A1")] = fake_ref  # type: ignore[index]

    def test_del_item_raises(self):
        with pytest.raises(TypeError):
            del SOURCE_REGISTRY[("04_Kuvvet", "F10")]  # type: ignore[attr-defined]

    def test_clear_raises(self):
        with pytest.raises(AttributeError):
            SOURCE_REGISTRY.clear()  # type: ignore[attr-defined]

    def test_update_raises(self):
        with pytest.raises(AttributeError):
            SOURCE_REGISTRY.update({("X", "Y"): SourceCellRef(**_MINIMAL_KWARGS)})  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# D. Registry contents — exactly two initial records
# ---------------------------------------------------------------------------

EXPECTED_KEYS = {
    ("04_Kuvvet", "F10"),
    ("05-Akım", "F10"),
}

WORKBOOK_FILENAME = "PuntaKaynak_CheckList_Rev03_22062017(2).xlsx"
WORKBOOK_SHA256 = "ee440f5451db54c3bd23b17f4773655eb424932f3e6c4f524faaf321d138fcfa"


class TestRegistryContents:
    def test_exactly_two_entries(self):
        assert len(SOURCE_REGISTRY) == 2

    def test_force_key_present(self):
        assert ("04_Kuvvet", "F10") in SOURCE_REGISTRY

    def test_current_key_present(self):
        assert ("05-Akım", "F10") in SOURCE_REGISTRY

    def test_no_other_keys(self):
        assert set(SOURCE_REGISTRY.keys()) == EXPECTED_KEYS

    def test_all_keys_are_two_string_tuples(self):
        for key in SOURCE_REGISTRY:
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str)
            assert isinstance(key[1], str)

    def test_keys_match_record_worksheet_name(self):
        for (ws, ca), ref in SOURCE_REGISTRY.items():
            assert ref.worksheet_name == ws

    def test_keys_match_record_cell_address(self):
        for (ws, ca), ref in SOURCE_REGISTRY.items():
            assert ref.cell_address == ca

    def test_no_band_id_keys(self):
        """Registry keys must not be band identifiers."""
        for key in SOURCE_REGISTRY:
            for part in key:
                assert not part.startswith("REF_BAND_"), (
                    f"Registry key {key!r} contains a band ID — "
                    "geometry authority must not be implied by key design"
                )


# ---------------------------------------------------------------------------
# E. Workbook identity for all registry entries
# ---------------------------------------------------------------------------

class TestWorkbookIdentity:
    def test_force_workbook_filename(self):
        ref = SOURCE_REGISTRY[("04_Kuvvet", "F10")]
        assert ref.workbook_filename == WORKBOOK_FILENAME

    def test_force_workbook_sha256(self):
        ref = SOURCE_REGISTRY[("04_Kuvvet", "F10")]
        assert ref.workbook_sha256 == WORKBOOK_SHA256

    def test_current_workbook_filename(self):
        ref = SOURCE_REGISTRY[("05-Akım", "F10")]
        assert ref.workbook_filename == WORKBOOK_FILENAME

    def test_current_workbook_sha256(self):
        ref = SOURCE_REGISTRY[("05-Akım", "F10")]
        assert ref.workbook_sha256 == WORKBOOK_SHA256

    def test_all_entries_share_same_workbook(self):
        filenames = {ref.workbook_filename for ref in SOURCE_REGISTRY.values()}
        sha256s = {ref.workbook_sha256 for ref in SOURCE_REGISTRY.values()}
        assert filenames == {WORKBOOK_FILENAME}
        assert sha256s == {WORKBOOK_SHA256}

    def test_sha256_length(self):
        """SHA-256 hex string must be exactly 64 characters."""
        assert len(WORKBOOK_SHA256) == 64
        assert all(c in "0123456789abcdef" for c in WORKBOOK_SHA256)

    def test_all_sha256_fields_are_64_hex(self):
        for ref in SOURCE_REGISTRY.values():
            assert len(ref.workbook_sha256) == 64
            assert all(c in "0123456789abcdef" for c in ref.workbook_sha256)


# ---------------------------------------------------------------------------
# F. Force record (04_Kuvvet / F10) field assertions
# ---------------------------------------------------------------------------

class TestForceRecord:
    @pytest.fixture
    def force_ref(self):
        return SOURCE_REGISTRY[("04_Kuvvet", "F10")]

    def test_worksheet_name(self, force_ref):
        assert force_ref.worksheet_name == "04_Kuvvet"

    def test_cell_address(self, force_ref):
        assert force_ref.cell_address == "F10"

    def test_raw_value_is_230(self, force_ref):
        assert force_ref.raw_value == "230"

    def test_original_unit_is_dan(self, force_ref):
        assert force_ref.original_unit == "daN"

    def test_cell_verification_status(self, force_ref):
        assert force_ref.cell_verification_status == SOURCE_CELL_VERIFIED

    def test_geometry_mapping_status_unverified(self, force_ref):
        assert force_ref.geometry_mapping_status == GEOMETRY_MAPPING_UNVERIFIED

    def test_geometry_mapping_status_not_confirmed(self, force_ref):
        assert force_ref.geometry_mapping_status != GEOMETRY_MAPPING_CONFIRMED

    def test_engineering_approval_status_pending(self, force_ref):
        assert force_ref.engineering_approval_status == ENGINEERING_APPROVAL_PENDING

    def test_engineering_approval_status_not_granted(self, force_ref):
        assert force_ref.engineering_approval_status != ENGINEERING_APPROVAL_GRANTED


# ---------------------------------------------------------------------------
# G. Current record (05-Akım / F10) field assertions
# ---------------------------------------------------------------------------

class TestCurrentRecord:
    @pytest.fixture
    def current_ref(self):
        return SOURCE_REGISTRY[("05-Akım", "F10")]

    def test_worksheet_name(self, current_ref):
        assert current_ref.worksheet_name == "05-Akım"

    def test_cell_address(self, current_ref):
        assert current_ref.cell_address == "F10"

    def test_raw_value_is_8_3(self, current_ref):
        assert current_ref.raw_value == "8.3"

    def test_original_unit_is_ka(self, current_ref):
        assert current_ref.original_unit == "kA"

    def test_cell_verification_status(self, current_ref):
        assert current_ref.cell_verification_status == SOURCE_CELL_VERIFIED

    def test_geometry_mapping_status_unverified(self, current_ref):
        assert current_ref.geometry_mapping_status == GEOMETRY_MAPPING_UNVERIFIED

    def test_geometry_mapping_status_not_confirmed(self, current_ref):
        assert current_ref.geometry_mapping_status != GEOMETRY_MAPPING_CONFIRMED

    def test_engineering_approval_status_pending(self, current_ref):
        assert current_ref.engineering_approval_status == ENGINEERING_APPROVAL_PENDING

    def test_engineering_approval_status_not_granted(self, current_ref):
        assert current_ref.engineering_approval_status != ENGINEERING_APPROVAL_GRANTED


# ---------------------------------------------------------------------------
# H. Engineering guard invariants — all current registry entries
# ---------------------------------------------------------------------------

class TestEngineeringGuardInvariants:
    def test_no_entry_has_geometry_confirmed(self):
        """All current entries must remain GEOMETRY_MAPPING_UNVERIFIED."""
        for key, ref in SOURCE_REGISTRY.items():
            assert ref.geometry_mapping_status != GEOMETRY_MAPPING_CONFIRMED, (
                f"Entry {key!r} has GEOMETRY_MAPPING_CONFIRMED — "
                "this axis must not be set without S-1 resolution"
            )

    def test_no_entry_has_engineering_approval_granted(self):
        """All current entries must remain ENGINEERING_APPROVAL_PENDING."""
        for key, ref in SOURCE_REGISTRY.items():
            assert ref.engineering_approval_status != ENGINEERING_APPROVAL_GRANTED, (
                f"Entry {key!r} has ENGINEERING_APPROVAL_GRANTED — "
                "no automatic engineering approval is allowed"
            )

    def test_no_entry_activates_production_authority(self):
        """Neither geometry confirmed nor approval granted may appear."""
        production_blocking = {GEOMETRY_MAPPING_CONFIRMED, ENGINEERING_APPROVAL_GRANTED}
        for key, ref in SOURCE_REGISTRY.items():
            statuses = {
                ref.cell_verification_status,
                ref.geometry_mapping_status,
                ref.engineering_approval_status,
            }
            overlap = statuses & production_blocking
            assert not overlap, (
                f"Entry {key!r} carries production-authority status: {overlap}"
            )

    def test_source_cell_verified_does_not_imply_geometry_confirmed(self):
        """Verifying a cell value does NOT confirm geometry mapping."""
        for key, ref in SOURCE_REGISTRY.items():
            if ref.cell_verification_status == SOURCE_CELL_VERIFIED:
                assert ref.geometry_mapping_status == GEOMETRY_MAPPING_UNVERIFIED, (
                    f"Entry {key!r}: SOURCE_CELL_VERIFIED must not imply "
                    "GEOMETRY_MAPPING_CONFIRMED"
                )

    def test_geometry_confirmed_does_not_imply_engineering_approved(self):
        """
        If any future entry reaches GEOMETRY_MAPPING_CONFIRMED, that alone
        must not also set ENGINEERING_APPROVAL_GRANTED.
        Passes trivially for current entries (none are GEOMETRY_MAPPING_CONFIRMED).
        """
        for key, ref in SOURCE_REGISTRY.items():
            if ref.geometry_mapping_status == GEOMETRY_MAPPING_CONFIRMED:
                assert ref.engineering_approval_status != ENGINEERING_APPROVAL_GRANTED, (
                    f"Entry {key!r}: GEOMETRY_MAPPING_CONFIRMED must not imply "
                    "ENGINEERING_APPROVAL_GRANTED"
                )

    def test_raw_values_are_strings_not_numerics(self):
        """raw_value must be the verbatim string from the source cell."""
        for key, ref in SOURCE_REGISTRY.items():
            assert isinstance(ref.raw_value, str), (
                f"Entry {key!r}: raw_value must be str, got {type(ref.raw_value)}"
            )

    def test_force_raw_value_not_converted_to_kn(self):
        """230 daN must remain as-is; no automatic unit conversion to kN."""
        ref = SOURCE_REGISTRY[("04_Kuvvet", "F10")]
        # raw_value stays "230", not "2.30" or "2.3"
        assert ref.raw_value == "230"
        assert ref.original_unit == "daN"

    def test_current_raw_value_not_converted(self):
        """8.3 kA must remain as-is; no conversion to A or other units."""
        ref = SOURCE_REGISTRY[("05-Akım", "F10")]
        assert ref.raw_value == "8.3"
        assert ref.original_unit == "kA"


# ---------------------------------------------------------------------------
# I. Pre-existing module symbols remain accessible (structural smoke-test)
# ---------------------------------------------------------------------------

class TestPreExistingSymbolsUnchanged:
    def test_parameter_band_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(ParameterBand)

    def test_ref_bands_is_sequence(self):
        # REF_BANDS is a tuple of ParameterBand; verify it is non-dict iterable
        assert hasattr(REF_BANDS, "__iter__")
        assert not isinstance(REF_BANDS, dict)

    def test_ref_bands_has_four_entries(self):
        assert len(REF_BANDS) == 4

    def test_ref_bands_band_ids(self):
        band_ids = {b.band_id for b in REF_BANDS}
        assert band_ids == {
            "REF_BAND_01",
            "REF_BAND_02",
            "REF_BAND_03",
            "REF_BAND_04",
        }

    def test_get_effective_thickness_2t_callable(self):
        assert callable(get_effective_thickness_2t)

    def test_get_effective_thickness_callable(self):
        assert callable(get_effective_thickness)

    def test_get_parameter_band_callable(self):
        assert callable(get_parameter_band)

    def test_matrix_lookup_returns_band_for_known_thickness(self):
        """Smoke-test: 1.5mm + 1.5mm should resolve to a ParameterBand."""
        result = get_parameter_band(1.5, 1.5)
        assert result is not None
        assert isinstance(result, ParameterBand)

    def test_parameter_band_has_no_provenance_fields(self):
        """ParameterBand must not have been modified to carry provenance."""
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(ParameterBand)}
        provenance_names = {
            "workbook_filename", "workbook_sha256", "worksheet_name",
            "cell_address", "raw_value", "original_unit",
            "source_column_header", "cell_verification_status",
            "geometry_mapping_status", "engineering_approval_status",
            "source_cell_ref", "provenance",
        }
        overlap = field_names & provenance_names
        assert not overlap, (
            f"ParameterBand has unexpected provenance fields: {overlap}"
        )


# ---------------------------------------------------------------------------
# J. API non-exposure guard
# ---------------------------------------------------------------------------

class TestAPIProvenance:
    def test_weld_analysis_response_has_no_source_registry_field(self):
        """WeldAnalysisResponse must not expose SOURCE_REGISTRY or provenance."""
        try:
            from app.schemas.analysis import WeldAnalysisResponse
            field_names = set(WeldAnalysisResponse.model_fields.keys())
        except ImportError:
            pytest.skip("WeldAnalysisResponse not importable in this environment")

        provenance_field_names = {
            "source_registry", "source_cells", "provenance",
            "workbook_filename", "workbook_sha256", "source_cell_ref",
            "cell_verification_status", "geometry_mapping_status",
            "engineering_approval_status",
        }
        overlap = field_names & provenance_field_names
        assert not overlap, (
            f"WeldAnalysisResponse exposes provenance fields: {overlap}"
        )

    def test_source_registry_not_importable_from_schemas(self):
        """SOURCE_REGISTRY should not be re-exported from API schemas."""
        try:
            import app.schemas.analysis as schemas
            has_registry = hasattr(schemas, "SOURCE_REGISTRY")
            assert not has_registry, (
                "SOURCE_REGISTRY is accessible from app.schemas.analysis — "
                "provenance must remain internal to domain layer"
            )
        except ImportError:
            pytest.skip("app.schemas.analysis not importable in this environment")
