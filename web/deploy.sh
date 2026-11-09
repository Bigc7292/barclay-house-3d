#!/bin/bash
# Deploy Barclay House viewer to Vercel (project barclay-house-viewer, production).
# Files are uploaded at site root (NOT under vercel-live/). Agent uses user-Vercel
# upload_file + create_deployment. Do not push to GitHub from this script.
set -euo pipefail
W=/workspace/barclay/web
# Prefer perf worktree if present (holds hero_mo/context_mo + vercel.json + app.js v38+)
if [[ -d /workspace/barclay-wt-perf/web ]]; then W=/workspace/barclay-wt-perf/web; fi
cd "$W"
FILES=(
  index.html app.js apt02_fp.png vercel.json
  hero.glb context.glb hero_m.glb context_m.glb hero_mo.glb context_mo.glb
  twobed.glb twobed_m.glb env.hdr env_m.hdr
  floorplan3d/2bed.html floorplan3d/2bed.json
  floorplan3d/vendor/three-r160/build/three.module.js
  floorplan3d/vendor/three-r160/LICENSE
  floorplan3d/vendor/three-r160/examples/jsm/loaders/GLTFLoader.js
  floorplan3d/vendor/three-r160/examples/jsm/controls/OrbitControls.js
  floorplan3d/vendor/three-r160/examples/jsm/controls/PointerLockControls.js
  floorplan3d/vendor/three-r160/examples/jsm/libs/meshopt_decoder.module.js
  floorplan3d/vendor/three-r160/examples/jsm/environments/RoomEnvironment.js
  floorplan3d/vendor/three-r160/examples/jsm/utils/BufferGeometryUtils.js
  floorplan3d/vendor/three-r160/examples/jsm/renderers/CSS2DRenderer.js
  floorplan3d/vendor/three-r160/examples/jsm/geometries/RoundedBoxGeometry.js
  vendor/floorplan-3d/LICENSE
)
echo "Deploy file set from $W:"
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then printf '  %s %s\n' "$(sha1sum "$f" | awk '{print $1}')" "$f ($(stat -c%s "$f") B)"
  else echo "  MISSING $f"; fi
done
