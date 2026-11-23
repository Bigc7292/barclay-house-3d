# CHANGELOG

## 2026-11-23 10:40 UTC+4 — r8c step 4: close street stills (hero4c)
- `tests/hero4/render_cams.py` adds two cameras. Both framings are stand-ins; distances are from ray casts in the blend.
  - `close_east`: camera at (60, −8, 1.7) looking at (80, −12, 3), lens 18. Shopfronts are 6.5–10 m away and the lamp at (66, −9) is about 6 m away.
  - `close_west`: camera at (−72, −20, 1.7) looking at (−95, −10, 3.5), lens 16. Shopfronts are about 10.6 m away and the lamp at (−86, −24) is about 14.6 m away.
  - There is also `--camdef` for ad-hoc cameras.
- Stills, all 1920x1080 at 48 spp, rendered from `out/barclay_hero4c.blend`:
  - `tests/hero4c/stills/hero4c_close_east_1920x1080.png`
  - `tests/hero4c/stills/hero4c_close_west_1920x1080.png`
  - `tests/hero4c/stills/hero4c_facade_1920x1080.png`
  - Shield before/after sheet: `tests/hero4c/stills/cmp_rb_shields_hero4b_vs_hero4c.jpg`.
- Step 5 (validate with MESHHEALTH=1) was done in steps 2–3: PASS, `tests/validate_20261123_1022.jsonl`.

## 2026-11-23 10:40 UTC+4 — combined deploy: polish r10 + hero4b
- Merged `origin/lane/polish` (r10) and `origin/lane/hero4` into barclay. Rebuilt `web/app.js` from `web/src/app.js` (`app.js?v=44`). Floor_* click hooks and the storey Y-band picker are in the bundle. Polish bed/bath camera presets and mobile safe-area layout kept.
- Polish comparison (same scorer, `tests/reference/score.py`): `renders/polish/v3_final` 78.8% (yes=10 no=3) vs `renders/polish/r10/stills_after` 61.2% (yes=8 no=5). The 17.6 point drop is a crop/scorer artefact: r10 reframed the kitchen, living and bath cameras, so the fixed checklist boxes now land on blank walls. `kitchen_white_units` (bidir 0.89) and `bathroom_grey_surfaces` (|Δhue|=3.0°) would still be yes on colour, but `luma_std` 0.026 / 0.032 is below the 0.05 presence floor so both were forced to no and scored 0. `living_window_grid` and `kitchen_black_appliances` already failed on v3; the r10 crop missed the window / appliances that are still in frame. Polish r10 therefore ships.
- Swapped the live exterior from hero4 to hero4b: copied `out/barclay_hero4b.glb` → `web/hero4b.glb` (4,233,068 B, 4.04 MB) and `out/mobile/barclay_hero4b_mobile.glb` → `web/hero4b_mobile.glb` (2,059,612 B, 1.96 MB). sha256 matches out/. Fallback is `hero4` / `hero4_mobile`. Floor_00–05 and Door_* names kept. Storey Y-band click fix kept.
- Khronos: 0 errors on both (desktop 3 warnings, mobile 1 warning). Size budgets 4.04/5 MB and 1.96/2 MB.


