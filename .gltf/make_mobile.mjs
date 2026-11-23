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
// Trick #16: tag Floor_*/Door_* (and per-floor groups) BEFORE flatten, then join
// only within a group. Never join across Floor_* slabs or Door_* leaves/frames
// of different doors. Mobile may still join Facade/Window pieces on one floor.
function parentNode(n){
  return n.listParents().find(p=>p.propertyType==='Node') || null;
}
function floorFromName(s){
  const m=/(?:Floor|Window|Facade|Cornice|Parapet)_?(0[0-5])/.exec(s||'');
  return m ? m[1] : null;
}
function tagJoinGroups(document){
  const visit=(node)=>{
    const name=node.getName()||'';
    let group, protect=false;
    if(/^Floor_/.test(name)){ group='protect:'+name; protect=true; }
    else if(/^Door_/.test(name) && /_leaf$/.test(name)){ group='protect:'+name; protect=true; }
    else if(/^Door_/.test(name)){ group='door:'+name.replace(/_frame(_.*)?$/ ,'_frame'); }
    else {
      let fl=floorFromName(name);
      let p=parentNode(node);
      while(!fl && p){ fl=floorFromName(p.getName()||''); p=parentNode(p); }
      group='floor:'+(fl||'Building');
    }
    const ex=Object.assign({}, node.getExtras()||{}, {joinGroup:group, joinProtect:protect, origName:name});
    node.setExtras(ex);
    for(const ch of node.listChildren()) visit(ch);
  };
  for(const sc of document.getRoot().listScenes()) for(const n of sc.listChildren()) visit(n);
}
tagJoinGroups(doc);
const steps=[dedup(),flatten()];
await doc.transform(...steps);
// refresh groups after flatten (extras/names preserved)
const groupSet=new Set();
for(const n of doc.getRoot().listNodes()){
  if(!n.getMesh()) continue;
  const ex=n.getExtras()||{};
  if(ex.joinProtect) continue;
  groupSet.add(ex.joinGroup || 'floor:Building');
}
for(const g of groupSet){
  await doc.transform(join({
    keepNamed:false,
    cleanup:false,
    filter:(node)=>{
      const ex=node.getExtras()||{};
      if(ex.joinProtect) return false;
      return (ex.joinGroup || 'floor:Building')===g;
    }
  }));
}
// restore protected / joined names (flatten+join can leave blanks)
for(const n of doc.getRoot().listNodes()){
  const ex=n.getExtras()||{};
  if(ex.origName && (ex.joinProtect || !n.getName())) n.setName(ex.origName);
}
const post=[weld()];
if(ratio<1) post.push(simplify({simplifier:MeshoptSimplifier,ratio,error:0.01,lockBorder:true}));
post.push(prune(), textureCompress({encoder:sharp,targetFormat:'jpeg',resize:[tex,tex],quality:82}));
await doc.transform(...post);
// normal maps must stay lossless-ish? jpeg fine for compatibility
await io.write(out,doc);
let dc=0; for(const m of root.listMeshes()) dc+=m.listPrimitives().length*Math.max(1,m.listParents().filter(p=>p.propertyType==='Node').length);
console.log(out,'meshes',root.listMeshes().length,'drawcalls~',dc,'materials',root.listMaterials().length,'textures',root.listTextures().length);

function calcNormals(doc,p){const pos=p.getAttribute('POSITION').getArray(),ix=p.getIndices().getArray();const n=new Float32Array(pos.length);
for(let t=0;t<ix.length;t+=3){const a=ix[t]*3,b=ix[t+1]*3,c=ix[t+2]*3;const ux=pos[b]-pos[a],uy=pos[b+1]-pos[a+1],uz=pos[b+2]-pos[a+2],vx=pos[c]-pos[a],vy=pos[c+1]-pos[a+1],vz=pos[c+2]-pos[a+2];
const nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;for(const k of[a,b,c]){n[k]+=nx;n[k+1]+=ny;n[k+2]+=nz;}}
for(let i=0;i<n.length;i+=3){const l=Math.hypot(n[i],n[i+1],n[i+2])||1;n[i]/=l;n[i+1]/=l;n[i+2]/=l;}
p.setAttribute('NORMAL',doc.createAccessor().setType('VEC3').setArray(n).setBuffer(doc.getRoot().listBuffers()[0]));}
