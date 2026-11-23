"""Hero4 facade pass (exterior r8). Enabled with BHERO4=1; with it unset build_scene.py is unchanged.
Look: the approved web/hero3.glb archive look (dark warm-grey front c7bda8 from its palette, black metal
window frames 222325, BARCLAY HOUSE lettering at the entrance) brought into the procedural blend.
Fixes (critic R17-trial / round-6 list, refs: Geograph 8144686 real_geograph.jpg, Commons real_commons.jpg):
  1 ground-floor colour discontinuity: Portland base and faience upper share one tone (photos show one tone)
  2 ashlar: groove pitch 0.55 -> 0.80 m, staggered vertical joints, stone normal 0.6 -> 0.12
  3 arcade: deeper reveal (glass y -0.12 -> -0.05, cutter to -0.02; critic's '-0.40' had the sign flipped), voussoir radial 1.0 -> 1.2 m, projection -0.58 -> -0.64
  4 RB shields: layered cartouche + raised 'RB' monogram relief 0.08 m
  5 glazed strips: oriel bays floors 1-2 only (Commons photo), solid spandrel panel between storeys,
    instead of one 3-storey glass strip crossed by pale transom strips
  6 parapet: moulded coping + plinth band; 7 entrance: door leaves set back -0.22 -> -0.02 (critic #4 'deeper'; -y is outward)
EVERY size here that is not in build_scene.SOURCES is a STAND-IN (photo-read, not dimensioned)."""
import os, math
ON = os.environ.get("BHERO4") == "1"
# hero3.glb PaletteBaseColor entries (sRGB) -> linear
def _lin(h):
    c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
FRONT = _lin("c7bda8")      # hero3 palette #6: front stone/faience tone
FRONT_D = _lin("c5b79a")    # hero3 palette #10: cornice tone (slightly darker, used as block variation)
RENDER_K = 0.80   # Cycles-only: darken so AgX stills read like the viewer's hero3 (three.js) front; GLB export keeps palette values
FRAME = _lin("222325")      # hero3 palette #17: black metal frames / glazing bars
GLASS = _lin("272a30")      # hero3 palette #21
P = {   # defaults == build_scene.py values when BHERO4 is off
    "groove_pitch": 0.80 if ON else 0.55,
    "arch_cut_back": -0.02 if ON else -0.12,
    "arch_glass": -0.05 if ON else -0.12,
    "vous_ext": 1.2 if ON else 1.0, "vous_key": 1.45 if ON else 1.25,
    "vous_y0": -0.64 if ON else -0.58,
    "door_y": (-0.10, -0.02) if ON else (-0.30, -0.22),   # deeper set-back (critic #4 asked "deeper"; its -0.45 had the sign flipped: -y is outward)
    "oriel_floors12": ON,
}
def _nodes(m, t): return [n for n in m.node_tree.nodes if n.bl_idname == t]
def mats(M):
    """Recolour in place (same material names, so export_glb / viewer name rules still apply)."""
    if not ON: return M
    import bpy
    st = M["stone"]; nt = st.node_tree
    for mx in _nodes(st, "ShaderNodeMix"):
        if mx.blend_type == "MULTIPLY" and mx.inputs[7].default_value[0] > 0.5 and not mx.inputs[7].is_linked:
            mx.inputs[7].default_value = (*[min(1, c*1.6*RENDER_K) for c in FRONT], 1)
            # soften the photo texture: 35 % texture, 65 % flat front tone (smooth ashlar, critic hf target)
            out = mx.outputs[2]; dst = [l.to_socket for l in out.links]
            mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = "RGBA"; mm.blend_type = "MIX"; mm.inputs[0].default_value = 0.35
            mm.inputs[6].default_value = (*[c*RENDER_K for c in FRONT], 1); nt.links.new(out, mm.inputs[7])
            for s in dst: nt.links.new(mm.outputs[2], s)
    for nm in _nodes(st, "ShaderNodeNormalMap"): nm.inputs[0].default_value = 0.12
    b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"]
    fa = M["terracotta"]
    for br in _nodes(fa, "ShaderNodeTexBrick"):
        br.inputs["Color1"].default_value = (*[c*RENDER_K for c in FRONT], 1); br.inputs["Color2"].default_value = (*[c*RENDER_K for c in FRONT_D], 1)
        br.inputs["Mortar"].default_value = (*[c*0.72*RENDER_K for c in FRONT], 1)
    for bm in _nodes(fa, "ShaderNodeBump"): bm.inputs["Strength"].default_value = 0.15
    fb = fa.node_tree.nodes["Principled BSDF"]; fb.inputs["Coat Weight"].default_value = 0.35   # less glaze sheen: hero3 reads matte
    M["groove"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*[c*0.35 for c in FRONT], 1)
    fr = M["frame"]; fr.name = "Window_frame_dark"
    fb_ = fr.node_tree.nodes["Principled BSDF"]; fb_.inputs["Base Color"].default_value = (*FRAME, 1); fb_.inputs["Roughness"].default_value = 0.5; fb_.inputs["Metallic"].default_value = 0.6
    M["glass"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*GLASS, 1)
    M["letter"] = bpy.data.materials.new("Lettering_gilt"); lb = M["letter"].node_tree if M["letter"].use_nodes else None
    M["letter"].use_nodes = True; lb = M["letter"].node_tree.nodes["Principled BSDF"]
    lb.inputs["Base Color"].default_value = (0.78, 0.66, 0.42, 1); lb.inputs["Metallic"].default_value = 0.85; lb.inputs["Roughness"].default_value = 0.3   # STAND-IN finish
    M["sign"] = bpy.data.materials.new("Sign_panel_dark"); M["sign"].use_nodes = True
    sb = M["sign"].node_tree.nodes["Principled BSDF"]; sb.inputs["Base Color"].default_value = (*FRAME, 1); sb.inputs["Roughness"].default_value = 0.45
    return M

