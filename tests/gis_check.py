import bpy
o=bpy.data.objects["dtm_bng"]; print("LOC",tuple(o.location),"VERTS",[tuple(round(c,1) for c in v.co) for v in o.data.vertices])
d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
zs=[v.co.z for v in d.vertices]; print("EVAL n",len(zs),"z",min(zs),max(zs))
import mathutils
# z at hero origin vs street
best=min(d.vertices,key=lambda v:(v.co.x)**2+(v.co.y)**2); print("Z_AT_HERO",best.co[:])
