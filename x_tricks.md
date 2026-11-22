# Barclay House – free X tricks (from bookmark analyst, 42 logged bookmarks, updated 3 Nov 2026 08:00 UTC+4)
Ranked by gain per effort. Skips items already in x_workflows.md/TOOLS.md unless there is a new angle. All free; nothing paid recommended.

## 1. One-change-per-pass critic loop with locked camera
Source: https://x.com/sorenxet/status/2116912025825616083
What: lock one camera to the reference, build shell → big masses → detail where camera looks → materials → match reference lighting; render, compare side by side, fix ONE thing per prompt.
Free? Yes (method; Blender MCP already installed). Skip paid Opus if not on existing plan; local Ollama model works.
Apply: after `camera_match.py` solves a ref, keep that camera fixed; each iteration = one edit + `python3 ref_check.py render.png refs/<ref>.png`; log the single fix in `critic_log.md`. Spend facade detail (cornices, sills, terracotta bands) only inside the matched frustum.

## 2. Meshopt + KTX2 compression on top of make_mobile
Source: https://x.com/realfxw/status/2116764674377015328
What: web asset pipeline (dedup/weld/simplify + meshopt geometry + KTX2 textures) for browser digital twins.
Free? Yes – gltf-transform (MIT), meshoptimizer (MIT), KTX-Software (Apache-2.0). Ignore SimReady assets unless per-asset license allows.
Apply: `make_mobile.sh` currently outputs no meshopt/KTX2. Add a final step: `gltf-transform meshopt in.glb out.glb --level medium` then `gltf-transform uastc` (normal maps) / `etc1s --quality 128` (albedo/ORM). `web/meshopt_decoder.js` is already present; add KTX2Loader (three.js) or model-viewer handles it natively. Also generate LODs: run make_mobile with ratios 1/0.5/0.15 and swap by distance in three.js `LOD`. Check size + `gltf-transform validate`.

## 3. Procedural glass/polished-stone via MeshPhysicalMaterial clearcoat
Source: https://x.com/cfenghub/status/2117061629670002782
What: pure-code three.js PBR – clearcoat, clearcoatRoughness, sheen + RoomEnvironment reflections.
Free? Technique yes (three.js MIT). The "Fable 5.5" model is unreleased/likely paid – don't use it.
Apply (web viewer): windows → MeshPhysicalMaterial transmission 0.9, roughness 0.05, ior 1.52, thickness 0.01, envMap = `web/env.hdr` via PMREMGenerator; glazed terracotta/polished stone → clearcoat 0.6, clearcoatRoughness 0.15. In Blender: Principled BSDF Coat Weight 0.3–0.6 on glazed terracotta, so the glTF export carries KHR_materials_clearcoat/transmission.

## 4. Render-check-before-animate (teardown rule) for flythroughs
Source: https://x.com/Nyxera0x/status/2116936449442357694 (repo github.com/elvarofficial/teardown, MIT)
What: render a still at every timeline beat and check vs reference before rendering motion.
Free? Yes; already installed. New angle only: make it a gate.
Apply: before any final `flythrough.py --keyframe` render, require each beat's still to pass `ref_check.py` (precision ≥0.7) and a clear-of-geometry check (no camera inside viaduct piers – the earlier bug).

## 5. Clickable floor/unit showcase in the web viewer
Source: https://x.com/anddrrrewww/status/2115935242812789106
What: hover a floor to highlight, click a unit for size/price card.
Free? Inspiration only (no code shared); build with three.js raycaster (MIT) or model-viewer hotspots.
Apply: in Blender name floor slabs `Floor_01..` and export as separate nodes in `hero.glb`; in `web/app.js` raycast on pointermove, set emissive on the hit floor; data from `web/manifest.json` (add floor/unit fields); twobed.glb opens on click.
Status (2026-11-20): CERTIFIED (viewer on lane/floors; not deployed). Main viewer loads web/hero3_floors.glb (desktop) / web/hero3_floors_m.glb (mobile), falls back to hero3.glb / hero_mo3.glb. Click a Floor_* to highlight (emissive tint) and show name + level; click again or empty space to clear; isolate hides floors above. Floor_01 can open the Two Bed interior. Tests: tests/floors/. Pale official look remains out/barclay_hero_floors.glb; archive-look source is out/barclay_hero3_floors.glb. web/hero3.glb not overwritten.

