// Headless check for tests/accessible/2bed_overlay.html (trick #21).
const {chromium,devices}=require('/workspace/barclay/.gltf/node_modules/playwright');
const fs=require('fs');
const path=require('path');
const URL='http://127.0.0.1:18491/tests/accessible/2bed_overlay.html';
const OUT='/workspace/barclay/tests/accessible/';
const py=JSON.parse(fs.readFileSync(path.join(OUT,'python_result.json'),'utf8'));
const pct=(a,b)=>b===0&&a===0?0:Math.abs(a-b)/Math.max(Math.abs(b),1e-9)*100;
(async()=>{
  const b=await chromium.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-setuid-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const res={python: {reachable_m2: py.reachable_m2, rooms: py.rooms, hide_Bed1_navy: py.hide_Bed1_navy}};
  for(const [name,ctx] of [['desktop',{viewport:{width:1600,height:900}}],['phone',{...devices['Galaxy S9+'],deviceScaleFactor:1}]]){
    const c=await b.newContext(ctx), p=await c.newPage(), errs=[], net=[];
    p.on('console',m=>m.type()==='error'&&errs.push(m.text()));
    p.on('pageerror',e=>errs.push(String(e)));
    p.on('request',r=>{const u=r.url(); if(!(u.startsWith('http://127.0.0.1')||u.startsWith('blob:http://127.0.0.1')||u.startsWith('data:'))) net.push(u)});
    await p.goto(URL);
    await p.waitForFunction(()=>window.__fp3d&&window.__fp3d.ready&&window.__access&&window.__access.ready,null,{timeout:180000});
    await p.waitForTimeout(500);
    // baseline compute (warms raster); then the timed hide-bed recompute
    const base=await p.evaluate(()=>__access.compute([]));
    const hide=await p.evaluate(()=>__access.hide('Bed1_navy', true));
    await p.waitForTimeout(400);
    await p.screenshot({path:OUT+name+'_overlay_bed1_hidden.png'});
    const reset=await p.evaluate(()=>__access.compute([]));
    await p.waitForTimeout(300);
    await p.screenshot({path:OUT+name+'_overlay.png'});
    const r={
      errors:errs, externalRequests:net,
      base, hide,
      reset_reachable_m2: reset.reachable_m2,
      reachable_m2: base.reachable_m2,
      vs_python_pct: pct(base.reachable_m2, py.reachable_m2),
      within_1pct: pct(base.reachable_m2, py.reachable_m2)<=1,
      reachable_le_63: !!base.reachable_le_sourced && base.reachable_m2<=63,
      hide_bed_raises_room: hide.rooms.i_bed1.reachable_m2 > base.rooms.i_bed1.reachable_m2,
      recompute_ms: hide.recompute_ms,
      recompute_under_50ms: hide.recompute_ms<50,
      rooms: base.rooms,
      zero_console_errors: errs.length===0,
      zero_external_requests: net.length===0
    };
    r.pass = r.zero_console_errors && r.zero_external_requests && r.within_1pct && r.reachable_le_63 && r.hide_bed_raises_room && r.recompute_under_50ms;
    res[name]=r;
    await c.close();
  }
  const pass=res.desktop.pass && res.phone.pass;
  res.verdict= pass ? 'CERTIFIED' : 'REJECTED';
  res.criteria={
    desktop: {console:res.desktop.errors.length, external:res.desktop.externalRequests, within_1pct:res.desktop.within_1pct, le_63:res.desktop.reachable_le_63, hide_bed:res.desktop.hide_bed_raises_room, ms:res.desktop.recompute_ms},
    phone: {console:res.phone.errors.length, external:res.phone.externalRequests, within_1pct:res.phone.within_1pct, le_63:res.phone.reachable_le_63, hide_bed:res.phone.hide_bed_raises_room, ms:res.phone.recompute_ms}
  };
  fs.writeFileSync(OUT+'result.json', JSON.stringify(res,null,2)+'\n');
  console.log(JSON.stringify({verdict:res.verdict, criteria:res.criteria, reachable:res.desktop.reachable_m2, rooms:res.desktop.rooms, hide_ms:[res.desktop.recompute_ms,res.phone.recompute_ms], errors:{d:res.desktop.errors,p:res.phone.errors}, net:{d:res.desktop.externalRequests,p:res.phone.externalRequests}},null,2));
  await b.close();
  process.exit(pass?0:0); // always exit 0 so we can record a REJECTED run
})().catch(e=>{console.error('FAIL',e); process.exit(1)});
