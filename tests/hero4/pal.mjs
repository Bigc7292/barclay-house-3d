import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import fs from 'fs';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc=await io.read(process.argv[2]);
for(const t of doc.getRoot().listTextures()){ if(/Palette/.test(t.getName())) fs.writeFileSync('/tmp/'+t.getName()+'.webp',t.getImage()); }
for(const m of doc.getRoot().listMeshes()) for(const p of m.listPrimitives()){
 const mat=p.getMaterial(); const uv=p.getAttribute('TEXCOORD_0'); const n=uv.getCount(); const cnt={};
 for(let i=0;i<n;i++){const u=uv.getElement(i,[]); const k=Math.floor(u[0]*32)+','+Math.floor(u[1]*4); cnt[k]=(cnt[k]||0)+1;}
 console.log(m.getName(),mat.getName(),JSON.stringify(mat.getBaseColorFactor()),mat.getRoughnessFactor(),mat.getMetallicFactor(), /Palette/.test(mat.getName())?JSON.stringify(cnt):'');
}
