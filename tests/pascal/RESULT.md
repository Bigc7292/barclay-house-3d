# Trick #20 Pascal Editor vs #14 Floorplan 3D — scorecard (2026-11-19, Asia/Dubai)

Sources: brief `/home/box/x-bookmarks/implementations/barclay/2026-11-19-pascal-editor.md`; CLI https://github.com/pascalorg/editor MIT 1.1.6; plan `interior/twobed/apt02_fp.png` (Rightmove 92163630); area 63 m² from https://barclay-house.com/two-bedroom-apartment/ and the same listing (679 sq ft). Nothing invented.

## Environment
- `npx @pascal-app/cli editor --no-open` with `PASCAL_HOME=tests/pascal/.pascal`. Runtime 127.6 MB from the GitHub release, digest-verified, **not committed**. No Pascal account (`ownerId` null). Hosted MCP not used. Local MCP on loopback only.
- Linux box (CLI docs say macOS is the verified platform; the editor and MCP nevertheless came up healthy here).

## #18 plan overlay (same gate for both layouts)

| Layout | IoU identity | IoU buffered ±4 px | Layout-on-ink precision (2 px) | Area vs 63 m² |
|---|---:|---:|---:|---|
| #14 `build_twobed_v4.py` walls (`tests/pascal/layout_2bed.json`) | **0.1408** | **0.2999** | **0.5733** | 63.00 m², residual **0% by construction** |
| Pascal centreline trace (`tests/pascal/layout_pascal.json`) | **0.4691** | **0.4336** | **0.9168** | outline scaled to 63; Pascal auto-zones 54.8+4.94+3.24=**62.98 m² (−0.03%)** |

- Gate IoU ≥ 0.85: **FAIL** for both. The plan PNG’s ink includes furniture linework; there are no printed dimensions to align by. The #14 failure is also geometric: v4’s right-wall kink is at plan y=180, but thick ink is already vertical by y≈108.
- Overlays: `out/plan_overlay.png`, `tests/pascal/out/plan_overlay_2bed.png`, `tests/pascal/out/plan_overlay_pascal.png` (red = layout not in plan ink, blue = plan ink missed).

## Pascal scene (local MCP, not a drop-in walk-mode model)
- 24 walls, 5 doors (entrance gap x=99–129 and bath door y=268–298 measured on the PNG; bedroom/storage openings as seen on the plan; door leaf height 2.1 m and clear ceiling 3.0 m are **UNSOURCED** modelling values, same family as #14).
- `verify_scene` valid; 1 occupied storey; 3 auto-zones (bedrooms were not closed into separate zones).
- Saved locally as scene `8ef51e1e8eb7` (graph in `tests/pascal/out/pascal_scene_graph.json`).

## GLB / viewer head-to-head
- Official `export_glb`: **`not_implemented`** — “GLB export requires the Three.js renderer, which is browser-only.”
- `view_scene`: **`view_unavailable`** — “This Pascal server has no editor to render with.”
- Send to Blender already broken (pascalorg/editor issue #899); not used.
- **No Pascal GLB was produced**, so desktop 1600×900 and Galaxy S9+ console errors, external requests, and fps could not be measured for a Pascal runtime.
- #14 walk-mode files, re-validated this run: `web/twobed.glb` **1.41 MB**, `web/twobed_m.glb` **1.27 MB**, Khronos **0 errors**. Certified #14 headless result remains `tests/floorplan3d/check_result.json` (0 console errors, 0 external requests, walk collision).
- `OUT=tests/pascal/out ./validate.sh` **FAIL** as expected: that script checks exterior `barclay_hero.glb` / surroundings budgets, which this interior test does not write.

## Verdict
**REJECTED for adoption into `web/floorplan3d`.** Keep #14 walk mode. The Pascal *trace* is the better plan fit, but official GLB export did not run in this local/headless setup, and a walls-only Pascal scene would drop the baked furnished model, door carve, and collision that walk mode depends on. Cutaway / exploded / 2D–3D split were not measurable without the renderer. Exterior Blender files were not modified. No Vercel deploy.
