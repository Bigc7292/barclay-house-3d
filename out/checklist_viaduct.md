# Checklist gate — viaduct
Render: `out/render_viaduct_4096x2304.png`
Ref: `refs/surroundings/Oxford_Road_station_-_viaduct_to_Deansgate_-_geograph.org.uk_-_5724012.jpg`
Gate: FAIL (no=1, partial=0; need no 'no' and ≤2 'partial')
Hybrid ref_check edge_F1=0.367

| element | status | metric | critic note |
|---|---|---|---|
| parapet_colour | **no** | salmon_frac=0.395 (ref=0.032) dark_brick=0.228/0.154 | R4 OPEN: viaduct parapet sunlit faces still salmon/orange; need dark red-brown brick |
| viaduct_brick_body | **yes** | salmon_frac=0.009 (ref=0.010) dark_brick=0.342/0.170 | Side/structure brick must stay deep red, not washed |
| neighbour_roofs_dark | **yes** | dark 0.558/0.060=9.25 | R3/R4: neighbour roofs must read dark (membrane/slate), not pale under double sun |

