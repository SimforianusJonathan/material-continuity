"""Load local JSON fixtures into typed recovery-option records."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .models import ApprovalStatus, RecoveryCategory, RecoveryOptionRecord


def load_recovery_option_fixtures(
    fixture_root: Path,
) -> tuple[RecoveryOptionRecord, ...]:
    approved_rows = _load_json(
        fixture_root / "recovery-options" / "approved_paths.json"
    )
    fallback_rows = _load_json(fixture_root / "recovery-options" / "fallbacks.json")
    candidate_rows = _load_json(fixture_root / "candidates" / "candidates.json")
    availability_rows = _load_json(
        fixture_root / "suppliers" / "candidate_availability.json"
    )

    candidates = {row["candidate_id"]: row for row in candidate_rows}
    candidate_options: list[RecoveryOptionRecord] = []
    for row in availability_rows:
        candidate_id = row["candidate_id"]
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise ValueError(
                f"candidate availability references unknown candidate: {candidate_id}"
            )
        status = (
            ApprovalStatus.APPROVED
            if candidate["plant_release"]
            else ApprovalStatus(candidate["qualification_status"])
        )
        candidate_options.append(
            RecoveryOptionRecord(
                option_id=row["availability_id"],
                category=RecoveryCategory.UNQUALIFIED_CANDIDATE,
                material_id=row["material_id"],
                description=candidate["description"],
                available_quantity=row["available_quantity"],
                ready_date=date.fromisoformat(row["eta"]),
                approval_status=status,
                source_reference=row["source_reference"],
                candidate_id=candidate_id,
                provider_id=row["supplier_id"],
                unit_cost_cents=row["quoted_unit_price_cents"],
            )
        )

    return tuple(
        [_record_from_row(row) for row in approved_rows]
        + candidate_options
        + [_record_from_row(row) for row in fallback_rows]
    )


def _record_from_row(row: dict[str, Any]) -> RecoveryOptionRecord:
    return RecoveryOptionRecord(
        **{
            **row,
            "category": RecoveryCategory(row["category"]),
            "approval_status": ApprovalStatus(row["approval_status"]),
            "ready_date": _optional_date(row.get("ready_date")),
            "valid_from": _optional_date(row.get("valid_from")),
            "valid_until": _optional_date(row.get("valid_until")),
        }
    )


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
