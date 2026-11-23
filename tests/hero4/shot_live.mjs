import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require('../../.gltf/node_modules/playwright');
const b = await chromium.launch({executablePath:'/usr/bin/google-chrome-stable',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p = await b.newPage({viewport:{width:1600,height:900}});
await p.goto(process.argv[2],{timeout:120000});
await p.waitForTimeout(45000);
await p.screenshot({path:process.argv[3]});
await b.close();
