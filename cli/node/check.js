#!/usr/bin/env node
// Node gate is Deferred by decision (docs/gate-modes.md).
// No shadow rule set lives here: the Python CLI is the only hard gate,
// and this stub refuses rather than drifting behind it.
function main() {
  console.log("gate_mode: deferred");
  console.log("runtime: node");
  console.log("ERROR: Node CLI is Deferred and cannot produce a hard PASS.");
  console.log("Use ./cli/run-check.sh (python3), or skills/ with gate_mode: degraded.");
  process.exit(3);
}

main();
