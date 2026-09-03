#!/usr/bin/env python3
"""Independent, contract-driven verifier for one candidate revision."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def git(worktree: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(worktree), *args], check=True, capture_output=True, text=True).stdout.strip()


def verify(args: argparse.Namespace) -> dict:
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    worktree = Path(args.worktree).resolve()
    evidence = Path(args.evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    base = {
        "package_id": contract["package_id"], "executor": args.executor,
        "attempt": args.attempt, "candidate_sha": args.after,
        "commands_run": [], "changed_files": [], "evidence_directory": str(evidence),
    }
    missing = [path for path in contract["environment"].get("required_paths", []) if not (worktree / path).exists()]
    if missing:
        return {**base, "status": "BLOCKED", "blocked_defect": "missing required paths: " + ", ".join(missing), "blocked_owner": "owner"}
    changed = git(worktree, "diff", "--name-only", f"{args.before}..{args.after}").splitlines()
    base["changed_files"] = changed
    unexpected = [path for path in changed if not matches(path, contract["expected_changes"])]
    prohibited = [path for path in changed if matches(path, contract["prohibited_changes"])]
    if unexpected or prohibited:
        detail = "unexpected=" + ",".join(unexpected) + " prohibited=" + ",".join(prohibited)
        return {**base, "status": "FAIL", "failed_criterion": "SCOPE", "failure_evidence": detail}
    for command in contract["verification"]["commands"]:
        try:
            completed = subprocess.run(
                ["bash", "-lc", command["cmd"]], cwd=worktree, capture_output=True,
                text=True, timeout=command["timeout_seconds"],
            )
            output = completed.stdout + completed.stderr
            matched = completed.returncode == command["expected_exit_code"]
            if "expected_stdout_match" in command:
                matched = matched and command["expected_stdout_match"] in output
            base["commands_run"].append(
                {"id": command["id"], "cmd": command["cmd"], "exit_code": completed.returncode,
                 "expected_exit_code": command["expected_exit_code"], "matched": matched,
                 "output_excerpt": output[-1000:]}
            )
        except subprocess.TimeoutExpired:
            matched = False
            base["commands_run"].append({"id": command["id"], "cmd": command["cmd"], "exit_code": 124, "matched": False, "output_excerpt": "timed out"})
        if not matched:
            return {**base, "status": "FAIL", "failed_criterion": command["id"], "failure_evidence": base["commands_run"][-1]["output_excerpt"]}
    for artifact in contract["verification"].get("required_artifacts", []):
        path = worktree / artifact["path"]
        exists = path.exists()
        good = exists == artifact["must_exist"]
        if good and exists and artifact.get("must_contain"):
            good = artifact["must_contain"] in path.read_text(encoding="utf-8", errors="replace")
        if not good:
            return {**base, "status": "FAIL", "failed_criterion": "ARTIFACT", "failure_evidence": artifact["path"]}
    return {**base, "status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract")
    parser.add_argument("worktree")
    parser.add_argument("executor")
    parser.add_argument("attempt", type=int)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("evidence")
    parser.add_argument("verdict")
    args = parser.parse_args()
    result = verify(args)
    Path(args.verdict).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
