"""Surroundings detail layer for Barclay House (NOT the hero, NOT interior). Blender 4.2.3, free only.
Run on a COPY:  cp out/barclay_scene.blend tests/surr/scene_copy.blend
  blender -b -y tests/surr/scene_copy.blend -P build_surroundings.py -- [--layers all|bldg,via,street,furn,trees,canal] [--save tests/surr/scene_surr.blend] [--render] [--res 960x540 --samples 48]
Never saves over out/barclay_scene.blend. Data: scene_data.json + surroundings_data.json (OSM Overpass ODbL, EA LIDAR OGL).
Tags: anything not from OSM/LIDAR/scene_data is STAND-IN (see surroundings_specs.md)."""
import bpy, json, math, os, sys, random
HERE = "/workspace/barclay"; A = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
arg = lambda k, d=None: A[A.index(k)+1] if k in A else d
LAYERS = set((arg("--layers", "all")).split(",")); ON = lambda l: "all" in LAYERS or l in LAYERS
G = {"__name__": "bs_helpers", "__file__": HERE+"/build_scene.py"}
exec(open(HERE+"/build_scene.py").read().rsplit("\nmain()", 1)[0], G)   # reuse helpers (ground, pbr, mk, box, prism, glow, ...)
ground, pbr, glow, weather, nwin = G["ground"], G["pbr"], G["glow"], G["weather"], G["neighbour_windows"]
SD = json.load(open(HERE+"/scene_data.json")); SU = json.load(open(HERE+"/surroundings_data.json"))
HERO_ID = "100646649"; R_HI, R_MID = 120.0, 250.0; random.seed(7)
def coll(n):
    c = bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c
CS = coll("Surroundings_Detail")
for im in bpy.data.images:   # copies live outside out/: re-anchor '//' paths to the master's folder
    if im.filepath.startswith("//"): im.filepath = os.path.normpath(os.path.join(HERE, "out", im.filepath[2:]))
# ---------- materials (Poly Haven CC0 textures in textures/; colours stand-in unless spec says confirmed) ----------
def M_():
    return {"brick": nwin(weather(pbr("S_red_brick", "s_red_brick_03", (0.50,0.24,0.17), 0.85, scale=2.0), 0.25, 0.2, 1.0)),
     "via": weather(pbr("S_viaduct_brick", "s_red_brick_03", (0.42,0.16,0.11), 0.9, scale=2.0), 0.45, 0.35, 2.0),
     "render": nwin(weather(pbr("S_render_white", "s_painted_plaster_wall", (0.86,0.84,0.79), 0.75, scale=3.0), 0.15, 0.15, 1.0)),
     "clad": nwin(weather(pbr("S_cladding_grey", "s_concrete_floor_02", (0.42,0.43,0.45), 0.6, scale=3.0), 0.1, 0.1, 1.0)),
     "cream": nwin(weather(pbr("S_cladding_cream", "s_painted_plaster_wall", (0.80,0.77,0.70), 0.6, scale=3.0), 0.1, 0.1, 1.0)),
     "tile_green": pbr("S_glazed_tile_green", None, (0.05,0.25,0.12), 0.25), "tile_yellow": pbr("S_glazed_tile_yellow", None, (0.80,0.66,0.08), 0.25),
     "stone": pbr("S_sandstone_dressing", "stone", (0.55,0.45,0.33), 0.8, scale=2.0),
     "glass": glow(pbr("S_window_glass", None, (0.015,0.02,0.025), 0.04), 2.0, 0.5), "frame": pbr("S_window_frame", None, (0.12,0.12,0.13), 0.5),
     "shop": glow(pbr("S_shop_glass", None, (0.03,0.035,0.04), 0.05), 4.0, 0.2), "fascia": pbr("S_fascia_dark", None, (0.04,0.04,0.045), 0.4),
     "sign": glow(pbr("S_sign_panel", None, (0.75,0.72,0.65), 0.4), 3.0, 0.2), "door": pbr("S_door_dark", None, (0.03,0.03,0.03), 0.5),
     "metal": pbr("S_painted_steel_black", None, (0.02,0.02,0.02), 0.45, metal=0.7), "galv": pbr("S_galv_steel", None, (0.45,0.46,0.47), 0.4, metal=1.0),
     "sleeper": pbr("S_concrete_sleeper", "s_concrete_floor_02", (0.5,0.5,0.48), 0.85, scale=1.0),
     "yellow": pbr("S_line_yellow", None, (0.85,0.65,0.05), 0.6), "white": pbr("S_line_white", None, (0.85,0.85,0.82), 0.6),
     "red": pbr("S_postbox_red", None, (0.55,0.02,0.02), 0.3), "lamp": glow(pbr("S_lantern", None, (0.9,0.9,0.85), 0.3), 40.0, -1.0),
     "sig_r": glow(pbr("S_signal_red", None, (0.5,0.02,0.01), 0.2), 15.0, -1.0), "sig_g": glow(pbr("S_signal_green", None, (0.02,0.4,0.15), 0.2), 15.0, -1.0),
     "bark": pbr("S_bark", None, (0.17,0.13,0.10), 0.9), "leaf": pbr("S_leaves", None, (0.10,0.20,0.06), 0.75),
     "leaf2": pbr("S_leaves_b", None, (0.14,0.24,0.08), 0.75), "roofplant": pbr("S_roof_plant", None, (0.5,0.5,0.5), 0.5, metal=0.6)}
