"""Evidence Specialist workflow with a replaceable retrieval adapter."""

from .engine import investigate_candidate
from .models import (
    EvidenceGap,
    EvidenceInvestigationRequest,
    EvidenceSpecialistInputError,
    EvidenceSpecialistResult,
    QualificationProcedureReference,
    RetrievalTool,
    RetrievalTrace,
)
from .prompts import SYSTEM_PROMPT
from .retrieval import EvidenceRetriever, MockEvidenceRetriever

__all__ = [
    "EvidenceGap",
    "EvidenceInvestigationRequest",
    "EvidenceRetriever",
    "EvidenceSpecialistInputError",
    "EvidenceSpecialistResult",
    "MockEvidenceRetriever",
    "QualificationProcedureReference",
    "RetrievalTool",
    "RetrievalTrace",
    "SYSTEM_PROMPT",
    "investigate_candidate",
]
