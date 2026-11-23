#!/bin/bash
# r8 hero4 replay. Writes only tests/hero4/* and NEW files out/barclay_hero4.blend, out/barclay_hero4.glb,
# out/mobile/barclay_hero4_mobile.glb. Never touches out/barclay_hero.glb, out/barclay_scene.blend, web/hero3.glb, *_floors.glb.
set -euo pipefail; cd "$(dirname "$0")/../.."; W=$PWD; B=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}; T=tests/hero4
mkdir -p $T/r8out $T/exp
BHERO4=1 BOUT=$T/r8out BRES=1920x1080 BSAMPLES=64 $B -b -P build_scene.py -- --noexport > $T/build_hero4.log 2>&1
BHERO4=1 BSURR_R8=1 BHERE=$W BSURR_BASE=$W/$T/r8out $B -b -y $T/r8out/barclay_scene.blend -P build_surroundings.py -- --layers all --save $W/$T/r8out/hero4_surr.blend > $T/surr.log 2>&1
cp $T/r8out/hero4_surr.blend out/barclay_hero4.blend
BHERO4=1 BOUT=$W/$T/exp/ $B -b -y $T/r8out/barclay_scene.blend -P export_glb.py > $T/export.log 2>&1
OUT=$T/exp ./make_mobile.sh > $T/mobile.log 2>&1
cp $T/exp/barclay_hero.glb out/barclay_hero4.glb; mkdir -p out/mobile; cp $T/exp/mobile/barclay_hero_mobile.glb out/mobile/barclay_hero4_mobile.glb
OUT=$T/exp MESHHEALTH=1 MESHHEALTH_BLEND=out/barclay_hero4.blend ./validate.sh | tee $T/validate.log
