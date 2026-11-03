#!/bin/bash
# re-copy exterior bot's assets (read-only source) and compress for web
set -e; cd /workspace/barclay/web; G="npx -y @gltf-transform/cli@4"
cp /workspace/barclay/out/barclay_hero.glb src/hero_src.glb; cp /workspace/barclay/out/barclay_surroundings.glb src/sur_src.glb
$G optimize src/hero_src.glb hero.glb --compress meshopt --texture-compress webp --texture-size 2048 --simplify false
~/bvenv/bin/python ctx.py >/dev/null 2>&1; $G optimize src/sur_dec.glb context.glb --compress meshopt --texture-compress webp --texture-size 512 --simplify true --simplify-ratio 0.5 --simplify-error 0.001
ls -la hero.glb context.glb
