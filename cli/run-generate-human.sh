#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"
OUT="${2:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./cli/run-generate-human.sh <machine-spec.yaml|json> [out.md]"
  exit 2
fi

runtime="${SPEC_KIT_RUNTIME:-}"
if [[ -z "$runtime" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    runtime=python
  elif command -v node >/dev/null 2>&1; then
    runtime=node
  else
    echo "ERROR: No runtime. Use Skill degraded mode to draft human view."
    exit 3
  fi
fi

echo "spec-kit generate-human: runtime=$runtime"
case "$runtime" in
  python)
    if [[ -n "$OUT" ]]; then
      exec python3 "$ROOT/cli/python/generate_human.py" "$TARGET" "$OUT"
    else
      exec python3 "$ROOT/cli/python/generate_human.py" "$TARGET"
    fi
    ;;
  node)
    if [[ -n "$OUT" ]]; then
      exec node "$ROOT/cli/node/generate_human.js" "$TARGET" "$OUT"
    else
      exec node "$ROOT/cli/node/generate_human.js" "$TARGET"
    fi
    ;;
  *) echo "ERROR: SPEC_KIT_RUNTIME must be python or node"; exit 2 ;;
esac
