import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dedup,flatten,join,weld,prune,textureCompress,simplify,getBounds,resample,instance} from '@gltf-transform/functions';
import {compactPrimitive,simplifyPrimitive,weldPrimitive} from '@gltf-transform/functions';
import {MeshoptSimplifier} from 'meshoptimizer';
import sharp from 'sharp';
const [,,inp,out,texStr,radStr,ratioStr]=process.argv;
const tex=+texStr, rad=+radStr, ratio=+ratioStr;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc=await io.read(inp);
const root=doc.getRoot();
if(rad>0){let n=0;
 for(const node of root.listNodes()){ if(!node.getMesh())continue;
  const b=getBounds(node); const cx=(b.min[0]+b.max[0])/2, cz=(b.min[2]+b.max[2])/2;
  if(Math.hypot(cx,cz)>rad){node.dispose();n++;} }
 console.log('culled nodes beyond',rad,'m:',n);}
await MeshoptSimplifier.ready;
if(rad>0){ for(const node of root.listNodes()){const m=node.getMesh(); if(!m||!/Terrain/i.test(m.getName()))continue;
 const W=node.getWorldMatrix();
 for(const p of m.listPrimitives()){const pos=p.getAttribute('POSITION'),idx=p.getIndices(); const keep=[]; const v=[0,0,0];
  const wp=i=>{pos.getElement(i,v);const x=W[0]*v[0]+W[4]*v[1]+W[8]*v[2]+W[12], z=W[2]*v[0]+W[6]*v[1]+W[10]*v[2]+W[14];return Math.hypot(x,z);};
  const a=idx.getArray(); for(let t=0;t<a.length;t+=3){ if(wp(a[t])<=rad&&wp(a[t+1])<=rad&&wp(a[t+2])<=rad) keep.push(a[t],a[t+1],a[t+2]);}
  idx.setArray(new Uint32Array(keep)); compactPrimitive(p); const N=p.getAttribute('NORMAL'); p.setAttribute('NORMAL',null); N&&N.dispose(); weldPrimitive(p); simplifyPrimitive(p,{simplifier:MeshoptSimplifier,ratio:0.08,error:0.02,lockBorder:false}); calcNormals(doc,p); console.log('terrain tris kept',keep.length/3,'-> after simplify',p.getIndices().getCount()/3,'verts',p.getAttribute('POSITION').getCount());}}}
const steps=[dedup(),flatten(),join({keepNamed:false}),weld()];
if(ratio<1) steps.push(simplify({simplifier:MeshoptSimplifier,ratio,error:0.01,lockBorder:true}));
steps.push(prune(), textureCompress({encoder:sharp,targetFormat:'jpeg',resize:[tex,tex],quality:82}));
await doc.transform(...steps);
// normal maps must stay lossless-ish? jpeg fine for compatibility
await io.write(out,doc);
let dc=0; for(const m of root.listMeshes()) dc+=m.listPrimitives().length*Math.max(1,m.listParents().filter(p=>p.propertyType==='Node').length);
console.log(out,'meshes',root.listMeshes().length,'drawcalls~',dc,'materials',root.listMaterials().length,'textures',root.listTextures().length);

function calcNormals(doc,p){const pos=p.getAttribute('POSITION').getArray(),ix=p.getIndices().getArray();const n=new Float32Array(pos.length);
for(let t=0;t<ix.length;t+=3){const a=ix[t]*3,b=ix[t+1]*3,c=ix[t+2]*3;const ux=pos[b]-pos[a],uy=pos[b+1]-pos[a+1],uz=pos[b+2]-pos[a+2],vx=pos[c]-pos[a],vy=pos[c+1]-pos[a+1],vz=pos[c+2]-pos[a+2];
const nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;for(const k of[a,b,c]){n[k]+=nx;n[k+1]+=ny;n[k+2]+=nz;}}
for(let i=0;i<n.length;i+=3){const l=Math.hypot(n[i],n[i+1],n[i+2])||1;n[i]/=l;n[i+1]/=l;n[i+2]/=l;}
p.setAttribute('NORMAL',doc.createAccessor().setType('VEC3').setArray(n).setBuffer(doc.getRoot().listBuffers()[0]));}
