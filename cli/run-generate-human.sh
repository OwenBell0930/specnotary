#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -z "${1:-}" ]]; then
  echo "Usage: ./cli/run-generate-human.sh <machine-spec.yaml|json> [out.md] [--allow-invalid]"
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required to generate human view."
  echo "Or use Skill degraded drafting. Node generator is Deferred."
  exit 3
fi

echo "specnotary generate-human: runtime=python"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m specnotary.generate_human "$@"
