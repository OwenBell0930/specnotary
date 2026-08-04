#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

function load(file) {
  const text = fs.readFileSync(file, "utf8");
  const ext = path.extname(file).toLowerCase();
  if (ext === ".json") return JSON.parse(text);
  const yaml = require("yaml");
  return yaml.parse(text);
}

function langText(node, lang) {
  if (node && typeof node === "object" && !Array.isArray(node)) {
    return String(node[lang] || node.zh || node.en || "");
  }
  return node == null ? "" : String(node);
}

function render(data, source) {
  const lines = [];
  lines.push(`<!-- generated_from: ${source} -->`);
  lines.push(`<!-- gate_mode: hard -->`);
  lines.push("");
  lines.push(`# ${langText(data.title, "zh")}`);
  const en = langText(data.title, "en");
  if (en) lines.push(`# ${en}`);
  lines.push("");
  lines.push(`- **ID:** \`${data.id}\``);
  lines.push(`- **Status:** \`${data.status}\``);
  lines.push("");
  lines.push("## Scope / 范围");
  lines.push("");
  lines.push("### In scope / 范围内");
  for (const item of data.in_scope || []) {
    lines.push(`- ${langText(item, "zh")} / ${langText(item, "en")}`);
  }
  lines.push("");
  lines.push("### Out of scope / 范围外");
  for (const item of data.out_of_scope || []) {
    lines.push(`- ${langText(item, "zh")} / ${langText(item, "en")}`);
  }
  lines.push("");
  lines.push("## Behaviors / 行为");
  for (const b of data.behaviors || []) {
    lines.push(`### \`${b.id}\` ${langText(b.name, "zh")}`);
    lines.push(`- **Given:** ${langText(b.given, "zh")}`);
    lines.push(`- **When:** ${langText(b.when, "zh")}`);
    lines.push(`- **Then:** ${langText(b.then, "zh")}`);
    lines.push("");
  }
  lines.push("## Acceptance / 验收");
  for (const a of data.acceptance || []) {
    lines.push(`- \`${a.id}\`: ${langText(a, "zh")}`);
  }
  lines.push("");
  return lines.join("\n");
}

function main() {
  const file = process.argv[2];
  const out = process.argv[3] || file.replace(/\.(ya?ml|json)$/i, ".human.md");
  if (!file) {
    console.log("Usage: generate_human.js <machine-spec> [out.md]");
    process.exit(2);
  }
  try {
    require("yaml");
  } catch (e) {
    console.log("FAIL: cd cli/node && npm i");
    process.exit(4);
  }
  const data = load(file);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, render(data, file), "utf8");
  console.log(`wrote: ${out}`);
}

main();
