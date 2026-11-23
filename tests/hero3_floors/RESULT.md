# Archive-look Floor_* hero (`out/barclay_hero3_floors.glb`)

`out/barclay_hero_floors.glb` has the official pale faience and cream frames.
The live look Colin wants is in `web/hero3.glb`: darker archive front, black
metal window frames, and BARCLAY HOUSE lettering on the door lintel.

This pass splits decoded `web/hero3.glb` by the storey / door world AABBs from
`out/barclay_hero_floors.glb` (same coordinate frame) and copies hero3
materials and textures losslessly (webp + clearcoat). Official Floor_* slabs
are not copied — they run through the window openings. Storey skin lives on
the Floor_* nodes so `make_mobile` keeps the names; entrance doors are
children of Floor_01.

Official `out/barclay_hero.glb`, `out/barclay_hero_floors.glb`,
`out/barclay_scene.blend` and `web/hero3.glb` were not written. No deploy.

## Delivered

- `out/barclay_hero3_floors.glb` — 3,114,300 bytes (2.97 MB)
- Test copy: `tests/hero3_floors/out/barclay_hero3_floors.glb`
- Mobile: `tests/hero3_floors/out/mobile/barclay_hero_mobile.glb` — 2,038,160 bytes (1.94 MB)

## Node names

Full hero: Floor_00, Floor_01, Floor_02, Floor_03, Floor_04, Floor_05;
Door_entrance_frame, Door_entrance_L_leaf, Door_entrance_R_leaf; Building.
0 stray `*.001`. check_parts 10/10.

Mobile keeps all Floor_* and Door_* names. The Building empty is pruned by
make_mobile (expected). Door tris: L 17, R 16, frame 236. 246 exact-zero-area
triangles in the Floor_01 band were dropped (they do not render). World bbox
matches `web/hero3.glb`.

## validate.sh (MESHHEALTH=1) — PASS

- hero 2.97 / 5 MB, 0 errors
- mobile hero 1.94 / 2 MB, 0 errors
- mobile surroundings 4.51 / 6 MB, 0 errors (surroundings was a copy of official, not re-exported)
- check_parts ok (10/10)
- mesh_health status=PASS blockers=0 majors=1442 minors=3351 dup_unshared=22 seconds=9.62 blend_unchanged=True

## three.js side-by-side vs live `web/hero3.glb`

Viewer cameras from `web/src/app.js` (street, facade, entrance) plus a lintel
close-up. Headless Chrome / swiftshader, same lights on both models.
`tests/hero3_floors/compare.mjs` + `compare_diff.py`.

| view     | mean abs | % px >2 | edge F1    |
|----------|----------|---------|------------|
| street   | 0.0144/255 | 0.149% | 0.999937 |
| facade   | 0.0239/255 | 0.303% | 0.999951 |
| entrance | 0.0010/255 | 0.005% | 1.000000 |
| lintel   | 0.0009/255 | 0.000% | 1.000000 |

Side-by-sides (hero3 left, new GLB right):

- `tests/hero3_floors/out/cmp_side_street.jpg`
- `tests/hero3_floors/out/cmp_side_facade.jpg`
- `tests/hero3_floors/out/cmp_side_entrance.jpg`
- `tests/hero3_floors/out/cmp_side_lintel.jpg`

Raw frames `cmp_{hero3,floors}_{cam}.png`, 8× diffs `cmp_diff_x8_*.png`,
ref_check sheets `cmp_refcheck_*.png`, numbers `compare_result.json`.

Both models show the darker archive front and black metal frames. Lettering
geometry is present (entrance and lintel F1 1.0 vs hero3). Shallow lintel
relief is easiest to read under the viewer's lighting; see also
`web/video/img/lintel.jpg`.

Replay: `./tests/hero3_floors/run.sh`.
