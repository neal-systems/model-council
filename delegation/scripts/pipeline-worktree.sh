#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: pipeline-worktree.sh create REPOSITORY PACKAGE_ID DESTINATION" >&2
  exit 2
}

[[ ${1:-} == create && $# == 4 ]] || usage
repository=$2
package_id=$3
destination=$4
[[ $package_id =~ ^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$ ]] || {
  echo "BLOCKED: invalid package id" >&2
  exit 3
}
[[ ! -e $destination ]] || {
  echo "BLOCKED: destination already exists" >&2
  exit 3
}
git -C "$repository" rev-parse --is-inside-work-tree >/dev/null
git -C "$repository" worktree add -b "work/$package_id" "$destination" HEAD >/dev/null
printf '%s\n' "$destination"
