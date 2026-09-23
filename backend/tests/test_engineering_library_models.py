from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.db.session import Base
from app.models.engineering_library import (
    EngineeringCoating,
    EngineeringCoatingRevision,
    EngineeringElectrode,
    EngineeringElectrodeRevision,
    EngineeringMaterial,
    EngineeringMaterialRevision,
    EngineeringStackLayer,
    EngineeringStackUp,
    EngineeringStackUpRevision,
    EngineeringWeldGun,
    EngineeringWeldGunRevision,
    EngineeringWeldPulse,
    EngineeringWeldSchedule,
    EngineeringWeldScheduleRevision,
)


def _constraint_names(table_name: str, constraint_type: type) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, constraint_type) and constraint.name
    }


def test_engineering_library_tables_are_registered() -> None:
    expected = {
        "engineering_materials",
        "engineering_material_revisions",
        "engineering_coatings",
        "engineering_coating_revisions",
        "engineering_stack_ups",
        "engineering_stack_up_revisions",
        "engineering_stack_layers",
        "engineering_electrodes",
        "engineering_electrode_revisions",
        "engineering_weld_guns",
        "engineering_weld_gun_revisions",
        "engineering_weld_schedules",
        "engineering_weld_schedule_revisions",
        "engineering_weld_pulses",
    }
    assert expected <= set(Base.metadata.tables)


def test_material_identity_and_revision_constraints_exist() -> None:
    assert EngineeringMaterial.__tablename__ == "engineering_materials"

    revision_unique = _constraint_names(
        "engineering_material_revisions",
        UniqueConstraint,
    )
    revision_checks = _constraint_names(
        "engineering_material_revisions",
        CheckConstraint,
    )
    revision_fks = _constraint_names(
        "engineering_material_revisions",
        ForeignKeyConstraint,
    )

    assert {
        "uq_engineering_material_revisions_logical_revision",
        "uq_engineering_material_revisions_context_internal_id",
        "uq_engineering_material_revisions_single_successor",
    } <= revision_unique

    assert {
        "ck_engineering_material_revisions_positive_revision",
        "ck_engineering_material_revisions_not_self_superseding",
        "ck_engineering_material_revisions_positive_min_thickness",
        "ck_engineering_material_revisions_positive_max_thickness",
        "ck_engineering_material_revisions_thickness_window",
    } <= revision_checks

    assert (
        "fk_engineering_material_revisions_same_material_supersession"
        in revision_fks
    )


def test_coating_identity_and_revision_constraints_exist() -> None:
    assert EngineeringCoating.__tablename__ == "engineering_coatings"

    revision_unique = _constraint_names(
        "engineering_coating_revisions",
        UniqueConstraint,
    )
    revision_checks = _constraint_names(
        "engineering_coating_revisions",
        CheckConstraint,
    )
    revision_fks = _constraint_names(
        "engineering_coating_revisions",
        ForeignKeyConstraint,
    )

    assert {
        "uq_engineering_coating_revisions_logical_revision",
        "uq_engineering_coating_revisions_context_internal_id",
        "uq_engineering_coating_revisions_single_successor",
    } <= revision_unique

    assert {
        "ck_engineering_coating_revisions_positive_revision",
        "ck_engineering_coating_revisions_not_self_superseding",
        "ck_engineering_coating_revisions_positive_thickness",
    } <= revision_checks

    assert (
        "fk_engineering_coating_revisions_same_coating_supersession"
        in revision_fks
    )


def test_stack_identity_revision_and_layer_constraints_exist() -> None:
    assert EngineeringStackUp.__tablename__ == "engineering_stack_ups"
    assert EngineeringStackLayer.__tablename__ == "engineering_stack_layers"

    revision_unique = _constraint_names(
        "engineering_stack_up_revisions",
        UniqueConstraint,
    )
    revision_checks = _constraint_names(
        "engineering_stack_up_revisions",
        CheckConstraint,
    )
    revision_fks = _constraint_names(
        "engineering_stack_up_revisions",
        ForeignKeyConstraint,
    )

    assert {
        "uq_engineering_stack_up_revisions_logical_revision",
        "uq_engineering_stack_up_revisions_context_internal_id",
        "uq_engineering_stack_up_revisions_single_successor",
    } <= revision_unique

    assert {
        "ck_engineering_stack_up_revisions_positive_revision",
        "ck_engineering_stack_up_revisions_not_self_superseding",
    } <= revision_checks

    assert (
        "fk_engineering_stack_up_revisions_same_stack_supersession"
        in revision_fks
    )

    layer_unique = _constraint_names(
        "engineering_stack_layers",
        UniqueConstraint,
    )
    layer_checks = _constraint_names(
        "engineering_stack_layers",
        CheckConstraint,
    )

    assert "uq_engineering_stack_layers_revision_sequence" in layer_unique
    assert {
        "ck_engineering_stack_layers_positive_sequence",
        "ck_engineering_stack_layers_positive_thickness",
    } <= layer_checks


