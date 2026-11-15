// Trick #16: required parts_plan.json node names present in a hero GLB, 0 stray *.001.
// Usage: node .gltf/check_parts.mjs out/barclay_hero.glb parts_plan.json
import fs from 'fs';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';

const [glbPath, planPath] = process.argv.slice(2);
if (!glbPath || !planPath) {
  console.error('usage: node check_parts.mjs <hero.glb> <parts_plan.json>');
  process.exit(2);
}
const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
const required = plan.required_in_glb || [];
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(glbPath);
const names = [];
for (const n of doc.getRoot().listNodes()) names.push(n.getName() || '');
const have = new Set(names.filter(Boolean));
const missing = required.filter((n) => !have.has(n));
const stray = names.filter((n) => /\.\d{3}$/.test(n));
const ok = missing.length === 0 && stray.length === 0;
const report = {
  file: glbPath,
  check: 'parts_plan_nodes',
  required: required.length,
  present: required.length - missing.length,
  missing,
  stray_dot001: stray.slice(0, 20),
  stray_count: stray.length,
  node_count: names.length,
  ok,
};
console.log(JSON.stringify(report));
process.exit(ok ? 0 : 1);
