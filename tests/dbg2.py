import bpy
sc=bpy.context.scene; sc.camera=bpy.data.objects['Cam_Street']; r=sc.render; r.resolution_percentage=15; sc.cycles.samples=8
print("DBG world",sc.world.name, [n.name for n in sc.world.node_tree.nodes], "view",sc.view_settings.view_transform, sc.view_settings.look, "film",r.film_transparent, "layers",[ (v.name,v.use) for v in sc.view_layers], "compositor",sc.use_nodes)
r.filepath='/workspace/barclay/tests/dbg_street.png'; bpy.ops.render.render(write_still=True)
