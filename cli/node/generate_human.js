#!/usr/bin/env node
// Node generator is Deferred by decision (docs/gate-modes.md).
// It must never stamp gate_mode: hard on a human view.
function main() {
  console.log("ERROR: Node generator is Deferred and cannot stamp gate_mode: hard.");
  console.log("Use ./cli/run-generate-human.sh (python3).");
  process.exit(3);
}

main();
