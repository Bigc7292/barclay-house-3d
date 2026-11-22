# Trick #22 — sun-time shadow-alignment gate

Method only from STUDIO DUCKBILL SplatStroll (closed, no repo). Own
`sun_check.py`, Pillow, Blender GPL, `tod_panel.sun_pos`. £0.

Official `out/barclay_scene.blend`, `out/barclay_hero.glb`,
`out/barclay_hero_floors.glb`, `out/barclay_hero3_floors.glb` and
`web/hero3.glb` were not written (sha256 checked). No deploy. `web/` was
not edited; the optional `?date=` viewer patch is
`tests/suncheck/web_date_param.patch` only.

## Verdict

**INSUFFICIENT_REFS** — the method runs, but the numeric pass rule needs
the IoU peak within ±1 h of EXIF time and a shadow-edge angle ≤10° on
**at least two** camera_match-solvable refs. Only one of the five dated
refs has a locked camera. That is a camera-match coverage limit, not a
failure of the sun / EXIF method.

The one solvable ref, `real_geograph`, **passes** on the street / 
ground-floor band.

## EXIF (used as-is; camera clock)

No `OffsetTimeOriginal` on any plate. Assumed UK local via
`tod_panel.is_bst` (approx. BST if date ≥ 29 Mar and < 25 Oct). The sun
was not "fixed" to match the photo. Three of the five listed intake
times do not match the file EXIF (the Geograph/Commons "date" field);
EXIF wins.

| ref | EXIF DateTimeOriginal | assumed offset | sun el / az | camera_match |
|-----|------------------------|----------------|-------------|--------------|
| real_geograph | 2025-07-03 12:34:22 | BST UTC+1 | 58.7° / 162.8° | yes — `Cam_Match_geograph` |
| whitworth_5809790 | 2018-01-06 13:38:17 (intake said 2018-06-16 15:15) | GMT UTC+0 | 11.8° / 199.8° | no — viaduct street, no points JSON |
| canal_5477629 | 2017-03-09 13:32:11 (intake said 2017-07-27 18:20) | GMT UTC+0 | 29.8° / 200.8° | no — canal/towpath, no points JSON |
| lane_2295568 | 2011-02-28 16:55:07 (intake said 2011-03-28 16:55) | GMT UTC+0 | 6.0° / 247.6° | no — nearby lane, no points JSON |
| hotspur_8088127 | 2025-07-03 12:33:07 | BST UTC+1 | 58.7° / 162.2° | no — under-viaduct ruins; good future second ref if solved |

`tod_panel.is_bst` agrees with actual UK BST for all five dates.

## real_geograph (locked camera)

`Cam_Match_geograph` from `tests/scene_matched_geograph.blend`. The
camera sits inside unsourced neighbour / viaduct set-dressing
(`camera_match` blockers; `PLAN.md` / `TOOLS.md` `--hide-near`).
`hide_near(8)` segfaulted Cycles/Embree on this scene, so the hugging
geometry is clipped with `clip_start=4` (session never saved). Render
960×720 (photo aspect, not 16:9), 32 spp, denoised, clouds=0. Seven
hours: EXIF ±3 h so a peak can fall outside ±1 h. Wall time 121 s.

Official score is the **street band** (rows y/h ≥ 0.55, sky excluded):
the upper window grid is dark in both images and is not a sun shadow, so
it swamps full-frame edge angles (~61°) and flattens the IoU curve.
Full-frame numbers are kept as a diagnostic.

Street-band IoU vs hour (percentile 35 luminance mask):

| offset | hour | el ° | IoU | edge-angle diff ° |
|--------|------|------|-----|-------------------|
| −3 | 9.57 | 39.2 | 0.293 | 1.75 |
| −2 | 10.57 | 47.4 | 0.321 | 0.97 |
| −1 | 11.57 | 54.3 | 0.339 | 0.48 |
| **0 (EXIF)** | **12.57** | **58.7** | **0.344** | **0.74** |
| +1 | 13.57 | 59.3 | 0.336 | 0.39 |
| +2 | 14.57 | 55.9 | 0.314 | 3.30 |
| +3 | 15.57 | 49.6 | 0.304 | 1.84 |

IoU **peaks at the EXIF hour**. Angle at EXIF is 0.74° (≤10°), so this
ref **passes**. Angle stays ≤3.3° at every hour because kerb / pavement
lines dominate the street-band edges; the discriminative test here is
the IoU peak, not the angle. Absolute IoU is modest (0.34) because the
model has no construction hoarding.

Images: `tests/suncheck/out/cmp_real_geograph_exif.jpg`,
`tests/suncheck/out/sweep_real_geograph.jpg`.

## Hooks and viewer patch

- `SUNCHECK=1 ./validate.sh` runs `python3 sun_check.py --verify` (reads
  `tests/suncheck/result.json` / `tests/suncheck/out/result.json`, checks
  official hashes, does not re-render).
- Optional `?date=YYYY-MM-DD` into `sunPos()` is in
  `tests/suncheck/web_date_param.patch` only. Interior owns `web/` and
  deploys; this was not merged.

Replay: `./tests/suncheck/run.sh`.
