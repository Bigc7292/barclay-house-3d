// Pre-pass for surroundings-detail mobile LOD: drop sleepers (ballast texture carries it), decimate tree crowns hard.
import {NodeIO} from '@gltf-transform/core'; import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {weld,simplify,prune} from '@gltf-transform/functions'; import {MeshoptSimplifier} from 'meshoptimizer';
const [,,inp,out]=process.argv; const io=new NodeIO().registerExtensions(ALL_EXTENSIONS); const doc=await io.read(inp); await MeshoptSimplifier.ready;
for(const n of doc.getRoot().listNodes()){const m=n.getMesh(); if(!m)continue; const nm=m.getName()||n.getName();
 if(/SURR_rail_sleepers|SURR_OLE/.test(nm)){n.dispose();}}
for(const m of doc.getRoot().listMeshes()) for(const p of m.listPrimitives()){const mt=p.getMaterial(); if(mt&&/S_window_frame/.test(mt.getName())) p.dispose();}
await doc.transform(weld(),prune());
for(const m of doc.getRoot().listMeshes()){ if(!/SURR_trees_crowns/.test(m.getName()))continue;
 for(const p of m.listPrimitives()){const {simplifyPrimitive,weldPrimitive}=await import('@gltf-transform/functions'); weldPrimitive(p); simplifyPrimitive(p,{simplifier:MeshoptSimplifier,ratio:0.06,error:0.2,lockBorder:false});}}
await doc.transform(prune()); await io.write(out,doc);
