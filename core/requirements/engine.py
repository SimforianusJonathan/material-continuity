"""Deterministic comparison of structured evidence against requirements."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

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
    ScalarValue,
)
from .units import IncompatibleUnitError, convert_decimal, normalize_unit


def compare_requirements(
    *,
    candidate_id: str,
    requirements: Iterable[Requirement],
    evidence: Iterable[CandidateEvidence],
) -> CandidateComparisonResult:
    """Compare every application requirement for one candidate."""

    requirement_list = tuple(requirements)
    evidence_list = tuple(evidence)
    if not candidate_id:
        raise RequirementInputError("candidate_id is required")
    if not requirement_list:
        raise RequirementInputError("at least one requirement is required")
    _require_unique_ids(
        "requirement", (requirement.requirement_id for requirement in requirement_list)
    )
    _require_unique_ids("evidence", (item.evidence_id for item in evidence_list))

    rows = tuple(
        compare_requirement(
            candidate_id=candidate_id,
            requirement=requirement,
            evidence=evidence_list,
        )
        for requirement in requirement_list
    )
    if any(row.hard_reject for row in rows):
        decision = CandidateDecision.REJECTED_HARD_MISMATCH
    elif any(
        row.status in {ComparisonStatus.UNKNOWN, ComparisonStatus.BLOCKED}
        for row in rows
    ):
        decision = CandidateDecision.BLOCKED_PENDING_EVIDENCE_OR_RELEASE
    else:
        decision = CandidateDecision.REQUIREMENTS_MATCH

    return CandidateComparisonResult(
        candidate_id=candidate_id,
        decision=decision,
        rows=rows,
    )


def compare_requirement(
    *,
    candidate_id: str,
    requirement: Requirement,
    evidence: Iterable[CandidateEvidence],
) -> ComparisonResult:
    """Classify one requirement using current, applicable structured evidence."""

    _validate_requirement(requirement)
    matching = tuple(
        item
        for item in evidence
        if item.candidate_id == candidate_id and item.property == requirement.property
    )
    provenance = tuple(_provenance(item) for item in matching)

    if not matching:
        return _unknown(
            candidate_id,
            requirement,
            "No evidence was supplied for this candidate requirement.",
            provenance,
        )
    if any(not item.applicable for item in matching):
        return _unknown(
            candidate_id,
            requirement,
            "Evidence is not applicable to the required application.",
            provenance,
        )
    if any(item.source_revision != item.current_source_revision for item in matching):
        return _unknown(
            candidate_id,
            requirement,
            "Evidence does not belong to the current source revision.",
            provenance,
        )

    normalized_values: list[ScalarValue] = []
    try:
        for item in matching:
            normalized_values.append(_normalize_value(item.value, item.unit, requirement.unit))
        normalized_required = _normalize_value(
            requirement.required_value, requirement.unit, requirement.unit
        )
    except IncompatibleUnitError as error:
        return _unknown(candidate_id, requirement, str(error), provenance)
    except RequirementInputError as error:
        return _unknown(candidate_id, requirement, str(error), provenance)

    if len({_value_key(value) for value in normalized_values}) > 1:
        return _unknown(
            candidate_id,
            requirement,
            "Applicable current evidence contains conflicting values.",
            provenance,
        )

    observed = matching[0]
    normalized_observed = normalized_values[0]
    try:
        comparison_matches = _evaluate(
            normalized_observed, requirement.operator, normalized_required
        )
    except RequirementInputError as error:
        return _unknown(candidate_id, requirement, str(error), provenance)
    if requirement.kind == RequirementKind.RELEASE_GATE and not comparison_matches:
        status = ComparisonStatus.BLOCKED
        reason = "Required release or qualification gate is not satisfied."
    elif comparison_matches:
        status = ComparisonStatus.MATCH
        reason = "Current applicable evidence satisfies the requirement."
    else:
        status = ComparisonStatus.MISMATCH
        reason = "Current applicable evidence violates the requirement."

    return ComparisonResult(
        candidate_id=candidate_id,
        requirement_id=requirement.requirement_id,
        requirement_name=requirement.name,
        status=status,
        required_operator=requirement.operator,
        required_value=requirement.required_value,
        required_unit=requirement.unit,
        observed_value=observed.value,
        observed_unit=observed.unit,
        normalized_required_value=normalized_required,
        normalized_observed_value=normalized_observed,
        normalized_unit=normalize_unit(requirement.unit) if requirement.unit else None,
        reason=reason,
        hard_reject=(
            status == ComparisonStatus.MISMATCH
            and requirement.criticality == RequirementCriticality.HARD
        ),
        evidence=provenance,
    )


def _normalize_value(
    value: ScalarValue, observed_unit: str | None, required_unit: str | None
) -> ScalarValue:
    if isinstance(value, bool):
        if observed_unit is not None or required_unit is not None:
            raise RequirementInputError("boolean evidence cannot have a unit")
        return value
    if isinstance(value, Decimal):
        if observed_unit is None and required_unit is None:
            return value
        if observed_unit is None or required_unit is None:
            raise IncompatibleUnitError("numeric evidence and requirement must both declare units")
        return convert_decimal(value, observed_unit, required_unit)
    if observed_unit is not None or required_unit is not None:
        raise RequirementInputError("text evidence cannot have a unit")
    return " ".join(value.split()).casefold()


def _evaluate(
    observed: ScalarValue,
    operator: ComparisonOperator,
    required: ScalarValue,
) -> bool:
    if type(observed) is not type(required):
        raise RequirementInputError("observed and required value types do not match")
    if operator == ComparisonOperator.EQUAL:
        return observed == required
    if isinstance(observed, (str, bool)):
        raise RequirementInputError(
            f"operator {operator.value} is only valid for numeric evidence"
        )
    if operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
        return observed >= required
    if operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
        return observed <= required
    if operator == ComparisonOperator.GREATER_THAN:
        return observed > required
    if operator == ComparisonOperator.LESS_THAN:
        return observed < required
    raise RequirementInputError(f"unsupported operator: {operator}")


def _validate_requirement(requirement: Requirement) -> None:
    if not requirement.requirement_id or not requirement.property:
        raise RequirementInputError("requirement ID and property are required")
    if requirement.kind == RequirementKind.RELEASE_GATE and requirement.operator != ComparisonOperator.EQUAL:
        raise RequirementInputError("release gates must use equality comparison")


def _unknown(
    candidate_id: str,
    requirement: Requirement,
    reason: str,
    provenance: tuple[EvidenceProvenance, ...],
) -> ComparisonResult:
    return ComparisonResult(
        candidate_id=candidate_id,
        requirement_id=requirement.requirement_id,
        requirement_name=requirement.name,
        status=ComparisonStatus.UNKNOWN,
        required_operator=requirement.operator,
        required_value=requirement.required_value,
        required_unit=requirement.unit,
        observed_value=None,
        observed_unit=None,
        normalized_required_value=None,
        normalized_observed_value=None,
        normalized_unit=normalize_unit(requirement.unit) if requirement.unit else None,
        reason=reason,
        hard_reject=False,
        evidence=provenance,
    )


def _provenance(item: CandidateEvidence) -> EvidenceProvenance:
    return EvidenceProvenance(
        evidence_id=item.evidence_id,
        source_document=item.source_document,
        source_revision=item.source_revision,
        current_source_revision=item.current_source_revision,
        source_page=item.source_page,
        source_location=item.source_location,
        applicability=item.applicability,
    )


def _value_key(value: ScalarValue) -> tuple[str, str]:
    return type(value).__name__, str(value)


def _require_unique_ids(entity: str, identifiers: Iterable[str]) -> None:
    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            raise RequirementInputError(f"duplicate {entity} ID: {identifier}")
        seen.add(identifier)
