// Headless load of web/ (before = main bundle, after = branch bundle): console errors + screenshots + Water2 stats. Free: Playwright + SwiftShader.
const {chromium,devices}=require('/workspace/barclay/.gltf/node_modules/playwright');const fs=require('fs');
const O='/workspace/barclay-wt-streetwater/tests/streetwater/';const B='http://127.0.0.1:18491/';
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const rep={};
const RUNS=[['aftercut','_cut/index.html','desktop','canal','&lq=1'],['after','index.html','desktop','canal','&lq=1']];
const DEV={desktop:{viewport:{width:1280,height:720}},mobile:{...devices['Galaxy S9+'],deviceScaleFactor:1}};
for(const [tag,page,dev,cam,xq] of RUNS){const ctxo=DEV[dev];
 const c=await b.newContext(ctxo),p=await c.newPage(),errs=[];p.on('console',m=>m.type()=='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push('PAGEERROR '+e.message));
 const t0=Date.now();await p.goto(B+page+'?cam='+cam+'&tod=midday'+xq);let ready=false;
 try{await p.waitForFunction(()=>window.__ready&&window.__ready(),null,{timeout:240000});ready=true}catch(e){errs.push('TIMEOUT ready')}
 if(cam!=='street')await p.evaluate(k=>window.cam(k),cam);await p.waitForTimeout(3000);
 const fps=await p.evaluate(()=>new Promise(r=>{let n=0;const s=performance.now();const f=()=>{n++;performance.now()-s<3000?requestAnimationFrame(f):r(+(n/3).toFixed(1))};requestAnimationFrame(f)}));
 const w=await p.evaluate(()=>window.__water?window.__water():null),sun=await p.evaluate(()=>window.__sunPos?window.__sunPos(15.5):null);
 const f=`${O}web_${tag}_${dev}_${cam}.png`;await p.screenshot({path:f,timeout:900000});
 rep[`${tag}_${dev}_${cam}`]={ready,load_s:(Date.now()-t0)/1000,fps_swiftshader:fps,errors:errs,water:w,sun_midday:sun,shot:f};fs.writeFileSync(O+'web_check_canal.json',JSON.stringify(rep,null,1));console.log(tag,dev,cam,ready,errs.length,'errors',fps,'fps',JSON.stringify(w));await c.close()}
fs.writeFileSync(O+'web_check_canal.json',JSON.stringify(rep,null,1));await b.close()})();
