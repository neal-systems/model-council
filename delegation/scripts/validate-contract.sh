#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 ]] || {
  echo "usage: validate-contract.sh CONTRACT" >&2
  exit 2
}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 "$script_dir/validate_contract.py" "$1"
