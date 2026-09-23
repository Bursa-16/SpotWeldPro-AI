from dataclasses import FrozenInstanceError

import pytest

from app.domain.engineering_library_types import (
    CoatingIdentity,
    ElectrodeCapGeometry,
    ElectrodeFaceGeometry,
    EngineeringLibraryLifecycleStatus,
    EngineeringLibraryRevisionMetadata,
    EngineeringLibrarySourceClass,
    MaterialIdentity,
    MaterialPropertySet,
    MaterialRevisionDraft,
    StackLayerDraft,
    StackUpRevisionDraft,
    WeldPulseDraft,
    WeldPulseType,
    WeldScheduleRevisionDraft,
)


def _metadata() -> EngineeringLibraryRevisionMetadata:
    return EngineeringLibraryRevisionMetadata(
        revision_number=1,
        lifecycle_status=EngineeringLibraryLifecycleStatus.DRAFT,
        source_class=EngineeringLibrarySourceClass.SOURCE_BACKED,
        created_by_actor_id="test-engineer",
        evidence_reference_ids=(1,),
    )


def test_revision_metadata_rejects_non_positive_revision() -> None:
    with pytest.raises(ValueError, match="revision_number must be positive"):
        EngineeringLibraryRevisionMetadata(
            revision_number=0,
            lifecycle_status=EngineeringLibraryLifecycleStatus.DRAFT,
            source_class=EngineeringLibrarySourceClass.SOURCE_BACKED,
            created_by_actor_id="test-engineer",
        )


def test_material_revision_rejects_inverted_thickness_range() -> None:
    with pytest.raises(
        ValueError,
        match="thickness_min_mm cannot exceed thickness_max_mm",
    ):
        MaterialRevisionDraft(
            identity=MaterialIdentity(
                material_id="MAT-001",
                family="Steel",
                grade="Example Grade",
            ),
            metadata=_metadata(),
            properties=MaterialPropertySet(),
            thickness_min_mm=2.0,
            thickness_max_mm=1.0,
        )


def test_stack_up_requires_contiguous_sequence() -> None:
    with pytest.raises(
        ValueError,
        match="stack layer sequence must be contiguous starting at 1",
    ):
        StackUpRevisionDraft(
            stack_id="STACK-001",
            metadata=_metadata(),
            layers=(
                StackLayerDraft(
                    sequence=1,
                    material_revision_id=1,
                    thickness_mm=1.0,
                ),
                StackLayerDraft(
                    sequence=3,
                    material_revision_id=2,
                    thickness_mm=1.2,
                ),
            ),
        )


def test_electrode_geometry_requires_positive_face_diameter() -> None:
    with pytest.raises(ValueError, match="face_diameter_mm must be positive"):
        ElectrodeCapGeometry(
            face_geometry=ElectrodeFaceGeometry.FLAT,
            face_diameter_mm=0.0,
        )


def test_weld_schedule_requires_contiguous_pulse_sequence() -> None:
    with pytest.raises(
        ValueError,
        match="pulse sequence must be contiguous starting at 1",
    ):
        WeldScheduleRevisionDraft(
            schedule_id="SCH-001",
            metadata=_metadata(),
            pulses=(
                WeldPulseDraft(
                    sequence=1,
                    pulse_type=WeldPulseType.PREHEAT,
                    current_ka=5.0,
                    duration_cycles=3.0,
                ),
                WeldPulseDraft(
                    sequence=3,
                    pulse_type=WeldPulseType.WELD,
                    current_ka=8.0,
                    duration_cycles=10.0,
                ),
            ),
        )


def test_domain_contracts_are_immutable() -> None:
    coating = CoatingIdentity(
        coating_id="COAT-001",
        family="Zn",
        designation="Example",
    )

    with pytest.raises(FrozenInstanceError):
        coating.family = "Changed"  # type: ignore[misc]


def test_valid_schedule_constructs_successfully() -> None:
    schedule = WeldScheduleRevisionDraft(
        schedule_id="SCH-OK",
        metadata=_metadata(),
        pulses=(
            WeldPulseDraft(
                sequence=1,
                pulse_type=WeldPulseType.PREHEAT,
                current_ka=4.5,
                duration_cycles=2.0,
            ),
            WeldPulseDraft(
                sequence=2,
                pulse_type=WeldPulseType.WELD,
                current_ka=8.5,
                duration_cycles=12.0,
            ),
        ),
        squeeze_cycles=10.0,
        hold_cycles=8.0,
        nominal_force_kn=3.2,
    )

    assert schedule.schedule_id == "SCH-OK"
    assert len(schedule.pulses) == 2