def test_electrode_identity_and_revision_constraints_exist() -> None:
    assert EngineeringElectrode.__tablename__ == "engineering_electrodes"

    revision_unique = _constraint_names(
        "engineering_electrode_revisions",
        UniqueConstraint,
    )
    revision_checks = _constraint_names(
        "engineering_electrode_revisions",
        CheckConstraint,
    )
    revision_fks = _constraint_names(
        "engineering_electrode_revisions",
        ForeignKeyConstraint,
    )

    assert {
        "uq_engineering_electrode_revisions_logical_revision",
        "uq_engineering_electrode_revisions_context_internal_id",
        "uq_engineering_electrode_revisions_single_successor",
    } <= revision_unique

    assert {
        "ck_engineering_electrode_revisions_positive_revision",
        "ck_engineering_electrode_revisions_not_self_superseding",
        "ck_engineering_electrode_revisions_positive_face_diameter",
        "ck_engineering_electrode_revisions_positive_tip_diameter",
        "ck_engineering_electrode_revisions_positive_radius",
    } <= revision_checks

    assert (
        "fk_engineering_electrode_revisions_same_electrode_supersession"
        in revision_fks
    )


def test_weld_gun_identity_and_revision_constraints_exist() -> None:
    assert EngineeringWeldGun.__tablename__ == "engineering_weld_guns"

    revision_unique = _constraint_names(
        "engineering_weld_gun_revisions",
        UniqueConstraint,
    )
    revision_checks = _constraint_names(
        "engineering_weld_gun_revisions",
        CheckConstraint,
    )
    revision_fks = _constraint_names(
        "engineering_weld_gun_revisions",
        ForeignKeyConstraint,
    )

    assert {
        "uq_engineering_weld_gun_revisions_logical_revision",
        "uq_engineering_weld_gun_revisions_context_internal_id",
        "uq_engineering_weld_gun_revisions_single_successor",
    } <= revision_unique

    assert {
        "ck_engineering_weld_gun_revisions_positive_revision",
        "ck_engineering_weld_gun_revisions_not_self_superseding",
        "ck_engineering_weld_gun_revisions_positive_max_force",
        "ck_engineering_weld_gun_revisions_positive_throat_depth",
        "ck_engineering_weld_gun_revisions_positive_max_opening",
    } <= revision_checks

    assert (
        "fk_engineering_weld_gun_revisions_same_gun_supersession"
        in revision_fks
    )


def test_weld_schedule_revision_and_pulse_constraints_exist() -> None:
    assert EngineeringWeldSchedule.__tablename__ == "engineering_weld_schedules"
    assert EngineeringWeldPulse.__tablename__ == "engineering_weld_pulses"

    revision_unique = _constraint_names(
        "engineering_weld_schedule_revisions",
        UniqueConstraint,
    )
    revision_checks = _constraint_names(
        "engineering_weld_schedule_revisions",
        CheckConstraint,
    )
    revision_fks = _constraint_names(
        "engineering_weld_schedule_revisions",
        ForeignKeyConstraint,
    )

    assert {
        "uq_engineering_weld_schedule_revisions_logical_revision",
        "uq_engineering_weld_schedule_revisions_context_internal_id",
        "uq_engineering_weld_schedule_revisions_single_successor",
    } <= revision_unique

    assert {
        "ck_engineering_weld_schedule_revisions_positive_revision",
        "ck_engineering_weld_schedule_revisions_not_self_superseding",
        "ck_engineering_weld_schedule_revisions_non_negative_squeeze",
        "ck_engineering_weld_schedule_revisions_non_negative_hold",
        "ck_engineering_weld_schedule_revisions_positive_nominal_force",
    } <= revision_checks

    assert (
        "fk_eng_weld_sched_rev_same_sched_supersession"
        in revision_fks
    )

    pulse_unique = _constraint_names(
        "engineering_weld_pulses",
        UniqueConstraint,
    )
    pulse_checks = _constraint_names(
        "engineering_weld_pulses",
        CheckConstraint,
    )

    assert "uq_engineering_weld_pulses_revision_sequence" in pulse_unique
    assert {
        "ck_engineering_weld_pulses_positive_sequence_number",
        "ck_engineering_weld_pulses_non_negative_duration",
    } <= pulse_checks


def test_revision_models_use_append_only_protection() -> None:
    protected = {
        EngineeringMaterial,
        EngineeringMaterialRevision,
        EngineeringCoating,
        EngineeringCoatingRevision,
        EngineeringStackUp,
        EngineeringStackUpRevision,
        EngineeringStackLayer,
        EngineeringElectrode,
        EngineeringElectrodeRevision,
        EngineeringWeldGun,
        EngineeringWeldGunRevision,
        EngineeringWeldSchedule,
        EngineeringWeldScheduleRevision,
        EngineeringWeldPulse,
    }

    for model in protected:
        assert model.__mapper__.dispatch.before_update
        assert model.__mapper__.dispatch.before_delete
