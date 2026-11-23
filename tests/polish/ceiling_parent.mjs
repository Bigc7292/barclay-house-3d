// lane/polish r10: gltf-transform optimize moves the Ceiling mesh onto an unnamed child node; put it back on the "Ceiling"
// node so the viewer's ceiling toggle (first mesh named ^Ceiling) also hides its children (downlights, window backdrops).
// Usage (run from .gltf/ so modules resolve): node ceiling_parent.mjs in.glb out.glb
import {NodeIO} from '@gltf-transform/core';import {ALL_EXTENSIONS} from '@gltf-transform/extensions';import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
await MeshoptDecoder.ready;await MeshoptEncoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const [i,o]=process.argv.slice(2);const d=await io.read(i);let n=0;
for(const c of d.getRoot().listNodes().filter(x=>/^Ceiling/.test(x.getName())&&!x.getMesh())){
  const k=c.listChildren().find(x=>x.getMesh()&&!x.getName());if(!k)continue;
  const id=k.getTranslation().every(v=>Math.abs(v)<1e-6)&&k.getScale().every(v=>Math.abs(v-1)<1e-6)&&Math.abs(k.getRotation()[3]-1)<1e-6;
  if(!id){console.log('skip (non-identity child)',c.getName());continue}
  c.setMesh(k.getMesh());c.removeChild(k);k.dispose();n++}
await io.write(o,d);console.log('ceiling nodes fixed',n)
