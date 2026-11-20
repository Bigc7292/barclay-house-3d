#!/usr/bin/env python3
"""Two Bed walk-mode layout in metres, derived ONLY from interior/trace/twobed_trace.json.

Shared by interior/build_twobed_v4.py (Blender, Z-up), interior/accessible_area.py (#21)
and the 2bed.json writer (web/floorplan3d). Pure Python (no bpy).

Frames
  plan px : x right, y down (apt02_fp.png pixel index space)
  blender : X = (x - CX) * K, Y = -(y - CY) * K, Z up          (v4 m())
  glTF    : X = (x - CX) * K, Z = (y - CY) * K, Y up           (web/twobed.glb, 2bed.json)
  K = trace metres_per_px = sqrt(63 m2 / internal-face floor px2)  (63 m2 by construction)

Sourced vs stand-in (every number below is one of these):
  PLAN   measured on apt02_fp.png via the trace (positions, opening widths, wall ink widths,
         joinery and furniture footprints as drawn).
  STAND-IN (NOT FOUND in any source): CEIL 3.0 m, partition thickness 0.10 m, door/opening
         head 2.1 m, window sill 0.5 m / head 2.75 m, joinery heights, furniture heights.
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACE = json.loads((ROOT / "interior/trace/twobed_trace.json").read_text())
K = TRACE["metres_per_px"]
CX, CY = 137.0, 190.0          # same origin as v4 so the overview camera framing is comparable
CEIL = 3.0                     # STAND-IN (floor-to-floor 3.663 m sourced, clear height NOT FOUND)
T_PART = 0.10                  # STAND-IN partition thickness (plan draws 1-2 px lines)
HEAD = 2.1                     # STAND-IN door / opening head
SILL, WIN_HEAD = 0.5, 2.75     # STAND-IN window sill / head (v4 values)
STANDIN = {"ceiling_m": CEIL, "partition_thickness_m": T_PART, "door_head_m": HEAD,
           "window_sill_m": SILL, "window_head_m": WIN_HEAD}


def bl(x, y):
    return ((x - CX) * K, -(y - CY) * K)


def gl(x, y):
    return ((x - CX) * K, (y - CY) * K)


def _by(name):
    return next(w for w in TRACE["walls"] if w["name"] == name)


def _unit(a, b):
    L = math.dist(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L), L


# ------------------------------------------------------------------ walls (metres, blender XY)
def walls_bl():
    """[{name, a, b (blender m), t (m), gaps [(s0,s1) m along a->b], kind, source}]"""
    out = []
    for w in TRACE["walls"]:
        if w["kind"] != "wall" or w["name"].startswith("Joinery_"):
            continue
        ext = w["name"].startswith("Ext_")
        t = w["thickness_px"] * K if ext else T_PART
        a, b = bl(*w["a"]), bl(*w["b"])
        # extend exterior segments by t/2 at each end so the polyline corners close
        if ext:
            (ux, uy), L = _unit(a, b)
            a = (a[0] - ux * t / 2, a[1] - uy * t / 2); b = (b[0] + ux * t / 2, b[1] + uy * t / 2)
            gaps = [(g[0] * K + t / 2, g[1] * K + t / 2) for g in w["gaps"]]
        else:
            gaps = [(g[0] * K, g[1] * K) for g in w["gaps"]]
        out.append({"name": w["name"], "a": a, "b": b, "t": t, "gaps": gaps, "ext": ext,
                    "source": "PLAN" + ("" if ext else "; thickness STAND-IN")})
    # bedroom/living lines continued across the bedroom openings so a lintel can sit over them
    for o, wname in ((TRACE["openings"][0], "Part_bed1_living_full"), (TRACE["openings"][1], "Part_bed2_living_full")):
        a, b = bl(*o["a_px"]), bl(*o["b_px"])
        L = math.dist(a, b)
        out.append({"name": wname + "_lintel_only", "a": a, "b": b, "t": T_PART, "gaps": [(0.0, L)], "ext": False,
                    "opening": o["name"], "source": "PLAN opening " + o["name"] + " (no leaf drawn); head STAND-IN"})
    return out


def windows_bl():
    out = []
    for wd in TRACE["windows"]:
        a, b = bl(*wd["a_px"]), bl(*wd["b_px"])
        outer = _by(wd["name"].replace("Window_", "Win_") + "_outer")
        inner = _by(wd["name"].replace("Window_", "Win_") + "_inner")
        # depth = distance between the two glass lines (PLAN)
        mo = ((outer["a"][0] + outer["b"][0]) / 2, (outer["a"][1] + outer["b"][1]) / 2)
        mi = ((inner["a"][0] + inner["b"][0]) / 2, (inner["a"][1] + inner["b"][1]) / 2)
        out.append({"name": wd["name"], "room": wd["room"], "a": a, "b": b,
                    "depth": max(0.12, math.dist(mo, mi) * K), "sill": SILL, "head": WIN_HEAD,
                    "source": "PLAN span; sill/head STAND-IN (NOT FOUND)"})
    return out


# ------------------------------------------------------------------ doors (leaf + hinge)
# closed_deg / open_deg are Blender Z rotations of the leaf's local +X (hinge -> latch).
DOOR_ANG = {
    "Door_entrance": (0.0, 90.0),     # leaf closes along +x px; drawn open against the lobby west side (+90)
    "Door_bath": (-90.0, -180.0),     # closes along +y px (Blender -Y); drawn open along y=270 into the bathroom
    "Door_storage": (-90.0, None),    # closes along +y px; drawn open towards (93,256) into the hall
}


def doors_bl():
    out = []
    for d in TRACE["doors"]:
        h = bl(*d["hinge_px"])
        w = d["w_px"] * K
        c, o = DOOR_ANG[d["name"]]
        if o is None:  # storage: angle of the drawn leaf (81,231)->(93,256)
            leaf = _by("Leaf_storage")
            dx, dy = leaf["b"][0] - leaf["a"][0], -(leaf["b"][1] - leaf["a"][1])
            o = math.degrees(math.atan2(dy, dx))
        out.append({"name": d["name"], "hinge": h, "w": w, "closed": math.radians(c), "open": math.radians(o),
                    "source": d["source"] + "; leaf height STAND-IN 2.08 m"})
    return out


# ------------------------------------------------------------------ joinery (fixed fit-out drawn on plan)
JOINERY_H = {"Wardrobe_bed2": 2.1, "Wardrobe_living_W": 2.1, "Wardrobe_living_C": 2.1, "TV_unit": 0.45,
             "Kitchen_run_S": 0.9, "Kitchen_run_E": 0.9, "Entrance_steps": 0.0}   # heights STAND-IN


def joinery_bl():
    out = []
    for j in TRACE["joinery"]:
        out.append({"name": j["name"], "room": j["room"], "poly": [bl(*p) for p in j["poly"]],
                    "h": JOINERY_H[j["name"]], "walkable": bool(j.get("walkable")), "source": "PLAN footprint; height STAND-IN"})
    return out


# ------------------------------------------------------------------ furniture placed where the plan draws it
def _line_hit(p, u, a, b):
    """param t where p + t*u meets line a-b (px)"""
    (ex, ey) = (b[0] - a[0], b[1] - a[1])
    den = u[0] * ey - u[1] * ex
    return ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den


def _bed_from_plan(foot_a, foot_b, head_a, head_b):
    """Bed footprint from the drawn foot edge and the wall/partition the headboard sits on."""
    fm = ((foot_a[0] + foot_b[0]) / 2, (foot_a[1] + foot_b[1]) / 2)
    (fx, fy), W = _unit(foot_a, foot_b)
    u = (fy, -fx)
    hm = ((head_a[0] + head_b[0]) / 2, (head_a[1] + head_b[1]) / 2)
    if (hm[0] - fm[0]) * u[0] + (hm[1] - fm[1]) * u[1] < 0:
        u = (-u[0], -u[1])
    L = _line_hit(fm, u, head_a, head_b) - 1.0     # stop 1 px (3 cm) off the partition face
    return fm, u, W * K, L * K


def furniture():
    """Blender-frame items: name, kind, room, c (x,y), s (sx,sy local), rot (Blender Z), extra."""
    F = []
    walls = {w["name"]: w for w in TRACE["walls"]}

    def add(name, kind, room, c_px, sx, sy, rot=0.0, **kw):
        F.append({"name": name, "kind": kind, "room": room, "c": bl(*c_px), "s": (sx, sy), "rot": rot, **kw})

    # beds: foot edges measured (Hough), heads on the divider / NE rake inner face
    beds = {
        "Bed1_navy": ("i_bed1", (47, 105.5), (63, 150), walls["Part_bed_divider"]["a"], walls["Part_bed_divider"]["b"]),
        "Bed2_navy": ("i_bed2", (177, 61), (192, 104), (229, 19), (259, 98.5)),
    }
    for name, (room, fa, fb, ha, hb) in beds.items():
        fm, u, W, L = _bed_from_plan(fa, fb, ha, hb)
        Lb = L - 0.12                               # bed() adds a 0.12 m headboard behind the base
        c = (fm[0] + u[0] * Lb / 2 / K, fm[1] + u[1] * Lb / 2 / K)
        ub = (u[0], -u[1])                          # head direction in blender
        rot = math.atan2(-ub[0], ub[1])             # local +Y -> head
        add(name, "bed", room, c, W, L, rot, W=W, Lb=Lb, foot_px=fm, head_dir_px=u)
        # bedsides either side of the head (sizes illustrative, as v4)
        hp = (fm[0] + u[0] * (L / K - 0.3 / K), fm[1] + u[1] * (L / K - 0.3 / K))
        perp = (-u[1], u[0])
        for k, sd in enumerate((-1, 1)):
            off = (W / 2 + 0.26) / K
            add(f"{name[:4]}_bedside_{k}", "bedside", room, (hp[0] + perp[0] * off * sd, hp[1] + perp[1] * off * sd), 0.45, 0.40, rot)
    # living: sofa (plan box x 220-249, y 151-204, back on the east side), coffee table at the drawn oval,
    # TV on the drawn media unit, rectangular dining table + 4 chairs as drawn
    add("Sofa_navy_velvet_3seat", "sofa", "i_living", (234.5, 177.5), 29 * K, 53 * K, 0.0)
    add("Coffee_table_oak_top", "table", "i_living", (194, 177.5), 0.55, 1.05, 0.0)
    add("Rug_cream", "rug", "i_living", (192, 177.5), 1.5, 2.0, 0.0, walkable=True)
    add("TV_on_media_unit", "tv", "i_living", (130, 178), 0.12, 1.12, 0.0)
    add("Dining_table_oak", "table", "i_living", (226.5, 244), 49 * K, 30 * K, 0.0)
    for k, (x, side) in enumerate(((214.5, -1), (239, -1), (214.5, 1), (239, 1))):
        y = 229 - 0.27 / K if side < 0 else 259 + 0.27 / K
        # chair opening faces the table: north chairs face +y px (blender -Y), south chairs face -y px
        add(f"Tub_chair_{k}", "chair", "i_living", (x, y), 0.56, 0.56, 0.0 if side < 0 else math.pi, r=0.28)
    add("Plant_pot", "plant", "i_living", (24, 196), 0.36, 0.36, 0.0, r=0.18)
    # kitchen (plan: L-shaped worktop; hob rings at x 189-200 on the south run; sink box 237-250 x 301-315)
    add("Hob", "kitchen_fixture", "i_kitchen", (194.5, 334), 0.52, 0.56, 0.0)
    add("Sink", "kitchen_fixture", "i_kitchen", (243.5, 308), 0.5, 0.42, 0.0)
    add("Washing_machine", "kitchen_fixture", "i_kitchen", (172, 333), 0.6, 0.6, 0.0)
    # bathroom (plan: WC x 17-28 y 270-288, basin x 17-43 y 289-306, shower zone south of dashed y=313)
    add("WC_pan", "sanitary", "i_bath", (16.5 + 0.33 / K, 279), 0.62, 0.40, 0.0)
    add("Vanity_basin", "sanitary", "i_bath", (16.5 + 0.23 / K, 297.5), 0.46, 0.55, 0.0)
    add("Shower_tray", "sanitary", "i_bath", ((16.5 + 84) / 2, (313 + 343.5) / 2), (84 - 16.5) * K - T_PART / 2, (343.5 - 313) * K, 0.0, walkable=True)
    # storage room shelving along its west wall (illustrative)
    add("Storage_shelving_white", "storage", "i_store", (16.5 + 0.2 / K, 245), 0.40, (264 - 226) * K - 0.25, 0.0)
    return F


# ------------------------------------------------------------------ rooms + cameras (glTF)
CAMS = {   # viewpoint / target in plan px (chosen inside each room, clear of drawn furniture)
    "i_living": ((150, 262), (232, 175), 1.5, 0.9, 70),
    "i_kitchen": ((185, 262), (240, 330), 1.5, 1.0, 70),
    "i_bed1": ((60, 166), (60, 85), 1.3, 0.8, 70),
    "i_bed2": ((180, 128), (205, 40), 1.3, 0.8, 70),
    "i_bath": ((76, 286), (30, 325), 1.55, 0.9, 80),
    "i_hall": ((110, 336), (145, 262), 1.5, 1.0, 70),
    "i_store": ((100, 245), (35, 245), 1.5, 1.0, 70),
}


def rooms_gl():
    out = []
    for r in TRACE["rooms"]:
        p, t, hp, ht, f = CAMS[r["id"]]
        pg, tg = gl(*p), gl(*t)
        out.append({"id": r["id"], "label": r["label"],
                    "cam": {"p": [round(pg[0], 2), hp, round(pg[1], 2)], "t": [round(tg[0], 2), ht, round(tg[1], 2)], "f": f},
                    "area_m2": r["area_m2"], "poly": [[round(v, 4) for v in gl(*q)] for q in r["poly"]]})
    return out


def doors_gl():
    return [{"name": d["name"], "hinge": [round(d["hinge"][0], 4), 0, round(-d["hinge"][1], 4)], "w": round(d["w"], 4),
             "closed_rot_y": round(d["closed"], 5), "open_rot_y": round(d["open"], 5), "source": d["source"]} for d in doors_bl()]


def floor_gl():
    return [list(gl(*p)) for p in TRACE["outline"]]


if __name__ == "__main__":
    print("K", K)
    for d in doors_gl():
        print(d)
    for f in furniture():
        print(f["name"], [round(v, 3) for v in f["c"]], [round(v, 3) for v in f["s"]], round(f["rot"], 3))
