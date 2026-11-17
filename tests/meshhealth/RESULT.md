# Trick #19 copy-test (2026-11-17 20:21 Asia/Dubai)

Scene: `tests/meshhealth/barclay_scene.blend` (copy of `out/barclay_scene.blend`). The official blend was not saved (mtime stayed 2026-11-15 20:55 Asia/Dubai). `web/*.glb` and `out/*.glb` were not written.

- `mesh_health.py` 8.81s on the copy, 9.11s on the official blend (both under 60s).
- Status **PASS**: Blockers 0, Majors 1442, Minors 3351. 6619 exported meshes (1471 Hero).
- Majors: 1430 Hero `*.001` names (saved blend predates the #16 unique-name pass; not rebuilt so a good export was not overwritten); 6 `HERO_fan_hub*` with duplicate verts and zero-area faces (open, not fixed this pass — no Blockers to fix).
- Duplicate-mesh groups for register #7: **22 unshared** groups (150 objects, 0 groups already share datablocks). Largest: 106 `tree_crown*` copies; the rest are tree crowns and viaduct piers in 2–3 copies.
- `./validate.sh` still PASS with MESHHEALTH unset. `MESHHEALTH=1 ./validate.sh` also PASS (0 Blockers).
