# Checklist gate — hero
Render: `out/render_hero_4096x2304.png`
Ref: `refs/critic1/real_commons.jpg`
Gate: PASS (no=0, partial=1; need no 'no' and ≤2 'partial')
Hybrid ref_check edge_F1=0.362

| element | status | metric | critic note |
|---|---|---|---|
| ground_floor_ashlar | **partial** | hf 5.52/3.84=1.44 | R4/interior: smooth banded Portland ashlar, not rubble-scale tiling |
| arcade | **yes** | edge=0.96 hf_excess=1.10 | R4/interior HIGH: deep radiating voussoirs + fanlight glazing |
| glazing | **yes** | edge 0.1308/0.1560=0.84 | R4: white multi-pane glazing bars vs flat glass |
| rb_shields | **yes** | edge=1.03 hf_excess=0.98 | R4 MED: carved RB monogram shields, not plain discs |
| parapet_colour | **yes** | salmon_frac=0.004 (ref=0.002) dark_brick=0.062/0.018 | Building parapet stone colour; fail washed salmon (pre-R4 sun_disc double light) |

