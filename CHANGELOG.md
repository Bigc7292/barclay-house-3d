# CHANGELOG

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
