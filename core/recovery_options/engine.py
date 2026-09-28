"""Ordered, deterministic discovery of material-recovery options."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from .models import (
    ApprovalStatus,
    OptionFinding,
    RecoveryCategory,
    RecoveryOptionInputError,
    RecoveryOptionRecord,
    RecoverySearchRequest,
    RecoverySearchResult,
    SearchStep,
)

APPROVED_SEARCH_ORDER = (
    RecoveryCategory.NETWORK_STOCK,
    RecoveryCategory.APPROVED_SOURCE,
    RecoveryCategory.APPROVED_EQUIVALENT,
    RecoveryCategory.ALTERNATE_BOM,
    RecoveryCategory.VALID_DEVIATION,
)

FALLBACK_SEARCH_ORDER = (
    RecoveryCategory.ORIGINAL_EXPEDITE,
    RecoveryCategory.PRODUCTION_RESEQUENCING,
)


def find_recovery_options(
    *, request: RecoverySearchRequest, options: Iterable[RecoveryOptionRecord]
) -> RecoverySearchResult:
    """Search recovery paths in the mandated order.

    Timely, valid, approved paths consume the required quantity in category
    order. Once they fully cover demand, discovery stops and unqualified
    candidates are not surfaced. If approved coverage is insufficient, the
    function returns unqualified candidates and fallbacks without treating
    either as authorized or production-ready.
    """

    option_list = tuple(options)
    _validate_inputs(request, option_list)
    material_options = tuple(
        option for option in option_list if option.material_id == request.material_id
    )

    remaining = request.required_quantity
    approved_findings: list[OptionFinding] = []
    candidate_findings: list[OptionFinding] = []
    fallback_findings: list[OptionFinding] = []
    trace: list[SearchStep] = []

    for category in APPROVED_SEARCH_ORDER:
        evaluated = tuple(
            option for option in material_options if option.category == category
        )
        qualifying = sorted(
            (
                option
                for option in evaluated
                if option.approval_status == ApprovalStatus.APPROVED
                and option.available_quantity > 0
                and option.ready_date is not None
                and option.ready_date <= request.need_by
                and option.is_valid_on(request.need_by)
            ),
            key=_option_sort_key,
        )

        category_coverage = 0
        for option in qualifying:
            coverage = min(option.available_quantity, remaining)
            if coverage == 0:
                break
            remaining -= coverage
            category_coverage += coverage
            approved_findings.append(_to_finding(option, coverage, request.need_by))

        if remaining == 0:
            outcome = "SUFFICIENT"
        elif category_coverage:
            outcome = "PARTIAL"
        else:
            outcome = "NONE"
        trace.append(_search_step(category, evaluated, qualifying, outcome))

        if remaining == 0:
            return _result(
                request=request,
                remaining=remaining,
                approved=approved_findings,
                candidates=candidate_findings,
                fallbacks=fallback_findings,
                trace=trace,
            )

    candidate_options = tuple(
        option
        for option in material_options
        if option.category == RecoveryCategory.UNQUALIFIED_CANDIDATE
    )
    qualifying_candidates = sorted(
        (
            option
            for option in candidate_options
            if option.approval_status == ApprovalStatus.UNQUALIFIED
            and option.available_quantity > 0
            and option.ready_date is not None
            and option.is_valid_on(request.need_by)
        ),
        key=lambda option: (
            option.ready_date > request.need_by,
            option.ready_date,
            option.option_id,
        ),
    )
    candidate_findings.extend(
        _to_finding(option, 0, request.need_by) for option in qualifying_candidates
    )
    trace.append(
        _search_step(
            RecoveryCategory.UNQUALIFIED_CANDIDATE,
            candidate_options,
            qualifying_candidates,
            "FOUND" if qualifying_candidates else "NONE",
        )
    )

    for category in FALLBACK_SEARCH_ORDER:
        evaluated = tuple(
            option for option in material_options if option.category == category
        )
        qualifying = sorted(
            (
                option
                for option in evaluated
                if option.approval_status == ApprovalStatus.AVAILABLE
                and option.available_quantity > 0
                and option.is_valid_on(request.need_by)
            ),
            key=_option_sort_key,
        )
        fallback_findings.extend(
            _to_finding(option, 0, request.need_by) for option in qualifying
        )
        trace.append(
            _search_step(
                category,
                evaluated,
                qualifying,
                "FOUND" if qualifying else "NONE",
            )
        )

    return _result(
        request=request,
        remaining=remaining,
        approved=approved_findings,
        candidates=candidate_findings,
        fallbacks=fallback_findings,
        trace=trace,
    )


def _validate_inputs(
    request: RecoverySearchRequest, options: tuple[RecoveryOptionRecord, ...]
) -> None:
    if not request.material_id:
        raise RecoveryOptionInputError("material_id is required")
    if request.required_quantity <= 0:
        raise RecoveryOptionInputError("required_quantity must be positive")
    if request.as_of > request.need_by:
        raise RecoveryOptionInputError("as_of cannot be after need_by")

    duplicates = [
        option_id
        for option_id, count in Counter(option.option_id for option in options).items()
        if count > 1
    ]
    if duplicates:
        raise RecoveryOptionInputError(
            f"duplicate recovery option ID: {sorted(duplicates)[0]}"
        )
    if any(option.available_quantity < 0 for option in options):
        raise RecoveryOptionInputError("available quantities cannot be negative")
    if any(
        option.unit_cost_cents is not None and option.unit_cost_cents < 0
        for option in options
    ):
        raise RecoveryOptionInputError("unit costs cannot be negative")
    if any(
        option.incremental_cost_cents is not None
        and option.incremental_cost_cents < 0
        for option in options
    ):
        raise RecoveryOptionInputError("incremental costs cannot be negative")


def _option_sort_key(option: RecoveryOptionRecord) -> tuple:
    return (
        option.ready_date is None,
        option.ready_date,
        option.unit_cost_cents is None,
        option.unit_cost_cents,
        option.option_id,
    )


def _to_finding(
    option: RecoveryOptionRecord, coverage_quantity: int, need_by
) -> OptionFinding:
    return OptionFinding(
        option_id=option.option_id,
        category=option.category,
        description=option.description,
        available_quantity=option.available_quantity,
        coverage_quantity=coverage_quantity,
        ready_date=option.ready_date,
        arrives_by_need=option.ready_date <= need_by
        if option.ready_date is not None
        else None,
        approval_status=option.approval_status,
        source_reference=option.source_reference,
        candidate_id=option.candidate_id,
        provider_id=option.provider_id,
        unit_cost_cents=option.unit_cost_cents,
        incremental_cost_cents=option.incremental_cost_cents,
    )


def _search_step(
    category: RecoveryCategory,
    evaluated: tuple[RecoveryOptionRecord, ...] | list[RecoveryOptionRecord],
    qualifying: tuple[RecoveryOptionRecord, ...] | list[RecoveryOptionRecord],
    outcome: str,
) -> SearchStep:
    return SearchStep(
        category=category,
        evaluated_option_ids=tuple(option.option_id for option in evaluated),
        qualifying_option_ids=tuple(option.option_id for option in qualifying),
        outcome=outcome,
    )


def _result(
    *,
    request: RecoverySearchRequest,
    remaining: int,
    approved: list[OptionFinding],
    candidates: list[OptionFinding],
    fallbacks: list[OptionFinding],
    trace: list[SearchStep],
) -> RecoverySearchResult:
    return RecoverySearchResult(
        material_id=request.material_id,
        required_quantity=request.required_quantity,
        need_by=request.need_by,
        approved_covered_quantity=request.required_quantity - remaining,
        remaining_quantity=remaining,
        approved_recovery_sufficient=remaining == 0,
        approved_options=tuple(approved),
        unqualified_candidates=tuple(candidates),
        fallbacks=tuple(fallbacks),
        search_trace=tuple(trace),
    )
