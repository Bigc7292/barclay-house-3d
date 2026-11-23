"""Furniture fit check (lane/walls, 2026-11-20).

Reads interior/live/furniture_fit.json (world XY convex hull + z range of every placed piece, written by
interior/build_twobed_v4.py after furniture_cc0.place_trace) and tests each piece against the plan trace
(interior/trace/twobed_layout.py) on a 5 mm raster:
  * outside_floor_cm2   hull area outside the internal-face floor outline
  * wall_cm2            hull area inside any wall/partition solid (walls_bl minus door/opening gaps)
  * joinery_cm2         hull area inside traced built-in joinery (wardrobes; kitchen/TV footprints are the
                        CC0 units' own footprints, so kitchen/TV items are exempt)
  * swing_cm2           hull area inside a door leaf swing sector (hinge, radius = leaf width, closed->open)
  * doorway_cm2         hull area inside a doorway clear zone = door gap / opening segment extended 0.375 m
                        each side (0.375 m = half the ADM 750 mm clear width already used by #21)
  * room_frac           share of the hull inside the room the piece was placed in; other rooms touched
                        are listed (room lines in the open-plan living/kitchen are not walls)
Flat walk-over items (z max < 0.05 m: rug, shower tray) are exempt from the swing/doorway tests only.
Contact tolerance: each hull mask is eroded by 2 px (10 mm) before testing, so touching a wall is allowed.
PASS = no wall, outside, joinery, swing or doorway area for any piece.
"""
import json, math, sys
from pathlib import Path
import numpy as np, cv2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "interior/trace"))
import twobed_layout as LY

RES = 0.005
dump = json.loads((ROOT / "interior/live/furniture_fit.json").read_text())
floor = [LY.bl(*p) for p in LY.TRACE["outline"]]
xs = [p[0] for p in floor]; ys = [p[1] for p in floor]
X0, Y0 = min(xs) - 0.6, min(ys) - 0.6
W = int((max(xs) + 0.6 - X0) / RES); H = int((max(ys) + 0.6 - Y0) / RES)

def px(p): return [int(round((p[0] - X0) / RES)), int(round((p[1] - Y0) / RES))]
def poly_mask(pts):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array([px(p) for p in pts], np.int32)], 1); return m.astype(bool)
def rect(a, b, t, ext=0.0):
    (ux, uy), L = LY._unit(a, b); nx, ny = -uy, ux
    a2 = (a[0] - ux * ext, a[1] - uy * ext); b2 = (b[0] + ux * 0, b[1] + uy * 0)
    return [(a[0] + nx * t / 2, a[1] + ny * t / 2), (b[0] + nx * t / 2, b[1] + ny * t / 2),
            (b[0] - nx * t / 2, b[1] - ny * t / 2), (a[0] - nx * t / 2, a[1] - ny * t / 2)]

FLOOR = poly_mask(floor)
WALL = np.zeros((H, W), bool)
gaps = []
for w in LY.walls_bl():
    (ux, uy), L = LY._unit(w["a"], w["b"])
    cuts = [0.0]
    for g0, g1 in sorted(w["gaps"]): cuts += [g0, g1]
    cuts.append(L)
    for s0, s1 in zip(cuts[0::2], cuts[1::2]):
        if s1 - s0 > 1e-3:
            WALL |= poly_mask(rect((w["a"][0] + ux * s0, w["a"][1] + uy * s0), (w["a"][0] + ux * s1, w["a"][1] + uy * s1), w["t"]))
    for g0, g1 in w["gaps"]:
        gaps.append((w["name"], (w["a"][0] + ux * g0, w["a"][1] + uy * g0), (w["a"][0] + ux * g1, w["a"][1] + uy * g1)))
DOORWAY = {}
for name, a, b in gaps:
    DOORWAY[name] = poly_mask(rect(a, b, 0.75))
SWING = {}
for d in LY.doors_bl():
    h = d["hinge"]; a0, a1 = sorted((d["closed"], d["open"]))
    pts = [h] + [(h[0] + d["w"] * math.cos(a0 + (a1 - a0) * i / 24), h[1] + d["w"] * math.sin(a0 + (a1 - a0) * i / 24)) for i in range(25)]
    SWING[d["name"]] = poly_mask(pts)
JOIN = np.zeros((H, W), bool)
for j in LY.joinery_bl():
    if j["name"].startswith(("Wardrobe",)):
        JOIN |= poly_mask(j["poly"])
ROOMS = {r["id"]: poly_mask([LY.bl(*q) for q in r["poly"]]) for r in LY.TRACE["rooms"]}
k3 = np.ones((5, 5), np.uint8)
rows, ok_all = [], True
for it in dump["items"]:
    m = cv2.erode(poly_mask(it["hull"]).astype(np.uint8), k3).astype(bool)
    a = m.sum() * RES * RES * 1e4
    low = it["z"][0] < 2.0
    flat = it["z"][1] < 0.05          # rug / shower tray: walk-over, cannot block a doorway or a swing
    r = {"name": it["name"], "kind": it["kind"], "cc0": it["cc0"], "room": it["room"], "area_cm2": round(a, 1),
         "outside_floor_cm2": round((m & ~FLOOR).sum() * RES * RES * 1e4, 1),
         "wall_cm2": round((m & WALL).sum() * RES * RES * 1e4, 1),
         "joinery_cm2": round((m & JOIN).sum() * RES * RES * 1e4, 1),
         "swing_cm2": {k: float(round((m & v).sum() * RES * RES * 1e4, 1)) for k, v in SWING.items() if low and not flat and (m & v).any()},
         "doorway_cm2": {k: float(round((m & v).sum() * RES * RES * 1e4, 1)) for k, v in DOORWAY.items() if low and not flat and (m & v).any()},
         "room_frac": round((m & ROOMS[it["room"]]).sum() / max(1, m.sum()), 3),
         "other_rooms": {k: float(round((m & v).sum() / max(1, m.sum()), 3)) for k, v in ROOMS.items() if k != it["room"] and (m & v).any()}}
    r["pass"] = bool(r["outside_floor_cm2"] == 0 and r["wall_cm2"] == 0 and r["joinery_cm2"] == 0 and not r["swing_cm2"] and not r["doorway_cm2"])
    ok_all = ok_all and r["pass"]; rows.append(r)
res = {"verdict": "PASS" if ok_all else "FAIL", "n": len(rows), "raster_m": RES, "contact_tolerance_m": 0.01,
       "doorway_half_depth_m": 0.375, "items": rows}
(ROOT / "tests/furniture_fit/result.json").write_text(json.dumps(res, indent=1))
for r in rows:
    flag = "ok " if r["pass"] else "BAD"
    print(flag, f'{r["name"]:34s} {r["room"]:9s} frac={r["room_frac"]:.3f} wall={r["wall_cm2"]} out={r["outside_floor_cm2"]} join={r["joinery_cm2"]} swing={r["swing_cm2"]} door={r["doorway_cm2"]} other={r["other_rooms"]}')
print("VERDICT", res["verdict"])
