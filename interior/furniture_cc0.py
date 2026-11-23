"""CC0 furniture module for Barclay House Two Bed.

Imported by build_twobed_v4.py. Places licence-checked Poly Haven / Kenney
models at the existing stand-in positions, with dining-chair front = local -Y
so the v4 dot-product assert still holds.

Canonical kit pose (after normalize): origin at bottom-centre, front -Y, Z-up,
real-world metres. See interior/assets/furniture_dims.json and MANIFEST.md.
"""
from __future__ import annotations

import json
import math
import os

import bpy
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
ASSETS = os.path.join(HERE, "assets")
KENNEY = os.path.join(ASSETS, "kenney_furniture_kit")
DIMS_PATH = os.path.join(ASSETS, "furniture_dims.json")

_PROTO = {}  # name -> root empty (hidden prototypes)

# Shared furniture palette, tuned to Rightmove Apt 02 CGI (listing 92163630).
# Tuple is (sRGB albedo, roughness, metallic). Builder materials use the same
# names/finishes (and may attach a texture, tinted toward these albedos).
PALETTE = {
    "NAVY":   ((0.04, 0.08, 0.145), 0.85, 0.0),  # teal-navy velvet, matte (CGI sofa/beds)
    "BOUC":   ((0.88, 0.84, 0.76), 0.95, 0.0),   # cream boucle
    "OAKF":   ((0.76, 0.61, 0.41), 0.50, 0.0),   # pale satin oak (CGI coffee / bedside)
    "WUNIT":  ((0.90, 0.89, 0.86), 0.36, 0.0),   # handleless painted, satin
    "BLK":    ((0.004, 0.004, 0.005), 0.48, 0.0), # matte black appliance (holds under LED)
    "WHITEP": ((0.95, 0.94, 0.92), 0.18, 0.0),   # ceramic sanitary, soft gloss
    "GREYV":  ((0.38, 0.37, 0.36), 0.50, 0.0),   # grey stone vanity
    "LIN":    ((0.94, 0.93, 0.90), 0.88, 0.0),   # white linen
    "CHROME": ((0.90, 0.90, 0.90), 0.08, 1.0),
    "BMET":   ((0.025, 0.022, 0.02), 0.38, 0.85),
    "DARKW":  ((0.055, 0.042, 0.032), 0.42, 0.0), # espresso chair / table frame
    "DTOP":   ((0.07, 0.06, 0.055), 0.35, 0.0),  # dark dining-table top (CGI)
    "STEEL":  ((0.75, 0.75, 0.76), 0.28, 1.0),
    "GLASS":  ((0.95, 0.97, 0.97), 0.02, 0.0),
    "LAMPS":  ((1.0, 0.97, 0.92), 0.35, 0.0),
}


def palette_defaults(key):
    col, rough, met = PALETTE[key]
    return col, rough, met


def _dims():
    with open(DIMS_PATH) as f:
        return json.load(f)["items"]


def _ph(name):
    return os.path.join(ASSETS, name, f"{name}.gltf")


def _kn(name):
    return os.path.join(KENNEY, f"{name}.glb")


def _scene():
    return bpy.context.scene


def _link(o):
    sc = _scene()
    if o.name not in sc.collection.objects:
        sc.collection.objects.link(o)
    return o


def _bbox_world(objs):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    anyv = False
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            mins.x, mins.y, mins.z = min(mins.x, w.x), min(mins.y, w.y), min(mins.z, w.z)
            maxs.x, maxs.y, maxs.z = max(maxs.x, w.x), max(maxs.y, w.y), max(maxs.z, w.z)
            anyv = True
    if not anyv:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    return mins, maxs


def _ensure_mode_object():
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")


