# Barclay House exterior scene - Blender 4.x, free/open only. Run:
#   blender -b -P build_scene.py -- [--render]
# Parses area.geojson (OSM, ODbL (c) OpenStreetMap contributors) with a local-metre projection.
import bpy, json, math, os, sys
# ---------------- HERO PARAMETERS (replace with Colin's CONFIRMED values) ----------------
HERO_OSM_ID   = "100646649"   # OSM way for Barclay House footprint
HERO_FOOTPRINT = None         # None = use OSM outline (~995 m2, ESTIMATED); or list of (x,y) metres
HERO_STOREYS  = 5             # CONFIRMED (WSP planning statement 2021)
HERO_FLOOR_H  = 4.2           # ESTIMATED (early-20th-c warehouse, double-height ground arches)
HERO_HEIGHT   = None          # metres; None = storeys*floor_h (ESTIMATED ~21 m)
DEFAULT_LEVEL_H = 3.2         # ESTIMATED storey height for neighbours
DEFAULT_LEVELS  = 4           # ESTIMATED when OSM has no levels/height
VIADUCT_DECK_H  = 8.0         # ESTIMATED rail viaduct deck height (verify with EA LIDAR DSM)
RES = tuple(int(v) for v in os.environ.get("BRES","4096x2304").split("x")); SAMPLES = int(os.environ.get("BSAMPLES",512))
HDRI = os.path.join(os.path.dirname(__file__), "hdri.exr")  # e.g. Poly Haven CC0 HDRI
LAT0, LON0 = 53.47415, -2.24419
# -----------------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
def xy(lon, lat):
    return ((lon-LON0)*111320*math.cos(math.radians(LAT0)), (lat-LAT0)*110540)
def num(v):
    try: return float(str(v).split()[0].replace('m',''))
    except: return None
def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m  # PBR slot: swap in ambientCG/Poly Haven CC0 textures here
def make_mats():
  return {"hero": mat("HERO_facade_PBR", (0.55,0.30,0.22)), "bldg": mat("Building_PBR", (0.6,0.58,0.55)),
          "road": mat("Asphalt_PBR", (0.08,0.08,0.08), .9), "path": mat("Paving_PBR", (0.4,0.4,0.38)),
          "rail": mat("RailBallast_PBR", (0.25,0.22,0.2)), "viaduct": mat("BrickViaduct_PBR", (0.45,0.22,0.15)),
          "ground": mat("Ground_PBR", (0.3,0.3,0.28)), "water": mat("Water", (0.05,0.08,0.08), .05)}
def coll(n):
    c = bpy.data.collections.new(n); bpy.context.scene.collection.children.link(c); return c
