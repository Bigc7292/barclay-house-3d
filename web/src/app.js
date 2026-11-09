import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { SSAOPass } from 'three/examples/jsm/postprocessing/SSAOPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { Water } from 'three/examples/jsm/objects/Water2.js'; // x_tricks #10: three r170 Water2 (MIT), bundled locally by esbuild, no CDN
import canals from './canal.json'; // Canal_water triangles from out/barclay_surroundings.glb (.gltf/canal_extract.mjs)
import lamps from './lights.json';
const $=id=>document.getElementById(id), msg=$('msg');
const say=(t,e)=>{msg.textContent=t;msg.className=e?'err':''};
const q0=new URLSearchParams(location.search);
const MOB=q0.get('lq')==='1'||(q0.get('lq')!=='0'&&(/Android|iPhone|iPad|iPod|Mobi|Samsung/i.test(navigator.userAgent)||(navigator.deviceMemory&&navigator.deviceMemory<=4)||(matchMedia('(pointer:coarse)').matches&&Math.min(screen.width,screen.height)<=900)));
window.__mobile=MOB;
const glOK=(()=>{try{const c=document.createElement('canvas');return !!(c.getContext('webgl2')||c.getContext('webgl'))}catch(e){return false}})();
if(!glOK){say('This browser/device has WebGL turned off or unsupported, so the 3D view cannot run. Try Chrome, or enable hardware acceleration.',1);throw new Error('no webgl')}
let R;try{R=new THREE.WebGLRenderer({antialias:!MOB,powerPreference:'high-performance'})}catch(e){say('Could not start 3D (WebGL error: '+e.message+'). Try reloading or another browser.',1);throw e}
R.domElement.style.touchAction='none';
R.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();say('Graphics memory ran out; reloading in low-quality mode…',1);if(!MOB||q0.get('lq')!=='1'){setTimeout(()=>{const u=new URL(location.href);u.searchParams.set('lq','1');location.replace(u)},1200)}else say('Graphics memory ran out even in low-quality mode. Close other tabs/apps and reload.',1)});
const DPR_MAX=Math.min(devicePixelRatio||1,MOB?1.25:1.5);let dpr=DPR_MAX;R.setPixelRatio(dpr);
R.shadowMap.enabled=!MOB;R.shadowMap.type=THREE.PCFSoftShadowMap;R.shadowMap.autoUpdate=false;const reshadow=()=>{R.shadowMap.needsUpdate=true;draw=true};
R.toneMapping=THREE.AgXToneMapping;R.toneMappingExposure=1;R.outputColorSpace=THREE.SRGBColorSpace;$('v').appendChild(R.domElement);
const S=new THREE.Scene(), C=new THREE.PerspectiveCamera(40,1,0.1,2600);
const nf=i=>{C.near=i?0.03:0.1;C.far=i?300:2600;C.updateProjectionMatrix()};
const O=new OrbitControls(C,R.domElement);O.enableDamping=true;O.dampingFactor=0.12;O.minDistance=0.8;O.maxDistance=800;O.zoomToCursor=false;O.zoomSpeed=0.85;O.rotateSpeed=0.6;O.minPolarAngle=0.04;O.maxPolarAngle=Math.PI*0.92;
const sun=new THREE.DirectionalLight(0xffffff,3);sun.castShadow=!MOB;
sun.shadow.mapSize.set(2048,2048);sun.shadow.bias=-0.00015;sun.shadow.normalBias=0.02;sun.shadow.radius=4;
const sc=sun.shadow.camera;sc.near=8;sc.far=420;sc.left=sc.bottom=-50;sc.right=sc.top=50;sc.updateProjectionMatrix();
S.add(sun,sun.target);const hemi=new THREE.HemisphereLight(0xdfe8ff,0x55504a,0.3);S.add(hemi);
const fill=new THREE.DirectionalLight(0xffd2a8,0.9);fill.position.set(1.4,4.2,0.6);fill.target.position.set(0,0.3,0);fill.castShadow=!MOB;fill.visible=false;
fill.shadow.mapSize.set(1024,1024);fill.shadow.radius=4;fill.shadow.bias=-0.00035;fill.shadow.normalBias=0.03;
const fc=fill.shadow.camera;fc.near=0.4;fc.far=9;fc.left=fc.bottom=-5.5;fc.right=fc.top=5.5;S.add(fill,fill.target);
const comp=new EffectComposer(R);
comp.addPass(new RenderPass(S,C));
const ssao=new SSAOPass(S,C,512,512,16);{const f=ssao.setSize.bind(ssao);ssao.setSize=(w,h)=>f(Math.max(1,w>>1),Math.max(1,h>>1))}
ssao.kernelRadius=0.3;ssao.minDistance=0.002;ssao.maxDistance=0.22;
comp.addPass(ssao);
const bloom=new UnrealBloomPass(new THREE.Vector2(512,512),0.12,0.35,0.9);{const f=bloom.setSize.bind(bloom);bloom.setSize=(w,h)=>f(Math.max(1,w>>1),Math.max(1,h>>1))}
comp.addPass(bloom);
comp.addPass(new OutputPass());
const lampG=new THREE.Group();
lamps.map((p,i)=>({i,d:p[0]*p[0]+p[2]*p[2]})).sort((a,b)=>a.d-b.d).slice(0,4).forEach(({i})=>{const p=lamps[i];const l=new THREE.PointLight(0xffc27a,0,22,2);l.position.set(p[0],p[1],p[2]);lampG.add(l)});S.add(lampG);
const L=new GLTFLoader();L.setMeshoptDecoder(MeshoptDecoder);
const ext=new THREE.Group(), intr=new THREE.Group();S.add(ext,intr);intr.visible=false;
function tile(draw,srgb){
 const c=document.createElement('canvas');c.width=c.height=256;const g=c.getContext('2d');draw(g,256);
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=MOB?1:4;
 t.colorSpace=srgb?THREE.SRGBColorSpace:THREE.LinearSRGBColorSpace;return t;
}
function grain(g,n,a){for(let i=0;i<2200;i++){g.fillStyle=`rgba(70,60,40,${a*(0.3+Math.random())})`;g.fillRect(Math.random()*n,Math.random()*n,1+Math.random()*2,1+Math.random()*2)}}
function pbr(o){
 const n=256,h=new Float32Array(n*n),j=o.joint;
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){
  const edge=x<j||y>n-1-j;
  let v=edge?0.04:0.86;
  if(!edge)v+=(Math.sin(x*0.37)+Math.cos(y*0.23))*o.noise;
  h[y*n+x]=v;
 }
 const mk=(srgb,fn)=>{const c=document.createElement('canvas');c.width=c.height=n;const g=c.getContext('2d'),im=g.createImageData(n,n);
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){const q=fn(x,y,h[y*n+x]);const i=(y*n+x)*4;im.data[i]=q[0];im.data[i+1]=q[1];im.data[i+2]=q[2];im.data[i+3]=255}
  g.putImageData(im,0,0);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=MOB?1:8;
  t.colorSpace=srgb?THREE.SRGBColorSpace:THREE.LinearSRGBColorSpace;return t};
 const alb=mk(true,(x,y,v)=>{const k=v<0.2?o.mortar:o.face.map((c,i)=>Math.max(0,Math.min(255,c+(Math.sin(x*0.11+y*0.07)*o.var+((x*3+y)%9-4)*1.5))));return k});
 const nrm=mk(false,(x,y)=>{const hx=h[y*n+((x+1)%n)]-h[y*n+((x+n-1)%n)],hy=h[((y+1)%n)*n+x]-h[((y+n-1)%n)*n+x];
  let nx=-hx*o.bump,ny=-hy*o.bump,nz=1,L=Math.hypot(nx,ny,nz)||1;return [(nx/L*0.5+0.5)*255,(ny/L*0.5+0.5)*255,(nz/L*0.5+0.5)*255]});
 const rgh=mk(false,(x,y,v)=>[v<0.2?o.roughJ:o.roughF+(Math.sin(x*0.2+y*0.15)*18),0,0]);
 const ao=mk(false,(x,y,v)=>{const a=v<0.2?90:v<0.5?150:230;return [a,a,a]});
 return {alb,nrm,rgh,ao};
}
const TEX={
 portland:pbr({joint:7,noise:0.05,bump:3.2,face:[214,206,192],mortar:[168,158,144],var:10,roughF:188,roughJ:242}),
 faience:pbr({joint:3,noise:0.015,bump:1.1,face:[236,232,226],mortar:[196,190,182],var:5,roughF:78,roughJ:170}),
 brick:pbr({joint:8,noise:0.04,bump:2.4,face:[138,84,58],mortar:[196,176,150],var:14,roughF:200,roughJ:235}),
 render:pbr({joint:4,noise:0.02,bump:0.55,face:[214,206,186],mortar:[186,178,160],var:6,roughF:155,roughJ:200}),
 grey:pbr({joint:3,noise:0.012,bump:0.35,face:[148,152,156],mortar:[118,122,126],var:4,roughF:110,roughJ:170}),
};
function stoneShader(mat,set,block){
 mat.metalness=0;mat.roughness=0.8;mat.envMapIntensity=set===TEX.faience?0.45:0.2;
 if('clearcoat' in mat){mat.clearcoat=0;mat.clearcoatRoughness=1}
 mat.onBeforeCompile=sh=>{
  sh.uniforms.uAlb={value:set.alb};sh.uniforms.uNrm={value:set.nrm};sh.uniforms.uRgh={value:set.rgh};sh.uniforms.uAo={value:set.ao};sh.uniforms.uBlock={value:block};
  sh.vertexShader=sh.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;')
   .replace('#include <begin_vertex>','#include <begin_vertex>\nvWP=(modelMatrix*vec4(transformed,1.0)).xyz;vWN=normalize(mat3(modelMatrix)*normal);');
  sh.fragmentShader=sh.fragmentShader.replace('#include <common>',`#include <common>
   varying vec3 vWP;varying vec3 vWN;uniform sampler2D uAlb,uNrm,uRgh,uAo;uniform vec2 uBlock;
   vec3 tri(sampler2D t,vec3 p,vec3 n){vec3 w=pow(abs(n),vec3(4.0));w/=(w.x+w.y+w.z+1e-4);
    return texture2D(t,p.zy/uBlock).rgb*w.x+texture2D(t,p.xz/vec2(uBlock.x)).rgb*w.y+texture2D(t,p.xy/uBlock).rgb*w.z;}
   vec3 triN(vec3 p,vec3 n){vec3 w=pow(abs(n),vec3(4.0));w/=(w.x+w.y+w.z+1e-4);
    vec3 tx=texture2D(uNrm,p.zy/uBlock).xyz*2.0-1.0;vec3 ty=texture2D(uNrm,p.xz/vec2(uBlock.x)).xyz*2.0-1.0;vec3 tz=texture2D(uNrm,p.xy/uBlock).xyz*2.0-1.0;
    return normalize(vec3(tx.z,tx.y,tx.x)*w.x+vec3(ty.x,ty.z,ty.y)*w.y+vec3(tz.x,tz.y,tz.z)*w.z);}`)
   .replace('#include <normal_fragment_begin>',`#include <normal_fragment_begin>
    normal=normalize(mat3(viewMatrix)*triN(vWP,normalize(vWN)));`)
   .replace('#include <map_fragment>',`#include <map_fragment>
    vec3 Nw=normalize(vWN);diffuseColor.rgb=tri(uAlb,vWP,Nw)*tri(uAo,vWP,Nw).r;
    float blot=fract(sin(dot(floor(vWP*0.85),vec3(12.9898,78.233,37.719)))*43758.5453);
    diffuseColor.rgb*=mix(0.94,1.05,blot);`)
   .replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
    roughnessFactor=clamp(tri(uRgh,vWP,normalize(vWN)).r,0.18,1.0);`);
 };
 mat.customProgramCacheKey=()=>'pbr'+set.alb.uuid;
 mat.needsUpdate=true;
}
const ROOM=tile(g=>{g.fillStyle='#141a22';g.fillRect(0,0,256,256);g.fillStyle='#2c261e';g.fillRect(0,168,256,88);g.fillStyle='#3d4c5c';g.fillRect(28,36,78,120);g.fillStyle='#0e1218';g.fillRect(150,48,36,130);g.fillStyle='#5c5348';g.fillRect(0,160,256,10)},true);
const VIEW=(()=>{const c=document.createElement('canvas');c.width=c.height=512;const g=c.getContext('2d');
 const sky=g.createLinearGradient(0,0,0,512);sky.addColorStop(0,'#6e86a0');sky.addColorStop(0.28,'#c5d4e2');sky.addColorStop(0.42,'#d9cbb8');
 g.fillStyle=sky;g.fillRect(0,0,512,220);g.fillStyle='#7c5c48';g.fillRect(0,200,512,312);
 for(let i=0;i<7;i++){const x=18+i*72;g.fillStyle='#5c4638';g.fillRect(x,230,58,250);g.fillStyle='#c9d6e2';for(let r=0;r<5;r++)for(let k=0;k<2;k++)g.fillRect(x+8+k*26,248+r*36,16,22)}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t})();
const TL=new THREE.TextureLoader();
function tx(url,srgb,rep){const t=TL.load(url,()=>{draw=true});t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=MOB?1:8;t.colorSpace=srgb?THREE.SRGBColorSpace:THREE.LinearSRGBColorSpace;if(rep)t.repeat.set(rep,rep);return t}
let FAB=null,OAK=null;const texIn=()=>{if(FAB)return;FAB={d:tx('tex/teddy_d.jpg',1,2.2),n:tx('tex/teddy_n.jpg',0,2.2),r:tx('tex/teddy_r.jpg',0,2.2)};OAK={n:tx('tex/oak_n.jpg',0,3),r:tx('tex/oak_r.jpg',0,3)}};
const STREET=tx('tex/whitworth.jpg',1);
// ---- 7-step exterior look (barclay/ext7): weathered cream stone, stone flags, darker asphalt, cloud sky.
// All world-position noise: nothing tiles on the hero (no grid; see AGENTS.md lessons).
const NZ=`float h21(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}
float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float a=.5,s=0.;for(int i=0;i<4;i++){s+=a*vn(p);p*=2.03;a*=.5;}return s;}`;
function wp(mat,key,frag,uni){
 mat.onBeforeCompile=sh=>{Object.assign(sh.uniforms,uni||{});
  sh.vertexShader=sh.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;')
   .replace('#include <begin_vertex>','#include <begin_vertex>\nvWP=(modelMatrix*vec4(transformed,1.0)).xyz;vWN=normalize(mat3(modelMatrix)*objectNormal);');
  sh.fragmentShader=sh.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 vWP;varying vec3 vWN;\n'+NZ)
   .replace('#include <map_fragment>','#include <map_fragment>\n'+frag);};
 mat.customProgramCacheKey=()=>key;mat.needsUpdate=true;
}
// stone: only stone-toned texels (palette hero) get warmth and wear, so frames, glass and door stay clean
const weather=(mat,palette,streak0)=>{const streak=streak0*0.65;return wp(mat,'ext7w'+(palette?1:0)+streak,`
 {vec3 N=normalize(vWN);float L=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));
 float st=${palette?'smoothstep(0.2,0.33,L)*(1.0-smoothstep(0.66,0.76,L))':'1.0'};
 diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*vec3(1.17,1.03,0.78),st);
 float al=vWP.x*0.8+vWP.z*0.6;
 diffuseColor.rgb*=mix(1.0,0.93+0.12*fbm(vec2(al*0.35,vWP.y*0.25)),st);
 float sk=smoothstep(0.55,0.8,fbm(vec2(al*2.6,vWP.y*0.18)+3.1));
 diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*vec3(0.6,0.56,0.5),sk*${streak.toFixed(2)}*st);
 float low=1.0-smoothstep(0.05,1.4,vWP.y);
 diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*vec3(0.62,0.56,0.48),low*0.55*st*(0.6+0.4*fbm(vWP.xz*3.0)));
 diffuseColor.rgb*=mix(1.0,0.7,smoothstep(-0.3,-0.8,N.y)*st);
 diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*vec3(0.8,0.74,0.66),smoothstep(0.5,0.9,N.y)*0.35*st);}`)};
// 600 mm stone flags in stretcher bond (flag size is a stand-in), joints, per-flag tone, stains, gum
const flags=mat=>{mat.map=null;mat.color.set(0xffffff);mat.roughness=0.8;mat.metalness=0;wp(mat,'ext7flags',`
 {vec2 p=vWP.xz/0.6;float row=floor(p.y);p.x+=mod(row,2.0)*0.5;vec2 c=floor(p),f=fract(p);
 float j=min(min(f.x,1.0-f.x),min(f.y,1.0-f.y));float aa=fwidth(p.x)+fwidth(p.y);float far=smoothstep(0.04,0.2,aa);float joint=(1.0-smoothstep(0.004,0.014+aa,j))*(1.0-far);
 vec3 col=mix(vec3(0.2,0.197,0.185),vec3(0.26,0.255,0.24),mix(h21(c+7.0),0.5,far));
 col*=0.9+0.2*fbm(vWP.xz*1.6);col*=1.0-0.35*smoothstep(0.6,0.76,fbm(vWP.xz*0.8+11.0));
 float g=step(0.985,h21(floor(vWP.xz*9.0)))*step(0.5,vn(vWP.xz*1.5));col=mix(col,vec3(0.12),g*0.7*(1.0-far));
 col=mix(col,vec3(0.15,0.145,0.135),joint);diffuseColor.rgb=col;}`)};
// the general 'Neighbour' mesh also carries the open ground: flags only on flat, low, upward faces
const groundFlags=mat=>{mat.metalness=0;mat.roughness=0.85;wp(mat,'ext7gflags',`
 {vec3 N=normalize(vWN);float gm=step(0.9,N.y)*(1.0-smoothstep(1.0,2.0,vWP.y));
 vec2 p=vWP.xz/0.6;float row=floor(p.y);p.x+=mod(row,2.0)*0.5;vec2 c=floor(p),f=fract(p);
 float j=min(min(f.x,1.0-f.x),min(f.y,1.0-f.y));float aa=fwidth(p.x)+fwidth(p.y);float far=smoothstep(0.04,0.2,aa);
 float joint=(1.0-smoothstep(0.004,0.014+aa,j))*(1.0-far);
 vec3 col=mix(vec3(0.2,0.197,0.185),vec3(0.26,0.255,0.24),mix(h21(c+7.0),0.5,far));
 col*=0.9+0.2*fbm(vWP.xz*1.6);col*=1.0-0.35*smoothstep(0.6,0.76,fbm(vWP.xz*0.8+11.0));
 col=mix(col,vec3(0.15,0.145,0.135),joint);diffuseColor.rgb=mix(diffuseColor.rgb,col,gm);}`)};
const asphalt=mat=>{mat.roughness=0.85;wp(mat,'ext7asph',`
 {diffuseColor.rgb*=0.62;float o=smoothstep(0.62,0.76,fbm(vec2(vWP.x*0.6,vWP.z*1.8)+5.0));diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.03),o*0.5);}`)};
// sky dome: blue gradient with drifting fbm cloud; colours set per time of day in tod()
const SKY={zen:{value:new THREE.Color(0x2a5bb8)},hor:{value:new THREE.Color(0xa9bdd8)},cl:{value:new THREE.Color(0xf4f4f2)},cover:{value:0.5},t:{value:0}};
const skyMesh=new THREE.Mesh(new THREE.SphereGeometry(1500,48,24),new THREE.ShaderMaterial({uniforms:SKY,side:THREE.BackSide,depthWrite:false,fog:false,
 vertexShader:'varying vec3 vD;void main(){vD=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);gl_Position.z=gl_Position.w;}',
 fragmentShader:'uniform vec3 zen,hor,cl;uniform float cover,t;varying vec3 vD;'+NZ+`void main(){float y=max(vD.y,0.0);vec3 c=mix(hor,zen,smoothstep(0.0,0.55,y));
 vec2 q=vD.xz/max(vD.y,0.06)*0.6+vec2(t*0.004,t*0.0015);float n=fbm(q*1.2)+0.5*fbm(q*4.0);
 float k=smoothstep(cover,cover+0.32,n*0.75)*smoothstep(0.02,0.22,vD.y);vec3 cc=cl*mix(0.72,1.0,smoothstep(0.4,1.0,n*0.8));
 gl_FragColor=vec4(mix(c,cc,k),1.0);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
 }`}));
skyMesh.frustumCulled=false;skyMesh.renderOrder=-1;skyMesh.name='EXT7_sky';S.add(skyMesh);
const prep=(g,kind)=>{if(kind==='in')texIn();g.traverse(o=>{
 if(o.isMesh&&o.material&&(/BAKED/.test(o.name)||/BAKED/.test(o.material.name||''))){const mp=o.material.map;if(mp){mp.colorSpace=THREE.SRGBColorSpace;mp.anisotropy=MOB?1:8}
  const m=new THREE.MeshBasicMaterial({map:mp,toneMapped:true});
  m.onBeforeCompile=sh=>{sh.fragmentShader=sh.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
   diffuseColor.rgb*=vec3(0.62,0.55,0.45);
   float L=max(diffuseColor.r,max(diffuseColor.g,diffuseColor.b));
   float hot=smoothstep(0.58,0.9,L);
   diffuseColor.rgb=mix(diffuseColor.rgb,vec3(1.0,0.82,0.62)*min(L,0.92),hot*0.8);`)};
  m.customProgramCacheKey=()=>'bake-knee';o.material=m;o.castShadow=o.receiveShadow=false;return}
 if(o.isMesh&&/backdrop/i.test(o.name)){o.material=new THREE.MeshBasicMaterial({map:STREET,toneMapped:true,side:THREE.DoubleSide});return}
 if(o.isMesh&&kind==='in'&&/window/i.test(o.name)&&/glass/i.test(o.name)){o.material=new THREE.MeshPhysicalMaterial({name:'Window_glass',color:0xffffff,transparent:true,opacity:0.16,roughness:0.04,metalness:0,envMapIntensity:1.1,depthWrite:false,side:THREE.DoubleSide});return}
 if(o.isMesh&&(o.name==='HERO_glass'||/PaletteMaterial003/i.test((o.material&&o.material.name)||''))){
  // Glass keeps the exported geometry so frames and glazing bars stay visible; only the material changes.
  o.material=new THREE.MeshPhysicalMaterial({name:'Glass',color:0x2a333c,roughness:0.06,metalness:0,envMapIntensity:1.25,side:THREE.DoubleSide});
  o.castShadow=o.receiveShadow=false;return}
