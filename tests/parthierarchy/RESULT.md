# Trick #16 copy-test (2026-11-15 20:54 Asia/Dubai)

Scene: `tests/parthierarchy/test_parts.py` (tiny Hero stand-in, not the real building).
Outputs: `tests/parthierarchy/out/` only. `out/` and `web/*.glb` were not written.

- `parts_plan.apply`: missing=[], dotted=[], required names created.
- Desktop `barclay_hero.glb`: Floor_00..05, Door_entrance_L_leaf, Door_entrance_R_leaf, Door_entrance_frame, Facade_01, Facade_upper, Window_01..04 glass/frame (joined within each floor, not across), Building, Parapet. 22 nodes.
- Mobile `barclay_hero_mobile.glb`: same Floor_* and Door_* still present and unmerged across floors/doors. Window_* remain per-floor. Empty `Building` node pruned by gltf-transform (expected; check is on the desktop hero). 21 nodes / 21 draw calls.
- `./validate.sh` (OUT=tests/parthierarchy/out): PASS. Khronos 0 errors, budgets OK, parts_plan_nodes ok (10/10 required, stray_count=0). Report: tests/validate_20261115_2054.jsonl.

Live viewer GLBs (`web/hero3.glb`, `web/hero_mo3.glb`) were not rebuilt or deployed.