def _select(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    if active is not None:
        bpy.context.view_layer.objects.active = active
    elif objs:
        bpy.context.view_layer.objects.active = objs[0]


def _make_unique_meshes(objs):
    for o in objs:
        if o.type == "MESH" and o.data is not None and o.data.users > 1:
            o.data = o.data.copy()


def _apply_t(objs):
    _ensure_mode_object()
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        return
    _make_unique_meshes(meshes)
    _select(meshes)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def _import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    # drop leftover animation empties that have no mesh descendants if needed
    return new


def _remap_materials(objs, mapping, mats):
    """mapping: list of (needle_lower, mat_key). First match wins. mats is ctx materials."""
    cache = {}
    for o in objs:
        if o.type != "MESH":
            continue
        for i, slot in enumerate(list(o.data.materials)):
            if slot is None:
                continue
            key = slot.name.lower()
            dest = None
            for needle, mk in mapping:
                if needle in key and mk in mats:
                    dest = mats[mk]
                    break
            if dest is not None:
                o.data.materials[i] = dest
                cache[slot.name] = dest.name


def _rename_glass(objs, tag):
    for o in objs:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if m and "glass" in m.name.lower():
                if "_glass" not in o.name:
                    o.name = f"{tag}_glass"
                break


def _decimate(obj, target_tris):
    n = len(obj.data.polygons)
    if n <= target_tris or target_tris <= 0:
        return
    _select([obj], obj)
    mod = obj.modifiers.new("cc0_decimate", "DECIMATE")
    mod.ratio = max(0.02, target_tris / n)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _front_rotation(front):
    """Return Z rotation (radians) that turns `front` into -Y."""
    return {
        "-Y": 0.0,
        "+Y": math.pi,
        "+X": -math.pi / 2,
        "-X": math.pi / 2,
    }[front]


def normalize_group(objs, front="-Y", target=None, decimate_tris=None, name="proto"):
    """Bottom-centre origin, front -Y, optional target (w, d, h) in metres after front is -Y."""
    meshes = [o for o in objs if o.type == "MESH"]
    others = [o for o in objs if o not in meshes]
    if not meshes:
        raise RuntimeError(f"no meshes in {name}")
    _apply_t(meshes)
    # clear parents so locations are world
    for o in list(objs):
        if o.parent:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    _apply_t(meshes)

    mins, maxs = _bbox_world(meshes)
    cx = (mins.x + maxs.x) * 0.5
    cy = (mins.y + maxs.y) * 0.5
    cz = mins.z
    for o in meshes:
        for v in o.data.vertices:
            v.co.x -= cx
            v.co.y -= cy
            v.co.z -= cz
        o.location = (0, 0, 0)
        o.rotation_euler = (0, 0, 0)
        o.scale = (1, 1, 1)

    yaw = _front_rotation(front)
    if abs(yaw) > 1e-9:
        rot = Matrix.Rotation(yaw, 4, "Z")
        for o in meshes:
            o.data.transform(rot)
            o.data.update()

    if decimate_tris:
        # decimate after optional join of same-material? keep separate; budget per whole group
        total = sum(len(o.data.polygons) for o in meshes)
        if total > decimate_tris:
            for o in meshes:
                share = decimate_tris * (len(o.data.polygons) / total)
                _decimate(o, max(64, int(share)))

    if target is not None:
        w, d, h = target
        mins, maxs = _bbox_world(meshes)
        size = maxs - mins
        sx = (w / size.x) if (w and size.x > 1e-6) else 1.0
        sy = (d / size.y) if (d and size.y > 1e-6) else 1.0
        sz = (h / size.z) if (h and size.z > 1e-6) else 1.0
        sca = Matrix.Diagonal((sx, sy, sz, 1.0))
        for o in meshes:
            o.data.transform(sca)
            o.data.update()

    # tidy leftover non-mesh
    for o in others:
        bpy.data.objects.remove(o, do_unlink=True)

    root = bpy.data.objects.new(name, None)
    _link(root)
    for o in meshes:
        o.parent = root
        o.matrix_parent_inverse.identity()
    root["cc0_source"] = name
    mins2, maxs2 = _bbox_world(meshes)
    size2 = maxs2 - mins2
    root["cc0_final_dims"] = [round(size2.x, 4), round(size2.y, 4), round(size2.z, 4)]
    if target is not None:
        # Blender ID property arrays cannot contain None (e.g. free width on shelving).
        if all(v is not None for v in target):
            root["cc0_target_dims"] = [float(target[0]), float(target[1]), float(target[2])]
        if size.x and size.y and size.z:
            root["cc0_applied_scale"] = [round(sx, 4), round(sy, 4), round(sz, 4)]
            root["cc0_original_dims"] = [round(size.x, 4), round(size.y, 4), round(size.z, 4)]
    print(f"NORM {name} front={front} final={[round(size2.x,3),round(size2.y,3),round(size2.z,3)]} scale={root.get('cc0_applied_scale')}")
    return root



def load_prototype(key, path, front="-Y", target=None, decimate_tris=None,
                   mat_map=None, mats=None, glass_tag=None):
    if key in _PROTO:
        return _PROTO[key]
    objs = _import_gltf(path)
    if mat_map and mats:
        _remap_materials(objs, mat_map, mats)
    if glass_tag:
        _rename_glass(objs, glass_tag)
    root = normalize_group(objs, front=front, target=target, decimate_tris=decimate_tris, name=f"proto_{key}")
    root.hide_set(True)
    root.hide_render = True
    for ch in root.children:
        ch.hide_set(True)
        ch.hide_render = True
    _PROTO[key] = root
    return root


def instance(key, name, loc, rot_z=0.0, hide_proto=True):
    root = _PROTO[key]
    e = bpy.data.objects.new(name, None)
    _link(e)
    e.location = loc
    e.rotation_euler[2] = rot_z
    for ch in root.children:
        inst = ch.copy()
        inst.data = ch.data  # linked mesh
        inst.name = ch.name.replace("proto_", "")
        _link(inst)
        inst.parent = e
        inst.location = ch.location
        inst.rotation_euler = ch.rotation_euler[:]
        inst.scale = ch.scale.copy()
        inst.hide_set(False)
        inst.hide_render = False
    return e


# Material maps: first matching needle in the imported material name wins.
MAP_WOOD = [("glass", "GLASS"), ("metal", "BMET"), ("wood", "OAKF"), ("carpetwhite", "LIN"), ("carpet", "OAKF")]
MAP_SOFA = [("glass", "GLASS"), ("metal", "BMET"), ("wood", "BMET"), ("sofa", "NAVY")]
# CGI chairs: cream boucle on a dark espresso / black frame (not pale oak).
MAP_CHAIR = [("glass", "GLASS"), ("metal", "DARKW"), ("wood", "DARKW"), ("dining_chair", "BOUC")]
MAP_STOVE = [("glass", "GLASS"), ("electric_stove", "BLK"), ("stove", "BLK")]
MAP_MICRO = [("glass", "BLK"), ("metal", "BLK"), ("carpetwhite", "BLK"), ("_defaultmat", "BLK")]
MAP_KITCHEN = [("glass", "GLASS"), ("metallight", "CHROME"), ("metaldark", "BLK"),
               ("metalmedium", "STEEL"), ("metal", "CHROME"), ("wooddark", "WUNIT"),
               ("wood", "WUNIT"), ("carpetwhite", "WHITEP"), ("carpet", "WUNIT"),
               ("_defaultmat", "WUNIT")]
MAP_BED = [("glass", "GLASS"), ("metal", "BMET"), ("wood", "NAVY"),
           ("carpetwhite", "LIN"), ("carpet", "NAVY")]
MAP_BATH = [("glass", "GLASS"), ("metallight", "CHROME"), ("metaldark", "CHROME"),
            ("metal", "CHROME"), ("wood", "GREYV"), ("carpetwhite", "WHITEP"),
            ("carpet", "WHITEP"), ("_defaultmat", "WHITEP")]
MAP_WASHER = [("glass", "GLASS"), ("metal", "BLK"), ("_defaultmat", "BLK"),
              ("carpetwhite", "WHITEP"), ("wood", "BLK")]
MAP_LAMP = [("lamp", "LAMPS"), ("metal", "BMET")]


def _t(items, key):
    it = items[key]
    return (it.get("w"), it.get("d"), it.get("h"))


def _prepare_prototypes(mats):
    items = _dims()
    load_prototype("sofa", _ph("sofa_02"), front="-Y", target=_t(items, "sofa_3seat"),
                   decimate_tris=4000, mat_map=MAP_SOFA, mats=mats)
    load_prototype("chair", _ph("dining_chair_02"), front="-Y", target=_t(items, "dining_chair"),
                   decimate_tris=7000, mat_map=MAP_CHAIR, mats=mats)
    _darken_chair_frame(_PROTO["chair"], mats)
    load_prototype("dining_table", _ph("round_wooden_table_01"), front="-Y",
                   target=_t(items, "dining_table_round"), decimate_tris=5000,
                   mat_map=MAP_WOOD, mats=mats)
    load_prototype("coffee", _ph("modern_coffee_table_01"), front="-Y",
                   target=_t(items, "coffee_table"), decimate_tris=3500,
                   mat_map=MAP_WOOD, mats=mats)
    load_prototype("tv_bench", _ph("modern_wooden_cabinet"), front="-Y",
                   target=_t(items, "tv_bench"), decimate_tris=8000,
                   mat_map=MAP_WOOD, mats=mats)
    load_prototype("bedside", _ph("side_table_01"), front="-Y",
                   target=_t(items, "bedside"), decimate_tris=2500,
                   mat_map=MAP_WOOD, mats=mats)
    load_prototype("wardrobe", _ph("drawer_cabinet"), front="-Y",
                   target=_t(items, "wardrobe"), decimate_tris=8000,
                   mat_map=MAP_WOOD, mats=mats)
    load_prototype("shelves", _ph("wooden_display_shelves_01"), front="+X",
                   target=_t(items, "storage_shelving"), decimate_tris=3000, mat_map=MAP_WOOD, mats=mats)
    load_prototype("stove", _ph("electric_stove"), front="-Y",
                   target=_t(items, "electric_stove"), decimate_tris=8000,
                   mat_map=MAP_STOVE, mats=mats, glass_tag="Stove")
    load_prototype("bed", _kn("bedDouble"), front="-Y", target=_t(items, "bed_double"),
                   mat_map=MAP_BED, mats=mats)
    load_prototype("kcab", _kn("kitchenCabinet"), front="-Y",
                   target=_t(items, "kitchen_base_unit"), mat_map=MAP_KITCHEN, mats=mats)
    load_prototype("kcabd", _kn("kitchenCabinetDrawer"), front="-Y",
                   target=_t(items, "kitchen_base_unit"), mat_map=MAP_KITCHEN, mats=mats)
    load_prototype("kwall", _kn("kitchenCabinetUpper"), front="-Y",
                   target=_t(items, "kitchen_wall_unit"), mat_map=MAP_KITCHEN, mats=mats)
    load_prototype("kwalld", _kn("kitchenCabinetUpperDouble"), front="-Y",
                   target=_t(items, "kitchen_wall_unit"), mat_map=MAP_KITCHEN, mats=mats)
    load_prototype("ksink", _kn("kitchenSink"), front="-Y",
                   target=_t(items, "kitchen_sink_unit"),
                   mat_map=MAP_KITCHEN, mats=mats)
    load_prototype("washer", _kn("washer"), front="-Y",
                   target=_t(items, "washer"), mat_map=MAP_WASHER, mats=mats, glass_tag="WM")
    load_prototype("micro", _kn("kitchenMicrowave"), front="-Y",
                   target=_t(items, "microwave"), mat_map=MAP_MICRO, mats=mats)
    load_prototype("fridge", _kn("kitchenFridge"), front="-Y",
                   target=_t(items, "fridge_tall"), mat_map=MAP_KITCHEN, mats=mats, glass_tag="Fridge")
    load_prototype("wc", _kn("toilet"), front="-Y",
                   target=_t(items, "wc"), mat_map=MAP_BATH, mats=mats)
    load_prototype("basin", _kn("bathroomSinkSquare"), front="-Y",
                   target=_t(items, "basin_vanity"), mat_map=MAP_BATH, mats=mats, glass_tag="Basin")
    load_prototype("shower", _kn("shower"), front="-Y",
                   target=_t(items, "shower"), mat_map=MAP_BATH, mats=mats, glass_tag="Shower")
    load_prototype("mirror", _kn("bathroomMirror"), front="-Y",
                   target=_t(items, "mirror"), mat_map=MAP_BATH, mats=mats, glass_tag="Mirror")
    load_prototype("lamp", _kn("lampRoundTable"), front="-Y",
                   target=(0.18, 0.18, 0.32), mat_map=MAP_LAMP, mats=mats)


def _scale_root_children(root, sx, sy, sz):
    """Non-uniform scale of an already-normalized prototype (width X, depth Y, height Z)."""
    sca = Matrix.Diagonal((sx, sy, sz, 1.0))
    for o in root.children:
        if o.type == "MESH":
            o.data.transform(sca)
            o.data.update()


def place_all(ctx):
    """Place all CC0 furniture. ctx must provide: sc, m, T, CEIL, box, cyl, mats (dict of materials).

    Returns a dict of layout anchors used by build_twobed_v4.py shots / chair assert.
    """
    m = ctx["m"]
    T = ctx["T"]
    CEIL = ctx["CEIL"]
    box = ctx["box"]
    mats = ctx["mats"]
    math_ = ctx.get("math", math)
    Vector_ = ctx.get("Vector", Vector)

    _prepare_prototypes(mats)
    items = _dims()

    # ---------- KITCHEN (right wall run, x≈262, y 240..345 px) — same coords as stand-ins
    kx = m(262, 0).x - T / 2
    ky0 = m(0, 343).y
    ky1 = m(0, 238).y
    L = ky1 - ky0
    n = int(L / 0.6)
    # Units face into the room (−X). front -Y + rot −pi/2 => open_dir (−1,0).
    face = -math.pi / 2
    unit_w = 0.60
    for i in range(n):
        yc = ky0 + 0.3 + i * 0.6
        # root at the footprint centre; depth extends toward −X (into room)
        loc = (kx - 0.30, yc, 0.0)
        if i == 0:
            instance("stove", "Induction_hob_black", loc, face)
        elif i == 1:
            instance("washer", "Washing_machine_black", loc, face)
        elif i == 2:
            instance("ksink", "Sink_steel", loc, face)
        else:
            instance("kcabd" if i == 3 else "kcab", f"Base_unit_{i}", loc, face)
        # wall units (shallower, centre at z will be handled by prototype height + loc z= wall)
        # Stand-in wall unit centre z=1.95, height 0.72 → bottom at 1.59
        wloc = (kx - 0.17, yc, 1.59)
        wu = instance("kwalld" if i == 3 else "kwall", f"Wall_unit_{i}", wloc, face)
        if i == 3:
            instance("micro", "Microwave_frame_black", (kx - 0.33, yc, 1.75), face)

    box("Plinth", (kx - 0.29, (ky0 + ky1) / 2, 0.04), (0.55, L, 0.08), mats["DARK"], 0, 0)
    # worktop over the run except the stove slot (i==0)
    box("Worktop", (kx - 0.31, ky0 + n * 0.3, 0.88), (0.62, n * 0.6, 0.04), mats["WTOP"], 0, 0.002)
    box("LED_strip_under_wall_units", (kx - 0.3, ky0 + n * 0.3, 1.585), (0.02, n * 0.6, 0.01), mats["LED"], 0, 0)
    if n * 0.6 < L - 0.62:
        instance("fridge", "Tall_unit", (kx - 0.30, ky0 + n * 0.6 + 0.3, 0.0), face)

    # dark peninsula with built-in oven — no suitable modern CC0 peninsula; keep stand-in
    pz = m(0, 250).y
    px0 = kx - 0.6
    box("Peninsula_dark", (px0 - 0.9, pz, 0.45), (1.8, 0.6, 0.9), mats["DARK"], 0, 0.003)
    box("Peninsula_top_white_quartz", (px0 - 0.9, pz, 0.915), (1.84, 0.64, 0.03), mats["QUARTZ"], 0, 0.002)
    box("Oven_black_built_in", (px0 - 0.4, pz - 0.301, 0.45), (0.58, 0.01, 0.58), mats["BLK"], 0, 0)

    # ---------- LIVING / DINING
    lc = m(205, 195)
    sofa_y = lc.y
    sx = m(255, 0).x - 0.5
    # sofa faces −X (toward the coffee table / TV)
    instance("sofa", "Sofa_navy_velvet_3seat", (sx, sofa_y, 0), -math.pi / 2)
    ct = Vector_((sx - 1.35, sofa_y, 0))
    instance("coffee", "Coffee_table_oak_top", (ct.x, ct.y, 0), 0)
    tvx = m(150, 0).x + 0.25
    # TV bench faces +X (toward the sofa)
    instance("tv_bench", "TV_bench_oak", (tvx, sofa_y, 0), math.pi / 2)

    dc = Vector_((m(190, 0).x, m(0, 305).y, 0))
    instance("dining_table", "Dining_table_oak_top", (dc.x, dc.y, 0), 0)
    for j, a in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2)):
        instance("chair", "Tub_chair_cream_boucle",
                 (dc.x + 0.72 * math.cos(a), dc.y + 0.72 * math.sin(a), 0),
                 a - math.pi / 2)

    # ---------- BEDROOMS
    b1 = m(55, 105)
    pol = ctx.get("polish") or {}   # lane/polish: optional placement overrides (x, y, rot_z) only; same models
    bp = pol.get("bed1", (b1.x, m(0, 62).y - 1.15, 0))
    sides = pol.get("bed1_sides", [(b1.x - 1.0, m(0, 62).y - 0.35, 0), (b1.x + 1.0, m(0, 62).y - 0.35, 0)])
    instance("bed", "Bed1_navy", (bp[0], bp[1], 0), bp[2])
    for sx_s, sy_s, sa in sides:
        instance("bedside", "Bedside_table_oak", (sx_s, sy_s, 0), sa)
        instance("lamp", "Lamp_mushroom_opal", (sx_s, sy_s, 0.55), sa)
    # wardrobe doors face into the room; keep stand-in rotations
    instance("wardrobe", "Wardrobe_oak_2door", (m(28, 0).x + 0.3, m(0, 150).y, 0), -math.pi / 2)

    b2 = m(185, 70)
    bp = pol.get("bed2", (b2.x, m(0, 40).y - 1.30, 0.06))
    sides = pol.get("bed2_sides", [(b2.x - 1.0, m(0, 40).y - 0.45, 0.06), (b2.x + 1.0, m(0, 40).y - 0.50, 0.06)])
    instance("bed", "Bed2_navy", (bp[0], bp[1], 0), bp[2])
    for sx_s, sy_s, sa in sides:
        instance("bedside", "Bedside_table_oak", (sx_s, sy_s, 0), sa)
        instance("lamp", "Lamp_mushroom_opal", (sx_s, sy_s, 0.55), sa)
    instance("wardrobe", "Wardrobe_oak_2door", (m(140, 0).x, m(0, 135).y, 0), math.pi - 0.12)

    # ---------- BATHROOM fittings (wall tiles stay in the builder)
    bx0, by0 = m(19, 344).x, m(19, 344).y
    bx1, by1 = m(85, 271).x, m(85, 271).y
    # Kenney shower enclosure fills the 0.9 m tray and clips the existing bathroom
    # camera (inside the tray Y-range). Keep the stand-in tray + glass screen.
    box("Shower_tray", (bx0 + 0.5, by0 + 0.5, 0.025), (0.9, 0.9, 0.05), mats["WHITEP"])
    box("Shower_glass_edge_chrome", (bx0 + 0.95, by0 + 0.5, 2.05), (0.02, 0.9, 0.02), mats["CHROME"], 0, 0)
    box("Shower_glass_wall", (bx0 + 0.95, by0 + 0.5, 1.05), (0.008, 0.9, 2.0), mats["GLASS"], 0, 0)
    cyl = ctx["cyl"]
    cyl("Shower_riser_chrome", (bx0 + 0.45, by0 + T / 2 + 0.02, 1.45), 0.012, 1.3, mats["CHROME"], 12)
    box("Shower_arm_chrome", (bx0 + 0.45, by0 + T / 2 + 0.17, 2.12), (0.025, 0.32, 0.025), mats["CHROME"], 0, 0.005)
    cyl("Shower_head", (bx0 + 0.45, by0 + T / 2 + 0.33, 2.09), 0.11, 0.012, mats["CHROME"])
    bw = 0.2
    box("WC_boxing_half_wall", (bx0 + T / 2 + bw / 2, (by0 + 0.95 + by1) / 2, 0.525),
        (bw, by1 - by0 - 0.95, 1.05), mats["TILE"], 0, 0.004)
    box("WC_boxing_top_shelf", (bx0 + T / 2 + bw / 2 + 0.01, (by0 + 0.95 + by1) / 2, 1.06),
        (bw + 0.03, by1 - by0 - 0.95, 0.02), mats["QUARTZ"], 0, 0.002)
    wcy = by1 - 0.65
    box("WC_flush_plate_chrome", (bx0 + T / 2 + bw + 0.004, wcy, 0.85), (0.008, 0.22, 0.15), mats["CHROME"], 0, 0.002)
    wx0 = bx0 + T / 2 + bw
    instance("wc", "WC_pan_back", (wx0 + 0.31, wcy, 0), math.pi / 2)
    vx = pol.get("vanity_x", bx1 - 0.45)
    instance("basin", "Vanity_grey_stone_look", (vx, by1 - T / 2 - 0.24, 0), 0)
    instance("mirror", "Mirror_black_frame", (vx, by1 - T / 2 - 0.02, 1.18), 0)

    # ---------- storage shelving: scale prototype to room width × 0.4 × 2.2
    s0 = m(20, 268)
    s1 = m(88, 202)
    width = abs(s1.y - s0.y) - 0.2
    # prototype currently native size (front already -Y after +X correction). Scale a unique copy.
    # Use a one-off scaled instance: duplicate meshes, scale, place. Width along X after front -Y,
    # then rot +pi/2 to face +X (into the room from the west wall).
    proto = _PROTO["shelves"]
    mins, maxs = _bbox_world(proto.children)
    size = maxs - mins
    sx_ = width / size.x if size.x else 1
    sy_ = 0.40 / size.y if size.y else 1
    sz_ = 2.20 / size.z if size.z else 1
    # Don't mutate the prototype (lineup may reuse it): instance then scale children data? that would
    # also mutate linked data. So make unique meshes for the room-sized shelf.
    e = bpy.data.objects.new("Storage_shelving_white", None)
    _link(e)
    e.location = (s0.x + 0.25, (s0.y + s1.y) / 2, 0)
    e.rotation_euler[2] = math.pi / 2
    sca = Matrix.Diagonal((sx_, sy_, sz_, 1.0))
    for ch in proto.children:
        inst = ch.copy()
        inst.data = ch.data.copy()
        inst.data.transform(sca)
        inst.data.update()
        inst.name = "Storage_shelving_mesh"
        _link(inst)
        inst.parent = e
        inst.location = (ch.location.x * sx_, ch.location.y * sy_, ch.location.z * sz_)
        inst.hide_set(False)
        inst.hide_render = False

    discard_prototypes()
    return {
        "kx": kx, "ky0": ky0, "ky1": ky1, "n": n,
        "sx": sx, "sofa_y": sofa_y, "ct": ct, "tvx": tvx, "dc": dc,
        "b1": b1, "b2": b2,
        "bx0": bx0, "by0": by0, "bx1": by1, "by1": by1,
        "wcy": wcy, "wx0": wx0, "vx": vx,
    }


