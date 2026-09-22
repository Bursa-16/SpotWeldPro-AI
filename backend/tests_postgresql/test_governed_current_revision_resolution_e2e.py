"""Real-PostgreSQL governed current-revision applicability resolution e2e (Phase 6B2B).

The tests drive the real governed Registry commands to create revisions in
concrete lifecycle states and then assert the public read-only resolver
``RuleRegistryService.resolve_current_applicable_revision`` projects exactly
one CURRENT authoritative revision per rule, while historical Evaluation,
MRC, and DWP records stay pinned to the revision they were created against.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.digital_weld_passport_service import (
    DigitalWeldPassportRevisionDraft,
    DigitalWeldPassportService,
)
from app.application.governed_unit_of_work import GovernedUnitOfWork
from app.application.machine_readiness_service import (
    MachineReadinessPersistenceDraft,
    MachineReadinessService,
)
from app.application.rule_evaluation_service import (
    RuleEvaluationPersistenceDraft,
    RuleEvaluationService,
)
from app.application.rule_registry_service import (
    GovernedAuditMetadata,
    RuleRegistryService,
)
from app.domain.governance_types import (
    ContentVersionMetadata,
    EvidenceClass,
    RuleLifecycleStatus,
)
from app.domain.idempotency_types import CanonicalRequestHash, CommandIdentity
from app.domain.readiness import (
    CheckCondition,
    GovernedMachineReadinessCheck,
    GovernedRuleEvaluationSnapshot,
    MachineReadinessCheckTrace,
    MachineReadinessResult,
    ReadinessState,
)
from app.domain.rule_applicability import (
    ApplicabilityResolutionOutcome,
    GovernedApplicabilityCandidate,
    GovernedApplicabilityContext,
    resolve_governed_applicability,
)
from app.domain.rule_evaluation import (
    Observation,
    RuleComparison,
    RuleComparisonOutcome,
    RuleRequirement,
    compare_rule,
)
from app.domain.rule_registry_types import (
    EvidenceReferenceDraft,
    MissingHandling,
    RuleCategory,
    RuleOperator,
    SafeDefault,
)
from app.domain.unit_policy import UnitPolicyContext
from app.domain.verification_types import (
    EvidenceVerificationAuthoritySnapshot,
    EvidenceVerificationDecisionDraft,
    EvidenceVerificationDelegationDraft,
    VerificationCapability,
    VerificationDecisionOutcome,
    VerificationDelegationStatus,
    VerificationScopeSnapshot,
)
from app.models.digital_weld_passport import DigitalWeldPassportRevision
from app.models.entities import User
from app.models.machine_readiness import MachineReadinessAssessmentRevision
from app.models.rule_evaluation import RuleEvaluation
from app.models.rule_registry import (
    EngineeringRuleRevision,
    RuleLifecycleEvent,
    RuleLifecycleEventType,
)
from app.models.verification import EvidenceVerificationDecision
from app.repositories.evidence_verification_repository import (
    EvidenceVerificationRepository,
)

BASE_TIME = datetime(2039, 1, 1, 10, 0, tzinfo=timezone.utc)
EVALUATION_UNIT = "synthetic_unit"


ACTORS = {
    "submitter": {
        "email": "phase6b2b-submitter@example.com",
        "name": "Phase 6B2B Submitter",
        "role": "Engineer",
    },
    "verifier": {
        "email": "phase6b2b-verifier@example.com",
        "name": "Phase 6B2B Verifier",
        "role": "Verifier",
    },
    "approver": {
        "email": "phase6b2b-approver@example.com",
        "name": "Phase 6B2B Approver",
        "role": "Approver",
    },
    "executor": {
        "email": "phase6b2b-executor@example.com",
        "name": "Phase 6B2B Executor",
        "role": "Governor",
    },
}


def _digest(data: object) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _version_metadata(label: str) -> ContentVersionMetadata:
    return ContentVersionMetadata(
        schema_version="phase-6b2b-content-schema-v1",
        canonicalization_version="phase-6b2b-canonical-v1",
        hash_algorithm="sha256",
        content_hash=_digest({"label": label}),
        software_version="phase-6b2b-test",
    )


def _identity(namespace: str, scope: str, key: str) -> CommandIdentity:
    return CommandIdentity(
        command_namespace=namespace, command_scope=scope, idempotency_key=key
    )


def _request_hash(key: str) -> CanonicalRequestHash:
    return CanonicalRequestHash(
        value=_digest({"key": key}),
        hash_algorithm="sha256",
        canonicalization_version="phase-6b2b-canonical-v1",
    )


def _audit(
    event_id: str,
    actor: dict,
    actor_user_id: int,
    idempotency_key: str,
    reason: str,
    project: str,
) -> GovernedAuditMetadata:
    return GovernedAuditMetadata(
        event_id=event_id,
        actor_id=actor["email"],
        actor_type="user",
        actor_role=actor["role"],
        reason=reason,
        authority_scope=VerificationScopeSnapshot(project=project).as_dict(),
        correlation_id="phase-6b2b",
        schema_version="phase-6b2b-audit-v1",
        canonicalization_version="phase-6b2b-canonical-v1",
        hash_algorithm="sha256",
        software_version="phase-6b2b-test",
        created_at=BASE_TIME,
        actor_user_id=actor_user_id,
        idempotency_key=idempotency_key,
        detail={},
    )


def _seed_users(session: Session) -> dict[str, int]:
    """Materialize (or reuse) the fixed Phase 6B2B actors, failing closed on drift."""
    result: dict[str, int] = {}
    for key, actor in ACTORS.items():
        email = str(actor["email"])
        expected_full_name = str(actor["name"])
        expected_role = str(actor["role"])
        existing = session.scalar(select(User).where(User.email == email))
        if existing is None:
            user = User(
                email=email,
                full_name=expected_full_name,
                password_hash=f"hash-{key}",
                role=expected_role,
            )
            session.add(user)
            session.flush()
        else:
            if existing.full_name != expected_full_name:
                raise RuntimeError(
                    f"Phase 6B2B ACTORS drift: user {email!r} full_name mismatch"
                )
            if existing.role != expected_role:
                raise RuntimeError(
                    f"Phase 6B2B ACTORS drift: user {email!r} role mismatch"
                )
            if not existing.is_active:
                raise RuntimeError(f"Phase 6B2B ACTORS drift: user {email!r} inactive")
            user = existing
        result[key] = user.id
    return result


def _create_evidence(
    session: Session,
    evidence_reference,
    verifier_uid: int,
    verifier_role: str,
    grantor_uid: int,
    label: str,
    project: str,
) -> None:
    delegation_id = f"phase-6b2b-delegation-{label}"
    verification_id = f"phase-6b2b-verification-{label}"
    repo = EvidenceVerificationRepository(session)
    scope = VerificationScopeSnapshot(project=project)

    delegation = repo.create_delegation_revision(
        draft=EvidenceVerificationDelegationDraft(
            delegation_id=delegation_id,
            revision_number=1,
            verifier_user_id=verifier_uid,
            granted_by_user_id=grantor_uid,
            scope_snapshot=scope,
            effective_from=BASE_TIME - timedelta(days=1),
            expires_at=None,
            revoked_by_user_id=None,
            revoked_at=None,
            revoked_reason=None,
            status=VerificationDelegationStatus.ACTIVE,
            capability=VerificationCapability.EVIDENCE_VERIFICATION,
            created_by_user_id=grantor_uid,
            created_by_actor_id=str(ACTORS["approver"]["email"]),
            schema_version="phase-6b2b-verification-v1",
            canonicalization_version="phase-6b2b-canonical-v1",
            hash_algorithm="sha256",
            content_hash=_digest(
                {"delegation_id": delegation_id, "verifier_user_id": verifier_uid}
            ),
            software_version="phase-6b2b-test",
        )
    )

    authority = EvidenceVerificationAuthoritySnapshot(
        verifier_user_id=verifier_uid,
        verifier_role_snapshot=verifier_role,
        capability=VerificationCapability.EVIDENCE_VERIFICATION,
        resource_scope=scope,
        delegation_id=delegation.delegation_id,
        delegation_revision_number=delegation.revision_number,
        delegation_status=delegation.status,
        delegation_effective_from=delegation.effective_from,
        delegation_expires_at=delegation.expires_at,
        delegation_revoked_at=delegation.revoked_at,
        policy_identifier="SDS-115",
        policy_version="0.1 Draft",
        decision_at=BASE_TIME,
        correlation_id="phase-6b2b-verification",
        schema_version="evidence-verification-authority-snapshot-v1",
        canonicalization_version="phase-6b2b-canonical-v1",
        hash_algorithm="sha256",
        content_hash=_digest(
            {
                "verification_id": verification_id,
                "delegation_id": delegation.delegation_id,
            }
        ),
        software_version="phase-6b2b-test",
    )

    repo.create_verification_decision(
        draft=EvidenceVerificationDecisionDraft(
            verification_id=verification_id,
            revision_number=1,
            evidence_reference_id=evidence_reference.id,
            evidence_verification_delegation_id=delegation.id,
            verifier_user_id=verifier_uid,
            authority_snapshot=authority.as_dict(),
            decision_reason="Verified Phase 6B2B evidence",
            decided_at=BASE_TIME,
            policy_identifier="SDS-115",
            policy_version="0.1 Draft",
            correlation_id="phase-6b2b-verification",
            supersedes_verification_decision_id=None,
            created_by_user_id=verifier_uid,
            created_by_actor_id=str(ACTORS["verifier"]["email"]),
            schema_version="phase-6b2b-verification-v1",
            canonicalization_version="phase-6b2b-canonical-v1",
            hash_algorithm="sha256",
            content_hash=_digest(
                {
                    "verification_id": verification_id,
                    "evidence_reference_id": evidence_reference.id,
                }
            ),
            software_version="phase-6b2b-test",
        )
    )
def _create_identity(
    session: Session,
    *,
    rule_id: str,
    user_ids: dict[str, int],
    project: str,
) -> None:
    with GovernedUnitOfWork(session) as unit_of_work:
        registry = RuleRegistryService(unit_of_work)
        registry.create_identity(
            rule_id=rule_id,
            audit=_audit(
                f"{rule_id}-identity",
                ACTORS["submitter"],
                user_ids["submitter"],
                f"{rule_id}-identity",
                f"Create Phase 6B2B identity {rule_id}",
                project,
            ),
        )
        unit_of_work.commit()


def _create_revision(
    session: Session,
    *,
    rule_id: str,
    revision: str,
    evidence_id: str,
    label: str,
    user_ids: dict[str, int],
    project: str,
) -> int:
    """Create one SOURCE_BACKED DRAFT revision row and verify its evidence."""
    with GovernedUnitOfWork(session) as unit_of_work:
        registry = RuleRegistryService(unit_of_work)
        created = registry.create_draft_revision(
            rule_id=rule_id,
            revision=revision,
            name=f"Phase 6B2B {label}",
            evidence_class=EvidenceClass.SOURCE_BACKED,
            category=RuleCategory.OTHER,
            parameter="governed_input_present",
            safe_default=SafeDefault.UNRESOLVED,
            missing_handling=MissingHandling.DATA_INSUFFICIENT,
            reason_for_change=f"Phase 6B2B {label} baseline",
            version_metadata=_version_metadata(f"{rule_id}:{revision}"),
            audit=_audit(
                f"{rule_id}-{revision}-audit",
                ACTORS["submitter"],
                user_ids["submitter"],
                f"{rule_id}-{revision}",
                f"Create {rule_id} {revision}",
                project,
            ),
            evidence_references=(
                EvidenceReferenceDraft(
                    evidence_id=evidence_id,
                    evidence_revision="1",
                    evidence_class=EvidenceClass.UNRESOLVED,
                    lifecycle_status=RuleLifecycleStatus.DRAFT,
                    created_by_actor_id=ACTORS["submitter"]["email"],
                    created_by_user_id=user_ids["submitter"],
                    reference_uri=f"urn:spotweld:test:{evidence_id}",
                ),
            ),
            allow_source_backed=True,
        )
        _create_evidence(
            session,
            created.evidence_references[0],
            user_ids["verifier"],
            ACTORS["verifier"]["role"],
            user_ids["approver"],
            f"{rule_id}-{revision}",
            project,
        )
        created_id = created.id
        unit_of_work.commit()
        return created_id
def _transition(
    session: Session,
    *,
    rule_id: str,
    revision: str,
    event_type: RuleLifecycleEventType,
    key: str,
    project: str,
    user_ids: dict[str, int],
    effective_from: datetime,
    expires_at: datetime | None,
    completed_at: datetime,
) -> None:
    namespace = (
        RuleRegistryService.ENABLEMENT_COMMAND_NAMESPACE
        if event_type is RuleLifecycleEventType.ENABLE
        else RuleRegistryService.ACTIVATION_COMMAND_NAMESPACE
    )
    with GovernedUnitOfWork(session) as unit_of_work:
        registry = RuleRegistryService(unit_of_work)
        method = (
            registry.enable_source_backed
            if event_type is RuleLifecycleEventType.ENABLE
            else registry.activate_source_backed
        )
        result = method(
            rule_id=rule_id,
            source_revision=revision,
            receipt_id=f"{rule_id}-{event_type.value.lower()}-receipt-{key}",
            command_identity=_identity(namespace, rule_id, key),
            request_hash=_request_hash(key),
            audit=_audit(
                f"{rule_id}-{event_type.value.lower()}-audit-{key}",
                ACTORS["executor"],
                user_ids["executor"],
                key,
                f"{event_type.value} {rule_id} {revision}",
                project,
            ),
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
        )
        assert result.result_type == "engineering_rule_lifecycle_event"
        unit_of_work.commit()
def _supersession_basis_hash(
    session: Session,
    *,
    rule_id: str,
    incumbent_id: int,
    incumbent_revision: str,
    candidate: EngineeringRuleRevision,
    replacement_revision: str,
    project: str,
) -> str:
    ordered_references = sorted(
        candidate.evidence_references,
        key=lambda reference: (
            reference.evidence_id,
            reference.evidence_revision,
            reference.id,
        ),
    )
    evidence_pins = []
    for reference in ordered_references:
        decision = session.scalar(
            select(EvidenceVerificationDecision)
            .where(
                EvidenceVerificationDecision.evidence_reference_id == reference.id,
                EvidenceVerificationDecision.decision_outcome
                == VerificationDecisionOutcome.VERIFIED,
            )
            .order_by(
                EvidenceVerificationDecision.revision_number.desc(),
                EvidenceVerificationDecision.id.desc(),
            )
        )
        assert decision is not None
        evidence_pins.append(
            {
                "evidence_reference_id": reference.id,
                "evidence_id": reference.evidence_id,
                "evidence_revision": reference.evidence_revision,
                "verification_decision_id": decision.id,
                "verification_revision_number": decision.revision_number,
                "verifier_user_id": decision.verifier_user_id,
            }
        )
    return _digest(
        {
            "rule_id": rule_id,
            "incumbent_revision": incumbent_revision,
            "incumbent_revision_id": incumbent_id,
            "replacement_candidate_revision": candidate.revision,
            "replacement_candidate_revision_id": candidate.id,
            "replacement_revision": replacement_revision,
            "scope_snapshot": VerificationScopeSnapshot(project=project).as_dict(),
            "evidence_pins": evidence_pins,
        }
    )


def _supersede(
    session: Session,
    *,
    rule_id: str,
    incumbent_revision: str,
    replacement_candidate_revision: str,
    replacement_revision: str,
    key: str,
    project: str,
    user_ids: dict[str, int],
    effective_from: datetime,
    expires_at: datetime | None,
) -> None:
    with session:
        incumbent = session.scalar(
            select(EngineeringRuleRevision).where(
                EngineeringRuleRevision.engineering_rule.has(rule_id=rule_id),
                EngineeringRuleRevision.revision == incumbent_revision,
            )
        )
        assert incumbent is not None
        candidate = session.scalar(
            select(EngineeringRuleRevision).where(
                EngineeringRuleRevision.engineering_rule.has(rule_id=rule_id),
                EngineeringRuleRevision.revision == replacement_candidate_revision,
            )
        )
        assert candidate is not None
        basis_content_hash = _supersession_basis_hash(
            session,
            rule_id=rule_id,
            incumbent_id=incumbent.id,
            incumbent_revision=incumbent_revision,
            candidate=candidate,
            replacement_revision=replacement_revision,
            project=project,
        )
    version_metadata = ContentVersionMetadata(
        schema_version="phase-6b2b-content-schema-v1",
        canonicalization_version="phase-6b2b-canonical-v1",
        hash_algorithm="sha256",
        content_hash=basis_content_hash,
        software_version="phase-6b2b-test",
    )
    with GovernedUnitOfWork(session) as unit_of_work:
        registry = RuleRegistryService(unit_of_work)
        result = registry.supersede_active_source_backed(
            rule_id=rule_id,
            incumbent_revision=incumbent_revision,
            replacement_candidate_revision=replacement_candidate_revision,
            replacement_revision=replacement_revision,
            version_metadata=version_metadata,
            receipt_id=f"{rule_id}-supersede-receipt-{key}",
            command_identity=_identity(
                RuleRegistryService.SUPERSESSION_COMMAND_NAMESPACE, rule_id, key
            ),
            request_hash=_request_hash(key),
            audit=_audit(
                f"{rule_id}-supersede-audit-{key}",
                ACTORS["executor"],
                user_ids["executor"],
                key,
                f"Supersede {rule_id}",
                project,
            ),
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=effective_from + timedelta(seconds=1),
        )
        assert result.result_type == "engineering_rule_lifecycle_event"
        unit_of_work.commit()
def _resolve_current(
    session: Session,
    *,
    rule_id: str,
    project: str,
    as_of: datetime,
) -> EngineeringRuleRevision:
    with GovernedUnitOfWork(session) as unit_of_work:
        registry = RuleRegistryService(unit_of_work)
        resolved = registry.resolve_current_applicable_revision(
            rule_id=rule_id,
            scope=GovernedApplicabilityContext(project=project),
            as_of=as_of,
        )

        # Detach the fully loaded read result before rolling back the
        # read-only transaction. This prevents later scalar access from
        # implicitly beginning a new transaction on the caller's session.
        session.expunge(resolved)
        unit_of_work.rollback()
        return resolved


def _active_rev1(
    session: Session,
    *,
    rule_id: str,
    project: str,
    user_ids: dict[str, int],
    enable_effective: datetime,
    activate_effective: datetime,
) -> int:
    _create_identity(session, rule_id=rule_id, user_ids=user_ids, project=project)
    rev1_id = _create_revision(
        session,
        rule_id=rule_id,
        revision="1.0",
        evidence_id=f"{rule_id}_EVIDENCE_1",
        label="Rev1",
        user_ids=user_ids,
        project=project,
    )
    _transition(
        session,
        rule_id=rule_id,
        revision="1.0",
        event_type=RuleLifecycleEventType.ENABLE,
        key=f"{rule_id}-enable-rev1",
        project=project,
        user_ids=user_ids,
        effective_from=enable_effective,
        expires_at=None,
        completed_at=enable_effective + timedelta(seconds=1),
    )
    _transition(
        session,
        rule_id=rule_id,
        revision="1.0",
        event_type=RuleLifecycleEventType.ACTIVATE,
        key=f"{rule_id}-activate-rev1",
        project=project,
        user_ids=user_ids,
        effective_from=activate_effective,
        expires_at=None,
        completed_at=activate_effective + timedelta(seconds=1),
    )
    return rev1_id
def test_active_rev1_resolves_rev1_on_postgresql(postgresql_engine) -> None:
    rule_id = "PHASE_6B2B_ACTIVE_REV1"
    project = "phase-6b2b-project_active"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        rev1_id = _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=BASE_TIME + timedelta(minutes=10),
        )
        assert resolved.id == rev1_id
        assert resolved.revision == "1.0"


def test_draft_rev2_does_not_displace_rev1_on_postgresql(postgresql_engine) -> None:
    rule_id = "PHASE_6B2B_DRAFT_REV2"
    project = "phase-6b2b-project_draft"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        rev1_id = _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )
        _create_revision(
            session,
            rule_id=rule_id,
            revision="2.0",
            evidence_id=f"{rule_id}_EVIDENCE_2",
            label="Rev2 draft",
            user_ids=user_ids,
            project=project,
        )
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=BASE_TIME + timedelta(minutes=10),
        )
        assert resolved.id == rev1_id
        assert resolved.revision == "1.0"


def test_enabled_rev2_does_not_displace_rev1_on_postgresql(postgresql_engine) -> None:
    rule_id = "PHASE_6B2B_ENABLED_REV2"
    project = "phase-6b2b-project_enabled"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        rev1_id = _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )
        _create_revision(
            session,
            rule_id=rule_id,
            revision="2.0",
            evidence_id=f"{rule_id}_EVIDENCE_2",
            label="Rev2 enabled candidate",
            user_ids=user_ids,
            project=project,
        )
        _transition(
            session,
            rule_id=rule_id,
            revision="2.0",
            event_type=RuleLifecycleEventType.ENABLE,
            key=f"{rule_id}-enable-rev2",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=3),
            expires_at=None,
            completed_at=BASE_TIME + timedelta(minutes=3, seconds=1),
        )
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=BASE_TIME + timedelta(minutes=10),
        )
        assert resolved.id == rev1_id
        assert resolved.revision == "1.0"


def test_superseding_active_rev2_resolves_and_pins_reference_on_postgresql(
    postgresql_engine,
) -> None:
    rule_id = "PHASE_6B2B_SUPERSEDING_REV2"
    project = "phase-6b2b-project_superseding"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        rev1_id = _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )
        _create_revision(
            session,
            rule_id=rule_id,
            revision="2.0-draft",
            evidence_id=f"{rule_id}_EVIDENCE_2",
            label="Rev2 replacement candidate",
            user_ids=user_ids,
            project=project,
        )
        _supersede(
            session,
            rule_id=rule_id,
            incumbent_revision="1.0",
            replacement_candidate_revision="2.0-draft",
            replacement_revision="2.0",
            key=f"{rule_id}-supersede",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=4),
            expires_at=None,
        )
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=BASE_TIME + timedelta(minutes=10),
        )
        assert resolved.revision == "2.0"
        with session:
            replacement = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=rule_id),
                    EngineeringRuleRevision.revision == "2.0",
                )
            )
            assert replacement is not None
            assert replacement.supersedes_revision_id == rev1_id
def test_effective_from_gates_applicability_on_postgresql(postgresql_engine) -> None:
    rule_id = "PHASE_6B2B_EFFECTIVE_FROM"
    project = "phase-6b2b-project_effective"
    effective = BASE_TIME + timedelta(minutes=5)
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=effective,
        )
        # as_of just before effective_from -> not yet applicable
        with pytest.raises(ValueError, match="no applicable governed revision"):
            _resolve_current(
                session,
                rule_id=rule_id,
                project=project,
                as_of=effective - timedelta(seconds=1),
            )
        # as_of == effective_from boundary -> applicable
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=effective,
        )
        assert resolved.revision == "1.0"


def test_expires_at_stops_applicability_on_postgresql(postgresql_engine) -> None:
    rule_id = "PHASE_6B2B_EXPIRES_AT"
    project = "phase-6b2b-project_expires"
    expires = BASE_TIME + timedelta(minutes=6)
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        _create_identity(session, rule_id=rule_id, user_ids=user_ids, project=project)
        _create_revision(
            session,
            rule_id=rule_id,
            revision="1.0",
            evidence_id=f"{rule_id}_EVIDENCE_1",
            label="Rev1",
            user_ids=user_ids,
            project=project,
        )
        _transition(
            session,
            rule_id=rule_id,
            revision="1.0",
            event_type=RuleLifecycleEventType.ENABLE,
            key=f"{rule_id}-enable-rev1",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=1),
            expires_at=None,
            completed_at=BASE_TIME + timedelta(minutes=1, seconds=1),
        )
        _transition(
            session,
            rule_id=rule_id,
            revision="1.0",
            event_type=RuleLifecycleEventType.ACTIVATE,
            key=f"{rule_id}-activate-rev1",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=2),
            expires_at=expires,
            completed_at=BASE_TIME + timedelta(minutes=2, seconds=1),
        )
        # before expiry -> resolves
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=BASE_TIME + timedelta(minutes=3),
        )
        assert resolved.revision == "1.0"
        # live semantics: at expires_at the revision is already expired
        # (decision_time >= expires_at is ineligible)
        with pytest.raises(ValueError, match="no applicable governed revision"):
            _resolve_current(
                session,
                rule_id=rule_id,
                project=project,
                as_of=expires,
            )
        with pytest.raises(ValueError, match="no applicable governed revision"):
            _resolve_current(
                session,
                rule_id=rule_id,
                project=project,
                as_of=expires + timedelta(minutes=1),
            )


def test_authority_scope_mismatch_does_not_resolve_on_postgresql(
    postgresql_engine,
) -> None:
    rule_id = "PHASE_6B2B_SCOPE_MISMATCH"
    project_alpha = "phase-6b2b-project_alpha"
    project_omega = "phase-6b2b-project_omega"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        _active_rev1(
            session,
            rule_id=rule_id,
            project=project_alpha,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )
        with pytest.raises(ValueError, match="no applicable governed revision"):
            _resolve_current(
                session,
                rule_id=rule_id,
                project=project_omega,
                as_of=BASE_TIME + timedelta(minutes=10),
            )
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project_alpha,
            as_of=BASE_TIME + timedelta(minutes=10),
        )
        assert resolved.revision == "1.0"


def test_no_applicable_revision_follows_error_convention_on_postgresql(
    postgresql_engine,
) -> None:
    rule_id = "PHASE_6B2B_NO_APPLICABLE"
    project = "phase-6b2b-project_no_applicable"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        _create_identity(session, rule_id=rule_id, user_ids=user_ids, project=project)
        _create_revision(
            session,
            rule_id=rule_id,
            revision="1.0",
            evidence_id=f"{rule_id}_EVIDENCE_1",
            label="Rev1",
            user_ids=user_ids,
            project=project,
        )
        with pytest.raises(ValueError, match="no applicable governed revision"):
            _resolve_current(
                session,
                rule_id=rule_id,
                project=project,
                as_of=BASE_TIME + timedelta(minutes=10),
            )
def test_ambiguous_applicable_state_never_selects_silently_on_postgresql(
    postgresql_engine,
) -> None:
    rule_id = "PHASE_6B2B_AMBIGUITY"
    project = "phase-6b2b-project_ambiguity"
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )
        _create_revision(
            session,
            rule_id=rule_id,
            revision="2.0",
            evidence_id=f"{rule_id}_EVIDENCE_2",
            label="Rev2 independently activated",
            user_ids=user_ids,
            project=project,
        )
        _transition(
            session,
            rule_id=rule_id,
            revision="2.0",
            event_type=RuleLifecycleEventType.ENABLE,
            key=f"{rule_id}-enable-rev2",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=3),
            expires_at=None,
            completed_at=BASE_TIME + timedelta(minutes=3, seconds=1),
        )
        _transition(
            session,
            rule_id=rule_id,
            revision="2.0",
            event_type=RuleLifecycleEventType.ACTIVATE,
            key=f"{rule_id}-activate-rev2",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=4),
            expires_at=None,
            completed_at=BASE_TIME + timedelta(minutes=4, seconds=1),
        )
        with pytest.raises(ValueError, match="ambiguous governed applicability"):
            _resolve_current(
                session,
                rule_id=rule_id,
                project=project,
                as_of=BASE_TIME + timedelta(minutes=10),
            )


def _evaluation_materials(
    session: Session,
    *,
    rule_id: str,
    revision: str,
    rev_id: int,
    project: str,
    decision_time: datetime,
):
    context = GovernedApplicabilityContext(project=project)
    rev = session.get(EngineeringRuleRevision, rev_id)
    assert rev is not None
    activate_event = session.scalar(
        select(RuleLifecycleEvent).where(
            RuleLifecycleEvent.engineering_rule_revision_id == rev_id,
            RuleLifecycleEvent.event_type == RuleLifecycleEventType.ACTIVATE,
        )
    )
    assert activate_event is not None
    scope_snapshot = {
        key: (value,) if isinstance(value, str) else tuple(value)
        for key, value in (activate_event.scope_snapshot or {}).items()
        if value is not None
    }
    candidate = GovernedApplicabilityCandidate(
        candidate_id=f"{rule_id}:{revision}",
        rule_id=rule_id,
        revision=revision,
        evidence_class=EvidenceClass.SOURCE_BACKED,
        enabled=True,
        active=True,
        scope_snapshot=scope_snapshot,
        effective_from=activate_event.effective_from,
        expires_at=activate_event.expires_at,
    )
    resolution = resolve_governed_applicability(context, decision_time, [candidate])
    assert resolution.outcome is ApplicabilityResolutionOutcome.SELECTED
    requirement = RuleRequirement(
        rule_id=rule_id,
        revision=revision,
        parameter="synthetic_parameter",
        operator=RuleOperator.MIN,
        unit=EVALUATION_UNIT,
        min_value=10.0,
        enabled=True,
    )
    observation = Observation(
        parameter="synthetic_parameter", value=11.0, unit=EVALUATION_UNIT
    )
    comparison = compare_rule(
        requirement,
        observation,
        applicability_result=resolution,
        unit_context=UnitPolicyContext(expected_unit=EVALUATION_UNIT),
    )
    assert comparison.outcome is RuleComparisonOutcome.SATISFIED
    return comparison, observation


def _persist_evaluation(
    session: Session,
    *,
    rule_id: str,
    project: str,
    user_ids: dict[str, int],
    decision_time: datetime,
    comparison: RuleComparison,
    observation: Observation,
) -> str:
    evaluation_id = f"{rule_id}-evaluation-1"
    with GovernedUnitOfWork(session) as unit_of_work:
        service = RuleEvaluationService(unit_of_work)
        result = service.persist_evaluation(
            draft=RuleEvaluationPersistenceDraft(
                evaluation_id=evaluation_id,
                revision_number=1,
                comparison=comparison,
                applicability_result=comparison.applicability_result,
                observation=observation,
                unit_context=UnitPolicyContext(expected_unit=EVALUATION_UNIT),
            ),
            receipt_id=f"{rule_id}-eval-receipt-1",
            command_identity=_identity(
                RuleEvaluationService.COMMAND_NAMESPACE,
                evaluation_id,
                f"{rule_id}-eval-1",
            ),
            request_hash=_request_hash(f"{rule_id}-eval-1"),
            audit=_audit(
                f"{rule_id}-eval-audit-1",
                ACTORS["submitter"],
                user_ids["submitter"],
                f"{rule_id}-eval-1",
                "Phase 6B2B historical evaluation",
                project,
            ),
            completed_at=decision_time,
        )
        assert result.result_type == "rule_evaluation"
        unit_of_work.commit()
    return evaluation_id
def _persist_mrc(
    session: Session,
    *,
    rule_id: str,
    project: str,
    user_ids: dict[str, int],
    decision_time: datetime,
    comparison: RuleComparison,
) -> str:
    assessment_id = f"{rule_id}-assessment-1"
    context = GovernedApplicabilityContext(project=project)
    snapshot = GovernedRuleEvaluationSnapshot(
        evaluation_id=f"{rule_id}-evaluation-1",
        revision_number=1,
        comparison=comparison,
    )
    check_id = f"{rule_id}-check-1"
    check = GovernedMachineReadinessCheck(
        check_id=check_id,
        required=True,
        evaluations=(snapshot,),
        description="Phase 6B2B governed check",
    )
    trace = MachineReadinessCheckTrace(
        check_id=check_id,
        required=True,
        evaluations=(snapshot,),
        condition=CheckCondition.PASSED,
        reason="Governed input present and satisfied",
    )
    result = MachineReadinessResult(
        state=ReadinessState.READY,
        reasons=("all required applicable checks passed",),
        prerequisites=(
            ("at least one applicable validated engineering rule exists", True),
        ),
        context=context,
        decision_time=decision_time,
        checks=(trace,),
        validated_applicable_basis_count=1,
    )
    with GovernedUnitOfWork(session) as unit_of_work:
        service = MachineReadinessService(unit_of_work)
        ref = service.persist_assessment(
            draft=MachineReadinessPersistenceDraft(
                assessment_id=assessment_id,
                revision_number=1,
                result=result,
                checks=(check,),
            ),
            receipt_id=f"{rule_id}-mrc-receipt-1",
            command_identity=_identity(
                MachineReadinessService.COMMAND_NAMESPACE,
                assessment_id,
                f"{rule_id}-mrc-1",
            ),
            request_hash=_request_hash(f"{rule_id}-mrc-1"),
            audit=_audit(
                f"{rule_id}-mrc-audit-1",
                ACTORS["submitter"],
                user_ids["submitter"],
                f"{rule_id}-mrc-1",
                "Phase 6B2B historical MRC",
                project,
            ),
            completed_at=decision_time,
        )
        assert ref.result_type == "machine_readiness"
        unit_of_work.commit()
    return assessment_id


def _persist_dwp(
    session: Session,
    *,
    rule_id: str,
    project: str,
    user_ids: dict[str, int],
    decision_time: datetime,
    eval_snapshot: dict,
    mrc_snapshot: dict,
) -> str:
    passport_id = f"{rule_id}-passport-1"
    with GovernedUnitOfWork(session) as unit_of_work:
        service = DigitalWeldPassportService(unit_of_work)
        result = service.create_draft_revision(
            draft=DigitalWeldPassportRevisionDraft(
                passport_id=passport_id,
                revision_number=1,
                supersedes_revision_id=None,
                context_snapshot={
                    "passport_id": passport_id,
                    "scope_snapshot": VerificationScopeSnapshot(
                        project=project
                    ).as_dict(),
                },
                provenance_snapshot={"rule_evaluations": [eval_snapshot]},
                authority_snapshot={
                    "scope_snapshot": VerificationScopeSnapshot(
                        project=project
                    ).as_dict()
                },
                mrc_snapshot=mrc_snapshot,
            ),
            receipt_id=f"{rule_id}-dwp-receipt-1",
            command_identity=_identity(
                DigitalWeldPassportService.COMMAND_NAMESPACE,
                passport_id,
                f"{rule_id}-dwp-1",
            ),
            request_hash=_request_hash(f"{rule_id}-dwp-1"),
            audit=_audit(
                f"{rule_id}-dwp-audit-1",
                ACTORS["submitter"],
                user_ids["submitter"],
                f"{rule_id}-dwp-1",
                "Phase 6B2B historical DWP",
                project,
            ),
            completed_at=decision_time,
        )
        assert result.result_type == "digital_weld_passport"
        unit_of_work.commit()
    return passport_id
def test_historical_references_remain_pinned_after_supersession_on_postgresql(
    postgresql_engine,
) -> None:
    rule_id = "PHASE_6B2B_HISTORICAL_PINS"
    project = "phase-6b2b-project_historical"
    decision_time = BASE_TIME + timedelta(minutes=3)
    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()
        rev1_id = _active_rev1(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            enable_effective=BASE_TIME + timedelta(minutes=1),
            activate_effective=BASE_TIME + timedelta(minutes=2),
        )

        # Historical Evaluation pinned to Rev1 (created before supersession)
        with session:
            comparison, observation = _evaluation_materials(
                session,
                rule_id=rule_id,
                revision="1.0",
                rev_id=rev1_id,
                project=project,
                decision_time=decision_time,
            )
        evaluation_id = _persist_evaluation(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            decision_time=decision_time,
            comparison=comparison,
            observation=observation,
        )
        # Historical MRC pinning the same Evaluation
        assessment_id = _persist_mrc(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            decision_time=decision_time,
            comparison=comparison,
        )
        with session:
            eval_row = session.scalar(
                select(RuleEvaluation).where(
                    RuleEvaluation.evaluation_id == evaluation_id,
                    RuleEvaluation.revision_number == 1,
                )
            )
            mrc_row = session.scalar(
                select(MachineReadinessAssessmentRevision).where(
                    MachineReadinessAssessmentRevision.assessment_id
                    == assessment_id,
                    MachineReadinessAssessmentRevision.revision_number == 1,
                )
            )
            assert eval_row is not None
            assert mrc_row is not None
            assert eval_row.engineering_rule_revision_id == rev1_id
            assert eval_row.rule_revision == "1.0"
            eval_snapshot = DigitalWeldPassportService._rule_evaluation_snapshot(
                eval_row
            )
            mrc_snapshot = DigitalWeldPassportService._mrc_snapshot(mrc_row)
            mrc_before = dict(mrc_row.result_snapshot)
        # Historical DWP referencing the Evaluation and MRC
        passport_id = _persist_dwp(
            session,
            rule_id=rule_id,
            project=project,
            user_ids=user_ids,
            decision_time=decision_time,
            eval_snapshot=eval_snapshot,
            mrc_snapshot=mrc_snapshot,
        )
        with session:
            dwp_row = session.scalar(
                select(DigitalWeldPassportRevision).where(
                    DigitalWeldPassportRevision.passport_id == passport_id
                )
            )
            assert dwp_row is not None
            assert dwp_row.provenance_snapshot["rule_evaluations"][0][
                "rule_revision"
            ] == "1.0"
            dwp_before = dict(dwp_row.provenance_snapshot)
# Supersede Rev1 with Rev2 -> current resolution becomes Rev2
        _create_revision(
            session,
            rule_id=rule_id,
            revision="2.0-draft",
            evidence_id=f"{rule_id}_EVIDENCE_2",
            label="Replacement candidate",
            user_ids=user_ids,
            project=project,
        )
        _supersede(
            session,
            rule_id=rule_id,
            incumbent_revision="1.0",
            replacement_candidate_revision="2.0-draft",
            replacement_revision="2.0",
            key=f"{rule_id}-supersede",
            project=project,
            user_ids=user_ids,
            effective_from=BASE_TIME + timedelta(minutes=4),
            expires_at=None,
        )
        resolved = _resolve_current(
            session,
            rule_id=rule_id,
            project=project,
            as_of=BASE_TIME + timedelta(minutes=30),
        )
        assert resolved.revision == "2.0"

        # Historical references are untouched by the current-state resolution
        with session:
            eval_after = session.scalar(
                select(RuleEvaluation).where(
                    RuleEvaluation.evaluation_id == evaluation_id,
                    RuleEvaluation.revision_number == 1,
                )
            )
            mrc_after = session.scalar(
                select(MachineReadinessAssessmentRevision).where(
                    MachineReadinessAssessmentRevision.assessment_id
                    == assessment_id,
                    MachineReadinessAssessmentRevision.revision_number == 1,
                )
            )
            dwp_after = session.scalar(
                select(DigitalWeldPassportRevision).where(
                    DigitalWeldPassportRevision.passport_id == passport_id
                )
            )
            assert eval_after is not None
            assert mrc_after is not None
            assert dwp_after is not None
            assert eval_after.engineering_rule_revision_id == rev1_id
            assert eval_after.rule_revision == "1.0"
            assert mrc_after.result_snapshot == mrc_before
            assert dwp_after.provenance_snapshot == dwp_before
            assert dwp_after.provenance_snapshot["rule_evaluations"][0][
                "rule_revision"
            ] == "1.0"
            replacement = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=rule_id),
                    EngineeringRuleRevision.revision == "2.0",
                )
            )
            assert replacement is not None
            assert replacement.supersedes_revision_id == rev1_id