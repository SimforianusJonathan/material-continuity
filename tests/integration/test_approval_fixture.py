from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.approval import (
    ApprovalBlockReason,
    ApprovalValidationRequest,
    ApproverRole,
    AuthenticatedPrincipal,
    ControlledAction,
    validate_approval,
)
from core.case_state import (
    ApprovalRecord,
    RecoveryCaseUpdate,
    append_approval,
    update_case,
)
from core.case_state.canonical import build_canonical_case


class CanonicalApprovalGateTests(unittest.TestCase):
    def test_valid_qualification_approval_becomes_stale_after_source_revision(self) -> None:
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
        request = ApprovalValidationRequest(
            approval_id=approval.approval_id,
            action=ControlledAction.CREATE_QUALIFICATION_TASK,
            principal=AuthenticatedPrincipal(
                principal_id=approval.approver_id,
                role=ApproverRole.QUALITY_ENGINEER,
            ),
            evaluated_at=created_at + timedelta(minutes=10),
            current_source_versions=case.current.source_versions,
            idempotency_key="case-001-create-qualification",
        )

        self.assertTrue(validate_approval(case, request).authorized)

        revised_sources = tuple(
            replace(source, version="3")
            if source.source_id == "SRC-CAND-A-DATASHEET"
            else source
            for source in case.current.source_versions
        )
        case = update_case(
            case,
            update=RecoveryCaseUpdate(source_versions=revised_sources),
            change_reason="Candidate A datasheet revision changed from 2 to 3.",
            updated_at=created_at + timedelta(hours=1),
        ).case
        stale_request = replace(
            request,
            evaluated_at=created_at + timedelta(hours=1, minutes=1),
            current_source_versions=case.current.source_versions,
        )
        decision = validate_approval(case, stale_request)

        self.assertFalse(decision.authorized)
        self.assertIn(ApprovalBlockReason.STALE_CASE_VERSION, decision.reasons)
        self.assertIn(ApprovalBlockReason.CASE_HASH_MISMATCH, decision.reasons)


if __name__ == "__main__":
    unittest.main()
