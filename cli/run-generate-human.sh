#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"
OUT=""
ALLOW=""

usage() {
  echo "Usage: ./cli/run-generate-human.sh <machine-spec.yaml|json> [out.md] [--allow-invalid]"
}

if [[ -z "$TARGET" ]]; then
  usage
  exit 2
fi

shift || true
for arg in "$@"; do
  if [[ "$arg" == "--allow-invalid" ]]; then
    ALLOW="--allow-invalid"
  elif [[ -z "$OUT" ]]; then
    OUT="$arg"
  else
    usage
    exit 2
  fi
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required to generate human view."
  echo "Or use Skill degraded drafting. Node generator is Deferred."
  exit 3
fi

echo "spec-kit generate-human: runtime=python"
if [[ -n "$OUT" ]]; then
  if [[ -n "$ALLOW" ]]; then
    exec python3 "$ROOT/cli/python/generate_human.py" "$TARGET" "$OUT" "$ALLOW"
  else
    exec python3 "$ROOT/cli/python/generate_human.py" "$TARGET" "$OUT"
  fi
else
  if [[ -n "$ALLOW" ]]; then
    exec python3 "$ROOT/cli/python/generate_human.py" "$TARGET" "$ALLOW"
  else
    exec python3 "$ROOT/cli/python/generate_human.py" "$TARGET"
  fi
fi
