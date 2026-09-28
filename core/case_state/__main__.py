"""Command-line entry point for canonical recovery-case construction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .canonical import build_canonical_case


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the canonical recovery case")
    parser.add_argument("--case-id", default="CASE-001")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("data/fixtures"),
        help="Fixture root (default: data/fixtures)",
    )
    args = parser.parse_args()

    case = build_canonical_case(args.fixtures, case_id=args.case_id)
    print(json.dumps(case.to_dict(), indent=2))


if __name__ == "__main__":
    main()
