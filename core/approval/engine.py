"""Fail-closed deterministic approval gate for controlled actions."""

from __future__ import annotations

from collections.abc import Iterable

from core.case_state.models import ApprovalRecord, RecoveryCase, SourceVersion

from .models import (
    ApprovalBlockReason,
    ApprovalGateDecision,
    ApprovalGateInputError,
    ApprovalGateStatus,
    ApprovalValidationRequest,
    ApproverRole,
    ControlledAction,
)


ALLOWED_ACTIONS_BY_ROLE: dict[ApproverRole, frozenset[ControlledAction]] = {
    ApproverRole.ENGINEERING_REVIEWER: frozenset(
        {ControlledAction.CREATE_QUALIFICATION_TASK}
    ),
    ApproverRole.QUALITY_ENGINEER: frozenset(
        {ControlledAction.CREATE_QUALIFICATION_TASK}
    ),
    ApproverRole.PRODUCTION_PLANNER: frozenset(
        {ControlledAction.AUTHORIZE_RESEQUENCING}
    ),
}


def validate_approval(
    case: RecoveryCase,
    request: ApprovalValidationRequest,
) -> ApprovalGateDecision:
    """Validate an approval against identity, scope, case, sources, and replay state."""

    _validate_request(request)
    approval = next(
        (item for item in case.approvals if item.approval_id == request.approval_id),
        None,
    )
    if approval is None:
        return _decision(
            case,
            request,
            reasons=(ApprovalBlockReason.APPROVAL_NOT_FOUND,),
            changed_source_ids=(),
        )

    reasons: list[ApprovalBlockReason] = []
    current = case.current
    if approval.case_id != case.case_id:
        reasons.append(ApprovalBlockReason.CASE_REFERENCE_MISMATCH)
    if approval.case_version != current.case_version:
        reasons.append(ApprovalBlockReason.STALE_CASE_VERSION)
    if approval.case_hash != current.case_hash:
        reasons.append(ApprovalBlockReason.CASE_HASH_MISMATCH)
    if approval.approver_id != request.principal.principal_id:
        reasons.append(ApprovalBlockReason.PRINCIPAL_ID_MISMATCH)
    if approval.approver_role != request.principal.role.value:
        reasons.append(ApprovalBlockReason.PRINCIPAL_ROLE_MISMATCH)
    if request.action not in ALLOWED_ACTIONS_BY_ROLE[request.principal.role]:
        reasons.append(ApprovalBlockReason.ROLE_NOT_PERMITTED)
    if approval.permitted_action != request.action.value:
        reasons.append(ApprovalBlockReason.ACTION_SCOPE_MISMATCH)
    if request.evaluated_at < approval.approved_at:
        reasons.append(ApprovalBlockReason.APPROVAL_NOT_ACTIVE)
    if request.evaluated_at >= approval.expires_at:
        reasons.append(ApprovalBlockReason.APPROVAL_EXPIRED)

    changed_sources = _changed_source_ids(
        current.source_versions, request.current_source_versions
    )
    if changed_sources:
        reasons.append(ApprovalBlockReason.SOURCE_STATE_CHANGED)
    if any(
        action.idempotency_key == request.idempotency_key for action in case.actions
    ):
        reasons.append(ApprovalBlockReason.DUPLICATE_ACTION)

    return _decision(
        case,
        request,
        reasons=tuple(dict.fromkeys(reasons)),
        changed_source_ids=changed_sources,
    )


def _decision(
    case: RecoveryCase,
    request: ApprovalValidationRequest,
    *,
    reasons: tuple[ApprovalBlockReason, ...],
    changed_source_ids: tuple[str, ...],
) -> ApprovalGateDecision:
    return ApprovalGateDecision(
        status=(
            ApprovalGateStatus.BLOCKED
            if reasons
            else ApprovalGateStatus.AUTHORIZED
        ),
        approval_id=request.approval_id,
        action=request.action,
        case_id=case.case_id,
        case_version=case.current.case_version,
        case_hash=case.current.case_hash,
        evaluated_at=request.evaluated_at,
        reasons=reasons,
        changed_source_ids=changed_source_ids,
    )


def _changed_source_ids(
    case_sources: Iterable[SourceVersion], current_sources: Iterable[SourceVersion]
) -> tuple[str, ...]:
    expected = _source_state(case_sources)
    observed = _source_state(current_sources)
    return tuple(
        sorted(
            source_id
            for source_id in set(expected) | set(observed)
            if expected.get(source_id) != observed.get(source_id)
        )
    )


def _source_state(
    sources: Iterable[SourceVersion],
) -> dict[str, tuple[str, str, str | None]]:
    state: dict[str, tuple[str, str, str | None]] = {}
    for source in sources:
        if not source.source_id:
            raise ApprovalGateInputError("source_id is required")
        if source.source_id in state:
            raise ApprovalGateInputError(f"duplicate source ID: {source.source_id}")
        state[source.source_id] = (
            source.source_type.value,
            source.version,
            source.content_hash,
        )
    return state


def _validate_request(request: ApprovalValidationRequest) -> None:
    if not request.approval_id.strip():
        raise ApprovalGateInputError("approval_id is required")
    if not request.principal.principal_id.strip():
        raise ApprovalGateInputError("principal_id is required")
    if not request.idempotency_key.strip():
        raise ApprovalGateInputError("idempotency_key is required")
    if request.evaluated_at.tzinfo is None or request.evaluated_at.utcoffset() is None:
        raise ApprovalGateInputError("evaluated_at must be timezone-aware")
    _source_state(request.current_source_versions)
