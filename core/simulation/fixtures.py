"""Load explicit recovery-scenario fixtures."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ScenarioInput, ScenarioType


def load_simulation_fixtures(fixture_root: Path) -> tuple[ScenarioInput, ...]:
    rows = _load_json(fixture_root / "simulation" / "scenarios.json")
    return tuple(
        ScenarioInput(
            **{
                **row,
                "scenario_type": ScenarioType(row["scenario_type"]),
                "ready_at": _optional_datetime(row["ready_at"]),
                "qualification_complete": _optional_datetime(
                    row["qualification_complete"]
                ),
                "unresolved_conditions": tuple(row["unresolved_conditions"]),
                "source_references": tuple(row["source_references"]),
            }
        )
        for row in rows
    )


def _optional_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
