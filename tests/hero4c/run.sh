#!/bin/bash
# r8c hero4c replay: hero4b + BHERO4C (no lower RB shield on the oriel heads) + BSURR_R8 viaduct + BSURR_R8B shopfronts/lamps/tree pits.
# Writes NEW files only: out/barclay_hero4c.blend, out/barclay_hero4c.glb, out/mobile/barclay_hero4c_mobile.glb (+ tests/hero4c/*).
set -euo pipefail; cd "$(dirname "$0")/../.."; W=$PWD; B=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}; T=tests/hero4c
export BHERO4=1 BHERO4B=1 BHERO4C=1; mkdir -p $T/r8cout $T/exp
[ "${SKIP_BUILD:-0}" = 1 ] || BOUT=$T/r8cout $B -b -P build_scene.py -- --noexport > $T/build.log 2>&1
BSURR_R8=1 BSURR_R8B=1 BHERE=$W BSURR_BASE=$W/$T/r8cout $B -b -y $T/r8cout/barclay_scene.blend -P build_surroundings.py -- --layers all --save $W/$T/r8cout/hero4c_surr.blend > $T/surr.log 2>&1
cp $T/r8cout/hero4c_surr.blend out/barclay_hero4c.blend
BOUT=$W/$T/exp/ $B -b -y $T/r8cout/barclay_scene.blend -P export_glb.py > $T/export.log 2>&1
OUT=$T/exp ./make_mobile.sh > $T/mobile.log 2>&1
cp $T/exp/barclay_hero.glb out/barclay_hero4c.glb; cp $T/exp/mobile/barclay_hero_mobile.glb out/mobile/barclay_hero4c_mobile.glb
OUT=$T/exp MESHHEALTH=1 MESHHEALTH_BLEND=out/barclay_hero4c.blend ./validate.sh | tee $T/validate.log
