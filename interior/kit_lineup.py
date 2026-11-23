#!/usr/bin/env python3
"""Render CC0 furniture lineups with a 1 m scale bar.

Writes:
  interior/assets/kit_lineup.png              overall (two rows, labels)
  interior/assets/kit_lineup_living.png
  interior/assets/kit_lineup_bedroom.png
  interior/assets/kit_lineup_kitchen.png
  interior/assets/kit_lineup_bath.png
  interior/assets/scale_audit.json
"""
import json, math, os, sys
import bpy
from mathutils import Vector
_HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import furniture_cc0 as furn

ASSETS = furn.ASSETS
os.makedirs(ASSETS, exist_ok=True)
TMP = os.path.join(ASSETS, "_lineup_raw")
os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(n, c, r=0.5, met=0):
    M = bpy.data.materials.new(n)
    M.use_nodes = True
    b = M.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = r
    b.inputs["Metallic"].default_value = met
    return M


def mats_from_palette():
    mats = {}
    for key, (col, rough, met) in furn.PALETTE.items():
        mats[key] = mat(key + "_pal", col, rough, met)
    mats["GLASS"].node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
    return mats


mats = mats_from_palette()
furn._prepare_prototypes(mats)

audit = furn.scale_audit()
with open(os.path.join(ASSETS, "scale_audit.json"), "w") as f:
    json.dump({"unit": "metres", "items": audit}, f, indent=2)
print("SCALE_AUDIT", os.path.join(ASSETS, "scale_audit.json"))
for row in audit:
    print("SCALE", row)


def make_floor(name, cx, cy, sx, sy, z=-0.01):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(sx, sy, 0.02), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = (cx, cy, z)
    fm = mat(name + "_mat", (0.78, 0.76, 0.72), 0.7)
    o.data.materials.append(fm)
    return o


def studio_world():
    world = bpy.data.worlds.new("kit_world")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.18, 0.185, 0.195, 1)
    bg.inputs[1].default_value = 0.55
    return world


def lights(cx, cy=-6.0):
    bpy.ops.object.light_add(type="AREA", location=(cx, cy + 1.0, 4.2))
    key = bpy.context.object
    key.data.energy = 420
    key.data.size = 7
    key.data.color = (1.0, 0.97, 0.93)
    bpy.ops.object.light_add(type="AREA", location=(cx + 5.0, 2.2, 3.2))
    fill = bpy.context.object
    fill.data.energy = 140
    fill.data.size = 5
    fill.data.color = (0.82, 0.88, 1.0)
    bpy.ops.object.light_add(type="AREA", location=(cx - 4.0, 1.0, 2.4))
    rim = bpy.context.object
    rim.data.energy = 80
    rim.data.size = 3
    rim.data.color = (1.0, 0.95, 0.9)
    return key, fill, rim


def place_row(items, y=0.0, gap=0.45, x0=0.0, min_slot=0.85):
    """Place (key, label) along +X, facing -Y, sitting on z=0. Returns recs and span.

    Narrow pieces get a min_slot so annotation labels do not overlap.
    A 0.4 m left pad is reserved for the vertical 1 m post.
    """
    x = x0 + 0.40
    recs = []
    max_h = 0.3
    max_d = 0.3
    for key, label in items:
        root = furn._PROTO[key]
        dims = list(root.get("cc0_final_dims", [1, 1, 1]))
        w, d, h = dims
        slot = max(w, min_slot)
        x += slot / 2
        inst = furn.instance(key, f"kit_{key}_{len(recs)}", (x, y, 0), 0.0)
        recs.append({"key": key, "label": label, "x": x, "w": w, "d": d, "h": h, "y": y})
        max_h = max(max_h, h)
        max_d = max(max_d, d)
        x += slot / 2 + gap
    span = x - gap if recs else 1.0
    return recs, span, max_h, max_d



def hide_placed():
    """Hide every instanced kit object (children keep their imported mesh names)."""
    for o in list(sc.objects):
        if o.type in ("CAMERA", "LIGHT", "WORLD"):
            continue
        if o.name in ("kit_floor",) or o.name.startswith("kit_floor"):
            continue
        if o.name.startswith("ScaleBar") or o.name.startswith("ScalePost"):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.hide_render = True
        try:
            o.hide_set(True)
        except Exception:
            pass

