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

## 13. Prop-kit normaliser + lineup with scale bar (street props)
Source: https://x.com/apekshik/status/2117798412703953143 → https://github.com/apekshik/anykit (MIT; the tool itself runs on fal+Meshy+Tripo ≈$25/kit = blocked: cost → method only)
What: every prop at real-world size, bottom-centre origin, front −Y, LOD1 ≈25% tris, shared material palette, one lineup render with a 1 m scale bar checked before placing.
Free? Yes – Blender script + CC0 props (Poly Haven/Kenney) + gltf-transform dedup (certified #2a).
Apply: new `props_normalize.py` for lamps/bollards/bins/vehicles used by `build_surroundings.py` and street-life `--life` (#9); heights from a sourced `props_dims.json` (URL per row, else "stand-in"); lineup render to `out/props_lineup.png`; LOD1 for `surr_mobile`. Map prop materials to ≤6 shared materials so dedup merges them.

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
