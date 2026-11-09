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
