// Headless check for web/floorplan3d/2bed.html: console errors, door carve, room fly-to, joystick walk + collision, door toggle, screenshots.
const {chromium,devices}=require('/workspace/barclay/.gltf/node_modules/playwright');
const URL='http://127.0.0.1:18490/web/floorplan3d/2bed.html',OUT='/workspace/barclay/tests/floorplan3d/';
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const res={};
for(const [name,ctx] of [['desktop',{viewport:{width:1600,height:900}}],['phone',{...devices['Galaxy S9+'],deviceScaleFactor:1}]]){
 const c=await b.newContext(ctx),p=await c.newPage(),errs=[],net=[];
 p.on('console',m=>m.type()==='error'&&errs.push(m.text()));p.on('pageerror',e=>errs.push(String(e)));
 p.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1'))net.push(r.url())});
 await p.goto(URL);await p.waitForFunction(()=>window.__fp3d&&window.__fp3d.ready,null,{timeout:180000});await p.waitForTimeout(1500);
 const r={doors:await p.evaluate(()=>__fp3d.doors())};
 await p.screenshot({path:OUT+name+'_overview.png'});
 await p.click('button[data-room="i_living"]');await p.waitForFunction(()=>!__fp3d.fly()&&__fp3d.mode()==='walk',null,{timeout:30000});await p.waitForTimeout(500);
 r.afterFly={mode:await p.evaluate(()=>__fp3d.mode()),cam:await p.evaluate(()=>__fp3d.cam())};
 await p.screenshot({path:OUT+name+'_living_walk.png'});
 r.walk1s=await p.evaluate(()=>__walk(0,-1,1));               // joystick forward 1 s
 r.walk20s=await p.evaluate(()=>__walk(0,-1,20));             // keep pushing: must stop at a wall
 await p.evaluate(()=>__fp3d.goRoom('i_bed1'));await p.waitForFunction(()=>!__fp3d.fly(),null,{timeout:30000});
 await p.evaluate(()=>__toggleDoor(0));await p.waitForTimeout(1500);r.doorAfterToggle=await p.evaluate(()=>__fp3d.doors()[0]);
 await p.screenshot({path:OUT+name+'_bed1_door_toggled.png'});
 await p.evaluate(()=>{__fp3d.goOver();[1,2,3,4].forEach(i=>__toggleDoor(i))});await p.waitForFunction(()=>!__fp3d.fly(),null,{timeout:30000});await p.waitForTimeout(1500);
 r.allClosed=await p.evaluate(()=>__fp3d.doors().map(d=>d.open));await p.screenshot({path:OUT+name+'_overview_doors_closed.png'});
 r.errors=errs;r.externalRequests=net;res[name]=r;await c.close()}
console.log(JSON.stringify(res,null,1));require('fs').writeFileSync(OUT+'check_result.json',JSON.stringify(res,null,1));await b.close()})().catch(e=>{console.error('FAIL',e);process.exit(1)});
