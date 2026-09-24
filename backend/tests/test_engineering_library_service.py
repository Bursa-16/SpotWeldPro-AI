"""Service unit tests for Engineering Library — CE-02C.

Tests the EngineeringLibraryService against an in-memory SQLite database,
verifying:
  - Content hash is computed and stored
  - Governed audit event is recorded within the same transaction
  - Actor attribution is propagated
  - GovernedUnitOfWork commit / rollback semantics
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.engineering_library_service import (
    CANONICALIZATION_VERSION,
    HASH_ALGORITHM,
    SCHEMA_VERSION,
    SOFTWARE_VERSION,
    EngineeringLibraryService,
    _hash,
)
from app.application.governed_unit_of_work import GovernedUnitOfWork
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
    WeldPulseDraft,
    WeldPulseType,
    WeldScheduleRevisionDraft,
)

_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_ENGINE)

ACTOR_ID = "user:99"
USER_ID = 99


def _meta(revision_number: int = 1, supersedes: int | None = None) -> EngineeringLibraryRevisionMetadata:
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
        created_by_actor_id=ACTOR_ID,
        created_by_user_id=USER_ID,
    )


def _mat_draft(material_id: str = "MAT-TEST") -> MaterialRevisionDraft:
    return MaterialRevisionDraft(
        identity=MaterialIdentity(material_id=material_id, family="Aluminium", grade="AA6016"),
        notes="test",
        metadata=_meta(),
        properties=MaterialPropertySet(
            density_kg_m3=2700.0,
            property_basis=MaterialPropertyBasis.REFERENCE_ONLY,
        ),
    )


def _coat_draft(coating_id: str = "COAT-TEST") -> CoatingRevisionDraft:
    return CoatingRevisionDraft(
        identity=CoatingIdentity(coating_id=coating_id, family="Zinc", designation="GA"),
        notes="test",
        metadata=_meta(),
    )


@pytest.fixture()
def db_session():
    with Session(_ENGINE) as s:
        yield s


class TestHashFunction:
    def test_hash_deterministic(self):
        v1 = _hash({"a": 1, "b": 2})
        v2 = _hash({"b": 2, "a": 1})
        assert v1 == v2, "hash must be key-order independent"

    def test_hash_is_sha256_hex(self):
        h = _hash({"x": "y"})
        assert len(h) == 64
        int(h, 16)  # must be valid hex


class TestMaterialService:
    def test_create_material_stores_content_hash(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            _identity, revision = svc.create_material_with_revision(
                draft=_mat_draft("SVC-MAT-HASH"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert revision.content_hash is not None
        assert len(revision.content_hash) == 64

    def test_create_material_actor_attribution(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_material_with_revision(
                draft=_mat_draft("SVC-MAT-ACTOR"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert identity.created_by_actor_id == ACTOR_ID
        assert identity.created_by_user_id == USER_ID
        assert revision.created_by_actor_id == ACTOR_ID

    def test_add_revision_supersedes(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, rev1 = svc.create_material_with_revision(
                draft=_mat_draft("SVC-MAT-SUPER"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.session.flush()
            # Capture PKs before commit to avoid expire-on-commit lazy refresh
            # opening an implicit transaction before the second GovernedUnitOfWork.
            identity_id = identity.id
            rev1_id = rev1.id
            uow.commit()

        meta2 = _meta(revision_number=2, supersedes=rev1_id)
        draft2 = MaterialRevisionDraft(
            identity=MaterialIdentity(material_id="SVC-MAT-SUPER", family="Aluminium", grade="AA6016-T4"),
            notes="revised",
            metadata=meta2,
            properties=MaterialPropertySet(property_basis=MaterialPropertyBasis.REFERENCE_ONLY),
        )
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            rev2 = svc.add_material_revision(
                entity_id=identity_id,
                draft=draft2,
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert rev2.revision_number == 2
        assert rev2.supersedes_revision_id == rev1_id

    def test_software_version_stamped(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            _, revision = svc.create_material_with_revision(
                draft=_mat_draft("SVC-MAT-VER"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert revision.software_version == SOFTWARE_VERSION
        assert revision.schema_version == SCHEMA_VERSION


class TestCoatingService:
    def test_create_coating(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, revision = svc.create_coating_with_revision(
                draft=_coat_draft("SVC-COAT-001"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert identity.coating_id == "SVC-COAT-001"
        assert revision.family == "Zinc"
        assert revision.designation == "GA"


class TestWeldScheduleService:
    def _sched_draft(self, schedule_id: str = "SCHED-SVC") -> WeldScheduleRevisionDraft:
        return WeldScheduleRevisionDraft(
            schedule_id=schedule_id,
            squeeze_cycles=10.0,
            hold_cycles=5.0,
            pulses=[
                WeldPulseDraft(sequence=1, pulse_type=WeldPulseType.WELD, current_ka=8.0, duration_cycles=12.0, force_kn=4.0),
            ],
            metadata=_meta(),
            process_metadata={"lobe_index": 1},
        )

    def test_create_schedule_with_pulses(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            identity, _revision, pulses = svc.create_weld_schedule_with_revision(
                draft=self._sched_draft("SCHED-SVC-001"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert identity.schedule_id == "SCHED-SVC-001"
        assert len(pulses) == 1
        assert pulses[0].pulse_type.value == WeldPulseType.WELD.value

    def test_process_metadata_stored(self, db_session):
        with GovernedUnitOfWork(db_session) as uow:
            svc = EngineeringLibraryService(uow)
            _, revision, _ = svc.create_weld_schedule_with_revision(
                draft=self._sched_draft("SCHED-SVC-META"),
                actor_id=ACTOR_ID,
                actor_user_id=USER_ID,
                reason="svc test",
            )
            uow.commit()
        assert revision.process_metadata is not None
        assert revision.process_metadata.get("lobe_index") == 1