def proto_dims(key):
    """Normalized prototype size (w along local X, d along local Y, h) in metres."""
    return Vector(_PROTO[key]["cc0_final_dims"])


def _fit(e, key, w=None, d=None, h=None):
    """Non-uniform scale on the instance root so the CC0 model fills a footprint taken from the plan trace."""
    s = proto_dims(key)
    e.scale = ((w / s.x) if w else 1.0, (d / s.y) if d else 1.0, (h / s.z) if h else 1.0)
    e["fit_target"] = [float(v or 0.0) for v in (w, d, h)]
    return e


def place_trace(ctx, FUR, JOIN):
    """lane/walls (2026-11-20): place the same CC0 models at the positions/footprints traced from the
    Rightmove plan (interior/trace/twobed_layout.py) instead of the pre-retrace stand-in coordinates.

    FUR  = {name: item} from twobed_layout.furniture() (Blender metres; c, s, rot, W/Lb for beds)
    JOIN = {name: item} from twobed_layout.joinery_bl() (Blender metres; poly)
    Plan wins: no kitchen peninsula (the plan does not draw one); the plan's dining table is rectangular,
    so the round CC0 table is not used (rectangular table stays procedural in build_twobed_v4.py);
    built-in wardrobes stay traced joinery. Returns a list of placed root empties tagged with "room".
    """
    m = ctx["m"]
    box = ctx["box"]
    mats = ctx["mats"]
    T = ctx["T"]
    _prepare_prototypes(mats)
    out = []

    def put(key, name, loc, rot, room, **fit):
        e = instance(key, name, loc, rot)
        if fit:
            _fit(e, key, **fit)
        e["room"] = room
        e["cc0_key"] = key
        out.append(e)
        return e

    def V2(p):
        return Vector((p[0], p[1], 0.0))

    # ---------- LIVING
    sf = FUR["Sofa_navy_velvet_3seat"]   # plan box 29 x 53 px, back on the east side, faces -X
    put("sofa", "Sofa_navy_velvet_3seat", V2(sf["c"]), -math.pi / 2, "i_living", w=sf["s"][1], d=sf["s"][0])
    ct = FUR["Coffee_table_oak_top"]
    put("coffee", "Coffee_table_oak_top", V2(ct["c"]), 0.0, "i_living", w=ct["s"][0], d=ct["s"][1])
    tvp = JOIN["TV_unit"]["poly"]       # plan box x 122-137, y 158-198: bench front faces +X (sofa)
    xs = [p[0] for p in tvp]; ys = [p[1] for p in tvp]
    put("tv_bench", "TV_bench_oak", Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0)), math.pi / 2,
        "i_living", w=max(ys) - min(ys) - 0.02, d=max(xs) - min(xs) - 0.02, h=0.45)   # 1 cm inside the drawn box
    for k in range(4):   # chair opening = local -Y, rotations from the trace (north chairs 0, south chairs pi)
        f = FUR[f"Tub_chair_{k}"]
        put("chair", "Tub_chair_cream_boucle", V2(f["c"]), f["rot"], "i_living")

    # ---------- BEDROOMS (bed footprint = drawn foot edge to the drawn head wall; headboard inside it)
    for bn, room in (("Bed1_navy", "i_bed1"), ("Bed2_navy", "i_bed2")):
        f = FUR[bn]
        hd = Vector((-math.sin(f["rot"]), math.cos(f["rot"]), 0))
        L = f["Lb"] + 0.12
        put("bed", bn, V2(f["c"]) + hd * 0.06, f["rot"], room, w=f["W"], d=L)
        for k in (0, 1):
            g = FUR[f"{bn[:4]}_bedside_{k}"]
            put("bedside", "Bedside_table_oak", V2(g["c"]), g["rot"], room)
            hb = proto_dims("bedside").z
            put("lamp", "Lamp_mushroom_opal", Vector((g["c"][0], g["c"][1], hb)), g["rot"], room)

    # ---------- KITCHEN: L-run drawn on the plan (south run x 161-253.5 / front y=321, east leg y 277-321)
    yb = m(0, 343.5).y; yf = m(0, 321).y; xw = m(161, 0).x + T / 2 + 0.005; xe = m(253.5, 0).x   # x=161 is the stair partition centreline
    BD = 0.58
    cy = yf - 0.02 - BD / 2
    box("Kitchen_plinth_S", ((xw + xe) / 2, cy, 0.04), (xe - xw, BD - 0.04, 0.08), mats["DARK"], 0, 0)
    wm = FUR["Washing_machine"]["c"][0]; hob = FUR["Hob"]["c"][0]; sk = FUR["Sink"]["c"]
    put("washer", "Washing_machine_black", Vector((wm, cy, 0)), math.pi, "i_kitchen", w=0.597)
    put("stove", "Induction_hob_black", Vector((hob, cy, 0)), math.pi, "i_kitchen", w=0.597, h=0.90)
    put("kcabd", "Base_unit_0", Vector(((xw + wm - 0.30) / 2, cy, 0.08)), math.pi, "i_kitchen",
        w=max(0.05, wm - 0.30 - xw - 0.003), h=0.78) if wm - 0.30 - xw > 0.08 else None
    x0 = hob + 0.30; run = xe - x0; n = max(1, round(run / 0.6)); uw = run / n
    for i in range(n):
        put("kcabd" if i == 0 else "kcab", f"Base_unit_{i + 1}", Vector((x0 + uw * (i + 0.5), cy, 0.08)), math.pi,
            "i_kitchen", w=uw - 0.003, h=0.78)
    # worktop over the south run, cut at the stove (it carries its own hob top)
    for a, b in ((xw, hob - 0.30), (hob + 0.30, xe)):
        if b - a > 0.02:
            box("Worktop", ((a + b) / 2, (yb + yf) / 2, 0.88), (b - a, yf - yb, 0.04), mats["WTOP"], 0, 0.002)
    # east leg: units face -X, sink unit at the drawn sink
    xe0 = m(233, 0).x; cx = xe - 0.01 - BD / 2; ytop = m(0, 277).y
    put("ksink", "Sink_steel", Vector((cx, sk[1], 0)), -math.pi / 2, "i_kitchen", w=0.597, h=0.90)
    top_len = ytop - (sk[1] + 0.30)
    if top_len > 0.1:
        put("kcab", "Base_unit_E", Vector((cx, sk[1] + 0.30 + top_len / 2, 0.08)), -math.pi / 2, "i_kitchen",
            w=top_len - 0.003, h=0.78)
        box("Worktop", ((xe0 + xe) / 2, sk[1] + 0.30 + top_len / 2, 0.88), (xe - xe0, top_len, 0.04), mats["WTOP"], 0, 0.002)
    gap = (sk[1] - 0.30) - yf
    if gap > 0.01:
        box("Kitchen_filler_E", (cx, yf + gap / 2, 0.45), (BD, gap, 0.82), mats["WUNIT"], 0, 0)
        box("Worktop", ((xe0 + xe) / 2, yf + gap / 2, 0.88), (xe - xe0, gap, 0.04), mats["WTOP"], 0, 0.002)
    box("Kitchen_plinth_E", (cx, (ytop + sk[1] + 0.30) / 2, 0.04), (BD - 0.04, max(0.05, ytop - sk[1] - 0.30), 0.08), mats["DARK"], 0, 0)
    # wall units along the south wall only (plan shows no east wall units; heights STAND-IN)
    nw = max(1, round((xe - xw) / 0.6)); ww = (xe - xw) / nw; wd = proto_dims("kwall").y
    for i in range(nw):
        wloc = Vector((xw + ww * (i + 0.5), yb + 0.025 + wd / 2, 1.45))
        if i == 1:
            # CGI kitchen_run: black microwave in the second wall-unit bay.
            # Neighbouring bays keep their centres; this bay is the microwave only.
            put("micro", "Microwave_frame_black", Vector((wloc.x, wloc.y, 1.45 + 0.06)),
                math.pi, "i_kitchen", w=min(0.50, ww - 0.06))
        else:
            put("kwall", f"Wall_unit_{i}", wloc, math.pi, "i_kitchen", w=ww - 0.003)

    # ---------- BATHROOM (plan: WC + basin on the west wall, face +X)
    xwb = m(16.5, 0).x
    wc = FUR["WC_pan"]["c"]
    put("wc", "WC_pan_back", Vector((wc[0], wc[1], 0)), math.pi / 2, "i_bath")
    vbf = FUR["Vanity_basin"]; vb = vbf["c"]
    put("basin", "Vanity_grey_stone_look", Vector((vb[0], vb[1], 0)), math.pi / 2, "i_bath", w=vbf["s"][1], d=vbf["s"][0])
    d_m = proto_dims("mirror").y
    put("mirror", "Mirror_black_frame", Vector((xwb + 0.012 + d_m / 2, vb[1], 1.18)), math.pi / 2, "i_bath")

    # ---------- STORAGE shelving along the west wall of the traced store, faces +X
    st = FUR["Storage_shelving_white"]
    put("shelves", "Storage_shelving_white", V2(st["c"]), math.pi / 2, "i_store", w=st["s"][1], d=st["s"][0], h=2.2)

    discard_prototypes()
    return [e for e in out if e is not None]


