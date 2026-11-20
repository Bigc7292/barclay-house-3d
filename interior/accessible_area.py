#!/usr/bin/env python3
"""Wheelchair accessible-area raster for the Two Bed walk-mode layout (bookmark trick #21).

2bed.json has no floor/wall polylines (documented by #18). The floor outline, partitions
and furniture footprints come from interior/build_twobed_v4.py — the same sourced
plan-px outline that was baked into web/twobed.glb — plus the entrance hinge and
room ids from web/floorplan3d/2bed.json. Plan is APPROXIMATE (#18 identity IoU 0.1408).

ADM Vol 1 (2015 edition with 2016 amendments), official PDF still linked from the
current GOV.UK Approved Document M page:
  https://www.gov.uk/government/publications/access-to-and-use-of-buildings-approved-document-m
  https://assets.publishing.service.gov.uk/media/5a7f8a82ed915d74e622b17b/BR_PDF_AD_M1_2015_with_2016_amendments_V3.pdf

ADM Vol 1 does not publish a wheelchair body width. Erosion uses the official
minimum clear width at a localised obstruction, 750 mm (M4(2) paragraph 2.22.b),
as the wheelchair *passage* width (radius 375 mm). M4(3) 3.24.a hall clear width
is 1050 mm and is cited but not used for erosion.

1500 mm turning circle (diameter) is official:
  M4(3) 3.14.d, 3.22.d, 3.43.e.

All area figures are indicative and computed, not a compliance certificate.
"""
from __future__ import annotations

import json, math, os, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELL = 0.05  # m
WHEELCHAIR_WIDTH = 0.75  # m; M4(2) 2.22.b — not a body width (see sources)
ERODE_R = WHEELCHAIR_WIDTH / 2.0
TURN_D = 1.50  # m; M4(3) 3.14.d / 3.22.d / 3.43.e
TURN_R = TURN_D / 2.0
SOURCED_AREA = 63.0
T_WALL = 0.12  # modelling wall thickness from v4 (not an ADM figure)

SOURCES = {
    "govuk": "https://www.gov.uk/government/publications/access-to-and-use-of-buildings-approved-document-m",
    "pdf": "https://assets.publishing.service.gov.uk/media/5a7f8a82ed915d74e622b17b/BR_PDF_AD_M1_2015_with_2016_amendments_V3.pdf",
    "pdf_edition": "Approved Document M Volume 1: Dwellings, 2015 edition with 2016 amendments",
    "wheelchair_width": {
        "mm": 750,
        "used_as": "passage width for raster erosion (ADM does not state a wheelchair body width)",
        "paragraph": "M4(2) 2.22.b",
        "quote": "the corridor is not reduced below a minimum 750mm width at any point",
    },
    "m4_3_hall_clear_width_mm": {"mm": 1050, "paragraph": "M4(3) 3.24.a", "not_used_for": "erosion"},
    "turning_circle_mm": {
        "diameter_mm": 1500,
        "paragraphs": ["M4(3) 3.14.d", "M4(3) 3.22.d", "M4(3) 3.43.e"],
        "quote_3_14_d": "A clear turning circle 1500mm in diameter is provided inside the entrance area, behind the entrance door when closed.",
        "quote_3_22_d": "There is a minimum 1500mm clear turning circle inside the entrance area, in front of the door when closed.",
        "quote_3_43_e": "The bathroom (or bathrooms) provides a minimum 1500mm clear turning circle.",
    },
    "floor_area": {
        "m2": 63,
        "urls": [
            "https://barclay-house.com/two-bedroom-apartment/",
            "https://www.rightmove.co.uk/properties/92163630",
        ],
        "note": "679 sq ft; outline scaled so shoelace area equals 63 m² (#18 residual 0% by construction)",
    },
    "plan_iou": {"identity": 0.1408, "gate": 0.85, "result": "FAIL", "trick": 18},
    "label": "indicative",
}


def _parea_px(P):
    return abs(sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))) / 2


def _shoelace(poly):
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2


