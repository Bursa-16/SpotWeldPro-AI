"""Domain contract unit tests for CE-03A weld-point types.

Tests:
  - Enum members exist and are StrEnum values
  - Frozen/immutable dataclasses
  - Non-empty string validation
  - Positive/finite numeric validation
  - Coordinate finiteness
  - Normal vector partial-supply rejection
  - WeldPointEngineeringContext: all revision IDs mandatory and positive
  - WeldMapRevisionDraft: duplicate weld_point_id forbidden
  - WeldMapRevisionDraft: empty points forbidden
  - WeldParameterSnapshot: range validations, contiguous pulse sequence
  - ValidationEvidence: sample_quantity positive
  - EngineeringChangeRequestDraft: same-object snapshot rejection
  - ReleaseMetadata / ApprovalRecord: non-empty field validation
"""

from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import pytest

from app.domain.weld_point_types import (
    ApprovalRecord,
    EngineeringChangeIdentity,
    EngineeringChangeReason,
    EngineeringChangeRequestDraft,
    EngineeringChangeStatus,
    ManufacturingLocationContext,
    PartIdentity,
    PartRevision,
    ProductIdentity,
    ReleaseMetadata,
    ValidationEvidence,
    WeldMapIdentity,
    WeldMapPoint,
    WeldMapRevisionDraft,
    WeldParameterSnapshot,
    WeldPointEngineeringContext,
    WeldPointIdentity,
    WeldPointLocation,
    WeldPointRevisionDraft,
    WeldPulseSnapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _eng_ctx(
    stack: int = 1,
    electrode: int = 2,
    gun: int = 3,
    schedule: int = 4,
) -> WeldPointEngineeringContext:
    return WeldPointEngineeringContext(
        stack_up_revision_id=stack,
        electrode_revision_id=electrode,
        weld_gun_revision_id=gun,
        weld_schedule_revision_id=schedule,
    )


def _pulse(sequence: int = 1) -> WeldPulseSnapshot:
    return WeldPulseSnapshot(
        sequence=sequence,
        pulse_type="WELD",
        current_ka=8.0,
        duration_cycles=12.0,
        force_kn=4.0,
    )


def _snapshot() -> WeldParameterSnapshot:
    return WeldParameterSnapshot(
        weld_current_ka=8.0,
        weld_cycles=12.0,
        electrode_force_kn=4.0,
        squeeze_cycles=10.0,
        hold_cycles=5.0,
        pulses=(_pulse(),),
        electrode_tip_diameter_mm=6.0,
    )


def _map_point(weld_point_id: str = "WP-001") -> WeldMapPoint:
    return WeldMapPoint(
        weld_point_id=weld_point_id,
        part_revision_id=1,
        engineering_context=_eng_ctx(),
    )


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------

class TestEnums:
    def test_reason_members(self):
        reasons = {r.value for r in EngineeringChangeReason}
        for expected in (
            "QUALITY_ISSUE", "SMALL_NUGGET", "EXPULSION", "ELECTRODE_WEAR",
            "MATERIAL_CHANGE", "SUPPLIER_CHANGE", "THICKNESS_CHANGE",
            "COATING_CHANGE", "MACHINE_CHANGE", "PROCESS_OPTIMIZATION",
            "CUSTOMER_REQUEST", "OTHER",
        ):
            assert expected in reasons

    def test_status_members(self):
        statuses = {s.value for s in EngineeringChangeStatus}
        for expected in (
            "DRAFT", "UNDER_REVIEW", "VALIDATION",
            "APPROVED", "REJECTED", "RELEASED", "CANCELLED",
        ):
            assert expected in statuses

    def test_reason_is_str(self):
        assert isinstance(EngineeringChangeReason.QUALITY_ISSUE, str)

    def test_status_is_str(self):
        assert isinstance(EngineeringChangeStatus.DRAFT, str)


# ---------------------------------------------------------------------------
# ProductIdentity
# ---------------------------------------------------------------------------

class TestProductIdentity:
    def test_valid(self):
        p = ProductIdentity(product_id="P-001", product_name="Test Car")
        assert p.product_id == "P-001"

    def test_empty_product_id(self):
        with pytest.raises(ValueError, match="product_id"):
            ProductIdentity(product_id="  ", product_name="Test Car")

    def test_empty_product_name(self):
        with pytest.raises(ValueError, match="product_name"):
            ProductIdentity(product_id="P-001", product_name="")

    def test_frozen(self):
        p = ProductIdentity(product_id="P-001", product_name="Test Car")
        with pytest.raises(FrozenInstanceError):
            p.product_id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# PartIdentity / PartRevision
# ---------------------------------------------------------------------------

class TestPartIdentity:
    def test_empty_part_number(self):
        with pytest.raises(ValueError, match="part_number"):
            PartIdentity(part_number="", product_id="P-001")

    def test_empty_product_id(self):
        with pytest.raises(ValueError, match="product_id"):
            PartIdentity(part_number="PART-A", product_id="  ")


class TestPartRevision:
    def test_valid(self):
        r = PartRevision(revision_id=1, part_number="PART-A", revision_label="A")
        assert r.revision_id == 1

    def test_zero_revision_id(self):
        with pytest.raises(ValueError, match="revision_id"):
            PartRevision(revision_id=0, part_number="PART-A", revision_label="A")

    def test_negative_revision_id(self):
        with pytest.raises(ValueError, match="revision_id"):
            PartRevision(revision_id=-1, part_number="PART-A", revision_label="A")

    def test_empty_revision_label(self):
        with pytest.raises(ValueError, match="revision_label"):
            PartRevision(revision_id=1, part_number="PART-A", revision_label="  ")


# ---------------------------------------------------------------------------
# ManufacturingLocationContext
# ---------------------------------------------------------------------------

class TestManufacturingLocationContext:
    def test_empty_plant(self):
        with pytest.raises(ValueError, match="plant"):
            ManufacturingLocationContext(plant="  ")

    def test_valid_minimal(self):
        ctx = ManufacturingLocationContext(plant="Plant-A")
        assert ctx.plant == "Plant-A"
        assert ctx.line is None


# ---------------------------------------------------------------------------
# WeldPointIdentity
# ---------------------------------------------------------------------------

class TestWeldPointIdentity:
    def test_empty_weld_point_id(self):
        with pytest.raises(ValueError, match="weld_point_id"):
            WeldPointIdentity(weld_point_id="", part_number="PART-A", product_id="P-001")

    def test_empty_part_number(self):
        with pytest.raises(ValueError, match="part_number"):
            WeldPointIdentity(weld_point_id="WP-001", part_number="  ", product_id="P-001")

    def test_empty_product_id(self):
        with pytest.raises(ValueError, match="product_id"):
            WeldPointIdentity(weld_point_id="WP-001", part_number="PART-A", product_id="")


# ---------------------------------------------------------------------------
# WeldPointLocation
# ---------------------------------------------------------------------------

class TestWeldPointLocation:
    def test_valid_no_normal(self):
        loc = WeldPointLocation(x_mm=10.0, y_mm=20.0, z_mm=5.0)
        assert loc.z_mm == 5.0

    def test_valid_with_normal(self):
        loc = WeldPointLocation(x_mm=0.0, y_mm=0.0, z_mm=0.0, normal_x=0.0, normal_y=0.0, normal_z=1.0)
        assert loc.normal_z == 1.0

    def test_infinite_coordinate(self):
        with pytest.raises(ValueError, match="x_mm"):
            WeldPointLocation(x_mm=math.inf, y_mm=0.0, z_mm=0.0)

    def test_nan_coordinate(self):
        with pytest.raises(ValueError, match="y_mm"):
            WeldPointLocation(x_mm=0.0, y_mm=math.nan, z_mm=0.0)

    def test_partial_normal_rejected(self):
        with pytest.raises(ValueError, match="normal vector"):
            WeldPointLocation(x_mm=0.0, y_mm=0.0, z_mm=0.0, normal_x=1.0, normal_y=None, normal_z=0.0)


# ---------------------------------------------------------------------------
# WeldPointEngineeringContext
# ---------------------------------------------------------------------------

class TestWeldPointEngineeringContext:
    def test_valid(self):
        ctx = _eng_ctx()
        assert ctx.stack_up_revision_id == 1
        assert ctx.weld_schedule_revision_id == 4

    def test_zero_stack_up(self):
        with pytest.raises(ValueError, match="stack_up_revision_id"):
            _eng_ctx(stack=0)

    def test_negative_electrode(self):
        with pytest.raises(ValueError, match="electrode_revision_id"):
            _eng_ctx(electrode=-5)

    def test_zero_gun(self):
        with pytest.raises(ValueError, match="weld_gun_revision_id"):
            _eng_ctx(gun=0)

    def test_negative_schedule(self):
        with pytest.raises(ValueError, match="weld_schedule_revision_id"):
            _eng_ctx(schedule=-1)

    def test_frozen(self):
        ctx = _eng_ctx()
        with pytest.raises(FrozenInstanceError):
            ctx.stack_up_revision_id = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# WeldPointRevisionDraft
# ---------------------------------------------------------------------------

class TestWeldPointRevisionDraft:
    def test_valid(self):
        draft = WeldPointRevisionDraft(
            identity=WeldPointIdentity(weld_point_id="WP-001", part_number="PART-A", product_id="P-001"),
            part_revision_id=1,
            engineering_context=_eng_ctx(),
        )
        assert draft.part_revision_id == 1

    def test_zero_part_revision_id(self):
        with pytest.raises(ValueError, match="part_revision_id"):
            WeldPointRevisionDraft(
                identity=WeldPointIdentity(weld_point_id="WP-001", part_number="PART-A", product_id="P-001"),
                part_revision_id=0,
                engineering_context=_eng_ctx(),
            )


# ---------------------------------------------------------------------------
# WeldMapIdentity / WeldMapPoint / WeldMapRevisionDraft
# ---------------------------------------------------------------------------

class TestWeldMapIdentity:
    def test_empty_weld_map_id(self):
        with pytest.raises(ValueError, match="weld_map_id"):
            WeldMapIdentity(weld_map_id="", product_id="P-001", part_number="PART-A")


class TestWeldMapPoint:
    def test_empty_weld_point_id(self):
        with pytest.raises(ValueError, match="weld_point_id"):
            WeldMapPoint(weld_point_id="  ", part_revision_id=1, engineering_context=_eng_ctx())

    def test_zero_part_revision_id(self):
        with pytest.raises(ValueError, match="part_revision_id"):
            WeldMapPoint(weld_point_id="WP-001", part_revision_id=0, engineering_context=_eng_ctx())


class TestWeldMapRevisionDraft:
    def test_valid(self):
        draft = WeldMapRevisionDraft(
            identity=WeldMapIdentity(weld_map_id="MAP-001", product_id="P-001", part_number="PART-A"),
            revision_number=1,
            points=(_map_point("WP-001"), _map_point("WP-002")),
        )
        assert len(draft.points) == 2

    def test_empty_points(self):
        with pytest.raises(ValueError, match="at least one point"):
            WeldMapRevisionDraft(
                identity=WeldMapIdentity(weld_map_id="MAP-001", product_id="P-001", part_number="PART-A"),
                revision_number=1,
                points=(),
            )

    def test_duplicate_weld_point_id(self):
        with pytest.raises(ValueError, match="duplicate weld_point_id"):
            WeldMapRevisionDraft(
                identity=WeldMapIdentity(weld_map_id="MAP-001", product_id="P-001", part_number="PART-A"),
                revision_number=1,
                points=(_map_point("WP-001"), _map_point("WP-001")),
            )

    def test_zero_revision_number(self):
        with pytest.raises(ValueError, match="revision_number"):
            WeldMapRevisionDraft(
                identity=WeldMapIdentity(weld_map_id="MAP-001", product_id="P-001", part_number="PART-A"),
                revision_number=0,
                points=(_map_point(),),
            )


# ---------------------------------------------------------------------------
# WeldPulseSnapshot
# ---------------------------------------------------------------------------

class TestWeldPulseSnapshot:
    def test_valid(self):
        p = _pulse()
        assert p.current_ka == 8.0

    def test_zero_sequence(self):
        with pytest.raises(ValueError, match="sequence"):
            WeldPulseSnapshot(sequence=0, pulse_type="WELD")

    def test_empty_pulse_type(self):
        with pytest.raises(ValueError, match="pulse_type"):
            WeldPulseSnapshot(sequence=1, pulse_type="  ")

    def test_negative_current(self):
        with pytest.raises(ValueError, match="current_ka"):
            WeldPulseSnapshot(sequence=1, pulse_type="WELD", current_ka=-1.0)

    def test_zero_force(self):
        with pytest.raises(ValueError, match="force_kn"):
            WeldPulseSnapshot(sequence=1, pulse_type="WELD", force_kn=0.0)

    def test_negative_duration(self):
        with pytest.raises(ValueError, match="duration_cycles"):
            WeldPulseSnapshot(sequence=1, pulse_type="WELD", duration_cycles=-0.1)


# ---------------------------------------------------------------------------
# WeldParameterSnapshot
# ---------------------------------------------------------------------------

class TestWeldParameterSnapshot:
    def test_valid(self):
        s = _snapshot()
        assert s.weld_current_ka == 8.0
        assert len(s.pulses) == 1

    def test_frozen(self):
        s = _snapshot()
        with pytest.raises(FrozenInstanceError):
            s.weld_current_ka = 99.0  # type: ignore[misc]

    def test_zero_current(self):
        with pytest.raises(ValueError, match="weld_current_ka"):
            WeldParameterSnapshot(
                weld_current_ka=0.0, weld_cycles=12.0, electrode_force_kn=4.0,
                squeeze_cycles=10.0, hold_cycles=5.0, pulses=(_pulse(),),
            )

    def test_negative_cycles(self):
        with pytest.raises(ValueError, match="weld_cycles"):
            WeldParameterSnapshot(
                weld_current_ka=8.0, weld_cycles=-1.0, electrode_force_kn=4.0,
                squeeze_cycles=10.0, hold_cycles=5.0, pulses=(_pulse(),),
            )

    def test_zero_force(self):
        with pytest.raises(ValueError, match="electrode_force_kn"):
            WeldParameterSnapshot(
                weld_current_ka=8.0, weld_cycles=12.0, electrode_force_kn=0.0,
                squeeze_cycles=10.0, hold_cycles=5.0, pulses=(_pulse(),),
            )

    def test_negative_squeeze(self):
        with pytest.raises(ValueError, match="squeeze_cycles"):
            WeldParameterSnapshot(
                weld_current_ka=8.0, weld_cycles=12.0, electrode_force_kn=4.0,
                squeeze_cycles=-1.0, hold_cycles=5.0, pulses=(_pulse(),),
            )

    def test_empty_pulses(self):
        with pytest.raises(ValueError, match="at least one pulse"):
            WeldParameterSnapshot(
                weld_current_ka=8.0, weld_cycles=12.0, electrode_force_kn=4.0,
                squeeze_cycles=10.0, hold_cycles=5.0, pulses=(),
            )

    def test_non_contiguous_pulse_sequence(self):
        with pytest.raises(ValueError, match="contiguous"):
            WeldParameterSnapshot(
                weld_current_ka=8.0, weld_cycles=12.0, electrode_force_kn=4.0,
                squeeze_cycles=10.0, hold_cycles=5.0,
                pulses=(_pulse(1), _pulse(3)),
            )

    def test_zero_tip_diameter(self):
        with pytest.raises(ValueError, match="electrode_tip_diameter_mm"):
            WeldParameterSnapshot(
                weld_current_ka=8.0, weld_cycles=12.0, electrode_force_kn=4.0,
                squeeze_cycles=10.0, hold_cycles=5.0, pulses=(_pulse(),),
                electrode_tip_diameter_mm=0.0,
            )

    def test_infinite_current(self):
        with pytest.raises(ValueError, match="weld_current_ka"):
            WeldParameterSnapshot(
                weld_current_ka=math.inf, weld_cycles=12.0, electrode_force_kn=4.0,
                squeeze_cycles=10.0, hold_cycles=5.0, pulses=(_pulse(),),
            )

    def test_multi_pulse_valid(self):
        s = WeldParameterSnapshot(
            weld_current_ka=8.0, weld_cycles=12.0, electrode_force_kn=4.0,
            squeeze_cycles=10.0, hold_cycles=5.0,
            pulses=(_pulse(1), _pulse(2)),
        )
        assert len(s.pulses) == 2


# ---------------------------------------------------------------------------
# ValidationEvidence
# ---------------------------------------------------------------------------

class TestValidationEvidence:
    def test_valid(self):
        e = ValidationEvidence(
            test_type="Peel", sample_quantity=5, result="PASS",
            evidence_date="2026-09-01", conducted_by="user:1",
        )
        assert e.sample_quantity == 5

    def test_zero_sample_quantity(self):
        with pytest.raises(ValueError, match="sample_quantity"):
            ValidationEvidence(
                test_type="Peel", sample_quantity=0, result="PASS",
                evidence_date="2026-09-01", conducted_by="user:1",
            )

    def test_empty_test_type(self):
        with pytest.raises(ValueError, match="test_type"):
            ValidationEvidence(
                test_type="  ", sample_quantity=5, result="PASS",
                evidence_date="2026-09-01", conducted_by="user:1",
            )


# ---------------------------------------------------------------------------
# ApprovalRecord
# ---------------------------------------------------------------------------

class TestApprovalRecord:
    def test_valid_approved(self):
        a = ApprovalRecord(approver_actor_id="user:5", approval_date="2026-09-10", approved=True)
        assert a.approved is True

    def test_valid_rejected(self):
        a = ApprovalRecord(approver_actor_id="user:5", approval_date="2026-09-10", approved=False)
        assert a.approved is False

    def test_empty_approver(self):
        with pytest.raises(ValueError, match="approver_actor_id"):
            ApprovalRecord(approver_actor_id="  ", approval_date="2026-09-10", approved=True)

    def test_empty_date(self):
        with pytest.raises(ValueError, match="approval_date"):
            ApprovalRecord(approver_actor_id="user:5", approval_date="", approved=True)


# ---------------------------------------------------------------------------
# ReleaseMetadata
# ---------------------------------------------------------------------------

class TestReleaseMetadata:
    def test_valid(self):
        r = ReleaseMetadata(
            release_number="ECR-001-R1",
            release_date="2026-09-15",
            released_by_actor_id="user:10",
        )
        assert r.release_number == "ECR-001-R1"

    def test_empty_release_number(self):
        with pytest.raises(ValueError, match="release_number"):
            ReleaseMetadata(release_number="  ", release_date="2026-09-15", released_by_actor_id="user:10")

    def test_empty_release_date(self):
        with pytest.raises(ValueError, match="release_date"):
            ReleaseMetadata(release_number="ECR-001-R1", release_date="", released_by_actor_id="user:10")


# ---------------------------------------------------------------------------
# EngineeringChangeIdentity
# ---------------------------------------------------------------------------

class TestEngineeringChangeIdentity:
    def test_empty_change_id(self):
        with pytest.raises(ValueError, match="change_id"):
            EngineeringChangeIdentity(change_id="", product_id="P-001", part_number="PART-A", weld_point_id="WP-001")

    def test_empty_weld_point_id(self):
        with pytest.raises(ValueError, match="weld_point_id"):
            EngineeringChangeIdentity(change_id="ECR-001", product_id="P-001", part_number="PART-A", weld_point_id=" ")


# ---------------------------------------------------------------------------
# EngineeringChangeRequestDraft
# ---------------------------------------------------------------------------

def _ecr_draft(old: WeldParameterSnapshot | None = None, new: WeldParameterSnapshot | None = None) -> EngineeringChangeRequestDraft:
    old_snap = old or _snapshot()
    new_snap = new or WeldParameterSnapshot(
        weld_current_ka=9.0, weld_cycles=14.0, electrode_force_kn=4.5,
        squeeze_cycles=10.0, hold_cycles=5.0, pulses=(_pulse(),),
    )
    return EngineeringChangeRequestDraft(
        identity=EngineeringChangeIdentity(
            change_id="ECR-001", product_id="P-001", part_number="PART-A", weld_point_id="WP-001"
        ),
        part_revision_id=1,
        requester_actor_id="user:1",
        request_date="2026-09-01",
        reason=EngineeringChangeReason.QUALITY_ISSUE,
        owner_actor_id="user:2",
        old_parameter_snapshot=old_snap,
        new_parameter_snapshot=new_snap,
    )


class TestEngineeringChangeRequestDraft:
    def test_valid(self):
        ecr = _ecr_draft()
        assert ecr.status == EngineeringChangeStatus.DRAFT
        assert ecr.reason == EngineeringChangeReason.QUALITY_ISSUE

    def test_frozen(self):
        ecr = _ecr_draft()
        with pytest.raises(FrozenInstanceError):
            ecr.status = EngineeringChangeStatus.APPROVED  # type: ignore[misc]

    def test_zero_part_revision_id(self):
        with pytest.raises(ValueError, match="part_revision_id"):
            snap = _snapshot()
            EngineeringChangeRequestDraft(
                identity=EngineeringChangeIdentity(
                    change_id="ECR-001", product_id="P-001", part_number="PART-A", weld_point_id="WP-001"
                ),
                part_revision_id=0,
                requester_actor_id="user:1",
                request_date="2026-09-01",
                reason=EngineeringChangeReason.OTHER,
                owner_actor_id="user:2",
                old_parameter_snapshot=snap,
                new_parameter_snapshot=_snapshot(),
            )

    def test_same_object_snapshots_rejected(self):
        """old and new snapshots must be independent objects."""
        snap = _snapshot()
        with pytest.raises(ValueError, match="independent"):
            EngineeringChangeRequestDraft(
                identity=EngineeringChangeIdentity(
                    change_id="ECR-001", product_id="P-001", part_number="PART-A", weld_point_id="WP-001"
                ),
                part_revision_id=1,
                requester_actor_id="user:1",
                request_date="2026-09-01",
                reason=EngineeringChangeReason.OTHER,
                owner_actor_id="user:2",
                old_parameter_snapshot=snap,
                new_parameter_snapshot=snap,
            )

    def test_empty_requester(self):
        with pytest.raises(ValueError, match="requester_actor_id"):
            snap = _snapshot()
            EngineeringChangeRequestDraft(
                identity=EngineeringChangeIdentity(
                    change_id="ECR-001", product_id="P-001", part_number="PART-A", weld_point_id="WP-001"
                ),
                part_revision_id=1,
                requester_actor_id="  ",
                request_date="2026-09-01",
                reason=EngineeringChangeReason.OTHER,
                owner_actor_id="user:2",
                old_parameter_snapshot=snap,
                new_parameter_snapshot=_snapshot(),
            )

    def test_with_evidence_and_approvals(self):
        evidence = ValidationEvidence(
            test_type="Peel", sample_quantity=3, result="PASS",
            evidence_date="2026-09-05", conducted_by="user:3",
        )
        approval = ApprovalRecord(approver_actor_id="user:5", approval_date="2026-09-10", approved=True)
        ecr = _ecr_draft()
        # Cannot mutate frozen; verify construction with evidence/approval directly
        ecr2 = EngineeringChangeRequestDraft(
            identity=ecr.identity,
            part_revision_id=ecr.part_revision_id,
            requester_actor_id=ecr.requester_actor_id,
            request_date=ecr.request_date,
            reason=ecr.reason,
            owner_actor_id=ecr.owner_actor_id,
            old_parameter_snapshot=ecr.old_parameter_snapshot,
            new_parameter_snapshot=ecr.new_parameter_snapshot,
            validation_evidence=(evidence,),
            approvals=(approval,),
        )
        assert len(ecr2.validation_evidence) == 1
        assert ecr2.approvals[0].approved is True

    def test_with_release_metadata(self):
        rel = ReleaseMetadata(
            release_number="ECR-001-R1",
            release_date="2026-09-15",
            released_by_actor_id="user:10",
        )
        ecr = _ecr_draft()
        ecr2 = EngineeringChangeRequestDraft(
            identity=ecr.identity,
            part_revision_id=ecr.part_revision_id,
            requester_actor_id=ecr.requester_actor_id,
            request_date=ecr.request_date,
            reason=ecr.reason,
            owner_actor_id=ecr.owner_actor_id,
            old_parameter_snapshot=ecr.old_parameter_snapshot,
            new_parameter_snapshot=ecr.new_parameter_snapshot,
            status=EngineeringChangeStatus.RELEASED,
            release_metadata=rel,
        )
        assert ecr2.release_metadata is not None
        assert ecr2.release_metadata.release_number == "ECR-001-R1"
