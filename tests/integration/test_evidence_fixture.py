from __future__ import annotations

import unittest
from pathlib import Path

from core.evidence import EvidenceExclusionReason, compare_extracted_evidence
from core.evidence.fixtures import load_evidence_extraction_fixtures
from core.requirements import CandidateDecision, ComparisonStatus
from core.requirements.fixtures import load_requirement_fixtures


class CanonicalEvidencePipelineTests(unittest.TestCase):
    def test_structured_extractions_reproduce_candidate_a_and_b_decisions(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        requirements, _ = load_requirement_fixtures(fixture_root)
        extractions = load_evidence_extraction_fixtures(fixture_root)

        candidate_a = compare_extracted_evidence(
            candidate_id="CAND-A",
            requirements=requirements,
            extractions=extractions,
        )
        candidate_b = compare_extracted_evidence(
            candidate_id="CAND-B",
            requirements=requirements,
            extractions=extractions,
        )

        a_rows = {row.requirement_id: row for row in candidate_a.comparison.rows}
        self.assertEqual(ComparisonStatus.MATCH, a_rows["REQ-BORE-001"].status)
        self.assertEqual(ComparisonStatus.MATCH, a_rows["REQ-LOAD-001"].status)
        self.assertEqual(ComparisonStatus.UNKNOWN, a_rows["REQ-LUBE-TEMP-001"].status)
        self.assertEqual(ComparisonStatus.BLOCKED, a_rows["REQ-RELEASE-001"].status)
        self.assertEqual(
            CandidateDecision.BLOCKED_PENDING_EVIDENCE_OR_RELEASE,
            candidate_a.comparison.decision,
        )
        self.assertEqual(
            EvidenceExclusionReason.UNSUPPORTED_CLAIM,
            candidate_a.prepared.exclusions[0].reason,
        )

        self.assertEqual(
            CandidateDecision.REJECTED_HARD_MISMATCH,
            candidate_b.comparison.decision,
        )
        self.assertTrue(
            all(
                evidence.candidate_id == "CAND-B"
                for evidence in candidate_b.prepared.evidence
            )
        )
        self.assertEqual((), candidate_b.prepared.exclusions)


if __name__ == "__main__":
    unittest.main()
