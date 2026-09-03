"""Turn a recorded council cut into dependency-ordered work packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def dependency_waves(parts: list[dict]) -> list[list[dict]]:
    ids = {part["part_id"] for part in parts}
    for part in parts:
        missing = set(part.get("depends_on", [])) - ids
        if missing:
            raise ValueError(f"{part['part_id']} depends on missing parts: {', '.join(sorted(missing))}")
    done: set[str] = set()
    remaining = list(parts)
    waves: list[list[dict]] = []
    while remaining:
        wave = [part for part in remaining if set(part.get("depends_on", [])) <= done]
        if not wave:
            raise ValueError("dependency cycle: " + ", ".join(part["part_id"] for part in remaining))
        waves.append(wave)
        done.update(part["part_id"] for part in wave)
        remaining = [part for part in remaining if part not in wave]
    return waves


def make_plan(cut: dict) -> dict:
    parts = [
        {
            "part_id": row["position_id"],
            "question": row["text"],
            "acceptance": row.get("acceptance") or "The stated question has a checkable answer.",
            "depends_on": row.get("depends_on", []),
            "treatment": "pipeline" if row["position_id"] in {"implementation", "verification"} else "direct",
        }
        for row in cut.get("positions", [])
        if row.get("kind") == "part" and row.get("state") != "CONTESTED"
    ]
    kept = [row["text"] for row in cut.get("positions", []) if row.get("kind") == "whole"]
    waves = dependency_waves(parts)
    return {
        "parts": parts,
        "waves": [[part["part_id"] for part in wave] for wave in waves],
        "kept_whole": kept,
        "operator_decisions": kept,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="council-delegate")
    parser.add_argument("run_directory")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    source = Path(args.run_directory) / "cut.json"
    if not source.exists():
        parser.error(f"no cut at {source}")
    try:
        plan = make_plan(json.loads(source.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValueError) as error:
        print(f"council-delegate: {error}", file=sys.stderr)
        return 2
    target = Path(args.out) if args.out else Path(args.run_directory) / "plan.json"
    target.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
