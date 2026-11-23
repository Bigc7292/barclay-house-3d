#!/bin/bash
# r8c step 1 replay: solve Cam_Match_geograph on the hero4b surroundings blend, render it, aligned re-score.
set -e; B=${B:-/home/box/apps/blender-4.2.3-linux-x64/blender}; cd "$(dirname "$0")/../.."
G=${G:-/workspace/hero4c_scratch/geomatch.blend}   # scratch copy (64 MB, not committed)
$B -b -y tests/hero4b/r8bout/hero4b_surr.blend -P camera_match.py -- --ref refs/critic1/real_geograph.jpg --points tests/geograph_points.json \
   --cam Cam_Match_geograph --clip-start 4 --render tests/hero4c/geomatch_test.png --scale 0.5 --samples 16 --save "$G"
$B -b -y "$G" -P tests/hero4/render_cams.py -- --out tests/hero4c/match --prefix hero4b --cams Cam_Match_geograph --res 2048x1536 --samples 32
$B -b -y "$G" -P tests/hero4/render_cams.py -- --out tests/hero4c/match --prefix hero4b_whitebars --cams Cam_Match_geograph --res 2048x1536 --samples 32 --frame-rgb 0.78,0.78,0.75
python3 tests/hero4c/aligned_score.py tests/hero4c/match/hero4b_Cam_Match_geograph_2048x1536.png tests/hero4c/match/hero4b_whitebars_Cam_Match_geograph_2048x1536.png