if(o.isMesh&&o.material){const n=o.material.name||'';
 if(kind==='hero'&&/Concrete_block|PaletteMaterial00[12]|Portland_stone|Burmantofts/.test(n)){o.material.envMapIntensity=0.35;if(!o.material.userData.w){o.material.userData.w=1;weather(o.material,/PaletteMaterial/.test(n),/Concrete/.test(n)?0.25:0.4)}}
 else if(kind==='ctx'&&/^Paving|^Ground/.test(n)){if(!o.material.userData.w){o.material.userData.w=1;flags(o.material)}}
 else if(kind==='ctx'&&n==='Neighbour'){if(!o.material.userData.w){o.material.userData.w=1;groundFlags(o.material)}}
 else if(kind==='ctx'&&/^Asphalt/.test(n)){if(!o.material.userData.w){o.material.userData.w=1;asphalt(o.material)}}
 else if(kind==='street'&&o.material.map&&o.material.transparent!==undefined&&/print/i.test(n)){o.material.alphaTest=0.45;o.material.transparent=false;o.material.depthWrite=true;o.material.polygonOffset=true;o.material.polygonOffsetFactor=-2;o.material.polygonOffsetUnits=-2}
 else if(kind==='ctx'&&n==='Ctx_brick'){o.material.onBeforeCompile=()=>{};o.material.map=null;o.material.color.set(0x9c5a40);o.material.roughness=0.9;o.material.metalness=0;o.material.envMapIntensity=0.15;o.material.needsUpdate=true}
 else if(kind==='ctx'&&n==='Ctx_render'){o.material.onBeforeCompile=()=>{};o.material.map=null;o.material.color.set(0xd9d0bf);o.material.roughness=0.85;o.material.metalness=0;o.material.envMapIntensity=0.2;o.material.needsUpdate=true}
 else if(kind==='ctx'&&n==='Ctx_grey'){o.material.onBeforeCompile=()=>{};o.material.map=null;o.material.color.set(0xa9adb1);o.material.roughness=0.75;o.material.metalness=0;o.material.envMapIntensity=0.25;o.material.needsUpdate=true}
 else if(kind==='ctx'&&n==='Ctx_glass'){o.material=new THREE.MeshPhysicalMaterial({name:'Ctx_glass',color:0x7f93a3,roughness:0.12,metalness:0,envMapIntensity:1.0})}
 else if(kind==='ctx'&&n==='Ctx_roof'){o.material.color.set(0x6a6c70);o.material.roughness=0.88;o.material.metalness=0;o.material.envMapIntensity=0.08}
 else if(kind==='ctx'&&n==='Neighbour'){o.material.metalness=0;o.material.roughness=0.9;o.material.envMapIntensity=0.15}
 else if(kind==='in'&&/velvet/i.test(n)&&!o.material.userData.fab){o.material.map=FAB.d;o.material.normalMap=FAB.n;o.material.roughnessMap=FAB.r;o.material.color.set(0x1c2c4a);o.material.roughness=1;o.material.metalness=0;o.material.envMapIntensity=0.15;o.material.userData.fab=1;o.material.needsUpdate=true}
 else if(kind==='in'&&/boucle/i.test(n)&&!o.material.userData.fab){o.material.map=FAB.d;o.material.normalMap=FAB.n;o.material.roughnessMap=FAB.r;o.material.color.set(0xe6d9c4);o.material.roughness=1;o.material.metalness=0;o.material.userData.fab=1;o.material.needsUpdate=true}
 else if(kind==='in'&&/oak|Floor_light/i.test(n)&&!o.material.userData.fab){o.material.normalMap=OAK.n;o.material.roughnessMap=OAK.r;o.material.roughness=1;o.material.metalness=0;o.material.normalScale.set(0.65,0.65);o.material.userData.fab=1;o.material.needsUpdate=true}
}
if(o.isMesh&&o.material&&o.material.clearcoat>0){o.material.clearcoat=0;o.material.needsUpdate=true}
if(o.isLight){o.castShadow=false;if(kind==='in'){o.color.set(0xffb060);o.intensity=9;o.decay=2;o.distance=4.2}else{o.intensity=(+new URLSearchParams(location.search).get("lk")||1.2);o.decay=2;o.distance=6}}if(o.isMesh){const glass=o.material&&/glass/i.test(o.material.name||'');const extSh=!MOB&&kind!=='in'&&!glass;const inSh=!MOB&&kind==='in'&&!glass&&!/backdrop/i.test(o.name);o.castShadow=!!(extSh||inSh);o.receiveShadow=!!(extSh||inSh);if(o.material&&o.material.name==='TV_screen'){o.material.color.set(0x101820);o.material.roughness=0.16;o.material.metalness=0;o.material.envMapIntensity=1.1}}})};
let draw=true,ceil=null;
let envTex;new RGBELoader().load(MOB?'env_m.hdr':'env.hdr',t=>{t.mapping=THREE.EquirectangularReflectionMapping;envTex=t;S.environment=t;S.background=null;tod($('tod').value);draw=true});
let done=0;const need=4;const pr={};const bar=$('pb'),pbw=$('pbw');
const upd=()=>{const v=Object.values(pr);const t=v.reduce((a,b)=>a+b,0)/need;if(bar)bar.style.width=Math.round(t*100)+'%';if(pbw)pbw.style.display=done>=need?'none':'';};
const prog=()=>{done++;upd();draw=true;say(done<need?`Loading 3D models… ${done}/${need}${MOB?' (mobile quality)':''}`:'')};
const INT=(q0.get('int')||'v5');const intU=INT==='v4'?(MOB?'twobed_m.glb':'twobed.glb'):(MOB?'twobed_v5_m.glb':'twobed_v5.glb');
const queue=MOB?[['hero_mo3.glb',ext],['context_mo.glb',ext],['ext7_street_o.glb',ext],[intU,intr]]:[['hero3.glb',ext],['context_typed_opt.glb',ext],['ext7_street.glb',ext],[intU,intr]];
const loadNext=()=>{if(!queue.length)return;const [u,g]=queue.shift();pr[u]=0;const kind=u.startsWith('context')?'ctx':u.startsWith('hero')?'hero':u.startsWith('ext7')?'street':'in';L.load(u,x=>{pr[u]=1;prep(x.scene,kind);g.add(x.scene);if(/^Ceiling/.test(x.scene.name))ceil=x.scene;x.scene.traverse(o=>{if(/^Ceiling/.test(o.name)&&o.isMesh)ceil=o});prog();reshadow();loadNext()},e=>{if(e&&e.total){pr[u]=e.loaded/e.total;upd();say(`Loading ${MOB?'mobile ':''}3D models… ${Math.round(Object.values(pr).reduce((a,b)=>a+b,0)/need*100)}%`)}},e=>say('Could not load '+u+' ('+(e&&e.message||'network error')+'). Check your connection and reload.',1))};
loadNext();
const P={street:{p:[-1.41,1.7,29.79],t:[0.2,8.5,9.8],f:70},facade:{p:[-1.4,1.7,29.8],t:[-1,6.5,17.3],f:62},entrance:{p:[-0.75,1.7,21.0],t:[-0.27,3.0,15.3],f:45},aerial:{p:[24.83,120,127.14],t:[-0.2,5.4,4],f:48},viaduct:{p:[-51.07,10.31,38.93],t:[-14.9,10,21.8],f:56},interior:{p:[0.6,12,11],t:[0.2,0,-0.3],f:45},i_living:{p:[-0.5,1.5,1.91],t:[2.97,0.9,0.15],f:70},i_kitchen:{p:[-0.79,1.5,1.18],t:[3.41,1.1,2.96],f:70},i_bed1:{p:[-2.0,1.3,-0.85],t:[-2.41,0.8,-3.17],f:70},i_bed2:{p:[1.5,1.3,-1.6],t:[1.36,0.8,-3.62],f:70},i_bath:{p:[-2.08,1.55,3.83],t:[-3.02,0.9,2.88],f:80},i_hall:{p:[-0.65,1.5,4.15],t:[0.09,1.3,0.29],f:75},i_store:{p:[-1.09,1.5,1.32],t:[-3.0,1.0,1.32],f:80}};
let preset='street';
window.cam=k=>{preset=k;const v=P[k];C.position.fromArray(v.p);O.target.fromArray(v.t);C.fov=v.f;C.updateProjectionMatrix();O.update();draw=true};
// sun elevation/azimuth = tod_panel.py sun_pos() (same NOAA formula, same preset hours, default date 21 June) so web == Blender renders
const LAT=53.4741,LON=-2.2442,TODH={sunrise:6.75,morning:9.0,midday:15.5,golden:18.5,dusk:19.75,night:23.0};
function sunPos(h,mo=6,dy=21){const n=[31,28,31,30,31,30,31,31,30,31,30,31].slice(0,mo-1).reduce((a,b)=>a+b,0)+dy,bst=(mo>3||(mo==3&&dy>=29))&&(mo<10||(mo==10&&dy<25)),hr=h-(bst?1:0),g=2*Math.PI/365*(n-1+(hr-12)/24),
 eqt=229.18*(0.000075+0.001868*Math.cos(g)-0.032077*Math.sin(g)-0.014615*Math.cos(2*g)-0.040849*Math.sin(2*g)),
 dec=0.006918-0.399912*Math.cos(g)+0.070257*Math.sin(g)-0.006758*Math.cos(2*g)+0.000907*Math.sin(2*g)-0.002697*Math.cos(3*g)+0.00148*Math.sin(3*g),
 ha=THREE.MathUtils.degToRad((hr*60+eqt+4*LON)/4-180),la=THREE.MathUtils.degToRad(LAT),el=Math.asin(Math.max(-1,Math.min(1,Math.sin(la)*Math.sin(dec)+Math.cos(la)*Math.cos(dec)*Math.cos(ha)))),
 az=Math.atan2(Math.sin(ha),Math.cos(ha)*Math.sin(la)-Math.tan(dec)*Math.cos(la))+Math.PI;return [THREE.MathUtils.radToDeg(el),(THREE.MathUtils.radToDeg(az)%360+360)%360]}
