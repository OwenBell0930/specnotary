#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"
OUT="${2:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./cli/run-report.sh <machine-spec.yaml|json> [out.md]"
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required for report."
  exit 3
fi

echo "spec-kit report: runtime=python"
if [[ -n "$OUT" ]]; then
  exec python3 "$ROOT/cli/python/report.py" "$TARGET" "$OUT"
else
  exec python3 "$ROOT/cli/python/report.py" "$TARGET"
fi
