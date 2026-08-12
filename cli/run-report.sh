#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -z "${1:-}" ]]; then
  echo "Usage: ./cli/run-report.sh <machine-spec.yaml|json> [out.md]"
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required for report."
  exit 3
fi

echo "specnotary report: runtime=python"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m specnotary.report "$@"
