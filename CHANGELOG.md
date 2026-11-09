# CHANGELOG

## 2026-11-09 — interior-backup branch

- Branch `interior-backup`: Interior bot backup (Two Bed bake, viewer, Floorplan 3D Walk mode, shots, FINDINGS/critic_log).
- Chair-fixed `twobed.glb` / `twobed_m.glb` (sha 130eda10… / 49a2ef6f…), geometric facing check `ang = a - π/2`.
- Merged on top of `perf/viewer-speed` (`hero_mo`/`context_mo`, `vercel.json`, on-demand render); stripped `__lookAt`/`__drawcalls` debug hooks.
- Live deploy `dpl_745x9tBVeNR97MqscvVLfiU45SrC` (app.js?v=38). See README_INTERIOR.md.
