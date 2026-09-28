"""Load source-version fixtures for recovery-case construction."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import SourceType, SourceVersion


def load_source_version_fixtures(
    fixture_root: Path,
) -> tuple[SourceVersion, ...]:
    rows = _load_json(fixture_root / "case-state" / "source_versions.json")
    return tuple(
        SourceVersion(
            **{
                **row,
                "source_type": SourceType(row["source_type"]),
                "observed_at": datetime.fromisoformat(row["observed_at"]),
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
