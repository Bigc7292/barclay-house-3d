#!/bin/bash
# Copy-test for trick #13. Does not touch official out/ GLBs or the official .blend.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/tests/props/out"
mkdir -p "$OUT"
BLENDER="${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}"
"$BLENDER" -b -P props_normalize.py
# validate exported GLBs (Khronos via gltf-transform)
export NODE_PATH="$ROOT/.gltf/node_modules"
rc=0
for f in "$ROOT"/assets/life/normalized/*.glb; do
  [ -f "$f" ] || continue
  echo "VALIDATE $f"
  "$ROOT/.gltf/node_modules/.bin/gltf-transform" validate "$f" 2>&1 | tail -8 || rc=1
done
python3 tests/props/score.py
# optional: LOD1 pass on a COPY of surroundings mobile, if present
if [ -f "$ROOT/out/barclay_surroundings.glb" ]; then
  mkdir -p "$OUT/surr"
  cp -p "$ROOT/out/barclay_surroundings.glb" "$OUT/surr/barclay_surroundings.glb"
  # do not touch official mobile; just report tri counts from kit.json
fi
[ $rc -eq 0 ]
echo "PROPS COPY-TEST DONE"
