#!/usr/bin/env python3
"""Two Bed (Rightmove 92163630, Apt 02) wall / door / window retrace -> interior/trace/twobed_trace.json

Single source for the walk-mode rebuild (build_twobed_v4.py), #18 plan_overlay and
#21 accessible_area. Every coordinate is MEASURED on interior/twobed/apt02_fp.png
(268x351 px) in plan-pixel index space (pixel centre = integer, x right, y down),
read from 6-8x zoomed gridded crops and the ink mask (luminance < 80) plus
OpenCV contour/Hough output (cv2.findContours on the 3x3-opened ink for the thick
walls, cv2.HoughLinesP on thin ink for 1-2 px partitions). Nothing was copied from
build_twobed_v4.py (v4 outline is off by up to 16 px, e.g. right wall x=262 vs ink 254-259).
tests/pascal/layout_pascal.json (rejected #20) was used ONLY as a cross-check of
the entrance (x 99-129) and bathroom door (y 268-298) ink breaks.

Scale: the plan prints no dimensions (interior/FINDINGS.md). The only sourced
dimension is the total area 63 m2 (679 sq ft; https://barclay-house.com/two-bedroom-apartment/,
https://www.rightmove.co.uk/properties/92163630). metres_per_px is therefore
sqrt(63 / area of the internal-face floor polygon), i.e. the area is 63 m2 by
construction (GIA convention: internal face of perimeter walls / glazing line).
No independent check of scale exists in the source.

NOT FOUND (no source; modelled values are labelled stand-in):
  partition thickness (plan draws 1 px lines), ceiling height (floor-to-floor 3.663 m
  sourced, clear height not), window sill/head heights and frame pattern, door leaf
  height, bedroom door leaves (plan draws openings with no leaf/swing), step riser
  heights / count at the entrance (3 tread lines drawn, level change not stated).
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = "interior/twobed/apt02_fp.png"
SRC_PLAN = "measured on apt02_fp.png (Rightmove 92163630)"


def shoelace(p):
    n = len(p)
    return abs(sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1] for i in range(n))) / 2


def W(name, a, b, t, kind="wall", gaps=(), src=SRC_PLAN, note=None):
    d = {"name": name, "kind": kind, "a": list(a), "b": list(b), "thickness_px": t,
         "gaps": [list(g) for g in gaps], "source": src}
    if note:
        d["note"] = note
    return d


def along(a, b, p):
    """distance along a->b of the projection of p (px)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L


