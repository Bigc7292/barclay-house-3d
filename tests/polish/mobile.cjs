// Mobile/desktop UI check: main viewer at several viewports; interior mode + a room; reports buttons off-screen + console errors.
// Usage: node tests/polish/mobile.cjs <outdir> [port]
const path=require('path'),fs=require('fs'),{spawn}=require('child_process');
const {chromium}=require(path.resolve(__dirname,'../../.gltf/node_modules/playwright'));
const ROOT=path.resolve(__dirname,'../..'),OUT=path.resolve(process.argv[2]||'renders/polish/mobile'),PORT=+(process.argv[3]||18541);
const VPS=[['desk',1280,800],['p390',390,844],['l390',844,390],['p360',360,740],['l360',740,360]];
fs.mkdirSync(OUT,{recursive:true});
(async()=>{const srv=spawn('python3',['-m','http.server',String(PORT),'--bind','127.0.0.1'],{cwd:ROOT,stdio:'ignore'});await new Promise(r=>setTimeout(r,1200));
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const res={};
try{for(const [k,w,h] of VPS){const mob=w<900;const c=await b.newContext({viewport:{width:w,height:h},isMobile:mob,hasTouch:mob,deviceScaleFactor:1}),p=await c.newPage(),errs=[];
 p.on('console',m=>m.type()==='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push(String(e)));
 await p.goto(`http://127.0.0.1:${PORT}/web/index.html?lq=0&life=0&water=0`);
 await p.waitForFunction(()=>window.__ready&&window.__ready(),null,{timeout:400000}).catch(e=>errs.push('ready timeout'));
 await p.screenshot({path:`${OUT}/${k}_ext.png`,timeout:240000});
 await p.evaluate(()=>{mode('i');goRoom('i_living')});await p.waitForTimeout(4000);
 const off=await p.evaluate(()=>{const W=innerWidth,H=innerHeight,o=[];const vis=r=>r.left>=-0.5&&r.top>=-0.5&&r.right<=W+0.5&&r.bottom<=H+0.5;
  for(const e of document.querySelectorAll('#bar button,#bar select,#rooms button,#rooms a')){if(e.offsetParent===null)continue;const sc=e.closest('#bar,#rooms');const scroll=sc&&sc.scrollWidth>sc.clientWidth+1;const r=(scroll?sc:e).getBoundingClientRect();if(!vis(r))o.push((e.textContent||e.id).trim()+` [${r.left|0},${r.top|0},${r.right|0},${r.bottom|0}]`)}
  const fv=id=>{const e=typeof id==='string'?document.querySelector(id):id;return !!(e&&e.offsetParent&&vis(e.getBoundingClientRect()))};
  const R=document.getElementById('rooms');const back0=fv('#bx');R.scrollLeft=R.scrollWidth;const back_after_scroll=fv('#bx');R.scrollLeft=0;
  return {off:o,back_visible:back0,back_visible_after_scroll:back_after_scroll,dollhouse_visible:fv('#ipresets button'),exterior_btn_visible:fv('#be')}});
 await p.screenshot({path:`${OUT}/${k}_int.png`,timeout:240000});
 res[k]={...off,errors:errs};console.log(k,JSON.stringify(res[k]));await c.close()}}
finally{await b.close();srv.kill()}
fs.writeFileSync(`${OUT}/mobile.json`,JSON.stringify(res,null,1))})().catch(e=>{console.error('FAIL',e);process.exit(1)});
