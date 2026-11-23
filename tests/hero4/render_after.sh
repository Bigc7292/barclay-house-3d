#!/bin/bash
cd "$(dirname "$0")/../.."; B=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}; S=tests/hero4/stills
while pgrep -f "prefix before_official" >/dev/null; do sleep 10; done
$B -b -y out/barclay_hero4.blend -P tests/hero4/render_cams.py -- --out $S --prefix after_hero4 --cams street,facade,entrance,viaduct,wsw_east --res 1920x1080 --samples 64 2>&1 | grep RENDER
$B -b -y out/barclay_hero4.blend -P tests/hero4/render_cams.py -- --out $S --prefix after_hero4 --cams street,hero --res 4096x2304 --samples 48 2>&1 | grep RENDER
echo ALL_DONE