window.__sunPos=sunPos;
// light colour/intensity/exposure per preset (archive look); sun direction from sunPos() above
const T={sunrise:[8,120,0xffb070,1.1,0.45,1.05],morning:[22,150,0xfff0d8,1.7,0.65,1.0],midday:[52,155,0xfff6ea,1.9,0.7,0.92],golden:[14,230,0xffc080,1.5,0.55,1.12],dusk:[3,250,0xff9a6a,0.4,0.28,1.2],night:[-8,0,0x8090c0,0.05,0.1,1.35]};
const SKYC={sunrise:[0x5a6fa8,0xf0b08a,0xffe2cc,0.55],morning:[0x3263b8,0xb8cbe2,0xffffff,0.5],midday:[0x2a5bb8,0xa9bdd8,0xf4f4f2,0.5],golden:[0x3a5aa0,0xf2c08e,0xffe6c8,0.55],dusk:[0x1c2850,0xc07a62,0xd9a28a,0.6],night:[0x05070d,0x0f1524,0x2a2f3a,0.62]};
window.tod=k=>{let [el,az,col,I,env,expo]=T[k];[el,az]=sunPos(TODH[k]);{const c=SKYC[k];SKY.zen.value.set(c[0]);SKY.hor.value.set(c[1]);SKY.cl.value.set(c[2]);SKY.cover.value=c[3]}const e=THREE.MathUtils.degToRad(Math.max(el,1)),a=THREE.MathUtils.degToRad(az);
 sun.position.set(200*Math.cos(e)*Math.sin(a),200*Math.sin(e),3+200*Math.cos(e)*Math.cos(a));sun.target.position.set(0,0,0);
 sun.position.z=-200*Math.cos(e)*Math.cos(a);sun.color.set(col);sun.intensity=I;
 if(!intr.visible){S.environmentIntensity=env;hemi.intensity=env*0.35;R.toneMappingExposure=expo}
 S.backgroundIntensity=Math.max(env,0.06);
 const n=(k=='night'||k=='dusk');lampG.children.forEach(l=>l.intensity=n?(k=='night'?18:8):0);lampG.visible=n&&!intr.visible;reshadow();};
