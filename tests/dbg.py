import bpy
sc=bpy.context.scene
print("DBG engine",sc.render.engine,"time",getattr(sc,'barclay_time',None),"cam",sc.camera.name,"exp",sc.view_settings.exposure,"sun",bpy.data.objects['Sun'].data.energy, bpy.data.objects['Sun'].rotation_euler[:])
c=bpy.data.objects['Cam_Match']; import mathutils
dg=bpy.context.evaluated_depsgraph_get()
hit=sc.ray_cast(dg,c.location,c.matrix_world.to_3x3()@mathutils.Vector((0,0,-1)))
print("DBG ray",hit[0],hit[4].name if hit[4] else None, (hit[1]-c.location).length if hit[0] else None)
for d in [(0,0,1),(0,0,-1),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]:
  h=sc.ray_cast(dg,c.location,mathutils.Vector(d)); print("DBG",d,h[4].name if h[4] else None,round((h[1]-c.location).length,2) if h[0] else None)
