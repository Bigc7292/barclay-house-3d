import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import cams from './cams.json';
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
const DPR_MAX=Math.min(devicePixelRatio,MOB?1.5:2);let dpr=DPR_MAX;R.setPixelRatio(dpr);R.shadowMap.enabled=!MOB;R.shadowMap.autoUpdate=false;R.shadowMap.type=THREE.PCFSoftShadowMap;
R.toneMapping=THREE.ACESFilmicToneMapping;R.outputColorSpace=THREE.SRGBColorSpace;$('v').appendChild(R.domElement);
const S=new THREE.Scene(), C=new THREE.PerspectiveCamera(40,1,0.1,2500);
// perf: render on demand. dirty>0 => draw this frame. shadows are static (redrawn only on time-of-day/model change)
let dirty=3;const kick=(n)=>{dirty=Math.max(dirty,n||2)};const reshadow=()=>{R.shadowMap.needsUpdate=true;kick()};window.__kick=kick;
const O=new OrbitControls(C,R.domElement);O.enableDamping=true;O.minDistance=0.3;O.maxDistance=1500;O.zoomToCursor=true;O.maxPolarAngle=Math.PI*0.495;O.addEventListener('change',()=>kick());
const sun=new THREE.DirectionalLight(0xffffff,3);sun.castShadow=!MOB;sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-70,right:70,top:70,bottom:-70,near:1,far:600});sun.shadow.bias=-0.0003;sun.shadow.normalBias=0.03;
S.add(sun,sun.target);const hemi=new THREE.HemisphereLight(0xdfe8ff,0x55504a,0.3);S.add(hemi);
const lampG=new THREE.Group();lampG.visible=false;lamps.slice().sort((a,b)=>Math.hypot(a[0],a[2])-Math.hypot(b[0],b[2])).slice(0,MOB?6:12).forEach(p=>{const l=new THREE.PointLight(0xffc27a,0,28,2);l.position.set(p[0],p[1],p[2]);lampG.add(l)});S.add(lampG);
const L=new GLTFLoader();L.setMeshoptDecoder(MeshoptDecoder);
const ext=new THREE.Group(), intr=new THREE.Group();S.add(ext,intr);intr.visible=false;
const prep=(g,shadow)=>g.traverse(o=>{if(o.isMesh&&/BAKED/.test(o.name)){const mp=o.material.map;if(mp){mp.colorSpace=THREE.SRGBColorSpace;mp.anisotropy=MOB?2:8}o.material=new THREE.MeshBasicMaterial({map:mp,toneMapped:false});o.castShadow=o.receiveShadow=false;return}
if(o.isMesh&&/backdrop/i.test(o.name)){const mp=o.material.map||o.material.emissiveMap;o.material=new THREE.MeshBasicMaterial({map:mp,toneMapped:false});return}
if(o.isMesh&&/(Window_glass|Glass_clear)/i.test(o.material&&o.material.name||'')){o.material=new THREE.MeshPhysicalMaterial({color:0xffffff,transparent:true,opacity:0.12,roughness:0.03,metalness:0,envMapIntensity:0.6,depthWrite:false});return}
if(o.isMesh&&o.material&&o.material.clearcoat>0&&MOB){o.material.clearcoat=0;o.material.needsUpdate=true}
if(o.isLight){o.castShadow=false;o.intensity=(+new URLSearchParams(location.search).get("lk")||1.2);o.decay=2;o.distance=6}if(o.isMesh){o.castShadow=shadow&&!MOB;o.receiveShadow=!MOB;const m=o.material;if(m&&/glass/i.test(m.name)){m.transparent=false;m.opacity=1;m.metalness=0.0;m.roughness=0.04;m.envMapIntensity=1.5}}});
let envTex;new RGBELoader().load(MOB?'env_m.hdr':'env.hdr',t=>{t.mapping=THREE.EquirectangularReflectionMapping;envTex=t;S.environment=t;S.background=t;tod($('tod').value);kick()});
let done=0;const need=3,needExt=2;const pr={};const bar=$('pb'),pbw=$('pbw');
const upd=()=>{const v=Object.values(pr);const t=v.reduce((a,b)=>a+b,0)/Math.max(v.length,1);if(bar)bar.style.width=Math.round(t*100)+'%';if(pbw)pbw.style.display=extDone>=needExt?'none':'';};let extDone=0;
const prog=(g)=>{done++;if(g===ext)extDone++;upd();say(extDone<needExt?`Loading 3D models… ${extDone}/${needExt}${MOB?' (mobile quality)':''}`:'');reshadow();if(extDone>=needExt&&!intrReq)loadIntr()};let intrReq=false;
const load=(u,g,sh)=>{pr[u]=0;L.load(u,x=>{pr[u]=1;prep(x.scene,sh);g.add(x.scene);prog(g)},e=>{if(e.total){pr[u]=e.loaded/e.total;upd();if(extDone<needExt)say(`Loading ${MOB?'mobile ':''}3D models… ${Math.round(Object.values(pr).reduce((a,b)=>a+b,0)/Object.keys(pr).length*100)}%`)}},e=>say('Could not load '+u+' ('+(e.message||'network error')+'). Check your connection and reload.',1))};
// phones: meshopt-compressed mobile files (hero_mo/context_mo = dedup+meshopt of hero_m/context_m, ~2.6x smaller). interior loads after the exterior is up (or first if opened in interior)
function loadIntr(){if(intrReq)return;intrReq=true;load(MOB?'twobed_m.glb':'twobed.glb',intr,!MOB)}
if(new URLSearchParams(location.search).get('m')==='i')loadIntr();
if(MOB){load('hero_mo.glb',ext,false);load('context_mo.glb',ext,false)}else{load('hero.glb',ext,true);load('context.glb',ext,true)}
const P={street:{p:[-1.41,1.7,29.79],t:[0.2,8.5,9.8],f:70},facade:{p:[-1.4,1.7,29.8],t:[-1,6.5,17.3],f:62},aerial:{p:[24.83,120,127.14],t:[-0.2,5.4,4],f:48},viaduct:{p:[-51.07,10.31,38.93],t:[-14.9,10,21.8],f:56},interior:{p:[0.6,12,11],t:[0.2,0,-0.3],f:45},i_living:{p:[-0.5,1.5,1.91],t:[2.97,0.9,0.15],f:70},i_kitchen:{p:[-0.79,1.5,1.18],t:[3.41,1.1,2.96],f:70},i_bed1:{p:[-2.0,1.3,-0.85],t:[-2.41,0.8,-3.17],f:70},i_bed2:{p:[1.5,1.3,-1.6],t:[1.36,0.8,-3.62],f:70},i_bath:{p:[-2.08,1.55,3.83],t:[-3.02,0.9,2.88],f:80},i_hall:{p:[-0.65,1.5,4.15],t:[0.09,1.3,0.29],f:75},i_store:{p:[-1.09,1.5,1.32],t:[-3.0,1.0,1.32],f:80}};
window.cam=k=>{const v=P[k];C.position.fromArray(v.p);O.target.fromArray(v.t);C.fov=v.f;C.updateProjectionMatrix();O.update()};
// illustrative sun positions (elevation, azimuth from north, deg); not an ephemeris
const T={sunrise:[3,120,0xffb070,1.2,0.35],morning:[18,145,0xfff0d8,2.6,0.8],midday:[30,180,0xffffff,3.4,1],golden:[8,225,0xffc080,2.0,0.6],dusk:[-2,245,0xff9a6a,0.25,0.25],night:[-20,0,0x8090c0,0.04,0.05]};
let lampOn=false;window.tod=k=>{const [el,az,col,I,env]=T[k];const e=THREE.MathUtils.degToRad(Math.max(el,1)),a=THREE.MathUtils.degToRad(az);
 sun.position.set(200*Math.cos(e)*Math.sin(a),200*Math.sin(e),3+200*Math.cos(e)*Math.cos(a));sun.target.position.set(0,0,0);
 // three +z = blender -y = south; az measured from north => south (180) maps to +z
 sun.position.z=-200*Math.cos(e)*Math.cos(a);sun.color.set(col);sun.intensity=I;S.environmentIntensity=env;S.backgroundIntensity=Math.max(env,0.06);
 hemi.intensity=env*0.3;const n=(k=='night'||k=='dusk');lampG.children.forEach(l=>l.intensity=n?(k=='night'?60:25):0);lampOn=n;lampG.visible=n&&ext.visible;reshadow();R.toneMappingExposure=k=='night'?1.6:0.8;};
