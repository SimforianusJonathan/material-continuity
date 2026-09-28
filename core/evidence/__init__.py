"""Structured evidence extraction and deterministic comparison bridge."""

from .engine import compare_extracted_evidence, prepare_evidence
from .models import (
    EvidenceExclusionReason,
    EvidenceExtraction,
    EvidencePipelineInputError,
    EvidencePipelineResult,
    ExcludedExtraction,
    ExtractionSupportStatus,
    PreparedEvidence,
)

__all__ = [
    "EvidenceExclusionReason",
    "EvidenceExtraction",
    "EvidencePipelineInputError",
    "EvidencePipelineResult",
    "ExcludedExtraction",
    "ExtractionSupportStatus",
    "PreparedEvidence",
    "compare_extracted_evidence",
    "prepare_evidence",
]