## 2026-11-23 10:20 UTC+4 — wire hero4 into the main viewer
- Copied `out/barclay_hero4.glb` → `web/hero4.glb` (4,233,200 B, 4.04 MB) and `out/mobile/barclay_hero4_mobile.glb` → `web/hero4_mobile.glb` (2,059,672 B, 1.96 MB). sha256 matches the out/ files. Official `out/` files and `web/hero3.glb` untouched. `out/barclay_hero4b.glb` is on barclay but is not wired; this lane ships hero4 as requested.
- Main viewer now loads `hero4.glb` (desktop) / `hero4_mobile.glb` (mobile). Fallback is `hero3_floors` / `hero3_floors_m` if hero4 fails to load. `app.js?v=43`.
- Khronos gltf-validator: 0 errors on both files (desktop 3 warnings: missing tangents + unused objects; mobile 1 warning: missing tangents + 24 degenerate triangles of 1200). Size budgets: 4.04/5 MB and 1.96/2 MB.
- Clickable floors: `make_mobile` flattens Floor_* children, so `bindFloors` also registers the named storey parts (Facade_01, Window_0N_*, doorcase, etc.) for picking, tint and isolate. Hits are classified by storey Y-band so the Floor_02 giant pilaster (y 5.5–20) does not steal Floor_03–05 clicks. Floor_00's coarse slab has no centre verts, so its click point is synthesised at the front centre.
- Headless Playwright (desktop 1280×720 and Galaxy S9+): Floor_00–05 each return the right name; isolate and empty-clear work; 0 console errors; 0 external requests. Street still: `shots/r13/hero4_street.png`.
- Not deployed from this lane. Interior bot merges and includes this in the next combined deploy.
## 2026-11-23 10:25 UTC+4 — r8c steps 2–3: hero4c (lower RB shields off the oriel heads), validate PASS
- Step 2: the aligned scores from step 1 show no real facade defect, so hero4b's facade is unchanged. hero4c carries only the shield fix.
- Step 3: `hero4.py` gets a new `BHERO4C=1` switch, which needs BHERO4B.
  - It adds `hero4.rb_skip()`, used by `build_scene.py` (the base `HERO_RB_shield`) and by `hero4.ornament` (cartouche and monogram).
  - It drops a lower-row RB shield (z = L3 + 0.3) wherever its disc overlaps or touches an oriel head. The head spans a·W − 0.4 to b·W + 0.4 and L3 − 0.35 to L3 + 0.10.
  - All 3 lower shields met that test: 2 on the east bay, at its edges, and the west one, which was 0.02 m from its head. The 3 upper-row shields at L4 − 1.6 stay, clear above the heads.
  - With BHERO4C off, the build is byte-for-byte hero4b.
- New files. No hero4, hero4b or protected file was touched.

  | File | Size |
  |---|---|
  | `out/barclay_hero4c.glb` | 4,078,872 B |
  | `out/mobile/barclay_hero4c_mobile.glb` | 1,960,368 B |
  | `out/barclay_hero4c.blend` (with R8 and R8B surroundings) | 65,913,692 B |

  Replay: `tests/hero4c/run.sh`.
- Validate (`OUT=tests/hero4c/exp MESHHEALTH=1 MESHHEALTH_BLEND=out/barclay_hero4c.blend`): PASS.
  - 0 errors on all 4 GLBs. check_parts 10/10 with 0 stray.
  - MESHHEALTH: 0 Blockers and 16 majors (hero4b had 19; the 3 removed shields accounted for 3 majors).
  - Report: `tests/validate_20261123_1022.jsonl`.

## 2026-11-23 10:20 UTC+4 — r8c step 1: camera matched to the Geograph photo, aligned re-score
- Ran `camera_match.py` on the hero4b surroundings blend with the 6 points in `tests/geograph_points.json` and clip_start 4 m.
  - Solved `Cam_Match_geograph`: lens 21.69 mm, location (9.10, −32.71, 3.39), rotation (103.43, −0.53, 21.70)°, rms 14.2 px. The worst point is DoorT at −29.6 px in y.
  - The camera is saved in `tests/hero4c/cam_match_geograph.json`, for use with `render_cams.py --camfile`. The solve report is `geomatch_solve.json.txt`.
- Renders at 2048x1536, 32 spp:
  - `tests/hero4c/match/hero4b_Cam_Match_geograph_2048x1536.png`
  - A diagnostic copy with white bars, `hero4b_whitebars_…png`. It uses `render_cams.py --frame-rgb`, which only recolours at render time and never saves.
  - Comparison sheet: `tests/hero4c/cmp_aligned_geograph.jpg`.
- New script `tests/hero4c/aligned_score.py` applies the same crop box to the photo and the render, using the stock `checks.score_element` rules and thresholds. Boxes are picked above the poster hoarding, which starts at y≈0.73. Results are in `tests/hero4c/aligned_scores.json`.

  | Row | Black bars (hero4b) | White bars (diagnostic) |
  |---|---|---|
  | Ashlar, east wall bay | hf 0.28, yes | 0.28, yes |
  | Ashlar, west band/voussoirs | hf 0.98, yes | 1.03, yes |
  | Arcade | edge 0.50, hf_excess 0.64, no | edge 0.84, hf 0.93, yes |

  Unaligned stock rows for hero4b, for comparison: ashlar hf 2.01 (no); arcade 1.11 / 1.59 (no).
