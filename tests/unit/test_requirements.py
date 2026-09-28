from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal

from core.requirements import (
    CandidateEvidence,
    ComparisonOperator,
    ComparisonStatus,
    Requirement,
    RequirementCriticality,
    RequirementInputError,
    RequirementKind,
    compare_requirement,
    compare_requirements,
)


class RequirementComparisonTests(unittest.TestCase):
    def test_exact_match(self) -> None:
        result = self.compare(required="25", observed="25")
        self.assertEqual(ComparisonStatus.MATCH, result.status)

    def test_minimum_bound_match(self) -> None:
        result = self.compare(
            required="14",
            observed="16",
            operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            unit="kN",
        )
        self.assertEqual(ComparisonStatus.MATCH, result.status)

    def test_maximum_bound_match(self) -> None:
        result = self.compare(
            required="120",
            observed="110",
            operator=ComparisonOperator.LESS_THAN_OR_EQUAL,
            unit="C",
        )
        self.assertEqual(ComparisonStatus.MATCH, result.status)

    def test_hard_mismatch_rejects(self) -> None:
        result = self.compare(required="25", observed="30")
        self.assertEqual(ComparisonStatus.MISMATCH, result.status)
        self.assertTrue(result.hard_reject)

    def test_missing_evidence_remains_unknown(self) -> None:
        result = compare_requirement(
            candidate_id="CAND-A", requirement=self.requirement(), evidence=()
        )
        self.assertEqual(ComparisonStatus.UNKNOWN, result.status)
        self.assertIn("No evidence", result.reason)

    def test_incompatible_units_remain_unknown(self) -> None:
        result = self.compare(required="25", observed="25", observed_unit="kN")
        self.assertEqual(ComparisonStatus.UNKNOWN, result.status)
        self.assertIn("cannot convert", result.reason)

    def test_convertible_units_are_normalized(self) -> None:
        result = self.compare(required="25.4", observed="1", observed_unit="in")
        self.assertEqual(ComparisonStatus.MATCH, result.status)
        self.assertEqual(Decimal("25.4"), result.normalized_observed_value)

    def test_wrong_document_revision_remains_unknown(self) -> None:
        evidence = replace(self.evidence(), source_revision="1", current_source_revision="2")
        result = compare_requirement(
            candidate_id="CAND-A",
            requirement=self.requirement(),
            evidence=(evidence,),
        )
        self.assertEqual(ComparisonStatus.UNKNOWN, result.status)
        self.assertIn("current source revision", result.reason)

    def test_conflicting_evidence_remains_unknown(self) -> None:
        first = self.evidence(value=Decimal("25"), evidence_id="EVD-1")
        second = self.evidence(value=Decimal("30"), evidence_id="EVD-2")
        result = compare_requirement(
            candidate_id="CAND-A",
            requirement=self.requirement(),
            evidence=(first, second),
        )
        self.assertEqual(ComparisonStatus.UNKNOWN, result.status)
        self.assertIn("conflicting", result.reason)

    def test_unsatisfied_release_gate_is_blocked(self) -> None:
        requirement = replace(
            self.requirement(),
            property="PLANT_RELEASE",
            required_value=True,
            unit=None,
            criticality=RequirementCriticality.CRITICAL,
            kind=RequirementKind.RELEASE_GATE,
        )
        evidence = replace(
            self.evidence(value=False), property="PLANT_RELEASE", unit=None
        )
        result = compare_requirement(
            candidate_id="CAND-A", requirement=requirement, evidence=(evidence,)
        )
        self.assertEqual(ComparisonStatus.BLOCKED, result.status)
        self.assertFalse(result.hard_reject)

    def test_wrong_value_type_remains_unknown(self) -> None:
        requirement = replace(self.requirement(), required_value=True, unit=None)
        evidence = replace(self.evidence(value="yes"), unit=None)

        result = compare_requirement(
            candidate_id="CAND-A", requirement=requirement, evidence=(evidence,)
        )

        self.assertEqual(ComparisonStatus.UNKNOWN, result.status)
        self.assertIn("types do not match", result.reason)

    def test_empty_requirement_set_fails_closed(self) -> None:
        with self.assertRaisesRegex(RequirementInputError, "at least one requirement"):
            compare_requirements(
                candidate_id="CAND-A", requirements=(), evidence=(self.evidence(),)
            )

    def compare(
        self,
        *,
        required: str,
        observed: str,
        operator: ComparisonOperator = ComparisonOperator.EQUAL,
        unit: str = "mm",
        observed_unit: str | None = None,
    ):
        requirement = replace(
            self.requirement(),
            operator=operator,
            required_value=Decimal(required),
            unit=unit,
        )
        evidence = self.evidence(
            value=Decimal(observed), unit=observed_unit or unit
        )
        return compare_requirement(
            candidate_id="CAND-A", requirement=requirement, evidence=(evidence,)
        )

    @staticmethod
    def requirement() -> Requirement:
        return Requirement(
            requirement_id="REQ-1",
            product_id="ASSEMBLY-A",
            application_id="APP-1",
            property="BORE",
            name="Bore",
            operator=ComparisonOperator.EQUAL,
            required_value=Decimal("25"),
            unit="mm",
            criticality=RequirementCriticality.HARD,
            kind=RequirementKind.TECHNICAL,
            source_document="drawing.pdf",
            source_revision="A",
        )

    @staticmethod
    def evidence(
        value=Decimal("25"), evidence_id: str = "EVD-1", unit: str | None = "mm"
    ) -> CandidateEvidence:
        return CandidateEvidence(
            evidence_id=evidence_id,
            candidate_id="CAND-A",
            property="BORE",
            value=value,
            unit=unit,
            source_document="candidate.pdf",
            source_revision="2",
            current_source_revision="2",
            source_page="2",
            source_location="table",
            applicability="APP-1",
            applicable=True,
        )


if __name__ == "__main__":
    unittest.main()
