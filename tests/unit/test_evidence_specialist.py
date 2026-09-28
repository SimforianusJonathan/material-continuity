from __future__ import annotations

import unittest
from pathlib import Path

from agents.evidence_specialist import (
    EvidenceInvestigationRequest,
    EvidenceSpecialistInputError,
    MockEvidenceRetriever,
    RetrievalTool,
    SYSTEM_PROMPT,
    investigate_candidate,
)
from agents.evidence_specialist.fixtures import (
    load_qualification_procedure_fixtures,
)
from core.evidence.fixtures import load_evidence_extraction_fixtures
from core.requirements import CandidateDecision, ComparisonStatus
from core.requirements.fixtures import load_requirement_fixtures


FIXTURE_ROOT = Path(__file__).parents[2] / "data" / "fixtures"


class EvidenceSpecialistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.requirements, _ = load_requirement_fixtures(FIXTURE_ROOT)
        cls.retriever = MockEvidenceRetriever(
            extractions=load_evidence_extraction_fixtures(FIXTURE_ROOT),
            procedures=load_qualification_procedure_fixtures(FIXTURE_ROOT),
        )

    def test_candidate_a_reports_evidence_and_release_gaps(self) -> None:
        result = self.investigate("CAND-A")
        gaps = {gap.requirement_id: gap for gap in result.gaps}

        self.assertEqual(ComparisonStatus.UNKNOWN, gaps["REQ-LUBE-TEMP-001"].status)
        self.assertEqual(("QUAL-TEMP-001",), gaps["REQ-LUBE-TEMP-001"].qualification_procedure_ids)
        self.assertEqual(ComparisonStatus.BLOCKED, gaps["REQ-RELEASE-001"].status)
        self.assertEqual(("QUAL-RELEASE-001",), gaps["REQ-RELEASE-001"].qualification_procedure_ids)
        self.assertEqual(2, len(result.retrieval_trace))

    def test_candidate_b_hard_mismatch_stops_procedure_retrieval(self) -> None:
        result = self.investigate("CAND-B")

        self.assertEqual(
            CandidateDecision.REJECTED_HARD_MISMATCH,
            result.comparison.decision,
        )
        self.assertEqual(("REQ-BORE-001",), result.hard_mismatch_requirement_ids)
        self.assertEqual((), result.qualification_procedures)
        self.assertEqual(1, len(result.retrieval_trace))
        self.assertEqual(
            RetrievalTool.CANDIDATE_EVIDENCE,
            result.retrieval_trace[0].tool,
        )

    def test_mock_retriever_filters_candidate_and_requirement_properties(self) -> None:
        rows = self.retriever.retrieve_candidate_evidence(
            candidate_id="CAND-A",
            properties=("BORE_DIAMETER",),
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("EXT-A-BORE", rows[0].extraction_id)

    def test_system_prompt_preserves_agent_boundaries(self) -> None:
        self.assertIn("never as authorization", SYSTEM_PROMPT)
        self.assertIn("UNKNOWN", SYSTEM_PROMPT)
        self.assertIn("deterministic tools", SYSTEM_PROMPT)
        self.assertIn("does not release material", SYSTEM_PROMPT)

    def test_empty_requirement_request_fails_closed(self) -> None:
        with self.assertRaisesRegex(EvidenceSpecialistInputError, "requirement"):
            investigate_candidate(
                EvidenceInvestigationRequest(
                    candidate_id="CAND-A",
                    requirements=(),
                ),
                retriever=self.retriever,
            )

    def investigate(self, candidate_id: str):
        return investigate_candidate(
            EvidenceInvestigationRequest(
                candidate_id=candidate_id,
                requirements=self.requirements,
            ),
            retriever=self.retriever,
        )


if __name__ == "__main__":
    unittest.main()
