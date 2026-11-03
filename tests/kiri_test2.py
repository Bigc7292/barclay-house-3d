import bpy, addon_utils
addon_utils.enable("bl_ext.user_default.dgs_render_by_kiri_engine", default_set=True)
n0=set(bpy.data.objects.keys())
r=bpy.ops.sna.import_ply_as_splats_8458e(filepath="/workspace/barclay/tests/sfm/splat_test.ply")
new=[bpy.data.objects[k] for k in set(bpy.data.objects.keys())-n0]
print("KIRI import",r,[(o.name,o.type,len(o.data.vertices) if o.type=='MESH' else '',[m.type for m in o.modifiers]) for o in new])
for o in new: print("KIRI attrs",[a.name for a in o.data.attributes][:12])
fr=bpy.data.objects["HERO_front_frame"]
for o in new: o.location=fr.matrix_world@__import__('mathutils').Vector((-5,-25,0))
bpy.ops.wm.save_as_mainfile(filepath="/workspace/barclay/tests/scene_copy_splat_chain.blend", copy=True)
