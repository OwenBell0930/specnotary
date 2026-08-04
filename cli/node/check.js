#!/usr/bin/env node
/** Minimal hard-gate checker for machine specs (YAML/JSON). */
const fs = require("fs");
const path = require("path");

const REQUIRED_TOP = ["spec_version", "id", "title", "status", "behaviors", "acceptance"];

function load(file) {
  const text = fs.readFileSync(file, "utf8");
  const ext = path.extname(file).toLowerCase();
  if (ext === ".json") return JSON.parse(text);
  if (ext === ".yaml" || ext === ".yml") {
    try {
      const yaml = require("yaml");
      return yaml.parse(text);
    } catch (e) {
      console.log("FAIL: Node package 'yaml' not installed. npm i yaml  OR use JSON  OR degraded Skill mode.");
      process.exit(4);
    }
  }
  console.log(`FAIL: unsupported suffix ${ext}`);
  process.exit(2);
}

function main() {
  const file = process.argv[2];
  if (!file) {
    console.log("Usage: check.js <machine-spec>");
    process.exit(2);
  }
  if (!fs.existsSync(file)) {
    console.log(`FAIL: file not found: ${file}`);
    process.exit(2);
  }
  const data = load(file);
  const errors = [];
  for (const key of REQUIRED_TOP) {
    if (!(key in data)) errors.push(`missing required field: ${key}`);
  }
  if (!Array.isArray(data.behaviors) || data.behaviors.length < 1) {
    errors.push("behaviors must have at least 1 item");
  }
  if (!Array.isArray(data.acceptance) || data.acceptance.length < 1) {
    errors.push("acceptance must have at least 1 item");
  }
  if (data.status === "ready" && Array.isArray(data.open_questions) && data.open_questions.length > 0) {
    errors.push("status=ready but open_questions is not empty");
  }
  console.log("gate_mode: hard");
  console.log("runtime: node");
  console.log(`file: ${file}`);
  if (errors.length) {
    console.log("RESULT: FAIL");
    for (const e of errors) console.log(`- ${e}`);
    process.exit(1);
  }
  console.log("RESULT: PASS");
}

main();
