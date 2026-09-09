"""Real-PostgreSQL governed active-revision supersession end-to-end integration test (Phase 6B2A)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.governed_unit_of_work import GovernedUnitOfWork
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
from app.domain.rule_registry_types import (
    EvidenceReferenceDraft,
    MissingHandling,
    RuleCategory,
    SafeDefault,
)
from app.domain.verification_types import (
    EvidenceVerificationAuthoritySnapshot,
    EvidenceVerificationDecisionDraft,
    EvidenceVerificationDelegationDraft,
    VerificationCapability,
    VerificationDecisionOutcome,
    VerificationDelegationStatus,
    VerificationScopeSnapshot,
)
from app.models.entities import User
from app.models.rule_registry import (
    EngineeringRuleRevision,
    RuleLifecycleEvent,
    RuleLifecycleEventType,
)
from app.models.verification import EvidenceVerificationDecision
from app.repositories.evidence_verification_repository import (
    EvidenceVerificationRepository,
)

RULE_ID = "PHASE_6B2A_ACTIVE_SUPERSESSION"
INCUMBENT_REVISION = "1.0"
CANDIDATE_REVISION = "2.0-draft"
REPLACEMENT_REVISION = "2.0"
CONFLICTING_REPLACEMENT_REVISION = "3.0"
PROJECT_SCOPE = {"project": "phase-6b2a-project"}
LIFECYCLE_SCOPE = VerificationScopeSnapshot(project=PROJECT_SCOPE["project"]).as_dict()
BASE_TIME = datetime(2038, 3, 1, 10, 0, tzinfo=timezone.utc)
ACTORS = {
    "submitter": {"email": "phase6b2a-submitter@example.com", "name": "Phase 6B2A Submitter", "role": "Engineer"},
    "verifier": {"email": "phase6b2a-verifier@example.com", "name": "Phase 6B2A Verifier", "role": "Verifier"},
    "approver": {"email": "phase6b2a-approver@example.com", "name": "Phase 6B2A Approver", "role": "Approver"},
    "executor": {"email": "phase6b2a-executor@example.com", "name": "Phase 6B2A Executor", "role": "Governor"},
}


def _digest(data: object) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _draft_version_metadata(label: str) -> ContentVersionMetadata:
    return ContentVersionMetadata(
        schema_version="phase-6b2a-content-schema-v1",
        canonicalization_version="phase-6b2a-canonical-v1",
        hash_algorithm="sha256",
        content_hash=_digest({"label": label}),
        software_version="phase-6b2a-test",
    )


def _identity(namespace: str, scope: str, key: str) -> CommandIdentity:
    return CommandIdentity(command_namespace=namespace, command_scope=scope, idempotency_key=key)


def _request_hash(key: str) -> CanonicalRequestHash:
    return CanonicalRequestHash(
        value=_digest({"key": key}),
        hash_algorithm="sha256",
        canonicalization_version="phase-6b2a-canonical-v1",
    )


def _audit(event_id: str, actor: dict, actor_user_id: int, idempotency_key: str, reason: str) -> GovernedAuditMetadata:
    return GovernedAuditMetadata(
        event_id=event_id,
        actor_id=actor["email"],
        actor_user_id=actor_user_id,
        actor_type="user",
        actor_role=actor["role"],
        reason=reason,
        authority_scope=dict(LIFECYCLE_SCOPE),
        correlation_id="phase-6b2a-supersession",
        schema_version="phase-6b2a-audit-v1",
        canonicalization_version="phase-6b2a-canonical-v1",
        hash_algorithm="sha256",
        software_version="phase-6b2a-test",
        created_at=BASE_TIME,
        idempotency_key=idempotency_key,
        detail={},
    )

def _seed_users(session: Session) -> dict[str, int]:
    """Materialize (or reuse) the fixed Phase 6B2A actors, failing closed on drift."""
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
                raise RuntimeError(f"Phase 6B2A ACTORS drift: user {email!r} full_name mismatch")
            if existing.role != expected_role:
                raise RuntimeError(f"Phase 6B2A ACTORS drift: user {email!r} role mismatch")
            if not existing.is_active:
                raise RuntimeError(f"Phase 6B2A ACTORS drift: user {email!r} inactive")
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
) -> None:
    delegation_id = f"phase-6b2a-delegation-{label}"
    verification_id = f"phase-6b2a-verification-{label}"
    repo = EvidenceVerificationRepository(session)
    scope = VerificationScopeSnapshot(project=str(LIFECYCLE_SCOPE["project"]))

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
            schema_version="phase-6b2a-verification-v1",
            canonicalization_version="phase-6b2a-canonical-v1",
            hash_algorithm="sha256",
            content_hash=_digest({"delegation_id": delegation_id, "verifier_user_id": verifier_uid}),
            software_version="phase-6b2a-test",
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
        correlation_id="phase-6b2a-verification",
        schema_version="evidence-verification-authority-snapshot-v1",
        canonicalization_version="phase-6b2a-canonical-v1",
        hash_algorithm="sha256",
        content_hash=_digest({"verification_id": verification_id, "delegation_id": delegation.delegation_id}),
        software_version="phase-6b2a-test",
    )

    repo.create_verification_decision(
        draft=EvidenceVerificationDecisionDraft(
            verification_id=verification_id,
            revision_number=1,
            evidence_reference_id=evidence_reference.id,
            evidence_verification_delegation_id=delegation.id,
            verifier_user_id=verifier_uid,
            authority_snapshot=authority.as_dict(),
            decision_reason="Verified Phase 6B2A evidence",
            decided_at=BASE_TIME,
            policy_identifier="SDS-115",
            policy_version="0.1 Draft",
            correlation_id="phase-6b2a-verification",
            supersedes_verification_decision_id=None,
            created_by_user_id=verifier_uid,
            created_by_actor_id=str(ACTORS["verifier"]["email"]),
            schema_version="phase-6b2a-verification-v1",
            canonicalization_version="phase-6b2a-canonical-v1",
            hash_algorithm="sha256",
            content_hash=_digest({"verification_id": verification_id, "evidence_reference_id": evidence_reference.id}),
            software_version="phase-6b2a-test",
        )
    )

def _supersession_basis_hash(
    session: Session,
    *,
    rule_id: str,
    incumbent_id: int,
    incumbent_revision: str,
    candidate: EngineeringRuleRevision,
    replacement_revision: str,
) -> str:
    """Recompute the governed basis hash pinned by the supersession command."""
    ordered_references = sorted(
        candidate.evidence_references,
        key=lambda reference: (reference.evidence_id, reference.evidence_revision, reference.id),
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
            "scope_snapshot": dict(LIFECYCLE_SCOPE),
            "evidence_pins": evidence_pins,
        }
    )

def test_governed_active_revision_supersession_on_postgresql(postgresql_engine) -> None:
    """Supersede one ACTIVE SOURCE_BACKED revision through the governed command."""
    assert postgresql_engine.dialect.name == "postgresql"

    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()

        # === PHASE 1: incumbent revision 1.0 (SOURCE_BACKED, verified evidence) ===
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            registry.create_identity(
                rule_id=RULE_ID,
                audit=_audit("phase-6b2a-identity-audit", ACTORS["submitter"], user_ids["submitter"], "phase-6b2a-identity", "Create Phase 6B2A identity"),
            )
            incumbent = registry.create_draft_revision(
                rule_id=RULE_ID, revision=INCUMBENT_REVISION,
                name="Active supersession incumbent", evidence_class=EvidenceClass.SOURCE_BACKED,
                category=RuleCategory.OTHER, parameter="governed_input_present",
                safe_default=SafeDefault.UNRESOLVED, missing_handling=MissingHandling.DATA_INSUFFICIENT,
                reason_for_change="Phase 6B2A incumbent baseline",
                version_metadata=_draft_version_metadata("incumbent"),
                audit=_audit("phase-6b2a-rev1-audit", ACTORS["submitter"], user_ids["submitter"], "phase-6b2a-rev1", "Phase 6B2A incumbent"),
                evidence_references=(EvidenceReferenceDraft(
                    evidence_id="PHASE_6B2A_EVIDENCE_INCUMBENT", evidence_revision="1",
                    evidence_class=EvidenceClass.UNRESOLVED, lifecycle_status=RuleLifecycleStatus.DRAFT,
                    created_by_actor_id=ACTORS["submitter"]["email"], created_by_user_id=user_ids["submitter"],
                    reference_uri="urn:spotweld:test:phase6b2a-incumbent"),),
                allow_source_backed=True,
            )
            _create_evidence(session, incumbent.evidence_references[0], user_ids["verifier"], ACTORS["verifier"]["role"], user_ids["approver"], "incumbent")
            unit_of_work.commit()

        for event_type, namespace, minute in (
            (RuleLifecycleEventType.ENABLE, RuleRegistryService.ENABLEMENT_COMMAND_NAMESPACE, 1),
            (RuleLifecycleEventType.ACTIVATE, RuleRegistryService.ACTIVATION_COMMAND_NAMESPACE, 2),
        ):
            key = f"phase-6b2a-{event_type.value.lower()}-rev1"
            with GovernedUnitOfWork(session) as unit_of_work:
                registry = RuleRegistryService(unit_of_work)
                transition = registry.enable_source_backed if event_type is RuleLifecycleEventType.ENABLE else registry.activate_source_backed
                transition_result = transition(
                    rule_id=RULE_ID, source_revision=INCUMBENT_REVISION,
                    receipt_id=f"phase-6b2a-{event_type.value.lower()}-receipt-1",
                    command_identity=_identity(namespace, RULE_ID, key), request_hash=_request_hash(key),
                    audit=_audit(f"phase-6b2a-{event_type.value.lower()}-audit-1", ACTORS["executor"], user_ids["executor"], key, f"Phase 6B2A {event_type.value} incumbent"),
                    effective_from=BASE_TIME + timedelta(minutes=minute), expires_at=None,
                    completed_at=BASE_TIME + timedelta(minutes=minute, seconds=1),
                )
                assert transition_result.result_type == "engineering_rule_lifecycle_event"
                unit_of_work.commit()

        with session:
            incumbent_persisted = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                    EngineeringRuleRevision.revision == INCUMBENT_REVISION,
                )
            )
            assert incumbent_persisted is not None
            incumbent_id = incumbent_persisted.id
            incumbent_activate_event = session.scalar(
                select(RuleLifecycleEvent).where(
                    RuleLifecycleEvent.engineering_rule_revision_id == incumbent_id,
                    RuleLifecycleEvent.event_type == RuleLifecycleEventType.ACTIVATE,
                )
            )
            assert incumbent_activate_event is not None

        # === PHASE 2: replacement candidate draft 2.0-draft (verified evidence) ===
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            candidate = registry.create_draft_revision(
                rule_id=RULE_ID, revision=CANDIDATE_REVISION,
                name="Active supersession replacement candidate", evidence_class=EvidenceClass.SOURCE_BACKED,
                category=RuleCategory.OTHER, parameter="governed_input_present",
                safe_default=SafeDefault.UNRESOLVED, missing_handling=MissingHandling.DATA_INSUFFICIENT,
                reason_for_change="Phase 6B2A replacement candidate",
                version_metadata=_draft_version_metadata("candidate"),
                audit=_audit("phase-6b2a-candidate-audit", ACTORS["submitter"], user_ids["submitter"], "phase-6b2a-candidate", "Phase 6B2A candidate"),
                evidence_references=(EvidenceReferenceDraft(
                    evidence_id="PHASE_6B2A_EVIDENCE_CANDIDATE", evidence_revision="1",
                    evidence_class=EvidenceClass.UNRESOLVED, lifecycle_status=RuleLifecycleStatus.DRAFT,
                    created_by_actor_id=ACTORS["submitter"]["email"], created_by_user_id=user_ids["submitter"],
                    reference_uri="urn:spotweld:test:phase6b2a-candidate"),),
                allow_source_backed=True,
            )
            _create_evidence(session, candidate.evidence_references[0], user_ids["verifier"], ACTORS["verifier"]["role"], user_ids["approver"], "candidate")
            unit_of_work.commit()

        with session:
            candidate_persisted = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                    EngineeringRuleRevision.revision == CANDIDATE_REVISION,
                )
            )
            assert candidate_persisted is not None
            basis_content_hash = _supersession_basis_hash(
                session,
                rule_id=RULE_ID,
                incumbent_id=incumbent_id,
                incumbent_revision=INCUMBENT_REVISION,
                candidate=candidate_persisted,
                replacement_revision=REPLACEMENT_REVISION,
            )
        replacement_version_metadata = ContentVersionMetadata(
            schema_version="phase-6b2a-content-schema-v1",
            canonicalization_version="phase-6b2a-canonical-v1",
            hash_algorithm="sha256",
            content_hash=basis_content_hash,
            software_version="phase-6b2a-test",
        )

        # === PHASE 3: governed supersession command ===
        supersede_key = "phase-6b2a-supersede-1"
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            supersede_result = registry.supersede_active_source_backed(
                rule_id=RULE_ID,
                incumbent_revision=INCUMBENT_REVISION,
                replacement_candidate_revision=CANDIDATE_REVISION,
                replacement_revision=REPLACEMENT_REVISION,
                version_metadata=replacement_version_metadata,
                receipt_id="phase-6b2a-supersede-receipt-1",
                command_identity=_identity(RuleRegistryService.SUPERSESSION_COMMAND_NAMESPACE, RULE_ID, supersede_key),
                request_hash=_request_hash(supersede_key),
                audit=_audit("phase-6b2a-supersede-audit-1", ACTORS["executor"], user_ids["executor"], supersede_key, "Phase 6B2A governed supersession"),
                effective_from=BASE_TIME + timedelta(minutes=3), expires_at=None,
                completed_at=BASE_TIME + timedelta(minutes=3, seconds=1),
            )
            assert supersede_result.result_type == "engineering_rule_lifecycle_event"
            assert supersede_result.result_revision == "1"
            unit_of_work.commit()

        # === PHASE 4: durable post-conditions ===
        with session:
            replacement = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                    EngineeringRuleRevision.revision == REPLACEMENT_REVISION,
                )
            )
            assert replacement is not None
            assert replacement.supersedes_revision_id == incumbent_id
            assert replacement.content_hash == basis_content_hash
            assert replacement.enabled is False
            assert replacement.status is RuleLifecycleStatus.DRAFT
            assert replacement.created_by_user_id == user_ids["executor"]

            incumbent_after = session.get(EngineeringRuleRevision, incumbent_id)
            assert incumbent_after is not None
            assert incumbent_after.supersedes_revision_id is None

            incumbent_history = session.scalars(
                select(RuleLifecycleEvent)
                .where(RuleLifecycleEvent.engineering_rule_revision_id == incumbent_id)
                .order_by(RuleLifecycleEvent.id)
            ).all()
            assert [event.event_type for event in incumbent_history] == [
                RuleLifecycleEventType.ENABLE,
                RuleLifecycleEventType.ACTIVATE,
                RuleLifecycleEventType.SUPERSEDE,
            ]
            supersede_event = incumbent_history[-1]
            assert supersede_event.revision_number == incumbent_activate_event.revision_number + 1
            assert supersede_event.supersedes_rule_lifecycle_event_id == incumbent_activate_event.id
            assert supersede_event.lifecycle_event_id == incumbent_activate_event.lifecycle_event_id

            replacement_history = session.scalars(
                select(RuleLifecycleEvent)
                .where(RuleLifecycleEvent.engineering_rule_revision_id == replacement.id)
                .order_by(RuleLifecycleEvent.id)
            ).all()
            assert [event.event_type for event in replacement_history] == [
                RuleLifecycleEventType.ENABLE,
                RuleLifecycleEventType.ACTIVATE,
            ]

            candidate_after = session.get(EngineeringRuleRevision, candidate_persisted.id)
            assert candidate_after is not None
            assert candidate_after.status is RuleLifecycleStatus.DRAFT
            assert candidate_after.content_hash == _draft_version_metadata("candidate").content_hash

        # === PHASE 5: durable idempotent replay of the completed command ===
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            replay_result = registry.supersede_active_source_backed(
                rule_id=RULE_ID,
                incumbent_revision=INCUMBENT_REVISION,
                replacement_candidate_revision=CANDIDATE_REVISION,
                replacement_revision=REPLACEMENT_REVISION,
                version_metadata=replacement_version_metadata,
                receipt_id="phase-6b2a-supersede-receipt-1",
                command_identity=_identity(RuleRegistryService.SUPERSESSION_COMMAND_NAMESPACE, RULE_ID, supersede_key),
                request_hash=_request_hash(supersede_key),
                audit=_audit("phase-6b2a-supersede-audit-1-replay", ACTORS["executor"], user_ids["executor"], supersede_key, "Phase 6B2A supersession replay"),
                effective_from=BASE_TIME + timedelta(minutes=3), expires_at=None,
                completed_at=BASE_TIME + timedelta(minutes=4),
            )
            assert replay_result == supersede_result

        # === PHASE 6: second supersession of the same incumbent -> governed denial ===
        conflict_key = "phase-6b2a-supersede-2"
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            denial_result = registry.supersede_active_source_backed(
                rule_id=RULE_ID,
                incumbent_revision=INCUMBENT_REVISION,
                replacement_candidate_revision=CANDIDATE_REVISION,
                replacement_revision=CONFLICTING_REPLACEMENT_REVISION,
                version_metadata=_draft_version_metadata("conflicting"),
                receipt_id="phase-6b2a-supersede-receipt-2",
                command_identity=_identity(RuleRegistryService.SUPERSESSION_COMMAND_NAMESPACE, RULE_ID, conflict_key),
                request_hash=_request_hash(conflict_key),
                audit=_audit("phase-6b2a-supersede-audit-2", ACTORS["executor"], user_ids["executor"], conflict_key, "Phase 6B2A conflicting supersession"),
                effective_from=BASE_TIME + timedelta(minutes=5), expires_at=None,
                completed_at=BASE_TIME + timedelta(minutes=5, seconds=1),
            )
            assert denial_result.result_type == "engineering_rule_supersession_denial"
            assert denial_result.result_revision == "denied"
            unit_of_work.commit()

        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            denial_replay = registry.supersede_active_source_backed(
                rule_id=RULE_ID,
                incumbent_revision=INCUMBENT_REVISION,
                replacement_candidate_revision=CANDIDATE_REVISION,
                replacement_revision=CONFLICTING_REPLACEMENT_REVISION,
                version_metadata=_draft_version_metadata("conflicting"),
                receipt_id="phase-6b2a-supersede-receipt-2",
                command_identity=_identity(RuleRegistryService.SUPERSESSION_COMMAND_NAMESPACE, RULE_ID, conflict_key),
                request_hash=_request_hash(conflict_key),
                audit=_audit("phase-6b2a-supersede-audit-2-replay", ACTORS["executor"], user_ids["executor"], conflict_key, "Phase 6B2A denial replay"),
                effective_from=BASE_TIME + timedelta(minutes=5), expires_at=None,
                completed_at=BASE_TIME + timedelta(minutes=6),
            )
            assert denial_replay == denial_result

        with session:
            conflicting = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                    EngineeringRuleRevision.revision == CONFLICTING_REPLACEMENT_REVISION,
                )
            )
            assert conflicting is None
            successors = session.scalars(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.supersedes_revision_id == incumbent_id
                )
            ).all()
            assert len(successors) == 1
            assert successors[0].revision == REPLACEMENT_REVISION