# ---------------------------------------------------------------- exterior (thick ink 6-8 px)
# Centrelines = middle of the thick ink band; thickness = measured band width.
EXT = [
    W("Ext_W_lower", (13, 346.5), (13, 184.5), 7),                 # ink x 10-16, y 183-349
    W("Ext_W_jog", (13, 184.5), (23, 182.5), 6),                   # ink jog y 181-188, x 10-26
    W("Ext_W_rake", (23, 182.5), (4.5, 81), 6),                    # outer (1,78)-(20,177), inner (7,84)-(26,185)
    W("Ext_W_jog_top", (4.5, 81), (11, 80), 5),                    # step at y 76-84
    W("Ext_NW_pier", (11, 80), (9.5, 62), 7),                      # pier x 6-14, y 62-81
    W("Ext_mid_pier_W", (89, 48), (92.5, 64.5), 7),                # U pier: west leg x 86-95, y 47-67
    W("Ext_mid_pier_S", (92.5, 64.5), (106.5, 61.5), 6),           # bottom y 60-67
    W("Ext_mid_pier_E", (106.5, 61.5), (104.5, 44), 6),            # east leg x 102-110, y 44-63
    W("Ext_NE_pier", (218, 3), (223, 18), 6),                      # pier (215-222, 2-21)
    W("Ext_NE_pier_jog", (223, 18), (230.5, 15.5), 6),
    W("Ext_E_rake", (230.5, 15.5), (262.5, 101), 7),               # outer (233,13)-(266,102), inner (229,19)-(259,98)
    W("Ext_E_jog", (262.5, 101), (256.5, 105.5), 6),
    W("Ext_E", (256.5, 105.5), (256.5, 346.5), 6),                 # ink x 254-259
    W("Ext_S", (256.5, 346.5), (13, 346.5), 6,                     # ink y 344-349
      gaps=[(256.5 - 128.5, 256.5 - 98.5)],
      note="entrance opening = ink break x 99-128 (30 px)"),
]
# ---------------------------------------------------------------- windows (double glazing lines)
WIN = [
    # Each glazed span is drawn as two 1 px glass lines between the piers; the model
    # treats the span as one window (sill/head NOT FOUND -> stand-in heights).
    W("Win_bed1_outer", (14, 61), (84, 48), 2, kind="window", note="Hough (14,61)-(84,48)"),
    W("Win_bed1_inner", (15, 66), (83, 54), 2, kind="window", note="Hough (15,66)-(83,54)"),
    W("Win_bed2_outer", (107, 42), (213, 3.5), 2, kind="window", note="Hough (107,42)-(212,4) / (119,37)-(213,3)"),
    W("Win_bed2_inner", (109, 48), (214, 9), 2, kind="window", note="Hough (109,48)-(214,9)"),
]
WINDOWS = [
    {"name": "Window_bed1", "room": "i_bed1", "a_px": [12.5, 63.5], "b_px": [88, 50.5], "source": "glazed span between NW pier and mid pier (two glass lines)",
     "sill_m": "NOT FOUND", "head_m": "NOT FOUND"},
    {"name": "Window_bed2", "room": "i_bed2", "a_px": [106, 45], "b_px": [219, 5.5], "source": "glazed span between mid pier and NE pier (two glass lines)",
     "sill_m": "NOT FOUND", "head_m": "NOT FOUND"},
]
# ---------------------------------------------------------------- partitions (thin 1-2 px ink)
PB = ((80, 172), (151, 146))           # bedroom / living line, Hough (80,172)-(151,146)
PB2 = ((213, 124), (253.5, 109.5))     # same line east of the Bedroom 2 opening, Hough (213,124)-(252,110)
PART = [
    W("Part_bed_divider", (101, 65.6), (131.5, 153.5), 2, note="Hough (100,67)-(132,153), pier to wardrobe corner"),
    W("Part_bed1_living", PB[0], (131.5, 153.5), 2),
    W("Joinery_bed2_wardrobe_back", (131.5, 153.5), PB[1], 2, kind="wall",
      note="collinear with the bed1/living line; back of the Bedroom 2 wardrobe"),
    W("Part_bed2_living", PB2[0], PB2[1], 2),
    W("Part_store_N", (16.5, 226), (84, 226), 2),
    W("Part_store_E", (84, 226), (84, 264), 2, gaps=[(5, 31)], note="door opening y 231-257 (leaf drawn open, angled)"),
    W("Part_store_S", (16.5, 264), (84, 264), 2),
    W("Part_bath_E", (84, 264), (84, 343.5), 2, gaps=[(5, 34)], note="door opening y 269-298 (leaf + swing arc drawn)"),
    W("Part_lobby_N", (84, 301), (122, 301), 2),
    W("Part_stair_W", (122, 269), (122, 301), 2),
    W("Part_stair_E_kitchen", (161, 269), (161, 343.5), 2),
]
# ---------------------------------------------------------------- openings / doors
DOORS = [
    {"name": "Door_entrance", "wall": "Ext_S", "hinge_px": [98.5, 343.5], "w_px": 30, "swing": "in",
     "open_dir_px": [0, -1], "source": "ink break x 99-128; leaf drawn open at x 94-97 against the lobby west side, arc to (125,343)"},
    {"name": "Door_bath", "wall": "Part_bath_E", "hinge_px": [84, 269], "w_px": 29, "swing": "in",
     "open_dir_px": [-1, 0], "source": "opening y 269-298 on x=84; leaf drawn open along y=270 x 55-84; arc to (82,298)"},
    {"name": "Door_storage", "wall": "Part_store_E", "hinge_px": [84, 231], "w_px": 26, "swing": "out",
     "open_dir_px": [0.43, 0.9], "source": "opening y 231-257 on x=84; leaf drawn open (81,231)-(93,256), arc to (84,257)"},
]
OPENINGS = [
    {"name": "Open_bed1", "between": ["i_bed1", "i_living"], "a_px": [23.7, 179.6], "b_px": [80, 172],
     "source": "gap between west wall inner face and the start of the bed1/living line (80,172); no leaf or swing drawn",
     "leaf": "NOT FOUND (plan draws no door leaf)"},
    {"name": "Open_bed2", "between": ["i_bed2", "i_living"], "a_px": [151, 146], "b_px": [213, 124],
     "source": "gap between wardrobe end (151,146) and the bed2/living line start (213,124); no leaf or swing drawn",
     "leaf": "NOT FOUND (plan draws no door leaf)"},
]
def _arc(name, c, r, t0, t1, n=10, src=SRC_PLAN):
    out = []
    for i in range(n):
        a0 = math.radians(t0 + (t1 - t0) * i / n); a1 = math.radians(t0 + (t1 - t0) * (i + 1) / n)
        out.append(W(f"{name}_{i}", (c[0] + r * math.cos(a0), c[1] + r * math.sin(a0)),
                     (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)), 1, kind="door_swing", src=src))
    return out


