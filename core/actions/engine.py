"""Approval-gated mock QMS action adapter."""

from __future__ import annotations

from hashlib import sha256

from core.approval import ApprovalGateDecision, ControlledAction, validate_approval
from core.case_state import ActionReceipt, RecoveryCase, append_action_receipt
from core.requirements import CandidateDecision

from .models import (
    ActionAdapterInputError,
    ActionBlockReason,
    ActionExecutionStatus,
    CreateQualificationTaskCommand,
    QualificationTaskCreationResult,
    QualificationTaskRecord,
)


def create_qualification_task(
    case: RecoveryCase,
    command: CreateQualificationTaskCommand,
) -> QualificationTaskCreationResult:
    """Create one mock QMS task only after all deterministic controls authorize it."""

    _validate_command(command)
    decision = validate_approval(case, command.approval)
    if not decision.authorized:
        return _blocked(
            case,
            decision,
            reasons=(ActionBlockReason.APPROVAL_BLOCKED,),
        )

    comparison = next(
        (
            item
            for item in case.current.candidate_comparisons
            if item.candidate_id == command.candidate_id
        ),
        None,
    )
    if comparison is None:
        return _blocked(
            case,
            decision,
            reasons=(ActionBlockReason.CANDIDATE_NOT_FOUND,),
        )
    if comparison.decision is CandidateDecision.REJECTED_HARD_MISMATCH:
        return _blocked(
            case,
            decision,
            reasons=(ActionBlockReason.CANDIDATE_HARD_REJECTED,),
        )

    graph = next(
        (
            item
            for item in case.current.qualification_graphs
            if item.candidate_id == command.candidate_id
        ),
        None,
    )
    if graph is None:
        return _blocked(
            case,
            decision,
            reasons=(ActionBlockReason.QUALIFICATION_PLAN_NOT_FOUND,),
        )
    if not any(
        schedule.requirement_id == command.requirement_id
        for schedule in graph.schedules
    ):
        return _blocked(
            case,
            decision,
            reasons=(ActionBlockReason.REQUIREMENT_NOT_IN_PLAN,),
        )

    qms_task_id, action_id = _deterministic_ids(
        case_id=case.case_id,
        case_version=case.current.case_version,
        candidate_id=command.candidate_id,
        requirement_id=command.requirement_id,
        idempotency_key=command.approval.idempotency_key,
    )
    receipt = ActionReceipt(
        action_id=action_id,
        case_id=case.case_id,
        case_version=case.current.case_version,
        case_hash=case.current.case_hash,
        action_type=ControlledAction.CREATE_QUALIFICATION_TASK.value,
        external_reference=qms_task_id,
        idempotency_key=command.approval.idempotency_key,
        status=ActionExecutionStatus.CREATED.value,
        executed_at=command.approval.evaluated_at,
    )
    task = QualificationTaskRecord(
        qms_task_id=qms_task_id,
        candidate_id=command.candidate_id,
        requirement_id=command.requirement_id,
        task_name=command.task_name.strip(),
        status=ActionExecutionStatus.CREATED,
        created_at=command.approval.evaluated_at,
        production_release_authorized=False,
    )
    updated_case = append_action_receipt(
        case,
        receipt,
        updated_at=command.approval.evaluated_at,
    )
    return QualificationTaskCreationResult(
        status=ActionExecutionStatus.CREATED,
        case=updated_case,
        approval_decision=decision,
        qms_task_id=qms_task_id,
        task=task,
        action_receipt=receipt,
        block_reasons=(),
        production_release_authorized=False,
    )


def _blocked(
    case: RecoveryCase,
    decision: ApprovalGateDecision,
    *,
    reasons: tuple[ActionBlockReason, ...],
) -> QualificationTaskCreationResult:
    return QualificationTaskCreationResult(
        status=ActionExecutionStatus.BLOCKED,
        case=case,
        approval_decision=decision,
        qms_task_id=None,
        task=None,
        action_receipt=None,
        block_reasons=reasons,
        production_release_authorized=False,
    )


def _deterministic_ids(
    *,
    case_id: str,
    case_version: int,
    candidate_id: str,
    requirement_id: str,
    idempotency_key: str,
) -> tuple[str, str]:
    payload = ":".join(
        (
            case_id,
            str(case_version),
            candidate_id,
            requirement_id,
            idempotency_key,
        )
    ).encode("utf-8")
    token = sha256(payload).hexdigest().upper()
    return f"QMS-QUAL-{token[:10]}", f"ACT-{token[10:22]}"


def _validate_command(command: CreateQualificationTaskCommand) -> None:
    if command.approval.action is not ControlledAction.CREATE_QUALIFICATION_TASK:
        raise ActionAdapterInputError(
            "approval request action must be CREATE_QUALIFICATION_TASK"
        )
    if not command.candidate_id.strip():
        raise ActionAdapterInputError("candidate_id is required")
    if not command.requirement_id.strip():
        raise ActionAdapterInputError("requirement_id is required")
    if not command.task_name.strip():
        raise ActionAdapterInputError("task_name is required")