def mesh_obj(name, verts, faces, m, c):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); o.data.materials.append(m); c.objects.link(o); return o
def extrude(name, pts, h, m, c, z0=0.0):
    if pts[0] == pts[-1]: pts = pts[:-1]
    n = len(pts)
    a = sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1] for i in range(n))
    if a < 0: pts = pts[::-1]
    v = [(x,y,z0) for x,y in pts] + [(x,y,z0+h) for x,y in pts]
    f = [list(range(n))[::-1], list(range(n, 2*n))] + [[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
    return mesh_obj(name, v, f, m, c)
def ribbon(name, pts, w, m, c, z=0.02, solid=0.0):
    v, f = [], []
    for i,(x,y) in enumerate(pts):
        a = pts[max(i-1,0)]; b = pts[min(i+1,len(pts)-1)]
        dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx,dy) or 1
        nx, ny = -dy/L*w/2, dx/L*w/2
        v += [(x+nx,y+ny,z),(x-nx,y-ny,z)]
    for i in range(len(pts)-1): f.append([2*i,2*i+1,2*i+3,2*i+2])
    o = mesh_obj(name, v, f, m, c)
    if solid:
        s = o.modifiers.new("solid","SOLIDIFY"); s.thickness = solid
    return o
ROAD_W = {"primary":10,"secondary":9,"tertiary":8,"residential":6,"unclassified":6,"service":4,
          "pedestrian":5,"footway":2,"cycleway":2,"steps":2,"trunk":12,"living_street":5}
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global M; M = make_mats()
    sc = bpy.context.scene
    gj = json.load(open(os.path.join(HERE, "area.geojson")))
    CB, CR, CT, CH = coll("Buildings"), coll("Roads"), coll("Rail"), coll("Hero")
    for ft in gj["features"]:
        p, g = ft["properties"], ft["geometry"]
        cs = g["coordinates"][0] if g["type"]=="Polygon" else g["coordinates"]
        pts = [xy(*c) for c in cs]
        oid = p.get("osm_id")
        if "building" in p and g["type"]=="Polygon":
            if oid == HERO_OSM_ID:
                fp = HERO_FOOTPRINT or pts
                h = HERO_HEIGHT or HERO_STOREYS*HERO_FLOOR_H
                o = extrude("HERO_BarclayHouse", fp, h, M["hero"], CH); o["height_status"]="ESTIMATED" if HERO_HEIGHT is None else "CONFIRMED"
                continue
            h = num(p.get("height")); st = "OSM height"
            if h is None and p.get("building:levels"): h = num(p["building:levels"])*DEFAULT_LEVEL_H; st = "ESTIMATED from levels"
            if h is None: h = DEFAULT_LEVELS*DEFAULT_LEVEL_H; st = "ESTIMATED default"
            z0 = (num(p.get("min_height")) or 0)
            o = extrude("bldg_"+oid, pts, max(h-z0,1), M["bldg"], CB, z0); o["height_status"] = st
        elif p.get("highway") in ROAD_W and g["type"]=="LineString":
            k = p["highway"]; ribbon("road_"+oid, pts, ROAD_W[k], M["path" if k in("footway","pedestrian","steps","cycleway") else "road"], CR, 0.02 + (VIADUCT_DECK_H if p.get("bridge")=="yes" and p.get("layer","0")>"1" else 0))
        elif p.get("railway") in ("rail","light_rail","tram") and g["type"]=="LineString":
            if p.get("bridge") in ("viaduct","yes"):
                ribbon("viaduct_"+oid, pts, 9, M["viaduct"], CT, VIADUCT_DECK_H, solid=VIADUCT_DECK_H)
                # TODO arches: add Array modifier of arch cutter (Boolean) along viaduct for hero shots
            else:
                ribbon("rail_"+oid, pts, 4, M["rail"], CT, 0.1)
        elif (p.get("waterway") or p.get("water")) and g["type"]=="LineString" and p.get("waterway")=="canal":
            ribbon("canal_"+oid, pts, 9, M["water"], CR, 0.01)
    bpy.ops.mesh.primitive_plane_add(size=1000, location=(0,0,0)); gnd = bpy.context.object
    gnd.name="Ground"; gnd.data.materials.append(M["ground"])
    # Lighting: HDRI if present else Nishita sky + sun
    w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes["Background"]
    if os.path.exists(HDRI):
        e = nt.nodes.new("ShaderNodeTexEnvironment"); e.image = bpy.data.images.load(HDRI)
        nt.links.new(e.outputs[0], bg.inputs[0])
    else:
        s = nt.nodes.new("ShaderNodeTexSky"); s.sky_type="NISHITA"; s.sun_elevation=math.radians(35)
        nt.links.new(s.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.25
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun","SUN")); sun.data.energy=3
    sun.rotation_euler=(math.radians(50),0,math.radians(200)); sc.collection.objects.link(sun)
    # Camera: street-level hero view from south-east across Whitworth St W
    cam = bpy.data.objects.new("Cam_Hero", bpy.data.cameras.new("Cam_Hero")); cam.data.lens=24
    cam.location=(10,-28,1.7)  # ESTIMATED: on Whitworth St W pavement, adjust; sc.collection.objects.link(cam)
    tgt = bpy.data.objects.new("CamTarget", None); tgt.location=(0,0,10); sc.collection.objects.link(tgt)
    tc = cam.constraints.new("TRACK_TO"); tc.target=tgt; sc.camera=cam
    cam2 = bpy.data.objects.new("Cam_Aerial", bpy.data.cameras.new("Cam_Aerial")); cam2.location=(180,-220,160)
    sc.collection.objects.link(cam2); t2=cam2.constraints.new("TRACK_TO"); t2.target=tgt
    if os.environ.get("BCAM")=="aerial": sc.camera=cam2
    r = sc.render; r.engine="CYCLES"; r.resolution_x, r.resolution_y = RES; r.resolution_percentage=100
    sc.cycles.samples=SAMPLES; sc.cycles.use_denoising=True
    sc.view_settings.view_transform="AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else "Filmic"
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "barclay_scene.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "barclay_scene.glb"))
    try: bpy.ops.export_scene.fbx(filepath=os.path.join(out, "barclay_scene.fbx"))
    except Exception as ex: print("FBX export skipped:", ex)
    if "--render" in sys.argv:
        r.filepath = os.path.join(out, "hero_"); bpy.ops.render.render(write_still=True)
    print("OK objects:", len(bpy.data.objects))
main()
