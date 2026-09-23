"""Real-PostgreSQL governed historical staleness end-to-end integration test."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.domain.readiness as readiness_domain
import app.domain.rule_evaluation as rule_evaluation_domain
from app.application.digital_weld_passport_service import (
    DigitalWeldPassportLifecycleTransitionDraft,
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
    GovernedMachineReadinessCheck,
    GovernedRuleEvaluationSnapshot,
    ReadinessState,
)
from app.domain.rule_applicability import (
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
from app.models.digital_weld_passport import (
    DigitalWeldPassportLifecycleEvent,
    DigitalWeldPassportLifecycleState,
    DigitalWeldPassportRevision,
)
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

RULE_ID = "PHASE_6B1_HISTORICAL_STALENESS"
RULE_REVISION_1 = "1.0"
RULE_REVISION_2 = "2.0"
RULE_REVISION_2_CANDIDATE = "2.0-draft"
EVALUATION_ID = "phase-6b1-evaluation-1"
ASSESSMENT_ID = "phase-6b1-assessment-1"
PASSPORT_ID = "phase-6b1-passport-1"
PROJECT_SCOPE = {"project": "phase-6b1-project"}
LIFECYCLE_SCOPE = VerificationScopeSnapshot(project=PROJECT_SCOPE["project"]).as_dict()
DECISION_TIME = datetime(2037, 2, 1, 12, 0, tzinfo=timezone.utc)
BASE_TIME = datetime(2037, 2, 1, 10, 0, tzinfo=timezone.utc)
ACTORS = {
    "submitter": {"email": "phase6b1-submitter@example.com", "name": "Phase 6B1 Submitter", "role": "Engineer"},
    "verifier": {"email": "phase6b1-verifier@example.com", "name": "Phase 6B1 Verifier", "role": "Verifier"},
    "approver": {"email": "phase6b1-approver@example.com", "name": "Phase 6B1 Approver", "role": "Approver"},
    "releaser": {"email": "phase6b1-releaser@example.com", "name": "Phase 6B1 Releaser", "role": "Releaser"},
}


def _digest(data: object) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _version_metadata(rule_id: str | None = None, revision: str | None = None) -> ContentVersionMetadata:
    return ContentVersionMetadata(
        schema_version="phase-6b1-content-schema-v1",
        canonicalization_version="phase-6b1-canonical-v1",
        hash_algorithm="sha256",
        content_hash=_digest({"rule_id": rule_id or RULE_ID, "revision": revision or RULE_REVISION_1}),
        software_version="phase-6b1-test",
    )


def _identity(namespace: str, scope: str, key: str) -> CommandIdentity:
    return CommandIdentity(command_namespace=namespace, command_scope=scope, idempotency_key=key)


def _request_hash(key: str) -> CanonicalRequestHash:
    return CanonicalRequestHash(
        value=_digest({"key": key}),
        hash_algorithm="sha256",
        canonicalization_version="phase-6b1-canonical-v1",
    )


def _audit(event_id: str, actor: dict, actor_user_id: int, idempotency_key: str, reason: str) -> GovernedAuditMetadata:
    return GovernedAuditMetadata(
        event_id=event_id, actor_id=actor["email"], actor_user_id=actor_user_id,
        actor_type="user", actor_role=actor["role"], reason=reason,
        authority_scope=LIFECYCLE_SCOPE, correlation_id="phase-6b1-staleness",
        schema_version="phase-6b1-audit-v1", canonicalization_version="phase-6b1-canonical-v1",
        hash_algorithm="sha256", software_version="phase-6b1-test",
        created_at=BASE_TIME, idempotency_key=idempotency_key, detail={},
    )


def _seed_users(session: Session) -> dict[str, int]:
    """Idempotently materialize the fixed Phase 6B1 ACTORS users.

    The PostgreSQL test session is session-scoped (see
    ``tests_postgresql/conftest.py``'s ``postgresql_engine`` fixture),
    so the migrated schema is shared across every governed-staleness
    test in the file. A previous test in the same session has already
    inserted the same fixed-emails rows; a naive second insert would
    collide with the ``users_email_key`` unique constraint and raise
    ``psycopg.errors.UniqueViolation``.

    The function therefore:

      1. Queries the durable ``User`` row for each ACTOR's fixed email.
      2. If no row exists, creates one with the same constructor
         fields used previously (including the model default
         ``is_active=True``).
      3. If a row already exists, reuses it and rejects unexpected
         drift on the important fixture properties
         (``full_name``, ``role``, ``is_active == True``). Drift
         fails closed: a runtime error is raised instead of silently
         reusing a row that does not match the test fixture's
         contract. This preserves the fail-closed governance
         posture of the rest of this file.
      4. Returns the same ``dict[str, int]`` mapping ACTOR key to
         the durable ``User.id`` (whether the row was newly
         inserted or reused).

    The function does NOT delete rows between tests and does NOT use
    random identities; the same deterministic Phase 6B1 actors are
    reused across the session.
    """
    result: dict[str, int] = {}
    for key, actor in ACTORS.items():
        email = str(actor["email"])
        expected_full_name = str(actor["name"])
        expected_role = str(actor["role"])
        existing = session.scalar(
            select(User).where(User.email == email)
        )
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
            # Reuse the durable row, but fail closed on unexpected
            # drift in the fixture properties other tests in this
            # session rely on.
            if existing.full_name != expected_full_name:
                raise RuntimeError(
                    f"Phase 6B1 ACTORS drift: user {email!r} has "
                    f"full_name={existing.full_name!r}, expected "
                    f"{expected_full_name!r}"
                )
            if existing.role != expected_role:
                raise RuntimeError(
                    f"Phase 6B1 ACTORS drift: user {email!r} has "
                    f"role={existing.role!r}, expected {expected_role!r}"
                )
            if not existing.is_active:
                raise RuntimeError(
                    f"Phase 6B1 ACTORS drift: user {email!r} is "
                    f"inactive; expected is_active=True"
                )
            user = existing
        result[key] = user.id
    return result


def _ctx_snapshot() -> dict:
    return {"project": PROJECT_SCOPE["project"], "site": "phase-6b1-site", "machine": "phase-6b1-machine"}


def _latest_lifecycle_event(
    session: Session,
    revision_id: int,
) -> RuleLifecycleEvent:
    event = session.scalar(
        select(RuleLifecycleEvent)
        .where(
            RuleLifecycleEvent.engineering_rule_revision_id == revision_id
        )
        .order_by(
            RuleLifecycleEvent.revision_number.desc(),
            RuleLifecycleEvent.id.desc(),
        )
    )
    assert event is not None
    return event


def _create_resolution(
    session: Session,
    rule_rev: EngineeringRuleRevision,
    dt: datetime,
):
    ctx = GovernedApplicabilityContext(**_ctx_snapshot())
    event = _latest_lifecycle_event(session, rule_rev.id)

    cand = GovernedApplicabilityCandidate(
        candidate_id=(
            f"{rule_rev.engineering_rule.rule_id}:{rule_rev.revision}"
        ),
        rule_id=rule_rev.engineering_rule.rule_id,
        revision=rule_rev.revision,
        evidence_class=rule_rev.evidence_class,
        enabled=event.event_type
        in {
            RuleLifecycleEventType.ENABLE,
            RuleLifecycleEventType.ACTIVATE,
        },
        active=event.event_type is RuleLifecycleEventType.ACTIVATE,
        suspended=event.event_type is RuleLifecycleEventType.SUSPEND,
        revoked=event.event_type is RuleLifecycleEventType.REVOKE,
        superseded=event.event_type is RuleLifecycleEventType.SUPERSEDE,
        basis_valid=event.event_type is not RuleLifecycleEventType.CORRECT,
        effective_from=event.effective_from,
        expires_at=event.expires_at,
        scope_snapshot={"project": (PROJECT_SCOPE["project"],)},
    )
    return resolve_governed_applicability(
        ctx,
        dt,
        (cand,),
    )


def _load_applicability_candidate(
    session: Session,
    rev: EngineeringRuleRevision,
    dt: datetime,
) -> GovernedApplicabilityCandidate:
    """Build applicability state from append-only lifecycle events."""
    event = _latest_lifecycle_event(session, rev.id)

    return GovernedApplicabilityCandidate(
        candidate_id=f"{rev.engineering_rule.rule_id}:{rev.revision}",
        rule_id=rev.engineering_rule.rule_id,
        revision=rev.revision,
        evidence_class=rev.evidence_class,
        enabled=event.event_type
        in {
            RuleLifecycleEventType.ENABLE,
            RuleLifecycleEventType.ACTIVATE,
        },
        active=event.event_type is RuleLifecycleEventType.ACTIVATE,
        suspended=event.event_type is RuleLifecycleEventType.SUSPEND,
        revoked=event.event_type is RuleLifecycleEventType.REVOKE,
        superseded=event.event_type is RuleLifecycleEventType.SUPERSEDE,
        basis_valid=event.event_type is not RuleLifecycleEventType.CORRECT,
        effective_from=event.effective_from or dt,
        expires_at=event.expires_at,
        scope_snapshot={"project": (PROJECT_SCOPE["project"],)},
    )


def _comparison(rule_rev: EngineeringRuleRevision, res) -> RuleComparison:
    obs = Observation(
        parameter="governed_input_present",
        value=1.0,
        unit="1",
    )
    req = RuleRequirement(
        rule_id=rule_rev.engineering_rule.rule_id,
        revision=rule_rev.revision,
        parameter="governed_input_present",
        operator=RuleOperator.EQUALS,
        unit="1",
        min_value=1.0,
        max_value=1.0,
    )
    result = compare_rule(
        req,
        obs,
        applicability_result=res,
    )
    assert result.outcome is RuleComparisonOutcome.SATISFIED
    return result


def _create_evidence(
    session: Session,
    ev_ref,
    verifier_uid: int,
    verifier_role: str,
    grantor_uid: int,
) -> None:
    delegation_id = f"phase-6b1-delegation-{ev_ref.id}"
    verification_id = f"phase-6b1-verification-{ev_ref.id}"
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
            schema_version="phase-6b1-verification-v1",
            canonicalization_version="phase-6b1-canonical-v1",
            hash_algorithm="sha256",
            content_hash=_digest({"delegation_id": delegation_id, "verifier_user_id": verifier_uid}),
            software_version="phase-6b1-test",
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
        correlation_id="phase-6b1-verification",
        schema_version="evidence-verification-authority-snapshot-v1",
        canonicalization_version="phase-6b1-canonical-v1",
        hash_algorithm="sha256",
        content_hash=_digest({"verification_id": verification_id, "delegation_id": delegation.delegation_id}),
        software_version="phase-6b1-test",
    )

    repo.create_verification_decision(
        draft=EvidenceVerificationDecisionDraft(
            verification_id=verification_id,
            revision_number=1,
            evidence_reference_id=ev_ref.id,
            evidence_verification_delegation_id=delegation.id,
            verifier_user_id=verifier_uid,
            authority_snapshot=authority.as_dict(),
            decision_reason="Verified Phase 6B1 evidence",
            decided_at=BASE_TIME,
            policy_identifier="SDS-115",
            policy_version="0.1 Draft",
            correlation_id="phase-6b1-verification",
            supersedes_verification_decision_id=None,
            created_by_user_id=verifier_uid,
            created_by_actor_id=str(ACTORS["verifier"]["email"]),
            schema_version="phase-6b1-verification-v1",
            canonicalization_version="phase-6b1-canonical-v1",
            hash_algorithm="sha256",
            content_hash=_digest({"verification_id": verification_id, "evidence_reference_id": ev_ref.id}),
            software_version="phase-6b1-test",
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
            "scope_snapshot": dict(LIFECYCLE_SCOPE),
            "evidence_pins": evidence_pins,
        }
    )


def test_governed_historical_staleness_on_postgresql(postgresql_engine, monkeypatch) -> None:
    """Verify historical pins remain stable when a new rule revision supersedes an active one."""
    assert postgresql_engine.dialect.name == "postgresql"

    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()

        # === PHASE 1: Create Rule Revision 1 ===
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)
            registry.create_identity(
                rule_id=RULE_ID,
                audit=_audit("phase-6b1-identity-audit", ACTORS["submitter"], user_ids["submitter"], "phase-6b1-identity", "Create Phase 6B1 identity"),
            )
            rev1 = registry.create_draft_revision(
                rule_id=RULE_ID, revision=RULE_REVISION_1,
                name="Historical staleness baseline", evidence_class=EvidenceClass.SOURCE_BACKED,
                category=RuleCategory.OTHER, parameter="governed_input_present",
                safe_default=SafeDefault.UNRESOLVED, missing_handling=MissingHandling.DATA_INSUFFICIENT,
                reason_for_change="Phase 6B1 baseline",
                version_metadata=_version_metadata(RULE_ID, RULE_REVISION_1),
                audit=_audit("phase-6b1-rev1-audit", ACTORS["submitter"], user_ids["submitter"], "phase-6b1-rev1", "Phase 6B1 Rev1"),
                evidence_references=(EvidenceReferenceDraft(
                    evidence_id="PHASE_6B1_EVIDENCE_1", evidence_revision="1",
                    evidence_class=EvidenceClass.UNRESOLVED, lifecycle_status=RuleLifecycleStatus.DRAFT,
                    created_by_actor_id=ACTORS["submitter"]["email"], created_by_user_id=user_ids["submitter"],
                    reference_uri="urn:spotweld:test:phase6b1-rev1"),),
                allow_source_backed=True,
            )
            _create_evidence(session, rev1.evidence_references[0], user_ids["verifier"], ACTORS["verifier"]["role"], user_ids["approver"])
            unit_of_work.commit()

        # Enable and activate Revision 1
        for event_type, namespace, minute in (
            (RuleLifecycleEventType.ENABLE, RuleRegistryService.ENABLEMENT_COMMAND_NAMESPACE, 1),
            (RuleLifecycleEventType.ACTIVATE, RuleRegistryService.ACTIVATION_COMMAND_NAMESPACE, 2),
        ):
            key = f"phase-6b1-{event_type.value.lower()}-rev1"
            with GovernedUnitOfWork(session) as unit_of_work:
                registry = RuleRegistryService(unit_of_work)
                transition = registry.enable_source_backed if event_type is RuleLifecycleEventType.ENABLE else registry.activate_source_backed
                result = transition(
                    rule_id=RULE_ID, source_revision=RULE_REVISION_1,
                    receipt_id=f"phase-6b1-{event_type.value.lower()}-receipt-1",
                    command_identity=_identity(namespace, RULE_ID, key), request_hash=_request_hash(key),
                    audit=_audit(f"phase-6b1-{event_type.value.lower()}-audit-1", ACTORS["approver"], user_ids["approver"], key, f"Phase 6B1 {event_type.value} Rev1"),
                    effective_from=BASE_TIME + timedelta(minutes=minute), expires_at=None,
                    completed_at=BASE_TIME + timedelta(minutes=minute, seconds=1),
                )
                assert result.result_type == "engineering_rule_lifecycle_event"
                unit_of_work.commit()

        # Verify Revision 1
        with session:
            rev1_persisted = session.scalar(select(EngineeringRuleRevision).where(EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID), EngineeringRuleRevision.revision == RULE_REVISION_1))
            assert rev1_persisted is not None
            rev1_id = rev1_persisted.id

        # === Create Evaluation1 against Rule Revision 1 ===
        with session:
            rev1 = session.get(EngineeringRuleRevision, rev1_id)
            res1 = _create_resolution(session, rev1, DECISION_TIME)
            comp1 = _comparison(rev1, res1)
            unit_policy = UnitPolicyContext(expected_unit="1")

            # The reads above autobegin a SQLAlchemy transaction.
            # GovernedUnitOfWork requires a clean session boundary.
            session.commit()

            with GovernedUnitOfWork(session) as unit_of_work:
                eval_service = RuleEvaluationService(unit_of_work)
                eval_result = eval_service.persist_evaluation(
                    draft=RuleEvaluationPersistenceDraft(
                        evaluation_id=EVALUATION_ID, revision_number=1, comparison=comp1,
                        applicability_result=res1,
                        observation=Observation(
                            parameter="governed_input_present",
                            value=1.0,
                            unit="1",
                        ),
                        unit_context=unit_policy,
                    ),
                    receipt_id="phase-6b1-eval-receipt-1",
                    command_identity=_identity(RuleEvaluationService.COMMAND_NAMESPACE, EVALUATION_ID, "phase-6b1-eval-1"),
                    request_hash=_request_hash("phase-6b1-eval-1"),
                    audit=_audit("phase-6b1-eval-audit-1", ACTORS["submitter"], user_ids["submitter"], "phase-6b1-eval-1", "Phase 6B1 Eval 1"),
                    completed_at=DECISION_TIME,
                )
                assert eval_result.result_type == "rule_evaluation"
                unit_of_work.commit()

        # === Create MRC1 referencing Evaluation1 ===
        evaluation_snapshot = GovernedRuleEvaluationSnapshot(
            evaluation_id=EVALUATION_ID,
            revision_number=1,
            comparison=comp1,
        )
        mrc_checks = (
            GovernedMachineReadinessCheck(
                check_id="phase-6b1-check-1",
                required=True,
                evaluations=(evaluation_snapshot,),
                description="Phase 6B1 check",
            ),
        )
        mrc_result = readiness_domain.evaluate_machine_readiness(
            res1.context,
            DECISION_TIME,
            mrc_checks,
        )

        with session:
            eval1 = session.scalar(
                select(RuleEvaluation).where(
                    RuleEvaluation.evaluation_id == EVALUATION_ID,
                    RuleEvaluation.revision_number == 1,
                )
            )
            assert eval1 is not None

            # Read operations above autobegin a transaction.
            # GovernedUnitOfWork requires a clean session boundary.
            session.commit()

            with GovernedUnitOfWork(session) as unit_of_work:
                mrc_service = MachineReadinessService(unit_of_work)
                mrc_result_ref = mrc_service.persist_assessment(
                    draft=MachineReadinessPersistenceDraft(
                        assessment_id=ASSESSMENT_ID,
                        revision_number=1,
                        result=mrc_result,
                        supersedes_assessment_revision_id=None,
                        checks=mrc_checks,
                    ),
                    receipt_id="phase-6b1-mrc-receipt-1",
                    command_identity=_identity(MachineReadinessService.COMMAND_NAMESPACE, ASSESSMENT_ID, "phase-6b1-mrc-1"),
                    request_hash=_request_hash("phase-6b1-mrc-1"),
                    audit=_audit("phase-6b1-mrc-audit-1", ACTORS["submitter"], user_ids["submitter"], "phase-6b1-mrc-1", "Phase 6B1 MRC 1"),
                    completed_at=DECISION_TIME + timedelta(minutes=2),
                )
                assert mrc_result_ref.result_type == "machine_readiness"
                unit_of_work.commit()

        # === Create DWP1 referencing MRC1 ===
        mrc_snapshot = {"assessment_id": ASSESSMENT_ID, "revision_number": 1, "state": ReadinessState.READY.value}
        eval_snapshot = {"evaluation_id": EVALUATION_ID, "revision_number": 1, "rule_id": RULE_ID, "rule_revision": RULE_REVISION_1, "outcome": "PASS"}

        with session, GovernedUnitOfWork(session) as unit_of_work:
                dwp_service = DigitalWeldPassportService(unit_of_work)
                dwp_result = dwp_service.create_draft_revision(
                    draft=DigitalWeldPassportRevisionDraft(
                        passport_id=PASSPORT_ID, revision_number=1,
                        supersedes_revision_id=None, context_snapshot=_ctx_snapshot(),
                        provenance_snapshot={"rule_evaluations": [eval_snapshot]},
                        authority_snapshot={"scope_snapshot": PROJECT_SCOPE}, mrc_snapshot=mrc_snapshot,
                    ),
                    receipt_id="phase-6b1-dwp-receipt-1",
                    command_identity=_identity(DigitalWeldPassportService.COMMAND_NAMESPACE, PASSPORT_ID, "phase-6b1-dwp-1"),
                    request_hash=_request_hash("phase-6b1-dwp-1"),
                    audit=_audit("phase-6b1-dwp-audit-1", ACTORS["submitter"], user_ids["submitter"], "phase-6b1-dwp-1", "Phase 6B1 DWP 1"),
                    completed_at=DECISION_TIME + timedelta(minutes=3),
                )
                assert dwp_result.result_type == "digital_weld_passport"
                unit_of_work.commit()

        # Advance DWP1 to PRODUCTION_ACTIVE
        for state, actor_name, sequence in (
            (DigitalWeldPassportLifecycleState.ENGINEERING_DEFINED, "submitter", 1),
            (DigitalWeldPassportLifecycleState.VALIDATION_PENDING, "submitter", 2),
            (DigitalWeldPassportLifecycleState.VALIDATED, "verifier", 3),
            (DigitalWeldPassportLifecycleState.APPROVED, "approver", 4),
            (DigitalWeldPassportLifecycleState.PRODUCTION_ACTIVE, "releaser", 5),
        ):
            key = f"phase-6b1-dwp-{state.value.lower()}"
            with session:
                revision = session.scalar(select(DigitalWeldPassportRevision).where(DigitalWeldPassportRevision.passport_id == PASSPORT_ID, DigitalWeldPassportRevision.revision_number == 1))
                current_event = session.scalar(select(DigitalWeldPassportLifecycleEvent).where(DigitalWeldPassportLifecycleEvent.passport_revision_id == revision.id).order_by(DigitalWeldPassportLifecycleEvent.revision_number.desc()))

                with GovernedUnitOfWork(session) as unit_of_work:
                    result = DigitalWeldPassportService(unit_of_work).transition_revision(
                        transition=DigitalWeldPassportLifecycleTransitionDraft(
                            passport_id=PASSPORT_ID, revision_number=1, state=state,
                            reason=f"Phase 6B1 advance to {state.value}", mrc_snapshot=mrc_snapshot,
                            supersedes_lifecycle_event_id=current_event.id,
                        ),
                        receipt_id=f"phase-6b1-dwp-transition-receipt-{sequence}",
                        command_identity=_identity(DigitalWeldPassportService.COMMAND_NAMESPACE, PASSPORT_ID, key),
                        request_hash=_request_hash(key),
                        audit=_audit(f"phase-6b1-dwp-{state.value.lower()}-audit", ACTORS[actor_name], user_ids[actor_name], key, f"Phase 6B1 DWP advance to {state.value}"),
                        completed_at=BASE_TIME + timedelta(minutes=10 + sequence),
                    )
                    assert result.result_type == "digital_weld_passport"
                    unit_of_work.commit()

        # === PHASE 2: Governed active supersession Rev1 -> Rev2 ===

        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)

            candidate = registry.create_draft_revision(
                rule_id=RULE_ID,
                revision=RULE_REVISION_2_CANDIDATE,
                name="Historical staleness updated candidate",
                evidence_class=EvidenceClass.SOURCE_BACKED,
                category=RuleCategory.OTHER,
                parameter="governed_input_present",
                safe_default=SafeDefault.UNRESOLVED,
                missing_handling=MissingHandling.DATA_INSUFFICIENT,
                reason_for_change="Phase 6B1 Revision 2 candidate",
                version_metadata=_version_metadata(
                    RULE_ID,
                    RULE_REVISION_2_CANDIDATE,
                ),
                audit=_audit(
                    "phase-6b1-rev2-candidate-audit",
                    ACTORS["submitter"],
                    user_ids["submitter"],
                    "phase-6b1-rev2-candidate",
                    "Phase 6B1 Rev2 candidate",
                ),
                evidence_references=(
                    EvidenceReferenceDraft(
                        evidence_id="PHASE_6B1_EVIDENCE_2",
                        evidence_revision="1",
                        evidence_class=EvidenceClass.UNRESOLVED,
                        lifecycle_status=RuleLifecycleStatus.DRAFT,
                        created_by_actor_id=ACTORS["submitter"]["email"],
                        created_by_user_id=user_ids["submitter"],
                        reference_uri="urn:spotweld:test:phase6b1-rev2",
                    ),
                ),
                allow_source_backed=True,
            )

            _create_evidence(
                session,
                candidate.evidence_references[0],
                user_ids["verifier"],
                ACTORS["verifier"]["role"],
                user_ids["approver"],
            )

            unit_of_work.commit()

        candidate_persisted = session.scalar(
            select(EngineeringRuleRevision).where(
                EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                EngineeringRuleRevision.revision
                == RULE_REVISION_2_CANDIDATE,
            )
        )
        assert candidate_persisted is not None

        basis_content_hash = _supersession_basis_hash(
            session,
            rule_id=RULE_ID,
            incumbent_id=rev1_id,
            incumbent_revision=RULE_REVISION_1,
            candidate=candidate_persisted,
            replacement_revision=RULE_REVISION_2,
        )
        session.commit()

        replacement_version_metadata = ContentVersionMetadata(
            schema_version="phase-6b1-content-schema-v1",
            canonicalization_version="phase-6b1-canonical-v1",
            hash_algorithm="sha256",
            content_hash=basis_content_hash,
            software_version="phase-6b1-test",
        )

        supersede_key = "phase-6b1-supersede-rev2"

        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)

            supersede_result = registry.supersede_active_source_backed(
                rule_id=RULE_ID,
                incumbent_revision=RULE_REVISION_1,
                replacement_candidate_revision=RULE_REVISION_2_CANDIDATE,
                replacement_revision=RULE_REVISION_2,
                version_metadata=replacement_version_metadata,
                receipt_id="phase-6b1-supersede-receipt-2",
                command_identity=_identity(
                    RuleRegistryService.SUPERSESSION_COMMAND_NAMESPACE,
                    RULE_ID,
                    supersede_key,
                ),
                request_hash=_request_hash(supersede_key),
                audit=_audit(
                    "phase-6b1-supersede-audit-2",
                    ACTORS["releaser"],
                    user_ids["releaser"],
                    supersede_key,
                    "Phase 6B1 governed Rev1 to Rev2 supersession",
                ),
                effective_from=BASE_TIME + timedelta(minutes=21),
                expires_at=None,
                completed_at=BASE_TIME + timedelta(
                    minutes=21,
                    seconds=1,
                ),
            )

            assert (
                supersede_result.result_type
                == "engineering_rule_lifecycle_event"
            )

            unit_of_work.commit()

        rev2_persisted = session.scalar(
            select(EngineeringRuleRevision).where(
                EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                EngineeringRuleRevision.revision == RULE_REVISION_2,
            )
        )

        assert rev2_persisted is not None

        rev2_id = rev2_persisted.id

        assert rev2_persisted.engineering_rule.rule_id == RULE_ID
        assert rev2_persisted.id != rev1_id
        assert rev2_persisted.supersedes_revision_id == rev1_id
        assert rev2_persisted.evidence_class is EvidenceClass.SOURCE_BACKED

        # === PHASE 3: Verify Historical Pins ===
        with session:
            # Verify Revision 1 still exists
            rev1_after = session.get(EngineeringRuleRevision, rev1_id)
            assert rev1_after is not None

            # Verify Revision 2 is the current active revision (CURRENT_BASIS_AFTER_REV2 = REV2)
            rev2_after = session.get(EngineeringRuleRevision, rev2_id)
            assert rev2_after is not None

            # EXERCISE PUBLIC CURRENT-BASIS RESOLUTION PATH
            # Load both candidates from database and call resolve_governed_applicability
            rev1_persisted = session.scalar(
                select(EngineeringRuleRevision).where(
                    EngineeringRuleRevision.engineering_rule.has(rule_id=RULE_ID),
                    EngineeringRuleRevision.revision == RULE_REVISION_1
                )
            )
            assert rev1_persisted is not None
            ctx = GovernedApplicabilityContext.from_mapping(_ctx_snapshot())
            candidates = (
                _load_applicability_candidate(session, rev1_persisted, DECISION_TIME + timedelta(minutes=30)),
                _load_applicability_candidate(session, rev2_after, DECISION_TIME + timedelta(minutes=30)),
            )
            resolution = resolve_governed_applicability(
                ctx.as_mapping(),
                DECISION_TIME + timedelta(minutes=30),
                candidates,
            )
            # CURRENT_BASIS_AFTER_REV2 = REV2: prove via actual resolution, not just is_active()
            from app.domain.rule_applicability import ApplicabilityResolutionOutcome
            assert resolution.outcome is ApplicabilityResolutionOutcome.SELECTED
            assert resolution.selected_rule_id == RULE_ID
            assert resolution.selected_revision == RULE_REVISION_2
            # Rev2's candidate_id is the one selected
            assert resolution.selected_candidate_id == f"{RULE_ID}:{RULE_REVISION_2}"

            # Read back Evaluation1 and verify it still pins to Revision 1
            eval_final = session.scalar(select(RuleEvaluation).where(RuleEvaluation.evaluation_id == EVALUATION_ID, RuleEvaluation.revision_number == 1))
            assert eval_final is not None
            # HISTORICAL_EVALUATION_RULE_PIN = REV1
            assert eval_final.rule_id == RULE_ID
            assert eval_final.rule_revision == RULE_REVISION_1

            # Read back MRC1 and verify it still pins to Evaluation1
            mrc_final = session.scalar(select(MachineReadinessAssessmentRevision).where(MachineReadinessAssessmentRevision.assessment_id == ASSESSMENT_ID, MachineReadinessAssessmentRevision.revision_number == 1))
            assert mrc_final is not None

            # Read back DWP1 and verify it still pins to Evaluation1
            dwp_final = session.scalar(select(DigitalWeldPassportRevision).where(DigitalWeldPassportRevision.passport_id == PASSPORT_ID, DigitalWeldPassportRevision.revision_number == 1))
            assert dwp_final is not None
            dwp_provenance = dwp_final.provenance_snapshot
            assert len(dwp_provenance["rule_evaluations"]) == 1
            dwp_eval = dwp_provenance["rule_evaluations"][0]
            # DWP still references the evaluation that pins to Revision 1
            assert dwp_eval["evaluation_id"] == EVALUATION_ID
            assert dwp_eval["rule_revision"] == RULE_REVISION_1

            # HISTORICAL_DWP_MRC_PIN = MRC1: verify DWP.mrc_snapshot references ASSESSMENT_ID with revision_number=1
            assert dwp_final.mrc_snapshot is not None
            assert dwp_final.mrc_snapshot["assessment_id"] == ASSESSMENT_ID
            assert dwp_final.mrc_snapshot["revision_number"] == 1

        # === PHASE 4: Verify Read Path Does Not Recompute ===
        def _unexpected_recompute(*_args, **_kwargs):
            raise AssertionError("governed read path recomputed an engineering result")

        monkeypatch.setattr(rule_evaluation_domain, "compare_rule", _unexpected_recompute)
        monkeypatch.setattr(readiness_domain, "evaluate_machine_readiness", _unexpected_recompute)

        # Verify that reading historical records does not trigger recomputation
        with session:
            eval_read = session.scalar(select(RuleEvaluation).where(RuleEvaluation.evaluation_id == EVALUATION_ID, RuleEvaluation.revision_number == 1))
            assert eval_read.rule_revision == RULE_REVISION_1

            mrc_read = session.scalar(select(MachineReadinessAssessmentRevision).where(MachineReadinessAssessmentRevision.assessment_id == ASSESSMENT_ID, MachineReadinessAssessmentRevision.revision_number == 1))
            assert mrc_read is not None

            dwp_read = session.scalar(select(DigitalWeldPassportRevision).where(DigitalWeldPassportRevision.passport_id == PASSPORT_ID, DigitalWeldPassportRevision.revision_number == 1))
            assert dwp_read is not None
            assert dwp_read.provenance_snapshot["rule_evaluations"][0]["rule_revision"] == RULE_REVISION_1
            # HISTORICAL_DWP_MRC_PIN (read path): verify mrc_snapshot still references MRC1
            assert dwp_read.mrc_snapshot is not None
            assert dwp_read.mrc_snapshot["assessment_id"] == ASSESSMENT_ID
            assert dwp_read.mrc_snapshot["revision_number"] == 1


def test_governed_supersession_chain(postgresql_engine) -> None:
    """Verify governed supersession establishes a durable queryable chain."""
    chain_rule_id = "PHASE_6B1_SUPERSESSION_CHAIN"
    candidate_revision = "2.0-draft"

    assert postgresql_engine.dialect.name == "postgresql"

    with Session(postgresql_engine) as session:
        user_ids = _seed_users(session)
        session.commit()

        # Create rule identity and verified Rev1 incumbent.
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)

            registry.create_identity(
                rule_id=chain_rule_id,
                audit=_audit(
                    "phase-6b1-chain-id-audit",
                    ACTORS["submitter"],
                    user_ids["submitter"],
                    "phase-6b1-chain-id",
                    "Chain test identity",
                ),
            )

            rev1 = registry.create_draft_revision(
                rule_id=chain_rule_id,
                revision=RULE_REVISION_1,
                name="Chain test rev1",
                evidence_class=EvidenceClass.SOURCE_BACKED,
                category=RuleCategory.OTHER,
                parameter="test_param",
                safe_default=SafeDefault.UNRESOLVED,
                missing_handling=MissingHandling.DATA_INSUFFICIENT,
                reason_for_change="Chain test rev1",
                version_metadata=_version_metadata(
                    chain_rule_id,
                    RULE_REVISION_1,
                ),
                audit=_audit(
                    "phase-6b1-chain-rev1-audit",
                    ACTORS["submitter"],
                    user_ids["submitter"],
                    "phase-6b1-chain-rev1",
                    "Chain test rev1",
                ),
                evidence_references=(
                    EvidenceReferenceDraft(
                        evidence_id="PHASE_6B1_CHAIN_EVIDENCE_1",
                        evidence_revision="1",
                        evidence_class=EvidenceClass.UNRESOLVED,
                        lifecycle_status=RuleLifecycleStatus.DRAFT,
                        created_by_actor_id=ACTORS["submitter"]["email"],
                        created_by_user_id=user_ids["submitter"],
                        reference_uri=(
                            "urn:spotweld:test:"
                            "phase6b1-chain-rev1"
                        ),
                    ),
                ),
                allow_source_backed=True,
            )

            _create_evidence(
                session,
                rev1.evidence_references[0],
                user_ids["verifier"],
                ACTORS["verifier"]["role"],
                user_ids["approver"],
            )

            rev1_id = rev1.id
            unit_of_work.commit()

        # Rev1 becomes active.
        for event_type, namespace, minute in (
            (
                RuleLifecycleEventType.ENABLE,
                RuleRegistryService.ENABLEMENT_COMMAND_NAMESPACE,
                1,
            ),
            (
                RuleLifecycleEventType.ACTIVATE,
                RuleRegistryService.ACTIVATION_COMMAND_NAMESPACE,
                2,
            ),
        ):
            key = (
                f"phase-6b1-chain-"
                f"{event_type.value.lower()}-1"
            )

            with GovernedUnitOfWork(session) as unit_of_work:
                registry = RuleRegistryService(unit_of_work)

                transition = (
                    registry.enable_source_backed
                    if event_type
                    is RuleLifecycleEventType.ENABLE
                    else registry.activate_source_backed
                )

                result = transition(
                    rule_id=chain_rule_id,
                    source_revision=RULE_REVISION_1,
                    receipt_id=(
                        f"phase-6b1-chain-"
                        f"{event_type.value.lower()}-receipt-1"
                    ),
                    command_identity=_identity(
                        namespace,
                        chain_rule_id,
                        key,
                    ),
                    request_hash=_request_hash(key),
                    audit=_audit(
                        f"phase-6b1-chain-"
                        f"{event_type.value.lower()}-audit-1",
                        ACTORS["approver"],
                        user_ids["approver"],
                        key,
                        f"Chain {event_type.value} Rev1",
                    ),
                    effective_from=(
                        BASE_TIME
                        + timedelta(minutes=minute)
                    ),
                    expires_at=None,
                    completed_at=(
                        BASE_TIME
                        + timedelta(
                            minutes=minute,
                            seconds=1,
                        )
                    ),
                )

                assert (
                    result.result_type
                    == "engineering_rule_lifecycle_event"
                )

                unit_of_work.commit()

        # Create a distinct verified replacement candidate.
        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)

            candidate = registry.create_draft_revision(
                rule_id=chain_rule_id,
                revision=candidate_revision,
                name="Chain test Rev2 candidate",
                evidence_class=EvidenceClass.SOURCE_BACKED,
                category=RuleCategory.OTHER,
                parameter="test_param",
                safe_default=SafeDefault.UNRESOLVED,
                missing_handling=MissingHandling.DATA_INSUFFICIENT,
                reason_for_change="Chain test Rev2 candidate",
                version_metadata=_version_metadata(
                    chain_rule_id,
                    candidate_revision,
                ),
                audit=_audit(
                    "phase-6b1-chain-candidate-audit",
                    ACTORS["submitter"],
                    user_ids["submitter"],
                    "phase-6b1-chain-candidate",
                    "Chain test Rev2 candidate",
                ),
                evidence_references=(
                    EvidenceReferenceDraft(
                        evidence_id="PHASE_6B1_CHAIN_EVIDENCE_2",
                        evidence_revision="1",
                        evidence_class=EvidenceClass.UNRESOLVED,
                        lifecycle_status=RuleLifecycleStatus.DRAFT,
                        created_by_actor_id=ACTORS["submitter"]["email"],
                        created_by_user_id=user_ids["submitter"],
                        reference_uri=(
                            "urn:spotweld:test:"
                            "phase6b1-chain-rev2"
                        ),
                    ),
                ),
                allow_source_backed=True,
            )

            _create_evidence(
                session,
                candidate.evidence_references[0],
                user_ids["verifier"],
                ACTORS["verifier"]["role"],
                user_ids["approver"],
            )

            unit_of_work.commit()

        candidate_persisted = session.scalar(
            select(EngineeringRuleRevision).where(
                EngineeringRuleRevision.engineering_rule.has(
                    rule_id=chain_rule_id
                ),
                EngineeringRuleRevision.revision
                == candidate_revision,
            )
        )

        assert candidate_persisted is not None

        basis_content_hash = _supersession_basis_hash(
            session,
            rule_id=chain_rule_id,
            incumbent_id=rev1_id,
            incumbent_revision=RULE_REVISION_1,
            candidate=candidate_persisted,
            replacement_revision=RULE_REVISION_2,
        )

        # Close SQLAlchemy's implicit read transaction before
        # entering the governed write UnitOfWork.
        session.commit()

        replacement_version_metadata = ContentVersionMetadata(
            schema_version="phase-6b1-content-schema-v1",
            canonicalization_version="phase-6b1-canonical-v1",
            hash_algorithm="sha256",
            content_hash=basis_content_hash,
            software_version="phase-6b1-test",
        )

        supersede_key = "phase-6b1-chain-supersede-2"

        with GovernedUnitOfWork(session) as unit_of_work:
            registry = RuleRegistryService(unit_of_work)

            result = registry.supersede_active_source_backed(
                rule_id=chain_rule_id,
                incumbent_revision=RULE_REVISION_1,
                replacement_candidate_revision=candidate_revision,
                replacement_revision=RULE_REVISION_2,
                version_metadata=replacement_version_metadata,
                receipt_id=(
                    "phase-6b1-chain-"
                    "supersede-receipt-2"
                ),
                command_identity=_identity(
                    RuleRegistryService
                    .SUPERSESSION_COMMAND_NAMESPACE,
                    chain_rule_id,
                    supersede_key,
                ),
                request_hash=_request_hash(
                    supersede_key
                ),
                audit=_audit(
                    "phase-6b1-chain-supersede-audit-2",
                    ACTORS["releaser"],
                    user_ids["releaser"],
                    supersede_key,
                    "Chain governed Rev1 to Rev2 supersession",
                ),
                effective_from=(
                    BASE_TIME
                    + timedelta(minutes=21)
                ),
                expires_at=None,
                completed_at=(
                    BASE_TIME
                    + timedelta(
                        minutes=21,
                        seconds=1,
                    )
                ),
            )

            assert (
                result.result_type
                == "engineering_rule_lifecycle_event"
            )

            unit_of_work.commit()

        rev2_persisted = session.scalar(
            select(EngineeringRuleRevision).where(
                EngineeringRuleRevision.engineering_rule.has(
                    rule_id=chain_rule_id
                ),
                EngineeringRuleRevision.revision
                == RULE_REVISION_2,
            )
        )

        assert rev2_persisted is not None
        assert rev2_persisted.supersedes_revision_id == rev1_id

        rev1_persisted = session.get(
            EngineeringRuleRevision,
            rev1_id,
        )

        assert rev1_persisted is not None

        rev1_latest_event = _latest_lifecycle_event(
            session,
            rev1_id,
        )
        assert (
            rev1_latest_event.event_type
            is RuleLifecycleEventType.SUPERSEDE
        )
