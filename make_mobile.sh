#!/bin/bash
# Re-run after hero/surroundings re-export. Free tools: gltf-transform + sharp + meshoptimizer (no Draco/meshopt/KTX2 in output).
set -e; cd "$(dirname "$(readlink -f "$0")")"; O=${OUT:-out}   # OUT=tests/x/out ./make_mobile.sh for test exports
[ -d .gltf/node_modules/@gltf-transform/functions ] || npm i --no-save --prefix .gltf @gltf-transform/core@4 @gltf-transform/functions@4 @gltf-transform/extensions@4 @gltf-transform/cli@4 sharp meshoptimizer gltf-validator playwright
M=$O/mobile; mkdir -p $M/src; cp -p $O/barclay_hero.glb $O/barclay_surroundings.glb $M/src/
export NODE_PATH=$PWD/.gltf/node_modules
cp make_mobile.mjs .gltf/make_mobile.mjs
node .gltf/make_mobile.mjs $M/src/barclay_hero.glb $M/barclay_hero_mobile.glb 1024 0 1
node .gltf/make_mobile.mjs $M/src/barclay_surroundings.glb $M/barclay_surroundings_mobile.glb 512 400 ${SURR_RATIO:-0.5}
for f in $M/*_mobile.glb; do .gltf/node_modules/.bin/gltf-transform validate $f 2>&1 | tail -6; done
ls -l $M/*.glb
