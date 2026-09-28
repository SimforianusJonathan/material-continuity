"""Create and update immutable, hash-bound recovery-case versions."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Iterable

from core.exposure.models import ExposureResult
from core.qualification.models import QualificationGraphResult
from core.recovery_options.models import RecoverySearchResult
from core.requirements.models import CandidateComparisonResult
from core.simulation.models import RecoverySimulationResult

from .models import (
    ActionReceipt,
    ApprovalRecord,
    CaseStatus,
    CaseTrigger,
    CaseUpdateResult,
    RecoveryCase,
    RecoveryCaseInputError,
    RecoveryCaseUpdate,
    RecoveryCaseVersion,
    SourceVersion,
)
from .serialization import canonical_hash


def create_case(
    *,
    case_id: str,
    status: CaseStatus,
    trigger: CaseTrigger,
    exposure: ExposureResult,
    recovery_options: RecoverySearchResult,
    candidate_comparisons: Iterable[CandidateComparisonResult],
    qualification_graphs: Iterable[QualificationGraphResult],
    simulation: RecoverySimulationResult,
    source_versions: Iterable[SourceVersion],
    created_at: datetime,
) -> RecoveryCase:
    """Create version 1 of a recovery case."""

    comparisons = tuple(sorted(candidate_comparisons, key=lambda item: item.candidate_id))
    graphs = tuple(sorted(qualification_graphs, key=lambda item: item.candidate_id))
    sources = tuple(sorted(source_versions, key=lambda item: item.source_id))
    _validate_common(
        case_id=case_id,
        trigger=trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        simulation=simulation,
        source_versions=sources,
        timestamp=created_at,
    )
    _require_unique_ids("candidate comparison", (item.candidate_id for item in comparisons))
    _require_unique_ids("qualification graph", (item.candidate_id for item in graphs))

    snapshot = _build_version(
        case_id=case_id,
        case_version=1,
        previous_case_hash=None,
        status=status,
        trigger=trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        candidate_comparisons=comparisons,
        qualification_graphs=graphs,
        simulation=simulation,
        source_versions=sources,
        change_reason="Case created.",
        created_at=created_at,
    )
    return RecoveryCase(
        case_id=case_id,
        versions=(snapshot,),
        approvals=(),
        actions=(),
        created_at=created_at,
        updated_at=created_at,
    )


def update_case(
    case: RecoveryCase,
    *,
    update: RecoveryCaseUpdate,
    change_reason: str,
    updated_at: datetime,
) -> CaseUpdateResult:
    """Append a version only when decision-relevant content changes."""

    _validate_timestamp(updated_at, "updated_at")
    if updated_at < case.updated_at:
        raise RecoveryCaseInputError("updated_at cannot move backwards")
    if not change_reason.strip():
        raise RecoveryCaseInputError("change_reason is required")

    current = case.current
    status = update.status if update.status is not None else current.status
    exposure = update.exposure if update.exposure is not None else current.exposure
    recovery_options = (
        update.recovery_options
        if update.recovery_options is not None
        else current.recovery_options
    )
    comparisons = (
        tuple(sorted(update.candidate_comparisons, key=lambda item: item.candidate_id))
        if update.candidate_comparisons is not None
        else current.candidate_comparisons
    )
    graphs = (
        tuple(sorted(update.qualification_graphs, key=lambda item: item.candidate_id))
        if update.qualification_graphs is not None
        else current.qualification_graphs
    )
    simulation = update.simulation if update.simulation is not None else current.simulation
    sources = (
        tuple(sorted(update.source_versions, key=lambda item: item.source_id))
        if update.source_versions is not None
        else current.source_versions
    )

    _validate_common(
        case_id=case.case_id,
        trigger=current.trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        simulation=simulation,
        source_versions=sources,
        timestamp=updated_at,
    )
    _require_unique_ids("candidate comparison", (item.candidate_id for item in comparisons))
    _require_unique_ids("qualification graph", (item.candidate_id for item in graphs))

    current_content = _decision_content(
        status=current.status,
        trigger=current.trigger,
        exposure=current.exposure,
        recovery_options=current.recovery_options,
        candidate_comparisons=current.candidate_comparisons,
        qualification_graphs=current.qualification_graphs,
        simulation=current.simulation,
        source_versions=current.source_versions,
    )
    proposed_content = _decision_content(
        status=status,
        trigger=current.trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        candidate_comparisons=comparisons,
        qualification_graphs=graphs,
        simulation=simulation,
        source_versions=sources,
    )
    changed_sources = _changed_source_ids(current.source_versions, sources)
    if canonical_hash(current_content) == canonical_hash(proposed_content):
        return CaseUpdateResult(
            case=case,
            version_changed=False,
            changed_source_ids=(),
        )

    snapshot = _build_version(
        case_id=case.case_id,
        case_version=current.case_version + 1,
        previous_case_hash=current.case_hash,
        status=status,
        trigger=current.trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        candidate_comparisons=comparisons,
        qualification_graphs=graphs,
        simulation=simulation,
        source_versions=sources,
        change_reason=change_reason.strip(),
        created_at=updated_at,
    )
    updated_case = replace(
        case,
        versions=case.versions + (snapshot,),
        updated_at=updated_at,
    )
    return CaseUpdateResult(
        case=updated_case,
        version_changed=True,
        changed_source_ids=changed_sources,
    )


def append_approval(
    case: RecoveryCase, approval: ApprovalRecord, *, updated_at: datetime
) -> RecoveryCase:
    """Store an approval without changing the decision version it targets."""

    _validate_timestamp(updated_at, "updated_at")
    _validate_timestamp(approval.approved_at, "approved_at")
    _validate_timestamp(approval.expires_at, "expires_at")
    if updated_at < case.updated_at:
        raise RecoveryCaseInputError("updated_at cannot move backwards")
    if approval.expires_at <= approval.approved_at:
        raise RecoveryCaseInputError("approval expiry must be after approval time")
    if any(item.approval_id == approval.approval_id for item in case.approvals):
        raise RecoveryCaseInputError(f"duplicate approval ID: {approval.approval_id}")
    target_version = _validate_version_reference(
        case,
        case_id=approval.case_id,
        case_version=approval.case_version,
        case_hash=approval.case_hash,
        entity="approval",
    )
    if approval.approved_at < target_version.created_at:
        raise RecoveryCaseInputError("approval cannot predate its case version")
    if updated_at < approval.approved_at:
        raise RecoveryCaseInputError("updated_at cannot predate approval time")
    return replace(
        case,
        approvals=case.approvals + (approval,),
        updated_at=updated_at,
    )


def append_action_receipt(
    case: RecoveryCase, action: ActionReceipt, *, updated_at: datetime
) -> RecoveryCase:
    """Store an action receipt without changing its referenced decision version."""

    _validate_timestamp(updated_at, "updated_at")
    _validate_timestamp(action.executed_at, "executed_at")
    if updated_at < case.updated_at:
        raise RecoveryCaseInputError("updated_at cannot move backwards")
    if any(item.action_id == action.action_id for item in case.actions):
        raise RecoveryCaseInputError(f"duplicate action ID: {action.action_id}")
    if any(item.idempotency_key == action.idempotency_key for item in case.actions):
        raise RecoveryCaseInputError(
            f"duplicate action idempotency key: {action.idempotency_key}"
        )
    target_version = _validate_version_reference(
        case,
        case_id=action.case_id,
        case_version=action.case_version,
        case_hash=action.case_hash,
        entity="action",
    )
    if action.executed_at < target_version.created_at:
        raise RecoveryCaseInputError("action cannot predate its case version")
    if updated_at < action.executed_at:
        raise RecoveryCaseInputError("updated_at cannot predate action execution")
    return replace(
        case,
        actions=case.actions + (action,),
        updated_at=updated_at,
    )


def _build_version(
    *,
    case_id: str,
    case_version: int,
    previous_case_hash: str | None,
    status: CaseStatus,
    trigger: CaseTrigger,
    exposure: ExposureResult,
    recovery_options: RecoverySearchResult,
    candidate_comparisons: tuple[CandidateComparisonResult, ...],
    qualification_graphs: tuple[QualificationGraphResult, ...],
    simulation: RecoverySimulationResult,
    source_versions: tuple[SourceVersion, ...],
    change_reason: str,
    created_at: datetime,
) -> RecoveryCaseVersion:
    content = _decision_content(
        status=status,
        trigger=trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        candidate_comparisons=candidate_comparisons,
        qualification_graphs=qualification_graphs,
        simulation=simulation,
        source_versions=source_versions,
    )
    case_hash = canonical_hash(
        {
            "case_id": case_id,
            "case_version": case_version,
            "previous_case_hash": previous_case_hash,
            "decision": content,
        }
    )
    return RecoveryCaseVersion(
        case_id=case_id,
        case_version=case_version,
        case_hash=case_hash,
        previous_case_hash=previous_case_hash,
        status=status,
        trigger=trigger,
        exposure=exposure,
        recovery_options=recovery_options,
        candidate_comparisons=candidate_comparisons,
        qualification_graphs=qualification_graphs,
        simulation=simulation,
        source_versions=source_versions,
        change_reason=change_reason,
        created_at=created_at,
    )


def _decision_content(
    *,
    status: CaseStatus,
    trigger: CaseTrigger,
    exposure: ExposureResult,
    recovery_options: RecoverySearchResult,
    candidate_comparisons: tuple[CandidateComparisonResult, ...],
    qualification_graphs: tuple[QualificationGraphResult, ...],
    simulation: RecoverySimulationResult,
    source_versions: tuple[SourceVersion, ...],
) -> dict[str, Any]:
    return {
        "status": status,
        "trigger": trigger,
        "exposure": exposure,
        "recovery_options": recovery_options,
        "candidate_comparisons": candidate_comparisons,
        "qualification_graphs": qualification_graphs,
        "simulation": simulation,
        "source_versions": source_versions,
    }


def _validate_common(
    *,
    case_id: str,
    trigger: CaseTrigger,
    exposure: ExposureResult,
    recovery_options: RecoverySearchResult,
    simulation: RecoverySimulationResult,
    source_versions: tuple[SourceVersion, ...],
    timestamp: datetime,
) -> None:
    if not case_id:
        raise RecoveryCaseInputError("case_id is required")
    _validate_timestamp(timestamp, "case timestamp")
    _validate_timestamp(trigger.detected_at, "trigger detected_at")
    if trigger.material_id != exposure.material_id:
        raise RecoveryCaseInputError("trigger and exposure material IDs do not match")
    if recovery_options.material_id != exposure.material_id:
        raise RecoveryCaseInputError(
            "recovery options and exposure material IDs do not match"
        )
    if simulation.material_id != exposure.material_id:
        raise RecoveryCaseInputError("simulation and exposure material IDs do not match")
    _require_unique_ids("source", (item.source_id for item in source_versions))
    for source in source_versions:
        _validate_timestamp(source.observed_at, f"source {source.source_id} observed_at")


def _validate_version_reference(
    case: RecoveryCase,
    *,
    case_id: str,
    case_version: int,
    case_hash: str,
    entity: str,
) -> RecoveryCaseVersion:
    if case_id != case.case_id:
        raise RecoveryCaseInputError(f"{entity} references a different case")
    version = next(
        (item for item in case.versions if item.case_version == case_version), None
    )
    if version is None:
        raise RecoveryCaseInputError(f"{entity} references an unknown case version")
    if version.case_hash != case_hash:
        raise RecoveryCaseInputError(f"{entity} case hash does not match its version")
    return version


def _changed_source_ids(
    previous: tuple[SourceVersion, ...], current: tuple[SourceVersion, ...]
) -> tuple[str, ...]:
    previous_map = {item.source_id: item for item in previous}
    current_map = {item.source_id: item for item in current}
    return tuple(
        sorted(
            source_id
            for source_id in set(previous_map) | set(current_map)
            if previous_map.get(source_id) != current_map.get(source_id)
        )
    )


def _validate_timestamp(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RecoveryCaseInputError(f"{name} must be timezone-aware")


def _require_unique_ids(entity: str, identifiers: Iterable[str]) -> None:
    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            raise RecoveryCaseInputError(f"duplicate {entity} ID: {identifier}")
        seen.add(identifier)
