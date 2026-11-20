"""Trick #13: street-prop normaliser (method from AnyKit, MIT; paid generators not used).

For each Kenney CC0 asset listed in props_dims.json:
  - apply transforms, origin to bottom-centre, front stays -Y (glTF import)
  - scale so the primary dimension matches the sourced value (or keep the
    certified #9 life_paths scale when keep_life_scale is set)
  - map materials onto a 6-slot palette (paint, metal, glass, rubber, fabric, wood)
  - export a full GLB and a LOD1 (~25% tris) GLB
  - measure and write tests/props/out/kit.json
  - render a lineup with a 1 m scale bar to tests/props/out/props_lineup.png

Never overwrites the original Kenney files (assets/life/kenney/...).
Run: blender -b -P props_normalize.py
     LINEUP=1 to also render the scale-bar lineup (default on).
"""
from __future__ import annotations
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
K = os.path.join(HERE, "assets", "life", "kenney")
DIMS = json.load(open(os.path.join(HERE, "props_dims.json")))
OUT = os.environ.get("BOUT", os.path.join(HERE, "tests", "props", "out"))
NORM = os.path.join(HERE, "assets", "life", "normalized")
os.makedirs(OUT, exist_ok=True)
os.makedirs(NORM, exist_ok=True)

PALETTE = {
    "paint":  ((0.15, 0.16, 0.18), 0.45, 0.0),
    "metal":  ((0.35, 0.35, 0.36), 0.35, 0.8),
    "glass":  ((0.05, 0.07, 0.08), 0.05, 0.0),
    "rubber": ((0.03, 0.03, 0.03), 0.7, 0.0),
    "fabric": ((0.25, 0.22, 0.20), 0.8, 0.0),
    "wood":   ((0.28, 0.18, 0.10), 0.7, 0.0),
}


def palette_mats():
    out = {}
    for name, (rgb, rough, metal) in PALETTE.items():
        m = bpy.data.materials.new("PROP_" + name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if name == "glass":
            b.inputs["Alpha"].default_value = 0.3
            m.blend_method = "BLEND"
        out[name] = m
    return out


def classify(mat_name):
    n = (mat_name or "").lower()
    if any(k in n for k in ("glass", "window", "wind", "transp")):
        return "glass"
    if any(k in n for k in ("rubber", "tyre", "tire", "wheel", "black")):
        return "rubber"
    if any(k in n for k in ("metal", "chrome", "steel", "iron", "silver")):
        return "metal"
    if any(k in n for k in ("cloth", "fabric", "shirt", "skin", "hair")):
        return "fabric"
    if any(k in n for k in ("wood", "bark")):
        return "wood"
    return "paint"


def world_bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    if not pts:
        return None
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def tris(objs):
    n = 0
    for o in objs:
        if o.type != "MESH":
            continue
        me = o.data
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
    return n


def decimate(objs, ratio=0.25):
    for o in objs:
        if o.type != "MESH" or not o.data.polygons:
            continue
        md = o.modifiers.new("LOD1", "DECIMATE")
        md.ratio = ratio
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.modifier_apply(modifier="LOD1")
        o.select_set(False)


def load_gltf(rel):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(K, rel))
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o)
    return [o for o in bpy.data.objects if o not in before and o.name in {x.name for x in new} or o in new]


