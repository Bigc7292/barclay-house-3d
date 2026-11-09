# CHANGELOG

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
