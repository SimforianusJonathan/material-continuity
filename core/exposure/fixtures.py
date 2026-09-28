"""Load local JSON fixtures into typed exposure inputs."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .models import BOMItem, Material, ProductionOrder, Receipt


def load_exposure_fixtures(
    fixture_root: Path, material_id: str
) -> tuple[Material, tuple[BOMItem, ...], tuple[ProductionOrder, ...], tuple[Receipt, ...]]:
    materials = _load_json(fixture_root / "materials" / "materials.json")
    bom_rows = _load_json(fixture_root / "bom" / "bom.json")
    order_rows = _load_json(
        fixture_root / "production-orders" / "production_orders.json"
    )
    receipt_rows = _load_json(
        fixture_root / "purchase-orders" / "purchase_orders.json"
    )

    material_row = next(
        (row for row in materials if row["material_id"] == material_id), None
    )
    if material_row is None:
        raise ValueError(f"unknown material fixture: {material_id}")

    material = Material(**material_row)
    boms = tuple(
        BOMItem(
            **{
                **row,
                "valid_from": date.fromisoformat(row["valid_from"]),
                "valid_to": date.fromisoformat(row["valid_to"])
                if row.get("valid_to")
                else None,
            }
        )
        for row in bom_rows
        if row["material_id"] == material_id
    )
    orders = tuple(
        ProductionOrder(
            **{
                **row,
                "scheduled_date": date.fromisoformat(row["scheduled_date"]),
                "due_date": date.fromisoformat(row["due_date"]),
            }
        )
        for row in order_rows
    )
    receipts = tuple(
        Receipt(
            **{
                **row,
                "expected_delivery": date.fromisoformat(row["expected_delivery"]),
            }
        )
        for row in receipt_rows
        if row["material_id"] == material_id
    )
    return material, boms, orders, receipts


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError(f"fixture must contain a JSON array: {path}")
    return value
