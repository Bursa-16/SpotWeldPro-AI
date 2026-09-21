"""Non-authoritative Registry identity and draft-revision orchestration."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from app.application.governed_audit_service import GovernedAuditService
from app.application.governed_idempotency_service import GovernedIdempotencyService
from app.application.governed_unit_of_work import GovernedUnitOfWork
from app.domain.governance_types import (
    ContentVersionMetadata,
    EvidenceClass,
    RuleLifecycleStatus,
)
from app.domain.idempotency_types import (
    CanonicalRequestHash,
    CommandIdentity,
    CommandResultReference,
    IdempotencyDisposition,
)
from app.domain.rule_applicability import (
    ApplicabilityResolutionOutcome,
    GovernedApplicabilityCandidate,
    GovernedApplicabilityContext,
    resolve_governed_applicability,
)
from app.domain.rule_registry_types import (
    EvidenceReferenceDraft,
    MissingHandling,
    RuleCategory,
    SafeDefault,
)
from app.domain.verification_types import VerificationDecisionOutcome
from app.models.entities import User
from app.models.rule_registry import (
    EngineeringRule,
    EngineeringRuleRevision,
    RuleLifecycleEvent,
    RuleLifecycleEventType,
)
from app.models.verification import EvidenceVerificationDecision
from app.repositories.rule_registry_repository import RuleRegistryRepository


@dataclass(frozen=True, slots=True)
class GovernedAuditMetadata:
    """Caller-supplied metadata supported by the existing audit schema.

    ``idempotency_key`` is trace metadata only.  The current schema does not
    provide authoritative idempotency uniqueness or command deduplication.
    """

    event_id: str
    actor_id: str
    actor_type: str
    reason: str
    correlation_id: str
    schema_version: str
    software_version: str
    canonicalization_version: str
    hash_algorithm: str
    created_at: datetime
    actor_user_id: int | None = None
    actor_role: str | None = None
    authority_scope: Mapping[str, object] | None = None
    idempotency_key: str | None = None
    detail: Mapping[str, object] | None = None


class RuleRegistryService:
    """Coordinate non-authoritative Registry drafts and governed audit."""

    COMMAND_NAMESPACE = "registry.rule.source_backed_promotion"
    ENABLEMENT_COMMAND_NAMESPACE = "registry.rule.enablement"
    ACTIVATION_COMMAND_NAMESPACE = "registry.rule.activation"
    SUPERSESSION_COMMAND_NAMESPACE = "registry.rule.source_backed_supersession"

    def __init__(self, unit_of_work: GovernedUnitOfWork):
        self._unit_of_work = unit_of_work
        self._repository = RuleRegistryRepository(unit_of_work.session)
        self._idempotency = GovernedIdempotencyService(unit_of_work)
        self._audit = GovernedAuditService(unit_of_work)

    def create_identity(
        self,
        *,
        rule_id: str,
        audit: GovernedAuditMetadata,
    ) -> EngineeringRule:
        """Create a stable Registry identity without engineering authority."""
        self._unit_of_work.ensure_open()
        rule = self._repository.create_rule(
            rule_id=rule_id,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule",
            entity_id=rule_id,
            entity_revision="identity",
            action="CREATE_RULE_IDENTITY",
            prior_content_hash=None,
            new_content_hash=None,
            detail=self._audit_detail(
                audit,
                command="CREATE_RULE_IDENTITY",
                rule_id=rule_id,
            ),
        )
        return rule

    def create_draft_revision(
        self,
        *,
        rule_id: str,
        revision: str,
        name: str,
        evidence_class: EvidenceClass,
        category: RuleCategory,
        parameter: str,
        safe_default: SafeDefault,
        missing_handling: MissingHandling,
        reason_for_change: str,
        version_metadata: ContentVersionMetadata,
        audit: GovernedAuditMetadata,
        evidence_references: Sequence[EvidenceReferenceDraft] = (),
        applicability_metadata: dict | None = None,
        applicability_schema_version: str | None = None,
        description: str | None = None,
        note: str | None = None,
        enabled: bool = False,
        allow_source_backed: bool = False,
    ) -> EngineeringRuleRevision:
        """Create a DRAFT revision; repository authority guards remain final."""
        self._unit_of_work.ensure_open()
        rule = self._repository.get_by_rule_id(rule_id)
        if rule is None:
            raise ValueError(f"engineering rule identity does not exist: {rule_id}")

        rule_revision = self._repository.create_revision(
            engineering_rule=rule,
            revision=revision,
            name=name,
            status=RuleLifecycleStatus.DRAFT,
            evidence_class=evidence_class,
            category=category,
            parameter=parameter,
            safe_default=safe_default,
            missing_handling=missing_handling,
            enabled=enabled,
            reason_for_change=reason_for_change,
            version_metadata=version_metadata,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            evidence_references=evidence_references,
            applicability_metadata=applicability_metadata,
            applicability_schema_version=applicability_schema_version,
            description=description,
            note=note,
            allow_source_backed=allow_source_backed,
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_revision",
            entity_id=rule_id,
            entity_revision=revision,
            action="CREATE_DRAFT_RULE_REVISION",
            prior_content_hash=None,
            new_content_hash=version_metadata.content_hash,
            detail=self._audit_detail(
                audit,
                command="CREATE_DRAFT_RULE_REVISION",
                rule_id=rule_id,
                revision=revision,
                lifecycle_status=RuleLifecycleStatus.DRAFT.value,
                evidence_class=evidence_class.value,
                enabled=enabled,
            ),
        )
        return rule_revision

    def promote_source_backed(
        self,
        *,
        rule_id: str,
        source_revision: str,
        revision: str,
        version_metadata: ContentVersionMetadata,
        receipt_id: str,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        audit: GovernedAuditMetadata,
        completed_at: datetime,
    ) -> CommandResultReference:
        """Promote one draft revision to SOURCE_BACKED with durable idempotency."""
        self._unit_of_work.ensure_open()
        if command_identity.command_namespace != self.COMMAND_NAMESPACE:
            raise ValueError("source-backed promotion command namespace mismatch")
        if command_identity.command_scope != rule_id:
            raise ValueError("source-backed promotion command scope must match rule_id")
        decision = self._idempotency.reserve_or_inspect(
            receipt_id=receipt_id,
            identity=command_identity,
            request_hash=request_hash,
            correlation_id=audit.correlation_id,
            schema_version=audit.schema_version,
            software_version=audit.software_version,
            created_at=audit.created_at,
        )
        if decision.disposition is IdempotencyDisposition.REPLAY:
            if decision.result_reference is None:
                raise RuntimeError("completed source-backed replay has no durable result")
            return decision.result_reference
        if decision.disposition is IdempotencyDisposition.CONFLICT:
            raise ValueError("idempotency conflict for source-backed promotion command")
        if decision.disposition is IdempotencyDisposition.IN_PROGRESS:
            raise RuntimeError("source-backed promotion command is already in progress")
        if audit.actor_type != "user" or audit.actor_user_id is None:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="NON_HUMAN_PROMOTER",
                denial_reason="source-backed promotion requires a human user",
            )

        rule = self._repository.get_by_rule_id(rule_id)
        if rule is None:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_RULE_IDENTITY",
                denial_reason="engineering rule identity does not exist",
            )

        source = self._repository.get_revision(rule_id, source_revision)
        if source is None:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_SOURCE_REVISION",
                denial_reason="source draft revision does not exist",
            )
        if source.status is not RuleLifecycleStatus.DRAFT:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SOURCE_REVISION_NOT_DRAFT",
                denial_reason="only a DRAFT revision can be promoted to SOURCE_BACKED",
            )
        if source.evidence_class is EvidenceClass.SOURCE_BACKED:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SOURCE_ALREADY_BACKED",
                denial_reason="source revision is already SOURCE_BACKED",
            )
        if source.created_by_user_id is None:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_SOURCE_SUBMITTER",
                denial_reason="source revision lacks durable human submitter identity",
            )
        if source.created_by_user_id == audit.actor_user_id:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SEPARATION_OF_DUTIES_VIOLATION",
                denial_reason="source submitter must not execute the promotion",
            )
        if source.revision == revision:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SOURCE_AND_TARGET_REVISION_MATCH",
                denial_reason="promoted revision must differ from the source revision",
            )

        source_evidence_references = list(source.evidence_references)
        if not source_evidence_references:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_EVIDENCE_REFERENCES",
                denial_reason="source-backed promotion requires verified evidence references",
            )

        verified_decisions: list[
            tuple[EvidenceReferenceDraft, EvidenceVerificationDecision]
        ] = []
        source_scope = dict(audit.authority_scope) if audit.authority_scope is not None else None
        if source_scope is None:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_AUTHORITY_SCOPE",
                denial_reason="source-backed promotion requires an explicit authority scope",
            )

        for evidence_reference in source_evidence_references:
            verified_decision = self._repository.get_latest_verified_evidence_decision(
                evidence_reference_id=evidence_reference.id
            )
            if verified_decision is None:
                return self._deny_source_backed_promotion(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    revision=revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="UNVERIFIED_EVIDENCE_REFERENCE",
                    denial_reason="each source evidence reference must have a VERIFIED decision",
                )
            if verified_decision.decision_outcome is not VerificationDecisionOutcome.VERIFIED:
                return self._deny_source_backed_promotion(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    revision=revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="INVALID_VERIFICATION_OUTCOME",
                    denial_reason="each source evidence reference must have a VERIFIED decision",
                )
            if verified_decision.verifier_user_id == audit.actor_user_id:
                return self._deny_source_backed_promotion(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    revision=revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="VERIFIER_EXECUTED_PROMOTION",
                    denial_reason="promotion executor must not be the evidence verifier",
                )
            verified_scope = verified_decision.authority_snapshot.get("resource_scope")
            if verified_scope != source_scope:
                return self._deny_source_backed_promotion(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    revision=revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="AUTHORITY_SCOPE_MISMATCH",
                    denial_reason="verified evidence scope must match the promotion scope",
                )
            verified_decisions.append((evidence_reference, verified_decision))

        expected_content_hash = self._hash(
            {
                "rule_id": rule_id,
                "source_revision": source.revision,
                "source_revision_id": source.id,
                "target_revision": revision,
                "source_content_hash": source.content_hash,
                "authority_scope": source_scope,
                "evidence_pins": [
                    {
                        "evidence_reference_id": evidence_reference.id,
                        "evidence_id": evidence_reference.evidence_id,
                        "evidence_revision": evidence_reference.evidence_revision,
                        "verification_decision_id": verified_decision.id,
                        "verification_revision_number": verified_decision.revision_number,
                        "verifier_user_id": verified_decision.verifier_user_id,
                    }
                    for evidence_reference, verified_decision in verified_decisions
                ],
            }
        )
        if version_metadata.content_hash != expected_content_hash:
            return self._deny_source_backed_promotion(
                rule_id=rule_id,
                source_revision=source_revision,
                revision=revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="CONTENT_HASH_MISMATCH",
                denial_reason="source-backed revision hash must pin the exact evidence revision set",
            )

        promoted_revision = self._repository.create_revision(
            engineering_rule=rule,
            revision=revision,
            name=source.name,
            status=RuleLifecycleStatus.DRAFT,
            evidence_class=EvidenceClass.SOURCE_BACKED,
            category=source.category,
            parameter=source.parameter,
            operator=source.operator,
            min_value=source.min_value,
            max_value=source.max_value,
            unit=source.unit,
            applicability_metadata=source.applicability_metadata,
            applicability_schema_version=source.applicability_schema_version,
            effective_date=source.effective_date,
            expiry_date=source.expiry_date,
            supersedes_revision_id=source.id,
            source_type=source.source_type,
            source_name=source.source_name,
            source_document=source.source_document,
            source_url=source.source_url,
            safe_default=source.safe_default,
            missing_handling=source.missing_handling,
            conflict_handling=source.conflict_handling,
            unit_mismatch_handling=source.unit_mismatch_handling,
            description=source.description,
            note=source.note,
            enabled=False,
            reason_for_change=audit.reason,
            version_metadata=version_metadata,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            evidence_references=tuple(
                EvidenceReferenceDraft(
                    evidence_id=evidence_reference.evidence_id,
                    evidence_revision=evidence_reference.evidence_revision,
                    evidence_class=evidence_reference.evidence_class,
                    lifecycle_status=evidence_reference.lifecycle_status,
                    created_by_actor_id=evidence_reference.created_by_actor_id,
                    created_by_user_id=evidence_reference.created_by_user_id,
                    source_type=evidence_reference.source_type,
                    source_name=evidence_reference.source_name,
                    source_document=evidence_reference.source_document,
                    edition=evidence_reference.edition,
                    section_reference=evidence_reference.section_reference,
                    page_reference=evidence_reference.page_reference,
                    table_reference=evidence_reference.table_reference,
                    reference_uri=evidence_reference.reference_uri,
                    reference_metadata=evidence_reference.reference_metadata,
                    schema_version=evidence_reference.schema_version,
                    hash_algorithm=evidence_reference.hash_algorithm,
                    content_hash=evidence_reference.content_hash,
                )
                for evidence_reference, _verified_decision in verified_decisions
            ),
            allow_source_backed=True,
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_revision",
            entity_id=rule_id,
            entity_revision=revision,
            action="PROMOTE_SOURCE_BACKED_RULE_REVISION",
            prior_content_hash=source.content_hash,
            new_content_hash=version_metadata.content_hash,
            detail=self._audit_detail(
                audit,
                command="PROMOTE_SOURCE_BACKED_RULE_REVISION",
                rule_id=rule_id,
                source_revision=source.revision,
                source_revision_id=source.id,
                source_revision_content_hash=source.content_hash,
                target_revision=revision,
                evidence_reference_ids=[
                    evidence_reference.id for evidence_reference, _ in verified_decisions
                ],
                verification_decision_ids=[
                    verified_decision.id for _evidence_reference, verified_decision in verified_decisions
                ],
                authority_scope=source_scope,
                promoted_content_hash=version_metadata.content_hash,
            ),
        )
        result = CommandResultReference(
            result_type="engineering_rule_revision",
            result_id=str(promoted_revision.id),
            result_revision=promoted_revision.revision,
        )
        completed = self._idempotency.complete(
            identity=command_identity,
            request_hash=request_hash,
            result_reference=result,
            completed_at=completed_at,
        )
        if completed.result_reference != result:
            raise RuntimeError("source-backed promotion idempotency completion failed")
        return result

    def enable_source_backed(
        self,
        *,
        rule_id: str,
        source_revision: str,
        receipt_id: str,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        audit: GovernedAuditMetadata,
        effective_from: datetime,
        expires_at: datetime | None,
        completed_at: datetime,
    ) -> CommandResultReference:
        return self._governed_source_backed_lifecycle_transition(
            rule_id=rule_id,
            source_revision=source_revision,
            receipt_id=receipt_id,
            command_identity=command_identity,
            request_hash=request_hash,
            audit=audit,
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
            command_namespace=self.ENABLEMENT_COMMAND_NAMESPACE,
            event_type=RuleLifecycleEventType.ENABLE,
            audit_action="ENABLE_SOURCE_BACKED_RULE_REVISION",
            denial_action="AUTHORIZE_SOURCE_BACKED_ENABLEMENT_DENIED",
        )

    def activate_source_backed(
        self,
        *,
        rule_id: str,
        source_revision: str,
        receipt_id: str,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        audit: GovernedAuditMetadata,
        effective_from: datetime,
        expires_at: datetime | None,
        completed_at: datetime,
    ) -> CommandResultReference:
        return self._governed_source_backed_lifecycle_transition(
            rule_id=rule_id,
            source_revision=source_revision,
            receipt_id=receipt_id,
            command_identity=command_identity,
            request_hash=request_hash,
            audit=audit,
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
            command_namespace=self.ACTIVATION_COMMAND_NAMESPACE,
            event_type=RuleLifecycleEventType.ACTIVATE,
            audit_action="ACTIVATE_SOURCE_BACKED_RULE_REVISION",
            denial_action="AUTHORIZE_SOURCE_BACKED_ACTIVATION_DENIED",
        )

    def resolve_current_applicable_revision(
        self,
        *,
        rule_id: str,
        scope: GovernedApplicabilityContext,
        as_of: datetime,
    ) -> EngineeringRuleRevision:
        """Resolve the single CURRENT authoritative revision for ``rule_id`` (read-only).

        Deterministic read-only projection of governed lifecycle authority.
        For every persisted revision of the rule the resolver derives the
        current lifecycle state from that revision's latest committed
        lifecycle event:

        * ``ENABLE``       -> enabled, not yet active
        * ``ACTIVATE``     -> enabled and active
        * ``SUPERSEDE``    -> retired and superseded
        * ``REVOKE``       -> retired and revoked
        * ``SUSPEND``      -> retired and suspended
        * ``EXPIRE``       -> retired by expiry
        * ``DEPRECATE``    -> retired and deprecated
        * ``CORRECT``      -> content basis invalidated

        Candidate revisions are then matched against the explicit requested
        ``scope`` and ``as_of`` window using the existing pure governed
        resolver:

        * exactly one winner        -> returns that ``EngineeringRuleRevision``
        * zero winners              -> ``ValueError`` (no applicable revision)
        * multiple equal winners    -> ``ValueError`` as explicit ambiguity;
          a winner is NEVER selected silently.

        The resolver never mutates revision rows, lifecycle events, or any
        historical Evaluation / MRC / DWP records.
        """
        self._unit_of_work.ensure_open()
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        rule = self._repository.get_by_rule_id(rule_id)
        if rule is None:
            raise ValueError(f"engineering rule identity does not exist: {rule_id}")
        revisions = self._repository.list_revisions(rule_id)
        latest_event_by_revision: dict[int, RuleLifecycleEvent] = {}
        for lifecycle_event in self._repository.list_lifecycle_events(rule_id):
            current = latest_event_by_revision.get(
                lifecycle_event.engineering_rule_revision_id
            )
            if current is None or (
                lifecycle_event.revision_number,
                lifecycle_event.id,
            ) > (current.revision_number, current.id):
                latest_event_by_revision[
                    lifecycle_event.engineering_rule_revision_id
                ] = lifecycle_event

        candidates: list[GovernedApplicabilityCandidate] = []
        for revision in revisions:
            lifecycle_event = latest_event_by_revision.get(revision.id)
            if lifecycle_event is None:
                continue
            event_type = lifecycle_event.event_type
            scope_snapshot = {
                key: (value,) if isinstance(value, str) else tuple(value)
                for key, value in (lifecycle_event.scope_snapshot or {}).items()
            }
            candidates.append(
                GovernedApplicabilityCandidate(
                    candidate_id=f"{rule_id}:{revision.revision}",
                    rule_id=rule_id,
                    revision=revision.revision,
                    evidence_class=revision.evidence_class,
                    enabled=event_type
                    in {
                        RuleLifecycleEventType.ENABLE,
                        RuleLifecycleEventType.ACTIVATE,
                    },
                    active=event_type is RuleLifecycleEventType.ACTIVATE,
                    scope_snapshot=scope_snapshot,
                    effective_from=lifecycle_event.effective_from,
                    expires_at=lifecycle_event.expires_at,
                    suspended=event_type is RuleLifecycleEventType.SUSPEND,
                    revoked=event_type is RuleLifecycleEventType.REVOKE,
                    superseded=event_type is RuleLifecycleEventType.SUPERSEDE,
                    basis_valid=event_type is not RuleLifecycleEventType.CORRECT,
                )
            )

        resolution = resolve_governed_applicability(scope, as_of, candidates)
        if resolution.outcome is ApplicabilityResolutionOutcome.CONFLICT:
            raise ValueError(
                "ambiguous governed applicability for rule "
                f"{rule_id}: " + ", ".join(resolution.conflict_candidate_ids)
            )
        if resolution.outcome is not ApplicabilityResolutionOutcome.SELECTED:
            raise ValueError(
                f"no applicable governed revision for rule {rule_id} "
                f"at {as_of.isoformat()}"
            )
        return next(
            revision
            for revision in revisions
            if f"{rule_id}:{revision.revision}"
            == resolution.selected_candidate_id
        )

    @staticmethod
    def _common_audit_fields(audit: GovernedAuditMetadata) -> dict[str, object]:
        return {
            "event_id": audit.event_id,
            "actor_id": audit.actor_id,
            "actor_type": audit.actor_type,
            "reason": audit.reason,
            "correlation_id": audit.correlation_id,
            "schema_version": audit.schema_version,
            "software_version": audit.software_version,
            "canonicalization_version": audit.canonicalization_version,
            "hash_algorithm": audit.hash_algorithm,
            "created_at": audit.created_at,
            "actor_user_id": audit.actor_user_id,
            "actor_role": audit.actor_role,
            "authority_scope": audit.authority_scope,
            "idempotency_key": audit.idempotency_key,
        }

    @staticmethod
    def _audit_detail(
        audit: GovernedAuditMetadata,
        **command_detail: object,
    ) -> dict[str, object]:
        detail = dict(audit.detail) if audit.detail is not None else {}
        detail.update(command_detail)
        return detail

    @staticmethod
    def _hash(value: object) -> str:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _governed_source_backed_lifecycle_transition(
        self,
        *,
        rule_id: str,
        source_revision: str,
        receipt_id: str,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        audit: GovernedAuditMetadata,
        effective_from: datetime,
        expires_at: datetime | None,
        completed_at: datetime,
        command_namespace: str,
        event_type: RuleLifecycleEventType,
        audit_action: str,
        denial_action: str,
    ) -> CommandResultReference:
        self._unit_of_work.ensure_open()
        if command_identity.command_namespace != command_namespace:
            raise ValueError("source-backed lifecycle command namespace mismatch")
        if command_identity.command_scope != rule_id:
            raise ValueError("source-backed lifecycle command scope must match rule_id")
        decision = self._idempotency.reserve_or_inspect(
            receipt_id=receipt_id,
            identity=command_identity,
            request_hash=request_hash,
            correlation_id=audit.correlation_id,
            schema_version=audit.schema_version,
            software_version=audit.software_version,
            created_at=audit.created_at,
        )
        if decision.disposition is IdempotencyDisposition.REPLAY:
            if decision.result_reference is None:
                raise RuntimeError("completed lifecycle replay has no durable result")
            return decision.result_reference
        if decision.disposition is IdempotencyDisposition.CONFLICT:
            raise ValueError("idempotency conflict for source-backed lifecycle command")
        if decision.disposition is IdempotencyDisposition.IN_PROGRESS:
            raise RuntimeError("source-backed lifecycle command is already in progress")
        actor = self._repository.session.get(User, audit.actor_user_id) if audit.actor_user_id is not None else None
        if audit.actor_type != "user" or actor is None or not actor.is_active:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="NON_HUMAN_OR_INACTIVE_ACTOR",
                denial_reason="source-backed lifecycle requires an active durable human user",
            )

        rule = self._repository.get_by_rule_id(rule_id)
        if rule is None:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="MISSING_RULE_IDENTITY",
                denial_reason="engineering rule identity does not exist",
            )

        source = self._repository.get_revision(rule_id, source_revision)
        if source is None:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="MISSING_SOURCE_REVISION",
                denial_reason="source-backed revision does not exist",
            )
        if source.status is not RuleLifecycleStatus.DRAFT:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="SOURCE_REVISION_NOT_DRAFT",
                denial_reason="only a DRAFT revision can be enabled or activated",
            )
        if source.evidence_class is not EvidenceClass.SOURCE_BACKED:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="SOURCE_REVISION_NOT_SOURCE_BACKED",
                denial_reason="lifecycle transition requires a SOURCE_BACKED revision",
            )
        if source.created_by_user_id is None:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="MISSING_SOURCE_SUBMITTER",
                denial_reason="source-backed revision lacks durable human submitter identity",
            )
        if source.created_by_user_id == actor.id:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="SEPARATION_OF_DUTIES_VIOLATION",
                denial_reason="source submitter must not perform the lifecycle transition",
            )

        scope_snapshot = dict(audit.authority_scope) if audit.authority_scope is not None else None
        if scope_snapshot is None or not any(value is not None for value in scope_snapshot.values()):
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="MISSING_SCOPE_SNAPSHOT",
                denial_reason="source-backed lifecycle requires an explicit non-empty scope snapshot",
            )

        basis = self._resolve_source_backed_basis(
            rule_id=rule_id,
            source=source,
            scope_snapshot=scope_snapshot,
            actor_user_id=actor.id,
            audit=audit,
            completed_at=completed_at,
            command_identity=command_identity,
            request_hash=request_hash,
            denial_action=denial_action,
        )
        if basis is None:
            return self._deny_source_backed_lifecycle(
                rule_id=rule_id,
                source_revision=source_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_action=denial_action,
                denial_code="UNRESOLVED_BASIS",
                denial_reason="source-backed lifecycle basis could not be resolved",
            )
        basis_snapshot, _verified_decisions = basis

        latest_lifecycle_event = self._repository.get_latest_lifecycle_event(
            engineering_rule_revision_id=source.id,
            scope_snapshot=scope_snapshot,
            event_types=(
                RuleLifecycleEventType.ENABLE,
                RuleLifecycleEventType.ACTIVATE,
            ),
        )
        if event_type is RuleLifecycleEventType.ENABLE:
            if latest_lifecycle_event is not None:
                return self._deny_source_backed_lifecycle(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_action=denial_action,
                    denial_code="ALREADY_ENABLED_OR_ACTIVE",
                    denial_reason="source-backed revision already has an enablement or activation event for this scope",
                )
        else:
            if latest_lifecycle_event is None:
                return self._deny_source_backed_lifecycle(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_action=denial_action,
                    denial_code="MISSING_ENABLEMENT",
                    denial_reason="activation requires an existing enablement event for the exact revision and scope",
                )
            if latest_lifecycle_event.event_type is RuleLifecycleEventType.ACTIVATE:
                return self._deny_source_backed_lifecycle(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_action=denial_action,
                    denial_code="ALREADY_ACTIVE",
                    denial_reason="source-backed revision is already active for this scope",
                )
            enabled_basis = latest_lifecycle_event.basis_snapshot
            if enabled_basis.get("content_hash") != basis_snapshot["content_hash"]:
                return self._deny_source_backed_lifecycle(
                    rule_id=rule_id,
                    source_revision=source_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_action=denial_action,
                    denial_code="BASIS_INVALIDATED",
                    denial_reason="source-backed enablement basis was superseded or corrected",
                )

        lifecycle_event_id = self._lifecycle_event_identity(
            rule_id=rule_id,
            source_revision=source,
            event_type=event_type,
            scope_snapshot=scope_snapshot,
        )
        authority_snapshot = self._lifecycle_authority_snapshot(
            audit=audit,
            event_type=event_type,
            scope_snapshot=scope_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
        )
        transition_content_hash = self._hash(
            {
                "lifecycle_event_id": lifecycle_event_id,
                "event_type": event_type.value,
                "rule_id": rule_id,
                "source_revision_id": source.id,
                "source_revision": source.revision,
                "scope_snapshot": scope_snapshot,
                "basis_content_hash": basis_snapshot["content_hash"],
                "authority_snapshot": authority_snapshot,
                "effective_from": effective_from,
                "expires_at": expires_at,
            }
        )
        lifecycle_event = self._repository.create_lifecycle_event(
            engineering_rule=rule,
            engineering_rule_revision=source,
            lifecycle_event_id=lifecycle_event_id,
            revision_number=1,
            event_type=event_type,
            scope_snapshot=scope_snapshot,
            basis_snapshot=basis_snapshot,
            authority_snapshot=authority_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            schema_version="rule-lifecycle-v1",
            canonicalization_version="rule-lifecycle-canonical-v1",
            hash_algorithm="sha256",
            content_hash=transition_content_hash,
            software_version=audit.software_version,
            correlation_id=audit.correlation_id,
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_lifecycle_event",
            entity_id=rule_id,
            entity_revision=source.revision,
            action=audit_action,
            prior_content_hash=source.content_hash,
            new_content_hash=lifecycle_event.content_hash,
            detail=self._audit_detail(
                audit,
                command=audit_action,
                rule_id=rule_id,
                source_revision=source.revision,
                source_revision_id=source.id,
                lifecycle_event_id=lifecycle_event.lifecycle_event_id,
                event_type=event_type.value,
                scope_snapshot=scope_snapshot,
                basis_content_hash=basis_snapshot["content_hash"],
                basis_revision_ids=[
                    pin["evidence_reference_id"] for pin in basis_snapshot["evidence_pins"]
                ],
                verification_decision_ids=[
                    pin["verification_decision_id"] for pin in basis_snapshot["evidence_pins"]
                ],
            ),
        )
        result = CommandResultReference(
            result_type="engineering_rule_lifecycle_event",
            result_id=str(lifecycle_event.id),
            result_revision=str(lifecycle_event.revision_number),
        )
        completed = self._idempotency.complete(
            identity=command_identity,
            request_hash=request_hash,
            result_reference=result,
            completed_at=completed_at,
        )
        if completed.result_reference != result:
            raise RuntimeError("source-backed lifecycle idempotency completion failed")
        return result

    def _resolve_source_backed_basis(
        self,
        *,
        rule_id: str,
        source: EngineeringRuleRevision,
        scope_snapshot: dict[str, object],
        actor_user_id: int,
        audit: GovernedAuditMetadata,
        completed_at: datetime,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        denial_action: str,
    ) -> tuple[dict[str, object], list[tuple[EvidenceReferenceDraft, EvidenceVerificationDecision]]] | None:
        if any(candidate.supersedes_revision_id == source.id for candidate in self._repository.list_revisions(rule_id)):
            return None

        source_evidence_references = list(source.evidence_references)
        if not source_evidence_references:
            return None

        verified_decisions: list[
            tuple[EvidenceReferenceDraft, EvidenceVerificationDecision]
        ] = []
        for evidence_reference in sorted(
            source_evidence_references,
            key=lambda reference: (reference.evidence_id, reference.evidence_revision, reference.id),
        ):
            verified_decision = self._repository.get_latest_verified_evidence_decision(
                evidence_reference_id=evidence_reference.id
            )
            if verified_decision is None:
                return None
            if verified_decision.decision_outcome is not VerificationDecisionOutcome.VERIFIED:
                return None
            if verified_decision.verifier_user_id == actor_user_id:
                return None
            verified_scope = verified_decision.authority_snapshot.get("resource_scope")
            if verified_scope != scope_snapshot:
                return None
            verified_decisions.append((evidence_reference, verified_decision))

        basis_snapshot = {
            "rule_id": rule_id,
            "source_revision_id": source.id,
            "source_revision": source.revision,
            "source_content_hash": source.content_hash,
            "scope_snapshot": scope_snapshot,
            "evidence_pins": [
                {
                    "evidence_reference_id": evidence_reference.id,
                    "evidence_id": evidence_reference.evidence_id,
                    "evidence_revision": evidence_reference.evidence_revision,
                    "verification_decision_id": verified_decision.id,
                    "verification_revision_number": verified_decision.revision_number,
                    "verification_decision_content_hash": verified_decision.content_hash,
                    "verification_authority_snapshot_hash": verified_decision.authority_snapshot_content_hash,
                    "verifier_user_id": verified_decision.verifier_user_id,
                }
                for evidence_reference, verified_decision in verified_decisions
            ],
        }
        basis_snapshot["content_hash"] = self._hash(basis_snapshot)
        return basis_snapshot, verified_decisions

    def supersede_active_source_backed(
        self,
        *,
        rule_id: str,
        incumbent_revision: str,
        replacement_candidate_revision: str,
        replacement_revision: str,
        version_metadata: ContentVersionMetadata,
        receipt_id: str,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        audit: GovernedAuditMetadata,
        effective_from: datetime,
        expires_at: datetime | None,
        completed_at: datetime,
    ) -> CommandResultReference:
        """Governed supersession of an ACTIVE SOURCE_BACKED revision (Phase 6B2A).

        Creates a NEW authoritative replacement revision whose
        ``supersedes_revision_id`` pins the incumbent revision row at creation
        time (revision rows are immutable), retires the incumbent with a
        SUPERSEDE lifecycle event, and enables/activates the replacement in
        the same transaction.  Neither the incumbent row nor the validated
        draft candidate row is mutated.
        """
        self._unit_of_work.ensure_open()
        if command_identity.command_namespace != self.SUPERSESSION_COMMAND_NAMESPACE:
            raise ValueError("supersession command namespace mismatch")
        if command_identity.command_scope != rule_id:
            raise ValueError("supersession command scope must match rule_id")
        decision = self._idempotency.reserve_or_inspect(
            receipt_id=receipt_id,
            identity=command_identity,
            request_hash=request_hash,
            correlation_id=audit.correlation_id,
            schema_version=audit.schema_version,
            software_version=audit.software_version,
            created_at=audit.created_at,
        )
        if decision.disposition is IdempotencyDisposition.REPLAY:
            if decision.result_reference is None:
                raise RuntimeError("completed supersession replay has no durable result")
            return decision.result_reference
        if decision.disposition is IdempotencyDisposition.CONFLICT:
            raise ValueError("idempotency conflict for supersession command")
        if decision.disposition is IdempotencyDisposition.IN_PROGRESS:
            raise RuntimeError("supersession command is already in progress")

        actor = (
            self._repository.session.get(User, audit.actor_user_id)
            if audit.actor_user_id is not None
            else None
        )
        if audit.actor_type != "user" or actor is None or not actor.is_active:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="NON_HUMAN_OR_INACTIVE_ACTOR",
                denial_reason="active revision supersession requires an active durable human user",
            )
        rule = self._repository.get_by_rule_id(rule_id)
        if rule is None:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_RULE_IDENTITY",
                denial_reason="engineering rule identity does not exist",
            )
        incumbent = self._repository.lock_revision(
            rule_id=rule_id,
            revision=incumbent_revision,
        )
        if incumbent is None:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_INCUMBENT_REVISION",
                denial_reason="incumbent revision does not exist",
            )
        if incumbent.engineering_rule_id != rule.id:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_INCUMBENT_REVISION",
                denial_reason="incumbent revision does not belong to the rule identity",
            )
        if incumbent.evidence_class is not EvidenceClass.SOURCE_BACKED:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="INCUMBENT_NOT_SOURCE_BACKED",
                denial_reason="supersession requires a SOURCE_BACKED incumbent revision",
            )
        if incumbent.revision == replacement_revision:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SOURCE_AND_TARGET_REVISION_MATCH",
                denial_reason="replacement revision must differ from the incumbent revision",
            )
        successor = self._repository.find_successor(incumbent_revision_id=incumbent.id)
        if successor is not None:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="INCUMBENT_ALREADY_SUPERSEDED",
                denial_reason="incumbent revision is already superseded by a successor revision",
            )
        scope_snapshot = dict(audit.authority_scope) if audit.authority_scope is not None else None
        if scope_snapshot is None or not any(value is not None for value in scope_snapshot.values()):
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_SCOPE_SNAPSHOT",
                denial_reason="supersession requires an explicit non-empty authority scope snapshot",
            )
        incumbent_latest = self._repository.get_latest_lifecycle_event(
            engineering_rule_revision_id=incumbent.id,
            scope_snapshot=scope_snapshot,
        )
        if (
            incumbent_latest is None
            or incumbent_latest.event_type is not RuleLifecycleEventType.ACTIVATE
        ):
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="INCUMBENT_NOT_ACTIVE",
                denial_reason="supersession requires an incumbent with a current ACTIVATE lifecycle event for the exact authority scope",
            )
        if incumbent_latest.expires_at is not None and incumbent_latest.expires_at <= completed_at:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="INCUMBENT_NOT_ACTIVE",
                denial_reason="incumbent activation authority window has expired",
            )
        if incumbent.created_by_user_id is None:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_INCUMBENT_SUBMITTER",
                denial_reason="incumbent revision lacks durable human submitter identity",
            )
        if incumbent.created_by_user_id == actor.id:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SEPARATION_OF_DUTIES_VIOLATION",
                denial_reason="incumbent submitter must not execute the supersession",
            )
        replacement_candidate = self._repository.get_revision(
            rule_id,
            replacement_candidate_revision,
        )
        if replacement_candidate is None:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_REPLACEMENT_CANDIDATE",
                denial_reason="replacement draft candidate revision does not exist",
            )
        if replacement_candidate.id == incumbent.id:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="REPLACEMENT_CANDIDATE_INVALID",
                denial_reason="replacement candidate must differ from the incumbent revision row",
            )
        if replacement_candidate.status is not RuleLifecycleStatus.DRAFT:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="REPLACEMENT_CANDIDATE_NOT_DRAFT",
                denial_reason="only a DRAFT candidate can seed the superseding revision",
            )
        if replacement_candidate.evidence_class is not EvidenceClass.SOURCE_BACKED:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="REPLACEMENT_CANDIDATE_NOT_SOURCE_BACKED",
                denial_reason="replacement candidate must follow the source-backed evidence workflow",
            )
        if replacement_candidate.created_by_user_id is None:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_REPLACEMENT_SUBMITTER",
                denial_reason="replacement candidate lacks durable human submitter identity",
            )
        if replacement_candidate.created_by_user_id == actor.id:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="SEPARATION_OF_DUTIES_VIOLATION",
                denial_reason="replacement draft submitter must not execute the supersession",
            )
        replacement_candidate_evidence_references = list(
            replacement_candidate.evidence_references
        )
        if not replacement_candidate_evidence_references:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="MISSING_EVIDENCE_REFERENCES",
                denial_reason="replacement candidate carries no evidence references",
            )
        verified_decisions: list[
            tuple[EvidenceReferenceDraft, EvidenceVerificationDecision]
        ] = []
        for evidence_reference in sorted(
            replacement_candidate_evidence_references,
            key=lambda reference: (
                reference.evidence_id,
                reference.evidence_revision,
                reference.id,
            ),
        ):
            verified_decision = self._repository.get_latest_verified_evidence_decision(
                evidence_reference_id=evidence_reference.id
            )
            if verified_decision is None:
                return self._deny_active_supersession(
                    rule_id=rule_id,
                    incumbent_revision=incumbent_revision,
                    replacement_candidate_revision=replacement_candidate_revision,
                    replacement_revision=replacement_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="UNVERIFIED_EVIDENCE_REFERENCE",
                    denial_reason="replacement candidate evidence lacks a VERIFIED decision",
                )
            if verified_decision.decision_outcome is not VerificationDecisionOutcome.VERIFIED:
                return self._deny_active_supersession(
                    rule_id=rule_id,
                    incumbent_revision=incumbent_revision,
                    replacement_candidate_revision=replacement_candidate_revision,
                    replacement_revision=replacement_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="INVALID_VERIFICATION_OUTCOME",
                    denial_reason="replacement candidate evidence must have a VERIFIED decision",
                )
            if verified_decision.verifier_user_id == actor.id:
                return self._deny_active_supersession(
                    rule_id=rule_id,
                    incumbent_revision=incumbent_revision,
                    replacement_candidate_revision=replacement_candidate_revision,
                    replacement_revision=replacement_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="VERIFIER_EXECUTED_SUPERSESSION",
                    denial_reason="supersession executor must not be the evidence verifier",
                )
            verified_scope = verified_decision.authority_snapshot.get("resource_scope")
            if verified_scope != scope_snapshot:
                return self._deny_active_supersession(
                    rule_id=rule_id,
                    incumbent_revision=incumbent_revision,
                    replacement_candidate_revision=replacement_candidate_revision,
                    replacement_revision=replacement_revision,
                    audit=audit,
                    completed_at=completed_at,
                    command_identity=command_identity,
                    request_hash=request_hash,
                    denial_code="AUTHORITY_SCOPE_MISMATCH",
                    denial_reason="verified evidence scope must match the supersession scope",
                )
            verified_decisions.append((evidence_reference, verified_decision))
        evidence_pins = [
            {
                "evidence_reference_id": evidence_reference.id,
                "evidence_id": evidence_reference.evidence_id,
                "evidence_revision": evidence_reference.evidence_revision,
                "verification_decision_id": verified_decision.id,
                "verification_revision_number": verified_decision.revision_number,
                "verifier_user_id": verified_decision.verifier_user_id,
            }
            for evidence_reference, verified_decision in verified_decisions
        ]
        basis_content_hash = self._hash(
            {
                "rule_id": rule_id,
                "incumbent_revision": incumbent.revision,
                "incumbent_revision_id": incumbent.id,
                "replacement_candidate_revision": replacement_candidate.revision,
                "replacement_candidate_revision_id": replacement_candidate.id,
                "replacement_revision": replacement_revision,
                "scope_snapshot": scope_snapshot,
                "evidence_pins": evidence_pins,
            }
        )
        if version_metadata.content_hash != basis_content_hash:
            return self._deny_active_supersession(
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                audit=audit,
                completed_at=completed_at,
                command_identity=command_identity,
                request_hash=request_hash,
                denial_code="CONTENT_HASH_MISMATCH",
                denial_reason="replacement content hash must pin the verified supersession basis",
            )
        replacement = self._repository.create_revision(
            engineering_rule=rule,
            revision=replacement_revision,
            name=replacement_candidate.name,
            status=RuleLifecycleStatus.DRAFT,
            evidence_class=EvidenceClass.SOURCE_BACKED,
            category=replacement_candidate.category,
            parameter=replacement_candidate.parameter,
            operator=replacement_candidate.operator,
            min_value=replacement_candidate.min_value,
            max_value=replacement_candidate.max_value,
            unit=replacement_candidate.unit,
            applicability_metadata=replacement_candidate.applicability_metadata,
            applicability_schema_version=replacement_candidate.applicability_schema_version,
            effective_date=replacement_candidate.effective_date,
            expiry_date=replacement_candidate.expiry_date,
            supersedes_revision_id=incumbent.id,
            source_type=replacement_candidate.source_type,
            source_name=replacement_candidate.source_name,
            source_document=replacement_candidate.source_document,
            source_url=replacement_candidate.source_url,
            safe_default=replacement_candidate.safe_default,
            missing_handling=replacement_candidate.missing_handling,
            conflict_handling=replacement_candidate.conflict_handling,
            unit_mismatch_handling=replacement_candidate.unit_mismatch_handling,
            description=replacement_candidate.description,
            note=replacement_candidate.note,
            enabled=False,
            reason_for_change=f"Governed supersession of revision {incumbent.revision}",
            version_metadata=version_metadata,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            evidence_references=tuple(
                EvidenceReferenceDraft(
                    evidence_id=evidence_reference.evidence_id,
                    evidence_revision=evidence_reference.evidence_revision,
                    evidence_class=evidence_reference.evidence_class,
                    lifecycle_status=evidence_reference.lifecycle_status,
                    created_by_actor_id=evidence_reference.created_by_actor_id,
                    created_by_user_id=evidence_reference.created_by_user_id,
                    source_type=evidence_reference.source_type,
                    source_name=evidence_reference.source_name,
                    source_document=evidence_reference.source_document,
                    edition=evidence_reference.edition,
                    section_reference=evidence_reference.section_reference,
                    page_reference=evidence_reference.page_reference,
                    table_reference=evidence_reference.table_reference,
                    reference_uri=evidence_reference.reference_uri,
                    reference_metadata=evidence_reference.reference_metadata,
                    schema_version=evidence_reference.schema_version,
                    hash_algorithm=evidence_reference.hash_algorithm,
                    content_hash=evidence_reference.content_hash,
                )
                for evidence_reference, _verified_decision in verified_decisions
            ),
            allow_source_backed=True,
        )
        supersession_basis_snapshot = {
            "rule_id": rule_id,
            "incumbent_revision": incumbent.revision,
            "incumbent_revision_id": incumbent.id,
            "replacement_revision": replacement_revision,
            "replacement_revision_id": replacement.id,
            "scope_snapshot": scope_snapshot,
            "evidence_pins": evidence_pins,
            "content_hash": basis_content_hash,
        }
        supersede_authority_snapshot = self._lifecycle_authority_snapshot(
            audit=audit,
            event_type=RuleLifecycleEventType.SUPERSEDE,
            scope_snapshot=scope_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
        )
        supersede_content_hash = self._hash(
            {
                "lifecycle_event_id": incumbent_latest.lifecycle_event_id,
                "event_type": RuleLifecycleEventType.SUPERSEDE.value,
                "rule_id": rule_id,
                "source_revision_id": incumbent.id,
                "source_revision": incumbent.revision,
                "scope_snapshot": scope_snapshot,
                "basis_content_hash": basis_content_hash,
                "authority_snapshot": supersede_authority_snapshot,
                "effective_from": effective_from,
                "expires_at": expires_at,
            }
        )
        supersede_event = self._repository.create_lifecycle_event(
            engineering_rule=rule,
            engineering_rule_revision=incumbent,
            lifecycle_event_id=incumbent_latest.lifecycle_event_id,
            revision_number=incumbent_latest.revision_number + 1,
            event_type=RuleLifecycleEventType.SUPERSEDE,
            scope_snapshot=scope_snapshot,
            basis_snapshot=supersession_basis_snapshot,
            authority_snapshot=supersede_authority_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            schema_version="rule-lifecycle-v1",
            canonicalization_version="rule-lifecycle-canonical-v1",
            hash_algorithm="sha256",
            content_hash=supersede_content_hash,
            software_version=audit.software_version,
            correlation_id=audit.correlation_id,
            supersedes_rule_lifecycle_event_id=incumbent_latest.id,
        )
        replacement_enable_event_id = self._lifecycle_event_identity(
            rule_id=rule_id,
            source_revision=replacement,
            event_type=RuleLifecycleEventType.ENABLE,
            scope_snapshot=scope_snapshot,
        )
        enable_authority_snapshot = self._lifecycle_authority_snapshot(
            audit=audit,
            event_type=RuleLifecycleEventType.ENABLE,
            scope_snapshot=scope_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
        )
        enable_content_hash = self._hash(
            {
                "lifecycle_event_id": replacement_enable_event_id,
                "event_type": RuleLifecycleEventType.ENABLE.value,
                "rule_id": rule_id,
                "source_revision_id": replacement.id,
                "source_revision": replacement.revision,
                "scope_snapshot": scope_snapshot,
                "basis_content_hash": basis_content_hash,
                "authority_snapshot": enable_authority_snapshot,
                "effective_from": effective_from,
                "expires_at": expires_at,
            }
        )
        replacement_enable_event = self._repository.create_lifecycle_event(
            engineering_rule=rule,
            engineering_rule_revision=replacement,
            lifecycle_event_id=replacement_enable_event_id,
            revision_number=1,
            event_type=RuleLifecycleEventType.ENABLE,
            scope_snapshot=scope_snapshot,
            basis_snapshot=supersession_basis_snapshot,
            authority_snapshot=enable_authority_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            schema_version="rule-lifecycle-v1",
            canonicalization_version="rule-lifecycle-canonical-v1",
            hash_algorithm="sha256",
            content_hash=enable_content_hash,
            software_version=audit.software_version,
            correlation_id=audit.correlation_id,
        )
        replacement_activation_event_id = self._lifecycle_event_identity(
            rule_id=rule_id,
            source_revision=replacement,
            event_type=RuleLifecycleEventType.ACTIVATE,
            scope_snapshot=scope_snapshot,
        )
        activation_authority_snapshot = self._lifecycle_authority_snapshot(
            audit=audit,
            event_type=RuleLifecycleEventType.ACTIVATE,
            scope_snapshot=scope_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            completed_at=completed_at,
        )
        activation_content_hash = self._hash(
            {
                "lifecycle_event_id": replacement_activation_event_id,
                "event_type": RuleLifecycleEventType.ACTIVATE.value,
                "rule_id": rule_id,
                "source_revision_id": replacement.id,
                "source_revision": replacement.revision,
                "scope_snapshot": scope_snapshot,
                "basis_content_hash": basis_content_hash,
                "authority_snapshot": activation_authority_snapshot,
                "effective_from": effective_from,
                "expires_at": expires_at,
            }
        )
        replacement_activation_event = self._repository.create_lifecycle_event(
            engineering_rule=rule,
            engineering_rule_revision=replacement,
            lifecycle_event_id=replacement_activation_event_id,
            revision_number=1,
            event_type=RuleLifecycleEventType.ACTIVATE,
            scope_snapshot=scope_snapshot,
            basis_snapshot=supersession_basis_snapshot,
            authority_snapshot=activation_authority_snapshot,
            effective_from=effective_from,
            expires_at=expires_at,
            created_by_actor_id=audit.actor_id,
            created_by_user_id=audit.actor_user_id,
            schema_version="rule-lifecycle-v1",
            canonicalization_version="rule-lifecycle-canonical-v1",
            hash_algorithm="sha256",
            content_hash=activation_content_hash,
            software_version=audit.software_version,
            correlation_id=audit.correlation_id,
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_lifecycle_event",
            entity_id=rule_id,
            entity_revision=incumbent.revision,
            action="SUPERSEDE_SOURCE_BACKED_RULE_REVISION",
            prior_content_hash=incumbent.content_hash,
            new_content_hash=supersede_event.content_hash,
            detail=self._audit_detail(
                audit,
                command="SUPERSEDE_SOURCE_BACKED_RULE_REVISION",
                rule_id=rule_id,
                incumbent_revision=incumbent.revision,
                incumbent_revision_id=incumbent.id,
                replacement_revision=replacement.revision,
                replacement_revision_id=replacement.id,
                superseded_lifecycle_event_id=incumbent_latest.id,
                lifecycle_event_id=supersede_event.lifecycle_event_id,
                lifecycle_event_revision_number=supersede_event.revision_number,
                event_type=RuleLifecycleEventType.SUPERSEDE.value,
                scope_snapshot=scope_snapshot,
                basis_content_hash=basis_content_hash,
                evidence_reference_ids=[
                    pin["evidence_reference_id"] for pin in evidence_pins
                ],
                verification_decision_ids=[
                    pin["verification_decision_id"] for pin in evidence_pins
                ],
            ),
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_lifecycle_event",
            entity_id=rule_id,
            entity_revision=replacement.revision,
            action="ENABLE_SOURCE_BACKED_RULE_REVISION",
            prior_content_hash=replacement.content_hash,
            new_content_hash=replacement_enable_event.content_hash,
            detail=self._audit_detail(
                audit,
                command="ENABLE_SOURCE_BACKED_RULE_REVISION",
                rule_id=rule_id,
                source_revision=replacement.revision,
                source_revision_id=replacement.id,
                lifecycle_event_id=replacement_enable_event.lifecycle_event_id,
                event_type=RuleLifecycleEventType.ENABLE.value,
                scope_snapshot=scope_snapshot,
                basis_content_hash=basis_content_hash,
            ),
        )
        self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_lifecycle_event",
            entity_id=rule_id,
            entity_revision=replacement.revision,
            action="ACTIVATE_SOURCE_BACKED_RULE_REVISION",
            prior_content_hash=replacement.content_hash,
            new_content_hash=replacement_activation_event.content_hash,
            detail=self._audit_detail(
                audit,
                command="ACTIVATE_SOURCE_BACKED_RULE_REVISION",
                rule_id=rule_id,
                source_revision=replacement.revision,
                source_revision_id=replacement.id,
                lifecycle_event_id=replacement_activation_event.lifecycle_event_id,
                event_type=RuleLifecycleEventType.ACTIVATE.value,
                scope_snapshot=scope_snapshot,
                basis_content_hash=basis_content_hash,
            ),
        )
        result = CommandResultReference(
            result_type="engineering_rule_lifecycle_event",
            result_id=str(replacement_activation_event.id),
            result_revision=str(replacement_activation_event.revision_number),
        )
        completed = self._idempotency.complete(
            identity=command_identity,
            request_hash=request_hash,
            result_reference=result,
            completed_at=completed_at,
        )
        if completed.result_reference != result:
            raise RuntimeError("active supersession idempotency completion failed")
        return result

    def _deny_active_supersession(
        self,
        *,
        rule_id: str,
        incumbent_revision: str,
        replacement_candidate_revision: str,
        replacement_revision: str,
        audit: GovernedAuditMetadata,
        completed_at: datetime,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        denial_code: str,
        denial_reason: str,
    ) -> CommandResultReference:
        denial_event = self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_supersession_denial",
            entity_id=rule_id,
            entity_revision=incumbent_revision,
            action="SUPERSEDE_SOURCE_BACKED_RULE_REVISION_DENIED",
            prior_content_hash=None,
            new_content_hash=None,
            detail=self._audit_detail(
                audit,
                command="SUPERSEDE_SOURCE_BACKED_RULE_REVISION_DENIED",
                rule_id=rule_id,
                incumbent_revision=incumbent_revision,
                replacement_candidate_revision=replacement_candidate_revision,
                replacement_revision=replacement_revision,
                denial_code=denial_code,
                denial_reason=denial_reason,
            ),
        )
        result = CommandResultReference(
            result_type="engineering_rule_supersession_denial",
            result_id=str(denial_event.id),
            result_revision="denied",
        )
        completed = self._idempotency.complete(
            identity=command_identity,
            request_hash=request_hash,
            result_reference=result,
            completed_at=completed_at,
        )
        if completed.result_reference != result:
            raise RuntimeError(
                "active supersession denial idempotency completion failed"
            )
        return result

    @staticmethod
    def _lifecycle_event_identity(
        *,
        rule_id: str,
        source_revision: EngineeringRuleRevision,
        event_type: RuleLifecycleEventType,
        scope_snapshot: dict[str, object],
    ) -> str:
        scope_hash = hashlib.sha256(
            json.dumps(scope_snapshot, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        return f"{rule_id}:{source_revision.revision}:{event_type.value}:{scope_hash}"

    @staticmethod
    def _lifecycle_authority_snapshot(
        *,
        audit: GovernedAuditMetadata,
        event_type: RuleLifecycleEventType,
        scope_snapshot: dict[str, object],
        effective_from: datetime,
        expires_at: datetime | None,
        completed_at: datetime,
    ) -> dict[str, object]:
        return {
            "actor_id": audit.actor_id,
            "actor_user_id": audit.actor_user_id,
            "actor_role": audit.actor_role,
            "actor_type": audit.actor_type,
            "lifecycle_capability": event_type.value,
            "scope_snapshot": scope_snapshot,
            "effective_from": effective_from.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at is not None else None,
            "decision_at": completed_at.isoformat(),
            "correlation_id": audit.correlation_id,
            "policy_identifier": "SDS-115",
            "policy_version": "0.1 Draft",
        }

    def _deny_source_backed_lifecycle(
        self,
        *,
        rule_id: str,
        source_revision: str,
        audit: GovernedAuditMetadata,
        completed_at: datetime,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        denial_action: str,
        denial_code: str,
        denial_reason: str,
    ) -> CommandResultReference:
        denial_event = self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_lifecycle_denial",
            entity_id=rule_id,
            entity_revision=source_revision,
            action=denial_action,
            prior_content_hash=None,
            new_content_hash=None,
            detail=self._audit_detail(
                audit,
                command=denial_action,
                rule_id=rule_id,
                source_revision=source_revision,
                denial_code=denial_code,
                denial_reason=denial_reason,
            ),
        )
        result = CommandResultReference(
            result_type="engineering_rule_lifecycle_denial",
            result_id=str(denial_event.id),
            result_revision="denied",
        )
        completed = self._idempotency.complete(
            identity=command_identity,
            request_hash=request_hash,
            result_reference=result,
            completed_at=completed_at,
        )
        if completed.result_reference != result:
            raise RuntimeError("source-backed lifecycle denial idempotency completion failed")
        return result

    def _deny_source_backed_promotion(
        self,
        *,
        rule_id: str,
        source_revision: str,
        revision: str,
        audit: GovernedAuditMetadata,
        completed_at: datetime,
        command_identity: CommandIdentity,
        request_hash: CanonicalRequestHash,
        denial_code: str,
        denial_reason: str,
    ) -> CommandResultReference:
        denial_event = self._audit.record_event(
            **self._common_audit_fields(audit),
            entity_type="engineering_rule_promotion_denial",
            entity_id=rule_id,
            entity_revision=revision,
            action="AUTHORIZE_SOURCE_BACKED_PROMOTION_DENIED",
            prior_content_hash=None,
            new_content_hash=None,
            detail=self._audit_detail(
                audit,
                command="AUTHORIZE_SOURCE_BACKED_PROMOTION_DENIED",
                rule_id=rule_id,
                source_revision=source_revision,
                target_revision=revision,
                denial_code=denial_code,
                denial_reason=denial_reason,
            ),
        )
        result = CommandResultReference(
            result_type="engineering_rule_promotion_denial",
            result_id=str(denial_event.id),
            result_revision="denied",
        )
        completed = self._idempotency.complete(
            identity=command_identity,
            request_hash=request_hash,
            result_reference=result,
            completed_at=completed_at,
        )
        if completed.result_reference != result:
            raise RuntimeError("source-backed promotion denial idempotency completion failed")
        return result
