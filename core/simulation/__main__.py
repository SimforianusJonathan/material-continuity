"""Command-line entry point for the canonical recovery simulation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from core.exposure import calculate_exposure
from core.exposure.fixtures import load_exposure_fixtures

from .engine import simulate_recovery
from .fixtures import load_simulation_fixtures


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare recovery scenarios")
    parser.add_argument("--material", required=True, help="Material fixture ID")
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware exposure timestamp",
    )
    parser.add_argument(
        "--shortage-at",
        required=True,
        help="Timezone-aware start of the shortage window",
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
    exposure = calculate_exposure(
        material=material,
        bom_items=boms,
        production_orders=orders,
        receipts=receipts,
        as_of=datetime.fromisoformat(args.as_of),
    )
    result = simulate_recovery(
        exposure=exposure,
        shortage_at=datetime.fromisoformat(args.shortage_at),
        scenarios=load_simulation_fixtures(args.fixtures),
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
