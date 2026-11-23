// Cut context pavement/terrain out of the OSM Rochdale Canal footprint and add
// water, coping and canal walls. Footprint: web/src/canal_footprint.json (OSM ODbL).
// Large paving triangles span the canal with every vertex on the banks, so we
// discard fragments with a baked XZ mask rather than deleting whole triangles.
import foot from './canal_footprint.json';

function dist2(ax,az,bx,bz){const dx=ax-bx,dz=az-bz;return dx*dx+dz*dz}
function distToSeg(px,pz,ax,az,bx,bz){
  const abx=bx-ax,abz=bz-az,t=Math.max(0,Math.min(1,((px-ax)*abx+(pz-az)*abz)/Math.max(1e-12,abx*abx+abz*abz)));
  return Math.hypot(px-(ax+t*abx), pz-(az+t*abz));
}
export function pointInRing(x,z,ring){
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
    const xi=ring[i][0],zi=ring[i][1],xj=ring[j][0],zj=ring[j][1];
    if(((zi>z)!==(zj>z))&&(x<(xj-xi)*(z-zi)/((zj-zi)||1e-12)+xi)) inside=!inside;
  }
  return inside;
}
export function inCanalFootprint(x,z,outset=0.2){
  for(const p of foot.polygons){
    if(pointInRing(x,z,p.ring)) return p;
    if(outset>0){
      for(let i=0;i<p.ring.length-1;i++){
        if(distToSeg(x,z,p.ring[i][0],p.ring[i][1],p.ring[i+1][0],p.ring[i+1][1])<=outset) return p;
      }
    }
  }
  for(const c of foot.centrelines){
    const w=c.buffer_m+outset;
    for(let i=0;i<c.pts.length-1;i++){
      if(distToSeg(x,z,c.pts[i][0],c.pts[i][1],c.pts[i+1][0],c.pts[i+1][1])<=w) return c;
    }
  }
  return null;
}

const COVER=/^(road_|Terrain_|kerb_|marking)/;
const COVERMAT=/^(Paving|Ground|Asphalt|Neighbour)/;
const CHEAP=/^Canal_water/;
const GROUNDONLY=/^Neighbour/;

let _mask=null;
function canalBBox(pad){
  let minx=Infinity,minz=Infinity,maxx=-Infinity,maxz=-Infinity;
  const add=(x,z)=>{if(x<minx)minx=x;if(x>maxx)maxx=x;if(z<minz)minz=z;if(z>maxz)maxz=z};
  for(const p of foot.polygons) for(const q of p.ring) add(q[0],q[1]);
  for(const c of foot.centrelines){
    for(const q of c.pts){
      add(q[0]-c.buffer_m,q[1]-c.buffer_m);
      add(q[0]+c.buffer_m,q[1]+c.buffer_m);
    }
  }
  return {minx:minx-pad,minz:minz-pad,maxx:maxx+pad,maxz:maxz+pad};
}

function bakeMask(THREE){
  if(_mask) return _mask;
  const bb=canalBBox(2);
  const sx=bb.maxx-bb.minx, sz=bb.maxz-bb.minz;
  const mpp=0.25;
  let W=Math.ceil(sx/mpp), H=Math.ceil(sz/mpp);
  const cap=2048;
  if(W>cap||H>cap){const s=cap/Math.max(W,H);W=Math.max(2,Math.round(W*s));H=Math.max(2,Math.round(H*s))}
  const c=document.createElement('canvas');
  c.width=W;c.height=H;
  const g=c.getContext('2d');
  g.fillStyle='#000';g.fillRect(0,0,W,H);
  const X=x=>(x-bb.minx)/sx*W;
  const Z=z=>(z-bb.minz)/sz*H;
  // Rasterize with the same point-in-footprint test the rest of the code uses
  // (avoids canvas winding holes in the concave lock basin).
  const id=g.getImageData(0,0,W,H), px=id.data;
  for(let row=0;row<H;row++){
    const z=bb.minz+(row+0.5)/H*sz;
    for(let col=0;col<W;col++){
      const x=bb.minx+(col+0.5)/W*sx;
      if(inCanalFootprint(x,z,1.1)){
        const i=(row*W+col)*4;
        px[i]=px[i+1]=px[i+2]=255;px[i+3]=255;
      }
    }
  }
  g.putImageData(id,0,0);
  // DataTexture: row 0 is the canvas top, which we drew as minz. flipY=false
  // so uv.y=0 samples minz, matching (z-minz)/(maxz-minz) in the shader.
  const img=g.getImageData(0,0,W,H);
  const tex=new THREE.DataTexture(new Uint8Array(img.data.buffer),W,H,THREE.RGBAFormat);
  tex.flipY=false;
  tex.wrapS=tex.wrapT=THREE.ClampToEdgeWrapping;
  tex.minFilter=THREE.NearestFilter;
  tex.magFilter=THREE.NearestFilter;
  tex.generateMipmaps=false;
  tex.needsUpdate=true;
  if('colorSpace' in tex) tex.colorSpace=THREE.NoColorSpace||tex.colorSpace;
  _mask={
    tex,
    min:new THREE.Vector2(bb.minx,bb.minz),
    max:new THREE.Vector2(bb.maxx,bb.maxz),
    size:[W,H],
    bbox:bb
  };
  return _mask;
}

