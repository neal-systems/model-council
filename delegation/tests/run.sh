#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT

pass_count=0
pass() {
  pass_count=$((pass_count + 1))
  echo "PASS $pass_count - $1"
}

contract="$root/delegation/contracts/example.json"
"$root/delegation/scripts/validate-contract.sh" "$contract" >/dev/null
pass "valid contract"

python3 - "$contract" "$tmp/bad.json" <<'PY'
import json, pathlib, sys
body = json.loads(pathlib.Path(sys.argv[1]).read_text())
del body["acceptance_criteria"]
pathlib.Path(sys.argv[2]).write_text(json.dumps(body))
PY
if "$root/delegation/scripts/validate-contract.sh" "$tmp/bad.json" >/dev/null 2>&1; then
  echo "invalid contract passed" >&2
  exit 1
fi
pass "invalid contract blocked"

history="$tmp/history.jsonl"
[[ $("$root/delegation/scripts/pipeline-dispatch.sh" "$contract" "$history") == primary_builder ]]
pass "first standard tier"
printf '%s\n' '{"executor":"primary_builder","status":"FAIL"}' >"$history"
[[ $("$root/delegation/scripts/pipeline-dispatch.sh" "$contract" "$history") == senior_builder ]]
pass "bounded escalation to senior tier"
printf '%s\n' '{"executor":"senior_builder","status":"FAIL"}' >>"$history"
[[ $("$root/delegation/scripts/pipeline-dispatch.sh" "$contract" "$history") == resolver ]]
pass "bounded escalation to resolver"
printf '%s\n' '{"executor":"resolver","status":"BLOCKED"}' >>"$history"
if "$root/delegation/scripts/pipeline-dispatch.sh" "$contract" "$history" >/dev/null 2>&1; then
  echo "blocked history was dispatched" >&2
  exit 1
fi
pass "blocked result routes to owner"

git init -q -b main "$tmp/repo"
git -C "$tmp/repo" -c user.name=Example -c user.email=example@example.invalid commit --allow-empty -qm initial
"$root/delegation/scripts/pipeline-worktree.sh" create "$tmp/repo" example-package "$tmp/work" >/dev/null
pass "linked worktree created"

if DELEGATION_OUTPUT="$tmp/output" "$root/delegation/scripts/pipeline-run-attempt.sh" "$contract" "$tmp/repo" >/dev/null 2>&1; then
  echo "primary checkout accepted" >&2
  exit 1
fi
pass "primary checkout rejected"

DELEGATION_OUTPUT="$tmp/output" "$root/delegation/scripts/pipeline-run-attempt.sh" "$contract" "$tmp/work" >/dev/null
status=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1]).readline())["status"])' "$tmp/output/example-package/attempts.jsonl")
[[ $status == PASS ]]
pass "independent verifier returned PASS"

echo "$pass_count shell checks passed"
