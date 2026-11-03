const {chromium,devices}=require('/workspace/barclay/.gltf/node_modules/playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const c=await b.newContext({...devices['Galaxy S9+'],deviceScaleFactor:1});
for(const [f,o,n] of [['barclay_hero_mobile.glb','200deg 75deg auto','hero'],['barclay_surroundings_mobile.glb','200deg 55deg 600m','surroundings']]){
const p=await c.newPage();p.on('console',m=>m.type()=='error'&&console.log(n,m.text()));
await p.goto(`http://127.0.0.1:18473/view.html?f=${f}&o=${encodeURIComponent(o)}`);
try{await p.waitForFunction(()=>document.title,null,{timeout:120000});}catch(e){}
await p.waitForTimeout(4000);console.log(n,await p.title());
await p.screenshot({timeout:240000,path:`/workspace/barclay/web/shots/mobile_${n}.png`});}
await b.close();})();
