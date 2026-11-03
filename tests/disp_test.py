# Trick #8 test (BDISP): true displacement via Cycles adaptive subdivision on hero facade slabs (faience brick Fac, stone noise). Copy only.
import bpy, os, time, resource, sys
sc = bpy.context.scene; disp = os.environ.get("BDISP") == "1"
if disp:
    sc.cycles.feature_set = "EXPERIMENTAL"
    for mn, scale in (("White_glazed_faience_Burmantofts", 0.01), ("Portland_stone_base", 0.02)):
        m = bpy.data.materials[mn]; nt = m.node_tree; out = nt.nodes["Material Output"]; m.cycles.displacement_method = "BOTH"
        src = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeTexBrick"), None)
        if src is None: src = nt.nodes.new("ShaderNodeTexNoise"); src.inputs["Scale"].default_value = 8; so = src.outputs["Fac"]
        else: so = src.outputs["Fac"]
        d = nt.nodes.new("ShaderNodeDisplacement"); d.inputs["Scale"].default_value = scale; nt.links.new(so, d.inputs["Height"]); nt.links.new(d.outputs[0], out.inputs["Displacement"])
    for n in ("HERO_front_terracotta", "HERO_front_stone_base"):
        o = bpy.data.objects[n]; md = o.modifiers.new("adaptive", "SUBSURF"); md.subdivision_type = "SIMPLE"; o.cycles.use_adaptive_subdivision = True
    sc.cycles.dicing_rate = 1.0
W, H = [int(x) for x in os.environ.get("BRES", "960x540").split("x")]
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.cycles.samples = int(os.environ.get("BSAMPLES", "32")); sc.camera = bpy.data.objects["Cam_Street"]
sc.render.filepath = f"/workspace/barclay/tests/disp_{'on' if disp else 'off'}_{W}x{H}.png"
t = time.time(); bpy.ops.render.render(write_still=True)
print(f"DISPTEST disp={disp} res={W}x{H} time={time.time()-t:.1f}s maxrss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f}MB")