window.mode=k=>{const i=k=='i';ext.visible=!i;intr.visible=i;$('li').className=i?'':'x';$('le').className=i?'x':'';$('bi').className=i?'on':'';$('be').className=i?'':'on';$('presets').style.display=i?'none':'';$('ipresets').style.display=i?'':'none';sun.visible=!i;lampG.visible=!i&&lampOn;if(i)loadIntr();cam(i?'interior':'street');reshadow()};
window.ar=()=>{O.autoRotate=!O.autoRotate;kick();$('ba').className=O.autoRotate?'on':''};
const rs=()=>{const w=$('v').clientWidth,h=$('v').clientHeight;R.setSize(w,h);C.aspect=w/h;C.updateProjectionMatrix();kick()};addEventListener('resize',rs);if(window.ResizeObserver)new ResizeObserver(rs).observe($('v'));rs();
const q=new URLSearchParams(location.search);mode(q.get('m')||'e');if(q.get('cam'))cam(q.get('cam'));if(q.get('tod')){$('tod').value=q.get('tod')}tod($('tod').value);
let ceil=null,ft=[],lastT=0;
R.setAnimationLoop(t=>{if(document.hidden)return;if(O.enabled&&!fp&&!flying&&O.update())kick();if(flying||O.autoRotate)kick();if(dirty<=0){lastT=0;return}
 if(!ceil&&intr.children.length)intr.traverse(o=>{if(/^Ceiling/.test(o.name)&&o.isMesh)ceil=o});if(ceil)ceil.visible=C.position.y<2.95;R.render(S,C);dirty--;
 // adaptive resolution: if continuous motion runs below ~30 fps, step pixel ratio down (never below 1)
 if(lastT){ft.push(t-lastT);if(ft.length>=45){ft.sort((a,b)=>a-b);const med=ft[22];ft=[];if(med>34&&dpr>1){dpr=Math.max(1,dpr-0.25);R.setPixelRatio(dpr);rs()}}}lastT=t});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)kick()});
