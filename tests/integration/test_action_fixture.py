from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.actions import CreateQualificationTaskCommand, create_qualification_task
from core.approval import (
    ApprovalBlockReason,
    ApprovalValidationRequest,
    ApproverRole,
    AuthenticatedPrincipal,
    ControlledAction,
)
from core.case_state import ApprovalRecord, append_approval
from core.case_state.canonical import build_canonical_case


class CanonicalQualificationTaskActionTests(unittest.TestCase):
    def test_canonical_approval_creates_one_task_and_duplicate_is_blocked(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        created_at = datetime(2026, 9, 29, 3, tzinfo=timezone.utc)
        case = build_canonical_case(fixture_root, created_at=created_at)
        approval = ApprovalRecord(
            approval_id="APR-001",
            case_id=case.case_id,
            case_version=case.current.case_version,
            case_hash=case.current.case_hash,
            approver_id="quality-reviewer-1",
            approver_role=ApproverRole.QUALITY_ENGINEER.value,
            permitted_action=ControlledAction.CREATE_QUALIFICATION_TASK.value,
            approved_at=created_at + timedelta(minutes=5),
            expires_at=created_at + timedelta(hours=8),
        )
        case = append_approval(case, approval, updated_at=approval.approved_at)
        command = CreateQualificationTaskCommand(
            candidate_id="CAND-A",
            requirement_id="REQ-LUBE-TEMP-001",
            task_name="Candidate A lubricant temperature qualification",
            approval=ApprovalValidationRequest(
                approval_id=approval.approval_id,
                action=ControlledAction.CREATE_QUALIFICATION_TASK,
                principal=AuthenticatedPrincipal(
                    principal_id=approval.approver_id,
                    role=ApproverRole.QUALITY_ENGINEER,
                ),
                evaluated_at=created_at + timedelta(minutes=10),
                current_source_versions=case.current.source_versions,
                idempotency_key="case-001-create-qualification-cand-a-temp",
            ),
        )

        first = create_qualification_task(case, command)
        duplicate = create_qualification_task(first.case, command)

        self.assertTrue(first.created)
        self.assertEqual("CREATE_QUALIFICATION_TASK", first.action_receipt.action_type)
        self.assertFalse(first.production_release_authorized)
        self.assertFalse(duplicate.created)
        self.assertIn(
            ApprovalBlockReason.DUPLICATE_ACTION,
            duplicate.approval_decision.reasons,
        )
        self.assertEqual(1, len(duplicate.case.actions))


if __name__ == "__main__":
    unittest.main()
