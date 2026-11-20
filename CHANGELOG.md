# CHANGELOG

## 2026-11-20 11:54 UTC+4 — clickable floors in the main viewer (lane/floors)
- Why: trick #5 export pipeline was certified (`out/barclay_hero3_floors.glb`, archive look). This wires it into the main viewer. Not deployed; Interior bot merges and deploys later with walls/polish.
- Copied `out/barclay_hero3_floors.glb` → `web/hero3_floors.glb` (3,114,300 B, 2.97 MB) and the mobile build `tests/hero3_floors/out/mobile/barclay_hero_mobile.glb` → `web/hero3_floors_m.glb` (2,038,160 B, 1.94 MB). `web/hero3.glb` and `web/hero_mo3.glb` kept as fallbacks if the Floor_* file fails to load.
- Viewer (`web/src/app.js`, bundled `web/app.js?v=42`): load the Floor_* hero (mobile picks `_m` as before). Click or tap a `Floor_*` node (drag is ignored) highlights it with a cloned-material emissive tint so shared PaletteMaterials do not leak across storeys, and shows a label with the UK floor name and level (Floor_00 Basement level 0, stand-in / NOT FOUND; Floor_01 Ground floor; … Floor_05 Attic storey). Click the same floor or empty space to clear. "Hide floors above" isolate mode. Floor_01 label has "View Two Bed interior" (`mode('i')`).
- Headless Playwright (Chromium + SwiftShader): desktop 1280×720 and Galaxy S9+ (deviceScaleFactor 1). 0 console errors, 0 external requests (blob: ignored). A real click on each Floor_00..05 shows the right name; click again or empty space clears; isolate hides Floor_02..05 when Floor_01 is selected. fps desktop 60.3; phone 60.0 local vs 60.3 live (SwiftShader). Tests: `tests/floors/check.cjs`, `tests/floors/result.json`.
- Look vs live https://barclay-house-viewer.vercel.app (`?life=0&tod=midday`): desktop street/facade/entrance mean abs 0.0087 / 0.0056 / 0.0008 per 255, 0.012 / 0.017 / 0.005 % px>2. Phone 0.465 / 0.527 / 0.587 per 255, 0.379 / 0.495 / 0.291 % px>2 (live still serves `hero_mo3.glb`). Side-by-sides: `tests/floors/out/{desktop,phone}_side_{street,facade,entrance}.jpg`.
- Docs: tricks_register row 5 CERTIFIED (viewer; not deployed), x_tricks #5, README, `web/deploy.sh` + `.vercelignore` list the new GLBs. No LFS, no force-push, nothing to barclay/main/archive, no deploy.

## 2026-11-20 11:23 UTC+4 — archive-look Floor_* hero (barclay)
- Why: `out/barclay_hero_floors.glb` has the official pale faience and cream frames. The live look Colin wants is in `web/hero3.glb` (darker archive front, black metal window frames, BARCLAY HOUSE lettering on the lintel). Interior needs those Floor_* / Door_* / Building names on that look so clickable floors can go live.
- New file `out/barclay_hero3_floors.glb` (3,114,300 bytes, 2.97 MB). Route: decode `web/hero3.glb` (gltf-transform copy + dequantize), split triangles by storey / door world AABBs from `out/barclay_hero_floors.glb` (same coordinate frame), keep hero3 materials/textures (webp + clearcoat). Official Floor_* slabs omitted (they run through window openings). Storey skin is on the Floor_* nodes so make_mobile keeps the names; doors are children of Floor_01. Official `out/barclay_hero.glb`, `out/barclay_hero_floors.glb`, `out/barclay_scene.blend` and `web/hero3.glb` mtimes unchanged. No deploy.
- `MESHHEALTH=1` `validate.sh` PASS: hero 2.97/5 MB, mobile hero 1.94/2 MB, 0 Khronos errors, check_parts 10/10, mesh_health 0 Blockers / 1442 Majors / 3351 Minors. Mobile keeps Floor_* and Door_* (Building empty pruned).
- three.js side-by-side vs live `web/hero3.glb` (viewer street/facade/entrance cameras + lintel close-up): street F1 0.999937, mean abs 0.0144/255, 0.149% px >2; facade F1 0.999951, 0.0239/255, 0.303%; entrance F1 1.0, 0.0010/255, 0.005%; lintel F1 1.0, 0.0009/255, 0.000%. Images: `tests/hero3_floors/out/cmp_side_{street,facade,entrance,lintel}.jpg`. Dark front and black frames match; lettering geometry is present (entrance/lintel F1 1.0).
- Docs: tricks_register row 5, x_tricks #5 status, AGENTS.md = CLAUDE.md = GROK.md tool map + certified-tricks line, README note on the new filename. Replay `tests/hero3_floors/run.sh`.

