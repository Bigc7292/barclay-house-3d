# Checklist gate — street
Render: `tests/match_geograph_p3_oriel3.png`
Ref: `refs/critic1/real_geograph.jpg`
Gate: FAIL (no=2, partial=1; need no 'no' and ≤2 'partial')

| element | status | metric | critic note |
|---|---|---|---|
| ground_floor_ashlar | **no** | hf 5.76/3.46=1.67 | R4/interior: stone must read as smooth banded Portland ashlar with channelled joints, not rubble/brick-like tiling |
| arcade | **no** | edge=1.19 hf_excess=1.69 | R4/interior HIGH: arcade too weak — need deep voussoirs, keystones, dark set-back glazing |
| glazing | **yes** | edge 0.2167/0.1876=1.16 | R4: white multi-pane sashes / fanlight bars must be legible vs flat single panes |
| rb_shields | **partial** | edge=1.61 hf_excess=1.58 | R4 MED: plain white discs read as satellite dishes; real = carved stone shield relief |
| parapet_colour | **yes** | salmon_frac=0.000 (ref=0.000) dark_brick=0.044/0.013 | Building parapet is stone (not brick). Flag washed salmon/orange under double-sun (pre-R4 failure mode) |

