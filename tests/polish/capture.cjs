// Polish lane: headless screenshots of main viewer (twobed_v5) + Walk mode (twobed) at fixed interior presets; records console errors.
// Usage: node tests/polish/capture.cjs <outdir> [port]   (serves repo root itself)
const path=require('path'),fs=require('fs'),{spawn}=require('child_process');
const {chromium}=require('/workspace/barclay/.gltf/node_modules/playwright');
const ROOT=path.resolve(__dirname,'../..'),OUT=path.resolve(process.argv[2]||'renders/polish/web'),PORT=+(process.argv[3]||18517);
const CAMS=['i_living','i_bed1','i_bed2','i_bath','i_store'];
fs.mkdirSync(OUT,{recursive:true});
(async()=>{const srv=spawn('python3',['-m','http.server',String(PORT),'--bind','127.0.0.1'],{cwd:ROOT,stdio:'ignore'});await new Promise(r=>setTimeout(r,1200));
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const res={};
try{
 // main viewer
 {const c=await b.newContext({viewport:{width:1280,height:800}}),p=await c.newPage(),errs=[];
  p.on('console',m=>m.type()==='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push(String(e)));
  await p.goto(`http://127.0.0.1:${PORT}/web/index.html?lq=0&life=0&water=0`);
  await p.waitForFunction(()=>window.__ready&&window.__ready(),null,{timeout:300000});
  await p.evaluate(()=>mode('i'));
  for(const k of CAMS){await p.evaluate(k=>{cam(k);__kick&&__kick()},k);await p.waitForTimeout(2500);await p.screenshot({path:`${OUT}/viewer_${k}.png`,timeout:240000})}
  res.viewer={errors:errs};await c.close()}
 // walk mode
 {const c=await b.newContext({viewport:{width:1280,height:800}}),p=await c.newPage(),errs=[];
  p.on('console',m=>m.type()==='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push(String(e)));
  await p.goto(`http://127.0.0.1:${PORT}/web/floorplan3d/2bed.html`);
  await p.waitForFunction(()=>window.__fp3d&&window.__fp3d.ready,null,{timeout:300000});await p.waitForTimeout(1500);
  for(const k of CAMS){const ok=await p.evaluate(k=>{try{__fp3d.goRoom(k);return true}catch(e){return String(e)}},k);
   await p.waitForFunction(()=>!__fp3d.fly(),null,{timeout:30000}).catch(()=>{});await p.waitForTimeout(1200);await p.screenshot({path:`${OUT}/walk_${k}.png`,timeout:240000})}
  res.walk={errors:errs};await c.close()}
}finally{await b.close();srv.kill()}
fs.writeFileSync(`${OUT}/console.json`,JSON.stringify(res,null,1));console.log(JSON.stringify(res))})().catch(e=>{console.error('FAIL',e);process.exit(1)});
