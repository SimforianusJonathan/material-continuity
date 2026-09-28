from __future__ import annotations

import unittest
from pathlib import Path

from agents.evidence_specialist import (
    EvidenceInvestigationRequest,
    MockEvidenceRetriever,
    investigate_candidate,
)
from agents.evidence_specialist.fixtures import load_qualification_procedure_fixtures
from core.evidence.fixtures import load_evidence_extraction_fixtures
from core.requirements import CandidateDecision, ComparisonStatus
from core.requirements.fixtures import load_requirement_fixtures


class CanonicalEvidenceSpecialistTests(unittest.TestCase):
    def test_candidate_a_and_b_follow_canonical_evidence_branches(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        requirements, _ = load_requirement_fixtures(fixture_root)
        retriever = MockEvidenceRetriever(
            extractions=load_evidence_extraction_fixtures(fixture_root),
            procedures=load_qualification_procedure_fixtures(fixture_root),
        )

        candidate_a = investigate_candidate(
            EvidenceInvestigationRequest("CAND-A", requirements),
            retriever=retriever,
        )
        candidate_b = investigate_candidate(
            EvidenceInvestigationRequest("CAND-B", requirements),
            retriever=retriever,
        )

        a_rows = {row.requirement_id: row for row in candidate_a.comparison.rows}
        self.assertEqual(ComparisonStatus.UNKNOWN, a_rows["REQ-LUBE-TEMP-001"].status)
        self.assertEqual(
            {"QUAL-TEMP-001", "QUAL-RELEASE-001"},
            {item.procedure_id for item in candidate_a.qualification_procedures},
        )
        self.assertEqual(
            CandidateDecision.REJECTED_HARD_MISMATCH,
            candidate_b.comparison.decision,
        )
        self.assertEqual((), candidate_b.qualification_procedures)


if __name__ == "__main__":
    unittest.main()
