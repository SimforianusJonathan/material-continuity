"""Retrieval interface and local mock adapter for the Evidence Specialist."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from core.evidence import EvidenceExtraction

from .models import EvidenceSpecialistInputError, QualificationProcedureReference


class EvidenceRetriever(Protocol):
    def retrieve_candidate_evidence(
        self,
        *,
        candidate_id: str,
        properties: Sequence[str],
    ) -> tuple[EvidenceExtraction, ...]: ...

    def retrieve_qualification_procedures(
        self,
        *,
        requirement_ids: Sequence[str],
    ) -> tuple[QualificationProcedureReference, ...]: ...


class MockEvidenceRetriever:
    """Fixture-backed retriever with the same boundary expected from Bedrock."""

    def __init__(
        self,
        *,
        extractions: Iterable[EvidenceExtraction],
        procedures: Iterable[QualificationProcedureReference],
    ) -> None:
        self._extractions = tuple(extractions)
        self._procedures = tuple(procedures)
        _require_unique_ids(
            "extraction", (item.extraction_id for item in self._extractions)
        )
        _require_unique_ids(
            "procedure", (item.procedure_id for item in self._procedures)
        )

    def retrieve_candidate_evidence(
        self,
        *,
        candidate_id: str,
        properties: Sequence[str],
    ) -> tuple[EvidenceExtraction, ...]:
        property_set = set(properties)
        return tuple(
            item
            for item in self._extractions
            if item.candidate_id == candidate_id and item.property in property_set
        )

    def retrieve_qualification_procedures(
        self,
        *,
        requirement_ids: Sequence[str],
    ) -> tuple[QualificationProcedureReference, ...]:
        requirement_set = set(requirement_ids)
        return tuple(
            item
            for item in self._procedures
            if item.requirement_id in requirement_set
        )


def _require_unique_ids(entity: str, identifiers: Iterable[str]) -> None:
    seen: set[str] = set()
    for identifier in identifiers:
        if not identifier:
            raise EvidenceSpecialistInputError(f"{entity} ID is required")
        if identifier in seen:
            raise EvidenceSpecialistInputError(f"duplicate {entity} ID: {identifier}")
        seen.add(identifier)
