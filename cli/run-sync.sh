#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -z "${1:-}" ]]; then
  echo "Usage: ./cli/run-sync.sh <machine-spec.yaml|json>"
  echo "Regenerates human view + refreshes prototype hash, then re-checks."
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required for sync."
  exit 3
fi

echo "specnotary sync: runtime=python"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m specnotary.sync "$@"
