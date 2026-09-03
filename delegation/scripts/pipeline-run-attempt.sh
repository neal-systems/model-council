#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "usage: pipeline-run-attempt.sh CONTRACT ISOLATED_WORKTREE" >&2
  exit 2
fi

contract=$(realpath "$1")
worktree=$(realpath "$2")
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/../.." && pwd)
"$script_dir/validate-contract.sh" "$contract" >/dev/null

git -C "$worktree" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "BLOCKED: implementation path is not a git worktree" >&2
  exit 3
}

listed=$(git -C "$worktree" worktree list --porcelain | awk '/^worktree / {print substr($0, 10)}')
count=$(printf '%s\n' "$listed" | sed '/^$/d' | wc -l)
first=$(printf '%s\n' "$listed" | sed -n '1p')
if [[ $count -lt 2 || $first == "$worktree" ]]; then
  echo "BLOCKED: implementation must run in a linked worktree, not the primary checkout" >&2
  exit 3
fi

package_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["package_id"])' "$contract")
output_root=${DELEGATION_OUTPUT:-$repo_root/.pipeline-output}
package_output="$output_root/$package_id"
history="$package_output/attempts.jsonl"
mkdir -p "$package_output"

set +e
executor=$("$script_dir/pipeline-dispatch.sh" "$contract" "$history")
dispatch_code=$?
set -e
if [[ $dispatch_code -eq 4 ]]; then
  echo "BLOCKED: escalation limits reached; owner action required" >&2
  exit 3
elif [[ $dispatch_code -ne 0 ]]; then
  exit "$dispatch_code"
fi

attempt=$(python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); print(1 + (len(p.read_text().splitlines()) if p.exists() else 0))' "$history")
attempt_dir="$package_output/$executor-attempt-$attempt"
evidence="$attempt_dir/evidence"
verdict="$attempt_dir/verdict.json"
mkdir -p "$evidence"
before=$(git -C "$worktree" rev-parse HEAD)

executor_command=${DELEGATION_EXECUTOR_COMMAND:-python3 $repo_root/delegation/fakes/executor.py}
read -r -a executor_argv <<<"$executor_command"
"${executor_argv[@]}" "$contract" "$worktree" "$executor" >"$attempt_dir/executor.stdout" 2>"$attempt_dir/executor.stderr"
after=$(git -C "$worktree" rev-parse HEAD)

set +e
python3 "$script_dir/verify.py" "$contract" "$worktree" "$executor" "$attempt" "$before" "$after" "$evidence" "$verdict"
verify_code=$?
set -e
python3 - "$verdict" "$history" <<'PY'
import json, pathlib, sys
verdict = json.loads(pathlib.Path(sys.argv[1]).read_text())
with pathlib.Path(sys.argv[2]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(verdict, sort_keys=True) + "\n")
PY
exit "$verify_code"
