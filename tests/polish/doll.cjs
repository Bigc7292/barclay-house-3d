// Dollhouse/overview shots: main viewer goDoll() + walk mode goOver(); records console errors. Usage: node tests/polish/doll.cjs <outdir> [port]
const path=require('path'),fs=require('fs'),{spawn}=require('child_process');
const {chromium}=require(path.resolve(__dirname,'../../.gltf/node_modules/playwright'));
const ROOT=path.resolve(__dirname,'../..'),OUT=path.resolve(process.argv[2]||'renders/polish/doll'),PORT=+(process.argv[3]||18561);
fs.mkdirSync(OUT,{recursive:true});
(async()=>{const srv=spawn('python3',['-m','http.server',String(PORT),'--bind','127.0.0.1'],{cwd:ROOT,stdio:'ignore'});await new Promise(r=>setTimeout(r,1200));
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const res={};
try{{const c=await b.newContext({viewport:{width:1280,height:800}}),p=await c.newPage(),errs=[];p.on('console',m=>m.type()==='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(`http://127.0.0.1:${PORT}/web/index.html?lq=0&life=0&water=0`);await p.waitForFunction(()=>window.__ready&&window.__ready(),null,{timeout:400000});
 await p.evaluate(()=>{mode('i');goDoll()});await p.waitForTimeout(5000);await p.screenshot({path:`${OUT}/viewer_doll.png`,timeout:240000});res.viewer={errors:errs};await c.close()}
 {const c=await b.newContext({viewport:{width:1280,height:800}}),p=await c.newPage(),errs=[];p.on('console',m=>m.type()==='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(`http://127.0.0.1:${PORT}/web/floorplan3d/2bed.html`);await p.waitForFunction(()=>window.__fp3d&&window.__fp3d.ready,null,{timeout:300000});
 await p.evaluate(()=>__fp3d.goOver());await p.waitForTimeout(4000);await p.screenshot({path:`${OUT}/walk_over.png`,timeout:240000});res.walk={errors:errs};await c.close()}
}finally{await b.close();srv.kill()}
fs.writeFileSync(`${OUT}/console.json`,JSON.stringify(res,null,1));console.log(JSON.stringify(res))})().catch(e=>{console.error('FAIL',e);process.exit(1)});
