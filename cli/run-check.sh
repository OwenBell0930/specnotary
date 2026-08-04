#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"
OUT="${2:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./cli/run-check.sh <machine-spec.yaml|json>"
  exit 2
fi

runtime="${SPEC_KIT_RUNTIME:-}"
if [[ -z "$runtime" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    runtime=python
  elif command -v node >/dev/null 2>&1; then
    runtime=node
  else
    echo "ERROR: Neither python3 nor node found."
    echo "Install a runtime for hard gate, or use skills/ (degraded). See docs/gate-modes.md"
    exit 3
  fi
fi

echo "spec-kit: using runtime=$runtime"
case "$runtime" in
  python) exec python3 "$ROOT/cli/python/check.py" "$TARGET" ;;
  node) exec node "$ROOT/cli/node/check.js" "$TARGET" ;;
  *) echo "ERROR: SPEC_KIT_RUNTIME must be python or node"; exit 2 ;;
esac