def _pip(x, z, poly):
    c = False
    j = len(poly) - 1
    for i, (xi, zi) in enumerate(poly):
        xj, zj = poly[j]
        if ((zi > z) != (zj > z)) and (x < (xj - xi) * (z - zi) / (zj - zi) + xi):
            c = not c
        j = i
    return c


def _rot(px, pz, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (px * c - pz * s, px * s + pz * c)


def build_layout():
    """Floor, walls, rooms, furniture in glTF/walk-mode XZ metres (Y-up)."""
    P = [(12, 62), (92, 50), (98, 40), (228, 22), (262, 180), (262, 345), (18, 345), (18, 185)]
    K = math.sqrt(63.0 / _parea_px(P))
    CX, CY = 137, 190

    def xz(px, py):
        return ((px - CX) * K, (py - CY) * K)

    floor = [xz(*p) for p in P]
    assert abs(_shoelace(floor) - 63.0) < 1e-9

    def wall(p0, p1, gap_at=None, gw=0.85):
        a, b = xz(*p0), xz(*p1)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        gaps = []
        if gap_at is not None:
            s = L * gap_at
            gaps.append([s - gw / 2, s + gw / 2])
        return {"a": [round(a[0], 6), round(a[1], 6)], "b": [round(b[0], 6), round(b[1], 6)], "t": T_WALL, "gaps": gaps}

    walls = []
    # Exterior outline. Door gap only at the south-wall entrance from 2bed.json
    # (hinge m(100,345), w=0.9). v4 comments mention edge i==6 for a gap; the
    # baked door and 2bed.json place Door_entrance on the south edge (py=345).
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        rec = wall(a, b, gap_at=None)
        if a == (262, 345) and b == (18, 345):
            # along -X from (262,345); entrance at px=100, width 0.9 m
            L = math.hypot(rec["b"][0] - rec["a"][0], rec["b"][1] - rec["a"][1])
            # distance from start (262,345) to door start (100+0.9? hinge is left of leaf at rot 0)
            # hinge m(100,345), leaf extends +X in glTF? closed_rot_y=0.
            # In Blender door local +X is leaf; after glTF, need inward gap covering [hinge.x, hinge.x+0.9].
            # Segment goes from x=m(262) down to x=m(18). s along segment from a.
            ax, az = rec["a"]
            hx, hz = xz(100, 345)
            # hinge is the west end of the leaf if leaf extends +X: x in [hx, hx+0.9]
            # along this segment (direction -X), s = ax - x
            s0 = ax - (hx + 0.9)
            s1 = ax - hx
            rec["gaps"] = [[round(min(s0, s1), 6), round(max(s0, s1), 6)]]
        walls.append(rec)

    walls += [
        wall((105, 45), (120, 152)),
        wall((18, 185), (120, 152), gap_at=0.8),
        wall((120, 152), (215, 140), gap_at=0.2),
        wall((18, 200), (90, 200)),
        wall((90, 200), (90, 270), gap_at=0.5),
        wall((18, 270), (90, 270)),
        wall((86, 270), (86, 345), gap_at=0.6),
    ]

    def poly_px(pts):
        return [[round(x, 6), round(z, 6)] for x, z in (xz(*p) for p in pts)]

    rooms = [
        {"id": "i_bed1", "label": "Bedroom 1",
         "poly": poly_px([(18, 185), (120, 152), (105, 45), (92, 50), (12, 62)])},
        {"id": "i_bed2", "label": "Bedroom 2",
         "poly": poly_px([(120, 152), (215, 140), (262, 180), (228, 22), (105, 45)])},
        {"id": "i_store", "label": "Storage",
         "poly": poly_px([(18, 200), (90, 200), (90, 270), (18, 270)])},
        {"id": "i_bath", "label": "Bathroom",
         "poly": poly_px([(18, 270), (86, 270), (86, 345), (18, 345)])},
        {"id": "i_kitchen", "label": "Kitchen",
         "poly": poly_px([(156, 242), (260, 242), (260, 343), (156, 343)])},
        {"id": "i_hall", "label": "Hall",
         "poly": poly_px([(90, 200), (156, 200), (156, 345), (86, 345), (86, 270), (90, 270)])},
        {"id": "i_living", "label": "Living",
         "poly": poly_px([(90, 200), (156, 200), (156, 242), (260, 242), (262, 180), (215, 140), (120, 152), (90, 161.7059)])},
    ]

    def box(name, kind, room, cx, cz, sx, sz, rot=0.0, shape="rect"):
        return {
            "name": name, "kind": kind, "room": room, "shape": shape,
            "c": [round(cx, 6), round(cz, 6)],
            "s": [round(sx, 6), round(sz, 6)],
            "rot": round(rot, 6),
        }

    def circ(name, kind, room, cx, cz, r):
        return box(name, kind, room, cx, cz, r * 2, r * 2, 0.0, shape="circle")

    # --- furniture from v4, converted blender (x,y) -> gltf (x, -y) ---
    def b2(px, py=None):
        # blender y from plan or already metres
        if py is None:
            raise ValueError
        return (px, py)

    def from_bl(bx, by):
        return (bx, -by)

    def mbl(px, py):
        # blender XY as in v4 m()
        return ((px - CX) * K, -(py - CY) * K)

    furn = []
    # kitchen run
    kx = mbl(262, 0)[0] - T_WALL / 2
    ky0 = mbl(0, 343)[1]
    ky1 = mbl(0, 238)[1]
    L = ky1 - ky0
    n = int(L / 0.6)
    # worktop footprint (largest of run)
    wt_cx, wt_cz = from_bl(kx - 0.31, ky0 + n * 0.3)
    furn.append(box("Kitchen_run", "kitchen", "i_kitchen", wt_cx, wt_cz, 0.62, n * 0.6, 0))
    if n * 0.6 < L - 0.62:
        tx, tz = from_bl(kx - 0.3, ky0 + n * 0.6 + 0.3)
        furn.append(box("Tall_unit", "kitchen", "i_kitchen", tx, tz, 0.58, 0.597, 0))
    pz = mbl(0, 250)[1]
    px0 = kx - 0.6
    pnx, pnz = from_bl(px0 - 0.9, pz)
    furn.append(box("Peninsula_dark", "kitchen", "i_kitchen", pnx, pnz, 1.84, 0.64, 0))

    # living
    lc = mbl(205, 195)
    sofa_y = lc[1]
    sx = mbl(255, 0)[0] - 0.5
    sofax, sofaz = from_bl(sx + 0.02, sofa_y)
    furn.append(box("Sofa_navy_velvet_3seat", "sofa", "i_living", sofax, sofaz, 0.94, 2.36, 0))
    ct = (sx - 1.35, sofa_y)
    ctx, ctz = from_bl(*ct)
    furn.append(box("Coffee_table_oak_top", "table", "i_living", ctx, ctz, 0.55, 1.05, 0))
    tvx = mbl(150, 0)[0] + 0.25
    tvxx, tvz = from_bl(tvx, sofa_y)
    furn.append(box("TV_bench_oak", "furniture", "i_living", tvxx, tvz, 0.40, 1.50, 0))
    pp = (sx, sofa_y + 1.4)
    ppx, ppz = from_bl(*pp)
    furn.append(circ("Plant_pot", "plant", "i_living", ppx, ppz, 0.18))

    dc = (mbl(190, 0)[0], mbl(0, 305)[1])
    dcx, dcz = from_bl(*dc)
    furn.append(circ("Dining_table_oak_top", "table", "i_living", dcx, dcz, 0.45))
    for j, a in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2)):
        cbl = (dc[0] + 0.72 * math.cos(a), dc[1] + 0.72 * math.sin(a))
        cx, cz = from_bl(*cbl)
        # blender rot around Z by a-pi/2; gltf yaw = -blender Z rot (Y-up, Z = -Y)
        furn.append(circ(f"Tub_chair_{j}", "chair", "i_living", cx, cz, 0.29))

    # beds
    b1 = mbl(55, 105)
    b1c = (b1[0], mbl(0, 62)[1] - 1.15)
    bx, bz = from_bl(*b1c)
    furn.append(box("Bed1_navy", "bed", "i_bed1", bx, bz, 1.45, 2.05, 0))
    for dx in (-1.0, 1.0):
        p = from_bl(b1[0] + dx, mbl(0, 62)[1] - 0.35)
        furn.append(box(f"Bed1_bedside_{dx:+.0f}", "bedside", "i_bed1", p[0], p[1], 0.45, 0.40, 0))
    w1 = from_bl(mbl(28, 0)[0] + 0.3, mbl(0, 150)[1])
    # wardrobe local size 1.0 x 0.58, blender rot -pi/2 → gltf yaw +pi/2
    furn.append(box("Wardrobe_bed1", "wardrobe", "i_bed1", w1[0], w1[1], 1.0, 0.58, math.pi / 2))

    b2 = mbl(185, 70)
    b2c = (b2[0], mbl(0, 40)[1] - 1.3)
    bx, bz = from_bl(*b2c)
    # blender rot 0.06 → gltf yaw -0.06
    furn.append(box("Bed2_navy", "bed", "i_bed2", bx, bz, 1.45, 2.05, -0.06))
    for i, (dx, dyoff) in enumerate(((-1.0, -0.45), (1.0, -0.5))):
        p = from_bl(b2[0] + dx, mbl(0, 40)[1] + dyoff)
        furn.append(box(f"Bed2_bedside_{i}", "bedside", "i_bed2", p[0], p[1], 0.45, 0.40, -0.06))
    w2 = from_bl(mbl(140, 0)[0], mbl(0, 135)[1])
    furn.append(box("Wardrobe_bed2", "wardrobe", "i_bed2", w2[0], w2[1], 1.0, 0.58, -(math.pi - 0.12)))

    # bathroom
    bx0, by0 = mbl(19, 344)
    bx1, by1 = mbl(85, 271)
    sh = from_bl(bx0 + 0.5, by0 + 0.5)
    furn.append(box("Shower_tray", "sanitary", "i_bath", sh[0], sh[1], 0.95, 0.90, 0))
    bw = 0.2
    boxing = from_bl(bx0 + T_WALL / 2 + bw / 2, (by0 + 0.95 + by1) / 2)
    furn.append(box("WC_boxing_half_wall", "sanitary", "i_bath", boxing[0], boxing[1], bw, (by1 - by0) - 0.95, 0))
    wcy = by1 - 0.65
    wx0 = bx0 + T_WALL / 2 + bw
    # pan occupies ~0.5 x 0.4 from boxing into the room
    pan = from_bl(wx0 + 0.31, wcy)
    furn.append(box("WC_pan", "sanitary", "i_bath", pan[0], pan[1], 0.50, 0.40, 0))
    vx = bx1 - 0.45
    van = from_bl(vx, by1 - T_WALL / 2 - 0.24)
    furn.append(box("Vanity_grey_stone_look", "sanitary", "i_bath", van[0], van[1], 0.60, 0.46, 0))

    # storage
    s0, s1 = mbl(20, 268), mbl(88, 202)
    st = from_bl(s0[0] + 0.25, (s0[1] + s1[1]) / 2)
    furn.append(box("Storage_shelving_white", "storage", "i_store", st[0], st[1], 0.40, abs(s1[1] - s0[1]) - 0.2, 0))

    entrance = {
        "name": "Door_entrance",
        "hinge": [-1.0891, 4.5626],
        "w": 0.9,
        "source": "web/floorplan3d/2bed.json",
    }
    # just inside: mid of leaf, inward (smaller Z)
    entrance["seed"] = [round(-1.0891 + 0.45, 6), round(4.5626 - T_WALL / 2 - 0.20, 6)]

    return {
        "coord": "gltf XZ metres, Y-up, same frame as web/floorplan3d/2bed.json and web/twobed.glb",
        "floor_source": "interior/build_twobed_v4.py OUTL (2bed.json has no floor polyline; #18)",
        "furniture_source": "footprints from build_twobed_v4.py placements (web/twobed.glb furniture is baked into BAKED_interior; named boxes are not in the walk-mode GLB)",
        "cell_m": CELL,
        "wheelchair_width_m": WHEELCHAIR_WIDTH,
        "erode_radius_m": ERODE_R,
        "turning_circle_diameter_m": TURN_D,
        "sourced_floor_m2": SOURCED_AREA,
        "wall_thickness_m": T_WALL,
        "sources": SOURCES,
        "floor": [[round(x, 6), round(z, 6)] for x, z in floor],
        "walls": walls,
        "rooms": rooms,
        "furniture": furn,
        "entrance": entrance,
        "label": "indicative",
        "approximate_layout": True,
    }


