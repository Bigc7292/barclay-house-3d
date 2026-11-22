import {NodeIO} from '@gltf-transform/core';import {ALL_EXTENSIONS,EXTMeshoptCompression} from '@gltf-transform/extensions';import {MeshoptDecoder} from 'meshoptimizer';
import {dequantize} from '@gltf-transform/functions';
await MeshoptDecoder.ready;const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const [i,o]=process.argv.slice(2);const d=await io.read(i);
for(const e of d.getRoot().listExtensionsUsed())if(e.extensionName==='EXT_meshopt_compression')e.dispose();
await d.transform(dequantize());
for(const e of d.getRoot().listExtensionsUsed())if(e.extensionName==='KHR_mesh_quantization')e.dispose();
await io.write(o,d);
const out=[];for(const n of d.getRoot().listNodes()){out.push([n.getName(),n.getTranslation().map(v=>+v.toFixed(3)).join(','),n.getRotation().map(v=>+v.toFixed(3)).join(','),n.getMesh()?n.getMesh().getName():'-',n.listChildren().length].join(' | '))}
console.log(out.join('\n'));
