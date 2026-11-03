import bpy
fr=bpy.data.objects["HERO_front_frame"]; b=bpy.data.objects["HERO_body"]; inv=fr.matrix_world.inverted()
vs=sorted({(round(v.x,2),round(v.y,2)) for v in [inv@(b.matrix_world@x.co) for x in b.data.vertices]})
print("FOOT",vs); print("FRAME",tuple(fr.location),fr.rotation_euler.z)
for c in [o for o in bpy.data.objects if o.type=='CAMERA']: print("CAM",c.name,tuple(round(x,2) for x in c.location),c.data.lens,c.data.sensor_width)
r=bpy.context.scene.render; print("RES",r.resolution_x,r.resolution_y)
