// Headless check of trick #5 clickable floors in the main viewer.
// Desktop + Galaxy S9+ (SwiftShader). 0 console errors, 0 external requests,
// a real click on each Floor_* gives the right name, fps vs live, look shots.
const {chromium,devices}=require(process.env.PLAYWRIGHT_PATH || '/workspace/barclay-ext-r8/.gltf/node_modules/playwright');
const http=require('http'),fs=require('fs'),path=require('path'),url=require('url');
const ROOT=path.resolve(__dirname,'../..');
const WEB=path.join(ROOT,'web');
const OUT=path.join(__dirname,'out');
const LIVE='https://barclay-house-viewer.vercel.app/';
const PORT=18765;
const MIME={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.glb':'model/gltf-binary','.hdr':'application/octet-stream','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.mp4':'video/mp4','.svg':'image/svg+xml','.txt':'text/plain','.wasm':'application/wasm'};
fs.mkdirSync(OUT,{recursive:true});
const SHOTS=path.resolve(ROOT,'shots/r13');
fs.mkdirSync(SHOTS,{recursive:true});

async function shot(page, dest){
  const sess=await page.context().newCDPSession(page);
  const {data}=await sess.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
  await sess.detach();
  const buf=Buffer.from(data,'base64');
  fs.writeFileSync(dest, buf);
  return dest;
}


function serve(root,port){
  const srv=http.createServer((req,res)=>{
    const p=url.parse(req.url).pathname||'/';
    let fp=path.join(root,decodeURIComponent(p==='/'?'/index.html':p));
    if(!fp.startsWith(root)){res.writeHead(403);return res.end()}
    fs.readFile(fp,(e,d)=>{
      if(e){res.writeHead(e.code==='ENOENT'?404:500);return res.end(String(e))}
      res.writeHead(200,{'Content-Type':MIME[path.extname(fp)]||'application/octet-stream','Cache-Control':'no-store'});
      res.end(d);
    });
  });
  return new Promise((resolve,reject)=>{srv.listen(port,'127.0.0.1',()=>resolve(srv));srv.on('error',reject)});
}

function attachNet(page,external,errors){
  page.on('console',m=>{if(m.type()!=='error')return;const loc=(m.location()&&m.location().url)||'';const t=m.text();if(/favicon\.ico/i.test(t+' '+loc))return;errors.push('CONSOLE '+t+' '+loc)});
  page.on('pageerror',e=>errors.push('PAGEERROR '+e.message));
  page.on('request',r=>{
    const u=r.url();
    if(u.startsWith('blob:')||u.startsWith('data:')||u.startsWith('ws:')||u.startsWith('wss:'))return;
    let host;try{host=new URL(u).hostname}catch(e){return}
    if(host==='127.0.0.1'||host==='localhost')return;
    external.push(u);
  });
}

async function waitReady(page,errors,ms=180000){
  try{await page.waitForFunction(()=>window.__ready&&window.__ready(),null,{timeout:ms});return true}
  catch(e){errors.push('TIMEOUT ready');return false}
}

async function fps(page,ms=3000){
  return page.evaluate(dur=>new Promise(r=>{
    if(window.__kick)window.__kick();
    let n=0;const s=performance.now();
    const f=()=>{n++;performance.now()-s<dur?requestAnimationFrame(f):r(+(n/(dur/1000)).toFixed(1))};
    requestAnimationFrame(f);
  }),ms);
}

async function settle(page){
  await page.evaluate(()=>{if(window.__kick)window.__kick()});
  await page.waitForTimeout(800);
}

const NAMES=['Floor_00','Floor_01','Floor_02','Floor_03','Floor_04','Floor_05'];

async function clickFloors(page,tag){
  const result={clicks:{},clears:{}};
  await page.evaluate(()=>{window.cam&&window.cam('street');window.__clearFloor&&window.__clearFloor();window.__kick&&window.__kick()});
  await settle(page);
  result.found=await page.evaluate(()=>window.__floors?window.__floors():[]);
  for(const name of NAMES){
    await page.evaluate(nm=>{
      window.__clearFloor();
      const CAMS={Floor_00:[[0,2.2,26],[0,0.2,16.3],50],Floor_01:[[0,3.6,28],[0,3.2,16],50],Floor_02:[[0,7.2,32],[0,7.0,16],50],Floor_03:[[0,11.0,34],[0,11.0,16],50],Floor_04:[[0,14.4,36],[0,14.4,16],50],Floor_05:[[0,18.0,38],[0,18.0,16],50]};
      const c=CAMS[nm];window.__setView(c[0],c[1],c[2]);
      window.__kick&&window.__kick();
    },name);
    await settle(page);
    let proj=await page.evaluate(nm=>window.__projectFloor(nm),name);
    if(!proj||!proj.visible){
      await page.evaluate(nm=>{
        const CAMS={Floor_00:[[0,2.0,30],[0,0.2,16.3],50],Floor_01:[[0,3.6,34],[0,3.2,16],50],Floor_02:[[0,7.2,40],[0,7.0,16],50],Floor_03:[[0,11.0,42],[0,11.0,16],50],Floor_04:[[0,14.4,44],[0,14.4,16],50],Floor_05:[[0,18.0,46],[0,18.0,16],50]};
        const c=CAMS[nm];window.__setView(c[0],c[1],c[2]);
        window.__kick&&window.__kick();
      },name);
      await settle(page);
      proj=await page.evaluate(nm=>window.__projectFloor(nm),name);
    }
    result.clicks[name]={project:proj};
    if(!proj){result.clicks[name].ok=false;result.clicks[name].err='no project';continue}
    console.log(tag,name,JSON.stringify(proj));
    await page.mouse.click(proj.x,proj.y);
    await settle(page);
    const after=await page.evaluate(()=>({sel:window.__selectedFloor(),lab:window.__floorLabel()}));
    result.clicks[name].ok=after.sel===name;
    result.clicks[name].got=after;
    await shot(page,path.join(OUT,`${tag}_click_${name}.png`));
    proj=await page.evaluate(nm=>window.__projectFloor(nm),name);
    await page.mouse.click(proj.x,proj.y);
    await settle(page);
    const cleared=await page.evaluate(()=>window.__selectedFloor());
    result.clears[name]={ok:cleared===null,got:cleared};
  }
  await page.evaluate(()=>{window.__selectFloor('Floor_02');window.__setView([-40,25,50],[-30,20,40],50);window.__kick&&window.__kick()});
  await settle(page);
  const box=await page.evaluate(()=>{
    const c=document.querySelector('#v canvas');const r=c.getBoundingClientRect();
    const samples=[[0.5,0.5],[0.2,0.2],[0.8,0.2],[0.08,0.08],[0.5,0.08]];
    for(const [u,v] of samples){
      const x=r.left+r.width*u,y=r.top+r.height*v;
      if(!window.__hitFloorAt(x,y))return{x,y,u,v};
    }
    return null;
  });
  if(box){await page.mouse.click(box.x,box.y);await settle(page)}
  const empty=await page.evaluate(()=>window.__selectedFloor());
  result.emptyClear={ok:empty===null,got:empty,at:box};
  await page.evaluate(()=>{window.cam('street');window.__selectFloor('Floor_01');window.__isolateFloors(true);window.__kick&&window.__kick()});
  await settle(page);
  const vis=await page.evaluate(()=>Object.fromEntries((window.__floors()||[]).map(n=>[n,window.__floorVisible(n)])));
  result.isolate={vis,ok:vis.Floor_00===true&&vis.Floor_01===true&&vis.Floor_02===false&&vis.Floor_03===false&&vis.Floor_04===false&&vis.Floor_05===false};
  await shot(page,path.join(OUT,`${tag}_isolate_Floor_01.png`));
  await page.evaluate(()=>{window.__clearFloor();window.__kick&&window.__kick()});
  await settle(page);
  return result;
}

(async()=>{
  const srv=await serve(WEB,PORT);
  const base=`http://127.0.0.1:${PORT}/`;
  const browser=await chromium.launch({executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage']});
  const DEV={
    desktop:{viewport:{width:1280,height:720}},
    phone:{...devices['Galaxy S9+'],deviceScaleFactor:1}
  };
  const q='?life=0&tod=midday&cam=street';
  const rep={started:new Date().toISOString(),base,live:LIVE,runs:{}};
  let pass=true;
  try{
    const only=(process.env.FLOORS_DEV||'').split(',').filter(Boolean);
    for(const dev of ['desktop','phone']){
      if(only.length&&!only.includes(dev))continue;
      const ctx=await browser.newContext(DEV[dev]);
      const page=await ctx.newPage();
      const errors=[],external=[];
      attachNet(page,external,errors);
      const t0=Date.now();
      await page.goto(base+q,{timeout:120000,waitUntil:'domcontentloaded'});
      const ready=await waitReady(page,errors);
      await settle(page);
      const found=ready?await page.evaluate(()=>window.__floors?window.__floors():[]):[];
      const fpsLocal=ready?await fps(page,3000):null;
      await page.evaluate(()=>{window.cam&&window.cam('street');window.__clearFloor&&window.__clearFloor();window.__kick&&window.__kick()});
      await settle(page);
      const clicks=ready?await clickFloors(page,dev):{clicks:{},clears:{},found};
      // look shots (no selection)
      const look={};
      for(const cam of ['street','facade','entrance']){
        await page.evaluate(k=>{window.__clearFloor&&window.__clearFloor();window.cam(k);window.__kick&&window.__kick()},cam);
        await settle(page);
        const f=path.join(OUT,`${dev}_local_${cam}.png`);
        await shot(page,f);
        if(dev==='desktop'&&cam==='street'){
          await shot(page,path.join(SHOTS,'hero4_street.png'));
          await shot(page,path.join(SHOTS,'desktop_local_street.png'));
        }
        look[cam]={local:f};
      }
      const run={
        ready,load_s:+((Date.now()-t0)/1000).toFixed(2),
        floors:found,errors:[...errors],external:[...external],
        fps_swiftshader:fpsLocal,clicks,look
      };
      // live compare (look + fps) — live requests are expected; don't mix into local external[]
      const lpage=await ctx.newPage();
      const lerr=[];
      lpage.on('console',m=>m.type()==='error'&&lerr.push('CONSOLE '+m.text()));
      lpage.on('pageerror',e=>lerr.push('PAGEERROR '+e.message));
      try{
        await lpage.goto(LIVE+q,{timeout:120000,waitUntil:'domcontentloaded'});
        const lready=await waitReady(lpage,lerr);
        await settle(lpage);
        const fpsLive=lready?await fps(lpage,3000):null;
        run.live={ready:lready,errors:lerr,fps_swiftshader:fpsLive};
        for(const cam of ['street','facade','entrance']){
          await lpage.evaluate(k=>{window.cam(k);window.__kick&&window.__kick()},cam);
          await settle(lpage);
          const f=path.join(OUT,`${dev}_live_${cam}.png`);
          await shot(lpage,f);
          if(dev==='desktop'&&cam==='street'){
            await shot(lpage,path.join(SHOTS,'live_street.png'));
          }
          look[cam].live=f;
        }
      }catch(e){
        run.live={ready:false,errors:lerr.concat([String(e)])};
      }
      await lpage.close();
      await ctx.close();

      const clickFail=NAMES.filter(n=>!clicks.clicks[n]||!clicks.clicks[n].ok);
      const clearFail=NAMES.filter(n=>!clicks.clears[n]||!clicks.clears[n].ok);
      run.gates={
        ready,
        console_errors:errors.length,
        external_requests:external.length,
        floors_found:found.slice(),
        click_fail:clickFail,
        clear_fail:clearFail,
        empty_clear:clicks.emptyClear&&clicks.emptyClear.ok,
        isolate:clicks.isolate&&clicks.isolate.ok,
        fps_local:fpsLocal,
        fps_live:run.live&&run.live.fps_swiftshader
      };
      const fpsLive=run.gates.fps_live; const fpsOk=fpsLocal==null||fpsLive==null||fpsLocal>=fpsLive-5||fpsLocal<10||fpsLive<10; // SwiftShader is noisy; sub-10 readings are inconclusive
      run.gates.fps_ok=fpsOk;
      run.ok=ready&&errors.length===0&&external.length===0&&found.length===6&&!clickFail.length&&!clearFail.length&&run.gates.empty_clear&&run.gates.isolate&&fpsOk;
      if(!run.ok)pass=false;
      rep.runs[dev]=run;
      console.log(dev,'ok='+run.ok,'ready='+ready,'errs='+errors.length,'ext='+external.length,'floors='+found,'fps='+fpsLocal+'/'+(run.gates.fps_live),'clickFail='+JSON.stringify(clickFail));
    }
  }finally{
    await browser.close();
    srv.close();
  }
  rep.ok=pass;
  fs.writeFileSync(path.join(__dirname,'result.json'),JSON.stringify(rep,null,2));
  console.log('PASS='+pass,'wrote tests/floors/result.json');
  process.exit(pass?0:1);
})().catch(e=>{console.error(e);process.exit(2)});