# ---- raster -------------------------------------------------------------

def _wall_hit(x, z, walls):
    for w in walls:
        ax, az = w["a"]
        bx, bz = w["b"]
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        if L2 < 1e-18:
            continue
        t = ((x - ax) * dx + (z - az) * dz) / L2
        if t < 0.0 or t > 1.0:
            continue
        s = t * math.sqrt(L2)
        blocked = True
        for g0, g1 in w.get("gaps") or []:
            if g0 <= s <= g1:
                blocked = False
                break
        if not blocked:
            continue
        px, pz = ax + t * dx, az + t * dz
        if (x - px) ** 2 + (z - pz) ** 2 <= (w["t"] / 2) ** 2:
            return True
    return False


def _furn_hit(x, z, items, hidden):
    for it in items:
        if it["name"] in hidden:
            continue
        cx, cz = it["c"]
        lx, lz = _rot(x - cx, z - cz, -it.get("rot") or 0.0)
        if it.get("shape") == "circle":
            r = it["s"][0] / 2
            if lx * lx + lz * lz <= r * r:
                return True
        else:
            hx, hz = it["s"][0] / 2, it["s"][1] / 2
            if abs(lx) <= hx and abs(lz) <= hz:
                return True
    return False


def _disk(radius_m):
    r = int(math.ceil(radius_m / CELL))
    r2 = (radius_m / CELL) ** 2
    out = []
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            if di * di + dj * dj <= r2 + 1e-9:
                out.append((di, dj))
    return tuple(out)


