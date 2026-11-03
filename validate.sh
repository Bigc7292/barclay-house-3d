#!/bin/bash
# One-command regression check (free: Khronos gltf-validator + gltf-transform). Usage: ./validate.sh
# Budgets per AGENTS.md: hero<5MB, mobile hero<2MB, mobile surroundings<6MB. Also flags stale mobile files.
cd /workspace/barclay; export NODE_PATH=$PWD/.gltf/node_modules; rc=0; L=tests/validate_$(date +%Y%m%d_%H%M).jsonl
chk(){ [ -f "$1" ] || { echo "{\"file\":\"$1\",\"missing\":true}"|tee -a $L; rc=1; return; }; node .gltf/validate.mjs "$1" $2 | tee -a $L || rc=1; }
chk out/barclay_hero.glb 5
chk out/mobile/barclay_hero_mobile.glb 2
chk out/mobile/barclay_surroundings_mobile.glb 6
chk out/barclay_surroundings.glb
for p in hero surroundings; do [ out/barclay_$p.glb -nt out/mobile/barclay_${p}_mobile.glb ] && { echo "STALE: out/mobile/barclay_${p}_mobile.glb older than out/barclay_$p.glb -> run ./make_mobile.sh"; rc=1; }; done
echo "report: $L  result: $([ $rc = 0 ] && echo PASS || echo FAIL)"; exit $rc
