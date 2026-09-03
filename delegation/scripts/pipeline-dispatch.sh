#!/usr/bin/env bash
set -euo pipefail
[[ $# == 2 ]] || {
  echo "usage: pipeline-dispatch.sh CONTRACT HISTORY" >&2
  exit 2
}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 "$script_dir/dispatch.py" "$1" "$2"
