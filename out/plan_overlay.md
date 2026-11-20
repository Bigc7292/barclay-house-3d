# Plan-overlay report (trick #18)

- Plan: `/workspace/barclay-lanes/walls/interior/twobed/apt02_fp.png` (268×351 px). Rightmove Apt 02, no printed dimensions.
- Sourced total area: 63.0 m² ([barclay-house.com/two-bedroom-apartment](https://barclay-house.com/two-bedroom-apartment/), [Rightmove 92163630](https://www.rightmove.co.uk/properties/92163630) 679 sq ft).
- Layout: {'plan': 'interior/twobed/apt02_fp.png', 'listing': 'https://www.rightmove.co.uk/properties/92163630', 'method': 'Single source for the walk-mode rebuild (build_twobed_v4.py), #18 plan_overlay and\n#21 accessible_area. Every coordinate is MEASURED on interior/twobed/apt02_fp.png\n(268x351 px) in plan-pixel index space (pixel centre = integer, x right, y down),\nread from 6-8x zoomed gridded crops and the ink mask (luminance < 80) plus\nOpenCV contour/Hough output (cv2.findContours on the 3x3-opened ink for the thick\nwalls, cv2.HoughLinesP on thin ink for 1-2 px partitions). Nothing was copied from\nbuild_twobed_v4.py (v4 outline is off by up to 16 px, e.g. right wall x=262 vs ink 254-259).\ntests/pascal/layout_pascal.json (rejected #20) was used ONLY as a cross-check of\nthe entrance (x 99-129) and bathroom door (y 268-298) ink breaks.', 'scale': 'metres_per_px = sqrt(63 m2 / 71278.9 px2) = 0.029730 (area 63 m2 by construction; plan has no printed dimensions)', 'area_source': ['https://barclay-house.com/two-bedroom-apartment/', 'https://www.rightmove.co.uk/properties/92163630 (679 sq ft = 63.08 m2)'], 'secondary_reference': 'tests/pascal/layout_pascal.json (#20, rejected) used only to cross-check entrance and bath door ink breaks', 'not_found': ['partition thickness', 'clear ceiling height', 'window sill/head heights', 'door leaf height', 'bedroom door leaves', 'entrance step riser heights'], 'generator': 'interior/trace/twobed_trace.py'}
- Wall-mask IoU (identity, raw ink): **0.7783** (intersection 7269 / union 9339 px).
- Wall-mask IoU buffered ±4 px (primary gate, absorbs stroke-width / inner-face vs centreline): **0.6562**.
- Layout-on-ink precision (layout px within 2 px of plan ink): **0.9977**.
- Wall-mask IoU after translation-only search ±8 px: **0.7783** at dx=0, dy=0 (sensitivity only; no labelled corners on the plan).
- Diagnostic `walls_windows_only` (not the gate): `{"iou_identity": 0.7239, "iou_buffered_4px": 0.5202}`
- Diagnostic `kinds_px` (not the gate): `{"door_leaf": 52, "joinery": 1163, "wall": 6914, "window": 417}`
- Diagnostic `excl_plan_furniture` (not the gate): `{"furniture_ink_px": 1102, "iou_identity": 0.832, "iou_buffered_4px": 0.8561, "note": "plan ink with loose furniture / sanitaryware / symbol boxes blanked (boxes listed in the layout); diagnostic only, NOT the gate"}`
- Area: Area uses layout['metres_per_px'] (sqrt(63 m2 sourced total / internal-face floor polygon px2): 63 m2 BY CONSTRUCTION, not an independent measurement). Outline 71278.9 px² × (0.029730 m/px)² = 63.000 m².
- Area residual vs 63.0 m²: **+0.00%** (measured area 63.000 m²).
- Gate (IoU ≥ 0.85 and area ±3%): **FAIL** (IoU False, area True).
- Overlay (red = layout not in plan wall mask, blue = plan wall missed, black = overlap): `plan_overlay.png`.

Mask method: plan ink = luminance < 80 (measured on this PNG). Opening defaults to 0 because a 3×3 opening deleted 2–3 px interior partitions. Raw ink includes furniture linework, which lowers IoU (furniture is not in the wall layout). Primary gate uses 4 px dilation on both masks. No dimension labels were read because the source image has none.
