#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"
HUMAN="${2:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./cli/run-check.sh <machine-spec.yaml|json> [human.md]"
  exit 2
fi

runtime="${SPEC_KIT_RUNTIME:-}"
if [[ -z "$runtime" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    runtime=python
  else
    echo "ERROR: python3 required for hard gate."
    echo "Install Python, or use skills/ (degraded). See docs/gate-modes.md"
    echo "Node CLI is Deferred — not an equivalent hard gate."
    exit 3
  fi
fi

echo "spec-kit: using runtime=$runtime"
case "$runtime" in
  python)
    if [[ -n "$HUMAN" ]]; then
      exec python3 "$ROOT/cli/python/check.py" "$TARGET" "$HUMAN"
    else
      exec python3 "$ROOT/cli/python/check.py" "$TARGET"
    fi
    ;;
  node)
    echo "WARN: Node CLI is Deferred — rules may lag behind Python. Prefer python3."
    exec node "$ROOT/cli/node/check.js" "$TARGET"
    ;;
  *) echo "ERROR: SPEC_KIT_RUNTIME must be python (preferred) or node (deferred)"; exit 2 ;;
esac
