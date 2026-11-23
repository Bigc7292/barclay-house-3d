# Barclay House 3D (35 Whitworth St W, Manchester M1 5NG)
Photorealistic exterior + surroundings model (Blender -> GLB) and web viewer (`web/`, deployed at https://barclay-house-viewer.vercel.app). Interior/apartments in `interior/`.
## Resume
1. Read `AGENTS.md` (= CLAUDE.md = GROK.md) first: hard rules (free only, no estimates, sourced facts), fixed pipeline, lessons.
2. Then `critic_log.md`, `tricks_register.md`, `x_tricks.md`, `optimizer_log.md`, `PLAN.md`, `TOOLS.md`.
3. Pipeline: source facts -> build one change set (Blender scripts) -> render locked camera + `ref_check.py` -> critic round -> export, `./make_mobile.sh`, `./validate.sh` (must PASS) -> redeploy viewer -> `./backup.sh "msg"`.
Layout: `out/` exports (GLB/FBX/renders), `out/mobile/` phone GLBs, `web/` viewer, `lidar/` EA LIDAR, `textures/`, `refs/` reference photos, `docs/`, `tests/` experiments. See SETUP.md. Floor_* / Door_* heroes: `out/barclay_hero_floors.glb` (official pale blend look) and `out/barclay_hero3_floors.glb` (live `web/hero3.glb` archive look — dark front, black frames, BARCLAY HOUSE lettering). Never overwrite `out/barclay_hero.glb`, `out/barclay_scene.blend` or `web/hero3.glb`. r8 hero4 (hero3 look rebuilt procedurally with facade fixes; `BHERO4=1`, replay `tests/hero4/run.sh`): `out/barclay_hero4.glb`, `out/mobile/barclay_hero4_mobile.glb`, `out/barclay_hero4.blend`. The main viewer loads `web/hero4c.glb` / `web/hero4c_mobile.glb` (copies of `out/barclay_hero4c.glb` and its mobile build: hero4b without the lower RB shields on the oriel heads; `BHERO4C=1`, replay `tests/hero4c/run.sh`) and falls back to `hero4b.glb` / `hero4b_mobile.glb`. `hero4` / `hero4_mobile`, `hero3_floors` / `hero3_floors_m` and `web/hero3.glb` stay in `web/`.

## Branches
- **`barclay` = integration branch. All bots working on Barclay House push here** (Colin's rule, 2026-11-09). Commit + push after every edit and add a CHANGELOG.md entry saying what changed and why. Never force-push or rewrite history; if a push is rejected, `git fetch` and merge `origin/barclay`, then push.
- Feature branches (kept for history, all merged into `barclay`): `feat/floorplan3d-2bed` (trick #14), `feat/refchecklist-gate` (trick #15), `feat/streetlife-canalwater` (tricks #9/#10), `interior-backup` (Interior bot), `perf/viewer-speed` (live viewer speed fix). `main` = older baseline. `viewer/unified` = in-progress viewer work (not yet merged at the time of writing).
- Worktrees on the box: `/workspace/barclay-wt-main` (branch `barclay-integration`, pushes to `origin/barclay`), `/workspace/barclay` (local `barclay`), plus one per feature branch.

### What is NOT in git, and why
- `.venv` / Python venvs (`/home/box/venv`, `/home/box/bvenv`) – rebuildable from `requirements-venv.txt`.
- `__pycache__/`, `*.blend@`, `*.blend~` – Python bytecode and Blender temp/lock files (see `.gitignore`).
- Files over 100 MB – GitHub rejects them; Git LFS is NOT used (can cost money; no `.gitattributes` LFS filters in this repo). Current largest tracked file: `out/barclay_scene.glb` 95.2 MB (under the limit). `backup.sh` blocks anything >99 MB; free fallback for any future big file: `split -b 90m` into parts committed in git, or a Google Drive copy.
- Everything else, including `node_modules` used by the tools (`.gltf/`, `web/src/`), is committed.

### Box sweep (2026-11-09)
Project files found outside the repo were copied (originals left in place): `docs/x-bookmarks/barclay/` (X Bookmark Analyst trick briefs), `docs/x-bookmarks/offplan-related/` (briefs for #13 and #14), `archive/box-sweep-2026-11-09/{critic2,critic4,barclay-deploy-out,perf-scratch}` (critic shots, Vercel deploy payload, viewer perf measurements).

## Viewer deploy (single source, 2026-11-09)
- **Source of truth:** branch `barclay` of github.com/Bigc7292/barclay-house-3d, folder `web/` (viewer source `web/src/app.js` -> minified bundle `web/app.js`; bump `app.js?v=N` in `web/index.html` on every change). Not barclay-house-archive (read-only history; never push its main).
- **Method:** `web/deploy.sh` (fetches origin/barclay into /workspace/barclay-deploy, rebuilds app.js with esbuild, writes /workspace/barclay-deploy-out/manifest.json + b64 files), then the Vercel connector: `upload_file` for changed files, ONE `create_deployment` {project barclay-house-viewer, target production, skipAutoDetectionConfirmation "1", files = manifest}.
- **Top-level upload only:** paths like `index.html`, `app.js`, `hero3.glb`. NEVER a `vercel-live/` prefix (caused a 404 outage 2026-11-09 08:33-08:39 UTC+4).
- **Required files:** listed in `web/deploy.sh` FILES (index.html, app.js, vercel.json, env*.hdr, hero3/hero_mo3, hero3_floors/hero3_floors_m, hero4/hero4_mobile, hero4b/hero4b_mobile (fallback), hero4c/hero4c_mobile (clickable Floor_* exterior), context_typed_opt/context_mo, ext7_street/_o, twobed_v5/_m (main viewer), twobed/_m (walk mode), tex/, water/, video/, floorplan3d/ + vendor licences). deploy.sh exits on any MISSING file.
- **Verify right after:** `curl -sI` on /, /app.js, /hero3.glb = 200; `node /workspace/perf/m.mjs https://barclay-house-viewer.vercel.app/ desktop` and `... phone` -> errs [] and s404 []. Roll back with the Vercel dashboard "Promote" on the previous deployment if not.
- **Perf rules (keep):** render on demand; static shadow map (needsUpdate on ToD/load); SSAO+bloom desktop only, half-res, SSAO skipped while moving (progressive refine); DPR cap 1.5 desktop / 1.25 phone + adaptive; phones load meshopt `_mo`/`_o` GLBs and `tex/*_m.jpg`; Water2 desktop only.
- **Git auto-deploy (2026-11-09, setup):** Vercel project `barclay-house-viewer` is to be Git-linked to `Bigc7292/barclay-house-3d`, **production branch `barclay`, Root Directory `web`**, framework Other, no build/install command (static). The repo link + branch tracking is a dashboard step (Settings -> Git -> Connect; Settings -> Environments -> Production -> Branch Tracking = `barclay`); the connector cannot link. Once linked, every push to `barclay` deploys production.
  - `web/.vercelignore` is a whitelist AUTO-GENERATED by `deploy.sh` from FILES, so a Git build ships exactly the same 67 files as a deploy.sh upload (no src/, node_modules, shots/, *.b64). After adding a file to FILES, run `web/deploy.sh --local` and commit the regenerated `.vercelignore` with the asset.
  - `web/app.js` is committed pre-built (Vercel does not run esbuild): rebuild with deploy.sh or esbuild and commit app.js + bumped `?v=N` together.
  - Never push to the GitHub default branch expecting production; only `barclay` is production. deploy.sh + connector stays as the manual / emergency path (rollback: Promote the previous deployment, last known good dpl_H7TqPZYWijdZAYP5PnbDbDVkMnNd, v41).

## Rochdale Canal (viewer, 2026-11-23)

The live context mesh `web/context_typed_opt.glb` (mobile: `context_mo.glb`) used to cover the Rochdale Canal behind Barclay House with a pale paved slab, so only a thin strip of water showed at the rear. That covering is **not** in the hero4c exterior GLB.

The viewer now cuts the context ground out of the OSM water footprint and dresses the cut with water, stone coping and canal walls (`web/src/canal_fix.js`, `web/src/canal_footprint.json`).

**OSM sources** (OpenStreetMap, ODbL; local extract `area.osm` / `scene_data.json`, bounds 53.4707,-2.2487 to 53.4779,-2.2367):

- Way **243445859** — `natural=water`, `water=canal`, `layer=-1`. Basin immediately behind the building. Width ≈ 7.97 m (polygon area / half-perimeter). Water surface Y = **-0.91 m** in viewer space, from the Blender `Canal_water` mesh extracted by `canal_web.py` into `web/src/canal.json`.
- Way **28047783** — `waterway=canal`, `name=Rochdale Canal`, `towpath=left`. Centreline along the rear.
- Way **28047773** — Tib Lock 89 (`lock=yes`, `lock_name=Tib Lock`, `lock_ref=89`).
- Way **28047776** — Rochdale Canal centreline, `towpath=left`.
- Way **670994990** — Manchester and Salford Junction Canal.
- Way **165386101** — Bridgewater Hall Basin (`natural=water`, `water=canal`).
- Way **449235693** — towpath (`highway=footway`, `towpath=yes`, operator=Canal & River Trust, `surface=paving_stones`). Left in place; not cut.

**Covering meshes (cause):** desktop node `road_27605679` (material `Paving.001`, a merged paved surface, not just OSM way 27605679) at world Y ≈ 0.11–5.5 m, at and above the water; `road_783670` (Asphalt.001) in places; `bldg_31176345` (Neighbour) open-ground faces; mobile also `Terrain_EA_DTM` (Ground). The viewer discards fragments of those context materials whose XZ lies in the footprint. **hero4c does not contain the slab** — no source change is required in the hero GLB. For a lasting fix in the surroundings export, cut those faces out of `road_27605679` / `Terrain_EA_DTM` (and the Neighbour ground) against way 243445859. `water_ripple.py` already has a terrain cut; it did not reach `context_typed_opt.glb`.

**UNSOURCED:** `wall_below_water_m` (0.80) and `coping_width_m` (0.35) are typical narrow-canal figures, not a cited gauge at Tib Lock 89. For way 243445859 the coping sits at the context paving elevation (`road_27605679` world Y ≈ 0.11 m at the canal edge) and the water is at −0.91 m, so the visible drop is about **1.02 m** (from those two elevations, not from a Canal & River Trust gauge).

**Water:** existing bundled three r170 Water2 (MIT) plus CC0 `web/water/Water_*_M_Normal.jpg`. Dark green-brown tint, gentle ripple. Phones keep the cheap scrolling material unless `?water=1`. No extra network requests. Rear view preset: `?cam=canal`.

