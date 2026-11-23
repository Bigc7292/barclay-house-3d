#!/bin/bash
# Copy-test for trick #12. Opens official out/barclay_scene.blend READ-ONLY
# (scripts never save). Never writes official out/ GLBs or stills.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/tests/weather2/out"
mkdir -p "$OUT"
BLENDER="${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}"
BLEND="$ROOT/out/barclay_scene.blend"
OFF_BEFORE=$(stat -c %Y "$BLEND")
BRES="${BRES:-960x540}" BSAMPLES="${BSAMPLES:-64}"
export BRES BSAMPLES BOUT="$OUT"
BWEATHER2=0 "$BLENDER" -b "$BLEND" --python tests/weather2/apply_and_render.py
BWEATHER2=1 "$BLENDER" -b "$BLEND" --python tests/weather2/apply_and_render.py
OFF_AFTER=$(stat -c %Y "$BLEND")
if [ "$OFF_BEFORE" != "$OFF_AFTER" ]; then
  echo "BLOCK: official blend mtime changed"; exit 1
fi
python3 tests/weather2/score.py
echo "WEATHER2 COPY-TEST DONE"
