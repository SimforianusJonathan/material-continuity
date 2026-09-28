"""Load requirement and candidate-evidence JSON fixtures."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import (
    CandidateEvidence,
    ComparisonOperator,
    Requirement,
    RequirementCriticality,
    RequirementKind,
    ScalarValue,
)


def load_requirement_fixtures(
    fixture_root: Path,
) -> tuple[tuple[Requirement, ...], tuple[CandidateEvidence, ...]]:
    requirement_rows = _load_json(
        fixture_root / "requirements" / "engineering_requirements.json"
    )
    evidence_rows = _load_json(
        fixture_root
        / "candidate-specifications"
        / "candidate_specifications.json"
    )
    requirements = tuple(
        Requirement(
            **{
                **row,
                "operator": ComparisonOperator(row["operator"]),
                "required_value": _scalar(row["required_value"]),
                "criticality": RequirementCriticality(row["criticality"]),
                "kind": RequirementKind(row["kind"]),
            }
        )
        for row in requirement_rows
    )
    evidence = tuple(
        CandidateEvidence(
            **{
                **row,
                "value": _scalar(row["value"]),
            }
        )
        for row in evidence_rows
    )
    return requirements, evidence


def _scalar(value: Any) -> ScalarValue:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        return value
    raise ValueError(f"unsupported scalar fixture value: {value!r}")


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
