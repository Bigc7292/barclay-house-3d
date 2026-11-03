import fs from 'fs'; import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS); const d=await io.read(process.argv[2]); const r=d.getRoot();
let dc=0,inst=0,floors=0,floorInst=0; for(const n of r.listNodes()){const m=n.getMesh(); if(/^Floor_/.test(n.getName()))floors++; if(!m)continue; const ext=n.getExtension('EXT_mesh_gpu_instancing'); if(ext){inst++; if(/^Floor_/.test(n.getName()))floorInst++;} dc+=m.listPrimitives().length;}
const exts=r.listExtensionsUsed().map(e=>e.extensionName);
console.log(JSON.stringify({f:process.argv[2],MB:+(fs.statSync(process.argv[2]).size/1048576).toFixed(2),drawcalls:dc,instancedNodes:inst,floors,floorInst,exts}));
