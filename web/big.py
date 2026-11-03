import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/workspace/barclay/web/src/sur_src.glb")
M=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:-len(o.data.vertices))
for o in M[:5]: print(o.name,len(o.data.vertices),[m.name for m in o.data.materials])