def kit_groups():
    """Category lineups: (group_key, title, [(proto_key, label), ...])."""
    return [
        ("living", "Living / dining", [
            ("sofa", "Sofa"),
            ("chair", "Dining chair"),
            ("dining_table", "Round table (kit)"),
            ("coffee", "Coffee table"),
            ("tv_bench", "TV bench"),
        ]),
        ("bedroom", "Bedroom / storage", [
            ("bed", "Double bed"),
            ("bedside", "Bedside table"),
            ("lamp", "Bedside lamp"),
            ("wardrobe", "Wardrobe (kit)"),
            ("shelves", "Storage shelving"),
        ]),
        ("kitchen", "Kitchen", [
            ("kcab", "Base unit"),
            ("ksink", "Sink unit"),
            ("kwall", "Wall unit"),
            ("stove", "Induction stove"),
            ("washer", "Washing machine"),
            ("micro", "Microwave"),
            ("fridge", "Fridge (kit)"),
        ]),
        ("bath", "Bathroom", [
            ("wc", "WC"),
            ("basin", "Vanity / basin"),
            ("shower", "Shower (kit)"),
            ("mirror", "Mirror"),
        ]),
    ]


def scale_audit():
    """Compare each loaded prototype to furniture_dims.json (metres)."""
    items = _dims()
    key_to_dim = {
        "sofa": "sofa_3seat", "chair": "dining_chair", "dining_table": "dining_table_round",
        "coffee": "coffee_table", "tv_bench": "tv_bench", "bedside": "bedside",
        "wardrobe": "wardrobe", "shelves": "storage_shelving", "stove": "electric_stove",
        "bed": "bed_double", "kcab": "kitchen_base_unit", "kcabd": "kitchen_base_unit",
        "kwall": "kitchen_wall_unit", "kwalld": "kitchen_wall_unit",
        "ksink": "kitchen_sink_unit", "washer": "washer", "micro": "microwave",
        "fridge": "fridge_tall", "wc": "wc", "basin": "basin_vanity",
        "shower": "shower", "mirror": "mirror", "lamp": "bedside_lamp",
    }
    rows = []
    for key, root in _PROTO.items():
        final = list(root.get("cc0_final_dims", [0, 0, 0]))
        target = list(root.get("cc0_target_dims", [])) if "cc0_target_dims" in root.keys() else None
        dim_key = key_to_dim.get(key)
        specified = None
        if dim_key and dim_key in items:
            it = items[dim_key]
            specified = [it.get("w"), it.get("d"), it.get("h")]
        err = None
        if specified:
            err = []
            for a, b in zip(final, specified):
                if a is None or b is None:
                    err.append(None)
                else:
                    err.append(round(a - b, 4))
        rows.append({"key": key, "final": [round(x, 4) for x in final],
                     "target": target, "furniture_dims": specified, "delta_m": err})
    return rows


