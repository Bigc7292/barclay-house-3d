import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
const require = createRequire(import.meta.url);
const { chromium } = require(resolve(dirname(fileURLToPath(import.meta.url)), '../../.gltf/node_modules/playwright'));
import { createServer, request as httpRequest } from 'http';
import { createReadStream, statSync, writeFileSync, mkdirSync } from 'fs';
import { extname, join } from 'path';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const OUT = join(ROOT, 'tests/hero3_floors/out');
const MIME = {
  '.html':'text/html', '.js':'text/javascript', '.mjs':'text/javascript',
  '.glb':'model/gltf-binary', '.wasm':'application/wasm', '.css':'text/css',
};

const mounts = {
  '/three/': join(ROOT, 'web/src/node_modules/three/'),
  '/meshopt/': join(ROOT, 'web/src/node_modules/three/examples/jsm/libs/'),
  '/hero3.glb': join(ROOT, 'web/hero3.glb'),
  '/hero3_floors.glb': join(OUT, 'barclay_hero3_floors.glb'),
  '/': join(ROOT, 'tests/hero3_floors/'),
};

function mapPath(url) {
  const u = url.split('?')[0];
  for (const [pref, dir] of Object.entries(mounts)) {
    if (u === pref || (pref.endsWith('/') && u.startsWith(pref)) || (!pref.endsWith('/') && u === pref)) {
      if (pref.endsWith('/')) return join(dir, u.slice(pref.length));
      return dir;
    }
  }
  return null;
}

const server = createServer((req, res) => {
  const p = mapPath(req.url);
  if (!p) { res.writeHead(404); res.end(); return; }
  try {
    const st = statSync(p);
    if (!st.isFile()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, {'Content-Type': MIME[extname(p)] || 'application/octet-stream'});
    createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const url = `http://127.0.0.1:${port}/compare.html`;

const browser = await chromium.launch({
  executablePath: process.env.CHROME || '/usr/bin/google-chrome-stable',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});
const page = await browser.newPage({ viewport: {width: 1600, height: 900} });
page.on('pageerror', (e) => console.error('PAGEERROR', e));
await page.goto(url, {waitUntil: 'networkidle', timeout: 60000});
await page.waitForFunction(() => window.__cmp && window.__cmp.done, {timeout: 30000});

const cams = ['street', 'facade', 'entrance', 'lintel'];
const models = [
  ['hero3', '/hero3.glb'],
  ['floors', '/hero3_floors.glb'],
];
mkdirSync(OUT, {recursive: true});
for (const [tag, src] of models) {
  await page.evaluate(async (s) => { await window.__cmp.load(s); }, src);
  // a couple frames to let textures settle
  await page.waitForTimeout(200);
  for (const cam of cams) {
    const data = await page.evaluate((c) => window.__cmp.render(c), cam);
    const buf = Buffer.from(data.split(',')[1], 'base64');
    const dest = join(OUT, `cmp_${tag}_${cam}.png`);
    writeFileSync(dest, buf);
    console.log('WROTE', dest, buf.length);
  }
}
await browser.close();
server.close();
console.log('COMPARE RENDER DONE');
