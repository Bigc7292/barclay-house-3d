# CHANGELOG

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

## 2026-11-09 ~13:20 UTC+4 — production deploy dpl_H7TqPZYWijdZAYP5PnbDbDVkMnNd (barclay 56464d9c, app.js?v=41)
- Deployed via web/deploy.sh + Vercel connector, top-level paths, 67 files. All probed paths 200, 0 console errors desktop + Pixel 7.
- Live verify: facade colour/glazing match archive dpl_6so3k (street/night/aerial side-by-side), BARCLAY HOUSE lettering visible (Entrance), CC0 asphalt + centre dashes, Kenney cars on Whitworth St W + train on viaduct (Traffic toggle).
- Live metrics (SwiftShader headless, ratios only): desktop 10.1 MB transferred, 157 draws, ready 5.2 s; phone 5.0 MB, 56 draws, ready 5.6 s, first view 4.6 s.
