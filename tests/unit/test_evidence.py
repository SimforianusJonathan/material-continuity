from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal

from core.evidence import (
    EvidenceExclusionReason,
    EvidenceExtraction,
    EvidencePipelineInputError,
    ExtractionSupportStatus,
    compare_extracted_evidence,
    prepare_evidence,
)
from core.requirements import (
    ComparisonOperator,
    ComparisonStatus,
    Requirement,
    RequirementCriticality,
    RequirementKind,
)


class EvidencePipelineTests(unittest.TestCase):
    def test_supported_extraction_preserves_provenance(self) -> None:
        prepared = prepare_evidence((self.extraction(),))

        self.assertEqual(1, len(prepared.evidence))
        evidence = prepared.evidence[0]
        self.assertEqual("Candidate_A_Datasheet_Rev2.pdf", evidence.source_document)
        self.assertEqual("2", evidence.source_revision)
        self.assertEqual("2", evidence.source_page)
        self.assertEqual("Dimensions table, bore row", evidence.source_location)

    def test_unsupported_claim_is_excluded_and_requirement_remains_unknown(self) -> None:
        extraction = replace(
            self.extraction(),
            value=None,
            support_status=ExtractionSupportStatus.UNSUPPORTED,
        )

        result = compare_extracted_evidence(
            candidate_id="CAND-A",
            requirements=(self.requirement(),),
            extractions=(extraction,),
        )

        self.assertEqual((), result.prepared.evidence)
        self.assertEqual(
            EvidenceExclusionReason.UNSUPPORTED_CLAIM,
            result.prepared.exclusions[0].reason,
        )
        self.assertEqual(ComparisonStatus.UNKNOWN, result.comparison.rows[0].status)

    def test_missing_provenance_is_excluded(self) -> None:
        extraction = replace(self.extraction(), source_page="")

        prepared = prepare_evidence((extraction,))

        self.assertEqual((), prepared.evidence)
        self.assertEqual(
            EvidenceExclusionReason.MISSING_PROVENANCE,
            prepared.exclusions[0].reason,
        )

    def test_wrong_revision_flows_to_deterministic_unknown(self) -> None:
        extraction = replace(self.extraction(), current_source_revision="3")

        result = compare_extracted_evidence(
            candidate_id="CAND-A",
            requirements=(self.requirement(),),
            extractions=(extraction,),
        )

        self.assertEqual(ComparisonStatus.UNKNOWN, result.comparison.rows[0].status)
        self.assertIn("current source revision", result.comparison.rows[0].reason)

    def test_conflicting_supported_extractions_remain_unknown(self) -> None:
        conflicting = replace(
            self.extraction(),
            extraction_id="EXT-A-BORE-2",
            value=Decimal("30"),
        )

        result = compare_extracted_evidence(
            candidate_id="CAND-A",
            requirements=(self.requirement(),),
            extractions=(self.extraction(), conflicting),
        )

        self.assertEqual(ComparisonStatus.UNKNOWN, result.comparison.rows[0].status)
        self.assertIn("conflicting", result.comparison.rows[0].reason)

    def test_duplicate_extraction_ids_fail_closed(self) -> None:
        with self.assertRaisesRegex(EvidencePipelineInputError, "duplicate"):
            prepare_evidence((self.extraction(), self.extraction()))

    def test_confidence_outside_zero_to_one_is_rejected(self) -> None:
        extraction = replace(
            self.extraction(), extraction_confidence=Decimal("1.01")
        )

        with self.assertRaisesRegex(EvidencePipelineInputError, "between 0 and 1"):
            prepare_evidence((extraction,))

    def extraction(self) -> EvidenceExtraction:
        return EvidenceExtraction(
            extraction_id="EXT-A-BORE",
            candidate_id="CAND-A",
            property="BORE_DIAMETER",
            value=Decimal("25"),
            unit="mm",
            source_document="Candidate_A_Datasheet_Rev2.pdf",
            source_revision="2",
            current_source_revision="2",
            source_page="2",
            source_location="Dimensions table, bore row",
            applicability="BEARING-SEAT-25MM",
            applicable=True,
            support_status=ExtractionSupportStatus.SUPPORTED,
            extraction_confidence=Decimal("0.99"),
        )

    def requirement(self) -> Requirement:
        return Requirement(
            requirement_id="REQ-BORE-001",
            product_id="ASSEMBLY-A",
            application_id="BEARING-SEAT-25MM",
            property="BORE_DIAMETER",
            name="Bore diameter",
            operator=ComparisonOperator.EQUAL,
            required_value=Decimal("25"),
            unit="mm",
            criticality=RequirementCriticality.HARD,
            kind=RequirementKind.TECHNICAL,
            source_document="Engineering_Drawing_Assembly_A.pdf",
            source_revision="A",
        )


if __name__ == "__main__":
    unittest.main()
