# Plan-overlay report (trick #18)

- Plan: `/workspace/barclay/interior/twobed/apt02_fp.png` (268×351 px). Rightmove Apt 02, no printed dimensions.
- Sourced total area: 63.0 m² ([barclay-house.com/two-bedroom-apartment](https://barclay-house.com/two-bedroom-apartment/), [Rightmove 92163630](https://www.rightmove.co.uk/properties/92163630) 679 sq ft).
- Layout: {'source_script': 'interior/build_twobed_v4.py', 'plan': 'interior/twobed/apt02_fp.png', 'note': '2bed.json has no wall polylines (cameras + door hinges only). These vertices are copied from build_twobed_v4.py, already in apt02_fp.png pixel space, scaled in 3D so outline area = sourced 63 m².'}
- Wall-mask IoU (identity, raw ink): **0.1408** (intersection 1875 / union 13321 px).
- Wall-mask IoU buffered ±4 px (primary gate, absorbs stroke-width / inner-face vs centreline): **0.2999**.
- Layout-on-ink precision (layout px within 2 px of plan ink): **0.5733**.
- Wall-mask IoU after translation-only search ±8 px: **0.2773** at dx=-5, dy=2 (sensitivity only; no labelled corners on the plan).
- Area: No independent scale on the layout. metres_per_px = sqrt(63.0/72707.0 px²) = 0.029436. Area residual is 0% BY CONSTRUCTION because the 3D model was scaled to the sourced 63 m². This is not an independent area measurement.
- Area residual vs 63.0 m²: **+0.00%** (measured area 63.000 m²).
- Gate (IoU ≥ 0.85 and area ±3%): **FAIL** (IoU False, area True).
- Overlay (red = layout not in plan wall mask, blue = plan wall missed, black = overlap): `plan_overlay_2bed.png`.

Mask method: plan ink = luminance < 80 (measured on this PNG). Opening defaults to 0 because a 3×3 opening deleted 2–3 px interior partitions. Raw ink includes furniture linework, which lowers IoU (furniture is not in the wall layout). Primary gate uses 4 px dilation on both masks. No dimension labels were read because the source image has none.
