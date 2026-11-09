# Checklist gate — street
Render: `out/render_street_4096x2304.png`
Ref: `refs/critic1/real_geograph.jpg`
Gate: FAIL (no=2, partial=1; need no 'no' and ≤2 'partial')
Hybrid ref_check edge_F1=0.429

| element | status | metric | critic note |
|---|---|---|---|
| ground_floor_ashlar | **no** | hf 8.55/3.50=2.44 | R4/interior: stone must read as smooth banded Portland ashlar with channelled joints, not rubble/brick-like tiling |
| arcade | **no** | edge=1.67 hf_excess=2.07 | R4/interior HIGH: arcade too weak — need deep voussoirs, keystones, dark set-back glazing |
| glazing | **yes** | edge 0.1686/0.1324=1.27 | R4: white multi-pane sashes / fanlight bars must be legible vs flat single panes |
| rb_shields | **partial** | edge=1.66 hf_excess=1.38 | R4 MED: plain white discs read as satellite dishes; real = carved stone shield relief |
| parapet_colour | **yes** | salmon_frac=0.000 (ref=0.000) dark_brick=0.323/0.015 | Building parapet is stone (not brick). Flag washed salmon/orange under double-sun (pre-R4 failure mode) |

