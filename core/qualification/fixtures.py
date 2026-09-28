"""Load qualification task and resource-calendar fixtures."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import QualificationTask, ResourceCalendar, TaskType


def load_qualification_fixtures(
    fixture_root: Path,
) -> tuple[tuple[QualificationTask, ...], tuple[ResourceCalendar, ...]]:
    task_rows = _load_json(fixture_root / "qualification" / "tasks.json")
    calendar_rows = _load_json(
        fixture_root / "qualification" / "resource_calendars.json"
    )
    tasks = tuple(
        QualificationTask(
            **{
                **row,
                "task_type": TaskType(row["task_type"]),
                "duration_hours": Decimal(str(row["duration_hours"]))
                if row["duration_hours"] is not None
                else None,
                "predecessor_ids": tuple(row["predecessor_ids"]),
                "earliest_start": datetime.fromisoformat(row["earliest_start"])
                if row["earliest_start"]
                else None,
            }
        )
        for row in task_rows
    )
    calendars = tuple(
        ResourceCalendar(
            resource_id=row["resource_id"],
            timezone=row["timezone"],
            working_weekdays=tuple(row["working_weekdays"]),
            workday_start=time.fromisoformat(row["workday_start"]),
            workday_end=time.fromisoformat(row["workday_end"]),
            unavailable_dates=tuple(
                date.fromisoformat(value) for value in row["unavailable_dates"]
            ),
        )
        for row in calendar_rows
    )
    return tasks, calendars


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
