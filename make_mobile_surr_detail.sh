#!/bin/bash
# Mobile LOD for barclay_surroundings_detail.glb (<6 MB): drop sleepers/OLE/window frames, decimate crowns, cull >300 m, merge by material, JPEG<=512, quantize. Free: gltf-transform/meshoptimizer/sharp.
set -e; cd /workspace/barclay; export NODE_PATH=$PWD/.gltf/node_modules; cp surr_mobile_pre.mjs .gltf/surr_mobile_pre.mjs
T=tests/surr; node .gltf/surr_mobile_pre.mjs out/barclay_surroundings_detail.glb $T/pre.glb
node .gltf/make_mobile.mjs $T/pre.glb $T/m.glb 512 300 0.5
.gltf/node_modules/.bin/gltf-transform quantize $T/m.glb out/mobile/barclay_surroundings_detail_mobile.tmp.glb
mv out/mobile/barclay_surroundings_detail_mobile.tmp.glb out/mobile/barclay_surroundings_detail_mobile.glb
node .gltf/validate.mjs out/barclay_surroundings_detail.glb; node .gltf/validate.mjs out/mobile/barclay_surroundings_detail_mobile.glb 6
