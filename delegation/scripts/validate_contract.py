#!/usr/bin/env python3
"""Validate the contract properties used by the runtime, with no dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REQUIRED = {
    "package_id", "objective", "lane", "allowed_scope", "expected_changes",
    "prohibited_changes", "acceptance_criteria", "verification", "environment",
    "escalation", "authority", "contract_version",
}


def errors(contract: dict) -> list[str]:
    found: list[str] = []
    missing = REQUIRED - set(contract)
    if missing:
        found.append("missing fields: " + ", ".join(sorted(missing)))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}", str(contract.get("package_id", ""))):
        found.append("package_id is not safe for a path or branch")
    if contract.get("lane") not in {"standard", "deterministic"}:
        found.append("lane must be standard or deterministic")
    criteria = {item.get("id") for item in contract.get("acceptance_criteria", []) if isinstance(item, dict)}
    if not criteria:
        found.append("at least one acceptance criterion is required")
    covered = set()
    for command in contract.get("verification", {}).get("commands", []):
        covered.update(command.get("satisfies", []))
        if not command.get("cmd") or not isinstance(command.get("expected_exit_code"), int):
            found.append("every verification command needs cmd and expected_exit_code")
    if criteria - covered:
        found.append("uncovered acceptance criteria: " + ", ".join(sorted(criteria - covered)))
    if not contract.get("expected_changes"):
        found.append("expected_changes must not be empty")
    limits = contract.get("escalation", {})
    for name in ("primary_max_failures", "senior_max_failures", "resolver_max_failures", "deterministic_max_failures"):
        value = limits.get(name)
        if not isinstance(value, int) or not 1 <= value <= 5:
            found.append(f"{name} must be an integer from 1 through 5")
    return found


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_contract.py CONTRACT", file=sys.stderr)
        return 2
    try:
        contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"BLOCKED: contract cannot be read: {error}", file=sys.stderr)
        return 2
    found = errors(contract)
    if found:
        for message in found:
            print("BLOCKED: " + message, file=sys.stderr)
        return 2
    print("PASS: contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
