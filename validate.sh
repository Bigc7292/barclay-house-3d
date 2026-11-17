#!/bin/bash
# One-command regression check (free: Khronos gltf-validator + gltf-transform). Usage: ./validate.sh
# OUT=tests/x/out ./validate.sh checks a test export instead of out/. Budgets per AGENTS.md: hero<5MB, mobile hero<2MB, mobile surroundings<6MB. Also flags stale mobile files.
cd "$(dirname "$(readlink -f "$0")")"; O=${OUT:-out}; export NODE_PATH=$PWD/.gltf/node_modules; rc=0; L=tests/validate_$(date +%Y%m%d_%H%M).jsonl
chk(){ [ -f "$1" ] || { echo "{\"file\":\"$1\",\"missing\":true}"|tee -a $L; rc=1; return; }; node .gltf/validate.mjs "$1" $2 | tee -a $L || rc=1; }
chk $O/barclay_hero.glb 5
chk $O/mobile/barclay_hero_mobile.glb 2
chk $O/mobile/barclay_surroundings_mobile.glb 6
chk $O/barclay_surroundings.glb
for p in hero surroundings; do [ $O/barclay_$p.glb -nt $O/mobile/barclay_${p}_mobile.glb ] && { echo "STALE: $O/mobile/barclay_${p}_mobile.glb older than $O/barclay_$p.glb -> run ./make_mobile.sh"; rc=1; }; done
# trick #16: required parts_plan.json names in the hero GLB, 0 stray *.001
if [ -f parts_plan.json ]; then
  node .gltf/check_parts.mjs $O/barclay_hero.glb parts_plan.json | tee -a $L || rc=1
fi
# trick #19: mesh-health gate (read-only). MESHHEALTH=1 enables it; default off so a
# plain ./validate.sh stays a GLB/size check. Done-criteria: MESHHEALTH=1 and 0 Blockers.
if [ "${MESHHEALTH:-0}" = 1 ]; then
  BLEND=${MESHHEALTH_BLEND:-out/barclay_scene.blend}
  BLENDER=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}
  if [ ! -f "$BLEND" ]; then echo "{\"check\":\"mesh_health\",\"missing_blend\":true,\"file\":\"$BLEND\"}"|tee -a $L; rc=1;
  elif [ ! -x "$BLENDER" ] && ! command -v blender >/dev/null 2>&1; then echo "{\"check\":\"mesh_health\",\"missing_blender\":true}"|tee -a $L; rc=1;
  else
    log=$L.meshhealth
    MH_OUT="$O" "${BLENDER:-blender}" -b "$BLEND" --python mesh_health.py >"$log" 2>&1
    mhrc=$?
    grep MESHHEALTH "$log" | tail -1 | tee -a $L
    [ $mhrc = 0 ] || rc=1
  fi
fi
echo "report: $L  result: $([ $rc = 0 ] && echo PASS || echo FAIL)"; exit $rc