def iter_kit_items():
    """Lineup order: (key, label, path). Prototypes must already be loaded."""
    return [
        ("sofa", "Sofa 02"),
        ("chair", "Dining Chair 02"),
        ("dining_table", "Round Wooden Table 01"),
        ("coffee", "Modern Coffee Table 01"),
        ("tv_bench", "Modern Wooden Cabinet"),
        ("bedside", "Side Table 01"),
        ("wardrobe", "Drawer Cabinet"),
        ("shelves", "Wooden Display Shelves 01"),
        ("stove", "Electric Stove"),
        ("bed", "Kenney bedDouble"),
        ("kcab", "Kenney kitchenCabinet"),
        ("ksink", "Kenney kitchenSink"),
        ("washer", "Kenney washer"),
        ("micro", "Kenney kitchenMicrowave"),
        ("fridge", "Kenney kitchenFridge"),
        ("wc", "Kenney toilet"),
        ("basin", "Kenney bathroomSinkSquare"),
        ("shower", "Kenney shower"),
        ("mirror", "Kenney bathroomMirror"),
        ("lamp", "Kenney lampRoundTable"),
    ]



def _darken_chair_frame(root, mats, seat_z=0.45):
    """Single-material CC0 chair: faces below the seat become espresso (CGI dark frame)."""
    import bmesh
    dark = mats["DARKW"]
    for o in list(root.children):
        if o.type != "MESH" or not o.data.polygons:
            continue
        me = o.data
        if dark.name not in me.materials:
            me.materials.append(dark)
        di = me.materials.find(dark.name)
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        mw = o.matrix_world
        for f in bm.faces:
            c = mw @ f.calc_center_median()
            if c.z < seat_z:
                f.material_index = di
        bm.to_mesh(me)
        bm.free()
        me.update()


