#!/usr/bin/env python3
"""Select one implementation tier from append-only attempt history."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def read_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def choose(contract: dict, history: list[dict]) -> str:
    if history and history[-1].get("status") == "BLOCKED":
        return "owner_action"
    failures = [row for row in history if row.get("status") == "FAIL"]
    limits = contract["escalation"]
    if contract["lane"] == "deterministic":
        used = sum(row.get("executor") == "deterministic_builder" for row in failures)
        return "deterministic_builder" if used < limits["deterministic_max_failures"] else "owner_action"
    tiers = [
        ("primary_builder", "primary_max_failures"),
        ("senior_builder", "senior_max_failures"),
        ("resolver", "resolver_max_failures"),
    ]
    for executor, limit_name in tiers:
        used = sum(row.get("executor") == executor for row in failures)
        if used < limits[limit_name]:
            return executor
    return "owner_action"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: dispatch.py CONTRACT HISTORY", file=sys.stderr)
        return 2
    contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    executor = choose(contract, read_history(Path(sys.argv[2])))
    print(executor)
    return 4 if executor == "owner_action" else 0


if __name__ == "__main__":
    raise SystemExit(main())
