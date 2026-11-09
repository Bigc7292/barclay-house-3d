# Barclay House 3D – project rules (AGENTS.md)
Read this FIRST on every task. CLAUDE.md and GROK.md are copies/symlinks of this file so any agent tool finds it.

## Hard rules
1. FREE ONLY. No paid tools, subscriptions, credits or paid APIs. A cost = blocker; propose a zero-cost path.
2. NO ESTIMATES for building facts. Only sourced numbers with URL (LIDAR counts). Stand-ins must be labelled "stand-in". Log in dossier.
3. Don't ask Colin for data. Do research/build yourself. Message Colin only with finished results or a hard blocker.
4. Don't burn tokens: short replies, no duplicate research, no ack ping-pong.
5. Never overwrite a good export: write to temp, then mv. Never save over barclay_scene.blend while the Blender MCP session has it open.

## Tool map (use these, in this order)
- Facts: dossier Page + listings_findings.md + docs/ (planning drawings). Data: area.osm, scene_data.json, lidar/.
- Build: build_scene.py, tod_panel.py via Blender 4.2.3 (-y). Blender MCP (port 9876) for live inspection/edits.
- Check: camera_match.py -> ref_check.py against refs/ -> checks.py (per-element checklist gate, trick #15). Render: Cycles 128 samples + denoise.
- Export: export_glb.py -> make_mobile.sh (hero + surroundings, full + mobile). Then ./validate.sh (Khronos validator + size budgets + stale-mobile check; must PASS).
- Interior walk page (trick #14, CERTIFIED): web/floorplan3d/2bed.html + 2bed.json (rooms, fly-to cams, door hinges recomputed from interior/build_twobed_v4.py). three r160 vendored in web/floorplan3d/vendor/three-r160 (no CDN). Test: node tests/floorplan3d/check.cjs (serve repo root on :18490).
- Ideas: x_tricks.md and x_workflows.md (from X Bookmark Analyst). Skills: teardown, canvas, box-desktop.

## The pipeline (same order every time)
0. READ: AGENTS.md, critic_log.md (last round), x_tricks.md. Note which tricks apply this round.
1. FACTS: any new dimension/material? Source it (URL) or mark NOT FOUND; keep searching before reporting missing.
2. BUILD: one change set only, from the latest critic defect list. One thing per pass where possible (locked camera).
3. CHECK: render preview from locked camera, run ref_check.py vs reference photo, then python3 checks.py --cam <cam>. Compare to refs/ side by side. Flythroughs: `flythrough.py --life` adds certified street life (#9, life_paths.py; clip_check must report 0).
4. CRITIC: independent critic (separate executor or Interior bot) scores and lists defects. Log in critic_log.md (round, score, defects, fix, applied tricks, skipped tricks + why).
5. EXPORT: GLB hero + surroundings, then make_mobile.sh; validate (OUT=tests/x/out for test exports); run canal_web.py and rebuild web/app.js (cd web/src && ./node_modules/.bin/esbuild app.js --bundle --minify --outfile=../app.js) for the #10 Water2 canal; if twobed.glb or door/room layout changed, regenerate web/floorplan3d/2bed.json and run tests/floorplan3d/check.cjs (0 console errors, 5 doors carved, walk blocked by walls); keep the viewer render-on-demand (perf/viewer-speed): water animates only on rendered frames; tell Interior bot to redeploy viewer.
6. DELIVER: 4K stills only when critic score meets target (>= online photos). One short message to Colin.
   Done-criteria (all must hold before messaging Colin):
   - ./validate.sh PASS (Khronos 0 errors; hero/surroundings/mobile within size budgets; mobile not stale).
   - Checklist gate PASS: `python3 checks.py --cam street --cam hero` (and `--cam viaduct` when that still is open) writes out/checklist_<cam>.md with no "no" rows and ≤2 "partial"; hybrid ref_check edge F1 is logged on the same report.
   - Human (or Interior critic) saw at least one multi-angle view this round.
   - No stray *.001 empty objects in the blend/GLB (name search).
Loop 2-5 until target met. Every round the critic_log must list which rules/MCPs/skills/tricks were used. Prefer citing checklist rows over prose for element defects.

## Improving this file
After each round, add any repeated mistake as a rule (one line) under "Lessons". Keep the pipeline short.

## Lessons
- Checklist crops must be compared at a shared modest size; upscaling a small ref crop to 4K wipes edges and falsely PASSes.
- Ashlar rubble reads as high HF-edge excess vs smooth ref ashlar; do not treat raw edge_ratio alone as quality.
- Cutters must stay until booleans applied; check windows/arches aren't solid in the GLB.
- Tiled stone textures read as rubble in the GLB; use flat colours.
- Phones: use out/mobile/ files, not full ones (36 MB surroundings GLB blanks Samsung).
- Executors can't spawn subagents; the orchestrator runs the critic loop.
- Don't message a running executor mid-task; it interrupts.
- Canal water was hidden under the DTM terrain for rounds: check new set dressing is actually visible (sky ray-cast) before tuning its look.
- Every hero/surroundings re-export must be followed by ./make_mobile.sh then ./validate.sh; R3 left mobile GLBs built from the 06:37 export.

- Quantized/meshopt GLB geometry (int16) must be dequantized to Float32 before applyMatrix4 or splitting, else the mesh collapses (floorplan3d R1 bug).

## Bookmark-trick intake gate (Colin's rule, 2026-11-03)
Every item X Bookmark Analyst adds to x_tricks.md is NOT adopted until Barclay House 3D has: (1) read the source + doc, (2) verified it's free and licence-OK, (3) checked where it fits (script/step/bot), (4) tested it on a copy in tests/, (5) certified it (PASS/FAIL with measured result, validate.sh must pass for exports), (6) integrated it into AGENTS.md pipeline or tool map, and (7) told all bots. Record each in /workspace/barclay/tricks_register.md: id, source, status (NEW/TESTING/CERTIFIED/REJECTED), test result, where integrated, date. Never leave a trick as NEW for more than one round.
- Certified tricks (see tricks_register.md / tricks_for_bots.md): #9 street life (life_paths.py, Kenney CC0, render-only); #10 canal (water_ripple.py ripple + terrain cut in build_scene.py, Water2 in web/src/app.js); phone files via ./make_mobile_v2.sh (dedup+meshopt; viewer must use LOCAL meshopt_decoder.js); KTX2 off (bigger downloads); instancing needs linked mesh data in build_scene.py first.

## Backup rule
- After EVERY change set or round, run ./backup.sh "<msg>" and confirm it prints PUSH OK. Never add files >99 MB (backup.sh blocks them).
