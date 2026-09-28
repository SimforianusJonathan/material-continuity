from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from core.recovery_options import (
    RecoveryCategory,
    RecoverySearchRequest,
    find_recovery_options,
)
from core.recovery_options.fixtures import load_recovery_option_fixtures


class CanonicalRecoveryOptionFixtureTests(unittest.TestCase):
    def test_canonical_fixture_exhausts_approved_paths_before_candidates(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        options = load_recovery_option_fixtures(fixture_root)

        result = find_recovery_options(
            request=RecoverySearchRequest(
                material_id="MAT-BRG-001",
                required_quantity=700,
                need_by=date(2026, 10, 4),
                as_of=date(2026, 9, 29),
            ),
            options=options,
        )

        self.assertFalse(result.approved_recovery_sufficient)
        self.assertEqual(0, result.approved_covered_quantity)
        self.assertEqual(700, result.remaining_quantity)
        self.assertEqual(
            (
                RecoveryCategory.NETWORK_STOCK,
                RecoveryCategory.APPROVED_SOURCE,
                RecoveryCategory.APPROVED_EQUIVALENT,
                RecoveryCategory.ALTERNATE_BOM,
                RecoveryCategory.VALID_DEVIATION,
                RecoveryCategory.UNQUALIFIED_CANDIDATE,
                RecoveryCategory.ORIGINAL_EXPEDITE,
                RecoveryCategory.PRODUCTION_RESEQUENCING,
            ),
            tuple(step.category for step in result.search_trace),
        )
        self.assertEqual(
            ("CAND-A", "CAND-B", "CAND-C"),
            tuple(option.candidate_id for option in result.unqualified_candidates),
        )
        self.assertEqual(
            (True, True, False),
            tuple(option.arrives_by_need for option in result.unqualified_candidates),
        )
        self.assertEqual(
            ("EXPEDITE-ORIGINAL-001", "RESEQUENCE-PRODUCTION-001"),
            tuple(option.option_id for option in result.fallbacks),
        )


if __name__ == "__main__":
    unittest.main()