## 2026-11-20 11:06 UTC+4 — exterior #12 / #8 / #13 certified; Floor_* hero export (barclay)
- Why: Colin approved the recommended upgrades. Interior is running lane bots on `lane/*` and merges/deploys; this pass is the four exterior items (certify #12, finish #8, certify #13, export a Floor_* hero for clickable floors). Free tools only, official exports not overwritten, no deploy, no Vercel, no LFS.
- #12 CERTIFIED (stills/flythrough only, `BWEATHER2=1`): new `weather2.py` (Cycles AO soot, Pointiness edge wear, Z-stretched drips below stand-in sill/LEVELS offsets). Copy-test `tests/weather2/run.sh` on the official blend read-only: street mean abs 1.14/255, 21.13% px >2; official street F1 0.991 off and on; Geograph F1 0.222/0.223 (not the R4 locked-plate 0.625; no on/off regression). Street render 56.0→206.6 s (3.69×) because of AO. Soot amounts are stand-ins. Not baked into the GLB. Rollback `BWEATHER2=0`.
- #8 CERTIFIED bump-only (`BDISP=1`, street cam / stills); BOTH + adaptive subdiv (`BDISP_ADAPTIVE=1`) REJECTED. `derive_height.py` writes 16-bit `textures/{stone,terracotta,brick}/{height,ao}.png` from Poly Haven CC0 `nor.jpg`. `displace.py` hooks a Displacement node (scale 0.004–0.01 m). Copy-test 960×540 32 spp: official street F1 0.9902 off / 0.9905 on, mean abs 0.42/255, 5.25% px >2, time 1.68× (≤2×), RSS 1.72 GB, no OOM. Adaptive/BOTH tore the BOOLEAN:windows facade (first pass F1 0.990→0.680, mean abs 45.5/255; constant Height 0.5 still failed). Moss left off. Not in the GLB.
- #13 CERTIFIED: `props_dims.json` + `props_normalize.py` → `assets/life/normalized/` (bottom-centre, front −Y, LOD1 ~25% tris, ≤6 shared materials). `life_paths.py` prefers those GLBs at scale 1; the viaduct train keeps certified #9 `keep_life_scale`. Copy-test: sedan length err 0.000 m vs 4.378 m (2018 Ford Focus, Ford EU media PDF); van 0.000 m vs 4.973 m (stand-in); walkers 0.000 m vs HSE 2019 means 1.755 / 1.617 m; origin z 0; LOD1 0.249–0.250; gltf-transform clean; 1 m scale-bar lineup `tests/props/out/props_lineup.png`. All site sizes labelled stand-in. LIFE still not exported.
- New hero `out/barclay_hero_floors.glb` (3,819,052 bytes, 3.64 MB) with Floor_00..05, Door_entrance_{L_leaf,R_leaf,frame}, Building; 0 stray `*.001`. Official `out/barclay_hero.glb`, `out/barclay_scene.blend` and `web/hero3.glb` mtimes unchanged. `MESHHEALTH=1` `validate.sh` PASS: hero 3.64/5 MB, mobile hero 1.68/2 MB, 0 Khronos errors, check_parts 10/10, mesh_health 0 Blockers / 1442 Majors / 3351 Minors. Mobile keeps Floor_* and Door_* (Building empty pruned). 4K still `tests/hero_floors/out/render_street_4096x2304.png` (Cam_Street 128 spp, 1343 s) vs official street 4K: F1 0.9987, mean abs 0.145/255. This blend is pale faience with cream frames and no lettering; the darker archive front, black frames and BARCLAY HOUSE letters live in `web/hero3.glb`, which was not overwritten. Interior can switch clickable floors onto the new file when it next deploys. No deploy from this pass.
- Docs: tricks_register rows 5/8/12/13, x_tricks status lines, AGENTS.md = CLAUDE.md = GROK.md tool map + certified-tricks line, README note on the new filename.

## 2026-11-20 11:38 UTC+4 — lane/walls: merge lane/furniture (CC0) onto the plan trace; #18 furniture-masked mode; handedness check
- Why: lane/furniture (CC0 models) was merged to origin/barclay (cbf78d9b). Barclay House Interior asked for the trace to drive the walls and `furniture_cc0.py` to drive the models, with the peninsula dropped (the plan wins), no CC0 clipping, the chair assert passing, a #18 furniture-masked score, a handedness check, and the #21 phone timing rerun.
- Merge: `git merge origin/barclay` (no rebase, no force-push). The only conflict was `interior/build_twobed_v4.py` plus 4 binaries. I kept the trace geometry and added `furniture_cc0.place_trace(ctx, FUR, JOIN)`, which places the same CC0 prototypes at the trace positions and footprints from `interior/trace/twobed_layout.py`, sized with a non-uniform root scale. The furniture lane's `place_all` is unchanged and still used by `kit_lineup.py`. The binaries were rebuilt.
- Plan wins:
  - The peninsula, quartz top and built-in oven are dropped.
  - The dining table stays a procedural rectangle: the plan draws 48 x 29 px (1.43 x 0.86 m) at x 203-251, y 228-257, and the round CC0 table doesn't match.
  - Built-in wardrobes stay traced joinery.
  - The kitchen is CC0 Kenney units on the drawn L-run: washer, stove at the drawn hob, sink unit at the drawn sink, and wall units along the south wall only. There is no microwave or tall fridge (not drawn).
  - The plant is removed (not drawn).
  - CC0 chairs sit with their backs on the drawn chair outer edges (y 221.5 and 265 px), tucked under the table as drawn.
- Correction: the bathroom symbols were swapped in the trace. The upper rounded box (x 17-26, y 271-286, 0.27 x 0.45 m) is the basin; the lower box with the cistern strip (x 17-41, y 291-305, 0.71 x 0.42 m) is the WC.
- Fit check, new `tests/furniture_fit/check_fit.py` (5 mm raster, 10 mm contact tolerance): **PASS, 35/35 pieces.** It checks each piece against walls/partitions (minus gaps), the floor outline, wardrobes, door swing sectors, and doorway zones (each gap and opening extended 0.375 m each side, half the ADM 750 mm). All pieces are 100% inside their own room. The rug and shower tray (walk-over) are exempt from the doorway test only.
  - Fixes it forced: the bed head stops at partition face +1 cm (was 1 px off the centreline); the washer and wall units clear the stair partition; wall units sit 25 mm off the wall; the TV bench is 1 cm inside its drawn box; the shower tray stays 1 cm off the walls.
- Chair assert: the lane/furniture criteria are unchanged (dot > 0.9, backrest farther from the table than the opening). The target is the nearest point on the rectangular table's long axis instead of the round table's centre. **4/4 PASS.**
- #18 furniture-masked mode (`plan_overlay.py`, `FURNITURE_SYMBOLS` / `ROOM_ERODE_PX`):
  - Mask = the polygons of the plan's own loose-furniture symbols only (Bed1/Bed2 with bedsides, sofa, rug ellipse, dining table + chairs, WC, basin; from `plan_furniture_px`, measured on the PNG), AND each traced room interior eroded by 3 px, so wall, partition or exterior ink is never masked.
  - Labels, hangers, the stair arrow, hob rings and the shower line are not masked.
  - Masked pixels are removed from both the plan and the layout: 702 plan-ink px; 0 layout px.
  - Raw is the headline and the gate: identity 0.7783, buffered 0.6562 (FAIL vs 0.85). Masked: identity 0.8416, buffered 0.8332. The APPROXIMATE badge stays.
- Handedness: the overlay is not flipped. Ink IoU of overlay vs plan is 0.997 as-is, 0.259 mirrored left-right, 0.169 flipped up-down. Per-label correlation as-is is 0.996-1.000; mirrored it is 0.06-0.74. The labels are about 4 px tall anti-aliased text, so at 3x nearest-neighbour they look garbled in both images (`walls-shots/handedness_labels.png`). The model is not mirrored either: glTF room centroids are kitchen (+2.09, +3.46), storage (-2.58, +1.64), bedrooms z < 0. In a top view (+X right, +Z down) that puts the kitchen bottom-right and storage left, as on the plan.
- #21: reachable 16.865 m² (JS = Python). Bedroom 2: 3.455 m², reachable. Phone recompute over 7 runs at load 16.6-23.7 on 8 cores: median 18.5 ms, 5/7 under 50 ms; desktop median 23.5 ms (`tests/accessible/timing_runs.json`).
- Khronos validator: 0 errors and 0 warnings on `web/twobed.glb` (1.74 MB), `web/twobed_m.glb` (1.68 MB) and `interior/live/twobed_raw.glb` (7.76 MB).

## 2026-11-20 10:37 UTC+4 — lane/walls: retrace 2-bed walls/doors/windows from Rightmove plan, rebuild walk mode
- Why: #18 plan_overlay failed (buffered IoU 0.2999) and #21 showed Bedroom 2 sealed (0 m² reachable). Walk mode was retraced from `apt02_fp.png` instead of replacing it with Pascal (#20 rejected; Pascal is reference only).
- New `interior/trace/twobed_trace.py` → `twobed_trace.json`: every wall, window, door and opening measured in plan px (OpenCV contours/Hough + ink-fit, max drift 2.69 px). Scale K = sqrt(63 m² / internal-face floor 71278.9 px²) = 0.029730 m/px (the plan prints no dimensions). Rooms sum to 63.011 m²; raster floor 62.8925 m² (−0.17%).
- New `interior/trace/twobed_layout.py` (shared metric layout) and `write_2bed_json.py`. `build_twobed_v4.py`, `plan_overlay.py` and `accessible_area.py` now read the trace. Bedroom 1 and 2 are door-less openings as drawn, so Bedroom 2 is no longer sealed. The kitchen peninsula was removed because the plan doesn't show it.
- #18 buffered IoU went from 0.2999 to 0.6562 (identity 0.7783, precision 0.9977). The gate still fails: raw ink includes beds, sofa, dining set, sanitaryware and labels. With the plan's furniture blanked, buffered IoU is 0.8561. The APPROXIMATE badge stays.
- #21 total reachable went from 9.93 to 16.63 m², and Bedroom 2 from 0 to 3.47 m². The JS twin matches Python at 0% difference. The phone recompute missed the <50 ms timing (51.9 ms, and 79 ms at load avg ~30 from other lanes); every functional criterion passes.
- Rebuilt `web/twobed.glb`, `web/twobed_m.glb` and `2bed.json`. The Khronos validator reports 0 errors and 0 warnings. Stand-ins NOT FOUND in any source: ceiling 3.0 m, partitions 0.10 m, door head 2.1 m, sill 0.5 m and window head 2.75 m, joinery and furniture heights.

## 2026-11-20 08:42 UTC+4 — trick #21 wheelchair accessible-area overlay (barclay)
- Why: Barclay House 3D asked Interior to certify bookmark trick #21 on a copy of `web/floorplan3d/2bed.html` first. Same rules as #20: free tools only, every parameter sourced or measured, no force-push, no LFS, no files >100 MB, no exterior Blender touch, no push to barclay-house-archive.
- #21 CERTIFIED and adopted: `interior/accessible_area.py` + `.js` twins (50 mm raster, flood from `Door_entrance`, green/red overlay). `2bed.json` has no floor polyline (#18); floor outline, partitions and furniture boxes come from `interior/build_twobed_v4.py` (the walk-mode GLB is baked into `BAKED_interior`). Official ADM Vol 1 (2015 edition with 2016 amendments, still the Vol 1 PDF on the current GOV.UK page): [Approved Document M](https://www.gov.uk/government/publications/access-to-and-use-of-buildings-approved-document-m), [PDF](https://assets.publishing.service.gov.uk/media/5a7f8a82ed915d74e622b17b/BR_PDF_AD_M1_2015_with_2016_amendments_V3.pdf). ADM does not publish a wheelchair body width; erosion uses the official 750 mm minimum clear width at a localised obstruction (M4(2) 2.22.b). 1500 mm turning circle: M4(3) 3.14.d, 3.22.d, 3.43.e. Output labelled **indicative**. Page carries an **APPROXIMATE layout** badge because #14 fails the #18 IoU≥0.85 gate (identity 0.1408).
- Headless Chrome (swiftshader) desktop 1600×900 + Galaxy S9+ on `tests/accessible/2bed_overlay.html`: 0 console errors, 0 external requests. Reachable **9.9325 m²** ≤63, **0%** vs Python. Hiding `Bed1_navy` raises Bedroom 1 **0.8075→3.6475 m²**. Recompute **9.3 ms** desktop / **34.3 ms** phone. Per-room Ø1500 mm: hall and storage yes; Bedroom 1, Bedroom 2, bathroom, kitchen, living no. Bedroom 2 reachable area is 0 (door 0.14 m from a corner, closed by 375 mm erosion). Results in `tests/accessible/result.json`.
- Adopted into `web/floorplan3d/2bed.html` (toggle does not kick the user out of walk mode). Deploy copies `accessible_area.js` and `accessible_layout.json` live next to that page; `web/deploy.sh` FILES list updated.


## 2026-11-19 08:35 UTC+4 — tricks #18 plan-overlay gate + #20 Pascal Editor (barclay)
- Why: Colin asked Interior to certify bookmark trick #20 (Pascal Editor vs certified #14 Floorplan 3D) and to build #18 if missing. Rules: free tools only, no invented dimensions, every claim sourced or measured. No Vercel unless something was adopted.
- #18 CERTIFIED (gate): new `interior/plan_overlay.py` (numpy/Pillow). `2bed.json` has no wall polylines; default walls are from `interior/build_twobed_v4.py` in plan-pixel space of `interior/twobed/apt02_fp.png`. Sourced total 63 m² ([barclay-house.com/two-bedroom-apartment](https://barclay-house.com/two-bedroom-apartment/), Rightmove 92163630 679 sq ft). #14 layout wall-mask IoU identity **0.1408**, buffered ±4 px **0.2999**, layout-on-ink precision **0.5733**; area residual **0% by construction**. Gate IoU≥0.85 **FAIL**. Provenance in `web/floorplan3d/2bed.json` now carries the measured IoU (the old “APPROXIMATE” label is gone). Reports: `out/plan_overlay.{png,md,json}` and `tests/pascal/out/plan_overlay_2bed.*`.
- #20 REJECTED (keep #14 walk mode): local `npx @pascal-app/cli editor` 1.1.6 ran on this box, no account, no hosted MCP (`PASCAL_HOME=tests/pascal/.pascal`, runtime 127.6 MB not committed). Independent centreline trace `tests/pascal/layout_pascal.json` beats #14 (IoU **0.4691**, precision **0.9168**). Local MCP built 24 walls + 5 doors; Pascal zone areas 54.8+4.94+3.24=**62.98 m²** (−0.03% vs 63). Official `export_glb` is `not_implemented` (browser Three.js renderer required); `view_scene` is `view_unavailable`; Send to Blender already broken (issue #899). No Pascal GLB, so no desktop/Galaxy S9+ fps or console comparison. `OUT=tests/pascal/out ./validate.sh` FAIL as expected (that script checks exterior hero/surroundings GLBs, which were not written here). `web/twobed.glb` 1.41 MB / `twobed_m.glb` 1.27 MB, Khronos 0 errors. Not adopted into `web/floorplan3d`: a walls-only Pascal scene would break the baked furnished Walk mode. Exterior Blender files were not touched. No Vercel deploy.
- Register rows 16, 17 and 19 were already CERTIFIED and are left as such.

## 2026-11-17 20:21 UTC+4 — trick #19 mesh-health gate (barclay)
- Why: X Bookmark Analyst intake 2026-11-17. validate.sh already checked glTF + size; checks.py checked pixels; nothing checked topology, normals, transforms, or unshared duplicate meshes (#7).
- #19 CERTIFIED: new `mesh_health.py` (Blender 4.2.3, bmesh only, read-only, never saves the .blend; checklist idea from arjun988/blender-skills MIT, £0). Writes `out/mesh_health.{md,json}`. Hook: `MESHHEALTH=1 ./validate.sh`. AGENTS.md, CLAUDE.md and GROK.md done-criteria now include "mesh_health 0 Blockers" (three files kept identical).
- Current scene report (copy-test + official blend): 8.81s / 9.11s, Blockers 0, Majors 1442, Minors 3351, 22 unshared duplicate-mesh groups (150 objects) for #7. Official `out/barclay_scene.blend` mtime unchanged. No Blocker to fix this pass; `./validate.sh` still PASS. Live web GLBs unchanged, not redeployed.
- Register rows 16 and 17 were already CERTIFIED on 2026-11-15 (commit 2cbdfe45) and are left as such.


## 2026-11-15 20:54 UTC+4 — tricks #16 named part hierarchy + #17 fresh-critic loop (barclay)
- Why: Colin's standing intake gate (every bookmark trick checked, tested on a copy, certified or rejected, integrated, bots informed). X Bookmark Analyst intake 2026-11-15, items #16–#17 (#18 is the Interior bot's).
- #16 CERTIFIED: new `parts_plan.json` (Building > Floor_00..05 > Facade/Window/Door_*/Cornice/Parapet, each with a source URL or `stand-in`); `parts_plan.py` names/parents in `build_scene.py` with no geometry change; `export_glb.py` and `make_mobile.mjs` no longer join across Floor_* or Door_*; `validate.sh` checks required node names and rejects stray `*.001`. Copy-test `tests/parthierarchy/run.sh` PASS (10/10 names in the test hero GLB, Floor_* and Door_* kept on mobile, Khronos 0 errors). Register #5 moved to CERTIFIED for the export pipeline. Live `web/hero3.glb` / `web/hero_mo3.glb` were not rebuilt or deployed.
- #17 CERTIFIED (method): `critic_prompt.md`; AGENTS.md, CLAUDE.md and GROK.md step 4 updated identically; trial pass on `tests/match_geograph_p3_oriel3.png` + Geograph ref + `checks.py` logged in `critic_log.md` (verdict no, rank-1 ashlar hf 1.67, not applied this intake).
- No viewer redeploy.


## 2026-11-09 09:25 UTC+4 — viewer/unified: archive visuals + fast viewer + street life + road (merged into `barclay`)
- Why: Colin: visuals first, speed second; live site had lost the archive look (pale facade, no BARCLAY HOUSE lettering, white glazing bars), road looked poor, no moving cars/trains.
- Visuals taken from barclay-house-archive main 58dd6f5 (vercel-live/ + barclay/web/src/app.js): ext7 weathered cream stone/flags/asphalt/sky-dome shaders, AgX tone mapping, `hero3.glb` (dark glazing bars, granite band + raised BARCLAY HOUSE letters, Entrance view), `context_typed_opt.glb`, `ext7_street.glb` street pieces, `twobed_v5` furniture (+ teddy/oak textures), SSAO + bloom, Entrance button, video/ renders page.
- Kept from `barclay`: tod_panel.py solar sun (sunPos), Water2 canal (desktop; phones use the cheap scrolling mesh), Walk mode link, info panel, Interior chair-fixed twobed.glb/_m (walk mode page).
- New: street life on the web (#9): Kenney CC0 sedan/van/SUV on the real Whitworth St W lanes + 3-car electric train on the viaduct rail (OSM via scene_data.json, DTM / rail z heights; speeds/sizes stand-ins), 30 fps cap, Traffic toggle, ?life=0. Road: Poly Haven Asphalt 02 (CC0) PBR, world-projected, + illustrative centre-line dashes.
- Speed: render on demand, static shadow map, SSAO/bloom half-res and SSAO skipped while the camera moves (full frame on stop), DPR 1.5 desktop / 1.25 phone + adaptive, per-mode near/far, phone meshopt files (hero_mo3, context_mo, ext7_street_o) and 512 px textures, bundle minified (1.31 MB -> 0.70 MB). Debug lines __lookAt/__drawcalls removed.
- Deploy: `web/deploy.sh` (from origin/barclay, top-level files). See README "Viewer deploy".

## 2026-11-09 08:55 UTC+4 — `barclay` integration branch (Colin: all Barclay work on one branch)
- Why: Colin ordered all Barclay House work, every file, onto branch `barclay` of Bigc7292/barclay-house-3d, pushed after every edit.
- Merged: feat/floorplan3d-2bed, feat/refchecklist-gate, interior-backup, perf/viewer-speed, feat/streetlife-canalwater, origin/barclay (Interior bot's first push + another bot's full snapshot 485110f).
- Conflicts resolved: tricks_register.md (kept all rows; #15 CERTIFIED); CHANGELOG.md (kept both); AGENTS.md/CLAUDE.md/GROK.md (kept all step 3/5 additions, three files identical); web/src/app.js (perf render-on-demand + Interior chairs kept, Water2 canal + tod_panel sun added; water animates only on rendered frames so idle cost stays zero); web/index.html (app.js?v=39); web/app.js rebuilt with esbuild.
- Checks: ./validate.sh PASS; node --check web/app.js OK; headless Chromium desktop+phone 0 console errors, Water2 present (tests/barclay_merge/).
- Known: web canal still sits under the old context_mo terrain until the next full re-export (terrain cut is in build_scene.py); not deployed.
- Tracked previously ignored out/checklist_*_refcheck.png. No Git LFS, no files >100 MB.
- Box sweep: see README "Box sweep".

## 2026-11-09 (Asia/Dubai) — `barclay` branch full project snapshot

- Full snapshot of Barclay House project onto branch `barclay` (created from `origin/main`), per Colin's rule that all Barclay House work lives on `barclay` in Bigc7292/barclay-house-3d.
- Includes Surroundings Bot work: `build_surroundings.py`, `surroundings_data.py` / `surroundings_data.json`, `surroundings_specs.md`, `surroundings_log.md`, `refs/surroundings/` (with `LICENCES.md`), `export_surroundings_detail.py`, mobile surroundings scripts (`make_mobile_surr_detail.sh`, `surr_mobile_pre.mjs`), and `out/` GLBs (`barclay_surroundings.glb`, `barclay_surroundings_detail.glb`, mobile copies).
- Also includes current interior/viewer/floorplan3d assets, docs (`README_INTERIOR.md`, AGENTS/CLAUDE/GROK updates), web deploy helpers, shots, and vendor floorplan-3d — everything present under the shared `/workspace/barclay` tree (excluding `.git`, `node_modules` re-copies, `__pycache__`, and editor lockfiles).
- Why: standing rule that every Barclay bot commits and pushes all project files to the `barclay` branch; no force-push; files over 95 MB skipped (none this snapshot).

## 2026-11-09 — interior-backup branch

- Branch `interior-backup`: Interior bot backup (Two Bed bake, viewer, Floorplan 3D Walk mode, shots, FINDINGS/critic_log).
- Chair-fixed `twobed.glb` / `twobed_m.glb` (sha 130eda10… / 49a2ef6f…), geometric facing check `ang = a - π/2`.
- Merged on top of `perf/viewer-speed` (`hero_mo`/`context_mo`, `vercel.json`, on-demand render); stripped `__lookAt`/`__drawcalls` debug hooks.
- Live deploy `dpl_745x9tBVeNR97MqscvVLfiU45SrC` (app.js?v=38). See README_INTERIOR.md.

## 2026-11-09 08:40 UTC+4 — perf/viewer-speed (live viewer speed fix)
Branch `perf/viewer-speed` (based on `feat/floorplan3d-2bed`). Deployed to production: dpl_8EvCfXUL1o2q4JfpdSKPzzHfEHxa → https://barclay-house-viewer.vercel.app

Root causes (main viewer, web/src/app.js):
- Redrew the full scene + 2048 PCF shadow pass every frame, even when idle (shadow pass doubled draw calls).
- 53 street-lamp PointLights always in every shader (intensity 0 in daytime still costs per pixel).
- Desktop logarithmicDepthBuffer + preserveDrawingBuffer (kills early-z, extra bandwidth).
- Phones: near 0.02 / far 5000 without log depth → z-fighting flicker ("glitchy"); DPR up to 2.
- Phone GLBs hero_m/context_m were NOT meshopt-compressed (4.7 MB context_m was bigger than desktop's).
- "Back to exterior" button visible on phones in exterior view (CSS override of .x).

Changes:
- Render on demand (OrbitControls change / fly / walk-look / autorotate / loads); skip when tab hidden.
- Shadow map static: autoUpdate=false, redrawn only on time-of-day or model load.
- DPR cap 1.5 phone / 2 desktop + adaptive step-down (to 1) if motion runs < ~30 fps.
- Dropped logDepth + preserveDrawingBuffer; near/far per mode (ext 0.1/2500, interior 0.03/300).
- Lamps: nearest 12 (desktop) / 6 (phone), lights only added at dusk/night.
- Phones load hero_mo.glb / context_mo.glb (dedup + meshopt medium of hero_m/context_m; validator 0 errors). Old files kept.
- Interior GLB loads after the exterior (or first with ?m=i).
- web/vercel.json cache headers (glb/hdr/js 1 h + SWR 7 d; html no-cache).
- floorplan3d/2bed.html: DPR cap 1.5 on phones, no preserveDrawingBuffer.

Measured (headless Chromium, SwiftShader software GL, so absolute FPS is low; compare ratios). Live before → live after:
- Desktop 1600x900: load 5.36 → 5.36 MB; ready 2.8 → 2.4 s (first view); orbit FPS 0.1 → 1.6; draws/frame 20 → 11; tris/frame 322k → 162k; idle redraws ~93/s → 0.
- Pixel 7 + 4x CPU throttle: load 4.02 → 2.97 MB; ready 5.6 → 2.8 s; FPS 0.3 → 3.8; canvas 824x1678 → 618x1258; idle redraws ~145/s → 0.
- Walk mode (phone): FPS 4.9 → 13.3. Console errors: 0 before and after.

## 2026-11-09 09:21 UTC+4 — production deploy dpl_H7TqPZYWijdZAYP5PnbDbDVkMnNd (barclay 56464d9c, app.js?v=41)
- Deployed via web/deploy.sh + Vercel connector, top-level paths, 67 files. All probed paths 200, 0 console errors desktop + Pixel 7.
- Live verify: facade colour/glazing match archive dpl_6so3k (street/night/aerial side-by-side), BARCLAY HOUSE lettering visible (Entrance), CC0 asphalt + centre dashes, Kenney cars on Whitworth St W + train on viaduct (Traffic toggle).
- Live metrics (SwiftShader headless, ratios only): desktop 10.1 MB transferred, 157 draws, ready 5.2 s; phone 5.0 MB, 56 draws, ready 5.6 s, first view 4.6 s.

## 2026-11-09 11:55 UTC+4 — Git auto-deploy prep (web/ as Vercel root)
- Added `web/.vercelignore` (whitelist generated by deploy.sh from FILES): a Git build with Root Directory `web` ships exactly the 67 deploy.sh files. Verified locally with git's own ignore engine: 67 kept, 0 extra, 0 missing.
- deploy.sh regenerates .vercelignore on every run and tells you to commit it if FILES changed.
- Docs (README/AGENTS/CLAUDE/GROK): Git-link target = barclay-house-3d, production branch `barclay`, root `web`, static, app.js committed pre-built.

## 2026-11-20
- Carried bookmark trick #21 (wheelchair accessible-area overlay, NEW, owner Interior bot) into tricks_register.md and x_tricks.md from the stale /workspace/barclay checkout.
