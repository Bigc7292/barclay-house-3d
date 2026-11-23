# CHANGELOG

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
