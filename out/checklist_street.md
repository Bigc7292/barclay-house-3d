# Checklist gate — street
Render: `tests/r3_street.png`
Ref: `refs/critic1/real_geograph.jpg`
Gate: FAIL (no=4, partial=0; need no 'no' and ≤2 'partial')

| element | status | metric | critic note |
|---|---|---|---|
| ground_floor_ashlar | **no** | hf 8.46/3.50=2.42 | R4/interior: stone must read as smooth banded Portland ashlar with channelled joints, not rubble/brick-like tiling |
| arcade | **no** | edge=1.91 hf_excess=2.11 | R4/interior HIGH: arcade too weak — need deep voussoirs, keystones, dark set-back glazing |
| glazing | **yes** | edge 0.1767/0.1324=1.34 | R4: white multi-pane sashes / fanlight bars must be legible vs flat single panes |
| rb_shields | **no** | edge=2.30 hf_excess=1.89 | R4 MED: plain white discs read as satellite dishes; real = carved stone shield relief |
| parapet_colour | **no** | salmon_frac=0.446 (ref=0.000) dark_brick=0.017/0.015 | Building parapet is stone (not brick). Flag washed salmon/orange under double-sun (pre-R4 failure mode) |

