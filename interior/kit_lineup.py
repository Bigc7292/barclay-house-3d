#!/usr/bin/env python3
"""Render the CC0 furniture kit in a row with a 1 m scale bar -> interior/assets/kit_lineup.png"""
import math, os, sys
import bpy
from mathutils import Vector
import furniture_cc0 as furn

ROOT = furn.ROOT
OUT = os.path.join(furn.ASSETS, "kit_lineup.png")
os.makedirs(furn.ASSETS, exist_ok=True)

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

# Shared 6-material palette (plus a few fittings) — same names the placer remaps to.
mats = {
    "NAVY": mat("Navy_velvet", (0.08, 0.10, 0.18), 0.75),
    "BOUC": mat("Cream_boucle", (0.86, 0.82, 0.74), 0.95),
    "OAKF": mat("Oak_furniture", (0.62, 0.42, 0.24), 0.5),
    "WUNIT": mat("Kitchen_handleless_white", (0.9, 0.89, 0.86), 0.3),
    "BLK": mat("Appliance_black_gloss", (0.015, 0.015, 0.017), 0.12),
    "WHITEP": mat("Sanitary_white", (0.95, 0.95, 0.95), 0.08),
    "CHROME": mat("Chrome", (0.9, 0.9, 0.9), 0.05, 1),
    "BMET": mat("Black_metal", (0.02, 0.02, 0.02), 0.35, 1),
    "STEEL": mat("Stainless_steel", (0.8, 0.8, 0.8), 0.22, 1),
    "GLASS": mat("Glass_clear", (0.95, 0.97, 0.97), 0.02),
    "LIN": mat("Bedding_white", (0.93, 0.93, 0.91), 0.9),
    "GREYV": mat("Vanity_grey", (0.45, 0.45, 0.46), 0.4),
    "LAMPS": mat("Lamp_shade_opal", (1, 0.97, 0.92), 0.3),
}
mats["GLASS"].node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0

furn._prepare_prototypes(mats)

# Floor
me = bpy.data.meshes.new("kit_floor")
import bmesh
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
bmesh.ops.scale(bm, vec=(24, 6, 0.02), verts=bm.verts)
bm.to_mesh(me); bm.free()
floor = bpy.data.objects.new("kit_floor", me)
sc.collection.objects.link(floor)
floor.location = (8, 0.5, -0.01)
fm = mat("Floor_light", (0.72, 0.68, 0.62), 0.7)
floor.data.materials.append(fm)

# Place items in a row, facing -Y, sitting on z=0
x = 0.0
gap = 0.45
placed = []
for key, label in furn.iter_kit_items():
    root = furn._PROTO[key]
    dims = list(root.get("cc0_final_dims", [1, 1, 1]))
    w, d, h = dims
    x += w / 2
    inst = furn.instance(key, f"kit_{key}", (x, 0, 0), 0.0)
    placed.append((x, w, d, h, label))
    x += w / 2 + gap

# 1 m bar in front of the row, under the camera, left-aligned near the middle for a readable scale
span = max(x, 1.0)
bar_origin = (span / 2 - 0.5, -1.35, 0.0)
furn.make_scale_bar(bar_origin, mats=mats, sc=sc)

# Orthographic camera so the 1 m bar is true-scale and the whole lineup fits
cam_x = span / 2
cam_y = -8.0
cam_z = 1.15
bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
cam = bpy.context.object
target = Vector((cam_x, 0.0, 0.7))
cam.rotation_euler = (target - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
cam.data.ortho_scale = span + 2.0
sc.camera = cam

# Lights
bpy.ops.object.light_add(type="AREA", location=(cam_x, cam_y + 1.0, 4.0))
key = bpy.context.object
key.data.energy = 600
key.data.size = 6
key.data.color = (1, 0.97, 0.92)
bpy.ops.object.light_add(type="AREA", location=(cam_x + 4, 2.0, 3.0))
fill = bpy.context.object
fill.data.energy = 200
fill.data.size = 4
fill.data.color = (0.85, 0.9, 1)

# World
world = bpy.data.worlds.new("kit_world")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.22, 0.23, 0.25, 1)
bg.inputs[1].default_value = 0.6

# Render
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in sc.render.bl_rna.properties["engine"].enum_items.keys() else "CYCLES"
if sc.render.engine == "CYCLES":
    sc.cycles.samples = 32
    sc.cycles.use_denoising = True
sc.render.resolution_x = 2400
sc.render.resolution_y = 800
sc.render.film_transparent = False
sc.render.filepath = OUT
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("LINEUP_WRITTEN", OUT, "span_m", round(span, 2), "n", len(placed))
for rec in placed:
    print("ITEM", rec)