def door_symbols():
    """Door symbols that are drawn in dark ink (lum < 80) on the plan, open position (overlay only).
    The entrance leaf (lum >= 121), entrance arc (5 dark px), bath leaf (lum >= 86) and bath arc are
    drawn in grey, so they are not part of the #18 ink mask and are not rasterised here; their
    geometry is still recorded in DOORS."""
    return [W("Leaf_storage", (81, 231), (93, 256), 2, kind="door_leaf", note="leaf drawn (81,231)-(93,256), lum 30")]


# ---------------------------------------------------------------- floor = internal faces
FLOOR = [
    (16.5, 343.5), (16.5, 186), (26.5, 185.5), (7.5, 84), (14.5, 81), (12.5, 66.5),
    (88.5, 54), (89.5, 61), (90.5, 68), (110.5, 63.5), (109, 48), (214, 9.5), (217.5, 9),
    (221.5, 21.5), (229, 19), (259, 98.5), (253.5, 103.5), (253.5, 343.5),
]
ROOMS = [
    {"id": "i_bed1", "label": "Bedroom 1", "poly": [(25.4, 179.6), (7.5, 84), (14.5, 81), (12.5, 66.5), (88.5, 54), (90.5, 68), (101, 65.6), (131.5, 153.5), (80, 172)]},
    {"id": "i_bed2", "label": "Bedroom 2", "poly": [(101, 65.6), (110.5, 63.5), (109, 48), (214, 9.5), (217.5, 9), (221.5, 21.5), (229, 19), (259, 98.5), (253.5, 103.5), (253.5, 109.5), (213, 124), (151, 146), (131.5, 153.5)]},
    {"id": "i_store", "label": "Storage", "poly": [(16.5, 226), (84, 226), (84, 264), (16.5, 264)]},
    {"id": "i_bath", "label": "Bathroom", "poly": [(16.5, 264), (84, 264), (84, 343.5), (16.5, 343.5)]},
    {"id": "i_hall", "label": "Hall", "poly": [(84, 301), (122, 301), (122, 269), (161, 269), (161, 343.5), (84, 343.5)]},
    {"id": "i_kitchen", "label": "Kitchen", "poly": [(161, 269), (253.5, 269), (253.5, 343.5), (161, 343.5)]},
    {"id": "i_living", "label": "Living", "poly": [(16.5, 186), (26.5, 185.5), (25.4, 179.6), (80, 172), (151, 146), (213, 124), (253.5, 109.5), (253.5, 269), (122, 269), (122, 301), (84, 301), (84, 226), (16.5, 226)]},
]
# fixed joinery / fit-out drawn on the plan (obstacles in walk mode; not walls)
JOINERY = [
    {"name": "Wardrobe_bed2", "room": "i_bed2", "poly": [(111, 96), (129, 89), (151, 146), (131.5, 153.5)], "source": "hanger box: top (111,96)-(129,89), side Hough (129,89)-(150,145), back on bed1/living line"},
    {"name": "Wardrobe_living_W", "room": "i_living", "poly": [(16.5, 206), (77, 206), (77, 226), (16.5, 226)], "source": "hanger boxes x 17-77, y 206-226"},
    {"name": "TV_unit", "room": "i_living", "poly": [(122, 158), (137, 158), (137, 198), (122, 198)], "source": "box x 122-137, y 158-198"},
    {"name": "Wardrobe_living_C", "room": "i_living", "poly": [(122, 209), (152, 209), (152, 229), (122, 229)], "source": "hanger box x 122-152, y 209-229"},
    {"name": "Kitchen_run_S", "room": "i_kitchen", "poly": [(161, 321), (253.5, 321), (253.5, 343.5), (161, 343.5)], "source": "worktop line y=321 x 161-233 + hob circles"},
    {"name": "Kitchen_run_E", "room": "i_kitchen", "poly": [(233, 277), (253.5, 277), (253.5, 321), (233, 321)], "source": "worktop x 233-251, y 277-321 + sink 237-250"},
    {"name": "Entrance_steps", "room": "i_hall", "poly": [(122, 278), (161, 278), (161, 295), (122, 295)], "source": "3 tread lines y 278/286/295 x 122-161, chevron; riser heights NOT FOUND", "walkable": True},
]


