const {chromium}=require('playwright');const http=require('http'),fs=require('fs'),path=require('path');
const s=http.createServer((q,r)=>{const p=path.join(__dirname,decodeURIComponent(q.url.split('?')[0]));fs.readFile(p,(e,d)=>{if(e){r.writeHead(404);return r.end()}r.writeHead(200,{'Content-Type':p.endsWith('.js')?'text/javascript':p.endsWith('.html')?'text/html':'model/gltf-binary'});r.end(d)})}).listen(8771,async()=>{
const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
for(const f of process.argv.slice(2)){const pg=await b.newPage({viewport:{width:412,height:846}});const t0=Date.now();await pg.on('console',m=>m.type()==='error'&&console.log('  console:',m.text().slice(0,200)));await pg.goto('http://localhost:8771/view.html?f='+f);
try{await pg.waitForFunction(()=>document.title==='LOADED'||document.title==='ERR',null,{timeout:90000})}catch(e){}
const t=await pg.title();await pg.waitForTimeout(1500);await pg.screenshot({path:'shot_'+f+'.png'});console.log(f,t,(Date.now()-t0)+'ms');await pg.close()}
await b.close();s.close()});
