#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./cli/run-check.sh <machine-spec.yaml|json> [human.md] [prototype.manifest.yaml] [--explain]"
  exit 2
fi

runtime="${SPECNOTARY_RUNTIME:-${SPEC_KIT_RUNTIME:-}}"
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

case "$runtime" in
  python)
    echo "specnotary: using runtime=python"
    export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
    exec python3 -m specnotary.check "$@"
    ;;
  node)
    echo "ERROR: Node CLI is Deferred and cannot produce a hard PASS."
    echo "Use python3 (default) or skills/ with gate_mode: degraded."
    exit 3
    ;;
  *) echo "ERROR: SPECNOTARY_RUNTIME must be python"; exit 2 ;;
esac
