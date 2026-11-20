# Trick #12 copy-test (procedural grime) — 2026-11-20 Asia/Dubai

Opened official `out/barclay_scene.blend` read-only (mtime unchanged). Applied `weather2.py` in memory behind `BWEATHER2=1` to `White_glazed_faience_Burmantofts`, `Portland_stone_base` and `Viaduct_brick`. Never saved the .blend; never wrote official `out/` or `web/` GLBs.

## Verdict: CERTIFIED (stills / flythrough only; off by default)

Geometry-aware soot/drips land in crevices, window reveals, cornice undersides and rustication (see `out/w2_diff` via the on−off pixel map). The official street silhouette is preserved. The shader is Cycles-only (AO + Pointiness) and is **not** baked into the hero GLB (`export_glb.py` remaps materials). Rollback: `BWEATHER2=0` (default).

Soot strength, drip length (0.9 m) and sill offsets remain visual **stand-ins** (no site weathering survey). Existing `weather()` is kept (hybrid).

## Measurements (960×540, Cycles CPU, 64 spp, OpenImageDenoise)

| cam | off time | on time | ratio | pixel mean abs | % px changed (>2/255) |
|---|---:|---:|---:|---:|---:|
| Cam_Street | 56.0 s | 206.6 s | 3.69× | 1.14 / 255 | 21.13% |
| Cam_Match_geograph | 73.5 s | 242.5 s | 3.30× | — | — |
| Cam_Viaduct | 97.6 s | 170.9 s | 1.75× | 0.88 / 255 | 16.65% |

Street crop means (RGB 0–255):

- Parapet off 113.8, 109.3, 101.1 → on 112.7, 108.8, 101.3 (slightly darker; not a salmon-wash scene to begin with).
- Facade (faience) off 133.5, 131.7, 127.3 → on 133.4, 131.8, 127.6 (essentially unchanged).

`ref_check.py` vs official `out/render_street_4096x2304.png`: edge F1 **0.991** off and **0.991** on (precision 1.000 / 0.999). No silhouette regression.

`ref_check.py` vs Geograph (`refs/critic1/real_geograph.jpg`) at 960×540 with an appended `Cam_Match_geograph`: F1 **0.222** off / **0.223** on (no on/off regression). This is **not** comparable to the R4 locked-plate F1 0.625 (`tests/match_geograph_p3_oriel3.png` was a different resolve/resolution); the apples-to-apples gate here is the official street still.

Render cost is higher than the brief's "+10%": Cycles AO at 0.3 m is about **3.7×** the street-cam time at this resolution. Acceptable only because the flag is off by default and is for stills/flythrough, not the viewer GLB.

## Files

- `weather2.py`, hooked from `build_scene.py` when `BWEATHER2=1`
- Stills and `result.json` in this folder's `out/`
