#!/bin/bash
# before/after stills for r8. Read-only on both blends.
cd "$(dirname "$0")/../.."; B=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}; S=tests/hero4/stills
$B -b -y out/barclay_scene.blend -P tests/hero4/render_cams.py -- --out $S --prefix before_official --cams street,facade,entrance,viaduct --res 1920x1080 --samples 64 2>&1 | grep RENDER
$B -b -y out/barclay_hero4.blend -P tests/hero4/render_cams.py -- --out $S --prefix after_hero4 --cams street,facade,entrance,viaduct,wsw_east --res 1920x1080 --samples 64 2>&1 | grep RENDER
$B -b -y out/barclay_hero4.blend -P tests/hero4/render_cams.py -- --out $S --prefix after_hero4 --cams hero,street --res 4096x2304 --samples 128 2>&1 | grep RENDER
echo ALL_DONE
