from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date

from core.recovery_options import (
    ApprovalStatus,
    RecoveryCategory,
    RecoveryOptionInputError,
    RecoveryOptionRecord,
    RecoverySearchRequest,
    find_recovery_options,
)


REQUEST = RecoverySearchRequest(
    material_id="MAT-1",
    required_quantity=100,
    need_by=date(2026, 10, 4),
    as_of=date(2026, 9, 29),
)


class RecoveryOptionEngineTests(unittest.TestCase):
    def test_sufficient_network_stock_stops_before_unqualified_candidates(self) -> None:
        result = find_recovery_options(
            request=REQUEST,
            options=(
                self.option("NET-1", RecoveryCategory.NETWORK_STOCK, 100, 3),
                self.option(
                    "CAND-1",
                    RecoveryCategory.UNQUALIFIED_CANDIDATE,
                    500,
                    2,
                    approval=ApprovalStatus.UNQUALIFIED,
                ),
            ),
        )

        self.assertTrue(result.approved_recovery_sufficient)
        self.assertEqual(100, result.approved_covered_quantity)
        self.assertEqual((), result.unqualified_candidates)
        self.assertEqual(
            (RecoveryCategory.NETWORK_STOCK,),
            tuple(step.category for step in result.search_trace),
        )

    def test_partial_approved_paths_accumulate_in_required_order(self) -> None:
        request = RecoverySearchRequest("MAT-1", 150, date(2026, 10, 4), date(2026, 9, 29))
        result = find_recovery_options(
            request=request,
            options=(
                self.option("SOURCE-1", RecoveryCategory.APPROVED_SOURCE, 100, 3),
                self.option("NET-1", RecoveryCategory.NETWORK_STOCK, 50, 3),
            ),
        )

        self.assertEqual(
            ("NET-1", "SOURCE-1"),
            tuple(option.option_id for option in result.approved_options),
        )
        self.assertEqual((50, 100), tuple(option.coverage_quantity for option in result.approved_options))
        self.assertTrue(result.approved_recovery_sufficient)

    def test_late_approved_option_does_not_count_as_coverage(self) -> None:
        result = find_recovery_options(
            request=REQUEST,
            options=(self.option("NET-LATE", RecoveryCategory.NETWORK_STOCK, 100, 5),),
        )

        self.assertFalse(result.approved_recovery_sufficient)
        self.assertEqual(100, result.remaining_quantity)
        self.assertEqual((), result.approved_options)

    def test_expired_deviation_is_not_approved_coverage(self) -> None:
        deviation = self.option("DEV-1", RecoveryCategory.VALID_DEVIATION, 100, 3)
        deviation = replace(deviation, valid_until=date(2026, 10, 3))

        result = find_recovery_options(request=REQUEST, options=(deviation,))

        self.assertFalse(result.approved_recovery_sufficient)
        self.assertEqual("NONE", result.search_trace[4].outcome)

    def test_duplicate_option_ids_fail_closed(self) -> None:
        duplicate = self.option("NET-1", RecoveryCategory.NETWORK_STOCK, 100, 3)

        with self.assertRaisesRegex(RecoveryOptionInputError, "duplicate recovery option ID"):
            find_recovery_options(request=REQUEST, options=(duplicate, duplicate))

    @staticmethod
    def option(
        option_id: str,
        category: RecoveryCategory,
        quantity: int,
        ready_day: int,
        approval: ApprovalStatus = ApprovalStatus.APPROVED,
    ) -> RecoveryOptionRecord:
        return RecoveryOptionRecord(
            option_id=option_id,
            category=category,
            material_id="MAT-1",
            description=option_id,
            available_quantity=quantity,
            ready_date=date(2026, 10, ready_day),
            approval_status=approval,
            source_reference=f"fixture:{option_id}",
        )


if __name__ == "__main__":
    unittest.main()
