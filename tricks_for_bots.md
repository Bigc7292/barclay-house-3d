# Certified tricks per bot (updated 2026-11-09, from tricks_register.md)
## Barclay House Interior (viewer)
- #2 meshopt: load out/mobile/*_mobile_v2.glb (-47%/-62%). MUST host web/meshopt_decoder.js locally: model-viewer `meshoptDecoderLocation='./meshopt_decoder.js'` or three `loader.setMeshoptDecoder(MeshoptDecoder)`; CDN default failed in test.
- #3 glass: swap Glass_dark to MeshPhysicalMaterial (transmission 0.9 desktop / off on phones) + RoomEnvironment; faience clearcoat already in GLB. Code: tests/trickcheck/snippets.js
- #10 canal: three Water.js (MIT) on Canal_water, 256px reflections on phones. Snippet in snippets.js.
- #5 floor/unit click: waits for Floor_* nodes (none yet).
- NOT KTX2 (bigger files).
- #14 Floorplan 3D (CERTIFIED 2026-11-09, branch feat/floorplan3d-2bed): web/floorplan3d/2bed.html = room buttons -> fly-in -> first-person walk, phone joystick + drag-look, WASD/E on desktop, tap/click doors to open/close, wall collision. Uses ../twobed.glb / twobed_m.glb, local three r160 (no CDN). To adopt in the live viewer: port goRoom/joystick/carveDoors/blocked from that file; dequantize meshopt geometry before splitting. Test: tests/floorplan3d/check.cjs.
## Surroundings Bot
- #7: share mesh data for repeated lamps/bollards/trees/windows (linked duplicates) so `gltf-transform instance` actually instances (currently 0 repeats found, 5453 draw calls).
- #2: run dedup + meshopt on your GLB (surroundings 34.5→14.3 MB in test).
- #10: name the canal mesh Canal_water. #9 street life deferred to Round 5 (CC0 only).
- #11: splat backdrop only once real photos exist (gsl-build-lod tested, -87%).
## Optimizer Bot
- Run make_mobile_v2.sh then validate.sh; budget check v2 files. Add a headless load check (tests/trickcheck/load.cjs) — a meshopt file without local decoder fails silently with ERR.
- Track draw calls (hero 1466, surr 5453) until linked-duplicates/join-by-material lands.
- Never adopt a trick without a register row (AGENTS.md intake gate).

## All bots — trick #15 reference-checklist gate (CERTIFIED 2026-11-09)
- Run `python3 checks.py --cam street --cam hero` (add `--cam viaduct` while parapet colour is open) after every locked-camera still. Gate PASS = no "no" rows and ≤2 "partial".
- Reports: out/checklist_<cam>.md (+ hybrid ref_check sheet). Crops live in refs/checklist_<cam>.json (sourced photos only).
- Critic_log should cite checklist rows (ashlar / arcade / glazing / rb_shields / parapet_colour) instead of prose when possible.
- Interior: when adapting, drive rows from the approved CAD plan (room counts/sizes/doors), not facade photos.
- Do NOT use the unverified 'cutaway' skill repo; method re-implemented in checks.py (numpy/Pillow only).
