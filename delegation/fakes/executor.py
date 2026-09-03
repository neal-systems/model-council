#!/usr/bin/env python3
"""Offline implementation stand-in used by the public demonstration and tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: executor.py CONTRACT WORKTREE EXECUTOR", file=sys.stderr)
        return 2
    contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    worktree = Path(sys.argv[2])
    executor = sys.argv[3]
    candidate = contract["expected_changes"][0]
    if any(character in candidate for character in "*?["):
        print("fake executor needs one literal expected_changes path", file=sys.stderr)
        return 2
    path = worktree / candidate
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("offline pipeline result\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(worktree), "add", "--", candidate], check=True)
    subprocess.run(
        ["git", "-C", str(worktree), "-c", "user.name=Offline Example", "-c",
         "user.email=example@example.invalid", "commit", "-m", f"{executor} attempt"],
        check=True, capture_output=True, text=True,
    )
    sha = subprocess.run(
        ["git", "-C", str(worktree), "rev-parse", "HEAD"], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    print(sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
