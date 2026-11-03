# Mobile GLBs (built 2026-11-03 07:12 UTC+4 Dubai)
Source exports copied from out/ (timestamps 06:37:58 hero, 06:38:07 surroundings, UTC+4) into out/mobile/src/.
Rebuild: `/workspace/barclay/make_mobile.sh` (gltf-transform + sharp + meshoptimizer simplifier; output has NO Draco/meshopt/KTX2, extensionsUsed = none). Screenshots: `node mobile_shots.cjs` (needs `python3 -m http.server 18473 --bind 127.0.0.1` in out/mobile).

| file | size | draw calls | meshes | verts / tris | textures |
|---|---|---|---|---|---|
| barclay_hero_mobile.glb | 1.74 MB (src 4.84 MB) | 8 (src ~1,460 meshes) | 7 | 39,310 / 20,396 | 3 JPEG, 1024² (src 2048²) |
| barclay_surroundings_mobile.glb | 4.60 MB (src 36.2 MB) | 20 (src ~5,100 meshes) | 17 | 139,963 / 71,392 | 12 JPEG, 512² |

Changes: meshes merged by material (join/flatten), welded, textures re-encoded JPEG q82. Surroundings: 1,611 nodes with centre >400 m from origin dropped; LIDAR terrain cropped to 400 m radius and simplified 232k→18.6k tris (normals recomputed smooth); other meshes simplified (ratio 0.25, error 1%). Units/origin/up-axis unchanged (Y-up, metres).
Validation: Khronos gltf-validator 0 errors (hero 1 warning, surroundings 4 warnings). Loaded in model-viewer, headless Chromium emulating Galaxy S9+: web/shots/mobile_hero.png, mobile_surroundings.png.
Note: merged node names are lost (individual objects not pickable); terrain uses 32-bit indices (supported by WebGL2 / all modern phones).
