#!/usr/bin/env bash
# Smoke: run moverStatus.sh against the disposable Unraid command contract (Linux; GNU date/stat).
# Run from the repo root: uv run --no-project bash scripts/smoke.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# The tests must not leave files behind in the repo.
before="$(git status --porcelain --untracked-files=all)"
python3 -B tests/runtime.py -v
after="$(git status --porcelain --untracked-files=all)"
if [[ "$after" != "$before" ]]; then
  echo "error: tests/runtime.py changed the working tree:" >&2
  diff <(printf '%s\n' "$before") <(printf '%s\n' "$after") >&2 || true
  exit 1
fi
