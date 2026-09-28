from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.approval import (
    ApprovalBlockReason,
    ApprovalGateInputError,
    ApprovalGateStatus,
    ApprovalValidationRequest,
    ApproverRole,
    AuthenticatedPrincipal,
    ControlledAction,
    validate_approval,
)
from core.case_state import (
    ActionReceipt,
    ApprovalRecord,
    RecoveryCaseUpdate,
    append_action_receipt,
    append_approval,
    update_case,
)
from core.case_state.canonical import build_canonical_case


FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "fixtures"
CREATED_AT = datetime(2026, 9, 29, 3, tzinfo=timezone.utc)
EVALUATED_AT = CREATED_AT + timedelta(minutes=10)


class ApprovalGateTests(unittest.TestCase):
    def setUp(self) -> None:
        case = build_canonical_case(FIXTURE_ROOT, created_at=CREATED_AT)
        self.approval = ApprovalRecord(
            approval_id="APR-001",
            case_id=case.case_id,
            case_version=case.current.case_version,
            case_hash=case.current.case_hash,
            approver_id="quality-reviewer-1",
            approver_role=ApproverRole.QUALITY_ENGINEER.value,
            permitted_action=ControlledAction.CREATE_QUALIFICATION_TASK.value,
            approved_at=CREATED_AT + timedelta(minutes=5),
            expires_at=CREATED_AT + timedelta(hours=8),
        )
        self.case = append_approval(case, self.approval, updated_at=self.approval.approved_at)

    def test_valid_current_approval_authorizes_exact_action(self) -> None:
        decision = validate_approval(self.case, self.request())

        self.assertTrue(decision.authorized)
        self.assertEqual(ApprovalGateStatus.AUTHORIZED, decision.status)
        self.assertEqual((), decision.reasons)
        self.assertEqual((), decision.changed_source_ids)

    def test_wrong_principal_identity_is_blocked(self) -> None:
        request = replace(
            self.request(),
            principal=AuthenticatedPrincipal(
                principal_id="different-user",
                role=ApproverRole.QUALITY_ENGINEER,
            ),
        )

        decision = validate_approval(self.case, request)

        self.assertFalse(decision.authorized)
        self.assertIn(ApprovalBlockReason.PRINCIPAL_ID_MISMATCH, decision.reasons)

    def test_role_without_action_permission_is_blocked(self) -> None:
        request = replace(
            self.request(),
            principal=AuthenticatedPrincipal(
                principal_id=self.approval.approver_id,
                role=ApproverRole.PRODUCTION_PLANNER,
            ),
        )

        decision = validate_approval(self.case, request)

        self.assertIn(ApprovalBlockReason.PRINCIPAL_ROLE_MISMATCH, decision.reasons)
        self.assertIn(ApprovalBlockReason.ROLE_NOT_PERMITTED, decision.reasons)

    def test_action_outside_approval_scope_is_blocked(self) -> None:
        request = replace(
            self.request(), action=ControlledAction.AUTHORIZE_RESEQUENCING
        )

        decision = validate_approval(self.case, request)

        self.assertIn(ApprovalBlockReason.ROLE_NOT_PERMITTED, decision.reasons)
        self.assertIn(ApprovalBlockReason.ACTION_SCOPE_MISMATCH, decision.reasons)

    def test_expired_approval_is_blocked_at_expiry_boundary(self) -> None:
        request = replace(self.request(), evaluated_at=self.approval.expires_at)

        decision = validate_approval(self.case, request)

        self.assertEqual((ApprovalBlockReason.APPROVAL_EXPIRED,), decision.reasons)

    def test_case_update_makes_prior_approval_stale(self) -> None:
        revised_sources = tuple(
            replace(source, version="3")
            if source.source_id == "SRC-CAND-A-DATASHEET"
            else source
            for source in self.case.current.source_versions
        )
        updated = update_case(
            self.case,
            update=RecoveryCaseUpdate(source_versions=revised_sources),
            change_reason="Candidate A datasheet revision changed.",
            updated_at=CREATED_AT + timedelta(hours=1),
        ).case
        request = replace(
            self.request(),
            evaluated_at=CREATED_AT + timedelta(hours=1, minutes=1),
            current_source_versions=updated.current.source_versions,
        )

        decision = validate_approval(updated, request)

        self.assertIn(ApprovalBlockReason.STALE_CASE_VERSION, decision.reasons)
        self.assertIn(ApprovalBlockReason.CASE_HASH_MISMATCH, decision.reasons)

    def test_live_source_change_is_blocked_even_before_case_update(self) -> None:
        live_sources = tuple(
            replace(source, version="3")
            if source.source_id == "SRC-CAND-A-DATASHEET"
            else source
            for source in self.case.current.source_versions
        )
        decision = validate_approval(
            self.case,
            replace(self.request(), current_source_versions=live_sources),
        )

        self.assertEqual(
            (ApprovalBlockReason.SOURCE_STATE_CHANGED,), decision.reasons
        )
        self.assertEqual(("SRC-CAND-A-DATASHEET",), decision.changed_source_ids)

    def test_used_idempotency_key_is_blocked_before_execution(self) -> None:
        action = ActionReceipt(
            action_id="ACT-001",
            case_id=self.case.case_id,
            case_version=self.case.current.case_version,
            case_hash=self.case.current.case_hash,
            action_type=ControlledAction.CREATE_QUALIFICATION_TASK.value,
            external_reference="QMS-QUAL-00001",
            idempotency_key="case-001-create-qualification",
            status="CREATED",
            executed_at=EVALUATED_AT,
        )
        case = append_action_receipt(
            self.case, action, updated_at=EVALUATED_AT
        )

        decision = validate_approval(case, self.request())

        self.assertEqual((ApprovalBlockReason.DUPLICATE_ACTION,), decision.reasons)

    def test_unknown_approval_is_blocked(self) -> None:
        decision = validate_approval(
            self.case, replace(self.request(), approval_id="APR-UNKNOWN")
        )

        self.assertEqual((ApprovalBlockReason.APPROVAL_NOT_FOUND,), decision.reasons)

    def test_naive_evaluation_timestamp_is_rejected(self) -> None:
        request = replace(
            self.request(), evaluated_at=datetime(2026, 9, 29, 3, 10)
        )

        with self.assertRaisesRegex(ApprovalGateInputError, "timezone-aware"):
            validate_approval(self.case, request)

    def request(self) -> ApprovalValidationRequest:
        return ApprovalValidationRequest(
            approval_id=self.approval.approval_id,
            action=ControlledAction.CREATE_QUALIFICATION_TASK,
            principal=AuthenticatedPrincipal(
                principal_id=self.approval.approver_id,
                role=ApproverRole.QUALITY_ENGINEER,
            ),
            evaluated_at=EVALUATED_AT,
            current_source_versions=self.case.current.source_versions,
            idempotency_key="case-001-create-qualification",
        )


if __name__ == "__main__":
    unittest.main()
