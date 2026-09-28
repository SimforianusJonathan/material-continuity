from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from core.qualification import build_qualification_graph
from core.qualification.fixtures import load_qualification_fixtures


class CanonicalQualificationFixtureTests(unittest.TestCase):
    def test_candidate_a_qualification_completes_after_shortage(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        tasks, calendars = load_qualification_fixtures(fixture_root)

        result = build_qualification_graph(
            candidate_id="CAND-A", tasks=tasks, calendars=calendars
        )

        self.assertTrue(result.resolved)
        self.assertEqual(date(2026, 10, 7), result.qualification_complete.date())
        self.assertGreater(result.qualification_complete.date(), date(2026, 10, 4))
        self.assertEqual(
            (
                "TASK-A-DELIVERY",
                "TASK-A-TEMP-TEST",
                "TASK-A-ENGINEERING-REVIEW",
                "TASK-A-QUALITY-REVIEW",
                "TASK-A-QUALIFICATION-RELEASE",
            ),
            result.critical_path,
        )


if __name__ == "__main__":
    unittest.main()
