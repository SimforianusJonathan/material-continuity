"""Command-line entry point for candidate requirement comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import compare_requirements
from .fixtures import load_requirement_fixtures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare candidate evidence with application requirements"
    )
    parser.add_argument("--candidate", required=True, help="Candidate fixture ID")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("data/fixtures"),
        help="Fixture root (default: data/fixtures)",
    )
    args = parser.parse_args()

    requirements, evidence = load_requirement_fixtures(args.fixtures)
    result = compare_requirements(
        candidate_id=args.candidate,
        requirements=requirements,
        evidence=evidence,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
