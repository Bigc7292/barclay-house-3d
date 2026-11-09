"""x_tricks #10 web data: VISIBLE Canal_water triangles (open sky above, ray-cast in the Blender scene) -> web/src/canal.json in viewer (glTF Y-up)
coordinates, using out/viewer_assets.json origin offset. Water basins under the EA DTM terrain mesh are skipped (not visible).
  blender -b -y out/barclay_scene.blend -P canal_web.py      (read-only on the .blend; writes only web/src/canal.json)"""
import bpy, json, os
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); off = json.load(open(os.path.join(HERE, "out", "viewer_assets.json")))["origin_blender_world_offset_m"]
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get(); out = []; skipped = 0
for o in [o for o in sc.objects if o.type == "MESH" and o.name.startswith("canal_")]:
    me = o.data; me.calc_loop_triangles(); V = [o.matrix_world @ v.co for v in me.vertices]; v, idx, k = [], [], {}
    for t in me.loop_triangles:
        P = [V[i] for i in t.vertices]; c = sum(P, Vector()) / 3
        if (o.matrix_world.to_3x3() @ t.normal).z < 0.5: continue                     # prism sides / bottom
        if sc.ray_cast(dg, c + Vector((0, 0, 0.05)), Vector((0, 0, 1)))[0]: skipped += 1; continue   # covered (terrain, bridge, building)
        for i in t.vertices:
            if i not in k: k[i] = len(v) // 3; p = V[i]; v += [round(p.x - off[0], 2), round(p.z + 0.03, 2), round(-(p.y - off[1]), 2)]
            idx.append(k[i])
    if idx: out.append({"name": o.name, "v": v, "i": idx})
p = os.path.join(HERE, "web", "src", "canal.json"); json.dump(out, open(p, "w"), separators=(",", ":"))
print("CANAL_WEB", len(out), "objects,", sum(len(x["i"]) // 3 for x in out), "visible tris,", skipped, "covered tris skipped,", os.path.getsize(p), "bytes")
