#!/bin/bash
# v2 = make_mobile.sh + CERTIFIED optional steps (tricks_register.md). Original script untouched.
# Flags: MESHOPT=1 (default on; trick #2, -47%..-62% size, needs meshopt_decoder.js in viewer)
#        DEDUP=1 (default on; trick #7 part, -13% size full GLBs; instancing found 0 repeats -> skipped)
#        KTX2=0 (default off; REJECTED for download size: +26%/+88%; only for GPU-memory tests)
set -e; cd /workspace/barclay
./make_mobile.sh
G=.gltf/node_modules/.bin/gltf-transform; M=out/mobile
for f in $M/barclay_hero_mobile.glb $M/barclay_surroundings_mobile.glb; do
  o=${f%.glb}_v2.glb; cp $f $o
  [ "${DEDUP:-1}" = 1 ] && $G dedup $o $o
  [ "${MESHOPT:-1}" = 1 ] && $G meshopt $o $o --level medium
  if [ "${KTX2:-0}" = 1 ]; then K=$(ls -d ~/apps/ktx/KTX-Software-*/ | head -1); PATH=$K/bin:$PATH LD_LIBRARY_PATH=$K/lib $G etc1s $o $o --quality 128; fi
  NODE_PATH=$PWD/.gltf/node_modules node .gltf/validate.mjs $o 6
done
echo "Outputs *_mobile_v2.glb (meshopt). Viewer MUST set meshoptDecoderLocation / MeshoptDecoder to local web/meshopt_decoder.js."
