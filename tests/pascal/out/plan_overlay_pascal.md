# Plan-overlay report (trick #18)

- Plan: `/workspace/barclay/interior/twobed/apt02_fp.png` (268×351 px). Rightmove Apt 02, no printed dimensions.
- Sourced total area: 63.0 m² ([barclay-house.com/two-bedroom-apartment](https://barclay-house.com/two-bedroom-apartment/), [Rightmove 92163630](https://www.rightmove.co.uk/properties/92163630) 679 sq ft).
- Layout: {'plan': 'interior/twobed/apt02_fp.png', 'method': 'Independent centreline trace. Exterior vertices are midpoints of measured thick ink (lum<80, typically 6-7 px) at corners and rakes. Interior partitions digitised from the same PNG (zoomed); hanging rails, furniture and the bathroom dashed shower line omitted. Door gaps are measured ink breaks where those exist (entrance x=99-129, bathroom y=268-298 at x=84); bedroom/storage door widths are the opening seen on the plan, recorded as along-segment gaps, not as sourced construction widths. Scale uses sourced 63 m² only.', 'not_from': 'build_twobed_v4.py / 2bed.json wall coordinates were not copied.', 'ceiling_height_m': '3.0 UNSOURCED (same modelling value as #14; floor-to-floor 3.663 m is sourced but clear height is not).'}
- Wall-mask IoU (identity, raw ink): **0.4691** (intersection 5488 / union 11698 px).
- Wall-mask IoU buffered ±4 px (primary gate, absorbs stroke-width / inner-face vs centreline): **0.4336**.
- Layout-on-ink precision (layout px within 2 px of plan ink): **0.9168**.
- Wall-mask IoU after translation-only search ±8 px: **0.4691** at dx=0, dy=0 (sensitivity only; no labelled corners on the plan).
- Area: No independent scale on the layout. metres_per_px = sqrt(63.0/74115.9 px²) = 0.029155. Area residual is 0% BY CONSTRUCTION because the 3D model was scaled to the sourced 63 m². This is not an independent area measurement.
- Area residual vs 63.0 m²: **+0.00%** (measured area 63.000 m²).
- Gate (IoU ≥ 0.85 and area ±3%): **FAIL** (IoU False, area True).
- Overlay (red = layout not in plan wall mask, blue = plan wall missed, black = overlap): `plan_overlay_pascal.png`.

Mask method: plan ink = luminance < 80 (measured on this PNG). Opening defaults to 0 because a 3×3 opening deleted 2–3 px interior partitions. Raw ink includes furniture linework, which lowers IoU (furniture is not in the wall layout). Primary gate uses 4 px dilation on both masks. No dimension labels were read because the source image has none.
