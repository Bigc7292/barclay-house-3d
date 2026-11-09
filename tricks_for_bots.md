# Certified tricks per bot (updated 2026-11-09, from tricks_register.md)
## Barclay House Interior (viewer)
- #2 meshopt: load out/mobile/*_mobile_v2.glb (-47%/-62%). MUST host web/meshopt_decoder.js locally: model-viewer `meshoptDecoderLocation='./meshopt_decoder.js'` or three `loader.setMeshoptDecoder(MeshoptDecoder)`; CDN default failed in test.
- #3 glass: swap Glass_dark to MeshPhysicalMaterial (transmission 0.9 desktop / off on phones) + RoomEnvironment; faience clearcoat already in GLB. Code: tests/trickcheck/snippets.js
- #10 canal (CERTIFIED 2026-11-09, branch feat/streetlife-canalwater): Water2 (three r170, MIT) is already in web/src/app.js; data = web/src/canal.json from canal_web.py (visible canal tris only). 1 Water2 mesh (512 px desktop, 256 px phones, ?water=0 off), rest one merged cheap mesh. Sun follows tod_panel.py. After the next hero/surroundings re-export (terrain cut), run canal_web.py and rebuild app.js (esbuild).
- #5 floor/unit click: waits for Floor_* nodes (none yet).
- NOT KTX2 (bigger files).
## Surroundings Bot
- #7: share mesh data for repeated lamps/bollards/trees/windows (linked duplicates) so `gltf-transform instance` actually instances (currently 0 repeats found, 5453 draw calls).
- #2: run dedup + meshopt on your GLB (surroundings 34.5→14.3 MB in test).
- #10: keep canal meshes named canal_* with material Canal_water; terrain over water is now cut by water_ripple.cut_terrain() (build_scene.py). Still needed: canal walls/copings at the cut edges (sourced heights only).
- #9 street life CERTIFIED: life_paths.py (Kenney CC0 cars, train, walkers on OSM geometry). Render-only (never exported). Use `flythrough.py --life`. Do not place props that clip (life_paths.clip_check).
- #11: splat backdrop only once real photos exist (gsl-build-lod tested, -87%).
## Optimizer Bot
- Run make_mobile_v2.sh then validate.sh; budget check v2 files. Add a headless load check (tests/trickcheck/load.cjs) — a meshopt file without local decoder fails silently with ERR.
- Track draw calls (hero 1466, surr 5453) until linked-duplicates/join-by-material lands.
- Never adopt a trick without a register row (AGENTS.md intake gate).
