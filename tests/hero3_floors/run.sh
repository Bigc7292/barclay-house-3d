#!/bin/bash
# New hero GLB: live web/hero3.glb look + Floor_*/Door_*/Building names.
# Never overwrites out/barclay_hero.glb, out/barclay_hero_floors.glb,
# out/barclay_scene.blend or web/hero3.glb. Does not deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/tests/hero3_floors/out"
mkdir -p "$OUT"
BLEND="$ROOT/out/barclay_scene.blend"

stamp() { stat -c %Y "$1"; }
OFF_BEFORE=$(stamp "$BLEND")
HERO_BEFORE=$(stamp "$ROOT/out/barclay_hero.glb")
FLOORS_BEFORE=$(stamp "$ROOT/out/barclay_hero_floors.glb")
WEB_BEFORE=$(stamp "$ROOT/web/hero3.glb")

check_official() {
  local label="$1"
  if [ "$(stamp "$BLEND")" != "$OFF_BEFORE" ] \
    || [ "$(stamp "$ROOT/out/barclay_hero.glb")" != "$HERO_BEFORE" ] \
    || [ "$(stamp "$ROOT/out/barclay_hero_floors.glb")" != "$FLOORS_BEFORE" ] \
    || [ "$(stamp "$ROOT/web/hero3.glb")" != "$WEB_BEFORE" ]; then
    echo "BLOCK: official blend or hero/floors/web GLB mtime changed ($label)"
    exit 1
  fi
}

export NODE_PATH="$ROOT/.gltf/node_modules"
GT="$ROOT/.gltf/node_modules/.bin/gltf-transform"

# Decode live hero3 (meshopt + quantized) so the splitter can read raw verts.
"$GT" copy "$ROOT/web/hero3.glb" "$OUT/hero3_copy.glb"
"$GT" dequantize "$OUT/hero3_copy.glb" "$OUT/hero3_decoded.glb"

python3 tests/hero3_floors/build_hero3_floors.py \
  "$OUT/hero3_decoded.glb" \
  "$OUT/barclay_hero3_floors.glb"

# validate.sh / make_mobile.sh expect $OUT/barclay_hero.glb
cp -p "$OUT/barclay_hero3_floors.glb" "$OUT/barclay_hero.glb"
# surroundings is required by those scripts; copy only, do not export over official.
cp -p "$ROOT/out/barclay_surroundings.glb" "$OUT/barclay_surroundings.glb"

check_official "after build"

OUT="$OUT" ./make_mobile.sh
MESHHEALTH=1 MESHHEALTH_BLEND="$BLEND" OUT="$OUT" ./validate.sh

# delivered filename: do not clobber official exports or web/hero3.glb
cp -p "$OUT/barclay_hero3_floors.glb" "$ROOT/out/barclay_hero3_floors.glb"

check_official "after copy to out/"

python3 tests/hero3_floors/list_nodes.py
if [ "${SKIP_COMPARE:-0}" != 1 ]; then
  node tests/hero3_floors/compare.mjs
  python3 tests/hero3_floors/compare_diff.py
fi

ls -l "$ROOT/out/barclay_hero3_floors.glb" \
  "$OUT/barclay_hero3_floors.glb" \
  "$OUT/mobile/barclay_hero_mobile.glb"
echo "HERO3 FLOORS EXPORT DONE"