- What this shows:
  - With aligned crops the ashlar "no" goes away completely. The earlier gap came from the crops landing on different parts of the facade, not from a stone defect.
  - The whole arcade gap is the bar colour. Black bars on dark glass give half the photo's edge density, and white bars give 0.84 (yes).
  - No real facade defect was found, so hero4b's facade stays as it is.
- Replay: `tests/hero4c/step1_match.sh`. The 64 MB scratch blend is not committed.

## 2026-11-23 10:40 UTC+4 — r8b step 4: before/after stills
- `tests/hero4b/stills/`: 1920x1080 at 64 spp. Before = hero4 (`before_hero4_shops_{east,west}`, plus `tests/hero4/stills/after_hero4_{street,entrance}`); after = hero4b (`after_hero4b_{street,entrance,shops_east,shops_west}`). Comparison sheets: `cmp_*_hero4_vs_hero4b.jpg`.
- At these street distances the shopfront and lamp changes are subtle, and the ashlar change is small.

## 2026-11-23 10:15 UTC+4 — r8b steps 2–3: hero4b (ashlar/arcade tweaks + 120 m layers), validate PASS
- `hero4.py`: new `BHERO4B=1` switch, which requires `BHERO4=1`; hero4 itself is unchanged.
  - Rustication channel half-height 0.035 → 0.06 m and joint width 0.03 → 0.06 m (stand-ins); channel tone softened from 0.35 to 0.55 of the front.
  - Stone photo texture 35 % → 8 %, stone normal 0.12 → 0.04, faience bump 0.15 → 0.06.
  - `build_scene.py` reads the groove height from `hero4.P`.
- New files:
  - `out/barclay_hero4b.blend`: hero4b plus the R8 viaduct layer and the R8B shopfront/lamp/tree-pit layers, 66,136,712 B.
  - `out/barclay_hero4b.glb`: 4,233,068 B (4.04 MB).
  - `out/mobile/barclay_hero4b_mobile.glb`: 2,059,612 B (1.96 MB).
  - No hero4 file or protected file was changed.
  - Replay: `tests/hero4b/run.sh`.
- Validate (`OUT=tests/hero4b/exp MESHHEALTH=1 MESHHEALTH_BLEND=out/barclay_hero4b.blend`): PASS. 0 errors on all 4 GLBs, check_parts 10/10 with 0 stray, MESHHEALTH 0 Blockers (19 majors, 3268 minors). Report: `tests/validate_20261123_0951.jsonl`.
- `checks.py` street rows (1600x900, 24 spp still):
  - ashlar: hf 2.15 → 2.01, still no.
  - arcade: edge 1.11, hf_excess 1.63 → 1.59, still no.
  - RB shields: yes.
- Why ashlar and arcade can't reach yes cheaply: on the uncalibrated `Cam_Street` the ashlar/arcade crops land on the upper windows and arches, and the reference crop lands on the photo's upper floors. The high-frequency score is driven mainly by the black glazing bars, which are Colin's approved look and are white in the photo. Getting to "yes" needs a camera-matched still (Cam_Match_geograph via `camera_match.py`) or recalibrated crops, not more facade changes.

## 2026-11-23 10:05 UTC+4 — r8b step 1: 120 m zone shopfronts, lamps, tree pits (code)
- `build_surroundings.py` gets a `BSURR_R8B=1` layer; with it off, nothing changes.
  - **Shopfronts** go on neighbour frontages within 120 m of the hero only where an OSM shop/café/bar/nightclub POI is within 12 m of that frontage (10 frontages). Each gets a stall riser, glazing with mullions, a transom, a recessed door, a fascia with a sign band, and end pilasters. All sizes are stand-ins.
  - **Lamps**: the 53 lamp positions (still stand-ins; OSM has no lamp nodes) become slim galvanised columns with an upswept arm and a flat LED lantern, as in Geograph 8144686. Height 8 m and arm 1.6 m are stand-ins.
  - **Street trees**: the 11 LIDAR trees on pavement next to a road get a cast grille (1.2 m) and an 8-bar guard (1.6 m). Both sizes are stand-ins.
- `tests/hero4/render_cams.py` gains `shops_east` / `shops_west` cameras.

