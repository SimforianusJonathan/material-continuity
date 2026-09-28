from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from core.exposure import calculate_exposure
from core.exposure.fixtures import load_exposure_fixtures


class CanonicalExposureFixtureTests(unittest.TestCase):
    def test_canonical_fixture_shortage_starts_on_october_fourth(self) -> None:
        fixture_root = Path(__file__).parents[2] / "data" / "fixtures"
        material, boms, orders, receipts = load_exposure_fixtures(
            fixture_root, "MAT-BRG-001"
        )

        result = calculate_exposure(
            material=material,
            bom_items=boms,
            production_orders=orders,
            receipts=receipts,
            as_of=datetime(2026, 9, 29, tzinfo=timezone.utc),
        )

        self.assertEqual(300, result.current_usable_stock)
        self.assertEqual(date(2026, 10, 4), result.shortage_date)
        self.assertEqual("MO-004", result.affected_orders[0].order_id)
        self.assertEqual(7, len(result.affected_orders))


if __name__ == "__main__":
    unittest.main()