window.mode=k=>{const i=k=='i';ext.visible=!i;intr.visible=i;$('li').className=i?'':'x';$('le').className=i?'x':'';$('bi').className=i?'on':'';$('be').className=i?'':'on';$('presets').style.display=i?'none':'';$('ipresets').style.display=i?'':'none';sun.visible=!i;lampG.visible=false;if(i){S.environmentIntensity=0.26;hemi.color.set(0xffd6a6);hemi.groundColor.set(0xb07f52);hemi.intensity=0.75;R.toneMappingExposure=0.9;fill.visible=true;ssao.kernelRadius=0.16;ssao.maxDistance=0.1;ssao.minDistance=0.001}else{fill.visible=false;hemi.color.set(0xdfe8ff);hemi.groundColor.set(0x55504a);ssao.kernelRadius=0.3;ssao.maxDistance=0.22;if($('tod'))tod($('tod').value)}nf(i);reshadow();cam(i?'interior':'street')};
window.ar=()=>{O.autoRotate=!O.autoRotate;draw=true;$('ba').className=O.autoRotate?'on':''};
const rs=()=>{const w=$('v').clientWidth,h=$('v').clientHeight;R.setSize(w,h);comp.setSize(w,h);C.aspect=w/h;C.updateProjectionMatrix();draw=true};addEventListener('resize',rs);if(window.ResizeObserver)new ResizeObserver(rs).observe($('v'));rs();
const q=new URLSearchParams(location.search);mode(q.get('m')||'e');if(q.get('cam'))cam(q.get('cam'));if(q.get('tod')){$('tod').value=q.get('tod')}tod($('tod').value);
let fp=false,flying=false,lastExt={p:[-1.41,1.7,29.79],t:[0.2,8.5,9.8],f:70},yaw=0,pitch=0,curRoom=null;
O.addEventListener('change',()=>{draw=true});
R.setAnimationLoop(()=>{skyMesh.position.copy(C.position);skyMesh.visible=!intr.visible;
 if(document.hidden)return;
 if(O.enabled&&!fp&&!flying)O.update();
 if(flying||(O.autoRotate&&O.enabled&&!fp))draw=true;
 if(!draw)return;
 if(ceil)ceil.visible=!(preset==='interior'||C.position.y>=2.95);
 wTick();if(!MOB)comp.render();else R.render(S,C);
 draw=false;
 const t=performance.now();if(lastT&&t-lastT<200){ft.push(t-lastT);if(ft.length>=45){ft.sort((a,b)=>a-b);const med=ft[22];ft=[];if(med>34&&dpr>1){dpr=Math.max(1,dpr-0.25);R.setPixelRatio(dpr);rs()}}}lastT=t;
});let ft=[],lastT=0;
document.addEventListener('visibilitychange',()=>{if(!document.hidden)draw=true});
window.__ready=()=>done>=need&&!!envTex;
// ---- x_tricks #10 canal water: Water2 on the flat OSM canal/basin tops (nearest first; 2 on desktop, 1 on phones), others get the
// same normal maps scrolling on a cheap standard material. Water2 has no sun input: it reflects the scene, whose sun follows tod_panel.py.
const wl=new THREE.TextureLoader(),wn=[wl.load('water/Water_1_M_Normal.jpg',()=>{draw=true}),wl.load('water/Water_2_M_Normal.jpg',()=>{draw=true})];wn.forEach(t=>{t.wrapS=t.wrapT=THREE.RepeatWrapping});
const waterG=new THREE.Group();waterG.name='CanalWater2';ext.add(waterG);const cheapW=[];
(()=>{const NW=(q0.get('water')==='0'||(MOB&&q0.get('water')!=='1'))?0:1; /* phones: cheap scrolling mesh only (perf); ?water=1 forces Water2 */ // ?water=0 = no Water2 (cheap mesh only); // canal.json = only the canal triangles with open sky above (canal_web.py); Water2 (2 extra scene passes) for the OSM canal way nearest the hero, the rest merged into ONE cheap mesh (1 draw call)
 const G=canals.map(c=>{const ys=[];for(let i=1;i<c.v.length;i+=3)ys.push(c.v[i]);ys.sort((a,b)=>a-b);let d=1e9;for(let i=0;i<c.v.length;i+=3)d=Math.min(d,Math.hypot(c.v[i],c.v[i+2]));return {c,y:ys[ys.length>>1],d}}).sort((a,b)=>a.d-b.d);
 const geoOf=(list,plane)=>{const pos=[],uv=[];for(const g of list){const v=g.c.v,I=g.c.i,y0=plane?g.y:0;
   for(let i=0;i<I.length;i+=3){const P=[0,1,2].map(j=>{const q=I[i+j]*3;return [v[q],-v[q+2],v[q+1]-y0]}),cz=(P[1][0]-P[0][0])*(P[2][1]-P[0][1])-(P[1][1]-P[0][1])*(P[2][0]-P[0][0]);
    (cz<0?[0,2,1]:[0,1,2]).forEach(j=>{pos.push(...P[j]);uv.push(P[j][0]/4,P[j][1]/4)})}} // local XY plane, wound to +Z (= world up after rotation.x=-PI/2)
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geo.computeVertexNormals();return geo};
 const put=(m,y,name,w2)=>{m.rotation.x=-Math.PI/2;m.position.y=y;m.name=name;m.userData.water2=w2;waterG.add(m)};
 G.slice(0,NW).forEach(g=>put(new Water(geoOf([g],true),{color:0x9fb3aa,scale:1,flowDirection:new THREE.Vector2(1,0.3),flowSpeed:0.012,reflectivity:0.04,textureWidth:MOB?256:512,textureHeight:MOB?256:512,normalMap0:wn[0],normalMap1:wn[1]}),g.y,'Canal_water2_'+g.c.name,true));
 if(G.length>NW){const mat=new THREE.MeshStandardMaterial({color:0x07100e,roughness:0.06,metalness:0,normalMap:wn[0].clone(),normalScale:new THREE.Vector2(0.35,0.35)});mat.normalMap.wrapS=mat.normalMap.wrapT=THREE.RepeatWrapping;cheapW.push(mat);put(new THREE.Mesh(geoOf(G.slice(NW),false),mat),0,'Canal_water_cheap',false)}})();
{const w=waterG.children.find(o=>o.userData.water2)||waterG.children[0];if(w){const b=new THREE.Box3().setFromObject(w),y=w.position.y;P.canal={p:[b.max.x-3,y+2.5,(b.min.z+b.max.z)/2],t:[b.min.x+20,y,(b.min.z+b.max.z)/2],f:56}}} // URL-only test view ?cam=canal (no button)
if(q0.get('cam')==='canal')cam('canal');
window.__water=()=>waterG.children.map(o=>({name:o.name,water2:o.userData.water2,y:+o.position.y.toFixed(2),tris:o.geometry.attributes.position.count/3}));
let wt0=performance.now();const wTick=()=>{const t=(performance.now()-wt0)/1000;cheapW.forEach(m=>m.normalMap.offset.set(t*0.004,t*0.0025))};
window.__extReady=()=>done>=3&&!!envTex;window.__dpr=()=>dpr;window.__kick=()=>{draw=true};
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
function fly(v,dur,done){flying=true;O.enabled=false;const p0=C.position.clone(),t0=O.target.clone(),f0=C.fov,p1=new THREE.Vector3().fromArray(v.p),t1=new THREE.Vector3().fromArray(v.t),f1=v.f,st=performance.now();
 (function step(){const k=Math.min(1,(performance.now()-st)/dur),e=ease(k);C.position.lerpVectors(p0,p1,e);O.target.lerpVectors(t0,t1,e);C.fov=f0+(f1-f0)*e;C.updateProjectionMatrix();C.lookAt(O.target);draw=true;if(k<1)requestAnimationFrame(step);else{flying=false;draw=true;done&&done()}})()}
