# Mesh health (trick #19)

Blend: `out/barclay_scene.blend`
Script is read-only: the .blend was not saved.
Checklist idea: [arjun988/blender-skills](https://github.com/arjun988/blender-skills) (MIT). Own script, £0.

**Status: PASS** in 8.42s — Blockers 0, Majors 1442, Minors 3351.
Objects checked: 6619 (Hero 1471).
Duplicate-mesh groups (register #7): **22 unshared** (150 objects, 0 groups already share datablocks).

Severity: Blocker = flipped/inconsistent normals on visible Hero faces, non-manifold on Hero, or negative scale. Unapplied positive scale, Hero loose/dup/zero-area, Hero `*.001` names = Major. Unused slots, surroundings leftovers, unshared duplicate groups = Minor. Unapplied rotation is not flagged (objects are parented/placed).

## Blockers
- none

## Majors
- **dot001_name**: 1430 objects (e.g. `HERO_cartouche.001`, `HERO_cartouche_frame.001`, `HERO_cornice.001`, `HERO_cornice.002`, `HERO_cornice_drip.001`, `HERO_cornice_drip.002`, `HERO_doorcase.001`, `HERO_doorcase.002`…). These predate the #16 unique-name pass; the saved blend was not rebuilt.
- **duplicate_verts**: 6 objects (e.g. `HERO_fan_hub`, `HERO_fan_hub.001`, `HERO_fan_hub.002`, `HERO_fan_hub.003`, `HERO_fan_hub.004`, `HERO_fan_hub.005`).
- **zero_area_faces**: 6 objects (e.g. `HERO_fan_hub`, `HERO_fan_hub.001`, `HERO_fan_hub.002`, `HERO_fan_hub.003`, `HERO_fan_hub.004`, `HERO_fan_hub.005`).

## Minors (summary)
- **dot001_name**: 3329
- **duplicate_mesh_unshared**: 22

### Unshared duplicate-mesh groups (instancing candidates, #7)
- 106 copies / 106 datablocks: tree_crown.002, tree_crown.004, tree_crown.005, tree_crown.007, tree_crown.008, tree_crown.009 +86
- 3 copies / 3 datablocks: tree_crown.051, tree_crown.100, tree_crown.103
- 2 copies / 2 datablocks: tree_crown.083, tree_crown.094
- 2 copies / 2 datablocks: tree_crown.095, tree_crown.117
- 2 copies / 2 datablocks: viaduct_101853634_pier.040, viaduct_101853634_pier.056
- 2 copies / 2 datablocks: viaduct_101853634_pier.126, viaduct_101853634_pier.134
- 3 copies / 3 datablocks: viaduct_101855024_pier, viaduct_101855024_pier.018, viaduct_636894321_pier
- 2 copies / 2 datablocks: viaduct_101855024_pier.042, viaduct_101855024_pier.056
- 2 copies / 2 datablocks: viaduct_101855024_pier.106, viaduct_101855024_pier.110
- 2 copies / 2 datablocks: viaduct_101855024_pier.118, viaduct_101855024_pier.122
- 2 copies / 2 datablocks: viaduct_117741282_pier.024, viaduct_117741282_pier.030
- 2 copies / 2 datablocks: viaduct_31178960_pier.020, viaduct_31178960_pier.022
- 2 copies / 2 datablocks: viaduct_31179674_pier.020, viaduct_31179674_pier.024
- 2 copies / 2 datablocks: viaduct_31179674_pier.042, viaduct_31179674_pier.046
- 2 copies / 2 datablocks: viaduct_31231603_pier.002, viaduct_31231603_pier.008
- 2 copies / 2 datablocks: viaduct_31231603_pier.012, viaduct_31231603_pier.022
- 2 copies / 2 datablocks: viaduct_31231603_pier.044, viaduct_31231603_pier.048
- 2 copies / 2 datablocks: viaduct_31231611_pier.004, viaduct_31231611_pier.006
- 2 copies / 2 datablocks: viaduct_427155418_pier.006, viaduct_427155418_pier.012
- 2 copies / 2 datablocks: viaduct_427155418_pier.020, viaduct_427155418_pier.024
- 2 copies / 2 datablocks: viaduct_636894323_pier.018, viaduct_636894323_pier.032
- 2 copies / 2 datablocks: viaduct_636894324_pier.004, viaduct_636894324_pier.006

