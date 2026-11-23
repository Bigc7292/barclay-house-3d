# Trick #8 — displacement (street camera), copy-test

**Verdict: CERTIFIED (bump only, stills / street cam, `BDISP=1`).**
True displacement + adaptive subdiv (`BDISP_ADAPTIVE=1`, method BOTH) is **REJECTED** as unsafe on the booleaned hero facade slabs.

Official `out/barclay_scene.blend`, `out/barclay_hero.glb` and `web/hero3.glb` were not written. Default look is unchanged (`BDISP` off).

## What shipped

- `derive_height.py` writes 16-bit `textures/{stone,terracotta,brick}/{height,ao}.png` from the existing Poly Haven CC0 `nor.jpg` (Poisson integrate, 2048×2048).
- `displace.py` hooks a dedicated Object-space height → Displacement node (scale 0.006 / 0.004 / 0.006 m, midlevel 0.5). In Blender 4.2 the method lives on `material.displacement_method` (not `m.cycles.displacement_method`).
- `BDISP=1` uses method **BUMP**. Not baked into the GLB (export remaps materials).
- `BDISP_ADAPTIVE=1` still exists for experiments: feature set EXPERIMENTAL, SIMPLE subsurf, dicing 2 px, method BOTH. Do not turn it on for hero stills.
- `BDISP_MOSS` left off.

## Safe bump evidence (960×540, 32 spp, Cam_Street, official blend read-only)

| gate | off | on (`BDISP=1`) |
|---|---|---|
| official street F1 | 0.9902 | 0.9905 |
| street mean abs | — | 0.42 / 255 |
| px changed >2 | — | 5.25 % |
| stone-base RGB mean | 105.9, 98.0, 88.1 | 105.8, 97.9, 88.0 |
| terracotta RGB mean | 133.0, 131.6, 127.4 | 133.1, 131.7, 127.5 |
| time | 29.7 s | 50.0 s (1.68×, ≤2×) |
| max RSS | 1709 MB | 1720 MB (no OOM) |

Stills: `tests/disp/out/disp_{off,on}_Cam_Street_960x540.png`. An 8× exaggerated difference shows the change on terracotta pilasters and window surrounds; the rusticated stone base barely moves (already modelled in geometry). Facade, cream frames and openings stay intact.

## Why BOTH + adaptive was rejected

1. First copy-test (CATMULL_CLARK subsurf after a live or applied BOOLEAN:windows) tore the facade: official F1 0.990 → 0.680, mean abs 45.5/255, 54.3 % px changed, terracotta mean 133 → 54. Still: `tests/disp/out/disp_on_Cam_Street_960x540.png` was overwritten by the later bump pass; the torn stills kept for evidence are `tests/disp/out/disp_retest_640x360.png`, `disp_simple_640x360.png`, `disp_live_simple_640x360.png`, `disp_simple_const05_640x360.png`.
2. Root cause A: Catmull-Clark on booleaned window cuts shrinks and melts the slabs. A constant Height 0.5 (zero displacement) still failed.
3. Root cause B: even SIMPLE adaptive dicing (live or applied boolean, constant or mapped height) punches holes through the 0.45 m rusticated base and, with the height maps, shreds the faience. Hooking the same maps with method BUMP or BOTH *without* adaptive subdiv does not.
4. `bpy.ops.object.modifier_apply` on the window booleans also dropped large regions of the stone base (white world showing through).

Time/RAM for the torn adaptive pass still met the ≤2× / no-OOM gates (1.25×, 2.4 GB) — those gates are not sufficient without a look check.

## Stand-ins / limits

- Displacement *scale* follows the trick brief (0.004–0.01 m). The height maps themselves are derived, not surveyed millimetre relief.
- AO maps are written but not yet wired into the street materials.
- Neighbour brick is hooked because the texture folder exists; it is not on the hero street facade.
