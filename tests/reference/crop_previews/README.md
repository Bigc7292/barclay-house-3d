# Official LY.CAMS crop previews (frozen)

Framing: `origin/lane/furniture` commit `f2cac162` `interior/live/v3_*.png`, rendered with `cam_bl(LY.CAMS[rid])` from `interior/trace/twobed_layout.py` (via `interior/build_twobed_v4.py`).

Boxes are the checklist `object_anchor.box` / `render_crop` values. These previews were checked visually before the freeze commit. Do not retune crops after that commit.

- `*_overlay.png` — all items for one official camera
- `crop_*.png` — isolated render crop for each item

## Freeze v2 reference crops (navy-bed items only)

Both Rightmove bedroom CGIs show navy upholstery *and* cream bedding. Freeze v2 re-anchors only the **reference** crops to the navy fabric. Render crops / `object_anchor.box` are unchanged. The 0.05 presence floor is unchanged.

- `bedroom1_navy_bed`: navy headboard fabric in `6830c23cc81166dfe894a94204f9eeeb.jpeg`
  URL `https://media.rightmove.co.uk/property-photo/6830c23cc/92163630/6830c23cc81166dfe894a94204f9eeeb.jpeg`
  box `[0.335, 0.598, 0.620, 0.626]`
- `bedroom2_navy_bed`: navy bed-base fabric in `09a28850469373714e2934f7bbf90dbb.jpeg`
  URL `https://media.rightmove.co.uk/property-photo/09a288504/92163630/09a28850469373714e2934f7bbf90dbb.jpeg`
  box `[0.42, 0.870, 0.72, 0.935]`

`ref_overlay_*.png` — red = v1 crop (mostly cream bedding), green = v2 navy-fabric crop.
`ref_crop_*.png` — isolated v2 reference crop (headboard crop also saved at 4×).
