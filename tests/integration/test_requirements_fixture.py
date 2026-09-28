from __future__ import annotations

import unittest
from pathlib import Path

from core.requirements import (
    CandidateDecision,
    ComparisonStatus,
    compare_requirements,
)
from core.requirements.fixtures import load_requirement_fixtures


class CanonicalRequirementFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        cls.requirements, cls.evidence = load_requirement_fixtures(fixture_root)

    def test_candidate_a_preserves_missing_evidence_as_unknown(self) -> None:
        result = compare_requirements(
            candidate_id="CAND-A",
            requirements=self.requirements,
            evidence=self.evidence,
        )
        statuses = {row.requirement_id: row.status for row in result.rows}

        self.assertEqual(
            CandidateDecision.BLOCKED_PENDING_EVIDENCE_OR_RELEASE,
            result.decision,
        )
        self.assertEqual(ComparisonStatus.MATCH, statuses["REQ-BORE-001"])
        self.assertEqual(ComparisonStatus.MATCH, statuses["REQ-LOAD-001"])
        self.assertEqual(ComparisonStatus.UNKNOWN, statuses["REQ-LUBE-TEMP-001"])
        self.assertEqual(ComparisonStatus.BLOCKED, statuses["REQ-RELEASE-001"])

    def test_candidate_b_is_rejected_for_hard_bore_mismatch(self) -> None:
        result = compare_requirements(
            candidate_id="CAND-B",
            requirements=self.requirements,
            evidence=self.evidence,
        )
        statuses = {row.requirement_id: row.status for row in result.rows}

        self.assertEqual(CandidateDecision.REJECTED_HARD_MISMATCH, result.decision)
        self.assertEqual(ComparisonStatus.MISMATCH, statuses["REQ-BORE-001"])
        self.assertEqual(ComparisonStatus.MATCH, statuses["REQ-LOAD-001"])
        self.assertEqual(ComparisonStatus.MATCH, statuses["REQ-LUBE-TEMP-001"])
        self.assertEqual(ComparisonStatus.BLOCKED, statuses["REQ-RELEASE-001"])


if __name__ == "__main__":
    unittest.main()