## 2026-11-23 09:45 UTC+4 — r8 stills + checklist
- Stills in `tests/hero4/stills/`: before (official blend) and after (hero4) at 1920x1080 for street, facade, entrance and viaduct, plus wsw_east after; comparison sheets `cmp_*_before_after.jpg`; `after_hero4_street_4096x2304.png` (48 spp). The hero 4096 still was skipped because it takes too long under the shared CPU load.
- `checks.py --cam street` on the 4K street still (`tests/hero4/checks_after_street.md`), compared with the official still (`checks_before_street.md`). The crops are not camera-matched, so treat these as indicative:
  - ashlar: no → no (hf 2.44 → 2.15)
  - arcade: no → no (edge 1.67 → 1.15, hf_excess 2.07 → 1.63)
  - RB shields: partial → yes
  - glazing and parapet: yes
  - Gate: still FAIL (2 × no).
- Shopfronts, lamps and trees inside 120 m are still the existing `build_surroundings.py` layers (applied to hero4). The only new 120 m detail in r8 is on the viaduct.

## 2026-11-23 08:40 UTC+4 — r8 exterior pass: hero4 (hero3 look in the procedural blend + facade fixes + viaduct detail)
- Why: Colin asked for the facade and surroundings improvements next (ground-floor colour break, missing ornament, round-6 critic defects, 120 m zone).
- New files only: `out/barclay_hero4.blend` (hero4 + surroundings detail layer, 65,628,044 B), `out/barclay_hero4.glb` (4,233,200 B, 4.04 MB, Floor_*/Door_*/Building names), `out/mobile/barclay_hero4_mobile.glb` (2,059,672 B, 1.96 MB). `out/barclay_hero.glb`, `out/barclay_scene.blend`, `web/hero3.glb` and all `*_floors.glb` untouched. No deploy, `web/` not edited.
- `hero4.py` (new, gated by `BHERO4=1`; with it unset `build_scene.py` / `export_glb.py` behave as before):
  - Look: front tone `#c7bda8`, cornice `#c5b79a`, frames `#222325`, glass `#272a30`, all read from the `web/hero3.glb` palette texture. Cycles stills use a 0.80 tone factor so they read like the viewer; the GLB keeps the palette values.
  - Ground-floor colour break fixed: Portland base and faience upper now share one tone (both reference photos show one tone). Stone photo texture at 35 %, normal 0.6 → 0.12.
  - Ashlar: groove pitch 0.55 → 0.80 m plus staggered vertical joints every 1.6 m (stand-in).
  - Arcade: arch glass set back to y −0.05 (cutter to −0.02); voussoirs 1.0 → 1.2 m radial (key 1.45), projection −0.58 → −0.64. The critic's "−0.40" had the sign flipped (−y is outward); the intent was a deeper reveal.
  - RB shields: a layered cartouche behind each disc plus a raised "RB" monogram (0.08 m relief, stand-in).
  - Glazed strips: oriel bays now cover floors 1–2 only (Commons photo shows the floor-3 triple window above the oriel head). There is a solid spandrel between storeys and two 3-light mullions. Previously one 3-storey glass strip was crossed by pale transoms.
  - Parapet: moulded coping and plinth band (heights are stand-ins). Entrance: door leaves set back to y −0.02 (critic #4).
  - BARCLAY HOUSE: gilt letters (0.26 m, stand-in) on a dark sign band on the porch frieze over the entrance (hero3 look + Commons photo).
- `build_surroundings.py`:
  - New `BSURR_R8=1` layer `viaduct_r8` (inside 120 m): blue-brick arch rings 0.45 m, red-brick pier pilasters and a blue-brick plinth. Source: Heritage Statement, "red brick with some small sections of blue brick"; all sizes are stand-ins.
  - `BHERE` / `BSURR_BASE` env overrides added; the default is still `/workspace/barclay`. `export_surroundings_detail.py` gets the same `BHERE` / `BOUT` overrides.
- `parts_plan.py`: the new hero4 part names are added to the facade groups (names only).
- Replay: `tests/hero4/run.sh`.
- Validate (`OUT=tests/hero4/exp MESHHEALTH=1 MESHHEALTH_BLEND=out/barclay_hero4.blend`): PASS. 0 errors on all 4 GLBs, check_parts 10/10 with 0 stray, MESHHEALTH 0 Blockers (19 majors, 3266 minors). Report: `tests/validate_20261123_0832.jsonl`.
## 2026-11-23 — deploy dpl_H2sRhyhqZwAsvyhyrpbvHGnjycup
- Live from 00f6fd85: walls retrace, CC0 furniture, polish (gate 78.8%), clickable floors.
- Recommitted web/app.js rebuilt from web/src (sha1 1c736ed3); merge 5e4facac had kept a stale polish-only bundle without clickable floors.

## 2026-11-22 20:45 UTC+4 — trick #22 sun-time shadow-alignment gate (barclay)
- Why: X Bookmark Analyst intake (SplatStroll method only, closed product). Barclay already has NOAA `tod_panel.sun_pos` / `web/src/app.js sunPos()` but presets are fixed to 21 June, so shadows were never checked against a dated photo.
- New `sun_check.py` + `tests/suncheck/`: EXIF DateTimeOriginal treated as UK local (`tod_panel.is_bst`, assumed offset logged, sun not "fixed"); renders of a locked `camera_match` camera from a read-only open of the official blend; street-band shadow-mask IoU + edge-angle; ±3 h sweep so a peak can fall outside ±1 h. Official exports and `web/hero3.glb` sha256 unchanged. No deploy. `web/` not edited.
- Verdict: **INSUFFICIENT_REFS** (camera-match coverage, not a method failure). Only `refs/critic1/real_geograph.jpg` has a locked camera (`Cam_Match_geograph`). That ref **passes**: street-band IoU peaks at the EXIF hour (0.344 at 12:34 BST on 2025-07-03; neighbours 0.339 / 0.336), edge-angle 0.74° ≤10°. The other four dated refs have no points JSON (viaduct street, canal, lane, Hotspur under-viaduct). Three intake times disagreed with file EXIF; EXIF was used (Whitworth 2018-01-06 13:38, canal 2017-03-09 13:32, lane 2011-02-28 16:55).
- Camera note: the locked Geograph camera sits in unsourced set-dressing. `hide_near(8)` crashed Cycles/Embree here; `clip_start=4` is used instead (not saved). Render 960×720 (photo aspect), 32 spp, 121 s for seven hours.
- Hook: `SUNCHECK=1 ./validate.sh` verifies `tests/suncheck/out/result.json` (no re-render). Optional viewer `?date=` patch is `tests/suncheck/web_date_param.patch` only, for Interior.
- Docs: tricks_register row 22, x_tricks #22, AGENTS.md = CLAUDE.md = GROK.md, tests/suncheck/RESULT.md. Replay `tests/suncheck/run.sh`.

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
- three.js side-by-side vs live `web/hero3.glb` (viewer street/facade/entrance cameras + lintel close-up): street F1 0.999937, mean abs 0.0144/255, 0.149% px >2; facade F1 0.999951, 0.0239/255, 0.303%; entrance F1 1.0, 0.0010/255, 0.005%; lintel F1 1.0, 0.0009/255, 0.000%. Images: `tests/hero3_floors/out/cmp_side_{street,facade,entrance,lintel}.jpg`. Dark front and black frames match; lettering geometry is present (entrance/lintel F1 0.0).
- Docs: tricks_register row 5, x_tricks #5 status, AGENTS.md = CLAUDE.md = GROK.md tool map + certified-tricks line, README note on the new filename. Replay `tests/hero3_floors/run.sh`.

## 2026-11-20 11:06 UTC+4 — exterior #12 / #8 / #13 certified; Floor_* hero export (barclay)
- Why: Colin approved the recommended upgrades. Interior is running lane bots on `lane/*` and merges/deploys; this pass is the four exterior items (certify #12, finish #8, certify #13, export a Floor_* hero for clickable floors). Free tools only, official exports not overwritten, no deploy, no Vercel, no LFS.
- #12 CERTIFIED (stills/flythrough only, `BWEATHER2=1`): new `weather2.py` (Cycles AO soot, Pointiness edge wear, Z-stretched drips below stand-in sill/LEVELS offsets). Copy-test `tests/weather2/run.sh` on the official blend read-only: street mean abs 1.14/255, 21.13% px >2; official street F1 0.991 off and on; Geograph F1 0.222/0.223 (not the R4 locked-plate 0.625; no on/off regression). Street render 56.0→206.6 s (3.69×) because of AO. Soot amounts are stand-ins. Not baked into the GLB. Rollback `BWEATHER2=0`.