window.__ready=()=>done>=need&&!!envTex;window.__extReady=()=>extDone>=needExt&&!!envTex;window.__dpr=()=>dpr;

// ---- room menu: fly-in + first-person look ----
let fp=false,flying=false,lastExt={p:[-1.41,1.7,29.79],t:[0.2,8.5,9.8],f:70},yaw=0,pitch=0,curRoom=null;
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
function fly(v,dur,done){flying=true;O.enabled=false;const p0=C.position.clone(),t0=O.target.clone(),f0=C.fov,p1=new THREE.Vector3().fromArray(v.p),t1=new THREE.Vector3().fromArray(v.t),f1=v.f,st=performance.now();
 (function step(){const k=Math.min(1,(performance.now()-st)/dur),e=ease(k);C.position.lerpVectors(p0,p1,e);O.target.lerpVectors(t0,t1,e);C.fov=f0+(f1-f0)*e;C.updateProjectionMatrix();C.lookAt(O.target);if(k<1)requestAnimationFrame(step);else{flying=false;done&&done()}})()}
function enterFP(){fp=true;O.enabled=false;const d=O.target.clone().sub(C.position).normalize();yaw=Math.atan2(-d.x,-d.z);pitch=Math.asin(d.y);C.near=0.03;C.far=300;C.updateProjectionMatrix();applyLook();kick();$('fph').className=''}
function applyLook(){C.rotation.set(pitch,yaw,0,'YXZ');kick()}
function setRoomUI(r){document.querySelectorAll('#rooms button[data-r]').forEach(b=>b.className=b.dataset.r===r?'on':'');$('bx').className='';}
window.goRoom=r=>{if(flying)return;const wasExt=ext.visible;if(wasExt){lastExt={p:C.position.toArray(),t:O.target.toArray(),f:C.fov};mode('i')}
 if(fp){ /* room to room: rise to just under ceiling, then glide */ const mid={p:[(C.position.x+P[r].p[0])/2,2.6,(C.position.z+P[r].p[2])/2],t:P[r].t,f:P[r].f};fp=false;fly(mid,450,()=>fly(P[r],750,enterFP))}
 else fly(P[r],wasExt?1400:1400,enterFP);curRoom=r;setRoomUI(r)};
