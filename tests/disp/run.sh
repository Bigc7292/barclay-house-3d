#!/bin/bash
# Copy-test for trick #8. Opens official out/barclay_scene.blend READ-ONLY.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/tests/disp/out"
mkdir -p "$OUT"
BLENDER="${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}"
BLEND="$ROOT/out/barclay_scene.blend"
if [ ! -f textures/stone/height.png ] || [ ! -f textures/terracotta/height.png ] || [ ! -f textures/brick/height.png ]; then
  python3 derive_height.py
fi
OFF_BEFORE=$(stat -c %Y "$BLEND")
BRES="${BRES:-960x540}" BSAMPLES="${BSAMPLES:-32}"
export BRES BSAMPLES BOUT="$OUT" BCAMS="${BCAMS:-Cam_Street}"
BDISP=0 "$BLENDER" -b "$BLEND" --python tests/disp/apply_and_render.py
BDISP=1 "$BLENDER" -b "$BLEND" --python tests/disp/apply_and_render.py
OFF_AFTER=$(stat -c %Y "$BLEND")
if [ "$OFF_BEFORE" != "$OFF_AFTER" ]; then
  echo "BLOCK: official blend mtime changed"; exit 1
fi
python3 tests/disp/score.py
echo "DISP COPY-TEST DONE"