def make_scale_bar(origin, mats=None, sc=None):
    """1 m reference bar along +X, two 0.5 m bands, origin at left end, z=0."""
    sc = sc or _scene()

    def band(n, x0, x1, col):
        me = bpy.data.meshes.new(n)
        # box from x0..x1, y=0..0.06, z=0..0.04
        dx, dy, dz = x1 - x0, 0.12, 0.08
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=(dx, dy, dz), verts=bm.verts)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(n, me)
        sc.collection.objects.link(o)
        o.location = (origin[0] + (x0 + x1) / 2, origin[1] + dy / 2, dz / 2)
        mat = bpy.data.materials.new(n + "_mat")
        mat.use_nodes = True
        b = mat.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1)
        b.inputs["Roughness"].default_value = 0.4
        o.data.materials.append(mat)
        return o

    a = band("ScaleBar_0_50cm", 0.0, 0.5, (0.05, 0.05, 0.05))
    b = band("ScaleBar_50_100cm", 0.5, 1.0, (0.95, 0.15, 0.1))
    # label
    bpy.ops.object.text_add(location=(origin[0] + 0.5, origin[1] - 0.32, 0.02))
    t = bpy.context.object
    t.name = "ScaleBar_label_1m"
    t.data.body = "1 m"
    t.data.extrude = 0.004
    t.data.size = 0.28
    t.data.align_x = "CENTER"
    return [a, b, t]