_DISK_ERODE = _disk(ERODE_R)
_DISK_TURN = _disk(TURN_R)


def _grid_meta(layout):
    cached = layout.get("_grid")
    if cached:
        return cached
    import numpy as np
    floor = layout["floor"]
    xs = [p[0] for p in floor]
    zs = [p[1] for p in floor]
    pad = 0.80  # >= turning radius so out-of-floor counts as an obstacle
    xmin, xmax = min(xs) - pad, max(xs) + pad
    zmin, zmax = min(zs) - pad, max(zs) + pad
    origin_x = math.floor(xmin / CELL) * CELL
    origin_z = math.floor(zmin / CELL) * CELL
    w = int(math.ceil((xmax - origin_x) / CELL))
    h = int(math.ceil((zmax - origin_z) / CELL))
    in_floor = np.zeros((w, h), dtype=bool)
    wall = np.zeros((w, h), dtype=bool)
    room = np.full((w, h), -1, dtype=np.int16)
    ids = [r["id"] for r in layout["rooms"]]
    id_index = {rid: i for i, rid in enumerate(ids)}
    for i in range(w):
        x = origin_x + (i + 0.5) * CELL
        for j in range(h):
            z = origin_z + (j + 0.5) * CELL
            if not _pip(x, z, floor):
                continue
            in_floor[i, j] = True
            if _wall_hit(x, z, layout["walls"]):
                wall[i, j] = True
                continue
            rid = None
            for r in layout["rooms"]:
                if _pip(x, z, r["poly"]):
                    rid = r["id"]
                    break
            if rid is not None:
                room[i, j] = id_index[rid]
    # paint leftover in-floor cells from nearest assigned neighbour (shared edges)
    changed = True
    while changed:
        changed = False
        for i in range(w):
            for j in range(h):
                if not in_floor[i, j] or wall[i, j] or room[i, j] >= 0:
                    continue
                votes = {}
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < w and 0 <= jj < h and room[ii, jj] >= 0:
                        votes[room[ii, jj]] = votes.get(room[ii, jj], 0) + 1
                if votes:
                    room[i, j] = max(votes, key=votes.get)
                    changed = True
    meta = {
        "origin_x": origin_x, "origin_z": origin_z, "w": w, "h": h,
        "in_floor": in_floor, "wall": wall, "room": room, "ids": ids,
        "static_clear": in_floor & ~wall,
    }
    layout["_grid"] = meta
    return meta


