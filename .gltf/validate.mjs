// Usage: node validate.mjs file.glb budgetMB  -> one-line JSON report; exit 1 if errors or over budget
import fs from 'fs'; import v from 'gltf-validator';
import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
const [f, budget] = process.argv.slice(2); const buf = fs.readFileSync(f); const mb = buf.length/1048576;
const r = await v.validateBytes(new Uint8Array(buf), {maxIssues: 50});
let prims=0, tex=0, mats=0;
try { const io = new NodeIO().registerExtensions(ALL_EXTENSIONS); const d = await io.readBinary(new Uint8Array(buf));
  const root=d.getRoot(); for (const m of root.listMeshes()) prims+=m.listPrimitives().length; tex=root.listTextures().length; mats=root.listMaterials().length; } catch(e) {}
const ok = r.issues.numErrors===0 && (!budget || mb < +budget);
console.log(JSON.stringify({file:f, MB:+mb.toFixed(2), budget:budget?+budget:null, errors:r.issues.numErrors, warnings:r.issues.numWarnings, primitives_drawcalls:prims, materials:mats, textures:tex, ok}));
process.exit(ok?0:1);
