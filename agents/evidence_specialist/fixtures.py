"""Load local qualification-procedure retrieval fixtures."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import QualificationProcedureReference


def load_qualification_procedure_fixtures(
    fixture_root: Path,
) -> tuple[QualificationProcedureReference, ...]:
    rows = _load_json(fixture_root / "evidence" / "qualification_procedures.json")
    return tuple(
        QualificationProcedureReference(
            **{
                **row,
                "duration_hours": (
                    Decimal(str(row["duration_hours"]))
                    if row.get("duration_hours") is not None
                    else None
                ),
            }
        )
        for row in rows
    )


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