window.goDoll=()=>{if(flying)return;fp=false;$('fph').className='x';C.near=0.03;C.far=300;C.updateProjectionMatrix();fly(P.interior,1200,()=>{O.enabled=true;O.update()});setRoomUI(null)};
window.backExt=()=>{if(flying)return;fp=false;$('fph').className='x';curRoom=null;fly(P.interior,1000,()=>{mode('e');C.position.set(lastExt.p[0],lastExt.p[1]+40,lastExt.p[2]+40);O.target.fromArray(lastExt.t);C.near=0.1;C.far=2500;C.updateProjectionMatrix();fly(lastExt,1100,()=>{O.enabled=true;O.update()});document.querySelectorAll('#rooms button').forEach(b=>b.className=b.id=='bx'?'x':'')})};
const _mode=window.mode;window.mode=k=>{if(k==='e'&&ext.visible===false&&!flying){fp=false;$('fph').className='x';$('bx').className='x'}if(k==='i')$('bx').className='';else $('bx').className='x';O.enabled=true;C.near=k==='i'?0.03:0.1;C.far=k==='i'?300:2500;C.updateProjectionMatrix();document.body.classList.toggle('ext',k!=='i');_mode(k)};
document.body.classList.toggle('ext',!intr.visible);
// pointer look (mouse + touch drag), wheel / pinch FOV zoom
const el=R.domElement,pts=new Map();let pd0=0,fov0=70;
el.addEventListener('pointerdown',e=>{if(!fp)return;pts.set(e.pointerId,[e.clientX,e.clientY]);el.setPointerCapture(e.pointerId);if(pts.size==2){const a=[...pts.values()];pd0=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);fov0=C.fov}});
el.addEventListener('pointermove',e=>{if(!fp||!pts.has(e.pointerId))return;const pr=pts.get(e.pointerId);
 if(pts.size==1){const s=0.0042*C.fov/70;yaw+=(e.clientX-pr[0])*s;pitch=Math.max(-1.3,Math.min(1.3,pitch+(e.clientY-pr[1])*s));applyLook()}
 pts.set(e.pointerId,[e.clientX,e.clientY]);
 if(pts.size==2){const a=[...pts.values()];const d=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);if(pd0>0){C.fov=Math.max(30,Math.min(95,fov0*pd0/d));C.updateProjectionMatrix();kick()}}});
const up=e=>{pts.delete(e.pointerId);if(pts.size<2)pd0=0};el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);
el.addEventListener('wheel',e=>{if(!fp)return;e.preventDefault();C.fov=Math.max(30,Math.min(95,C.fov*(1+Math.sign(e.deltaY)*0.08)));C.updateProjectionMatrix();kick()},{passive:false});
window.__fp=()=>fp&&!flying;window.__flying=()=>flying;
window.__lookAt=(p,t,f)=>{C.position.fromArray(p);O.target.fromArray(t);if(f){C.fov=f;C.updateProjectionMatrix()}if(O.enabled)O.update();else C.lookAt(O.target);kick()};
window.__drawcalls=()=>R.info.render.calls;window.__tris=()=>R.info.render.triangles;