def joinery_lines():
    """Outline strokes of the fixed joinery drawn on the plan (overlay only, kind=joinery)."""
    out = []
    for j in JOINERY:
        P = j["poly"]
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            out.append(W(f"{j['name']}_{i}", a, b, 1, kind="joinery", src=j["source"]))
    for k, (a, b) in enumerate(JOINERY_EXTRA):
        out.append(W(f"Joinery_detail_{k}", a, b, 1, kind="joinery"))
    return out


# internal joinery strokes drawn on the plan (wardrobe splits, treads, TV insert, sink bowl)
JOINERY_EXTRA = [
    ((47, 206), (47, 226)),            # living wardrobe split
    ((122, 286), (161, 286)),          # middle tread
    ((122, 198), (122, 209)),          # spine between TV unit and centre wardrobe
    ((124, 168), (124, 196)), ((124, 196), (136, 196)),   # TV unit inner frame
    ((126, 164), (127, 193)),          # TV screen bar
    ((237, 301), (250, 301)), ((250, 301), (250, 315)), ((250, 315), (237, 315)), ((237, 315), (237, 301)),  # sink
]


# Loose furniture, sanitaryware and symbols drawn on the plan (boxes = 1 px around the
# connected ink components left after the wall/joinery trace, each classified by eye). NOT walls; used
# only for the #18 diagnostic "IoU vs plan ink with these regions blanked" (the gate itself
# stays on raw ink). Boxes are generous hand-drawn regions around each item on the PNG.
PLAN_FURNITURE = [
    {"name": "Bed1_bedsides", "poly": [(44, 103), (100, 82), (118, 141), (60, 150)]},
    {"name": "Hangers_bed2_wardrobe", "poly": [(121, 102), (138, 102), (138, 143), (121, 143)]},
    {"name": "Bed2_bedsides", "poly": [(170, 58), (207, 39), (249, 39), (249, 94), (186, 103)]},
    {"name": "Sofa", "poly": [(219, 151), (249, 151), (249, 204), (219, 204)]},
    {"name": "Rug_ellipse", "poly": [(181, 156), (207, 156), (207, 199), (181, 199)]},
    {"name": "Dining_table_chairs", "poly": [(201, 220), (252, 220), (252, 266), (201, 266)]},
    {"name": "Hangers_living_W", "poly": [(30, 210), (35, 210), (35, 216), (30, 216)]},
    {"name": "Hangers_living_W2", "poly": [(59, 210), (65, 210), (65, 218), (59, 218)]},
    {"name": "Hangers_living_C", "poly": [(134, 215), (140, 215), (140, 221), (134, 221)]},
    {"name": "Stair_arrow", "poly": [(136, 267), (147, 267), (147, 273), (136, 273)]},
    {"name": "Basin", "poly": [(18, 289), (25, 289), (25, 307), (18, 307)]},
    {"name": "WC", "poly": [(17, 270), (28, 270), (28, 288), (17, 288)]},
    {"name": "Shower_dashed_line", "poly": [(19, 312), (80, 312), (80, 314), (19, 314)]},
    {"name": "Label_bedroom1", "poly": [(28, 81), (50, 81), (50, 85), (28, 85)]},
    {"name": "Label_bedroom2", "poly": [(130, 64), (152, 64), (152, 68), (130, 68)]},
    {"name": "Label_kitchen", "poly": [(181, 291), (199, 291), (199, 295), (181, 295)]},
    {"name": "Hob_rings", "poly": [(189, 326), (200, 326), (200, 343), (189, 343)]},
]


