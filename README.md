# Barclay House 3D (35 Whitworth St W, Manchester M1 5NG)
Photorealistic exterior + surroundings model (Blender -> GLB) and web viewer (`web/`, deployed at https://barclay-house-viewer.vercel.app). Interior/apartments in `interior/`.
## Resume
1. Read `AGENTS.md` (= CLAUDE.md = GROK.md) first: hard rules (free only, no estimates, sourced facts), fixed pipeline, lessons.
2. Then `critic_log.md`, `tricks_register.md`, `x_tricks.md`, `optimizer_log.md`, `PLAN.md`, `TOOLS.md`.
3. Pipeline: source facts -> build one change set (Blender scripts) -> render locked camera + `ref_check.py` -> critic round -> export, `./make_mobile.sh`, `./validate.sh` (must PASS) -> redeploy viewer -> `./backup.sh "msg"`.
Layout: `out/` exports (GLB/FBX/renders), `out/mobile/` phone GLBs, `web/` viewer, `lidar/` EA LIDAR, `textures/`, `refs/` reference photos, `docs/`, `tests/` experiments. See SETUP.md.

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
- **Required files:** listed in `web/deploy.sh` FILES (index.html, app.js, vercel.json, env*.hdr, hero3/hero_mo3, context_typed_opt/context_mo, ext7_street/_o, twobed_v5/_m (main viewer), twobed/_m (walk mode), tex/, water/, video/, floorplan3d/ + vendor licences). deploy.sh exits on any MISSING file.
- **Verify right after:** `curl -sI` on /, /app.js, /hero3.glb = 200; `node /workspace/perf/m.mjs https://barclay-house-viewer.vercel.app/ desktop` and `... phone` -> errs [] and s404 []. Roll back with the Vercel dashboard "Promote" on the previous deployment if not.
- **Perf rules (keep):** render on demand; static shadow map (needsUpdate on ToD/load); SSAO+bloom desktop only, half-res, SSAO skipped while moving (progressive refine); DPR cap 1.5 desktop / 1.25 phone + adaptive; phones load meshopt `_mo`/`_o` GLBs and `tex/*_m.jpg`; Water2 desktop only.