# ---------- merged-mesh builder (one object per layer, multi-material) ----------
class MB:
    def __init__(s, name): s.n = name; s.v = []; s.f = []; s.mi = []; s.mats = []
    def mat(s, m):
        if m not in s.mats: s.mats.append(m)
        return s.mats.index(m)
    def poly(s, pts, m):
        b = len(s.v); s.v += pts; s.f.append(list(range(b, b+len(pts)))); s.mi.append(s.mat(m))
    def box(s, c, u, w, d, h, m, z0):   # centre c(x,y), unit dir u, width along u, depth, z0..z0+h
        ux, uy = u; nx, ny = -uy, ux; P = []
        for a, b in ((-1,-1),(1,-1),(1,1),(-1,1)): P.append((c[0]+ux*w/2*a+nx*d/2*b, c[1]+uy*w/2*a+ny*d/2*b))
        lo = [(x,y,z0) for x,y in P]; hi = [(x,y,z0+h) for x,y in P]
        s.poly(lo[::-1], m); s.poly(hi, m)
        for i in range(4): j = (i+1)%4; s.poly([lo[i], lo[j], hi[j], hi[i]], m)
    def cyl(s, x, y, z0, z1, r0, r1, m, seg=8):
        lo = [(x+r0*math.cos(2*math.pi*k/seg), y+r0*math.sin(2*math.pi*k/seg), z0) for k in range(seg)]
        hi = [(x+r1*math.cos(2*math.pi*k/seg), y+r1*math.sin(2*math.pi*k/seg), z1) for k in range(seg)]
        s.poly(lo[::-1], m); s.poly(hi, m)
        for i in range(seg): j = (i+1)%seg; s.poly([lo[i], lo[j], hi[j], hi[i]], m)
    def wallrect(s, a, u, n, s0, s1, z0, z1, off, m):   # rectangle on a facade plane
        p = lambda t, z: (a[0]+u[0]*t+n[0]*off, a[1]+u[1]*t+n[1]*off, z)
        s.poly([p(s0,z0), p(s1,z0), p(s1,z1), p(s0,z1)], m)
    def build(s, col):
        if not s.v: return None
        me = bpy.data.meshes.new(s.n); me.from_pydata(s.v, [], s.f)
        for m in s.mats: me.materials.append(m)
        for p, i in zip(me.polygons, s.mi): p.material_index = i
        me.validate(); me.update(); o = bpy.data.objects.new(s.n, me); col.objects.link(o); return o
def pip(pt, poly):
    x, y = pt; c = False; n = len(poly)
    for i in range(n):
        (x1,y1),(x2,y2) = poly[i], poly[(i+1)%n]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: c = not c
    return c
def dseg(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; L2 = dx*dx+dy*dy or 1e-9; t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)
def dline(p, pts): return min(dseg(p, a, b) for a, b in zip(pts, pts[1:]))
ROADS = [r for r in SD["roads"] if r["k"] in ("primary","secondary","tertiary","residential","unclassified","service","trunk")]
def near_road(p, lim):
    best = (1e9, None)
    for r in ROADS:
        for a, b in zip(r["pts"], r["pts"][1:]):
            d = dseg(p, a, b)
            if d < best[0]: best = (d, (r, a, b))
    return best if best[0] < lim else (best[0], None)
