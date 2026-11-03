import bpy, addon_utils, sys
addon_utils.enable("BlenderGIS", default_set=True)
from BlenderGIS.geoscene import GeoScene
import json
p=bpy.context.preferences.addons["BlenderGIS"].preferences
d=json.loads(p.predefCrsJson); d.append(["EPSG:27700","British National Grid","OSGB36"]); p.predefCrsJson=json.dumps(d)
sc=bpy.context.scene; geo=GeoScene(sc)
geo.crs='EPSG:27700'; geo.setOriginPrj(383889.38,397518.84)
print("GEOREF",geo.isGeoref, geo.crs, geo.getOriginPrj())
n0=len(bpy.data.objects)
r=bpy.ops.importgis.georaster(filepath="/workspace/barclay/tests/dtm_bng.tif", importMode="DEM", subdivision="subsurf", fillNodata=True, rastCRS="EPSG:27700")
print("IMPORT",r)
new=[o for o in bpy.data.objects][n0:] or [bpy.context.active_object]
o=bpy.context.active_object
import mathutils
bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
print("DEM_OBJ",o.name,len(o.data.vertices),[m.type for m in o.modifiers],"x",min(v.x for v in bb),max(v.x for v in bb),"y",min(v.y for v in bb),max(v.y for v in bb),"z",min(v.z for v in bb),max(v.z for v in bb))
bpy.ops.wm.save_as_mainfile(filepath="/workspace/barclay/tests/scene_copy_gis.blend")