def _text(bpy, name, body, size, extrude, coll, parent, loc, m):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.extrude = extrude/2
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.space_character = 1.05
    tmp = bpy.data.objects.new(name+"_crv", cu); coll.objects.link(tmp)
    tmp.rotation_euler = (math.pi/2, 0, 0); tmp.location = loc; tmp.parent = parent
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    o = bpy.data.objects.new(name, me); o.data.materials.clear(); o.data.materials.append(m); coll.objects.link(o)
    o.parent = parent; o.matrix_parent_inverse = tmp.matrix_parent_inverse.copy(); o.rotation_euler = tmp.rotation_euler; o.location = loc
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    return o

def ornament(bpy, M, C, fr, W, L, ROOF, box, disc, ex, ew, TRIPLE, openings):
    """Extra geometry. Called inside build_scene.hero() before the booleans."""
    if not ON: return
    # (a) staggered vertical ashlar joints between the 0.80 m grooves. Block length 1.6 m: STAND-IN (photos, not dimensioned)
    z = 0.5; row = 0
    while z + P["groove_pitch"] < L[1]-0.5:
        zt = z + P["groove_pitch"]; off = 0.8 if row % 2 else 0.0; x = off + 1.6
        while x < W - 0.2:
            blocked = any(a_ - 0.05 < x < b_ + 0.05 and z < zt_ for a_, b_, zt_ in openings)
            if not blocked: box("HERO_ashlar_joint", x-0.015, x+0.015, -0.455, -0.449, z+0.035, zt-0.035, M["groove"], C, fr)
            x += 1.6
        z = zt; row += 1
    # (b) RB shields: layered cartouche frame behind + raised 'RB' monogram, relief 0.08 m (critic R17 #3, STAND-IN depth)
    for a_, b_ in TRIPLE:
        for xx in (a_*W+(-0.9 if a_ < 0.5 else 0), b_*W+(0.9 if a_ < 0.5 else 0)):
            if a_ < 0.5 and xx < a_*W: continue
            if a_ > 0.5 and xx > b_*W: continue
            for zz in (L[3]+0.3, L[4]-1.6):
                disc("HERO_RB_cartouche", xx, zz, 0.48, 0.58, -0.62, -0.40, M["terracotta"], 20)
                _text(bpy, "HERO_RB_monogram", "RB", 0.40, 0.08, C, fr, (xx, -0.78-0.04, zz-0.02), M["terracotta"])
    # (c) parapet: moulded coping + plinth band (heights STAND-IN; E05 shows a light parapet, not dimensioned)
    box("HERO_parapet_coping", -0.3, W+0.3, -0.52, 0.05, ROOF+0.25, ROOF+0.36, M["terracotta"], C, fr)
    box("HERO_parapet_plinth", -0.25, W+0.25, -0.47, 0.0, ROOF, ROOF+0.08, M["terracotta"], C, fr)
    # (d) BARCLAY HOUSE lettering: approved hero3 look + Commons photo (name plate over the doorway). Letter height 0.18 m: STAND-IN
    # on the porch frieze over the entrance (hero3 look; Commons photo shows the name over the doorway). Letter height 0.26 m: STAND-IN
    box("HERO_entrance_sign", ex-ew/2-0.2, ex+ew/2+0.2, -1.17, -1.15, L[1]-0.66, L[1]-0.28, M["sign"], C, fr)
    _text(bpy, "HERO_entrance_lettering", "BARCLAY HOUSE", 0.26, 0.02, C, fr, (ex, -1.17-0.01, L[1]-0.47), M["letter"])

def oriel(M, C, fr, W, L, box, glass, TRIPLE):
    """(e) oriel bays over floors 1-2 only (Commons photo: floor-3 triple window sits above the oriel head)."""
    if not P["oriel_floors12"]: return
    for a_, b_ in TRIPLE:
        xa, xb = a_*W-0.15, b_*W+0.15; z0_ = L[1]+0.15; zt_ = L[3]-0.35; d_ = -1.0   # depth 0.6 m STAND-IN (from R3)
        for xx in (xa, xb): box("HERO_oriel_cheek", xx-0.12, xx+0.12, d_, -0.40, z0_, zt_, M["terracotta"], C, fr)
        box("HERO_oriel_base", xa-0.15, xb+0.15, d_-0.1, -0.40, z0_-0.45, z0_, M["terracotta"], C, fr)
        box("HERO_oriel_head", xa-0.25, xb+0.25, d_-0.2, -0.40, zt_, zt_+0.45, M["terracotta"], C, fr)
        box("HERO_oriel_spandrel", xa+0.12, xb-0.12, d_, d_+0.2, L[2]-0.55, L[2]+0.35, M["terracotta"], C, fr)
        n = 3   # 3 lights per storey, mullions between (Commons photo)
        for k in range(1, n):
            xm = xa+0.12+(xb-xa-0.24)*k/n; box("HERO_oriel_cheek", xm-0.09, xm+0.09, d_, d_+0.12, z0_, zt_, M["terracotta"], C, fr)
        glass(xa+0.12, xb-0.12, z0_, L[2]-0.55, depth=d_+0.08, panes=(6, 3))
        glass(xa+0.12, xb-0.12, L[2]+0.35, zt_, depth=d_+0.08, panes=(6, 3))
