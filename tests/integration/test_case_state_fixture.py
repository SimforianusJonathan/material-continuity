from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.case_state import (
    ApprovalRecord,
    RecoveryCaseUpdate,
    append_approval,
    update_case,
)
from core.case_state.canonical import build_canonical_case


class CanonicalCaseVersioningTests(unittest.TestCase):
    def test_document_revision_creates_new_version_and_leaves_approval_stale(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        created_at = datetime(2026, 9, 29, 3, tzinfo=timezone.utc)
        case = build_canonical_case(fixture_root, created_at=created_at)
        approval = ApprovalRecord(
            approval_id="APR-001",
            case_id=case.case_id,
            case_version=case.current.case_version,
            case_hash=case.current.case_hash,
            approver_id="quality-reviewer-1",
            approver_role="QUALITY_ENGINEER",
            permitted_action="CREATE_QUALIFICATION_TASK",
            approved_at=created_at + timedelta(minutes=5),
            expires_at=created_at + timedelta(hours=8),
        )
        case = append_approval(
            case, approval, updated_at=created_at + timedelta(minutes=5)
        )
        revised_sources = tuple(
            replace(source, version="3")
            if source.source_id == "SRC-CAND-A-DATASHEET"
            else source
            for source in case.current.source_versions
        )

        result = update_case(
            case,
            update=RecoveryCaseUpdate(source_versions=revised_sources),
            change_reason="Candidate A datasheet revision changed from 2 to 3.",
            updated_at=created_at + timedelta(hours=1),
        )

        self.assertEqual(2, result.case.current.case_version)
        self.assertEqual(1, len(result.case.approvals))
        self.assertNotEqual(
            result.case.approvals[0].case_version,
            result.case.current.case_version,
        )
        self.assertNotEqual(
            result.case.approvals[0].case_hash,
            result.case.current.case_hash,
        )


if __name__ == "__main__":
    unittest.main()