def _dilate(obs, disk):
    """Boolean dilation of obs by a (di,dj) disk. out-of-array is already padded."""
    out = obs.copy()
    for di, dj in disk:
        if di == 0 and dj == 0:
            continue
        if di >= 0:
            si, ti = slice(di, None), slice(None, -di if di else None)
        else:
            si, ti = slice(None, di), slice(-di, None)
        if dj >= 0:
            sj, tj = slice(dj, None), slice(None, -dj if dj else None)
        else:
            sj, tj = slice(None, dj), slice(-dj, None)
        out[si, sj] |= obs[ti, tj]
    return out


def compute(layout, hidden=None):
    import numpy as np
    hidden = set(hidden or [])
    g = _grid_meta(layout)
    w, h = g["w"], g["h"]
    origin_x, origin_z = g["origin_x"], g["origin_z"]
    furn = np.zeros((w, h), dtype=bool)
    for it in layout["furniture"]:
        if it["name"] in hidden:
            continue
        cx, cz = it["c"]
        sx, sz = it["s"]
        rot = it.get("rot") or 0.0
        rad = 0.5 * math.hypot(sx, sz)
        i0 = max(0, int((cx - rad - origin_x) / CELL) - 1)
        i1 = min(w, int((cx + rad - origin_x) / CELL) + 2)
        j0 = max(0, int((cz - rad - origin_z) / CELL) - 1)
        j1 = min(h, int((cz + rad - origin_z) / CELL) + 2)
        is_circ = it.get("shape") == "circle"
        hx, hz = sx / 2, sz / 2
        for i in range(i0, i1):
            x = origin_x + (i + 0.5) * CELL
            for j in range(j0, j1):
                z = origin_z + (j + 0.5) * CELL
                lx, lz = _rot(x - cx, z - cz, -rot)
                if is_circ:
                    if lx * lx + lz * lz <= hx * hx:
                        furn[i, j] = True
                elif abs(lx) <= hx and abs(lz) <= hz:
                    furn[i, j] = True
    free = g["static_clear"] & ~furn
    # obstacle = not free (includes outside-floor and walls and furniture)
    obst = ~free
    nav = free & ~_dilate(obst, _DISK_ERODE)
    # flood from entrance seed
    sx, sz = layout["entrance"]["seed"]
    si = int((sx - origin_x) / CELL)
    sj = int((sz - origin_z) / CELL)
    if not (0 <= si < w and 0 <= sj < h and nav[si, sj]):
        found = False
        for r in range(0, 30):
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    ii, jj = si + di, sj + dj
                    if 0 <= ii < w and 0 <= jj < h and nav[ii, jj]:
                        si, sj = ii, jj
                        found = True
                        break
                if found:
                    break
            if found:
                break
    reach = np.zeros((w, h), dtype=bool)
    if 0 <= si < w and 0 <= sj < h and nav[si, sj]:
        stack = [(si, sj)]
        reach[si, sj] = True
        while stack:
            i, j = stack.pop()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, j + dj
                if 0 <= ii < w and 0 <= jj < h and nav[ii, jj] and not reach[ii, jj]:
                    reach[ii, jj] = True
                    stack.append((ii, jj))
    cell_a = CELL * CELL
    ids = g["ids"]
    per = {}
    for k, rid in enumerate(ids):
        mask = g["room"] == k
        clear_m2 = float(np.count_nonzero(free & mask) * cell_a)
        reach_m2 = float(np.count_nonzero(reach & mask) * cell_a)
        # turning circle: disk of radius 0.75 m entirely in this room's clear floor
        obst_r = ~(free & mask)
        dil_r = _dilate(obst_r, _DISK_TURN)
        ok = bool(np.any(mask & free & ~dil_r))
        per[rid] = {
            "reachable_m2": round(reach_m2, 4),
            "clear_m2": round(clear_m2, 4),
            "turning_circle": ok,
        }
    n_free = int(np.count_nonzero(free))
    n_nav = int(np.count_nonzero(nav))
    n_reach = int(np.count_nonzero(reach))
    grid = np.zeros((h, w), dtype=np.uint8)
    grid = np.where(g["in_floor"].T, np.where(reach.T, 2, 1), 0).astype(int)
    overlay = {
        "origin": [origin_x, origin_z],
        "cell": CELL,
        "w": w,
        "h": h,
        "grid": grid.tolist(),
    }
    return {
        "label": "indicative",
        "approximate_layout": True,
        "cell_m": CELL,
        "wheelchair_width_m": WHEELCHAIR_WIDTH,
        "erode_radius_m": ERODE_R,
        "turning_circle_diameter_m": TURN_D,
        "hidden": sorted(hidden),
        "clear_floor_m2": round(n_free * cell_a, 4),
        "navigable_m2": round(n_nav * cell_a, 4),
        "reachable_m2": round(n_reach * cell_a, 4),
        "sourced_floor_m2": SOURCED_AREA,
        "reachable_le_sourced": n_reach * cell_a <= SOURCED_AREA + 1e-9,
        "rooms": per,
        "seed_cell": [si, sj],
        "overlay": overlay,
        "sources": SOURCES,
    }