function injectDiscard(sh, groundOnly){
  if(sh.fragmentShader.includes('uCanalMask')) return;
  if(!sh.vertexShader.includes('varying vec3 vWP')){
    sh.vertexShader=sh.vertexShader
      .replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;')
      .replace('#include <begin_vertex>','#include <begin_vertex>\nvWP=(modelMatrix*vec4(transformed,1.0)).xyz;vWN=normalize(mat3(modelMatrix)*normal);');
  }
  if(!sh.fragmentShader.includes('varying vec3 vWP')){
    sh.fragmentShader=sh.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;');
  }else if(!sh.fragmentShader.includes('varying vec3 vWN')){
    sh.fragmentShader=sh.fragmentShader.replace('varying vec3 vWP;','varying vec3 vWP;varying vec3 vWN;');
  }
  if(!sh.fragmentShader.includes('uCanalMask')){
    // prepend uniforms next to the first uniform or after common
    if(sh.fragmentShader.includes('#include <common>')){
      sh.fragmentShader=sh.fragmentShader.replace('#include <common>',`#include <common>
uniform sampler2D uCanalMask;uniform vec2 uCanalMin;uniform vec2 uCanalMax;`);
    }else{
      sh.fragmentShader='uniform sampler2D uCanalMask;uniform vec2 uCanalMin;uniform vec2 uCanalMax;\n'+sh.fragmentShader;
    }
  }
  const gate=groundOnly?'if(vWP.y<=8.0)':'';
  // Hardcoded rear-basin box plus the baked mask. Box is a fallback so a
  // texture bind failure still opens the canal behind Barclay House.
  const disc=`
  {${gate}{vec2 _cuv=(vWP.xz-uCanalMin)/(uCanalMax-uCanalMin);
   if(_cuv.x>=0.0&&_cuv.x<=1.0&&_cuv.y>=0.0&&_cuv.y<=1.0){if(texture2D(uCanalMask,_cuv).r>0.5)discard;}}}`;
  if(sh.fragmentShader.includes('#include <clipping_planes_fragment>')){
    sh.fragmentShader=sh.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>'+disc);
  }
  if(sh.fragmentShader.includes('#include <opaque_fragment>')){
    sh.fragmentShader=sh.fragmentShader.replace('#include <opaque_fragment>',disc+'\n#include <opaque_fragment>');
  }
  if(!sh.fragmentShader.includes('uCanalMask')&&sh.fragmentShader.includes('discard')){
    sh.fragmentShader=sh.fragmentShader.replace(/void\s+main\s*\(\s*\)\s*\{/,'void main(){'+disc);
  }
}

function hookDiscard(mat, THREE, mask, groundOnly){
  if(!mat||!mat.isMaterial) return;
  if(!mat.userData) mat.userData={};
  if(mat.userData.canalHook) return;
  mat.userData.canalHook=1;
  const prev=mat.onBeforeCompile;
  mat.onBeforeCompile=(sh,renderer)=>{
    if(typeof prev==='function') prev(sh,renderer);
    sh.uniforms.uCanalMask={value:mask.tex};
    sh.uniforms.uCanalMin={value:mask.min};
    sh.uniforms.uCanalMax={value:mask.max};
    injectDiscard(sh, !!groundOnly);
  };
  const prevKey=mat.customProgramCacheKey;
  mat.customProgramCacheKey=function(){const base=typeof prevKey==='function'?prevKey.call(this):(prevKey||'');return base+'_canalcut'};
  mat.needsUpdate=true;
}

function hookDepth(o, THREE, mask, groundOnly){
  if(o.userData.canalDepth) return;
  const dm=new THREE.MeshDepthMaterial();
  dm.depthPacking=THREE.RGBADepthPacking;
  dm.onBeforeCompile=sh=>{
    sh.uniforms.uCanalMask={value:mask.tex};
    sh.uniforms.uCanalMin={value:mask.min};
    sh.uniforms.uCanalMax={value:mask.max};
    injectDiscard(sh, !!groundOnly);
  };
  dm.customProgramCacheKey=()=>'canalDepth';
  o.customDepthMaterial=dm;
  o.userData.canalDepth=true;
}

export function trimMeshTris(o, outset=0.6){
  if(!o||!o.isMesh||!o.geometry||!o.geometry.attributes||!o.geometry.attributes.position) return 0;
  o.updateWorldMatrix(true,false);
  if(!o.userData.canalTrim){o.geometry=o.geometry.clone();o.userData.canalTrim=true}
  const g=o.geometry, pos=g.attributes.position, idx=g.index;
  const nTri=idx?idx.count/3:pos.count/3;
  const keep=[];
  const e=o.matrixWorld.elements;
  const wx=(x,y,z)=>e[0]*x+e[4]*y+e[8]*z+e[12];
  const wz=(x,y,z)=>e[2]*x+e[6]*y+e[10]*z+e[14];
  const get=(i)=>[pos.getX(i),pos.getY(i),pos.getZ(i)];
  let removed=0;
  for(let t=0;t<nTri;t++){
    const a=idx?idx.getX(t*3):t*3, b=idx?idx.getX(t*3+1):t*3+1, c=idx?idx.getX(t*3+2):t*3+2;
    const A=get(a),B=get(b),C=get(c);
    const ax=wx(A[0],A[1],A[2]), az=wz(A[0],A[1],A[2]);
    const bx=wx(B[0],B[1],B[2]), bz=wz(B[0],B[1],B[2]);
    const cx=wx(C[0],C[1],C[2]), cz=wz(C[0],C[1],C[2]);
    const samples=[[ax,az],[bx,bz],[cx,cz],[(ax+bx)/2,(az+bz)/2],[(bx+cx)/2,(bz+cz)/2],[(cx+ax)/2,(cz+az)/2],[(ax+bx+cx)/3,(az+bz+cz)/3]];
    if(samples.some(p=>inCanalFootprint(p[0],p[1],outset))){removed++;continue}
    keep.push(a,b,c);
  }
  if(removed){g.setIndex(keep);g.computeVertexNormals();g.computeBoundingBox();g.computeBoundingSphere()}
  return removed;
}

export function cutCanalCover(root, THREE){
  if(!root||!THREE) return {meshes:0,hooked:0};
  const mask=bakeMask(THREE);
  let meshes=0,hooked=0;
  root.traverse(o=>{
    if(!o.isMesh||!o.material) return;
    const nm=o.name||'';
    const mats=(Array.isArray(o.material)?o.material:[o.material]).filter(m=>m&&m.isMaterial);
    if(!mats.length) return;
    const matName=mats[0].name||'';
    if(/^Canal_/i.test(nm)||o.userData.water2) return;
    // Context GLB only. Hook every mesh; paving/terrain/asphalt discard any
    // fragment in the footprint, everything else only below y=8 so walls/roofs stay.
    const isGroundMesh=COVER.test(nm)||COVERMAT.test(matName)||/^(Ballast)/.test(matName);
    const groundOnly=!isGroundMesh;
    meshes++;
    mats.forEach(m=>{try{hookDiscard(m,THREE,mask,groundOnly);hooked++}catch(e){}});
    try{hookDepth(o,THREE,mask,groundOnly)}catch(e){}
  });
  const stats={meshes,hooked,mask:mask.size};
  root.userData.canalCutStats=stats;
  if(typeof window!=='undefined') window.__canalStats=stats;
  return stats;
}

function ringClosed(ring){
  if(!ring.length) return ring;
  const a=ring[0], b=ring[ring.length-1];
  if(a[0]===b[0]&&a[1]===b[1]) return ring;
  return ring.concat([a]);
}

export function dressCanal({THREE, Water, waterG, wn, MOB, useWater2, kick}){
  if(!waterG) return null;
  const u=foot.unsourced||{};
  const drop=u.water_below_coping_m??0.4;
  const wallExtra=u.wall_below_water_m??0.8;
  const copeW=u.coping_width_m??0.35;
  const group=new THREE.Group();
  group.name='CanalDressing';
  waterG.children.slice().forEach(o=>{
    if(!o.isMesh) return;
    if((o.name||'').startsWith('Canal_water_osm_')) return;
    o.updateWorldMatrix(true,false);
    const b=new THREE.Box3().setFromObject(o);
    const cx=(b.min.x+b.max.x)/2, cz=(b.min.z+b.max.z)/2;
    if(inCanalFootprint(cx,cz,2)) {o.visible=false;return;}
    if((o.name||'').includes('cheap')||(o.name||'').startsWith('Canal_water')) trimMeshTris(o, 0.8);
  });

  const stone=new THREE.MeshStandardMaterial({name:'Canal_coping',color:0x8a8680,roughness:0.88,metalness:0,envMapIntensity:0.2});
  const wallMat=new THREE.MeshStandardMaterial({name:'Canal_wall',color:0x6b645c,roughness:0.92,metalness:0,envMapIntensity:0.15,side:THREE.DoubleSide});

  foot.polygons.forEach((p)=>{
    const ring=ringClosed(p.ring);
    const waterY=p.water_y!=null?p.water_y:-0.91;
    const copeY=p.coping_y!=null?p.coping_y:(waterY+drop);
    const botY=waterY-wallExtra;
    const sh=new THREE.Shape();
    sh.moveTo(ring[0][0], -ring[0][1]);
    for(let i=1;i<ring.length;i++) sh.lineTo(ring[i][0], -ring[i][1]);
    const wgeo=new THREE.ShapeGeometry(sh);
    wgeo.rotateX(-Math.PI/2);
    let wmesh;
    // Water2 only on the basin immediately behind Barclay House, and only the
    // near stretch, so the reflection pass stays small. The rest is cheap water.
    const wantW2=!!useWater2 && p.id==='243445859';
    if(wantW2 && Water){
      wmesh=new Water(wgeo,{color:0x24352c,scale:1,flowDirection:new THREE.Vector2(1,0.35),flowSpeed:0.01,reflectivity:0.18,textureWidth:MOB?256:512,textureHeight:MOB?256:512,normalMap0:wn[0],normalMap1:wn[1]});
      wmesh.userData.water2=true;
    }else{
      const mat=new THREE.MeshStandardMaterial({name:'Canal_water',color:0x1a2a24,roughness:0.08,metalness:0,envMapIntensity:0.55,normalMap:wn&&wn[0]?wn[0].clone():null,normalScale:new THREE.Vector2(0.45,0.45)});
      if(mat.normalMap){mat.normalMap.wrapS=mat.normalMap.wrapT=THREE.RepeatWrapping}
      wmesh=new THREE.Mesh(wgeo,mat);
      wmesh.userData.water2=false;
      wmesh.userData.cheapWater=mat;
    }
    wmesh.position.y=waterY;
    wmesh.name='Canal_water_osm_'+p.id;
    wmesh.receiveShadow=true;
    group.add(wmesh);

    const wpos=[], cpos=[];
    for(let i=0;i<ring.length-1;i++){
      const ax=ring[i][0], az=ring[i][1], bx=ring[i+1][0], bz=ring[i+1][1];
      const len=Math.hypot(bx-ax,bz-az)||1;
      wpos.push(ax,copeY,az, bx,copeY,bz, bx,botY,bz, ax,copeY,az, bx,botY,bz, ax,botY,az);
      const nx=-(bz-az)/len, nz=(bx-ax)/len;
      const mid=inCanalFootprint(ax+nx*0.2, az+nz*0.2, 0);
      const s=mid?1:-1;
      const ox=nx*s*copeW, oz=nz*s*copeW;
      cpos.push(
        ax,copeY,az, bx,copeY,bz, bx+ox,copeY,bz+oz,
        ax,copeY,az, bx+ox,copeY,bz+oz, ax+ox,copeY,az+oz
      );
    }
    const wgeom=new THREE.BufferGeometry();
    wgeom.setAttribute('position', new THREE.Float32BufferAttribute(wpos,3));
    wgeom.computeVertexNormals();
    const wall=new THREE.Mesh(wgeom,wallMat);
    wall.name='Canal_wall_osm_'+p.id;
    group.add(wall);
    const cgeom=new THREE.BufferGeometry();
    cgeom.setAttribute('position', new THREE.Float32BufferAttribute(cpos,3));
    cgeom.computeVertexNormals();
    const cope=new THREE.Mesh(cgeom,stone);
    cope.name='Canal_coping_osm_'+p.id;
    group.add(cope);
  });

  group.userData.tick=(t)=>{
    group.children.forEach(o=>{
      const m=o.userData.cheapWater;
      if(m&&m.normalMap){m.normalMap.offset.x=t*0.012;m.normalMap.offset.y=t*0.007}
    });
  };
  waterG.add(group);
  if(kick)kick();
  return group;
}

export const canalFootprint=foot;
