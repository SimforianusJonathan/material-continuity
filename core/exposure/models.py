"""Typed inputs and outputs for the deterministic exposure engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


class ExposureInputError(ValueError):
    """Raised when exposure inputs are ambiguous or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class Material:
    material_id: str
    description: str
    current_stock: int
    allocated_quantity: int = 0
    quality_hold_quantity: int = 0
    unit: str = "EA"

    @property
    def usable_stock(self) -> int:
        return self.current_stock - self.allocated_quantity - self.quality_hold_quantity


@dataclass(frozen=True, slots=True)
class BOMItem:
    product_id: str
    material_id: str
    quantity_required: int
    bom_revision: str
    valid_from: date
    valid_to: date | None = None

    def is_effective_on(self, scheduled_date: date) -> bool:
        return self.valid_from <= scheduled_date and (
            self.valid_to is None or scheduled_date <= self.valid_to
        )


@dataclass(frozen=True, slots=True)
class ProductionOrder:
    order_id: str
    product_id: str
    quantity: int
    scheduled_date: date
    due_date: date
    priority: int
    status: str


@dataclass(frozen=True, slots=True)
class Receipt:
    po_id: str
    material_id: str
    supplier_id: str
    quantity: int
    expected_delivery: date
    status: str


@dataclass(frozen=True, slots=True)
class AffectedOrder:
    order_id: str
    product_id: str
    scheduled_date: date
    due_date: date
    required_material_quantity: int
    unserved_quantity: int


@dataclass(frozen=True, slots=True)
class ProjectedDay:
    date: date
    confirmed_receipts: int
    material_demand: int
    ending_available: int
    unserved_quantity: int


@dataclass(frozen=True, slots=True)
class ExposureResult:
    material_id: str
    as_of: str
    current_usable_stock: int
    shortage_date: date | None
    affected_orders: tuple[AffectedOrder, ...]
    projection: tuple[ProjectedDay, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation without custom encoders."""

        def serialize(value: Any) -> Any:
            if isinstance(value, date):
                return value.isoformat()
            if isinstance(value, tuple):
                return [serialize(item) for item in value]
            if isinstance(value, list):
                return [serialize(item) for item in value]
            if isinstance(value, dict):
                return {key: serialize(item) for key, item in value.items()}
            return value

        return serialize(asdict(self))
