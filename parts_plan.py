#!/usr/bin/env python3
"""Named part hierarchy (trick #16).

Load parts_plan.json, name/parent existing hero objects, never change geometry.
Safe to call twice. Used by build_scene.py and tests/parthierarchy/test_parts.py.
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_PATH = os.path.join(HERE, "parts_plan.json")
DOT_SUFFIX = re.compile(r"^(.*)\.(\d{3})$")
WINDOW_NAMES = (
    "HERO_glass", "HERO_frame", "HERO_glazing_bar", "HERO_sill",
    "HERO_fan_bar", "HERO_fan_hub", "HERO_side_glass", "HERO_side_sill",
    "Window_",
)
FACADE_STONE = ("HERO_front_stone_base", "HERO_gf_pilaster", "HERO_rustication_groove", "HERO_cartouche", "HERO_cartouche_frame", "HERO_ashlar_joint", "HERO_entrance_sign", "HERO_entrance_lettering")
FACADE_UPPER = ("HERO_front_terracotta", "HERO_giant_pilaster", "HERO_pilaster_capital", "HERO_oriel_base", "HERO_oriel_cheek", "HERO_oriel_head", "HERO_oriel_transom", "HERO_pediment", "HERO_RB_shield", "HERO_RB_cartouche", "HERO_RB_monogram", "HERO_oriel_spandrel", "HERO_parapet_coping", "HERO_parapet_plinth")


def load_plan(path: str | None = None) -> dict:
    return json.load(open(path or PLAN_PATH))


def required_names(plan: dict | None = None) -> list[str]:
    plan = plan or load_plan()
    return list(plan["required_in_glb"])


def walk_names(node: dict, acc: list[str] | None = None) -> list[str]:
    acc = acc if acc is not None else []
    acc.append(node["name"])
    for ch in node.get("children") or []:
        walk_names(ch, acc)
    return acc


def _source_for(plan: dict, name: str) -> str:
    def find(n):
        if n["name"] == name:
            return n.get("source") or "stand-in"
        for ch in n.get("children") or []:
            got = find(ch)
            if got is not None:
                return got
        return None
    return find(plan["tree"]) or "stand-in"


def _ensure_empty(bpy, name: str, collection=None):
    o = bpy.data.objects.get(name)
    if o and o.type == "EMPTY":
        return o
    if o and o.type != "EMPTY":
        return o
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.3
    (collection or bpy.context.scene.collection).objects.link(o)
    return o


def _world_reparent(o, parent):
    mw = o.matrix_world.copy()
    o.parent = parent
    o.matrix_world = mw


def _mid_z(o):
    pts = [o.matrix_world @ v.co if hasattr(v, "co") else o.matrix_world @ __import__("mathutils").Vector(v)
          for v in (o.bound_box if o.type == "MESH" else ((0, 0, 0),))]
    if not pts:
        return o.matrix_world.translation.z
    return sum(p.z for p in pts) / len(pts)


def _floor_index_for_z(z: float, levels: list[tuple[int, float]]) -> int:
    """Assign a part to a floor by height.

    Floor_00 is the basement stand-in at/below street. Ground-floor doors and
    windows sit below the Floor_01 slab (DAS lobby) but belong to Floor_01.
    """
    by = dict(levels)
    if 0 in by and 1 in by:
        if z < 0.15:
            return 0
        chosen = 1
        for i, zi in sorted(levels):
            if i <= 1:
                continue
            if z >= zi - 0.05:
                chosen = i
        return chosen
    chosen = levels[0][0]
    for i, zi in levels:
        if z >= zi - 0.05:
            chosen = i
    return chosen


def _set_source(o, src: str):
    try:
        o["source"] = src
    except Exception:
        pass


def _unique_undot(bpy):
    """Rename foo.001 -> foo_001 so validate.sh can reject stray dotted suffixes."""
    # Two-pass: first move dotted names aside, then into _NNN form.
    pending = []
    for o in list(bpy.data.objects):
        m = DOT_SUFFIX.match(o.name)
        if m:
            pending.append((o, m.group(1), m.group(2)))
    for o, base, num in pending:
        o.name = f"_tmp_{base}_{num}"
    used = {o.name for o in bpy.data.objects}
    for o, base, num in pending:
        want = f"{base}_{num}"
        if want in used:
            k = 0
            while f"{want}_{k}" in used:
                k += 1
            want = f"{want}_{k}"
        o.name = want
        used.add(want)


def apply(bpy, plan: dict | None = None, collection=None) -> dict:
    """Name/parent existing objects from parts_plan.json. No geometry change."""
    plan = plan or load_plan()
    src = lambda n: _source_for(plan, n)
    sc = bpy.context.scene
    # Hero collection if present
    hero_coll = bpy.data.collections.get("Hero") or collection or sc.collection

    building = _ensure_empty(bpy, "Building", hero_coll)
    _set_source(building, src("Building"))
    if building.parent:
        _world_reparent(building, None)

    floors = {}
    for i in range(6):
        name = f"Floor_{i:02d}"
        o = bpy.data.objects.get(name)
        if o is None:
            # tolerate already-undotted unique names only if exact match missing
            continue
        floors[i] = o
        _world_reparent(o, building)
        _set_source(o, src(name))

    # levels from custom props or object z
    levels = []
    for i, o in sorted(floors.items()):
        z = o.get("level_m_above_street") if o.get("level_m_above_street") is not None else _mid_z(o)
        levels.append((i, float(z)))
    if not levels:
        levels = [(0, 0.0)]

    def floor_of(z):
        return _floor_index_for_z(z, levels)

    def parent_to_floor(o, i, name=None, source_name=None):
        if name and o.name != name:
            o.name = name
        fl = floors.get(i)
        if fl is not None and o != fl:
            _world_reparent(o, fl)
        if source_name:
            _set_source(o, src(source_name))

    # Doors (GF entrance, Floor_01)
    mapping = {
        "HERO_door_left": "Door_entrance_L_leaf",
        "HERO_door_right": "Door_entrance_R_leaf",
        "HERO_door_lintel": "Door_entrance_frame",
    }
    for old, new in mapping.items():
        o = bpy.data.objects.get(old)
        if o:
            parent_to_floor(o, 1, new, new)

    # doorcase pieces stay Door_* so export will not join them across doors
    k = 0
    for o in list(bpy.data.objects):
        base = o.name.split(".")[0]
        if base in ("HERO_doorcase", "HERO_doorcase_head"):
            parent_to_floor(o, 1, f"Door_entrance_frame_{k:02d}", "Door_entrance_frame")
            k += 1

    # Facades
    o = bpy.data.objects.get("HERO_front_stone_base")
    if o:
        parent_to_floor(o, 1, "Facade_01", "Facade_01")
    o = bpy.data.objects.get("HERO_front_terracotta")
    if o:
        # shared unsplit upper facade: parent to Floor_02, name Facade_upper
        parent_to_floor(o, 2 if 2 in floors else 1, "Facade_upper", "Facade_upper")

    n = 0
    for o in list(bpy.data.objects):
        base = o.name.split(".")[0]
        if base in FACADE_STONE and o.name not in ("Facade_01",):
            parent_to_floor(o, 1, None, "Facade_01")
            n += 1
        elif base in FACADE_UPPER and o.name not in ("Facade_upper",):
            parent_to_floor(o, 2 if 2 in floors else 1, None, "Facade_upper")

    # Cornice / parapet
    for o in list(bpy.data.objects):
        base = o.name.split(".")[0]
        if base in ("HERO_cornice", "HERO_cornice_drip"):
            i = floor_of(_mid_z(o))
            nm = "Cornice_01" if i <= 1 else "Cornice"
            # unique later
            if o.name.split(".")[0] in ("HERO_cornice",) and i >= 5:
                o.name = "Cornice"
            parent_to_floor(o, i, None, "Cornice" if i >= 5 else "Cornice_01")
        elif base == "HERO_parapet":
            parent_to_floor(o, 5 if 5 in floors else max(floors, default=1), "Parapet", "Parapet")

    # Windows: parent by height, unique Window_{floor}_{kind}_{n}
    counters = {}
    for o in list(bpy.data.objects):
        base = o.name.split(".")[0]
        if not any(base.startswith(p.rstrip("_")) or base == p for p in (
            "HERO_glass", "HERO_frame", "HERO_glazing_bar", "HERO_sill",
            "HERO_fan_bar", "HERO_fan_hub", "HERO_side_glass", "HERO_side_sill",
        )) and not base.startswith("Window_"):
            continue
        if base.startswith("Window_") and not DOT_SUFFIX.match(o.name):
            # already named; still reparent
            try:
                i = int(base.split("_")[1])
            except Exception:
                i = floor_of(_mid_z(o))
            parent_to_floor(o, i, None, f"Window_{i:02d}")
            continue
        i = floor_of(_mid_z(o))
        kind = {
            "HERO_glass": "glass", "HERO_side_glass": "glass",
            "HERO_frame": "frame", "HERO_glazing_bar": "bar",
            "HERO_sill": "sill", "HERO_side_sill": "sill",
            "HERO_fan_bar": "fan", "HERO_fan_hub": "hub",
        }.get(base, "win")
        counters.setdefault((i, kind), 0)
        c = counters[(i, kind)]
        counters[(i, kind)] += 1
        parent_to_floor(o, i, f"Window_{i:02d}_{kind}_{c:03d}", f"Window_{i:02d}")

    _unique_undot(bpy)

    present = {o.name for o in bpy.data.objects}
    missing = [n for n in required_names(plan) if n not in present]
    return {"missing": missing, "objects": len(present)}


def join_group(name: str, parent_name: str | None = None) -> str:
    """Group key used by export_glb.py / make_mobile.mjs: never join across Floor_* or Door_*."""
    n = name or ""
    if n.startswith("Floor_"):
        return f"protect:{n}"
    if n.startswith("Door_") and n.endswith("_leaf"):
        return f"protect:{n}"
    if n.startswith("Door_"):
        # frames of the same door may join with each other
        door = re.sub(r"_frame(_.*)?$", "_frame", n)
        if not door.startswith("Door_"):
            door = n
        return f"door:{door}"
    # floor rest: parse Floor_XX / Window_XX / Facade_XX from name or parent
    for s in (n, parent_name or ""):
        m = re.search(r"(?:Floor|Window|Facade|Cornice|Parapet)_?(0[0-5])", s)
        if m:
            return f"floor:{m.group(1)}"
        m = re.match(r"Floor_(\d{2})", s)
        if m:
            return f"floor:{m.group(1)}"
    return "floor:Building"


if __name__ == "__main__":
    p = load_plan()
    print("required:", ", ".join(required_names(p)))
    print("tree names:", ", ".join(walk_names(p["tree"])))
