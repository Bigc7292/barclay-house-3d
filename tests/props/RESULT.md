# Trick #13 — street-prop normaliser + LOD1, copy-test

**Verdict: CERTIFIED.** Official `out/barclay_scene.blend`, `out/barclay_hero.glb` and `web/hero3.glb` were not written. LIFE actors are still not exported by `export_glb.py`.

## What shipped

- `props_dims.json` — sourced sizes or labelled stand-ins (URL per row where found).
- `props_normalize.py` — imports Kenney CC0 kits, bottom-centre origin, front −Y, uniform scale to the sourced primary dim, ≤6 shared palette materials, LOD1 decimate ~25% tris. Writes `assets/life/normalized/*.glb` + `kit.json`.
- `life_paths.py` prefers the normalised GLB at scale 1. The viaduct train keeps the certified #9 `keep_life_scale` (not silently retargeted).
- Lineup with a visible 1 m scale bar: `tests/props/out/props_lineup.png`.
- Copy-test: `tests/props/run.sh` (Khronos / gltf-transform validate on every GLB, `tests/props/score.py`).

## Evidence (`tests/props/out/result.json`, pass=true)

| prop | primary | error | origin z | LOD1 tris / ratio | notes |
|---|---|---|---|---|---|
| kenney_sedan | length 4.378 m | 0.000 m | 0.000 | 508 / 0.250 | 2018 Ford Focus 5-door, Ford EU media PDF. Toy stand-in. |
| kenney_van | length 4.973 m | 0.000 m | 0.000 | 520 / 0.250 | Typical UK mid-size van length, stand-in (no Ford PDF archived). |
| kenney_train_car | keep_life_scale | — | 0.000 | 281 / 0.249 | Certified #9 stand-in scale left alone. |
| kenney_walker_male | height 1.755 m | 0.000 m | 0.000 | 192 / 0.249 | HSE 2019 mean men 175.5 cm (NHS Digital 2021 trends). |
| kenney_walker_female | height 1.617 m | 0.000 m | 0.000 | 197 / 0.249 | HSE 2019 mean women 161.7 cm. |

All five Kenney GLBs and their LOD1 copies: gltf-transform validate clean. Materials remapped onto a 6-name palette (each file uses 1–6 of `PROP_{paint,metal,glass,rubber,fabric,wood}`).

Procedural surroundings props (lamp 6.0 m, bollard 1.0 m / Ø 0.10 m, Type A/B pillar box 1.626 m, waste 0.95 m, bench 0.45 / 1.8 m, signal 3.3 m) are documented in `props_dims.json`. Lamp, bollard and pillar-box figures are typical-UK stand-ins (Durham lighting spec, MK F10, wicks.org); waste / bench / signal heights were NOT FOUND for this site and stay at the current stand-in values already in `build_surroundings.py`.

## Fix applied during the copy-test

The first run left the Kenney walkers at native height (~0.67 m, height_err 1.08 / 0.89 m) because scale was applied only to parentless meshes and the characters are a parented node tree. `normalize_one` now unparents with keep_transform, then bakes loc/rot/scale into mesh data. Re-run: height_err 0.000 m.

The 1 m scale bar was first built along X (end-on to the side-view camera) and sat under the sedan; it is now a 1 m vertical post + 1 m ground bar to the left of the lineup.
