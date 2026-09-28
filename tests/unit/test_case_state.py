from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.case_state import (
    ActionReceipt,
    ApprovalRecord,
    RecoveryCaseInputError,
    RecoveryCaseUpdate,
    append_action_receipt,
    append_approval,
    update_case,
)
from core.case_state.canonical import build_canonical_case


FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "fixtures"
CREATED_AT = datetime(2026, 9, 29, 3, tzinfo=timezone.utc)


class RecoveryCaseStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = build_canonical_case(FIXTURE_ROOT, created_at=CREATED_AT)

    def test_case_hash_is_deterministic(self) -> None:
        second = build_canonical_case(FIXTURE_ROOT, created_at=CREATED_AT)
        self.assertEqual(self.case.current.case_hash, second.current.case_hash)
        self.assertEqual(64, len(self.case.current.case_hash))

    def test_noop_update_does_not_increment_version(self) -> None:
        result = update_case(
            self.case,
            update=RecoveryCaseUpdate(),
            change_reason="No effective source change.",
            updated_at=CREATED_AT + timedelta(hours=1),
        )
        self.assertFalse(result.version_changed)
        self.assertIs(self.case, result.case)

    def test_source_revision_change_increments_version_and_chains_hash(self) -> None:
        sources = tuple(
            replace(source, version="3")
            if source.source_id == "SRC-CAND-A-DATASHEET"
            else source
            for source in self.case.current.source_versions
        )
        result = update_case(
            self.case,
            update=RecoveryCaseUpdate(source_versions=sources),
            change_reason="Candidate A datasheet revision changed from 2 to 3.",
            updated_at=CREATED_AT + timedelta(hours=1),
        )

        self.assertTrue(result.version_changed)
        self.assertEqual(2, result.case.current.case_version)
        self.assertEqual(
            self.case.current.case_hash, result.case.current.previous_case_hash
        )
        self.assertNotEqual(self.case.current.case_hash, result.case.current.case_hash)
        self.assertEqual(("SRC-CAND-A-DATASHEET",), result.changed_source_ids)

    def test_approval_is_stored_without_incrementing_decision_version(self) -> None:
        approval = self.approval()
        updated = append_approval(
            self.case, approval, updated_at=CREATED_AT + timedelta(minutes=10)
        )

        self.assertEqual(1, updated.current.case_version)
        self.assertEqual((approval,), updated.approvals)

    def test_approval_with_wrong_hash_fails_closed(self) -> None:
        approval = replace(self.approval(), case_hash="wrong")

        with self.assertRaisesRegex(RecoveryCaseInputError, "hash does not match"):
            append_approval(
                self.case,
                approval,
                updated_at=CREATED_AT + timedelta(minutes=10),
            )

    def test_action_receipt_is_stored_without_incrementing_decision_version(self) -> None:
        action = self.action()
        updated = append_action_receipt(
            self.case, action, updated_at=CREATED_AT + timedelta(minutes=10)
        )

        self.assertEqual(1, updated.current.case_version)
        self.assertEqual((action,), updated.actions)

    def test_duplicate_action_idempotency_key_fails_closed(self) -> None:
        action = self.action()
        case = append_action_receipt(
            self.case, action, updated_at=CREATED_AT + timedelta(minutes=10)
        )
        duplicate = replace(action, action_id="ACT-002")

        with self.assertRaisesRegex(RecoveryCaseInputError, "idempotency key"):
            append_action_receipt(
                case,
                duplicate,
                updated_at=CREATED_AT + timedelta(minutes=11),
            )

    def test_update_timestamp_cannot_move_backwards(self) -> None:
        with self.assertRaisesRegex(RecoveryCaseInputError, "cannot move backwards"):
            update_case(
                self.case,
                update=RecoveryCaseUpdate(),
                change_reason="Invalid time.",
                updated_at=CREATED_AT - timedelta(seconds=1),
            )

    def approval(self) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id="APR-001",
            case_id=self.case.case_id,
            case_version=self.case.current.case_version,
            case_hash=self.case.current.case_hash,
            approver_id="quality-reviewer-1",
            approver_role="QUALITY_ENGINEER",
            permitted_action="CREATE_QUALIFICATION_TASK",
            approved_at=CREATED_AT + timedelta(minutes=5),
            expires_at=CREATED_AT + timedelta(hours=8),
        )

    def action(self) -> ActionReceipt:
        return ActionReceipt(
            action_id="ACT-001",
            case_id=self.case.case_id,
            case_version=self.case.current.case_version,
            case_hash=self.case.current.case_hash,
            action_type="CREATE_QUALIFICATION_TASK",
            external_reference="QMS-QUAL-00001",
            idempotency_key="case-001-create-qualification",
            status="CREATED",
            executed_at=CREATED_AT + timedelta(minutes=9),
        )


if __name__ == "__main__":
    unittest.main()
