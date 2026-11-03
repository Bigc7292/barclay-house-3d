import bpy, addon_utils, mathutils
addon_utils.enable("bl_ext.user_default.dgs_render_by_kiri_engine", default_set=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.sna.import_ply_as_splats_8458e(filepath="/workspace/barclay/tests/synthetic_splat.ply")
sc=bpy.context.scene; c=bpy.data.objects.new("C",bpy.data.cameras.new("C")); sc.collection.objects.link(c); sc.camera=c
c.location=(10,-30,6); c.rotation_euler=(mathutils.Vector((10,0,6))-c.location).to_track_quat("-Z","Y").to_euler()
sc.render.engine="BLENDER_EEVEE_NEXT"; sc.render.resolution_x,sc.render.resolution_y=320,180; sc.render.filepath="/workspace/barclay/tests/kiri_splat_eevee.png"
bpy.ops.render.render(write_still=True); print("KIRI_RENDER done")
