from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.db.session import Base
from app.models.engineering_library import (
    EngineeringCoating,
    EngineeringCoatingRevision,
    EngineeringMaterial,
    EngineeringMaterialRevision,
    EngineeringStackLayer,
    EngineeringStackUp,
    EngineeringStackUpRevision,
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


def test_revision_models_use_append_only_protection() -> None:
    protected = {
        EngineeringMaterial,
        EngineeringMaterialRevision,
        EngineeringCoating,
        EngineeringCoatingRevision,
        EngineeringStackUp,
        EngineeringStackUpRevision,
        EngineeringStackLayer,
    }

    for model in protected:
        assert model.__mapper__.dispatch.before_update
        assert model.__mapper__.dispatch.before_delete
