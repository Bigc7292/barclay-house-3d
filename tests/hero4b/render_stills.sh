#!/bin/bash
# r8b before (hero4) / after (hero4b) stills, 1920x1080 64 spp. Skips stills that already exist.
cd "$(dirname "$0")/../.."; B=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}; S=tests/hero4b/stills; mkdir -p $S
r(){ blend=$1; pre=$2; shift 2; for c in "$@"; do [ -f $S/${pre}_${c}_1920x1080.png ] && continue
  $B -b -y $blend -P tests/hero4/render_cams.py -- --out $S --prefix $pre --cams $c --res 1920x1080 --samples 64 2>&1 | grep RENDER; done; }
r out/barclay_hero4.blend before_hero4 shops_east shops_west
r out/barclay_hero4b.blend after_hero4b street entrance shops_east shops_west
echo ALL_DONE
