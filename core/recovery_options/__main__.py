"""Command-line entry point for local recovery-option discovery."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .engine import find_recovery_options
from .fixtures import load_recovery_option_fixtures
from .models import RecoverySearchRequest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find deterministic material-recovery options"
    )
    parser.add_argument("--material", required=True, help="Material fixture ID")
    parser.add_argument("--required-quantity", required=True, type=int)
    parser.add_argument("--need-by", required=True, type=date.fromisoformat)
    parser.add_argument("--as-of", required=True, type=date.fromisoformat)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("data/fixtures"),
        help="Fixture root (default: data/fixtures)",
    )
    args = parser.parse_args()

    options = load_recovery_option_fixtures(args.fixtures)
    result = find_recovery_options(
        request=RecoverySearchRequest(
            material_id=args.material,
            required_quantity=args.required_quantity,
            need_by=args.need_by,
            as_of=args.as_of,
        ),
        options=options,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
