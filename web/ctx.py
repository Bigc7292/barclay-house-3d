import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/workspace/barclay/web/src/sur_src.glb")
t=bpy.data.objects['Terrain_EA_DTM']; d=t.modifiers.new('d','DECIMATE'); d.ratio=0.12
bpy.context.view_layer.objects.active=t; bpy.ops.object.modifier_apply(modifier='d'); print("terrain",len(t.data.vertices))
bpy.ops.export_scene.gltf(filepath="/workspace/barclay/web/src/sur_dec.glb",export_format='GLB',export_image_format='JPEG')
