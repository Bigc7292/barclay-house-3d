# usage: bash tests/pass.sh <label>  -> rebuild blend copy, render both matched cams, ref_check
cd /workspace/barclay; B=~/apps/blender-4.2.3-linux-x64/blender; L=$1
BCAMS=hero $B -b -P build_scene.py -- --time midday --noexport >/dev/null 2>&1   # writes out/barclay_scene.blend (no MCP session open)
cp out/barclay_scene.blend tests/scene_copy.blend
for r in geograph commons; do
 $B -b -y tests/scene_copy.blend -P camera_match.py -- --ref refs/critic1/real_$r.jpg --points tests/${r}_points.json --cam Cam_Match_$r --render tests/match_${r}_$L.png --scale 0.5 --samples 16 --hide-near 3 2>&1 | grep -o '"rms_px": [0-9.]*'
 python3 ref_check.py tests/match_${r}_$L.png refs/critic1/real_$r.jpg
done
