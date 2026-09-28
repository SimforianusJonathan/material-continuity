"""Assemble the local canonical scenario into a versioned recovery case."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.exposure import calculate_exposure
from core.exposure.fixtures import load_exposure_fixtures
from core.qualification import build_qualification_graph
from core.qualification.fixtures import load_qualification_fixtures
from core.recovery_options import RecoverySearchRequest, find_recovery_options
from core.recovery_options.fixtures import load_recovery_option_fixtures
from core.requirements import compare_requirements
from core.requirements.fixtures import load_requirement_fixtures
from core.simulation import simulate_recovery
from core.simulation.fixtures import load_simulation_fixtures

from .engine import create_case
from .fixtures import load_source_version_fixtures
from .models import CaseStatus, CaseTrigger, RecoveryCase, TriggerType


def build_canonical_case(
    fixture_root: Path,
    *,
    case_id: str = "CASE-001",
    created_at: datetime = datetime(2026, 9, 29, 3, tzinfo=timezone.utc),
) -> RecoveryCase:
    material, boms, orders, receipts = load_exposure_fixtures(
        fixture_root, "MAT-BRG-001"
    )
    exposure = calculate_exposure(
        material=material,
        bom_items=boms,
        production_orders=orders,
        receipts=receipts,
        as_of=datetime(2026, 9, 29, tzinfo=timezone.utc),
    )
    if exposure.shortage_date is None:
        raise ValueError("canonical fixture must produce a shortage")
    required_quantity = sum(
        order.unserved_quantity for order in exposure.affected_orders
    )
    recovery_options = find_recovery_options(
        request=RecoverySearchRequest(
            material_id="MAT-BRG-001",
            required_quantity=required_quantity,
            need_by=exposure.shortage_date,
            as_of=datetime(2026, 9, 29).date(),
        ),
        options=load_recovery_option_fixtures(fixture_root),
    )
    requirements, evidence = load_requirement_fixtures(fixture_root)
    comparisons = tuple(
        compare_requirements(
            candidate_id=candidate_id,
            requirements=requirements,
            evidence=evidence,
        )
        for candidate_id in ("CAND-A", "CAND-B")
    )
    tasks, calendars = load_qualification_fixtures(fixture_root)
    qualification = build_qualification_graph(
        candidate_id="CAND-A", tasks=tasks, calendars=calendars
    )
    simulation = simulate_recovery(
        exposure=exposure,
        shortage_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
        scenarios=load_simulation_fixtures(fixture_root),
    )
    return create_case(
        case_id=case_id,
        status=CaseStatus.UNDER_REVIEW,
        trigger=CaseTrigger(
            event_id="EVT-DELAY-001",
            trigger_type=TriggerType.DELIVERY_DELAY,
            material_id="MAT-BRG-001",
            detected_at=datetime(2026, 9, 29, 1, tzinfo=timezone.utc),
            source_reference="purchase-order:PO-ORIGINAL-001",
        ),
        exposure=exposure,
        recovery_options=recovery_options,
        candidate_comparisons=comparisons,
        qualification_graphs=(qualification,),
        simulation=simulation,
        source_versions=load_source_version_fixtures(fixture_root),
        created_at=created_at,
    )
