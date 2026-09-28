"""Load synthetic structured evidence-extraction fixtures."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from core.requirements.models import ScalarValue

from .models import EvidenceExtraction, ExtractionSupportStatus


def load_evidence_extraction_fixtures(
    fixture_root: Path,
) -> tuple[EvidenceExtraction, ...]:
    rows = _load_json(fixture_root / "evidence" / "extractions.json")
    return tuple(
        EvidenceExtraction(
            **{
                **row,
                "value": _scalar(row.get("value")),
                "support_status": ExtractionSupportStatus(row["support_status"]),
                "extraction_confidence": (
                    Decimal(str(row["extraction_confidence"]))
                    if row.get("extraction_confidence") is not None
                    else None
                ),
            }
        )
        for row in rows
    )


def _scalar(value: Any) -> ScalarValue | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        return value
    raise ValueError(f"unsupported extraction scalar value: {value!r}")


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
