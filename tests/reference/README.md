# tests/reference — Two Bed checklist gate + walkthrough

Trick #15 reference-checklist gate for the Barclay House **Two Bed** interior, scored against the Rightmove Apt 02 CGI room photos (listing [92163630](https://www.rightmove.co.uk/properties/92163630)). Method: `x_tricks.md` #15 and `/home/box/x-bookmarks/implementations/barclay/2026-11-09-reference-checklist-gate.md`. numpy/Pillow only (via repo `checks.py`). No paid APIs.

## Score a renders folder

```bash
python tests/reference/score.py --renders <dir>
python tests/reference/score.py --renders interior/live --output tests/reference/result.json
```

`--renders` is required. `--output` is optional (default: `tests/reference/result.json`).

The script picks one image per room (`living`, `kitchen`, `bedroom1`, `bedroom2`, `bathroom`) from the folder. A `v3_living.png` wins over `v2_living.png` or `living.png`. Other lanes can drop their stills in a folder and re-score with the same command.

Each checklist item is **yes** / **partial** / **no**:

- ratio stats (edge density, dark-pixel share, mean value): **yes** ≥80% of the CGI reference, **partial** 60–80%, **no** <60%
- hue: **yes** if |Δhue| ≤ 30°, **partial** ≤ 60°, else **no**

Numeric `score` is the raw metric (ratio or |Δhue|). `score_norm` is 0–1. The overall `score` is the mean of `score_norm`. Colour-only rules (hue / mean value) are marked **no** (and contribute 0 to the mean) when the render crop luma std is below 0.05 — a flat or blown-out wall cannot pass by hue luck.

**Gate PASS** (trick #15): no `no` rows, and at most 2 `partial`.

CGI URLs and local copies are recorded in `checklist.json` and copied into `result.json`. Locals live at `refs/critic1/92163630/`.

## Walkthrough MP4

```bash
python tests/reference/make_walkthrough.py
python tests/reference/make_walkthrough.py --out tests/reference/walkthrough.mp4
```

Uses ffmpeg (libx264, yuv420p, `+faststart`, <25 MB) with slow pans and crossfades over the live interior stills. Near-blank frames (almost no edges or colours) are skipped: the current `v3_bedroom*.png` stills are washed-out walls, so the script falls back to `v2_bedroom1.png` / `closeup_bedroom2.png` in the same folder. `v3_bathroom.png` is kept (bright, but the fittings are visible).
