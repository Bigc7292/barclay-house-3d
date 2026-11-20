#!/usr/bin/env python3
"""Regenerate web/floorplan3d/2bed.json (rooms + fly-to cams, overview, door hinges) from the
2026-11-20 retrace (interior/trace/twobed_trace.json via twobed_layout.py). Also copies
interior/accessible_layout.json next to the page. Run after interior/accessible_area.py and
interior/plan_overlay.py (reads out/plan_overlay.json for the measured IoU)."""
import json, shutil
from pathlib import Path
import twobed_layout as LY

ROOT = LY.ROOT
ov = json.loads((ROOT / "out/plan_overlay.json").read_text())
dg = ov.get("diagnostics", {})
order = ["i_living", "i_kitchen", "i_bed1", "i_bed2", "i_bath", "i_hall", "i_store"]
rooms = {r["id"]: r for r in LY.rooms_gl()}
cx, cz = LY.gl(*[sum(p[i] for p in LY.TRACE["outline"]) / len(LY.TRACE["outline"]) for i in (0, 1)])
out = {
    "_provenance": {
        "model": "web/twobed.glb (built by interior/build_twobed_v4.py from interior/trace/twobed_trace.json, baked lightmap, meshopt). Mobile: web/twobed_m.glb.",
        "total_area": "63 m2 average two-bed, SOURCED https://barclay-house.com/two-bedroom-apartment/ (Rightmove Apt 02 679 sq ft https://www.rightmove.co.uk/properties/92163630)",
        "layout": ("Walls, doors, windows, rooms and joinery RETRACED 2026-11-20 from the Rightmove plan interior/twobed/apt02_fp.png "
                   "(no dimensions printed): interior/trace/twobed_trace.py -> twobed_trace.json. Scale = sqrt(63 m2 / internal-face floor px2), "
                   f"metres_per_px {LY.K:.6f}; total area 63 m2 BY CONSTRUCTION, not an independent measurement. "
                   f"#18 plan_overlay (raw ink incl. furniture, the gate): IoU identity {ov['iou_identity']}, buffered +-4 px {ov['iou_buffered_4px']} "
                   f"-> gate IoU>=0.85 {'PASS' if ov['gate']['iou_ge_0.85'] else 'FAIL'}; layout-on-ink precision {ov['layout_on_ink_precision_2px']}. "
                   f"Diagnostic with the plan's loose furniture blanked: identity {dg.get('excl_plan_furniture', {}).get('iou_identity')}, "
                   f"buffered {dg.get('excl_plan_furniture', {}).get('iou_buffered_4px')}. Pascal (#20, rejected) used only as a cross-check."),
        "room_areas_m2": {r: rooms[r]["area_m2"] for r in order},
        "room_areas_note": "per-room m2 = traced room polygons x the 63 m2-derived scale (not sourced per room)",
        "room_cams": "viewpoints chosen inside each traced room (interior/trace/twobed_layout.py CAMS)",
        "doors": "hinge, width and drawn open angle measured from the plan door symbols (entrance 30 px, bath 29 px, storage 26 px). Bedroom 1/2 have openings with no leaf drawn on the plan (leaf NOT FOUND), so no door leaf is modelled there. Leaf height 2.08 m STAND-IN.",
        "standins": LY.STANDIN,
        "not_from": "no sample data from wy51ai/floorplan-3d is used",
    },
    "rooms": [{"id": r, "label": rooms[r]["label"], "cam": rooms[r]["cam"]} for r in order],
    "overview": {"p": [round(cx + 0.6, 2), 12, round(cz + 11, 2)], "t": [round(cx, 2), 0, round(cz, 2)], "f": 45},
    "doors": [{k: v for k, v in d.items() if k != "source"} for d in LY.doors_gl()],
}
dst = ROOT / "web/floorplan3d/2bed.json"
dst.write_text(json.dumps(out, indent=1) + "\n")
shutil.copyfile(ROOT / "interior/accessible_layout.json", ROOT / "web/floorplan3d/accessible_layout.json")
print("wrote", dst, "and web/floorplan3d/accessible_layout.json")
