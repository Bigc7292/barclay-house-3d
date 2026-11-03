import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/workspace/barclay/web/src/sur_src.glb")
M=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:-len(o.data.vertices))
P=[M[i::4] for i in range(4)]
for name,grp in zip("abcd",P):
    bpy.ops.object.select_all(action='DESELECT')
    for o in grp:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f"/workspace/barclay/web/src/sur_{name}.glb",export_format='GLB',use_selection=True,export_image_format='JPEG')
