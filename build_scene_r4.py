"""Barclay House exterior scene. Blender 4.x, free/open-source only.
Run:  blender -b -P build_scene.py -- [--render] [--noexport]
Env:  BRES=4096x2304  BSAMPLES=256  BCAMS=street,aerial,viaduct
Inputs (same folder): scene_data.json (prep.py: OSM (c) OpenStreetMap contributors ODbL +
EA LIDAR Composite 1m DSM/DTM, OGL), textures/* (Poly Haven CC0), hdri.exr (Poly Haven CC0).
Every hero number below is SOURCED; see SOURCES. Values with no source are marked NOT_FOUND
and only drive set dressing, never the hero massing."""
import bpy, json, math, os, sys, mathutils
HERE = os.path.dirname(os.path.abspath(__file__))
# ---------------- HERO PARAMETERS (all sourced) ----------------
SOURCES = {
 "E05": "Howard & Seddon dwg 12,982 E05 rev C 'Existing Front Elevation' https://docs.planning.org.uk/20210803/27/QKTOMYBCKT600/goza3b6sv2a2q83u.pdf",
 "DAS": "Howard & Seddon Design & Access Statement https://docs.planning.org.uk/20210803/27/QKTOMYBCKT600/s4c5tvdfq0syslhg.pdf",
 "LIDAR": "EA LIDAR Composite 1m FZ DSM / DTM (OGL) https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178",
 "OSM": "https://www.openstreetmap.org/way/100646649",
 "MVA": "https://www.manchestervictorianarchitects.org.uk/buildings/barclays-warehouse-barclay-house-whitworth-street-west",
}
HERO_ID = "100646649"                     # OSM footprint (front edge 37.54 m; E05 scaled 37.4 m)
GF_ABOVE_STREET = 102.20 - 100.10         # DAS: street 100.10 m, main lobby 102.20 m
STOREY_H = [3.663, 3.925, 3.290, 3.323, 3.480]  # E05 dims: GF-1st, 1st-2nd, 2nd-3rd, 3rd-4th, 4th-roof
PAVILION = 0.108                          # end pavilions, fraction of width (scaled E05 1:250, +/-0.3 m)
ARCH_CENTRES = [0.175, 0.274, 0.375, 0.627, 0.725, 0.828]  # 6 round-headed GF arches (E05)
ARCH_W = 2.5                              # m, scaled E05
ENTRANCE = (0.5, 2.6)                     # centre fraction, width m (scaled E05)
UPPER_BAYS = 15                           # E05: 15 bays between pavilions, floors 1-4
ROOF_TOWER = (0.32, 0.467, 4.15)          # stair/lift tower start/end fraction, height m (scaled E05)
ROOF_EXTENSION = False                    # 2-storey mansard (app 128804/FO/2020): built status NOT_FOUND
VIADUCT_SPAN = 9.0; VIADUCT_W = 9.0; PIER_W = 1.6   # NOT_FOUND: set dressing only; deck height from LIDAR
RES = tuple(int(v) for v in os.environ.get("BRES", "4096x2304").split("x"))
SAMPLES = int(os.environ.get("BSAMPLES", 256))
# ---------------------------------------------------------------
D = json.load(open(os.path.join(HERE, "scene_data.json")))
LEVELS = [GF_ABOVE_STREET + sum(STOREY_H[:i]) for i in range(len(STOREY_H)+1)]  # GF..roof above street
ROOF = LEVELS[-1]
DT = D["dtm"]
def ground(x, y):
    c = (x - DT["e0"]) / DT["step"]; r = (DT["n0"] - y) / DT["step"]
    ci, ri = int(max(0, min(DT["cols"]-2, c))), int(max(0, min(DT["rows"]-2, r)))
    fc, fr = max(0, min(1, c-ci)), max(0, min(1, r-ri)); z = DT["z"]; C = DT["cols"]
    a = z[ri*C+ci]*(1-fc)+z[ri*C+ci+1]*fc; b = z[(ri+1)*C+ci]*(1-fc)+z[(ri+1)*C+ci+1]*fc
    return a*(1-fr)+b*fr