def make_scale_post(origin, sc=None, band=0.10):
    """Vertical 1 m bar at origin (z=0..1), alternating 10 cm black/white bands + '1 m' label."""
    import bmesh
    sc = sc or _scene()
    outs = []
    n = int(round(1.0 / band))
    for i in range(n):
        z0, z1 = i * band, (i + 1) * band
        me = bpy.data.meshes.new(f"ScalePost_{i}")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=(0.05, 0.05, z1 - z0), verts=bm.verts)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(f"ScalePost_{i}", me)
        sc.collection.objects.link(o)
        o.location = (origin[0], origin[1], (z0 + z1) / 2)
        mat = bpy.data.materials.new(f"ScalePost_{i}_mat")
        mat.use_nodes = True
        col = (0.06, 0.06, 0.06) if i % 2 == 0 else (0.96, 0.96, 0.94)
        b = mat.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1)
        b.inputs["Roughness"].default_value = 0.45
        o.data.materials.append(mat)
        outs.append(o)
    bpy.ops.object.text_add(location=(origin[0], origin[1] - 0.18, 1.04))
    t = bpy.context.object
    t.name = "ScalePost_label_1m"
    t.data.body = "1 m"
    t.data.extrude = 0.004
    t.data.size = 0.16
    t.data.align_x = "CENTER"
    t.rotation_euler = (1.5708, 0, 0)
    outs.append(t)
    return outs


def discard_prototypes():
    """Remove prototype objects after instancing so they are not baked/exported. Mesh data stays."""
    for root in list(_PROTO.values()):
        for ch in list(root.children):
            bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(root, do_unlink=True)
    _PROTO.clear()