def main():
    layout = build_layout()
    out_layout = ROOT / "interior" / "accessible_layout.json"
    # strip private
    pub = {k: v for k, v in layout.items() if not k.startswith("_")}
    out_layout.write_text(json.dumps(pub, indent=2) + "\n")
    t0 = time.perf_counter()
    r = compute(layout, hidden=[])
    ms = (time.perf_counter() - t0) * 1000
    r["python_recompute_ms"] = round(ms, 3)
    t1 = time.perf_counter()
    r_bed1 = compute(layout, hidden=["Bed1_navy"])
    r["hide_Bed1_navy"] = {
        "reachable_m2": r_bed1["reachable_m2"],
        "room_i_bed1_m2": r_bed1["rooms"]["i_bed1"]["reachable_m2"],
        "base_room_i_bed1_m2": r["rooms"]["i_bed1"]["reachable_m2"],
        "room_area_rose": r_bed1["rooms"]["i_bed1"]["reachable_m2"] > r["rooms"]["i_bed1"]["reachable_m2"] + 1e-9,
        "ms": round((time.perf_counter() - t1) * 1000, 3),
    }
    t2 = time.perf_counter()
    r_bed2 = compute(layout, hidden=["Bed2_navy"])
    r["hide_Bed2_navy"] = {
        "reachable_m2": r_bed2["reachable_m2"],
        "room_i_bed2_m2": r_bed2["rooms"]["i_bed2"]["reachable_m2"],
        "base_room_i_bed2_m2": r["rooms"]["i_bed2"]["reachable_m2"],
        "room_area_rose": r_bed2["rooms"]["i_bed2"]["reachable_m2"] > r["rooms"]["i_bed2"]["reachable_m2"] + 1e-9,
        "ms": round((time.perf_counter() - t2) * 1000, 3),
    }
    # do not embed full overlay grid in the python summary written for tests (large);
    # keep a compact copy for the preview
    preview = r.pop("overlay")
    dest = ROOT / "tests" / "accessible" / "python_result.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(r, indent=2) + "\n")
    # small preview png
    try:
        from PIL import Image
        g = preview["grid"]
        w, h = preview["w"], preview["h"]
        im = Image.new("RGB", (w, h), (255, 255, 255))
        px = im.load()
        for j in range(h):
            for i in range(w):
                v = g[j][i]
                if v == 1:
                    px[i, j] = (200, 60, 60)
                elif v == 2:
                    px[i, j] = (40, 160, 80)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        scale = 4
        im = im.resize((w * scale, h * scale), Image.NEAREST)
        im.save(ROOT / "tests" / "accessible" / "preview_reachable.png")
    except Exception as e:
        print("preview skip", e)
    print(json.dumps({k: r[k] for k in r if k != "sources"}, indent=2))
    print("python_recompute_ms", r["python_recompute_ms"], "wrote", dest)


if __name__ == "__main__":
    main()
