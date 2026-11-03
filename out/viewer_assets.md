# Barclay House viewer assets
## Files
| File | Size | Content |
|---|---|---|
| /workspace/barclay/out/barclay_hero.glb | 8.0 MB | Barclay House only, full detail, 2K JPEG PBR textures embedded (482 meshes) |
| /workspace/barclay/out/barclay_surroundings.glb | 35.1 MB | Neighbours (EA LIDAR heights), viaduct, canal, roads, terrain, trees, lamp posts; 512 px textures (3,651 meshes) |
Plain glTF 2.0 binary, no Draco or meshopt, so any viewer can load it. Both re-import cleanly in Blender 4.2.

## Units, origin, axes
- Metres, real-world scale. glTF Y-up, right-handed: +X = grid east, +Y = up, -Z = grid north (British National Grid).
- Origin is the centre of the hero bounding box in plan at street level (Whitworth St W pavement, Y=0). In BNG that is E 383883.71, N 397522.20; Z=0 is 32.18 m ODN (EA DTM).
- Both files share the same origin, so load them both with an identity transform and they line up.

## Bounding boxes (glTF coords, m)
- Hero: min [-19.32, -0.5, -17.34] max [19.32, 23.93, 17.34] (roof 19.78 m; stair tower top 23.93 m; body base -0.5 m below grade)
- Surroundings: min [-853.54, -7.02, -530.0] max [850.43, 90.8, 492.24] (long OSM road and rail ways run past the 820 m LIDAR tile)

## Cameras (glTF coords)
| Camera | Position | Forward | Lens |
|---|---|---|---|
| Cam_Street | [-1.41, 1.7, 29.79] | [0.078, 0.0, -0.997] | 12.0 mm on 36.0 mm sensor (shift_y 0.17) |
| Cam_Aerial | [24.83, 120.0, 127.14] | [-0.147, -0.674, -0.724] | 40.0 mm on 36.0 mm sensor (shift_y 0.0) |
| Cam_Viaduct | [-51.07, 10.31, 38.93] | [0.904, -0.006, -0.428] | 24.0 mm on 36.0 mm sensor (shift_y 0.0) |

## Materials and sources
| Material (glTF name) | Used on | Source / quote | Status |
|---|---|---|---|
| Portland_stone | Front, street to 1st floor | "Portland stone up to first floor" https://www.manchestervictorianarchitects.org.uk/buildings/barclays-warehouse-barclay-house-whitworth-street-west | CONFIRMED |
| Burmantofts_white_glazed_faience | Front above 1st floor, cornices, parapet | "Burmantoft vitreous terra cotta above" (same URL); "smooth white faiance finish of Barclay House" (Heritage Statement https://docs.planning.org.uk/20210803/27/QKTOMYBCKT600/kr3moadl8zok1e27.pdf) | CONFIRMED white; exact shade NOT FOUND |
| Concrete_block | Sides and rear | "The remainder of the building cased in concrete blocks." (MVA) | CONFIRMED |
| Aluminium_frame_dark | Window frames | "replacement aluminium framed windows to all elevations" (WSP Planning Statement) | aluminium CONFIRMED; colour placeholder |
| Glass, Roof | Glazing, flat roof | none | placeholder |
| Viaduct_red_brick | Viaduct | "Red brick with some small sections of blue brick, sandstone dressings" (Heritage Statement) | CONFIRMED |
| Neighbour, Asphalt, Paving, Ground, Ballast, Canal_water, Leaves, Bark, Lamp_* | Context | generic | placeholder |
Textures: Poly Haven CC0 (white_sandstone_blocks_02, concrete_block_wall, asphalt_02, concrete_pavers, gravel, medieval_red_brick, roof_slates_02), box-projected UVs, tiled in world metres.
Hero geometry sources: Howard & Seddon E05 Existing Front Elevation (storey heights 3.663/3.925/3.290/3.323/3.480 m), DAS (GF +2.10 m above street), OSM footprint way 100646649, EA LIDAR check (roof median 18.96 m, p95 20.01 m).
The time-of-day rig, night window glow and the neighbours' procedural window lights stay in barclay_scene.blend only. They are not in the glbs.

### Round 1 update (2026-11-03 03:32 Asia/Dubai)
- New default camera **Cam_Hero_34** (glTF coords, metres): pos [-5.32, 1.6, 28.28], dir [0.746, 0.0, -0.666], lens 16 mm, sensor 36 mm, shift_y 0.2. All cameras are listed in viewer_assets.json.
- Sizes: barclay_hero.glb 9.2 MB, barclay_surroundings.glb 37.0 MB.
- New export materials: Rustication_channel, Neighbour_red_brick / render_cream / grey_cladding / glass_curtain, Kerb, Road_marking (flat colours, stand-ins). Faience is exported with the faience texture fallback (the procedural blocks are Cycles-only).