def ink_fit(walls, iters=2):
    """Deterministic sub-pixel fit of the hand trace to the plan ink (#18 raster, lum < 80).
    Coordinate descent on each wall/window end point (+-0.5/1 px steps) and stroke width
    (+-1 px), accepting a move only if identity IoU rises. Hand values kept as a_hand/b_hand/t_hand.
    Total drift is reported per wall; nothing moves further than the steps allow (max 2 px/iter)."""
    import copy, sys
    sys.path.insert(0, str(ROOT / "interior"))
    from plan_overlay import load_plan_mask, raster_walls, iou
    _, _, pm = load_plan_mask(ROOT / PLAN)
    W = copy.deepcopy(walls)
    for w in W:
        w["a_hand"], w["b_hand"], w["t_hand"] = list(w["a"]), list(w["b"]), w["thickness_px"]
    score = lambda ws: iou(raster_walls(pm.shape, ws), pm)[0]
    best = score(W)
    idx = [i for i, w in enumerate(W) if w["kind"] in ("wall", "window")]
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1), (-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]
    for _ in range(iters):
        for i in idx:
            for key in ("a", "b", "t"):
                for d in (steps if key != "t" else [(-1,), (1,)]):
                    W2 = copy.deepcopy(W)
                    if key == "t":
                        W2[i]["thickness_px"] = max(1, W2[i]["thickness_px"] + d[0])
                    else:
                        W2[i][key] = [W2[i][key][0] + d[0], W2[i][key][1] + d[1]]
                    v = score(W2)
                    if v > best + 1e-4:
                        best, W = v, W2
    for w in W:
        w["fit_drift_px"] = round(max(math.dist(w["a"], w["a_hand"]), math.dist(w["b"], w["b_hand"])), 2)
    return W


def build():
    area_px = shoelace(FLOOR)
    K = math.sqrt(63.0 / area_px)
    walls = ink_fit(EXT + WIN + PART) + door_symbols() + joinery_lines()
    return {
        "_provenance": {
            "plan": PLAN,
            "listing": "https://www.rightmove.co.uk/properties/92163630",
            "method": __doc__.strip().split("\n\n")[1],
            "scale": f"metres_per_px = sqrt(63 m2 / {area_px:.1f} px2) = {K:.6f} (area 63 m2 by construction; plan has no printed dimensions)",
            "area_source": ["https://barclay-house.com/two-bedroom-apartment/", "https://www.rightmove.co.uk/properties/92163630 (679 sq ft = 63.08 m2)"],
            "secondary_reference": "tests/pascal/layout_pascal.json (#20, rejected) used only to cross-check entrance and bath door ink breaks",
            "not_found": ["partition thickness", "clear ceiling height", "window sill/head heights", "door leaf height",
                          "bedroom door leaves", "entrance step riser heights"],
            "generator": "interior/trace/twobed_trace.py",
        },
        "units": "plan_px",
        "metres_per_px": K,
        "metres_per_px_source": "sqrt(63 m2 sourced total / internal-face floor polygon px2): 63 m2 BY CONSTRUCTION, not an independent measurement",
        "floor_px_area": area_px,
        "outline": [list(p) for p in FLOOR],
        "walls": walls,
        "doors": DOORS,
        "windows": WINDOWS,
        "openings": OPENINGS,
        "rooms": [{**r, "poly": [list(p) for p in r["poly"]], "area_m2": round(shoelace(r["poly"]) * K * K, 3)} for r in ROOMS],
        "joinery": [{**j, "poly": [list(p) for p in j["poly"]]} for j in JOINERY],
        "plan_furniture_px": [{**f, "poly": [list(p) for p in f["poly"]]} for f in PLAN_FURNITURE],
    }


if __name__ == "__main__":
    d = build()
    out = ROOT / "interior/trace/twobed_trace.json"
    out.write_text(json.dumps(d, indent=1) + "\n")
    print("wrote", out, "K", round(d["metres_per_px"], 6), "floor px2", d["floor_px_area"])
    tot = 0
    for r in d["rooms"]:
        tot += r["area_m2"]; print(f"  {r['id']:10s} {r['area_m2']:7.3f} m2")
    print("  rooms sum", round(tot, 3))
