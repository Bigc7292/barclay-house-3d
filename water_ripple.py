"""x_tricks #10 Blender path (Water Pro is paid -> not used): Noise texture -> Bump (strength 0.05) on the Canal_water material.
Idempotent: flags the material "surr_ripple" (same flag build_surroundings.py canal() checks), so it is never applied twice.
Noise scale/detail are STAND-INS (look only; no water fact is sourced)."""
def ripple(m, strength=0.05, scale=3.0, detail=6.0):
    if not (m and m.use_nodes) or m.get("surr_ripple"): return False
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.name = "CANAL_RIPPLE_NOISE"
    nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    bm = nt.nodes.new("ShaderNodeBump"); bm.name = "CANAL_RIPPLE_BUMP"; bm.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"]); m["surr_ripple"] = 1; return True

def cut_terrain(terrain, waters, depth=3.0):
    """Found in the #10 test: the EA DTM terrain mesh lies ABOVE every Canal_water surface near the hero (ribbons sit 1 m under it,
    basins 0.4 m under the lowest bank), so the canal was invisible in renders and the viewer. Delete terrain faces that have canal
    water within `depth` m straight below their centre. Geometry-only, no invented heights (water levels stay as build_scene.py sets)."""
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    V, F = [], []
    for w in waters:
        mw = w.matrix_world; b = len(V); V += [mw @ v.co for v in w.data.vertices]; F += [[b + i for i in p.vertices] for p in w.data.polygons]
    if not F: return 0
    T = BVHTree.FromPolygons(V, F); mw = terrain.matrix_world; bm = bmesh.new(); bm.from_mesh(terrain.data); down = Vector((0, 0, -1))
    kill = [f for f in bm.faces if T.ray_cast(mw @ f.calc_center_median() - Vector((0, 0, 0.01)), down, depth)[0] is not None]
    bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(terrain.data); bm.free(); terrain.data.update(); terrain["canal_cut_faces"] = len(kill)
    return len(kill)
