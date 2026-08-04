#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

function load(file) {
  const text = fs.readFileSync(file, "utf8");
  const ext = path.extname(file).toLowerCase();
  if (ext === ".json") return JSON.parse(text);
  if (ext === ".yaml" || ext === ".yml") {
    let yaml;
    try {
      yaml = require("yaml");
    } catch (e) {
      console.log("FAIL: install deps: cd cli/node && npm i");
      process.exit(4);
    }
    return yaml.parse(text);
  }
  console.log(`FAIL: unsupported suffix ${ext}`);
  process.exit(2);
}

function langText(node, lang) {
  if (node && typeof node === "object" && !Array.isArray(node)) {
    return String(node[lang] || node.zh || node.en || "");
  }
  return node == null ? "" : String(node);
}

function validate(data, project) {
  const errors = [];
  if (!data || typeof data !== "object") return ["root must be an object"];
  for (const key of ["spec_version", "id", "title", "status", "behaviors", "acceptance"]) {
    if (!(key in data)) errors.push(`missing required field: ${key}`);
  }
  if (!Array.isArray(data.behaviors) || data.behaviors.length < 1) errors.push("behaviors must have at least 1 item");
  if (!Array.isArray(data.acceptance) || data.acceptance.length < 1) errors.push("acceptance must have at least 1 item");
  if (data.status === "ready" && Array.isArray(data.open_questions) && data.open_questions.length > 0) {
    errors.push("status=ready but open_questions is not empty");
  }
  if (data.status === "ready") {
    if (!data.actors || !data.actors.length) errors.push("status=ready requires actors");
    if (!data.defaults) errors.push("status=ready requires defaults");
  }
  const weight = (project && project.object_ai_weight) || "medium";
  const obj = data.object_ai || {};
  if (weight === "high") {
    if (!obj.enabled) errors.push("object_ai_weight=high requires object_ai.enabled=true");
    for (const key of ["tools_boundary", "failure_fallback", "human_takeover_when"]) {
      if (!obj[key] || (Array.isArray(obj[key]) && !obj[key].length)) {
        errors.push(`object_ai_weight=high requires object_ai.${key}`);
      }
    }
  }
  return errors;
}

function loadProject(root) {
  const yamlPath = path.join(root, "project.yaml");
  const example = path.join(root, "project.example.yaml");
  const file = fs.existsSync(yamlPath) ? yamlPath : fs.existsSync(example) ? example : null;
  if (!file) return {};
  try {
    const yaml = require("yaml");
    return yaml.parse(fs.readFileSync(file, "utf8")) || {};
  } catch (e) {
    return {};
  }
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
  const root = path.resolve(__dirname, "../..");
  const data = load(file);
  let project = loadProject(root);
  if (data.project_hint && typeof data.project_hint === "object") {
    project = { ...project, ...data.project_hint };
  }
  const errors = validate(data, project);
  console.log("gate_mode: hard");
  console.log("runtime: node");
  console.log(`file: ${file}`);
  if (project.object_ai_weight) console.log(`object_ai_weight: ${project.object_ai_weight}`);
  if (errors.length) {
    console.log("RESULT: FAIL");
    for (const e of errors) console.log(`- ${e}`);
    process.exit(1);
  }
  console.log("RESULT: PASS");
}

main();
