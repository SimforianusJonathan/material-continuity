"""Command-line entry point for the local exposure fixture."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .engine import calculate_exposure
from .fixtures import load_exposure_fixtures


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate deterministic material exposure")
    parser.add_argument("--material", required=True, help="Material fixture ID")
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware ISO-8601 timestamp, for example 2026-09-29T00:00:00+00:00",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("data/fixtures"),
        help="Fixture root (default: data/fixtures)",
    )
    args = parser.parse_args()

    material, boms, orders, receipts = load_exposure_fixtures(
        args.fixtures, args.material
    )
    result = calculate_exposure(
        material=material,
        bom_items=boms,
        production_orders=orders,
        receipts=receipts,
        as_of=datetime.fromisoformat(args.as_of),
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
