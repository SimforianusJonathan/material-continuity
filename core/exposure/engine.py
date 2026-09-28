"""Pure, deterministic stock-depletion and production-exposure calculation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from .models import (
    AffectedOrder,
    BOMItem,
    ExposureInputError,
    ExposureResult,
    Material,
    ProductionOrder,
    ProjectedDay,
    Receipt,
)

ACTIVE_ORDER_STATUSES = frozenset({"PLANNED", "RELEASED"})
CONFIRMED_RECEIPT_STATUS = "CONFIRMED"


def calculate_exposure(
    *,
    material: Material,
    bom_items: Iterable[BOMItem],
    production_orders: Iterable[ProductionOrder],
    receipts: Iterable[Receipt],
    as_of: datetime,
) -> ExposureResult:
    """Calculate the first shortage date and all affected future orders.

    The calculation operates at calendar-day grain. Confirmed receipts on a day
    are made available before that day's production orders. Orders sharing a day
    are allocated by descending priority, then due date and order ID. The
    shortage date is the first date on which a production order cannot be fully
    served, not the date on which stock merely reaches zero.
    """

    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ExposureInputError("as_of must be an ISO-8601 timezone-aware timestamp")
    if material.current_stock < 0:
        raise ExposureInputError("current_stock cannot be negative")
    if material.allocated_quantity < 0 or material.quality_hold_quantity < 0:
        raise ExposureInputError("allocated and quality-hold quantities cannot be negative")
    if material.usable_stock < 0:
        raise ExposureInputError("allocations and quality holds exceed current stock")

    bom_list = tuple(bom_items)
    order_list = tuple(production_orders)
    receipt_list = tuple(receipts)
    _require_unique_ids("production order", (order.order_id for order in order_list))
    _require_unique_ids("purchase order", (receipt.po_id for receipt in receipt_list))
    _validate_positive_quantities(bom_list, order_list, receipt_list)

    as_of_date = as_of.date()
    products_using_material = {
        item.product_id for item in bom_list if item.material_id == material.material_id
    }
    relevant_orders = [
        order
        for order in order_list
        if order.scheduled_date >= as_of_date
        and order.status.upper() in ACTIVE_ORDER_STATUSES
        and order.product_id in products_using_material
    ]
    relevant_receipts = [
        receipt
        for receipt in receipt_list
        if receipt.material_id == material.material_id
        and receipt.expected_delivery >= as_of_date
        and receipt.status.upper() == CONFIRMED_RECEIPT_STATUS
    ]

    orders_by_date: dict = defaultdict(list)
    receipts_by_date: dict = defaultdict(int)
    for order in relevant_orders:
        orders_by_date[order.scheduled_date].append(order)
    for receipt in relevant_receipts:
        receipts_by_date[receipt.expected_delivery] += receipt.quantity

    event_dates = sorted(set(orders_by_date) | set(receipts_by_date))
    available = material.usable_stock
    shortage_date = None
    affected_orders: list[AffectedOrder] = []
    projection: list[ProjectedDay] = []

    for event_date in event_dates:
        received = receipts_by_date[event_date]
        available += received
        day_demand = 0
        day_unserved = 0

        day_orders = sorted(
            orders_by_date[event_date],
            key=lambda order: (-order.priority, order.due_date, order.order_id),
        )
        for order in day_orders:
            bom = _effective_bom(
                bom_items=bom_list,
                product_id=order.product_id,
                material_id=material.material_id,
                scheduled_date=order.scheduled_date,
            )
            required = order.quantity * bom.quantity_required
            served = min(available, required)
            unserved = required - served
            available -= served
            day_demand += required
            day_unserved += unserved

            if unserved:
                if shortage_date is None:
                    shortage_date = event_date
                affected_orders.append(
                    AffectedOrder(
                        order_id=order.order_id,
                        product_id=order.product_id,
                        scheduled_date=order.scheduled_date,
                        due_date=order.due_date,
                        required_material_quantity=required,
                        unserved_quantity=unserved,
                    )
                )

        projection.append(
            ProjectedDay(
                date=event_date,
                confirmed_receipts=received,
                material_demand=day_demand,
                ending_available=available,
                unserved_quantity=day_unserved,
            )
        )

    return ExposureResult(
        material_id=material.material_id,
        as_of=as_of.isoformat(),
        current_usable_stock=material.usable_stock,
        shortage_date=shortage_date,
        affected_orders=tuple(affected_orders),
        projection=tuple(projection),
    )


def _effective_bom(
    *,
    bom_items: tuple[BOMItem, ...],
    product_id: str,
    material_id: str,
    scheduled_date,
) -> BOMItem:
    matches = [
        item
        for item in bom_items
        if item.product_id == product_id
        and item.material_id == material_id
        and item.is_effective_on(scheduled_date)
    ]
    if not matches:
        raise ExposureInputError(
            f"no effective BOM for product {product_id}, material {material_id}, "
            f"date {scheduled_date.isoformat()}"
        )
    if len(matches) > 1:
        raise ExposureInputError(
            f"multiple effective BOM rows for product {product_id}, material {material_id}, "
            f"date {scheduled_date.isoformat()}"
        )
    return matches[0]


def _require_unique_ids(entity: str, identifiers: Iterable[str]) -> None:
    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            raise ExposureInputError(f"duplicate {entity} ID: {identifier}")
        seen.add(identifier)


def _validate_positive_quantities(
    bom_items: tuple[BOMItem, ...],
    orders: tuple[ProductionOrder, ...],
    receipts: tuple[Receipt, ...],
) -> None:
    if any(item.quantity_required <= 0 for item in bom_items):
        raise ExposureInputError("BOM quantities must be positive")
    if any(order.quantity <= 0 for order in orders):
        raise ExposureInputError("production-order quantities must be positive")
    if any(receipt.quantity <= 0 for receipt in receipts):
        raise ExposureInputError("receipt quantities must be positive")