def render_strip(path, recs, span, max_h, title=None, resx=2400, resy=900):
    cam_x = span / 2
    # Fit both the row width and the tallest piece + headroom so the 1 m post stays in frame.
    margin_x = 0.45
    need_h = max_h + 0.55
    aspect = resx / float(resy)
    ortho_w = max(span + 2 * margin_x, need_h * aspect)
    cam_y = -10.0
    cam_z = need_h * 0.48
    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    cam = bpy.context.object
    target = Vector((cam_x, 0.0, need_h * 0.42))
    cam.rotation_euler = (target - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ortho_w
    sc.camera = cam

    # Vertical 1 m post just left of the first piece; horizontal 1 m bar on the floor in front.
    first = recs[0]
    post_x = first["x"] - max(first["w"], 0.85) / 2 - 0.22
    furn.make_scale_post((post_x, first["y"] + 0.15, 0.0), sc=sc)
    bar_origin = (post_x - 0.10, first["y"] - 0.85, 0.0)
    furn.make_scale_bar(bar_origin, mats=mats, sc=sc)

    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 24
        sc.cycles.use_denoising = True
    print("ENGINE", sc.render.engine)
    sc.render.resolution_x = resx
    sc.render.resolution_y = resy
    sc.render.film_transparent = False
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    bpy.ops.render.render(write_still=True)
    print("LINEUP_WRITTEN", path, "span_m", round(span, 2), "n", len(recs), "ortho", round(ortho_w, 2))
    return cam_x, ortho_w, bar_origin



# Collect render metadata; annotation happens in system Python (Blender has no Pillow).
META = []

def record(raw, recs, span, ortho_w, title, out_path):
    META.append({"raw": raw, "recs": recs, "span": span, "ortho_w": ortho_w, "title": title, "out": out_path})
    print("RECORDED", out_path, "n", len(recs))


# ---- per-category lineups ----
studio_world()
make_floor("kit_floor", 8, 0.2, 28, 8)
lights(6.0)

outputs = {}
groups = furn.kit_groups()

for gkey, title, items in groups:
    recs, span, max_h, max_d = place_row(items, y=0.0, gap=0.50)
    raw = os.path.join(TMP, f"{gkey}.png")
    cam_x, ortho_w, _ = render_strip(raw, recs, span, max_h, title=title, resx=2400, resy=720)
    out = os.path.join(ASSETS, f"kit_lineup_{gkey}.png")
    record(raw, recs, span, ortho_w, title + "  ·  1 m bar", out)
    outputs[gkey] = out
    hide_placed()
    if sc.camera:
        bpy.data.objects.remove(sc.camera, do_unlink=True)


def render_combined(items, name, resx=3200, resy=900, gap=0.40):
    recs, span, max_h, max_d = place_row(items, y=0.0, gap=gap)
    raw = os.path.join(TMP, f"{name}.png")
    cam_x, ortho_w, _ = render_strip(raw, recs, span, max_h, resx=resx, resy=resy)
    hide_placed()
    if sc.camera:
        bpy.data.objects.remove(sc.camera, do_unlink=True)
    return recs, span, ortho_w, raw, max_h

living_items = groups[0][2] + groups[1][2]
kitchen_items = groups[2][2] + groups[3][2]
recs_a, span_a, ow_a, raw_a, ha = render_combined(living_items, "overall_a", resx=3200, resy=900)
recs_b, span_b, ow_b, raw_b, hb = render_combined(kitchen_items, "overall_b", resx=3200, resy=900)
record(raw_a, recs_a, span_a, ow_a, "Living / bedroom  ·  1 m bar", os.path.join(TMP, "overall_a_ann.png"))
record(raw_b, recs_b, span_b, ow_b, "Kitchen / bathroom  ·  1 m bar", os.path.join(TMP, "overall_b_ann.png"))

meta_path = os.path.join(TMP, "meta.json")
with open(meta_path, "w") as f:
    json.dump({"meta": META, "overall": os.path.join(ASSETS, "kit_lineup.png")}, f, indent=2)
print("META_WRITTEN", meta_path, "n", len(META))
