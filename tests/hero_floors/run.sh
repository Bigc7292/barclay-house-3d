#!/bin/bash
# New hero GLB with Floor_* names. Never overwrites
# out/barclay_hero.glb, out/barclay_scene.blend or web/hero3.glb.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/tests/hero_floors/out"
mkdir -p "$OUT"
BLENDER="${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}"
BLEND="$ROOT/out/barclay_scene.blend"
OFF_BEFORE=$(stat -c %Y "$BLEND")
HERO_BEFORE=$(stat -c %Y "$ROOT/out/barclay_hero.glb")
WEB_BEFORE=$(stat -c %Y "$ROOT/web/hero3.glb")

# surroundings is required by make_mobile.sh / validate.sh; copy only, do not export over official.
cp -p "$ROOT/out/barclay_surroundings.glb" "$OUT/barclay_surroundings.glb"
BOUT="$OUT/" "$BLENDER" -b "$BLEND" --python tests/hero_floors/export.py

OFF_AFTER=$(stat -c %Y "$BLEND")
HERO_AFTER=$(stat -c %Y "$ROOT/out/barclay_hero.glb")
WEB_AFTER=$(stat -c %Y "$ROOT/web/hero3.glb")
if [ "$OFF_BEFORE" != "$OFF_AFTER" ] || [ "$HERO_BEFORE" != "$HERO_AFTER" ] || [ "$WEB_BEFORE" != "$WEB_AFTER" ]; then
  echo "BLOCK: official blend or hero/web GLB mtime changed"; exit 1
fi

OUT="$OUT" ./make_mobile.sh
MESHHEALTH=1 MESHHEALTH_BLEND="$BLEND" OUT="$OUT" ./validate.sh

# delivered filename: do not clobber official out/barclay_hero.glb
cp -p "$OUT/barclay_hero.glb" "$ROOT/out/barclay_hero_floors.glb"
ls -l "$ROOT/out/barclay_hero_floors.glb" "$OUT/barclay_hero.glb" "$OUT/mobile/barclay_hero_mobile.glb"

python3 tests/hero_floors/list_nodes.py
echo "HERO FLOORS EXPORT DONE"