def pbr(name, folder=None, rgb=(0.6,0.6,0.6), rough=0.7, scale=2.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    p = os.path.join(HERE, "textures", folder or "")
    if folder and os.path.isdir(p):
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1/scale,)*3; nt.links.new(tc.outputs["Object"], mp.inputs[0])
        def img(f, col):
            fp = os.path.join(p, f)
            if not os.path.exists(fp): return None
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fp, check_existing=True); t.projection = "BOX"; t.projection_blend = 0.2
            if not col: t.image.colorspace_settings.name = "Non-Color"
            nt.links.new(mp.outputs[0], t.inputs[0]); return t
        d = img("diff.jpg", True)
        if d:
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs[0].default_value = 1.0
            mix.inputs[7].default_value = (*[min(1, c*1.6) for c in rgb], 1)
            nt.links.new(d.outputs[0], mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        r = img("rough.jpg", False)
        if r: nt.links.new(r.outputs[0], b.inputs["Roughness"])
        n = img("nor.jpg", False)
        if n:
            nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = 0.6
            nt.links.new(n.outputs[0], nm.inputs[1]); nt.links.new(nm.outputs[0], b.inputs["Normal"])
    return m
def glow(m, strength, thresh):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; v = nt.nodes.new("ShaderNodeValue"); v.name = "GLOW"; v.outputs[0].default_value = 0
    oi = nt.nodes.new("ShaderNodeObjectInfo"); gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = thresh
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu2 = nt.nodes.new("ShaderNodeMath"); mu2.operation = "MULTIPLY"; mu2.inputs[1].default_value = strength
    nt.links.new(oi.outputs["Random"], gt.inputs[0])
    vr = nt.nodes.new("ShaderNodeMapRange"); vr.inputs[3].default_value = 0.25; vr.inputs[4].default_value = 1.2; nt.links.new(oi.outputs["Random"], vr.inputs[0])
    gv = nt.nodes.new("ShaderNodeMath"); gv.operation = "MULTIPLY"; nt.links.new(gt.outputs[0], gv.inputs[0]); nt.links.new(vr.outputs[0], gv.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (1.0, 0.55, 0.25, 1); ramp.color_ramp.elements[1].color = (1.0, 0.85, 0.65, 1)
    nt.links.new(oi.outputs["Random"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], nt.nodes["Principled BSDF"].inputs["Emission Color"])
    nt.links.new(gv.outputs[0], mu.inputs[0]); nt.links.new(v.outputs[0], mu.inputs[1]); nt.links.new(mu.outputs[0], mu2.inputs[0])
    nt.links.new(mu2.outputs[0], b.inputs["Emission Strength"]); return m
def neighbour_windows(m):
    # night-only lit window grid on neighbours (procedural pattern, not real window positions)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; v = nt.nodes.new("ShaderNodeValue"); v.name = "GLOW"; v.outputs[0].default_value = 0
    tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"; nt.links.new(sx.outputs[0], ad.inputs[0]); nt.links.new(sx.outputs[1], ad.inputs[1])
    cb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ad.outputs[0], cb.inputs[0]); nt.links.new(sx.outputs[2], cb.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0; br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.6
    br.inputs["Brick Width"].default_value = 2.5; br.inputs["Row Height"].default_value = 3.2; br.inputs["Color1"].default_value = (1,1,1,1); br.inputs["Color2"].default_value = (0,0,0,1)
    nt.links.new(cb.outputs[0], br.inputs["Vector"])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1; nt.links.new(br.outputs["Fac"], inv.inputs[1])
    gm = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(br.outputs["Color"], gm.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.55; nt.links.new(gm.outputs[0], gt.inputs[0])
    nz = nt.nodes.new("ShaderNodeNewGeometry"); sn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(nz.outputs["Normal"], sn.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(sn.outputs[2], ab.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.3; nt.links.new(ab.outputs[0], lt.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; nt.links.new(inv.outputs[0], m1.inputs[0]); nt.links.new(gt.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(lt.outputs[0], m2.inputs[1])
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(v.outputs[0], m3.inputs[1])
    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"; m4.inputs[1].default_value = 1.5; nt.links.new(m3.outputs[0], m4.inputs[0])
    b.inputs["Emission Color"].default_value = (1.0, 0.7, 0.4, 1); nt.links.new(m4.outputs[0], b.inputs["Emission Strength"]); return m
def weather(m, dirt=0.35, streak=0.25, band=1.2):
    """Grime: darker base band (z<band m), vertical soot streaks (stretched noise). Visual stand-in."""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.5, 1.5, 0.08)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs[0], nz.inputs["Vector"]); cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.45; cr.color_ramp.elements[1].position = 0.75
    cr.color_ramp.elements[0].color = (1,1,1,1); cr.color_ramp.elements[1].color = (1-streak, 1-streak, 1-streak, 1); nt.links.new(nz.outputs["Fac"], cr.inputs[0])
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = band; mr.inputs[3].default_value = 1-dirt; mr.inputs[4].default_value = 1.0
    nt.links.new(sx.outputs[2], mr.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 1
    if src: nt.links.new(src, m1.inputs[6])
    else: m1.inputs[6].default_value = b.inputs["Base Color"].default_value[:]
    nt.links.new(cr.outputs[0], m1.inputs[7])
    m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[0].default_value = 1
    nt.links.new(m1.outputs[2], m2.inputs[6]); cm = nt.nodes.new("ShaderNodeCombineColor"); [nt.links.new(mr.outputs[0], cm.inputs[i]) for i in range(3)]
    nt.links.new(cm.outputs[0], m2.inputs[7]); nt.links.new(m2.outputs[2], b.inputs["Base Color"]); return m
def faience():
    """Large ashlar-style glazed faience blocks (block size visual, from elevation coursing), fine joints, coat sheen."""
    m = bpy.data.materials.new("White_glazed_faience_Burmantofts"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"; nt.links.new(sx.outputs[0], ad.inputs[0]); nt.links.new(sx.outputs[1], ad.inputs[1])
    cb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ad.outputs[0], cb.inputs[0]); nt.links.new(sx.outputs[2], cb.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = 0.9; br.inputs["Row Height"].default_value = 0.45
    br.inputs["Mortar Size"].default_value = 0.012; br.inputs["Color1"].default_value = (0.55,0.47,0.33,1); br.inputs["Color2"].default_value = (0.50,0.43,0.30,1)
    br.inputs["Mortar"].default_value = (0.36,0.32,0.26,1); nt.links.new(cb.outputs[0], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.22; b.inputs["Coat Weight"].default_value = 0.6; b.inputs["Coat Roughness"].default_value = 0.15
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.25; bm.inputs["Distance"].default_value = 0.01; nt.links.new(br.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs[0], b.inputs["Normal"])
    return weather(m, 0.15, 0.22, 0.0)
def mats():
    return {
     "stone": weather(pbr("Portland_stone_base", "stone", (0.58,0.52,0.40), 0.75, scale=3), 0.35, 0.2, 1.5),
     "groove": pbr("Rustication_channel_shadow", None, (0.12,0.12,0.12), 0.9),
     "terracotta": faience(),
     "blocks": pbr("Concrete_block_sides_rear", "concrete", (0.6,0.58,0.55), scale=3),
     "blocks_base": pbr("Concrete_block_base_sides_rear", "concrete", (0.58,0.56,0.53), scale=3),
     "glass": glow(pbr("Glass", None, (0.01,0.012,0.015), 0.02), 2.5, 0.35),
     "frame": pbr("Window_frame_dark", None, (0.78,0.78,0.75), 0.5), "door": pbr("Door_dark", None, (0.03,0.03,0.03), 0.4),
     "bldg": neighbour_windows(pbr("Neighbour_generic", "concrete", (0.62,0.6,0.57), scale=4)),
     "road": pbr("Asphalt", "asphalt", (0.25,0.25,0.25), scale=4), "path": pbr("Paving", "paving", (0.55,0.54,0.5), scale=2),
     "ballast": pbr("Ballast", "ballast", (0.4,0.37,0.33), scale=2), "viaduct": weather(pbr("Viaduct_brick", None, (0.24,0.075,0.045), 0.85, scale=3), 0.45, 0.35, 2.0),
     "ground": pbr("Ground_paving", "paving", (0.5,0.5,0.47), scale=3), "water": pbr("Canal_water", None, (0.03,0.05,0.05), 0.04),
     "rail": pbr("Rail_steel", None, (0.3,0.3,0.3), 0.3, metal=1), "roof": pbr("Roof", None, (0.13,0.13,0.14), 0.85, scale=3), "roof2": pbr("Roof_grey_membrane", None, (0.22,0.22,0.23), 0.8), "roof3": pbr("Roof_dark_slate", None, (0.07,0.075,0.085), 0.7),
     "nb_brick": neighbour_windows(weather(pbr("Neighbour_red_brick", "brick", (0.45,0.2,0.14), scale=2.5), 0.2, 0.2, 1.0)), "nb_render": neighbour_windows(weather(pbr("Neighbour_render_cream", "concrete", (0.8,0.76,0.66), scale=4), 0.2, 0.2, 1.0)),
     "nb_grey": neighbour_windows(weather(pbr("Neighbour_grey_cladding", "concrete", (0.35,0.36,0.38), scale=4), 0.2, 0.15, 1.0)), "nb_glass": pbr("Neighbour_glass_curtain", None, (0.05,0.07,0.09), 0.05, metal=0.6),
     "kerb": pbr("Kerb", "concrete", (0.55,0.55,0.53), scale=1), "marking": pbr("Road_marking", None, (0.85,0.85,0.8), 0.6),
     "leaf": pbr("Tree_leaves", None, (0.12,0.22,0.08), 0.8), "bark": pbr("Bark", None, (0.2,0.15,0.1), 0.9),
     "lamp": pbr("Lamp_post", None, (0.05,0.05,0.05), 0.4, metal=0.8),
     "lamphead": glow(pbr("Lamp_head", None, (0.9,0.9,0.85), 0.3), 40.0, -1.0)}
def coll(n, parent=None):
    c = bpy.data.collections.new(n); (parent or bpy.context.scene.collection).children.link(c); return c
def mk(name, v, f, m, c):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.validate(); me.update()
    o = bpy.data.objects.new(name, me); o.data.materials.append(m); c.objects.link(o); return o
def prism(name, pts, z0, z1, m, c, mtop=None):
    pts = [tuple(p) for p in pts]
    if pts[0] == pts[-1]: pts = pts[:-1]
    n = len(pts)
    if sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1] for i in range(n)) < 0: pts = pts[::-1]
    v = [(x,y,z0) for x,y in pts]+[(x,y,z1) for x,y in pts]
    f = [list(range(n))[::-1], list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
    o = mk(name, v, f, m, c)
    if mtop: o.data.materials.append(mtop); o.data.polygons[1].material_index = 1
    return o
def box(name, x0, x1, y0, y1, z0, z1, m, c, parent=None):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
    o = mk(name, v, f, m, c)
    if parent: o.parent = parent
    return o
def normals(pts):
    out = []
    for i in range(len(pts)):
        a = pts[max(i-1,0)]; b = pts[min(i+1,len(pts)-1)]; dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx,dy) or 1
        out.append((-dy/L, dx/L))
    return out
def ribbon(name, pts, w, m, c, zoff=0.05):
    v, f = [], []
    for i,(x,y) in enumerate(pts):
        a = pts[max(i-1,0)]; b = pts[min(i+1,len(pts)-1)]; dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx,dy) or 1
        nx, ny = -dy/L*w/2, dx/L*w/2
        v += [(x+nx,y+ny,ground(x+nx,y+ny)+zoff),(x-nx,y-ny,ground(x-nx,y-ny)+zoff)]
    for i in range(len(pts)-1): f.append([2*i,2*i+1,2*i+3,2*i+2])
    return mk(name, v, f, m, c)
def hero(M, C, pts):
    body = prism("HERO_body", pts, -0.5, ROOF, M["blocks"], C, M["roof"])
    body["source"] = "footprint OSM; height E05+DAS 19.78 m above street; LIDAR check median 18.96 / p95 20.01"
    P = [tuple(p) for p in pts[:-1]] if tuple(pts[0]) == tuple(pts[-1]) else [tuple(p) for p in pts]
    n_ = len(P)
    if sum(P[i][0]*P[(i+1)%n_][1]-P[(i+1)%n_][0]*P[i][1] for i in range(n_)) < 0: P = P[::-1]
    best = None
    for i in range(n_):
        a, b = P[i], P[(i+1)%n_]; L = math.dist(a,b); ny = -(b[0]-a[0])/L if L else 0
        if ny < -0.7 and (best is None or L > best[2]): best = (a, b, L)
    a, b, W = best; ang = math.atan2(b[1]-a[1], b[0]-a[0])
    fr = bpy.data.objects.new("HERO_front_frame", None); C.objects.link(fr)
    fr.location = (a[0], a[1], 0); fr.rotation_euler = (0, 0, ang)  # local x along facade, -y = outward (south)
    base = box("HERO_front_stone_base", 0, W, -0.45, 0.0, -0.3, LEVELS[1], M["stone"], C, fr)
    upper = box("HERO_front_terracotta", 0, W, -0.40, 0.0, LEVELS[1], ROOF, M["terracotta"], C, fr)
    cut = coll("HERO_cutters"); 
    def cutter(x0, x1, z0, z1, arch=False):
        o = box("cut", x0, x1, -1.0, -0.12, z0, z1, M["glass"], cut, fr); res = [o]
        if arch:
            r = (x1-x0)/2; bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=0.88, location=(x0+r, -0.56, z1), rotation=(math.pi/2,0,0))
            cy = bpy.context.object; [cl.objects.unlink(cy) for cl in cy.users_collection]; cut.objects.link(cy); cy.parent = fr; res.append(cy)
        return res
    def glass(x0, x1, z0, z1, depth=-0.12, arch=False, panes=(2, 2)):
        top = z1 + ((x1-x0)/2 if arch else 0)
        box("HERO_glass", x0, x1, depth-0.02, depth, z0, top, M["glass"], C, fr)
        if arch:
            r_ = (x1-x0)/2; cx_ = x0+r_
            for k in range(1, 6):
                a = math.pi*k/6; wedge("HERO_fan_bar", cx_, z1, 0.08, r_, a-0.012, a+0.012, depth-0.06, depth, M["frame"])
            wedge("HERO_fan_hub", cx_, z1, 0.0, 0.25, 0.0, math.pi, depth-0.07, depth, M["frame"])
            panes = (panes[0], panes[1]); top = z1
        for k in range(1, panes[0]): xm = x0+(x1-x0)*k/panes[0]; box("HERO_glazing_bar", xm-0.025, xm+0.025, depth-0.06, depth, z0, top, M["frame"], C, fr)
        for k in range(1, panes[1]+1):
            tz = z0+(z1-z0)*k/(panes[1]+0.0001) if k < panes[1] else z0+(z1-z0)*0.999
            if k < panes[1]: box("HERO_glazing_bar", x0, x1, depth-0.06, depth, tz-0.025, tz+0.025, M["frame"], C, fr)
        for xx in (x0, x1): box("HERO_frame", xx-0.04, xx+0.04, depth-0.08, depth, z0, top, M["frame"], C, fr)
        box("HERO_frame", x0, x1, depth-0.08, depth, z0, z0+0.06, M["frame"], C, fr)
        box("HERO_sill", x0-0.1, x1+0.1, -0.55, -0.35, z0-0.12, z0, M["stone"] if z0 < LEVELS[1] else M["terracotta"], C, fr)
    def wedge(name, cx_, cz, r0, r1, a0, a1, y0, y1, m):
        v = []
        for a in (a0, a1):
            for rr in (r0, r1):
                for yy in (y0, y1): v.append((cx_+rr*math.cos(a), yy, cz+rr*math.sin(a)))
        f = [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
        o = mk(name, v, f, m, C); o.parent = fr; return o
    openings = []   # (x0, x1, ztop) on the stone base, used to stop rustication grooves at openings
    # ground-floor arches (6) with radiating voussoirs + keystone + pilasters between (E05)
    for f in ARCH_CENTRES:
        x = f*W; x0, x1 = x-ARCH_W/2, x+ARCH_W/2; zt = LEVELS[1]-0.6-ARCH_W/2; r = ARCH_W/2
        cutter(x0, x1, 0.6, zt, arch=True); glass(x0, x1, 0.6, zt, arch=True, panes=(4, 3))
        openings.append((x0-0.05, x1+0.05, zt+r+0.75))
        NV = 9
        for j in range(NV):
            a0 = math.pi*j/NV; a1 = math.pi*(j+1)/NV; ext = 1.25 if j == NV//2 else 1.0
            wedge("HERO_voussoir", x, zt, r, r+ext, a0+0.012, a1-0.012, -0.58, -0.40, M["stone"])
    for f in ARCH_CENTRES + [ENTRANCE[0]]:
        pass
    pil = sorted([f*W for f in ARCH_CENTRES])
    for xa, xb in zip(pil[:-1], pil[1:]):
        if xb - xa < ARCH_W*1.6: continue
        xm = (xa+xb)/2
        if abs(xm - ENTRANCE[0]*W) < 0.5: continue
        box("HERO_gf_pilaster", xm-0.3, xm+0.3, -0.62, -0.40, 0.0, LEVELS[1]-0.45, M["stone"], C, fr)
    # projecting entrance porch (E05 + CGI): pilasters, recessed glazed door, framed panel above, steps
    ex = ENTRANCE[0]*W; ew = ENTRANCE[1]
    cutter(ex-ew/2, ex+ew/2, 0.0, LEVELS[1]-0.8); openings.append((ex-ew/2-0.9, ex+ew/2+0.9, LEVELS[1]))
    box("HERO_door_left", ex-ew/2+0.1, ex-0.01, -0.30, -0.22, 0.0, 3.4, M["door"], C, fr)   # Geograph 2025: dark double doors at pavement
    box("HERO_door_right", ex+0.01, ex+ew/2-0.1, -0.30, -0.22, 0.0, 3.4, M["door"], C, fr)
    box("HERO_door_lintel", ex-ew/2, ex+ew/2, -0.45, -0.22, 3.4, 3.7, M["stone"], C, fr)
    glass(ex-ew/2+0.2, ex+ew/2-0.2, 3.7, LEVELS[1]-0.9, depth=-0.25, panes=(4, 1))
    for sgn in (-1, 1):
        xp = ex + sgn*(ew/2+0.45)
        box("HERO_porch_pilaster", xp-0.4, xp+0.4, -1.05, -0.40, 0.0, LEVELS[1]-0.2, M["stone"], C, fr)
    box("HERO_porch_entablature", ex-ew/2-0.95, ex+ew/2+0.95, -1.15, -0.40, LEVELS[1]-0.75, LEVELS[1]-0.2, M["stone"], C, fr)
    # steps removed: not shown in any source (critic1 B4); DAS lobby +2.10 m level change assumed internal (NOT FOUND)
#    for s in range(8):  # steps up to GF lobby level (DAS: +2.10 m)
#        box("HERO_step", ex-1.4, ex+1.4, -2.8+s*0.3, -0.4, 0, GF_ABOVE_STREET*(s+1)/8, M["stone"], C, fr)
    for f in (PAVILION/2, 1-PAVILION/2):
        x = f*W; cutter(x-0.6, x+0.6, 0.2, 2.6); glass(x-0.6, x+0.6, 0.2, 2.6, panes=(2, 2)); openings.append((x-0.65, x+0.65, 2.7))
    # upper floors per E05: corner pavilions (single wide window), 2 pedimented triple-light bays,
    # 13 single bays between giant pilasters; attic storey above main cornice with 15 windows + small corner windows
    TRIPLE = [(0.127, 0.223), (0.777, 0.873)]; SINGLE = [0.251 + k*(0.752-0.251)/12 for k in range(13)]
    for li in range(1, 5):
        z0 = LEVELS[li]+0.75 if li < 4 else LEVELS[li]+0.7
        z1 = LEVELS[li+1]-0.55 if li < 4 else ROOF-0.85
        for f in SINGLE:
            x = f*W; hw = 0.62
            cutter(x-hw, x+hw, z0, z1); glass(x-hw, x+hw, z0, z1, panes=(4, 5))
        for a_, b_ in TRIPLE:
            xa, xb = a_*W, b_*W
            if li < 4:
                lw = (xb-xa-0.5)/3
                for k in range(3):
                    x0 = xa+0.1+k*(lw+0.15); w_ = lw if k != 1 else lw
                    cutter(x0, x0+w_, z0, z1); glass(x0, x0+w_, z0, z1, panes=(3, 5))
            else:
                xm = (xa+xb)/2; cutter(xm-0.62, xm+0.62, z0, z1); glass(xm-0.62, xm+0.62, z0, z1, panes=(4, 5))
        for f in (PAVILION/2, 1-PAVILION/2):
            x = f*W
            if li < 4: cutter(x-0.85, x+0.85, z0, z1); glass(x-0.85, x+0.85, z0, z1, panes=(4, 5))
            else: cutter(x-1.0, x+1.0, z0+0.6, z0+1.3); glass(x-1.0, x+1.0, z0+0.6, z0+1.3, panes=(3, 1))
    # giant pilasters between single bays + pavilion edges (1st floor band to main cornice)
    edges = [(SINGLE[k]+SINGLE[k+1])/2 for k in range(0, 12, 2)] + [SINGLE[0]-(SINGLE[1]-SINGLE[0])/2, SINGLE[-1]+(SINGLE[1]-SINGLE[0])/2, PAVILION, 1-PAVILION]
    for f in edges:
        x = f*W; box("HERO_giant_pilaster", x-0.38, x+0.38, -0.62, -0.40, LEVELS[1], LEVELS[4]-0.55, M["terracotta"], C, fr)
        box("HERO_pilaster_capital", x-0.32, x+0.32, -0.7, -0.40, LEVELS[4]-0.85, LEVELS[4]-0.55, M["terracotta"], C, fr)
    # oriel bays at the triple-window bays, floors 1-2 (Commons 2015 photo: projecting bay, flat moulded head). Projection depth NOT FOUND: 0.6 m stand-in
    for a_, b_ in TRIPLE:
        xa, xb = a_*W-0.15, b_*W+0.15; z0_ = LEVELS[1]+0.15; zt_ = LEVELS[4]-0.6; d_ = -1.0   # R4: Commons photo shows the oriel over floors 1-3
        for xx in (xa, xb): box("HERO_oriel_cheek", xx-0.12, xx+0.12, d_, -0.40, z0_, zt_, M["terracotta"], C, fr)
        box("HERO_oriel_base", xa-0.15, xb+0.15, d_-0.1, -0.40, z0_-0.45, z0_, M["terracotta"], C, fr)
        box("HERO_oriel_head", xa-0.25, xb+0.25, d_-0.2, -0.40, zt_, zt_+0.45, M["terracotta"], C, fr)
        for lv in (2, 3): box("HERO_oriel_transom", xa, xb, d_, d_+0.15, LEVELS[lv]-0.2, LEVELS[lv]+0.3, M["terracotta"], C, fr)
        glass(xa+0.12, xb-0.12, z0_, zt_, depth=d_+0.05, panes=(6, 6))
    # small triangular pediments over the corner-bay first-floor windows (Commons + Geograph photos)
    for f in (PAVILION/2, 1-PAVILION/2):
        xm = f*W; zt_ = LEVELS[2]-0.25; h_ = 0.5
        v = [(xm-1.1, -0.75, zt_), (xm+1.1, -0.75, zt_), (xm, -0.75, zt_+h_), (xm-1.1, -0.40, zt_), (xm+1.1, -0.40, zt_), (xm, -0.40, zt_+h_)]
        o = mk("HERO_pediment", v, [[0,1,2],[5,4,3],[0,3,4,1],[1,4,5,2],[2,5,3,0]], M["terracotta"], C); o.parent = fr
    # rustication grooves: recessed dark channels, interrupted at openings (no lines across glazing)
    z = 0.5
    while z < LEVELS[1]-0.5:
        cuts_ = sorted((a_, b_) for a_, b_, zt_ in openings if z < zt_)
        xs = 0.0
        for a_, b_ in cuts_ + [(W, W)]:
            if a_ > xs + 0.05: box("HERO_rustication_groove", xs, a_, -0.455, -0.449, z-0.035, z+0.035, M["groove"], C, fr)
            xs = max(xs, b_)
        z += 0.55
    for zc, d, h, m in ((LEVELS[1], 0.75, 0.45, "stone"), (LEVELS[4], 0.95, 0.55, "terracotta"), (ROOF, 0.85, 0.55, "terracotta")):
        box("HERO_cornice", -0.3, W+0.3, -d, 0.0, zc-h, zc, M[m], C, fr)
        box("HERO_cornice_drip", -0.3, W+0.3, -d-0.05, -d+0.05, zc-h-0.08, zc-h, M[m], C, fr)
    box("HERO_parapet", -0.2, W+0.2, -0.42, 0.0, ROOF, ROOF+0.25, M["terracotta"], C, fr)
    t0, t1, th = ROOF_TOWER; box("HERO_roof_tower", t0*W, t1*W, 6.0, 11.0, ROOF, ROOF+th, M["blocks"], C, fr)
    if ROOF_EXTENSION: box("HERO_roof_extension_UNCONFIRMED", 2, W-2, 2.0, 25, ROOF, ROOF+6.0, M["roof"], C, fr)
    for i in range(n_):   # sides/rear: wide window bands (Heritage Statement para 37; rear dwg D06)
        p0, p1 = P[i], P[(i+1)%n_]
        if (p0, p1) == (a, b): continue
        L = math.dist(p0, p1)
        if L < 6: continue
        e = bpy.data.objects.new("HERO_side_frame", None); C.objects.link(e)
        e.location = (p0[0], p0[1], 0); e.rotation_euler = (0, 0, math.atan2(p1[1]-p0[1], p1[0]-p0[0]))
        n = max(1, int((L-2)/3.2))
        for li in range(1, 5):
            z0, z1 = LEVELS[li]+0.9, LEVELS[li]+0.9+2.1
            for k in range(n):
                x0 = 1+k*(L-2)/n+0.15; x1 = 1+(k+1)*(L-2)/n-0.15
                box("HERO_side_glass", x0, x1, -0.03, -0.01, z0, z1, M["glass"], C, e)
                box("HERO_side_sill", x0-0.08, x1+0.08, -0.08, -0.0, z0-0.1, z0, M["frame"], C, e)
        box("HERO_side_block_base", 0, L, -0.06, 0.0, -0.3, LEVELS[1], M["blocks_base"], C, e)
    # --- R3 decoration from Commons/Geograph photos; all sizes/depths are STAND-INS (not dimensioned in any source)
    def disc(name, cx_, cz, rx, rz, y0, y1, m, n=24):
        v = []
        for k in range(n):
            a = 2*math.pi*k/n; v += [(cx_+rx*math.cos(a), y0, cz+rz*math.sin(a)), (cx_+rx*math.cos(a), y1, cz+rz*math.sin(a))]
        f = [[2*k, 2*((k+1)%n), 2*((k+1)%n)+1, 2*k+1] for k in range(n)] + [[2*k for k in range(n)][::-1], [2*k+1 for k in range(n)]]
        o = mk(name, v, f, m, C); o.parent = fr; return o
    for f in (PAVILION/2, 1-PAVILION/2):   # large ground-floor cartouches at both end bays
        xm = f*W; zc = 3.2   # above the small end-bay window (top 2.6 m), below the first-floor band
        disc("HERO_cartouche_frame", xm, zc, 0.55, 0.5, -0.72, -0.40, M["stone"]); disc("HERO_cartouche", xm, zc, 0.38, 0.36, -0.85, -0.70, M["stone"])
    for a_, b_ in TRIPLE:   # 'RB' monogram shields on the piers beside the oriel bays (Geograph/Commons)
        for xx in (a_*W+(-0.9 if a_ < 0.5 else 0), b_*W+(0.9 if a_ < 0.5 else 0)):
            if a_ < 0.5 and xx < a_*W: continue
            if a_ > 0.5 and xx > b_*W: continue
            for zz in (LEVELS[3]+0.3, LEVELS[4]-1.6):
                disc("HERO_RB_shield", xx, zz, 0.42, 0.52, -0.78, -0.55, M["terracotta"], 16)
    for sgn in (-1, 1):   # moulded doorcase: stepped architrave (3 fasciae)
        for k, (w_, d_) in enumerate(((0.12, -0.55), (0.10, -0.65), (0.08, -0.75))):
            xx = ex + sgn*(ew/2 + 0.05 + k*0.12)
            box("HERO_doorcase", xx-w_/2, xx+w_/2, d_, -0.40, 0.0, LEVELS[1]-0.8+k*0.12, M["stone"], C, fr)
    for k in range(3): box("HERO_doorcase_head", ex-ew/2-0.1-k*0.12, ex+ew/2+0.1+k*0.12, -0.55-k*0.1, -0.40, LEVELS[1]-0.8+k*0.12, LEVELS[1]-0.68+k*0.12, M["stone"], C, fr)
    for o in (base, upper):  # restore window/arch booleans (lost in R1 hero rewrite)
        bm = o.modifiers.new("windows", "BOOLEAN"); bm.operation = "DIFFERENCE"; bm.operand_type = "COLLECTION"; bm.collection = cut; bm.solver = "EXACT"
    for o_ in cut.objects: o_.hide_render = True; o_.display_type = "WIRE"
    return fr, W
def viaduct(name, pts, zs, M, C):
    zz = sorted(z for z in zs if z is not None and 5 < z < 16); deck = zz[len(zz)//2] if zz else 8.55
    for i in range(len(pts)-1):
        a, b = pts[i], pts[i+1]; L = math.dist(a, b)
        if L < 0.5: continue
        g = min(ground(*a), ground(*b)); top = deck
        n = max(1, round(L/VIADUCT_SPAN)); sp = L/n
        e = bpy.data.objects.new(name+"_seg", None); C.objects.link(e)
        e.location = (a[0], a[1], 0); e.rotation_euler = (0, 0, math.atan2(b[1]-a[1], b[0]-a[0]))
        for k in range(n):
            x0 = k*sp; x1 = x0+sp; w = max(1.0, sp-PIER_W); r = w/2; spring = max(g+0.5, top-1.4-r)
            box(name+"_pier", x0, x0+PIER_W/2, -VIADUCT_W/2, VIADUCT_W/2, g-0.5, top, M["viaduct"], C, e)
            box(name+"_pier", x1-PIER_W/2, x1, -VIADUCT_W/2, VIADUCT_W/2, g-0.5, top, M["viaduct"], C, e)
            cx = x0+sp/2; NS = 12; v = []; f = []
            for j in range(NS+1):
                t = math.pi*(1-j/NS); xa = cx+r*math.cos(t); za = spring+r*math.sin(t)
                v += [(xa,-VIADUCT_W/2,za),(xa,-VIADUCT_W/2,top),(xa,VIADUCT_W/2,za),(xa,VIADUCT_W/2,top)]
            for j in range(NS):
                q = 4*j; f += [[q,q+4,q+5,q+1],[q+2,q+3,q+7,q+6],[q,q+2,q+6,q+4]]
            o = mk(name+"_arch", v, f, M["viaduct"], C); o.parent = e
            for xs in (x0+PIER_W/2, x1-PIER_W/2):
                box(name+"_spring", min(xs, cx-r), max(xs, cx-r) if xs < cx else max(xs, cx+r), -VIADUCT_W/2, VIADUCT_W/2, g-0.5, spring, M["viaduct"], C, e) if abs(xs-(cx-r if xs < cx else cx+r)) > 0.01 else None
        box(name+"_deck", 0, L, -VIADUCT_W/2-0.3, VIADUCT_W/2+0.3, top, top+0.25, M["ballast"], C, e)
        box(name+"_parapet_l", 0, L, -VIADUCT_W/2-0.3, -VIADUCT_W/2, top, top+1.1, M["viaduct"], C, e)
        box(name+"_parapet_r", 0, L, VIADUCT_W/2, VIADUCT_W/2+0.3, top, top+1.1, M["viaduct"], C, e)
        for yy in (-0.75, 0.75): box(name+"_rail", 0, L, yy-0.04, yy+0.04, top+0.25, top+0.42, M["rail"], C, e)
    return deck
ROAD_W = {"primary":10,"secondary":9,"tertiary":8,"residential":6,"unclassified":6,"service":4,"trunk":12,"living_street":5,
          "pedestrian":4,"footway":2,"cycleway":2,"steps":2,"path":2}
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = mats(); sc = bpy.context.scene
    CB, CR, CT, CH, CN = coll("Buildings"), coll("Roads_Terrain_Water"), coll("Rail_Viaduct"), coll("Hero"), coll("Trees_Furniture")
    R, Cc, st = DT["rows"], DT["cols"], DT["step"]; v = []; f = []
    for r in range(R):
        for c in range(Cc): v.append((DT["e0"]+c*st+1, DT["n0"]-r*st-1, DT["z"][r*Cc+c]-0.02))
    for r in range(R-1):
        for c in range(Cc-1): i = r*Cc+c; f.append([i, i+1, i+Cc+1, i+Cc])
    mk("Terrain_EA_DTM", v, f, M["ground"], CR)
    heroO = None
    for bd in D["buildings"]:
        if bd["id"] == HERO_ID: heroO = hero(M, CH, bd["pts"]); continue
        if "h" not in bd: continue   # no measured height -> NOT_FOUND, not modelled
        z0 = bd.get("base", ground(*bd["pts"][0]))
        hsh = int(bd["id"]) % 7; tall = bd["h"] > 28
        mk_ = (["nb_glass","nb_grey","nb_grey"] if tall else ["nb_brick","nb_brick","nb_render","nb_grey","bldg","nb_brick","nb_render"])[hsh % (3 if tall else 7)]
        o = prism("bldg_"+bd["id"], bd["pts"], z0-0.5, z0+max(bd["h"],2.5), M[mk_], CB, M[("roof","roof2","roof3")[__import__("zlib").crc32((bd["id"]+"r").encode()) % 3]]); o["height_source"] = bd["src"]; o["material_note"] = "stand-in (not sourced)"
    for rd in D["roads"]:
        k = rd["k"]
        if k not in ROAD_W or rd.get("area") == "yes" or rd.get("bridge"): continue
        if rd.get("layer") and rd["layer"].lstrip("-").isdigit() and int(rd["layer"]) < 0: continue
        rd = dict(rd); rd["pts"] = [p_ for p_ in rd["pts"] if -300 < p_[0] < 500 and -380 < p_[1] < 410]
        if len(rd["pts"]) < 2: continue
        foot = k in ("pedestrian","footway","cycleway","steps","path")
        ribbon("road_"+rd["id"], rd["pts"], ROAD_W[k], M["path" if foot else "road"], CR)
        if not foot and ROAD_W[k] >= 6:   # stand-in kerbs + dashed centre line
            for sg in (-1, 1):
                off_ = [(x - sg*ROAD_W[k]/2*nx_, y - sg*ROAD_W[k]/2*ny_) for (x, y), (nx_, ny_) in zip(rd["pts"], normals(rd["pts"]))]
                ribbon("kerb_"+rd["id"], off_, 0.3, M["kerb"], CR, 0.13)
            pts_ = rd["pts"]
            for i in range(len(pts_)-1):
                a_, b_ = pts_[i], pts_[i+1]; L_ = math.dist(a_, b_); t_ = 0.0
                while t_ + 3 < L_:
                    p0 = (a_[0]+(b_[0]-a_[0])*t_/L_, a_[1]+(b_[1]-a_[1])*t_/L_); p1 = (a_[0]+(b_[0]-a_[0])*(t_+3)/L_, a_[1]+(b_[1]-a_[1])*(t_+3)/L_)
                    ribbon("marking", [p0, p1], 0.12, M["marking"], CR, 0.07); t_ += 9
    decks = []
    for rl in D["rails"]:
        if rl["k"] != "rail": continue
        if rl.get("bridge") == "viaduct": decks.append(viaduct("viaduct_"+rl["id"], rl["pts"], rl["z"], M, CT))
        else: ribbon("rail_"+rl["id"], rl["pts"], 3.5, M["ballast"], CT, 0.1)
    for wt in D["water"]:
        if wt["closed"]:
            z = min(ground(*p) for p in wt["pts"]) - 0.4
            prism("canal_"+wt["id"], wt["pts"], z-0.5, z, M["water"], CR)
        elif wt["k"] == "canal": ribbon("canal_"+wt["id"], wt["pts"], 6, M["water"], CR, -1.0)
    tx = bpy.data.textures.new("treeN", "CLOUDS"); tx.noise_scale = 1.0
    for x, y, h in D["trees"]:
        h = h if h and 3 < h < 25 else 6.0; g = ground(x, y)
        tr = box("tree_trunk", x-0.15, x+0.15, y-0.15, y+0.15, g, g+h*0.5, M["bark"], CN)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=h*0.3, location=(x, y, g+h*0.68)); cr = bpy.context.object; cr.name = "tree_crown"
        cr.data.materials.append(M["leaf"]); d = cr.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = h*0.12
        [cl.objects.unlink(cr) for cl in cr.users_collection]; CN.objects.link(cr)
    for rd in D["roads"]:   # lamp posts: set dressing (positions NOT_FOUND)
        if rd.get("name") == "Whitworth Street West" and rd["k"] in ROAD_W:
            for i in range(len(rd["pts"])-1):
                a, b = rd["pts"][i], rd["pts"][i+1]; L = math.dist(a, b); s = 7.0
                while s < L:
                    x = a[0]+(b[0]-a[0])*s/L; y = a[1]+(b[1]-a[1])*s/L; nx, ny = -(b[1]-a[1])/L*6.5, (b[0]-a[0])/L*6.5
                    px, py = x+nx, y+ny; g = ground(px, py)
                    box("lamp_post", px-0.07, px+0.07, py-0.07, py+0.07, g, g+6, M["lamp"], CN)
                    box("lamp_head", px-0.25, px+0.25, py-0.25, py+0.25, g+6, g+6.2, M["lamphead"], CN)
                    ld = bpy.data.lights.new("StreetLight", "POINT"); ld.energy = 0; ld.color = (1.0, 0.75, 0.45); ld.shadow_soft_size = 0.2
                    lo = bpy.data.objects.new("StreetLight", ld); lo.location = (px, py, g+5.9); CN.objects.link(lo); s += 25
    w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree; out_ = nt.nodes["World Output"]; nt.nodes.remove(nt.nodes["Background"])
    sky = nt.nodes.new("ShaderNodeTexSky"); sky.name = "SKY"; sky.sky_type = "NISHITA"; sky.altitude = 40
    bgS = nt.nodes.new("ShaderNodeBackground"); bgS.name = "BG_SKY"
    tcw = nt.nodes.new("ShaderNodeTexCoord"); sxw = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcw.outputs["Generated"], sxw.inputs[0])
    dv = nt.nodes.new("ShaderNodeVectorMath"); dv.operation = "DIVIDE"; nt.links.new(tcw.outputs["Generated"], dv.inputs[0])
    czc = nt.nodes.new("ShaderNodeCombineXYZ"); mx_ = nt.nodes.new("ShaderNodeMath"); mx_.operation = "MAXIMUM"; mx_.inputs[1].default_value = 0.05
    nt.links.new(sxw.outputs[2], mx_.inputs[0]); [nt.links.new(mx_.outputs[0], czc.inputs[i]) for i in range(3)]; nt.links.new(czc.outputs[0], dv.inputs[1])
    cn = nt.nodes.new("ShaderNodeTexNoise"); cn.inputs["Scale"].default_value = 1.2; cn.inputs["Detail"].default_value = 8; cn.inputs["Roughness"].default_value = 0.6
    nt.links.new(dv.outputs[0], cn.inputs["Vector"]); crw = nt.nodes.new("ShaderNodeMapRange"); crw.name = "CLOUD_COVER"; crw.inputs[1].default_value = 0.52; crw.inputs[2].default_value = 0.72
    nt.links.new(cn.outputs["Fac"], crw.inputs[0]); hz = nt.nodes.new("ShaderNodeMapRange"); hz.inputs[1].default_value = 0.02; hz.inputs[2].default_value = 0.2
    nt.links.new(sxw.outputs[2], hz.inputs[0]); cm_ = nt.nodes.new("ShaderNodeMath"); cm_.operation = "MULTIPLY"; nt.links.new(crw.outputs[0], cm_.inputs[0]); nt.links.new(hz.outputs[0], cm_.inputs[1])
    bw_ = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(sky.outputs[0], bw_.inputs[0]); cl = nt.nodes.new("ShaderNodeMath"); cl.operation = "MULTIPLY"; cl.inputs[1].default_value = 1.6
    nt.links.new(bw_.outputs[0], cl.inputs[0]); cc = nt.nodes.new("ShaderNodeCombineColor"); [nt.links.new(cl.outputs[0], cc.inputs[i]) for i in range(3)]
    mxc = nt.nodes.new("ShaderNodeMix"); mxc.data_type = "RGBA"; nt.links.new(cm_.outputs[0], mxc.inputs[0]); nt.links.new(sky.outputs[0], mxc.inputs[6]); nt.links.new(cc.outputs[0], mxc.inputs[7])
    nt.links.new(mxc.outputs[2], bgS.inputs[0])
    bgH = nt.nodes.new("ShaderNodeBackground"); bgH.name = "BG_HDRI"; bgH.inputs[1].default_value = 0.6
    hdri = os.path.join(HERE, "hdri.exr")
    if os.path.exists(hdri):
        e = nt.nodes.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(hdri); nt.links.new(e.outputs[0], bgH.inputs[0])
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.name = "SKY_HDRI_MIX"; nt.links.new(bgS.outputs[0], mix.inputs[1]); nt.links.new(bgH.outputs[0], mix.inputs[2])
    night = nt.nodes.new("ShaderNodeBackground"); night.name = "NIGHT"; night.inputs[0].default_value = (0.02, 0.03, 0.06, 1)
    add = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(mix.outputs[0], add.inputs[0]); nt.links.new(night.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out_.inputs[0])
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sun.data.energy = 1.5; sun.data.angle = math.radians(4)
    sc.collection.objects.link(sun)
    fr, W = heroO; bpy.context.view_layer.update(); mw = fr.matrix_world.copy()
    for k in range(7):   # stand-in facade uplights for the night preset
        ld = bpy.data.lights.new("StreetLight_uplight", "SPOT"); ld.energy = 0; ld.color = (1.0, 0.8, 0.55); ld.spot_size = math.radians(40)
        lo = bpy.data.objects.new("StreetLight_uplight", ld); sc.collection.objects.link(lo)
        lo.matrix_world = mw @ mathutils.Matrix.Translation((W*(k+0.5)/7, -2.0, 0.2)) @ mathutils.Euler((math.radians(-15), 0, 0)).to_matrix().to_4x4()
    def L2W(x, y, z): return mw @ mathutils.Vector((x, y, z))
    def cam(name, loc, tgt, lens, shift=0.0):
        cd = bpy.data.cameras.new(name); cd.lens = lens; cd.shift_y = shift; cd.clip_end = 3000
        o = bpy.data.objects.new(name, cd); o.location = loc; sc.collection.objects.link(o)
        o.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
    CAMS = {
     "hero": cam("Cam_Hero_34", L2W(W*0.5-4.0, -14.0, 1.6), L2W(W*0.75, 0, 1.6), 16, 0.2),
     "street": cam("Cam_Street", L2W(W*0.5, -STREET_D, 1.7), L2W(W*0.5, 0, 1.7), STREET_LENS, 0.17),
     "aerial": cam("Cam_Aerial", L2W(W*1.4, -110, 120), L2W(W*0.5, 8, 8), 40),
     "viaduct": cam("Cam_Viaduct", L2W(-W*0.3, -VIA_D, (sorted(decks)[len(decks)//2] if decks else 8.55)+6.5), L2W(W*0.5, 0, 9), 28)}
    sc.camera = CAMS["hero"]
    r = sc.render; r.engine = "CYCLES"; r.resolution_x, r.resolution_y = RES; r.resolution_percentage = 100
    sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02; sc.cycles.max_bounces = 6
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = float(os.environ.get("BEXP", 0.6))
    code = open(os.path.join(HERE, "tod_panel.py")).read(); t = bpy.data.texts.new("barclay_tod.py"); t.write(code); t.use_module = True
    exec(compile(code, "barclay_tod.py", "exec"), TOD)
    sc.barclay_camera = "Cam_Hero_34"; sc.render.film_transparent = False
    arg = lambda k: sys.argv[sys.argv.index(k)+1] if k in sys.argv else None
    tm = arg("--time") or os.environ.get("BTIME", "midday")
    if tm in TOD["PRESETS"]: TOD["set_preset"](sc, tm)
    else: hh, mm = tm.split(":"); sc.barclay_time = int(hh)+int(mm)/60
    if arg("--date"): mo, dy = arg("--date").split("-"); sc.barclay_month, sc.barclay_day = int(mo), int(dy)
    TOD["apply"](None, bpy.context)
    if "BRES" in os.environ: r.resolution_x, r.resolution_y = RES
    if "BSAMPLES" in os.environ: sc.cycles.samples = SAMPLES
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "barclay_scene.blend"))
    if "--noexport" not in sys.argv:
        bpy.ops.export_scene.gltf(filepath=os.path.join(out, "barclay_scene.glb"), export_apply=True)
        bpy.ops.export_scene.fbx(filepath=os.path.join(out, "barclay_scene.fbx"), use_mesh_modifiers=True, path_mode="COPY", embed_textures=True)
    if "--all-presets" in sys.argv:
        import time
        for n in (arg("--all-presets") or ",".join(TOD["PRESETS"])).split(","):
            TOD["set_preset"](sc, n)
            if "BRES" in os.environ: r.resolution_x, r.resolution_y = RES
            if "BSAMPLES" in os.environ: sc.cycles.samples = SAMPLES
            for cname in os.environ.get("BCAMS", "hero").split(","):
                sc.barclay_camera = CAMS[cname].name; TOD["apply"](None, bpy.context); t = time.time()
                r.filepath = os.path.join(out, f"tod_{n}_{cname}_{r.resolution_x}x{r.resolution_y}.png"); bpy.ops.render.render(write_still=True)
                print(f"RENDER {n} {cname} {time.time()-t:.1f}s")
    if "--render" in sys.argv:
        import time
        for cname in os.environ.get("BCAMS", "hero,aerial,viaduct").split(","):
            sc.barclay_camera = CAMS[cname].name; TOD["apply"](None, bpy.context); t = time.time(); r.filepath = os.path.join(out, f"render_{cname}_{r.resolution_x}x{r.resolution_y}.png")
            bpy.ops.render.render(write_still=True); print(f"RENDER {cname} {time.time()-t:.1f}s")
    print("OK objects:", len(bpy.data.objects), "roof above street:", round(ROOF, 3), "front W:", round(W, 2))
SUN_Z = float(os.environ.get("SUN_Z", 20)); TOD = {"__name__": "barclay_tod"}; STREET_D = float(os.environ.get("STREET_D", 15)); STREET_LENS = float(os.environ.get("STREET_LENS", 12)); VIA_D = float(os.environ.get("VIA_D", 28))
main()
