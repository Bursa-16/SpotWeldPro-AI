"""Repository unit tests for Engineering Library — CE-02C.

Tests run against SQLite (in-memory) via the session-scoped `database` fixture
from conftest.py.  Every test is self-contained: it creates its own identities
and revisions so there is no ordering dependency.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.domain.engineering_library_types import (
    CoatingIdentity,
    CoatingRevisionDraft,
    EngineeringLibraryLifecycleStatus,
    EngineeringLibraryRevisionMetadata,
    EngineeringLibrarySourceClass,
    MaterialIdentity,
    MaterialPropertyBasis,
    MaterialPropertySet,
    MaterialRevisionDraft,
    StackLayerDraft,
    StackUpRevisionDraft,
    WeldPulseDraft,
    WeldPulseType,
    WeldScheduleRevisionDraft,
)
from app.repositories.engineering_library_repository import (
    AmbiguousCurrentRevisionError,
    CrossIdentitySupersessionError,
    EngineeringLibraryRepository,
)

# ---------------------------------------------------------------------------
# Minimal test fixtures
# ---------------------------------------------------------------------------

_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_ENGINE)


@pytest.fixture()
def session():
    with Session(_ENGINE) as s:
        yield s


@pytest.fixture()
def repo(session: Session) -> EngineeringLibraryRepository:
    return EngineeringLibraryRepository(session)


# ---------------------------------------------------------------------------
# Helpers to build minimal drafts
# ---------------------------------------------------------------------------

ACTOR = "user:1"
USER_ID = 1


def _mat_meta(revision_number: int = 1, supersedes: int | None = None) -> EngineeringLibraryRevisionMetadata:
    from app.application.engineering_library_service import (
        CANONICALIZATION_VERSION,
        HASH_ALGORITHM,
        SCHEMA_VERSION,
        SOFTWARE_VERSION,
    )
    return EngineeringLibraryRevisionMetadata(
        revision_number=revision_number,
        lifecycle_status=EngineeringLibraryLifecycleStatus.ACTIVE,
        source_class=EngineeringLibrarySourceClass.SOURCE_BACKED,
        supersedes_revision_id=supersedes,
        evidence_reference_ids=[],
        schema_version=SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        hash_algorithm=HASH_ALGORITHM,
        software_version=SOFTWARE_VERSION,
        created_by_actor_id=ACTOR,
        created_by_user_id=USER_ID,
    )


def _mat_draft(family: str = "Steel", grade: str = "DP600", revision_number: int = 1, supersedes: int | None = None) -> MaterialRevisionDraft:
    return MaterialRevisionDraft(
        identity=MaterialIdentity(material_id="MAT-TEST", family=family, grade=grade),
        notes="n/a",
        metadata=_mat_meta(revision_number, supersedes),
        properties=MaterialPropertySet(property_basis=MaterialPropertyBasis.REFERENCE_ONLY),
    )


def _coat_meta(revision_number: int = 1, supersedes: int | None = None) -> EngineeringLibraryRevisionMetadata:
    from app.application.engineering_library_service import (
        CANONICALIZATION_VERSION,
        HASH_ALGORITHM,
        SCHEMA_VERSION,
        SOFTWARE_VERSION,
    )
    return EngineeringLibraryRevisionMetadata(
        revision_number=revision_number,
        lifecycle_status=EngineeringLibraryLifecycleStatus.ACTIVE,
        source_class=EngineeringLibrarySourceClass.SOURCE_BACKED,
        supersedes_revision_id=supersedes,
        evidence_reference_ids=[],
        schema_version=SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        hash_algorithm=HASH_ALGORITHM,
        software_version=SOFTWARE_VERSION,
        created_by_actor_id=ACTOR,
        created_by_user_id=USER_ID,
    )


def _coat_draft(family: str = "Zinc", designation: str = "GI", revision_number: int = 1, supersedes: int | None = None) -> CoatingRevisionDraft:
    return CoatingRevisionDraft(
        identity=CoatingIdentity(coating_id="COAT-TEST", family=family, designation=designation),
        notes="n/a",
        metadata=_coat_meta(revision_number, supersedes),
    )


def _pulse_draft(seq: int = 1) -> WeldPulseDraft:
    return WeldPulseDraft(
        sequence=seq,
        pulse_type=WeldPulseType.WELD,
        current_ka=8.0,
        duration_cycles=12.0,
        force_kn=4.0,
    )


# ---------------------------------------------------------------------------
# Material tests
# ---------------------------------------------------------------------------


class TestMaterialRepository:
    def test_create_identity_and_revision(self, repo, session):
        identity = repo.create_material_identity(
            material_id="MAT-001",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        assert identity.id is not None
        assert identity.material_id == "MAT-001"

        draft = _mat_draft()
        rev = repo.add_material_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash="abc123",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        assert rev.id is not None
        assert rev.revision_number == 1
        assert rev.content_hash == "abc123"
        assert rev.family == "Steel"
        assert rev.grade == "DP600"

    def test_lookup_by_business_id(self, repo, session):
        repo.create_material_identity(
            material_id="MAT-BIZ-LOOKUP",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        found = repo.get_material_identity_by_business_id("MAT-BIZ-LOOKUP")
        assert found is not None
        assert found.material_id == "MAT-BIZ-LOOKUP"

        not_found = repo.get_material_identity_by_business_id("DOES-NOT-EXIST")
        assert not_found is None

    def test_list_revisions_ordered(self, repo, session):
        identity = repo.create_material_identity(
            material_id="MAT-MULTI-REV",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        rev1 = repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=1),
            content_hash="h1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=2, supersedes=rev1.id),
            content_hash="h2",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        revisions = repo.list_material_revisions(identity.id)
        assert len(revisions) == 2
        assert revisions[0].revision_number == 1
        assert revisions[1].revision_number == 2

    def test_resolve_current_single_active(self, repo, session):
        identity = repo.create_material_identity(
            material_id="MAT-CURRENT-SINGLE",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=1),
            content_hash="h1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        current = repo.resolve_current_material_revision(identity.id)
        assert current is not None
        assert current.revision_number == 1

    def test_resolve_current_none_when_no_revisions(self, repo, session):
        identity = repo.create_material_identity(
            material_id="MAT-CURRENT-NONE",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        current = repo.resolve_current_material_revision(identity.id)
        assert current is None

    def test_resolve_current_superseded_excluded(self, repo, session):
        identity = repo.create_material_identity(
            material_id="MAT-SUPERSEDED",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        rev1 = repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=1),
            content_hash="h1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=2, supersedes=rev1.id),
            content_hash="h2",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        current = repo.resolve_current_material_revision(identity.id)
        assert current is not None
        assert current.revision_number == 2

    def test_resolve_current_ambiguous_raises(self, repo, session):
        identity = repo.create_material_identity(
            material_id="MAT-AMBIGUOUS",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        # Two ACTIVE revisions, neither supersedes the other → ambiguous
        repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=1),
            content_hash="h1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        repo.add_material_revision(
            entity_id=identity.id,
            draft=_mat_draft(revision_number=2),
            content_hash="h2",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        with pytest.raises(AmbiguousCurrentRevisionError):
            repo.resolve_current_material_revision(identity.id)

    def test_cross_identity_supersession_rejected(self, repo, session):
        id_a = repo.create_material_identity(
            material_id="MAT-CROSS-A",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        id_b = repo.create_material_identity(
            material_id="MAT-CROSS-B",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        rev_a = repo.add_material_revision(
            entity_id=id_a.id,
            draft=_mat_draft(revision_number=1),
            content_hash="hA",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        # Try to supersede rev_a from identity B → must fail
        with pytest.raises(CrossIdentitySupersessionError):
            repo.add_material_revision(
                entity_id=id_b.id,
                draft=_mat_draft(revision_number=2, supersedes=rev_a.id),
                content_hash="hB",
                created_by_actor_id=ACTOR,
                created_by_user_id=USER_ID,
            )

    def test_list_identities(self, repo, session):
        before = len(repo.list_material_identities())
        repo.create_material_identity(
            material_id="MAT-LIST-1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        repo.create_material_identity(
            material_id="MAT-LIST-2",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        after = repo.list_material_identities()
        assert len(after) >= before + 2


# ---------------------------------------------------------------------------
# Coating tests (minimal — resolver + cross-identity already covered above)
# ---------------------------------------------------------------------------


class TestCoatingRepository:
    def test_create_and_retrieve(self, repo, session):
        identity = repo.create_coating_identity(
            coating_id="COAT-001",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        rev = repo.add_coating_revision(
            entity_id=identity.id,
            draft=_coat_draft(),
            content_hash="hC1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        assert rev.family == "Zinc"
        assert rev.designation == "GI"

    def test_resolve_current_coating(self, repo, session):
        identity = repo.create_coating_identity(
            coating_id="COAT-CURRENT",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        repo.add_coating_revision(
            entity_id=identity.id,
            draft=_coat_draft(revision_number=1),
            content_hash="hC1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        current = repo.resolve_current_coating_revision(identity.id)
        assert current is not None


# ---------------------------------------------------------------------------
# StackUp tests — layer atomicity + exact revision pinning
# ---------------------------------------------------------------------------


class TestStackUpRepository:
    def _setup_material_revision(self, repo, session, mid: str = "MAT-ST") -> int:
        ident = repo.create_material_identity(
            material_id=mid,
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        rev = repo.add_material_revision(
            entity_id=ident.id,
            draft=_mat_draft(),
            content_hash="hM",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        return rev.id

    def test_create_stackup_with_layers(self, repo, session):
        mat_rev_id = self._setup_material_revision(repo, session, "MAT-SU-CREATE")
        identity = repo.create_stack_up_identity(
            stack_id="STACK-001",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        layers = [
            StackLayerDraft(sequence=1, material_revision_id=mat_rev_id, thickness_mm=1.2),
            StackLayerDraft(sequence=2, material_revision_id=mat_rev_id, thickness_mm=1.5),
        ]
        draft = StackUpRevisionDraft(
            stack_id="STACK-001",
            adhesive_present=False,
            layers=layers,
            metadata=_mat_meta(1),
        )
        rev = repo.add_stack_up_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash="hS1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        assert rev.id is not None
        layer_rows = repo.list_stack_layers(rev.id)
        assert len(layer_rows) == 2
        assert layer_rows[0].sequence == 1
        assert layer_rows[1].sequence == 2

    def test_invalid_material_revision_raises(self, repo, session):
        identity = repo.create_stack_up_identity(
            stack_id="STACK-INVALID-MAT",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        layers = [
            StackLayerDraft(sequence=1, material_revision_id=999999, thickness_mm=1.2),
            StackLayerDraft(sequence=2, material_revision_id=999999, thickness_mm=1.5),
        ]
        draft = StackUpRevisionDraft(
            stack_id="STACK-INVALID-MAT",
            adhesive_present=False,
            layers=layers,
            metadata=_mat_meta(1),
        )
        with pytest.raises(ValueError, match="material revision"):
            repo.add_stack_up_revision(
                entity_id=identity.id,
                draft=draft,
                content_hash="hSX",
                created_by_actor_id=ACTOR,
                created_by_user_id=USER_ID,
            )


# ---------------------------------------------------------------------------
# WeldSchedule tests — pulse atomicity
# ---------------------------------------------------------------------------


class TestWeldScheduleRepository:
    def test_create_schedule_with_pulses(self, repo, session):
        identity = repo.create_weld_schedule_identity(
            schedule_id="SCHED-001",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        pulses = [
            _pulse_draft(seq=1),
            WeldPulseDraft(sequence=2, pulse_type=WeldPulseType.COOL, current_ka=None, duration_cycles=4.0, force_kn=4.0),
        ]
        draft = WeldScheduleRevisionDraft(
            schedule_id="SCHED-001",
            squeeze_cycles=10.0,
            hold_cycles=5.0,
            pulses=pulses,
            metadata=_mat_meta(1),
            process_metadata={},
        )
        rev, pulse_rows = repo.add_weld_schedule_revision(
            entity_id=identity.id,
            draft=draft,
            content_hash="hSCH1",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        assert rev.id is not None
        assert len(pulse_rows) == 2
        listed = repo.list_weld_pulses(rev.id)
        assert len(listed) == 2
        assert listed[0].sequence_number == 1
        assert listed[1].sequence_number == 2

    def test_ambiguous_resolver_for_schedule(self, repo, session):
        identity = repo.create_weld_schedule_identity(
            schedule_id="SCHED-AMB",
            created_by_actor_id=ACTOR,
            created_by_user_id=USER_ID,
        )
        session.flush()
        pulses = [_pulse_draft(seq=1)]
        for rev_num in (1, 2):
            draft = WeldScheduleRevisionDraft(
                schedule_id="SCHED-AMB",
                squeeze_cycles=10.0,
                hold_cycles=5.0,
                pulses=pulses,
                metadata=_mat_meta(rev_num),
                process_metadata={},
            )
            repo.add_weld_schedule_revision(
                entity_id=identity.id,
                draft=draft,
                content_hash=f"hSCH{rev_num}",
                created_by_actor_id=ACTOR,
                created_by_user_id=USER_ID,
            )
            session.flush()
        with pytest.raises(AmbiguousCurrentRevisionError):
            repo.resolve_current_weld_schedule_revision(identity.id)
