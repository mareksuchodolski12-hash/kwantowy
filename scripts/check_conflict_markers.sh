#!/usr/bin/env bash
set -euo pipefail

if rg -n "^<<<<<<<|^=======|^>>>>>>>" .; then
  echo "Conflict markers detected." >&2
  exit 1
fi

echo "No conflict markers found."
