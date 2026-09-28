"""Validate structured extraction and bridge it to deterministic comparison."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from core.requirements import (
    CandidateEvidence,
    Requirement,
    compare_requirements,
)

from .models import (
    EvidenceExclusionReason,
    EvidenceExtraction,
    EvidencePipelineInputError,
    EvidencePipelineResult,
    ExcludedExtraction,
    ExtractionSupportStatus,
    PreparedEvidence,
)


def prepare_evidence(
    extractions: Iterable[EvidenceExtraction],
) -> PreparedEvidence:
    """Accept only supported claims with complete source provenance."""

    rows = tuple(extractions)
    _require_unique_ids(item.extraction_id for item in rows)
    evidence: list[CandidateEvidence] = []
    exclusions: list[ExcludedExtraction] = []

    for extraction in rows:
        _validate_extraction(extraction)
        if not _has_complete_provenance(extraction):
            exclusions.append(
                ExcludedExtraction(
                    extraction=extraction,
                    reason=EvidenceExclusionReason.MISSING_PROVENANCE,
                )
            )
            continue
        if extraction.support_status is ExtractionSupportStatus.UNSUPPORTED:
            exclusions.append(
                ExcludedExtraction(
                    extraction=extraction,
                    reason=EvidenceExclusionReason.UNSUPPORTED_CLAIM,
                )
            )
            continue
        if extraction.value is None:
            exclusions.append(
                ExcludedExtraction(
                    extraction=extraction,
                    reason=EvidenceExclusionReason.MISSING_VALUE,
                )
            )
            continue

        evidence.append(
            CandidateEvidence(
                evidence_id=extraction.extraction_id,
                candidate_id=extraction.candidate_id,
                property=extraction.property,
                value=extraction.value,
                unit=extraction.unit,
                source_document=extraction.source_document,
                source_revision=extraction.source_revision,
                current_source_revision=extraction.current_source_revision,
                source_page=extraction.source_page,
                source_location=extraction.source_location,
                applicability=extraction.applicability,
                applicable=extraction.applicable,
            )
        )

    return PreparedEvidence(evidence=tuple(evidence), exclusions=tuple(exclusions))


def compare_extracted_evidence(
    *,
    candidate_id: str,
    requirements: Iterable[Requirement],
    extractions: Iterable[EvidenceExtraction],
) -> EvidencePipelineResult:
    """Prepare extraction output and invoke the existing deterministic engine."""

    candidate_extractions = tuple(
        extraction
        for extraction in extractions
        if extraction.candidate_id == candidate_id
    )
    prepared = prepare_evidence(candidate_extractions)
    comparison = compare_requirements(
        candidate_id=candidate_id,
        requirements=requirements,
        evidence=prepared.evidence,
    )
    return EvidencePipelineResult(prepared=prepared, comparison=comparison)


def _validate_extraction(extraction: EvidenceExtraction) -> None:
    if not extraction.extraction_id.strip():
        raise EvidencePipelineInputError("extraction_id is required")
    if not extraction.candidate_id.strip():
        raise EvidencePipelineInputError("candidate_id is required")
    if not extraction.property.strip():
        raise EvidencePipelineInputError("property is required")
    confidence = extraction.extraction_confidence
    if confidence is not None and not Decimal("0") <= confidence <= Decimal("1"):
        raise EvidencePipelineInputError(
            "extraction_confidence must be between 0 and 1"
        )


def _has_complete_provenance(extraction: EvidenceExtraction) -> bool:
    return all(
        value.strip()
        for value in (
            extraction.source_document,
            extraction.source_revision,
            extraction.current_source_revision,
            extraction.source_page,
            extraction.source_location,
            extraction.applicability,
        )
    )


def _require_unique_ids(identifiers: Iterable[str]) -> None:
    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            raise EvidencePipelineInputError(f"duplicate extraction ID: {identifier}")
        seen.add(identifier)