function enterFP(){fp=true;O.enabled=false;const d=O.target.clone().sub(C.position).normalize();yaw=Math.atan2(-d.x,-d.z);pitch=Math.asin(d.y);nf(1);applyLook();$('fph').className=''}
function applyLook(){C.rotation.set(pitch,yaw,0,'YXZ');draw=true}
function setRoomUI(r){document.querySelectorAll('#rooms button[data-r]').forEach(b=>b.className=b.dataset.r===r?'on':'');$('bx').className='';}
window.goRoom=r=>{if(flying)return;const wasExt=ext.visible;if(wasExt){lastExt={p:C.position.toArray(),t:O.target.toArray(),f:C.fov};mode('i')}
 preset=r;
 if(fp){ /* room to room: rise to just under ceiling, then glide */ const mid={p:[(C.position.x+P[r].p[0])/2,2.6,(C.position.z+P[r].p[2])/2],t:P[r].t,f:P[r].f};fp=false;fly(mid,450,()=>fly(P[r],750,enterFP))}
 else fly(P[r],wasExt?1400:1400,enterFP);curRoom=r;setRoomUI(r)};
window.goDoll=()=>{if(flying)return;preset='interior';fp=false;$('fph').className='x';nf(1);fly(P.interior,1200,()=>{O.enabled=true;O.update()});setRoomUI(null)};
window.backExt=()=>{if(flying)return;fp=false;$('fph').className='x';curRoom=null;fly(P.interior,1000,()=>{mode('e');C.position.set(lastExt.p[0],lastExt.p[1]+40,lastExt.p[2]+40);O.target.fromArray(lastExt.t);nf(0);fly(lastExt,1100,()=>{O.enabled=true;O.update()});document.querySelectorAll('#rooms button').forEach(b=>b.className=b.id=='bx'?'x':'')})};
const _mode=window.mode;window.mode=k=>{if(k==='e'&&ext.visible===false&&!flying){fp=false;$('fph').className='x';$('bx').className='x'}if(k==='i')$('bx').className='';else $('bx').className='x';O.enabled=true;nf(k==='i');document.body.classList.toggle('ext',k!=='i');_mode(k)};
document.body.classList.toggle('ext',!intr.visible);
// pointer look (mouse + touch drag), wheel / pinch FOV zoom
const el=R.domElement,pts=new Map();let pd0=0,fov0=70;
el.addEventListener('pointerdown',e=>{if(!fp)return;pts.set(e.pointerId,[e.clientX,e.clientY]);el.setPointerCapture(e.pointerId);if(pts.size==2){const a=[...pts.values()];pd0=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);fov0=C.fov}});
el.addEventListener('pointermove',e=>{if(!fp||!pts.has(e.pointerId))return;const pr=pts.get(e.pointerId);
 if(pts.size==1){const s=0.0042*C.fov/70;yaw+=(e.clientX-pr[0])*s;pitch=Math.max(-1.3,Math.min(1.3,pitch+(e.clientY-pr[1])*s));applyLook()}
 pts.set(e.pointerId,[e.clientX,e.clientY]);
 if(pts.size==2){const a=[...pts.values()];const d=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);if(pd0>0){C.fov=Math.max(30,Math.min(95,fov0*pd0/d));C.updateProjectionMatrix();draw=true}}});
const up=e=>{pts.delete(e.pointerId);if(pts.size<2)pd0=0};el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);
el.addEventListener('wheel',e=>{if(!fp)return;e.preventDefault();C.fov=Math.max(30,Math.min(95,C.fov*(1+Math.sign(e.deltaY)*0.08)));C.updateProjectionMatrix();draw=true},{passive:false});
window.__fp=()=>fp&&!flying;window.__flying=()=>flying;
