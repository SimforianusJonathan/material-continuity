"""Command-line entry point for qualification graph scheduling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import build_qualification_graph
from .fixtures import load_qualification_fixtures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and schedule a candidate qualification graph"
    )
    parser.add_argument("--candidate", required=True, help="Candidate fixture ID")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("data/fixtures"),
        help="Fixture root (default: data/fixtures)",
    )
    args = parser.parse_args()

    tasks, calendars = load_qualification_fixtures(args.fixtures)
    result = build_qualification_graph(
        candidate_id=args.candidate,
        tasks=tasks,
        calendars=calendars,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
