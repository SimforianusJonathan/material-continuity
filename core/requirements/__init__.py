"""Deterministic requirement comparison and evidence classification."""

from .engine import compare_requirement, compare_requirements
from .models import (
    CandidateComparisonResult,
    CandidateDecision,
    CandidateEvidence,
    ComparisonOperator,
    ComparisonResult,
    ComparisonStatus,
    EvidenceProvenance,
    Requirement,
    RequirementCriticality,
    RequirementInputError,
    RequirementKind,
)

__all__ = [
    "CandidateComparisonResult",
    "CandidateDecision",
    "CandidateEvidence",
    "ComparisonOperator",
    "ComparisonResult",
    "ComparisonStatus",
    "EvidenceProvenance",
    "Requirement",
    "RequirementCriticality",
    "RequirementInputError",
    "RequirementKind",
    "compare_requirement",
    "compare_requirements",
]
