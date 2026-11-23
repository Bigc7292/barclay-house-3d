const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1024,height:640}});
await p.goto('https://barclay-house-viewer.vercel.app',{timeout:120000});await p.waitForTimeout(60000);
for(const c of ['street','facade']){await p.evaluate(c=>cam(c),c);await p.waitForTimeout(25000);await p.screenshot({path:`ext_${c}.png`,timeout:240000});}
await p.evaluate(()=>mode('i'));await p.waitForTimeout(60000);
for(const c of ['interior','i_living','i_kitchen','i_bed1','i_bed2','i_bath']){await p.evaluate(c=>cam(c),c);await p.waitForTimeout(25000);await p.screenshot({path:`int_${c}.png`,timeout:240000});console.log(c);}
await b.close();})();
