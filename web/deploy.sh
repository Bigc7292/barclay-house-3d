#!/bin/bash
# Barclay House viewer deploy prep. SINGLE SOURCE: branch `barclay` of github.com/Bigc7292/barclay-house-3d, folder web/.
# Vercel project: barclay-house-viewer (team_DY4fBmwCbebV0AbJ7rKGf13W), production URL https://barclay-house-viewer.vercel.app
# Deploy method: Vercel connector (user-Vercel MCP): upload_file for each CHANGED file, then ONE create_deployment
#   {name/project: barclay-house-viewer, target: production, skipAutoDetectionConfirmation: "1", files: <manifest>}
# Files go at the SITE ROOT (index.html, app.js, ...). NEVER prefix with vercel-live/ (that caused a 404 outage on 2026-11-09).
# Usage: web/deploy.sh            -> fetch origin/barclay into /workspace/barclay-deploy, build, write manifest + b64 files
#        web/deploy.sh --local    -> use the web/ folder this script lives in (testing only)
# After deploy: curl -sI https://barclay-house-viewer.vercel.app/{,app.js,hero3.glb} must be 200, then run the Playwright check
#   node /workspace/perf/m.mjs https://barclay-house-viewer.vercel.app/ desktop|phone  (0 errors, 0 s404)
set -euo pipefail
OUT=/workspace/barclay-deploy-out
if [[ "${1:-}" == "--local" ]]; then W="$(cd "$(dirname "$0")" && pwd)"
else
  R=/workspace/barclay; D=/workspace/barclay-deploy
  git -C "$R" fetch -q origin barclay
  if [[ ! -d "$D" ]]; then git -C "$R" worktree add -q --detach --no-checkout "$D" origin/barclay; git -C "$D" sparse-checkout set --no-cone '/web/*'; fi
  git -C "$D" checkout -q --detach origin/barclay
  W="$D/web"; echo "Deploying origin/barclay @ $(git -C "$D" rev-parse --short HEAD)"
fi
cd "$W"
# rebuild the bundle from source (three.js + decoders are bundled locally; no CDN)
if [[ -x src/node_modules/.bin/esbuild ]]; then E=src/node_modules/.bin/esbuild; else E=/workspace/barclay/web/src/node_modules/.bin/esbuild; NODE_PATH=/workspace/barclay/web/src/node_modules; export NODE_PATH; fi
[[ -d src/node_modules ]] || ln -s /workspace/barclay/web/src/node_modules src/node_modules
(cd src && "../$E" app.js --bundle --minify --format=iife --legal-comments=eof --outfile=../app.js 2>&1 | tail -1) || (cd src && "$E" app.js --bundle --minify --format=iife --legal-comments=eof --outfile=../app.js)
FILES=(
  index.html app.js vercel.json apt02_fp.png env.hdr env_m.hdr
  hero3.glb hero_mo3.glb context_typed_opt.glb context_mo.glb ext7_street.glb ext7_street_o.glb
  twobed_v5.glb twobed_v5_m.glb twobed.glb twobed_m.glb
  tex/oak_n.jpg tex/oak_r.jpg tex/teddy_d.jpg tex/teddy_n.jpg tex/teddy_r.jpg tex/whitworth.jpg
  tex/oak_n_m.jpg tex/oak_r_m.jpg tex/teddy_d_m.jpg tex/teddy_n_m.jpg tex/teddy_r_m.jpg
  water/Water_1_M_Normal.jpg water/Water_2_M_Normal.jpg water/LICENSE-three.js.txt
  video/index.html video/barclay_exterior_step7.mp4 video/img/aerial.jpg video/img/compare_corner.jpg video/img/corner.jpg
  video/img/entrance.jpg video/img/front.jpg video/img/lintel.jpg video/img/pole.jpg
  floorplan3d/2bed.html floorplan3d/2bed.json vendor/floorplan-3d/LICENSE
  floorplan3d/vendor/three-r160/LICENSE floorplan3d/vendor/three-r160/build/three.module.js
  floorplan3d/vendor/three-r160/examples/jsm/loaders/GLTFLoader.js
  floorplan3d/vendor/three-r160/examples/jsm/controls/OrbitControls.js
  floorplan3d/vendor/three-r160/examples/jsm/controls/PointerLockControls.js
  floorplan3d/vendor/three-r160/examples/jsm/libs/meshopt_decoder.module.js
  floorplan3d/vendor/three-r160/examples/jsm/environments/RoomEnvironment.js
  floorplan3d/vendor/three-r160/examples/jsm/utils/BufferGeometryUtils.js
  floorplan3d/vendor/three-r160/examples/jsm/renderers/CSS2DRenderer.js
  floorplan3d/vendor/three-r160/examples/jsm/geometries/RoundedBoxGeometry.js
)
rm -rf "$OUT"; mkdir -p "$OUT/b64"
python3 - "$OUT" "${FILES[@]}" <<'P'
import sys,hashlib,base64,json,os
out=sys.argv[1];fs=sys.argv[2:];man=[];miss=[]
for f in fs:
    if not os.path.isfile(f): miss.append(f); continue
    b=open(f,'rb').read();h=hashlib.sha1(b).hexdigest()
    man.append({"file":f,"sha":h,"size":len(b)})   # top-level path, no prefix
    p=f"{out}/b64/{f.replace('/','__')}.b64";open(p,'w').write(base64.b64encode(b).decode())
if miss: print("MISSING:",miss); sys.exit(1)
assert not any(m["file"].startswith("vercel-live/") for m in man)
json.dump(man,open(f"{out}/manifest.json","w"))
print(f"{len(man)} files, {sum(m['size'] for m in man)/1e6:.1f} MB -> {out}/manifest.json")
print("Upload each with upload_file(teamId, xVercelDigest=sha, contentLength=size, requestBody=$file:"+out+"/b64/<path with / as __>.b64)")
print("Unchanged files (same sha as current production) can skip upload_file. Then create_deployment with files=manifest.json contents.")
P