# ---------- per-building specs (see surroundings_specs.md; 'conf' = confirmed source, else stand-in) ----------
SPEC = {"204921679": dict(mat="clad", gf_shop=True, bay=3.0),            # 10-storey apts, OSM levels; GF units = OSM shop nodes
        "705574571": dict(mat="render", gf_shop=False, bay=4.0, canopy="RITZ"),   # O2 Ritz, white render (Commons ref 4329097)
        "100646638": dict(mat="tile_green", band="tile_yellow", gf_shop=False, bay=2.4),  # Peveril: OSM building:colour #eada0b + Commons ref 3606000
        "100646641": dict(mat="brick", gf_shop=True, bay=3.2), "114615385": dict(mat="brick", ruin=True, bay=3.2),
        "647385655": dict(mat="cream", bay=2.6), "647385657": dict(mat="cream", bay=2.6),
        "136999879": dict(mat="brick", gf_shop=True, bay=3.0), "1281855670": dict(mat="brick", windows=False)}
def bspec(b):
    s = dict(mat="brick", gf_shop=False, bay=3.0, windows=True); s.update(SPEC.get(b["id"], {}))
    if b["h"] > 28 and b["id"] not in SPEC: s["mat"] = "clad"
    return s
def buildings(M):
    OS = {x["osm"].split("/")[1]: x["tags"] for x in SU["buildings_osm"]}
    polys = {b["id"]: [tuple(p) for p in b["pts"][:-1]] for b in SD["buildings"]}
    shops = [p for p in SU["pois"] if "shop" in p["tags"] or p["tags"].get("amenity") in ("cafe","restaurant","fast_food","bar","pub")]
    n_b = 0; removed = 0
    for b in SD["buildings"]:
        if b["id"] == HERO_ID or "h" not in b: continue
        P = polys[b["id"]]; cx = sum(p[0] for p in P)/len(P); cy = sum(p[1] for p in P)/len(P)
        if math.hypot(cx, cy) > R_HI: continue
        o = bpy.data.objects.get("bldg_"+b["id"])
        if o: bpy.data.objects.remove(o); removed += 1
        sp = bspec(b); t = OS.get(b["id"], {}); z0 = b.get("base", ground(cx, cy)); H = max(b["h"], 2.5)
        lv = int(float(t["building:levels"])) if t.get("building:levels") else max(1, round(H/3.2))  # OSM levels (confirmed) else stand-in 3.2 m/floor
        mb = MB("SURR_bldg_"+b["id"]); m = M[sp["mat"]]
        if sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P))) < 0: P = P[::-1]
        n = len(P); top = z0+H
        mb.poly([(x,y,z0-0.5) for x,y in P][::-1], m)
        mb.poly([(x,y,top-0.05) for x,y in P], M["roofplant"] if False else M["fascia"])  # roof deck (dark membrane, stand-in)
        others = [q for k, q in polys.items() if k != b["id"] and abs(sum(p[0] for p in q)/len(q)-cx) < 150]
        gf = min(4.2, H*0.4); fl = (H-gf)/max(lv-1, 1) if lv > 1 else H
        for i in range(n):
            a, c = P[i], P[(i+1)%n]; L = math.dist(a, c)
            mb.poly([(a[0],a[1],z0-0.5),(c[0],c[1],z0-0.5),(c[0],c[1],top),(a[0],a[1],top)], m)
            if L < 0.3: continue
            u = ((c[0]-a[0])/L, (c[1]-a[1])/L); nn = (u[1], -u[0])
            mid = (a[0]+u[0]*L/2+nn[0]*1.5, a[1]+u[1]*L/2+nn[1]*1.5)
            party = any(pip(mid, q) for q in others)
            # parapet coping + cornice (stand-in profile)
            mb.box((a[0]+u[0]*L/2+nn[0]*0.12, a[1]+u[1]*L/2+nn[1]*0.12), u, L+0.24, 0.35, 0.3, M["stone"] if sp["mat"] in ("brick","tile_green") else M["frame"], top)
            if sp.get("band"): mb.box((a[0]+u[0]*L/2+nn[0]*0.06, a[1]+u[1]*L/2+nn[1]*0.06), u, L, 0.14, 0.5, M[sp["band"]], z0+gf-0.25)
            if party or L < 4 or not sp["windows"] or sp.get("ruin") and H < 6: continue
            nb = max(1, int(L // sp["bay"])); bw = L/nb; ww = min(1.5, bw*0.55)
            front, _ = near_road(mid, 14)
            for k in range(nb):
                s0 = k*bw+(bw-ww)/2; s1 = s0+ww
                for f in range(1 if lv > 1 else 0, lv):
                    zb = z0+gf+(f-1)*fl+fl*0.25; zt = z0+gf+(f-1)*fl+fl*0.82
                    if zt > top-0.4: continue
                    mb.wallrect(a, u, nn, s0-0.08, s1+0.08, zb-0.08, zt+0.08, 0.02, M["frame"])
                    mb.wallrect(a, u, nn, s0, s1, zb, zt, 0.035, M["glass"])
                    mb.box((a[0]+u[0]*(s0+s1)/2+nn[0]*0.08, a[1]+u[1]*(s0+s1)/2+nn[1]*0.08), u, ww+0.25, 0.16, 0.07, M["stone"], zb-0.15)
                if sp["gf_shop"] and front < 14:     # shopfront bay: glazing, mullion, fascia
                    mb.wallrect(a, u, nn, k*bw+0.25, (k+1)*bw-0.25, z0+0.45, z0+gf-0.9, 0.04, M["shop"])
                    mb.box((a[0]+u[0]*k*bw+nn[0]*0.1, a[1]+u[1]*k*bw+nn[1]*0.1), u, 0.3, 0.2, gf, M["fascia"], z0)
                elif lv == 1 or front >= 14 or not sp["gf_shop"]:
                    mb.wallrect(a, u, nn, s0, s1, z0+0.9, z0+gf-0.6, 0.035, M["glass"])
            if sp["gf_shop"] and front < 14:
                mb.box((a[0]+u[0]*L/2+nn[0]*0.15, a[1]+u[1]*L/2+nn[1]*0.15), u, L, 0.3, 0.75, M["fascia"], z0+gf-0.85)
                mb.wallrect(a, u, nn, 0.4, L-0.4, z0+gf-0.75, z0+gf-0.2, 0.31, M["sign"])
            if sp.get("canopy") and front < 14 and L > 10:
                mb.box((a[0]+u[0]*L/2+nn[0]*1.5, a[1]+u[1]*L/2+nn[1]*1.5), u, min(L*0.6, 16), 3.0, 0.6, M["fascia"], z0+3.4)
        o = mb.build(CS); o["src"] = b.get("src"); o["levels_src"] = "OSM building:levels" if t.get("building:levels") else "stand-in (h/3.2)"; n_b += 1
    # shop signage anchors: one fascia sign per OSM shop node near a modelled frontage (name text in spec sheet)
    mb = MB("SURR_shop_signs")
    for p in shops:
        x, y = p["xy"]
        if math.hypot(x, y) > R_HI: continue
        HP = polys[HERO_ID]
        if pip((x, y), HP) or dline((x, y), HP+[HP[0]]) < 3: continue   # never dress the hero
        d, hit = near_road((x, y), 25)
        if not hit: continue
        r, a, c = hit; L = math.dist(a, c) or 1; u = ((c[0]-a[0])/L, (c[1]-a[1])/L)
        mb.box((x, y), u, 0.08, 0.6, 0.6, M["sign"], ground(x, y)+3.0)   # projecting blade sign (stand-in size)
    mb.build(CS); return n_b, removed
# ---------- viaduct: PBR brick swap, arch infill shopfronts on outer faces, coping, sleepers, OLE masts ----------
VW, SPAN, PW = G["VIADUCT_W"], G["VIADUCT_SPAN"], G["PIER_W"]
def viaduct(M):
    old = bpy.data.materials.get("Viaduct_brick")
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("viaduct"):
            for s in o.material_slots:
                if s.material == old: s.material = M["via"]
    vias = [r for r in SD["rails"] if r["k"] == "rail" and r.get("bridge") == "viaduct"]
    inf = MB("SURR_viaduct_infill"); cop = MB("SURR_viaduct_coping"); slp = MB("SURR_rail_sleepers"); ole = MB("SURR_OLE_masts")
    narch = 0
    for rl in vias:
        zz = sorted(z for z in rl["z"] if z is not None and 5 < z < 16); top = zz[len(zz)//2] if zz else 8.55
        others = [o["pts"] for o in vias if o is not rl]
        for i in range(len(rl["pts"])-1):
            a, b = rl["pts"][i], rl["pts"][i+1]; L = math.dist(a, b)
            if L < 0.5: continue
            mid = ((a[0]+b[0])/2, (a[1]+b[1])/2)
            if math.hypot(*mid) > R_MID: continue
            u = ((b[0]-a[0])/L, (b[1]-a[1])/L); nl = (-u[1], u[0]); g = min(ground(*a), ground(*b))
            for side in (-1, 1):
                nn = (nl[0]*side, nl[1]*side); fa = (a[0]+nn[0]*VW/2, a[1]+nn[1]*VW/2)
                cop.box((fa[0]+u[0]*L/2+nn[0]*0.15, fa[1]+u[1]*L/2+nn[1]*0.15), u, L, 0.42, 0.14, M["stone"], top+1.1)
                cop.box((fa[0]+u[0]*L/2+nn[0]*0.02, fa[1]+u[1]*L/2+nn[1]*0.02), u, L, 0.1, 0.25, M["stone"], top-0.6)  # string course (stand-in)
                probe = (mid[0]+nn[0]*(VW/2+1.0), mid[1]+nn[1]*(VW/2+1.0))
                if math.hypot(*mid) > R_HI or any(dline(probe, q) < VW/2 for q in others): continue   # inner face: hidden
                n = max(1, round(L/SPAN)); sp = L/n
                for k in range(n):
                    x0 = k*sp; x1 = x0+sp; w = max(1.0, sp-PW); r = w/2; spring = max(g+0.5, top-1.4-r); cx = x0+sp/2
                    off = -0.35; p = lambda t, z: (fa[0]+u[0]*t+nn[0]*off, fa[1]+u[1]*t+nn[1]*off, z)
                    inf.poly([p(cx-r, g), p(cx+r, g), p(cx+r, spring), p(cx-r, spring)] if side < 0 else [p(cx+r, g), p(cx-r, g), p(cx-r, spring), p(cx+r, spring)], M["shop"])
                    arc = [p(cx+r*math.cos(math.pi*j/12), spring+r*math.sin(math.pi*j/12)) for j in range(13)]
                    inf.poly(arc if side > 0 else arc[::-1], M["fascia"])
                    for t_ in (cx-r*0.35, cx+r*0.35): inf.box((p(t_, 0)[0]+nn[0]*0.05, p(t_, 0)[1]+nn[1]*0.05), u, 0.12, 0.1, spring-g, M["frame"], g)
                    inf.box((p(cx, 0)[0]+nn[0]*0.08, p(cx, 0)[1]+nn[1]*0.08), u, w-0.2, 0.12, 0.6, M["sign"], spring-0.7)
                    inf.box((p(cx, 0)[0]+nn[0]*0.06, p(cx, 0)[1]+nn[1]*0.06), u, 1.1, 0.08, 2.3, M["door"], g); narch += 1
            # sleepers (0.65 m spacing is UK standard-ish -> stand-in) and OLE masts every 55 m (stand-in)
            t = 0.3
            while t < L:
                c = (a[0]+u[0]*t, a[1]+u[1]*t); slp.box(c, nl, 2.5, 0.25, 0.12, M["sleeper"], top+0.22); t += 0.65
            t = 20.0
            while t < L:
                c = (a[0]+u[0]*t+nl[0]*2.6, a[1]+u[1]*t+nl[1]*2.6); ole.box(c, u, 0.3, 0.3, 7.0, M["galv"], top+0.25)
                ole.box((a[0]+u[0]*t+nl[0]*1.2, a[1]+u[1]*t+nl[1]*1.2), nl, 3.2, 0.12, 0.15, M["galv"], top+6.3)
                ole.box((a[0]+u[0]*t, a[1]+u[1]*t), u, 0.05, 0.05, 1.0, M["metal"], top+5.3); t += 55.0
    for mb in (inf, cop, slp, ole): mb.build(CS)
    return narch
# ---------- street: lamp columns, double yellows, crossings, signals, furniture ----------
def street(M):
    st = {}
    # lamps: OSM has 0 street_lamp nodes -> keep the existing stand-in positions, upgrade geometry
    lp = MB("SURR_lamp_columns"); lamps = [o for o in bpy.data.objects if o.name.startswith("lamp_post")]
    for o in lamps:
        bb = [o.matrix_world @ __import__("mathutils").Vector(v) for v in o.bound_box]; x = sum(v.x for v in bb)/8; y = sum(v.y for v in bb)/8; g = min(v.z for v in bb)
        d, hit = near_road((x, y), 20); r, a, c = hit if hit else (None, (0,0), (1,0))
        L = math.dist(a, c) or 1; u = ((c[0]-a[0])/L, (c[1]-a[1])/L); nn = (-u[1], u[0])
        if hit and ((x-a[0])*nn[0]+(y-a[1])*nn[1]) > 0: nn = (-nn[0], -nn[1])   # arm points to road
        lp.cyl(x, y, g, g+0.6, 0.12, 0.1, M["metal"]); lp.cyl(x, y, g+0.6, g+6.0, 0.08, 0.055, M["metal"])
        hx, hy = x+nn[0]*0.9, y+nn[1]*0.9; lp.box(((x+hx)/2, (y+hy)/2), nn, 0.9, 0.06, 0.06, M["metal"], g+5.95)
        lp.box((hx, hy), nn, 0.6, 0.28, 0.12, M["metal"], g+5.85); lp.box((hx, hy), nn, 0.5, 0.22, 0.03, M["lamp"], g+5.82)
    for o in [o for o in bpy.data.objects if o.name.startswith(("lamp_post", "lamp_head"))]: bpy.data.objects.remove(o)
    lp.build(CS); st["lamps(stand-in pos)"] = len(lamps)
    # double yellow lines along both kerbs of Whitworth St W (observed in Commons refs 4329092/5809790)
    ln = MB("SURR_road_lines")
    for r in SD["roads"]:
        if r["name"] != "Whitworth Street West" or r["k"] != "secondary": continue
        W = G["ROAD_W"]["secondary"]; pts = r["pts"]; nrm = G["normals"](pts)
        for sg in (-1, 1):
            for off in (W/2-0.35, W/2-0.55):
                for (p, q), (n1, n2) in zip(zip(pts, pts[1:]), zip(nrm, nrm[1:])):
                    if math.hypot(*p) > R_MID: continue
                    A_ = (p[0]+sg*off*n1[0], p[1]+sg*off*n1[1]); B_ = (q[0]+sg*off*n2[0], q[1]+sg*off*n2[1]); L = math.dist(A_, B_)
                    if L < 0.1: continue
                    u = ((B_[0]-A_[0])/L, (B_[1]-A_[1])/L); ln.box(((A_[0]+B_[0])/2, (A_[1]+B_[1])/2), u, L, 0.1, 0.02, M["yellow"], ground(*A_)+0.075)
    cnt = {}
    sig = MB("SURR_traffic_signals"); fur = MB("SURR_furniture")
    for f in SU["furniture"]:
        t = f["tags"]; x, y = f["xy"]; g = ground(x, y)
        if math.hypot(x, y) > R_MID: continue
        d, hit = near_road((x, y), 30); r, a, c = hit if hit else (None, (0,0), (1,0)); L = math.dist(a, c) or 1; u = ((c[0]-a[0])/L, (c[1]-a[1])/L); nn = (-u[1], u[0])
        W = G["ROAD_W"].get(r["k"], 6) if r else 6; key = None
        if t.get("highway") == "crossing" and hit and d < 3:
            if t.get("crossing") in ("marked", "zebra", "uncontrolled") or t.get("crossing_ref") == "zebra":
                for k in range(-3, 4): ln.box((x+u[0]*k*1.0, y+u[1]*k*1.0), nn, W-0.6, 0.5, 0.02, M["white"], g+0.075)
                key = "zebra"
            elif t.get("crossing") == "traffic_signals":
                for sgn in (-1.4, 1.4):
                    k = -W/2+0.3
                    while k < W/2-0.3: ln.box((x+u[0]*sgn+nn[0]*k, y+u[1]*sgn+nn[1]*k), nn, 0.25, 0.1, 0.02, M["white"], g+0.075); k += 0.6
                ln.box((x+u[0]*3.5, y+u[1]*3.5), nn, W/2, 0.3, 0.02, M["white"], g+0.075); key = "signal_crossing"
            else: key = "crossing_unmarked"
        elif t.get("highway") == "traffic_signals":
            for sgn in (-1, 1):
                px, py = x+nn[0]*sgn*(W/2+0.6), y+nn[1]*sgn*(W/2+0.6); gz = ground(px, py)
                sig.cyl(px, py, gz, gz+3.3, 0.06, 0.06, M["metal"]); sig.box((px, py), u, 0.3, 0.25, 0.9, M["metal"], gz+2.3)
                for j, mm in enumerate((M["sig_g"], M["fascia"], M["sig_r"])): sig.box((px+u[0]*0.0+nn[0]*0.13*-sgn, py+u[1]*0.0+nn[1]*0.13*-sgn), u, 0.18, 0.02, 0.18, mm, gz+2.38+j*0.28)
                sig.cyl(px, py, gz+0.9, gz+1.2, 0.07, 0.07, M["fascia"])   # push-button unit
            key = "traffic_signals"
        elif t.get("highway") == "bus_stop":
            fur.cyl(x, y, g, g+2.8, 0.04, 0.04, M["galv"]); fur.box((x, y), u, 0.45, 0.04, 0.45, M["sign"], g+2.4)
            if t.get("shelter") == "yes":
                for s0 in (-1.6, 1.6): fur.box((x+u[0]*s0+nn[0]*1.0, y+u[1]*s0+nn[1]*1.0), u, 0.08, 1.4, 2.4, M["shop"], g)
                fur.box((x+nn[0]*1.6, y+nn[1]*1.6), u, 3.3, 0.05, 2.4, M["shop"], g); fur.box((x+nn[0]*1.0, y+nn[1]*1.0), u, 3.4, 1.5, 0.08, M["galv"], g+2.4)
            key = "bus_stop"
        elif t.get("amenity") == "bench": fur.box((x, y), u, 1.8, 0.45, 0.45, M["metal"], g); fur.box((x+nn[0]*0.2, y+nn[1]*0.2), u, 1.8, 0.06, 0.45, M["metal"], g+0.45); key = "bench"
        elif t.get("amenity") == "waste_basket": fur.cyl(x, y, g, g+0.95, 0.25, 0.27, M["metal"]); key = "waste_basket"
        elif t.get("amenity") == "post_box": fur.cyl(x, y, g, g+1.5, 0.27, 0.27, M["red"], 12); fur.cyl(x, y, g+1.5, g+1.62, 0.3, 0.2, M["red"], 12); key = "post_box"
        elif t.get("amenity") == "bicycle_parking":
            for k in range(-1, 2):
                for s_ in (-0.35, 0.35): fur.box((x+u[0]*k*1.0+nn[0]*s_, y+u[1]*k*1.0+nn[1]*s_), u, 0.05, 0.05, 0.8, M["galv"], g)
                fur.box((x+u[0]*k*1.0, y+u[1]*k*1.0), nn, 0.75, 0.05, 0.05, M["galv"], g+0.8)
            key = "bicycle_parking"
        elif t.get("barrier") == "bollard": fur.cyl(x, y, g, g+1.0, 0.1, 0.1, M["metal"]); key = "bollard"
        elif t.get("amenity") in ("telephone", "atm", "vending_machine"): fur.box((x, y), u, 1.0, 0.5, 2.3, M["fascia"], g); key = t["amenity"]
        if key: cnt[key] = cnt.get(key, 0)+1
    ln.build(CS); sig.build(CS); fur.build(CS); st.update(cnt); return st
# ---------- trees from LIDAR (DSM-DTM blobs) replacing OSM-node trees inside 250 m ----------
def trees(M):
    rm = 0
    for o in [o for o in bpy.data.objects if o.name.startswith(("tree_trunk", "tree_crown"))]:
        bb = [o.matrix_world @ __import__("mathutils").Vector(v) for v in o.bound_box]
        if math.hypot(sum(v.x for v in bb)/8, sum(v.y for v in bb)/8) < R_MID: bpy.data.objects.remove(o); rm += 1
    tr = MB("SURR_trees_trunks"); n = 0; cols = []
    for t in SU["trees_lidar"]:
        if t["height"] < 4 or t["px"] < 10 or math.hypot(*t["xy"]) > R_MID: continue
        x, y = t["xy"]; dr, hit = near_road((x, y), 12)
        if hit and dr < G["ROAD_W"].get(hit[0]["k"], 6)/2: continue   # blob on carriageway = vehicle, not tree
        if t["height"] > 25 or (t["height"] > 12 and min(dline((x, y), b["pts"]) for b in SD["buildings"] if abs(b["pts"][0][0]-x) < 200) < 5): continue   # facade overhang / roof edge, not tree
        g = ground(x, y); h = t["height"]; cr = max(1.2, t["canopy_d"]/2)
        tr.cyl(x, y, g, g+h*0.55, 0.06+h*0.012, 0.04+h*0.006, M["bark"], 7)
        for k in range(3):   # main limbs
            ang = 2*math.pi*k/3+random.random(); tr.cyl(x, y, g+h*0.4, g+h*0.65, 0.05, 0.03, M["bark"], 5) if False else None
        lo = g+max(2.2, h-2*cr*0.85); cols.append((x, y, lo, h+g, cr, t["osm_match"])); n += 1
    tr.build(CS)
    tx = bpy.data.textures.get("surr_leafN") or bpy.data.textures.new("surr_leafN", "VORONOI"); tx.noise_scale = 0.35
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0); base = bpy.context.object; me = base.data; bpy.data.objects.remove(base)
    # crowns as one mesh with displaced clumps (baked by joining linked copies is heavy; use MB of jittered icospheres)
    cm = MB("SURR_trees_crowns"); V = [v.co.copy() for v in me.vertices]; F = [list(p.vertices) for p in me.polygons]
    for x, y, lo, hi, cr, om in cols:
        for k in range(5):
            r = cr*(0.55+0.25*random.random()); ox = (random.random()-0.5)*cr*0.9; oy = (random.random()-0.5)*cr*0.9
            oz = lo+(hi-lo)*(0.35+0.4*random.random()); m = M["leaf"] if k % 2 else M["leaf2"]
            b0 = len(cm.v)
            for v in V:
                j = 1+0.22*(math.sin(v.x*7.1+k)*math.sin(v.y*6.3+x)*math.sin(v.z*5.7+y))
                cm.v.append((x+ox+v.x*r*j, y+oy+v.y*r*j, oz+v.z*r*0.85*j))
            for f in F: cm.f.append([b0+i for i in f]); cm.mi.append(cm.mat(m))
    o = cm.build(CS); [setattr(p_, "use_smooth", True) for p_ in o.data.polygons]; bpy.data.meshes.remove(me); return n, rm
# ---------- canal: rippled water + railings (railing line = stand-in offset) ----------
def canal(M):
    for m in bpy.data.materials:
        if m.name.startswith("Canal_water") and m.use_nodes and not m.get("surr_ripple"):
            nt = m.node_tree; b = nt.nodes["Principled BSDF"]; nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
            bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.05; nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
            b.inputs["Base Color"].default_value = (0.025, 0.035, 0.03, 1); b.inputs["Roughness"].default_value = 0.03; m["surr_ripple"] = 1   # x_tricks #10 Blender path
    rl = MB("SURR_canal_railings"); n = 0
    for w in SD["water"]:
        if w["k"] != "canal" or w["closed"]: continue
        pts = w["pts"]
        for sg in (1,):
            for a, b in zip(pts, pts[1:]):
                L = math.dist(a, b)
                if L < 0.5 or math.hypot((a[0]+b[0])/2, (a[1]+b[1])/2) > R_HI+30: continue
                u = ((b[0]-a[0])/L, (b[1]-a[1])/L); nn = (-u[1]*sg, u[0]*sg); o = 3.4
                A_ = (a[0]+nn[0]*o, a[1]+nn[1]*o); g = ground(*A_)
                rl.box((A_[0]+u[0]*L/2, A_[1]+u[1]*L/2), u, L, 0.05, 0.05, M["metal"], g+1.05)
                rl.box((A_[0]+u[0]*L/2, A_[1]+u[1]*L/2), u, L, 0.04, 0.04, M["metal"], g+0.15)
                t = 0.0
                while t < L: rl.box((A_[0]+u[0]*t, A_[1]+u[1]*t), u, 0.05, 0.05, 1.1, M["metal"], g); t += 2.0; n += 1
    rl.build(CS); return n
if __name__ == "__main__":
    M = M_(); rep = {}
    if ON("bldg"): rep["buildings_detailed,removed_old"] = buildings(M)
    if ON("via"): rep["viaduct_arch_infills"] = viaduct(M)
    if ON("street"): rep["street"] = street(M)
    if ON("trees"): rep["trees_lidar,removed_old"] = trees(M)
    if ON("canal"): rep["canal_railing_posts"] = canal(M)
    print("SURR REPORT", json.dumps(rep))
    sv = arg("--save")
    if sv:
        assert not os.path.abspath(sv).endswith("out/barclay_scene.blend"), "refuse to overwrite master"
        bpy.ops.wm.save_as_mainfile(filepath=sv, copy=True)
    if "--render" in A:
        sc = bpy.context.scene; r = sc.render; rx, ry = (int(v) for v in arg("--res", "960x540").split("x")); r.resolution_x, r.resolution_y = rx, ry; r.resolution_percentage = 100
        sc.cycles.samples = int(arg("--samples", 48)); sc.cycles.device = "CPU"; r.threads_mode = "FIXED"; r.threads = 8
        import mathutils
        def cam(name, loc, look, lens):
            c = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.cameras.new(name))
            if c.name not in sc.collection.objects: sc.collection.objects.link(c)
            c.location = loc; c.rotation_euler = (mathutils.Vector(look)-mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler(); c.data.lens = lens; return c
        cams = {"street": bpy.data.objects["Cam_Street"], "viaduct": bpy.data.objects["Cam_Viaduct"], "aerial": bpy.data.objects["Cam_Aerial"],
                "wsw_east": cam("Cam_Surr_WSW_east", (-30, -27.5, 1.7), (60, -12, 4), 20), "wsw_west": cam("Cam_Surr_WSW_west", (70, -10, 1.7), (-40, -28, 5), 20)}
        outd = HERE+"/out/surroundings_preview"; os.makedirs(outd, exist_ok=True)
        for k in arg("--cams", "wsw_east,wsw_west,street,viaduct,aerial").split(","):
            sc.camera = cams[k]; r.filepath = f"{outd}/surr_{k}_{rx}x{ry}.tmp.png"; bpy.ops.render.render(write_still=True)
            os.replace(r.filepath, r.filepath.replace(".tmp.png", ".png")); print("RENDERED", k)
