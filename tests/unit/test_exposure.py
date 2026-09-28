from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from core.exposure import (
    BOMItem,
    ExposureInputError,
    Material,
    ProductionOrder,
    Receipt,
    calculate_exposure,
)


AS_OF = datetime(2026, 9, 29, tzinfo=timezone.utc)


class ExposureEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.material = Material("MAT-1", "Test bearing", 200)
        self.bom = (
            BOMItem("PRODUCT-1", "MAT-1", 1, "A", date(2026, 1, 1)),
        )

    def test_reports_first_order_after_exact_depletion(self) -> None:
        result = self.calculate(
            stock=200,
            orders=(self.order("MO-1", 100, 1), self.order("MO-2", 100, 2), self.order("MO-3", 100, 3)),
        )

        self.assertEqual(date(2026, 10, 3), result.shortage_date)
        self.assertEqual(("MO-3",), tuple(item.order_id for item in result.affected_orders))

    def test_confirmed_receipt_before_shortage_extends_coverage(self) -> None:
        result = self.calculate(
            stock=100,
            orders=(self.order("MO-1", 100, 1), self.order("MO-2", 100, 2), self.order("MO-3", 100, 3)),
            receipts=(self.receipt("PO-1", 100, 2),),
        )

        self.assertEqual(date(2026, 10, 3), result.shortage_date)
        self.assertEqual(100, result.projection[1].confirmed_receipts)

    def test_receipt_after_shortage_does_not_rewrite_first_shortage(self) -> None:
        result = self.calculate(
            stock=100,
            orders=(self.order("MO-1", 100, 1), self.order("MO-2", 100, 2), self.order("MO-3", 100, 3)),
            receipts=(self.receipt("PO-1", 100, 3),),
        )

        self.assertEqual(date(2026, 10, 2), result.shortage_date)
        self.assertEqual(("MO-2",), tuple(item.order_id for item in result.affected_orders))

    def test_zero_stock_exposes_first_order(self) -> None:
        result = self.calculate(stock=0, orders=(self.order("MO-1", 75, 1),))

        self.assertEqual(date(2026, 10, 1), result.shortage_date)
        self.assertEqual(75, result.affected_orders[0].unserved_quantity)

    def test_same_day_orders_use_priority_then_report_partial_shortage(self) -> None:
        high = self.order("MO-HIGH", 100, 1, priority=100)
        low = self.order("MO-LOW", 100, 1, priority=10)

        result = self.calculate(stock=150, orders=(low, high))

        self.assertEqual(("MO-LOW",), tuple(item.order_id for item in result.affected_orders))
        self.assertEqual(50, result.affected_orders[0].unserved_quantity)

    def test_repeat_calculation_is_idempotent(self) -> None:
        orders = (self.order("MO-1", 250, 1),)

        first = self.calculate(stock=200, orders=orders)
        second = self.calculate(stock=200, orders=orders)

        self.assertEqual(first, second)

    def test_order_for_product_that_does_not_use_material_is_ignored(self) -> None:
        unrelated = ProductionOrder(
            "MO-OTHER",
            "PRODUCT-OTHER",
            1000,
            date(2026, 10, 1),
            date(2026, 10, 1),
            100,
            "RELEASED",
        )

        result = self.calculate(stock=50, orders=(unrelated,))

        self.assertIsNone(result.shortage_date)
        self.assertEqual((), result.affected_orders)
        self.assertEqual((), result.projection)

    def test_duplicate_order_ids_fail_closed(self) -> None:
        duplicate_orders = (self.order("MO-1", 100, 1), self.order("MO-1", 100, 2))

        with self.assertRaisesRegex(ExposureInputError, "duplicate production order ID"):
            self.calculate(stock=200, orders=duplicate_orders)

    def test_naive_as_of_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(ExposureInputError, "timezone-aware"):
            calculate_exposure(
                material=self.material,
                bom_items=self.bom,
                production_orders=(),
                receipts=(),
                as_of=datetime(2026, 9, 29),
            )

    def calculate(self, *, stock: int, orders=(), receipts=()):
        return calculate_exposure(
            material=Material("MAT-1", "Test bearing", stock),
            bom_items=self.bom,
            production_orders=orders,
            receipts=receipts,
            as_of=AS_OF,
        )

    @staticmethod
    def order(order_id: str, quantity: int, day: int, priority: int = 50) -> ProductionOrder:
        scheduled = date(2026, 10, day)
        return ProductionOrder(
            order_id,
            "PRODUCT-1",
            quantity,
            scheduled,
            scheduled,
            priority,
            "RELEASED",
        )

    @staticmethod
    def receipt(po_id: str, quantity: int, day: int) -> Receipt:
        return Receipt(po_id, "MAT-1", "SUP-1", quantity, date(2026, 10, day), "CONFIRMED")


if __name__ == "__main__":
    unittest.main()
