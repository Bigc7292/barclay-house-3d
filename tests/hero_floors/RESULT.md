# Floor_* / Door_* hero export (trick #5 / #16)

Official `out/barclay_hero.glb`, `out/barclay_scene.blend` and `web/hero3.glb` were not written.

## Delivered

- `out/barclay_hero_floors.glb` — 3,819,052 bytes (3.64 MB)
- Test copy: `tests/hero_floors/out/barclay_hero.glb`
- Mobile: `tests/hero_floors/out/mobile/barclay_hero_mobile.glb` — 1,760,288 bytes (1.68 MB)

## Node names

Full hero: Floor_00, Floor_01, Floor_02, Floor_03, Floor_04, Floor_05; Door_entrance_frame, Door_entrance_L_leaf, Door_entrance_R_leaf; Building. 0 stray `*.001`. check_parts 10/10.

Mobile keeps all Floor_* and Door_* names. The Building empty is pruned by make_mobile (expected).

## validate.sh (MESHHEALTH=1) — PASS

- hero 3.64 / 5 MB, 0 errors
- mobile hero 1.68 / 2 MB, 0 errors
- mobile surroundings 4.51 / 6 MB, 0 errors (surroundings was a copy of official, not re-exported)
- check_parts ok
- mesh_health status=PASS blockers=0 majors=1442 minors=3351 dup_unshared=22 seconds=12.62 blend_unchanged=True

## 4K still

`tests/hero_floors/out/render_street_4096x2304.png` — Cam_Street, 128 spp, official blend read-only (BDISP/BWEATHER2 off). Compare to `out/render_street_4096x2304.png`.

This official blend is pale faience with cream/off-white window frames and no BARCLAY HOUSE lettering geometry. The darker archive front, black glazing bars and raised lettering live in the live `web/hero3.glb`, which was not overwritten. The new Floor_* export matches the official stills, not the archive mesh.

Rendered in 1343.3 s (128 spp, official blend read-only, flags off). ref_check vs `out/render_street_4096x2304.png`: edge F1 **0.9987**, mean abs 0.145/255, 0.28% px >2 (denoise variance). Cream frames, pale faience and rusticated base match; no lettering was invented.