## 6. Free AI assist inside Blender (mcp-for-blender-pro + Ollama)
Source: https://x.com/RoundtableSpace/status/2112751982633205983
What: open-source Blender add-on, 21 scene tools, works with local Ollama.
Free? Yes, but repo/license unverified (Apache-2.0 or GPL-3.0 candidates); executes code – test on `tests/` copies only.
Apply: only worth it for repetitive window-grid/material edits if existing Blender MCP falls short; otherwise skip (already have Blender MCP).

## 7. GPU instancing for repeated facade pieces (web)
Source: https://x.com/zavrenn/status/2117289699694055771 (reply: 60 fps on a 3060 "because instancing carries it")
What: identical meshes drawn as one instanced draw call (EXT_mesh_gpu_instancing).
Free? Yes – gltf-transform (MIT), already in `.gltf/node_modules`.
Apply: in `make_mobile.sh` after `make_mobile.mjs`: `.gltf/node_modules/.bin/gltf-transform dedup in.glb t.glb && .gltf/node_modules/.bin/gltf-transform instance t.glb out.glb` (keep `Floor_*` nodes un-instanced if trick #5 raycast is used). Optionally link window/lamp/tree mesh data in `build_scene.py`. Check `renderer.info.render.calls` in `web/app.js` before/after + `validate`. Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-03-gpu-instancing-web.md

## 8. True displacement + height/AO maps on hero stone/terracotta; mask-driven moss
Source: https://x.com/mukadeshinigami/status/2117128574964560278 (+ quoted article "one reference photo → photoreal PBR in Blender")
What: full PBR set aligned to diffuse (16-bit height, AO, ORM), real Cycles displacement, scatter only where the colour map says (two lengths).
Free? Yes – Blender + Material Maker (MIT). Skip Opus.
Apply: `textures/{stone,terracotta,brick}` have only diff/nor/rough → derive `height.png`/`ao.png`; in `build_scene.py` pbr() add a Displacement node (scale 0.004–0.01 m, method BOTH) when height exists; adaptive subdivision only on HERO objects for the street cam (env flag, e.g. BDISP=1) – no GPU, so test at 960x540 on `tests/` copy. Moss/weeds via Geometry Nodes on `Rail_Viaduct` masked by dark diff areas. Doc: …/implementations/barclay/2026-11-03-height-displacement.md
Status (2026-11-20): CERTIFIED bump-only behind BDISP=1 (stills / street cam). BOTH + adaptive subdiv (BDISP_ADAPTIVE=1) REJECTED — tears the booleaned facade. Height/AO maps derived. Moss left off. See tests/disp/RESULT.md.

## 9. Street life in the flythrough: car departs, train crosses viaduct, dusk glow
Source: https://x.com/uncle_render/status/2117240312439742479 (paid AI render kit – method only)
What: hero still → short clip with one moving vehicle and lit interiors to sell the mood.
Free? Yes – Blender keyframe-free Follow Path, CC0 vehicles (Poly Haven/Kenney) or primitives.
Apply: curves from `scene_data.json` roads "Whitworth Street West" (ids 155768981…) and `rails` at viaduct deck z; add `--life` to `flythrough.py` driving path offsets as a pure function of t; `--tod dusk` sets the window `GLOW` value nodes (build_scene.py) on a seeded subset. Review with `sheet.mjs`; vehicles must not clip hero/piers. Doc: …/implementations/barclay/2026-11-03-street-life-animation.md

## 10. Canal ripples without Water Pro
Source: https://x.com/dangreenheck/status/2117398465256800371 (Three.js Water Pro v4 – paid, $; blocked: cost)
What: believable moving water on the Rochdale Canal.
Free? Yes – three.js `examples/jsm/objects/Water.js` / `Water2.js` (MIT) with a normal map; Blender noise bump.
Apply: web: replace `canal_*` node material in `web/app.js` with three Water (sun dir from `tod_panel.py` sun_pos, flowSpeed low); Blender: add Noise→Bump (strength 0.05) to `Canal_water` in `build_scene.py`, roughness 0.04 kept. Low priority.

## 11. Splat backdrop: RAD LOD conversion for the web (when site photos exist)
Source: https://x.com/lyzzz97/status/2117246558962057515 (Gaussian-Splat-Lite, Apache-2.0; renderer already in x_workflows.md #6 – new angle = converter)
What: `gsl-build-lod` turns PLY/SPZ into streamed LOD RAD with SH codebooks (~56% smaller).
Free? Yes – npm `gaussian-splat-lite`, Node ≥22.12, three ≥0.187.
Apply: after OpenSplat (`TOOLS.md`) on real street photos: `npx --package gaussian-splat-lite gsl-build-lod out.ply --max-sh 0 -o web/context.rad`; load with `RadStreamScheduler` beside `hero.glb`. Test now on `tests/sfm/splat_test.ply`; real use blocked until Colin has site photos/video.

## 12. Geometry-aware procedural grime (soot in crevices, drips under sills) + close-up critique
Source: https://x.com/sidahuj/status/2117640443345379421 → https://www.mcp-for-blender.com/blog/photorealistic-renders/ (steps 4 + 6; Opus/ChatGPT in the recipe = paid, not needed)
What: wear placed where it really collects — AO-masked crevice soot, Pointiness edge wear, gravity drip streaks below overhangs — all shader nodes, no textures; then close-up crops critiqued one fix per pass.
Free? Yes – Blender (GPL) + mcp-for-blender (MIT, already on port 9876).
Apply: `build_scene.py` add `weather2()` after existing `weather()` (keep it; hybrid) behind `BWEATHER2=1`; AO node (0.3 m) inverted → soot, Z-stretched noise × below-sill/cornice mask (heights from `scene_data.json`) → drips, +0.1 roughness in grime. Apply to faience/terracotta/stone/`Viaduct_brick` (AO darkens the salmon parapet tops). Close-ups from `camera_match.py` cams → `ref_check.py`. AO is Cycles-only: stills/flythrough first, GLB only if baked within budget. Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-07-procedural-weathering.md
Status (2026-11-20): CERTIFIED stills/flythrough only, BWEATHER2=1. Not in the GLB. See tests/weather2/RESULT.md.

## 13. Prop-kit normaliser + lineup with scale bar (street props)
Source: https://x.com/apekshik/status/2117798412703953143 → https://github.com/apekshik/anykit (MIT; the tool itself runs on fal+Meshy+Tripo ≈$25/kit = blocked: cost → method only)
What: every prop at real-world size, bottom-centre origin, front −Y, LOD1 ≈25% tris, shared material palette, one lineup render with a 1 m scale bar checked before placing.
Free? Yes – Blender script + CC0 props (Poly Haven/Kenney) + gltf-transform dedup (certified #2a).
Apply: new `props_normalize.py` for lamps/bollards/bins/vehicles used by `build_surroundings.py` and street-life `--life` (#9); heights from a sourced `props_dims.json` (URL per row, else "stand-in"); lineup render to `out/props_lineup.png`; LOD1 for `surr_mobile`. Map prop materials to ≤6 shared materials so dedup merges them.
Status (2026-11-20): CERTIFIED. props_normalize.py + props_dims.json; Kenney assets in assets/life/normalized/; lineup tests/props/out/props_lineup.png. Train keeps #9 scale. See tests/props/RESULT.md.

## 14. Interior viewer: room fly-to buttons + touch walk (Interior bot)
Source: https://x.com/bkdgiffug/status/2117486428645138512 → https://github.com/wy51ai/floorplan-3d (MIT, 3.6k★; live https://wy51ai.github.io/floorplan-3d/)
What: list of rooms → camera flies into that room; first-person walk with on-screen joystick on phones; cut-away walls toggle.
Free? Yes – MIT patterns; model-viewer camera-target/camera-orbit (already used) or a tiny three.js PointerLock/joystick page.
Apply: `interior/live/index.html` (model-viewer on `twobed.glb`, orbit only today): add room buttons that set `camera-target`/`camera-orbit` per room (room centres from `build_twobed_v4.py` / `das_unit_areas.txt`, show sourced m²); optional walk page with joystick + wall collision. Validate on Samsung via `mobile_shots.cjs`.

Skipped: 22 earlier + 9 of 14 new (2026-11-03: 3D World Simulator, DetailCraft, SUAPP, SimReady studio, quantity estimator, PlanFinder, Unreal sun loop (tod_panel.py already does sun path), cfenghub/Codestudiopjbk three.js dupes) (already covered in x_workflows.md/TOOLS.md, interior/off-plan only, paid/proprietary, or spam).
2026-11-07 skipped: ageospatial (paid SaaS), PhysAg3D (paid model + 28 GB GPU), Scenario 3D OS repost (dup, paid credits), Roomtone v2 (no licence; dusk = #9).

## 15. Reference-checklist gate (per-element yes/partial/no + pixel-stat threshold + done criteria)
Source: https://x.com/i/status/2119285434060603642 → https://x.com/rektwild/status/2119281630632145093 (Claude+Blender article; bridge https://github.com/ahujasid/mcp-for-blender MIT). The advertised 'cutaway' skill repo could not be found/licence unknown → method only.
What: each locked-camera render scored per named element vs refs/ crops (yes/partial/no) plus a numeric threshold (≥80% of the reference stat, e.g. dark-pixel share) that must pass; explicit done criteria so the agent can't stop early.
Free? Yes – numpy/Pillow + existing Blender MCP; no ChatGPT/audio steps.
Apply: new `checks.py` + `refs/checklist_<cam>.json` (elements only from sourced ref photos), called after `ref_check.py` (hybrid, keep it); gate = no "no" rows; done-criteria block in AGENTS.md step 6; Interior bot builds rows from the approved CAD plan. Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-09-reference-checklist-gate.md

2026-11-09 skipped: free .edu.kg mail (not relevant, privacy risk), tinyrj pixel-art map, Claude MEP demo (no services in scope), Steam arch tool (unnamed, closed, likely paid), 67.js (Blender covers; licence NOASSERTION).

## 16. Named part hierarchy (plan → split → build)
Source: https://x.com/0xWast3/status/2119837465821499885 · method only · licences: Blender GPL, mcp-for-blender MIT (https://github.com/ahujasid/mcp-for-blender), gltf-transform MIT
What: decide object boundaries before geometry; output a named tree so doors are separate from frames and floors from facade, each part editable/clickable.
Free? Yes – £0.
Apply: parts_plan.json + parts_plan.py; build_scene.py names/parents; export_glb.py and make_mobile.mjs do not join across Floor_*/Door_*; validate.sh node-name check. CERTIFIED 2026-11-15 (copy-test tests/parthierarchy; live web GLBs unchanged). Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-15-part-hierarchy.md

## 17. Fresh-critic loop with numeric fixes + A/B
Source: https://x.com/everestchris6/status/2120175941616128277 · method only · £0 (paid GPT image / Seedance tools in the post are not used)
What: builder never grades itself; each round a new critic with no history gets render + ref crop + checks.py report → yes/no, ≤5 ranked problems each with a numeric fix; taste as A/B; fix only the top item per pass.
Free? Yes – existing agents, no paid image models.
Apply: critic_prompt.md; AGENTS.md/CLAUDE.md/GROK.md step 4; critic_log.md schema. CERTIFIED (method) 2026-11-15 after one trial on the locked-cam Geograph still. Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-15-fresh-critic-loop.md

## 18. Interior plan-overlay gate (trace → draw back over plan → measure IoU before 3D)
Source: https://x.com/everestchris6/status/2120175941616128277 + https://github.com/ZWD11/house-plan-designer (MIT method; we do not invent dimension labels the source image does not have)
What: wall-mask IoU + area residual of the Two Bed layout vs interior/twobed/apt02_fp.png (Rightmove 92163630). Gate IoU ≥0.85 and area ±3% of sourced 63 m².
Free? Yes – numpy/Pillow, £0.
Apply: interior/plan_overlay.py → out/plan_overlay.{png,md,json}. 2bed.json has no wall polylines; default layout is build_twobed_v4.py vertices in plan-px (documented).
Status: CERTIFIED (gate) 2026-11-19 by Interior bot. Current #14 layout FAILS the IoU gate: identity 0.1408, buffered ±4 px 0.2999, layout-on-ink precision 0.5733; area residual 0% by construction. 2bed.json provenance now carries these numbers (no longer “APPROXIMATE”).
Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-15-plan-overlay-gate.md

## 19. Blender mesh-health gate
Source: https://x.com/Aygramm_/status/2122408109113008561 → https://github.com/arjun988/blender-skills (MIT, verification: .claude/skills/references/validation-checklist.md). Claude Code in the post is paid and is not used; checklist idea only, own script, £0 (Blender GPL).
What: per exported object, check non-manifold (3+ faces), flipped/inconsistent normals, loose/dup verts (<0.1 mm), zero-area faces, unapplied or negative scale, unused material slots, *.001 names, and unshared duplicate-mesh groups (register #7). Grade Blocker/Major/Minor; PASS = 0 Blockers.
Free? Yes.
Apply: mesh_health.py (read-only, never saves the .blend); MESHHEALTH=1 ./validate.sh; AGENTS.md done-criteria "mesh_health 0 Blockers". CERTIFIED 2026-11-17 (8.81–9.11 s, 0 Blockers, 22 unshared duplicate groups). Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-17-mesh-health-gate.md

## 20. Pascal Editor head-to-head vs Floorplan 3D interior viewer (#14)
Source: https://x.com/mayaislam_ai/status/2122914096794452040 → https://github.com/pascalorg/editor (MIT, CLI 1.1.6). Local only: `npx @pascal-app/cli editor`, no account, no hosted MCP.
What: trace the Rightmove 2-bed plan, export GLB, compare with web/floorplan3d/2bed.* on #18 IoU/area, phone load, size, console/external requests; borrow wall cutaway / level modes / 2D-3D split only if they win.
Free? Yes – MIT, local CLI. WebGPU needs recent Chrome. “Send to Blender” broken (issue #899) → GLB only.
Status: REJECTED (keep #14) 2026-11-19 by Interior bot. Local CLI ran (Linux, PASCAL_HOME=tests/pascal/.pascal, ownerId null). Independent centreline layout beats #14 on IoU (0.4691 vs 0.1408) and precision (0.9168 vs 0.5733). Official export_glb is not_implemented without a browser Three.js renderer; view_scene is view_unavailable. No Pascal GLB, so no fps/console head-to-head. Not adopted into web/floorplan3d (would break baked walk mode). validate.sh OUT=tests/pascal/out FAIL (exterior hero GLBs correctly absent).
Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-19-pascal-editor.md


## 21. Wheelchair accessible-area overlay (recompute as furniture hides/moves)
Source: https://x.com/tokufxug/status/2123226895030587710 → https://www.linkedin.com/posts/leomallet_3dgs-archviz-webgpu-ugcPost-7528793251185696768-oHvq/ (Léo Mallet et al., PlayCanvas + WebGPU 3DGS interior tool; no repo/licence → method only). Free stack: own JS + three.js (MIT); PlayCanvas engine https://github.com/playcanvas/engine (MIT) not needed (we are mesh-based).
What: floor polygon − furniture footprints, raster 50 mm, erode by wheelchair half-width, flood-fill from entrance, Ø1500 mm turning-circle test per room; show green/red overlay + accessible m²; recompute live on furniture hide. Parameters cite UK Approved Document M (M4(2)/M4(3)); label "indicative". Their splat time-of-day relight: we already have web ToD (web/src/app.js) → keep ours.
Free? Yes – £0.
Apply: web/floorplan3d/2bed.html toggle + new interior/accessible_area.{js,py}; tests/accessible/result.json; "APPROXIMATE layout" badge while #14 fails #18 (IoU 0.1408); optional comparison on tests/pascal/layout_pascal.json. Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-20-accessible-area-overlay.md
Status: CERTIFIED 2026-11-20 by Interior bot. Desktop + Galaxy S9+ 0 console errors, 0 external requests; reachable 9.9325 m² (0% vs Python, ≤63); hiding Bed1_navy raises that room 0.8075→3.6475 m²; recompute 9.3/34.3 ms. Adopted into web/floorplan3d/2bed.html. Results labelled indicative. ADM width is M4(2) 2.22.b 750 mm passage width (no official body width).

## 22. Sun-time shadow-alignment gate (set the sun to the photo's capture time; shadows must line up)
Source: https://x.com/DuckbillStudio/status/2124018140602572902 → method reply https://x.com/DuckbillStudio/status/2124258347608387834 (STUDIO DUCKBILL SplatStroll, geo-referenced 3DGS in PlayCanvas; demo https://moments.splatstroll.com/soundscape/aono/; closed, no repo/licence → method only).
What: read EXIF capture time of dated refs (refs/critic1/real_geograph.jpg 2025-07-03 12:34; refs/surroundings Whitworth_Street_West 5809790, Rochdale_Canal 5477629, Lane_to_West_Whitworth_Street 2295568, Hotspur_Press_remains 8088127) → tod_panel.sun_pos(hour, month, day) → render the camera_match.py locked camera → shadow-mask IoU + shadow-edge angle vs the photo, plus a sweep (peak must sit near the EXIF time). Optional web ?date= into sunPos() (presets currently fixed to 21 June).
Free? Yes – £0 (own code, Pillow, Blender GPL, three.js MIT). EXIF clocks can be wrong → ±1 h tolerance, log assumed offset; do not "fix" the sun.
Apply: sun_check.py + tests/suncheck/result.json (copy / read-only official blend); optional SUNCHECK=1 hook in validate.sh; web/src/app.js date param only if certified, and only as a patch for Interior. Doc: /home/box/x-bookmarks/implementations/barclay/2026-11-22-sun-time-shadow-gate.md
Status: CERTIFIED (method/gate) 2026-11-22; numeric ≥2-ref pass NOT MET (camera-match coverage). Only real_geograph is solvable; that ref PASSES (street-band IoU peaks at EXIF 0.344, angle 0.74°). Three intake times disagreed with file EXIF (Whitworth 2018-01-06 13:38, canal 2017-03-09 13:32, lane 2011-02-28 16:55); EXIF used. Optional ?date= is tests/suncheck/web_date_param.patch, not merged into web/.