def normalize_one(prop, mats):
    rel = prop.get("asset")
    if not rel:
        return None
    # fresh objects only
    new = []
    before = set(bpy.data.objects)
    path = os.path.join(K, rel)
    if not os.path.isfile(path):
        print("MISSING", path)
        return None
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o, do_unlink=True)
    new = [o for o in bpy.data.objects if o not in before and o.name in bpy.data.objects]
    meshes = [o for o in new if o.type == "MESH"]
    # Kenney characters ship as a parented node tree. Applying scale only to
    # parentless meshes left walkers at native height (~0.67 m). Unparent
    # with keep_transform, then bake loc/rot/scale into the mesh data.
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                pass
    bpy.context.view_layer.update()
    for o in meshes:
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    bb = world_bounds(meshes)
    if not bb:
        return None
    (x0, y0, z0), (x1, y1, z1) = bb
    # shift so bottom-centre is at origin (all meshes are now unparented)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    for o in meshes:
        o.location.x -= cx
        o.location.y -= cy
        o.location.z -= z0
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    native = world_bounds(meshes)
    (nx0, ny0, nz0), (nx1, ny1, nz1) = native
    nat = {"w": nx1 - nx0, "l": ny1 - ny0, "h": nz1 - nz0}
    # scale
    if prop.get("keep_life_scale"):
        # leave at native * later life_paths scale; here export unscaled (scale 1)
        scale = 1.0
        reason = "keep_life_scale (certified #9 stand-in)"
    else:
        primary = prop.get("primary", "height_m")
        if primary == "length_m" and prop.get("length_m") and nat["l"] > 1e-6:
            scale = prop["length_m"] / nat["l"]
            reason = "length_m"
        elif prop.get("height_m") and nat["h"] > 1e-6:
            scale = prop["height_m"] / nat["h"]
            reason = "height_m"
        else:
            scale = 1.0
            reason = "no primary dim"
        for o in meshes:
            o.scale = (scale, scale, scale)
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.context.view_layer.update()
    # remap materials
    for o in meshes:
        for slot in o.material_slots:
            if slot.material:
                slot.material = mats[classify(slot.material.name)]
    bb2 = world_bounds(meshes)
    (ax0, ay0, az0), (ax1, ay1, az1) = bb2
    sized = {"w": ax1 - ax0, "l": ay1 - ay0, "h": az1 - az0, "zmin": az0, "zmax": az1}
    ntris = tris(meshes)
    # export full
    dest = os.path.join(NORM, prop["id"] + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    for o in new:
        if o.name in bpy.data.objects:
            o.select_set(True)
    tmp = dest + ".tmp.glb"
    bpy.ops.export_scene.gltf(filepath=tmp, use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True, export_cameras=False, export_lights=False)
    os.replace(tmp, dest)
    # LOD1 copy: decimate then export, then we leave the full-res objects for the lineup
    # Work on copies
    lod_objs = []
    for o in meshes:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        lod_objs.append(c)
    decimate(lod_objs, 0.25)
    lod_tris = tris(lod_objs)
    lod = os.path.join(NORM, prop["id"] + "_lod1.glb")
    bpy.ops.object.select_all(action="DESELECT")
    for o in lod_objs:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
    tmp = lod + ".tmp.glb"
    bpy.ops.export_scene.gltf(filepath=tmp, use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True, export_cameras=False, export_lights=False)
    os.replace(tmp, lod)
    for o in lod_objs:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    rec = {
        "id": prop["id"],
        "asset": rel,
        "source_url": prop.get("source_url"),
        "source_note": prop.get("source_note"),
        "stand_in": bool(prop.get("stand_in", True)),
        "licence": "Kenney CC0 (assets/life/kenney/*/License.txt)",
        "native_m": {k: round(v, 4) for k, v in nat.items()},
        "scale": round(scale, 5),
        "scale_reason": reason,
        "sized_m": {k: round(v, 4) for k, v in sized.items()},
        "target": {k: prop[k] for k in ("length_m", "height_m", "width_m") if k in prop},
        "tris": ntris,
        "lod1_tris": lod_tris,
        "lod1_ratio": (lod_tris / ntris) if ntris else None,
        "glb": os.path.relpath(dest, HERE),
        "lod1_glb": os.path.relpath(lod, HERE),
        "front": "-Y",
        "origin": "bottom-centre",
    }
    # keep the full-res meshes for lineup (tagged)
    for o in meshes:
        o["prop_id"] = prop["id"]
    return rec, meshes


def add_scale_bar(col, y, mats):
    """1 m scale visible in the +X side-view lineup: a vertical post and a
    ground bar along Y (a bar along X is end-on to the camera and disappears).
    """
    def box(name, x0, x1, y0, y1, z0, z1, m):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        me = bpy.data.meshes.new(name)
        me.from_pydata(v, [], f)
        me.update()
        o = bpy.data.objects.new(name, me)
        o.data.materials.append(m)
        col.objects.link(o)
        return o
    # vertical 1 m post
    bar = box("SCALE_BAR_1m", -0.03, 0.03, y - 0.03, y + 0.03, 0.0, 1.0, mats["metal"])
    for z in (0.0, 0.5, 1.0):
        box("SCALE_TICK", -0.06, 0.06, y - 0.06, y + 0.06, z, z + 0.03, mats["paint"])
    # 1 m ground bar along Y (lineup axis)
    box("SCALE_BAR_1m_Y", -0.02, 0.02, y, y + 1.0, 0.0, 0.03, mats["metal"])
    bar["source"] = "1 m scale bar"
    return bar


def lineup(records_and_meshes, mats):
    # place each prop in a row, +Y is front, side view along +X looking at -X? 
    # Camera on +X looking at origin, props spaced along Y, standing on Z=0, front -Y so side profile is visible from +X.
    x = 0.0
    gap = 0.6
    placed = []
    cursor = 3.2  # leave room on the left for the 1 m scale bar
    for rec, meshes in records_and_meshes:
        w = rec["sized_m"]["w"]
        # move to cursor along Y
        # current origin is bottom-centre
        for o in meshes:
            if o.parent is None:
                o.location.y += cursor
        placed.append((rec, cursor, w))
        cursor += max(w, rec["sized_m"]["l"]) + gap
    add_scale_bar(bpy.context.scene.collection, 0.0, mats)
    # ortho camera from +X; include the 1 m bar at y=-1.5 and the last prop
    camd = bpy.data.cameras.new("Cam_Lineup")
    camd.type = "ORTHO"
    y0, y1 = -0.8, cursor + 0.4
    span = max(y1 - y0, 3.0)
    camd.ortho_scale = span
    cam = bpy.data.objects.new("Cam_Lineup", camd)
    cam.location = (14.0, (y0 + y1) / 2.0, 1.2)
    cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    bpy.context.scene.collection.objects.link(cam)
    sc = bpy.context.scene
    sc.camera = cam
    # simple light
    sun = bpy.data.objects.new("LineupSun", bpy.data.lights.new("LineupSun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    sc.collection.objects.link(sun)
    world = sc.world or bpy.data.worlds.new("LineupWorld")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.8, 0.82, 0.85, 1)
        bg.inputs[1].default_value = 1.0
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 32
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1920, 540
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    path = os.path.join(OUT, "props_lineup.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # also copy to repo out/ only as a test artifact path note; official out/ gets a copy if LINEUP_OUT=1
    print("LINEUP", path)
    return path


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = palette_mats()
    recs = []
    hold = []
    for prop in DIMS["props"]:
        if not prop.get("asset"):
            recs.append({
                "id": prop["id"],
                "kind": prop["kind"],
                "procedural": True,
                "used_by": prop.get("used_by"),
                "target": {k: prop[k] for k in ("length_m", "height_m", "width_m", "diameter_m") if k in prop},
                "source_url": prop.get("source_url"),
                "source_note": prop.get("source_note"),
                "stand_in": bool(prop.get("stand_in", True)),
            })
            continue
        result = normalize_one(prop, mats)
        if not result:
            recs.append({"id": prop["id"], "error": "import failed"})
            continue
        rec, meshes = result
        recs.append(rec)
        hold.append((rec, meshes))
        print("NORM", rec["id"], "scale", rec["scale"], "sized", rec["sized_m"], "tris", rec["tris"], "lod1", rec["lod1_tris"])
    kit = {"trick": 13, "palette": list(PALETTE), "props": recs}
    json.dump(kit, open(os.path.join(OUT, "kit.json"), "w"), indent=2)
    json.dump(kit, open(os.path.join(NORM, "kit.json"), "w"), indent=2)
    if os.environ.get("LINEUP", "1") == "1" and hold:
        lineup(hold, mats)
    print("PROPS_NORMALIZE_DONE", len(recs))


if __name__ == "__main__":
    main()
