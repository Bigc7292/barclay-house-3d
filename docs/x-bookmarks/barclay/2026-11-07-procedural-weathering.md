# Barclay House: procedural-weathering
Date: 2026-11-07 · Source note: notes/2117640443345379421.md
Status: proposed · Owner: Barclay House 3D · Briefed: brief drafted 2026-11-07 (with x_tricks #12–#14), sent by parent; pending certification

WHAT: step 4 "grime" + step 6 "close-up critique" of the MCP-for-Blender photoreal recipe (https://www.mcp-for-blender.com/blog/photorealistic-renders/, via https://x.com/sidahuj/status/2117640443345379421): layered procedural wear from shader nodes, placed where water and soot really collect.
WHY: build_scene.py `weather(m, dirt, streak, band)` is a uniform stand-in (z-band darkening + stretched noise); critic_log R3/R4 keeps "soot and weathering" as a stand-in and the viaduct parapet still "reads salmon/orange" in sun. Geometry-aware grime breaks the CG-clean look on the hero and darkens sun-facing tops naturally. Head-to-head: existing weather() = cheap, global; new = location-aware → hybrid (keep weather(), add mask layer). Lenses: quality gain, viz gain, efficiency none, UX none.
HOW:
1) build_scene.py: new `weather2(m, soot=0.3, drip=0.25)` called after weather(): masks = Ambient Occlusion node (Cycles, distance 0.3 m, inside off) inverted → crevice soot; Geometry Pointiness → edge wear (light chipping on terracotta arrises only); gravity drips = Object-coord noise stretched in Z (scale 1.5,1.5,0.05) multiplied by a "below overhang" mask (Normal.z < −0.3 projected down via a Z gradient from sill/cornice heights in scene_data.json).
2) Multiply into Base Color (as weather()) and raise Roughness +0.1 in grime areas; behind env flag `BWEATHER2=1`.
3) Apply to faience/terracotta/stone/Viaduct_brick; parapet tops get soot via the AO mask (fixes salmon read without guessing albedo).
4) Step 6 critique: from camera_match.py locked cams render 4 close-up crops (cornice, oriel, doorcase, parapet) at 960x540 and compare to refs/ crops; one fix per pass (x_tricks #1).
5) Test on tests/ copy → ref_check.py; then export_glb.py (note: AO node is Cycles-only → bake grime to the GLB only if the mobile budget allows; else stills/flythrough only).
CHANGES: build_scene.py (+weather2, ~40 lines, flag), critic_log.md entry, tests/trickcheck/weather2/.
EFFORT S-M · RISK low (shader only; Cycles AO node adds ~10% render time) · ROLLBACK BWEATHER2=0.
LICENSE: Blender GPL, mcp-for-blender MIT; no textures needed.
COST: £0 (Opus/ChatGPT in the recipe not needed — use refs/ photos as reference).
SUCCESS: ref_check edge/colour score on street + viaduct cams ≥ R4 values; critic no longer lists "soot and weathering" as stand-in defect; parapet top reads brick-red not salmon; validate.sh PASS.
