"""Evidence Specialist workflow over a replaceable retrieval boundary."""

from __future__ import annotations

from core.evidence import compare_extracted_evidence
from core.requirements import CandidateDecision, ComparisonStatus

from .models import (
    EvidenceGap,
    EvidenceInvestigationRequest,
    EvidenceSpecialistInputError,
    EvidenceSpecialistResult,
    RetrievalTool,
    RetrievalTrace,
)
from .retrieval import EvidenceRetriever


def investigate_candidate(
    request: EvidenceInvestigationRequest,
    *,
    retriever: EvidenceRetriever,
) -> EvidenceSpecialistResult:
    """Retrieve, map, compare, and report gaps for one candidate."""

    _validate_request(request)
    properties = tuple(requirement.property for requirement in request.requirements)
    extractions = retriever.retrieve_candidate_evidence(
        candidate_id=request.candidate_id,
        properties=properties,
    )
    trace: list[RetrievalTrace] = [
        RetrievalTrace(
            tool=RetrievalTool.CANDIDATE_EVIDENCE,
            query=(
                f"candidate={request.candidate_id};"
                f"properties={','.join(sorted(set(properties)))}"
            ),
            returned_count=len(extractions),
        )
    ]
    pipeline = compare_extracted_evidence(
        candidate_id=request.candidate_id,
        requirements=request.requirements,
        extractions=extractions,
    )
    comparison = pipeline.comparison
    hard_mismatches = tuple(
        row.requirement_id for row in comparison.rows if row.hard_reject
    )
    unresolved_rows = tuple(
        row
        for row in comparison.rows
        if row.status in {ComparisonStatus.UNKNOWN, ComparisonStatus.BLOCKED}
    )

    if comparison.decision is CandidateDecision.REJECTED_HARD_MISMATCH:
        procedures = ()
    else:
        requirement_ids = tuple(row.requirement_id for row in unresolved_rows)
        procedures = retriever.retrieve_qualification_procedures(
            requirement_ids=requirement_ids
        )
        trace.append(
            RetrievalTrace(
                tool=RetrievalTool.QUALIFICATION_PROCEDURE,
                query=f"requirements={','.join(sorted(requirement_ids))}",
                returned_count=len(procedures),
            )
        )

    procedure_map: dict[str, list[str]] = {}
    for procedure in procedures:
        procedure_map.setdefault(procedure.requirement_id, []).append(
            procedure.procedure_id
        )
    gaps = tuple(
        EvidenceGap(
            requirement_id=row.requirement_id,
            requirement_name=row.requirement_name,
            status=row.status,
            reason=row.reason,
            qualification_procedure_ids=tuple(
                sorted(procedure_map.get(row.requirement_id, ()))
            ),
        )
        for row in unresolved_rows
    )
    return EvidenceSpecialistResult(
        candidate_id=request.candidate_id,
        pipeline=pipeline,
        comparison=comparison,
        retrieved_extractions=extractions,
        gaps=gaps,
        hard_mismatch_requirement_ids=hard_mismatches,
        qualification_procedures=procedures,
        retrieval_trace=tuple(trace),
    )


def _validate_request(request: EvidenceInvestigationRequest) -> None:
    if not request.candidate_id.strip():
        raise EvidenceSpecialistInputError("candidate_id is required")
    if not request.requirements:
        raise EvidenceSpecialistInputError("at least one requirement is required")
    seen: set[str] = set()
    for requirement in request.requirements:
        if requirement.requirement_id in seen:
            raise EvidenceSpecialistInputError(
                f"duplicate requirement ID: {requirement.requirement_id}"
            )
        seen.add(requirement.requirement_id)
