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
echo "report: $L  result: $([ $rc = 0 ] && echo PASS || echo FAIL)"; exit $rc
