# Surroundings-detail export (derived from export_glb.py). blender -b -y tests/surr/scene_surr.blend -P export_surroundings_detail.py -> out/barclay_surroundings_detail.glb (temp+mv). Hero NOT exported.
import bpy, bmesh, os, json, math, mathutils
HERE = "/workspace/barclay"; TX = HERE + "/textures/export/"; OUT = HERE + "/out/"
sc = bpy.context.scene
# 1. remove cutters, apply modifiers on everything (booleans/solidify/displace)
dg = bpy.context.evaluated_depsgraph_get()
for o in [o for o in sc.objects if o.type == "MESH" and o.modifiers]:
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); o.modifiers.clear(); o.data = me
for o in list(bpy.data.objects):
    if any(c.name.startswith("HERO_cutters") for c in o.users_collection) or o.name.startswith("cut"):
        bpy.data.objects.remove(o)
# 2. origin = hero base centre at street level
hero = [o for o in sc.objects if any(c.name == "Hero" for c in o.users_collection)]
pts = [o.matrix_world @ mathutils.Vector(v) for o in hero if o.type == "MESH" for v in o.bound_box]
cx = (min(p.x for p in pts)+max(p.x for p in pts))/2; cy = (min(p.y for p in pts)+max(p.y for p in pts))/2
off = mathutils.Vector((cx, cy, 0))
for o in sc.objects:
    if o.parent is None: o.location -= off
