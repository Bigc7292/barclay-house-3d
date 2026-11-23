# Two Bed CC0 furniture — licence manifest

Lane: `lane/furniture`. Sources restricted to Poly Haven, Kenney, or ambientCG.
Every placed asset was checked CC0 on its own page (URLs below). Dimensions are metres (width × depth × height after front is normalised to −Y). Applied scale is `target / original` on those axes.

General licences:

- Poly Haven: all site assets are [CC0](https://polyhaven.com/license) (“Our assets are all licensed as CC0”).
- Kenney Furniture Kit 2.0 (2018-10-20): [CC0](https://creativecommons.org/publicdomain/zero/1.0/) on [kenney.nl/assets/furniture-kit](https://kenney.nl/assets/furniture-kit) and in `kenney_furniture_kit/License.txt`.

Shared palette (`furniture_cc0.PALETTE`, kit normaliser + `build_twobed_v4.py`): teal-navy velvet (matte), cream boucle, pale satin oak, handleless white (satin), satin black appliances, sanitary white (soft gloss), grey stone vanity, espresso chair frames, dark dining-table top. Roughness/albedo tuned to the Rightmove Apt 02 CGI (listing 92163630, `refs/critic1/92163630/`). Wood prototypes are remapped onto this oak; dining chairs use espresso frames, not pale oak.

Prototype sizes are checked against `furniture_dims.json` (see `interior/assets/scale_audit.json`). After `place_trace`, some pieces are then fitted to the plan footprint (sofa, beds, kitchen run, vanity, shelving) so positions stay trace-driven.

## Placed Poly Haven models

| Object name(s) | Asset | Licence page | Original W×D×H | Target W×D×H | Applied scale |
|---|---|---|---|---|---|
| `Sofa_navy_velvet_3seat` | [Sofa 02](https://polyhaven.com/a/sofa_02) | https://polyhaven.com/a/sofa_02 — CC0 | 1.807 × 0.818 × 0.710 | 2.00 × 0.92 × 0.80 | 1.107 × 1.125 × 1.128 |
| `Tub_chair_cream_boucle` ×4 | [Dining Chair 02](https://polyhaven.com/a/dining_chair_02) | https://polyhaven.com/a/dining_chair_02 — CC0 | 0.434 × 0.576 × 0.973 | 0.43 × 0.58 × 0.97 | 0.992 × 1.006 × 0.997 |
| `Dining_table_oak_top` | [Round Wooden Table 01](https://polyhaven.com/a/round_wooden_table_01) | https://polyhaven.com/a/round_wooden_table_01 — CC0 | 1.399 × 1.399 × 1.005 | 0.90 × 0.90 × 0.74 | 0.643 × 0.643 × 0.736 |
| `Coffee_table_oak_top` | [Modern Coffee Table 01](https://polyhaven.com/a/modern_coffee_table_01) | https://polyhaven.com/a/modern_coffee_table_01 — CC0 | 0.600 × 1.202 × 0.390 | 0.55 × 1.05 × 0.42 | 0.917 × 0.874 × 1.077 |
| `TV_bench_oak` | [Modern Wooden Cabinet](https://polyhaven.com/a/modern_wooden_cabinet) | https://polyhaven.com/a/modern_wooden_cabinet — CC0 | 2.440 × 0.520 × 0.680 | 1.50 × 0.40 × 0.50 | 0.615 × 0.769 × 0.735 |
| `Bedside_table_oak` ×4 | [Side Table 01](https://polyhaven.com/a/side_table_01) | https://polyhaven.com/a/side_table_01 — CC0 | 0.550 × 0.450 × 0.551 | 0.45 × 0.40 × 0.55 | 0.818 × 0.889 × 0.999 |
| `Wardrobe_oak_2door` ×2 | [Drawer Cabinet](https://polyhaven.com/a/drawer_cabinet) | https://polyhaven.com/a/drawer_cabinet — CC0 | 1.141 × 0.488 × 1.881 | 1.00 × 0.58 × 2.10 | 0.876 × 1.188 × 1.116 |
| `Storage_shelving_white` | [Wooden Display Shelves 01](https://polyhaven.com/a/wooden_display_shelves_01) | https://polyhaven.com/a/wooden_display_shelves_01 — CC0 | 1.078 × 0.372 × 1.556 (native) | room width × 0.40 × 2.20 | per-room (unique mesh) |
| `Induction_hob_black` | [Electric Stove](https://polyhaven.com/a/electric_stove) | https://polyhaven.com/a/electric_stove — CC0 | 0.503 × 0.648 × 0.859 | 0.60 × 0.60 × 0.90 | 1.194 × 0.927 × 1.048 |

Sofa / chair / stove materials are remapped onto the shared palette so they match the Rightmove CGI: navy velvet sofa, cream boucle chairs, **black** appliance faces (`kitchen_black_appliances`).

## Placed Kenney Furniture Kit models

Licence page for every row: https://kenney.nl/assets/furniture-kit (CC0) and `interior/assets/kenney_furniture_kit/License.txt`.

| Object name(s) | Asset file | Original W×D×H | Target W×D×H | Applied scale |
|---|---|---|---|---|
| `Bed1_navy`, `Bed2_navy` | `bedDouble.glb` | 0.956 × 1.125 × 0.375 | 1.45 × 2.05 × 0.60 | 1.517 × 1.822 × 1.600 |
| `Base_unit_*` | `kitchenCabinet.glb` / `kitchenCabinetDrawer.glb` | 0.430 × 0.450 × 0.450 | 0.60 × 0.58 × 0.78 | 1.395 × 1.289 × 1.733 |
| `Wall_unit_*` | `kitchenCabinetUpper.glb` / `kitchenCabinetUpperDouble.glb` | 0.430 × 0.220 × 0.390 | 0.60 × 0.33 × 0.72 | 1.395 × 1.500 × 1.846 |
| `Sink_steel` | `kitchenSink.glb` | 0.430 × 0.450 × 0.490 | 0.60 × 0.58 × 0.90 | 1.395 × 1.289 × 1.837 |
| `Washing_machine_black` | `washer.glb` | 0.390 × 0.390 × 0.470 | 0.60 × 0.58 × 0.85 | 1.538 × 1.487 × 1.809 |
| `Microwave_frame_black` | `kitchenMicrowave.glb` | 0.290 × 0.230 × 0.180 | 0.50 × 0.32 × 0.30 | 1.724 × 1.391 × 1.667 |
| `Tall_unit` | `kitchenFridge.glb` | (Kenney native) | 0.60 × 0.58 × 2.00 | scaled to target |
| `WC_pan_back` | `toilet.glb` | 0.313 × 0.477 × 0.451 | 0.40 × 0.65 × 0.42 | 1.280 × 1.362 × 0.931 |
| `Vanity_grey_stone_look` | `bathroomSinkSquare.glb` | 0.430 × 0.300 × 0.580 | 0.60 × 0.46 × 0.85 | 1.395 × 1.533 × 1.466 |
| *(not placed)* `shower.glb` | — | Kenney enclosure fills the 0.9 m tray and clips the existing bathroom camera | stand-in glass screen kept | — |
| `Mirror_black_frame` | `bathroomMirror.glb` | 0.301 × 0.144 × 0.435 | 0.55 × 0.04 × 0.75 | 1.825 × 0.277 × 1.726 |
| bedside lamps | `lampRoundTable.glb` | 0.152 × 0.176 × 0.314 | 0.18 × 0.18 × 0.32 | 1.184 × 1.025 × 1.018 |

Beds are remapped to **navy velvet + white linen** (`bedroom1_navy_bed`, `bedroom2_navy_bed`). WC / basin / shower sanitary surfaces are remapped to **sanitary white** (`bathroom_sanitary_white`). Washer and microwave are remapped to **black**.

No photoreal modern CC0 bed, kitchen run, or bathroom fittings exist on Poly Haven (only gothic / vintage beds and a white electric stove). Kenney fills those gaps, scaled to the stand-in footprints and tinted to the CGI palette.

## Stand-ins kept

| Item | Why |
|---|---|
| `Peninsula_dark`, `Peninsula_top_white_quartz`, `Oven_black_built_in` | No suitable modern CC0 peninsula / breakfast bar (Kenney `kitchenBar` is stylized and the wrong type). Kept as procedural stand-ins at the original position. |
| Worktop, plinth, LED strip, WC boxing / flush plate | Built-in architectural fittings, not standalone CC0 models. |
| Rug, TV screen / stand, wall art, plants, globe pendant, chrome towel ladder | Not in the required furniture/fittings swap, and no suitable matching CC0 model was used. |
| Shower enclosure (`Shower_tray` + glass screen + head) | Kenney `shower.glb` is a 0.9×0.9×2.1 m cubicle; the existing bathroom camera stands inside that tray, so the enclosure goes black in frame. The original glass-screen stand-in is kept. |
| Bathroom wall tiles | Architecture / finish, not furniture. Unchanged. |

## Unused asset already in the tree

`ClassicNightstand_01` (Poly Haven, CC0, https://polyhaven.com/a/ClassicNightstand_01) was already downloaded. It is **not placed**: tags are gothic / victorian, which is not suitable for this modern apartment. `side_table_01` is used instead.

## Build

- Module: `interior/furniture_cc0.py`, imported by `interior/build_twobed_v4.py` (object names unchanged so the lane merges with walls/polish).
- Dims: `interior/assets/furniture_dims.json`.
- Lineup (vertical + horizontal 1 m bars, labels, real-world metres): `interior/assets/kit_lineup.png` (overall) plus per-category `kit_lineup_{living,bedroom,kitchen,bath}.png`, rendered by `interior/kit_lineup.py` and annotated by `interior/kit_lineup_annotate.py`.
- Scale audit: `interior/assets/scale_audit.json` (prototype vs `furniture_dims.json`). Sink unit height is 0.90 m (tap included); storage shelving is scaled to 0.4 × 2.2 m; bedside lamp is listed.
- Dining chairs: four empties `Tub_chair_cream_boucle*`, front = local −Y; `build_twobed_v4.py` keeps the dot-product assert.
- Kitchen: the plan L-run has no drawn microwave; a CC0 black microwave is placed in the second south wall-unit bay (CGI kitchen_run) without moving neighbouring units.