bpy.context.view_layer.update()
# 3. export materials (UV box-mapped image textures; glTF-compatible)
def emat(name, key, scale, rough=0.7, rgb=None, metal=0.0, emis=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if key:
        for suf, sock, col in (("diff", "Base Color", True), ("rough", "Roughness", False), ("nor", None, False)):
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(TX + f"{key}_{suf}.jpg", check_existing=True)
            if not col: t.image.colorspace_settings.name = "Non-Color"
            if sock: nt.links.new(t.outputs[0], b.inputs[sock])
            else:
                nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(t.outputs[0], nm.inputs[1]); nt.links.new(nm.outputs[0], b.inputs["Normal"])
    elif rgb: b.inputs["Base Color"].default_value = (*rgb, 1)
    m["uv_scale"] = scale; return m
def glazed(m):   # PBR finish preset (x-bookmarks pbr-finish-presets, "polished/glazed": clearcoat 1, clearcoatRoughness 0.05) -> KHR_materials_clearcoat
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15; return m  # R4 cap per x_tricks #3
def glassmat():
    m = emat("Glass_dark", None, 1, 0.03, (0.02,0.025,0.03), 0.0); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Alpha"].default_value = 0.85; m.blend_method = "BLEND"; m.use_backface_culling = False; return m
H = {"Portland_stone_base": emat("Portland_stone", None, 1, 0.75, (0.58,0.52,0.40)), "White_glazed_faience_Burmantofts": glazed(emat("Burmantofts_white_glazed_faience", None, 1, 0.25, (0.55,0.47,0.33))),
     "Concrete_block_sides_rear": emat("Concrete_block", "blocks", 3.0), "Concrete_block_base_sides_rear": emat("Concrete_block", "blocks", 3.0),
     "Glass": glassmat(), "Window_frame_dark": emat("Window_frame_white_painted", None, 1, 0.5, (0.78,0.78,0.75)), "Door_dark": emat("Door_dark", None, 1, 0.4, (0.03,0.03,0.03)),
     "Roof": emat("Roof", None, 1, 0.8, (0.13,0.13,0.14)), "Rustication_channel_shadow": emat("Rustication_channel", None, 1, 0.9, (0.12,0.12,0.12))}
S = {"Neighbour_generic": emat("Neighbour", "n_bldg", 4.0), "Asphalt": emat("Asphalt", "n_asphalt", 4.0), "Paving": emat("Paving", "n_paving", 2.0),
     "Ground_paving": emat("Ground", "n_paving", 3.0), "Ballast": emat("Ballast", "n_ballast", 2.0), "Viaduct_brick": emat("Viaduct_red_brick", None, 1, 0.85, (0.24,0.075,0.045)),
     "Roof": emat("Roof_s", None, 1, 0.85, (0.13,0.13,0.14)), "Roof_grey_membrane": emat("Roof_grey_membrane", None, 1, 0.8, (0.22,0.22,0.23)), "Roof_dark_slate": emat("Roof_dark_slate", None, 1, 0.7, (0.07,0.075,0.085)), "Canal_water": emat("Canal_water", None, 1, 0.05, (0.03,0.05,0.05)), "Rail_steel": emat("Rail_steel", None, 1, 0.3, (0.3,0.3,0.3), 1.0),
     "Tree_leaves": emat("Leaves", None, 1, 0.8, (0.12,0.22,0.08)), "Bark": emat("Bark", None, 1, 0.9, (0.2,0.15,0.1)),
     "Lamp_post": emat("Lamp_post", None, 1, 0.4, (0.05,0.05,0.05), 0.8), "Lamp_head": emat("Lamp_head", None, 1, 0.3, (0.9,0.9,0.85)),
     "Neighbour_red_brick": emat("Neighbour_red_brick", None, 1, 0.85, (0.45,0.2,0.14)), "Neighbour_render_cream": emat("Neighbour_render_cream", None, 1, 0.8, (0.8,0.76,0.66)),
     "Neighbour_grey_cladding": emat("Neighbour_grey_cladding", None, 1, 0.6, (0.35,0.36,0.38)), "Neighbour_glass_curtain": emat("Neighbour_glass_curtain", None, 1, 0.05, (0.05,0.07,0.09), 0.6),
     "Kerb": emat("Kerb", None, 1, 0.8, (0.55,0.55,0.53)), "Road_marking": emat("Road_marking", None, 1, 0.6, (0.85,0.85,0.8))}
S.update({"S_red_brick": emat("S_red_brick", "s_brick", 2.0), "S_viaduct_brick": emat("S_viaduct_brick", "s_brick", 2.0),
  "S_render_white": emat("S_render_white", "s_plaster", 3.0), "S_cladding_grey": emat("S_cladding_grey", None, 1, 0.6, (0.42,0.43,0.45)),
  "S_cladding_cream": emat("S_cladding_cream", None, 1, 0.6, (0.80,0.77,0.70)), "S_concrete_sleeper": emat("S_concrete_sleeper", "s_concrete", 1.0),
  "S_sandstone_dressing": emat("S_sandstone_dressing", None, 1, 0.8, (0.55,0.45,0.33)), "S_window_glass": emat("S_window_glass", None, 1, 0.05, (0.015,0.02,0.025)),
  "S_shop_glass": emat("S_shop_glass", None, 1, 0.05, (0.03,0.035,0.04)), "S_leaves": emat("S_leaves", None, 1, 0.75, (0.10,0.20,0.06)), "S_leaves_b": emat("S_leaves_b", None, 1, 0.75, (0.14,0.24,0.08)),
  "S_lantern": emat("S_lantern", None, 1, 0.3, (0.9,0.9,0.85)), "S_sign_panel": emat("S_sign_panel", None, 1, 0.4, (0.75,0.72,0.65))})
def remap(o, table):
    for i, s in enumerate(o.material_slots):
        base = s.material.name.split(".")[0] if s.material else ""
        if base in table: o.material_slots[i].material = table[base]
    bm = bmesh.new(); bm.from_mesh(o.data); uv = bm.loops.layers.uv.verify(); mw = o.matrix_world
    for f in bm.faces:
        sc_ = 1.0
        if f.material_index < len(o.material_slots) and o.material_slots[f.material_index].material:
            sc_ = o.material_slots[f.material_index].material.get("uv_scale", 1.0)
        n = (mw.to_3x3() @ f.normal); ax = max(range(3), key=lambda k: abs(n[k]))
        for l in f.loops:
            p = mw @ l.vert.co; a, b = [(p.y, p.z), (p.x, p.z), (p.x, p.y)][ax]; l[uv].uv = (a/sc_, b/sc_)
    bm.to_mesh(o.data); bm.free()
heroset = set(hero); kids = lambda o: [o] + [k for c in o.children for k in kids(c)]
for o in list(heroset):
    for k in kids(o): heroset.add(k)
surr = [o for o in sc.objects if o not in heroset and o.type == "MESH"]
for o in heroset:
    if o.type == "MESH": remap(o, H)
for o in surr: remap(o, S)
def bbox(objs):
    P = [o.matrix_world @ mathutils.Vector(v) for o in objs if o.type == "MESH" for v in o.bound_box]
    mn = [min(p[i] for p in P) for i in range(3)]; mx = [max(p[i] for p in P) for i in range(3)]
    g = lambda v: [round(v[0], 2), round(v[2], 2), round(-v[1], 2)]   # Blender Z-up -> glTF Y-up
    lo, hi = g(mn), g(mx); return {"min": [min(lo[i], hi[i]) for i in range(3)], "max": [max(lo[i], hi[i]) for i in range(3)]}
def export(objs, path, maxsize):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    tmp = path + ".tmp.glb"
    bpy.ops.export_scene.gltf(filepath=tmp, use_selection=True, export_format="GLB", export_yup=True, export_apply=True,
        export_image_format="JPEG", export_jpeg_quality=85, export_cameras=False, export_lights=False, export_materials="EXPORT")
    os.replace(tmp, path)
export(surr, OUT + "barclay_surroundings_detail.glb", 512)
print("EXPORT DONE")
