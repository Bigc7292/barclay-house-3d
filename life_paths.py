"""life_paths.py - x_tricks #9 'street life' (method from https://x.com/uncle_render/status/2117240312439742479; their paid kit NOT used).
Moving car, train and pedestrians on REAL OSM geometry from scene_data.json (OSM (c) contributors, ODbL), heights by ray-casting
the scene's own road / viaduct-deck meshes (LIDAR-derived). Motion is a PURE function of t (no hand keyframes), like flythrough.py.
Assets: Kenney CC0 (assets/life/kenney/*/License.txt): car-kit, train-kit, mini-characters. Sizes/speeds = STAND-INS (illustrative set
dressing, not building facts). Poly Haven (CC0) checked: no moving vehicles/people available, none used.
Use from flythrough.py --life, or:  blender -b -y tests/x.blend -P life_paths.py -- --t 3 --check
"""
import bpy, json, math, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); K = os.path.join(HERE, "assets", "life", "kenney")
# OSM way chains (ids from scene_data.json); order = direction of travel
CAR_WAYS = ["171648623", "1417881765", "1417881764", "155768981"]   # Whitworth Street West, eastern end -> west past the hero
TRAIN_WAYS = ["427155418", "31179674"]                              # viaduct rail: west -> east, joins at (-0.8, -35.71)
WALK_WAYS = ["1423359051"]                                          # footway on the hero frontage
# STAND-INS (illustrative): speeds m/s, scales, lane offset; t when each actor passes the hero (x ~ -6 m)
ACTORS = [  # name, kind, asset, ways, speed, side offset m (+ = left of travel), pass time s, scale, length stretch
    ("LIFE_car_1", "car", "car-kit/sedan.glb", CAR_WAYS, 9.0, 1.8, 8.0, 1.46, 1.0),     # westbound, left (south) lane
    ("LIFE_car_2", "car", "car-kit/van.glb",   CAR_WAYS, -9.0, -1.8, 2.78, 1.30, 1.0),   # eastbound (negative speed), north lane
    ("LIFE_train", "train", ["train-kit/train-electric-city-a.glb", "train-kit/train-electric-city-b.glb", "train-kit/train-electric-city-c.glb"],
        TRAIN_WAYS, 12.0, 0.0, 6.0, 2.5, 2.8),
    ("LIFE_walker_1", "walk", "mini-characters/character-male-a.glb",   WALK_WAYS, 1.3, 0.6, 2.0, 2.6, 1.0),
    ("LIFE_walker_2", "walk", "mini-characters/character-female-b.glb", WALK_WAYS, -1.2, -0.7, 4.0, 2.6, 1.0),
    ("LIFE_walker_3", "walk", "mini-characters/character-male-c.glb",   WALK_WAYS, 1.1, -0.2, 7.0, 2.6, 1.0),
]
HERO_X = -6.0

def chain(ids, D):
    W = {w["id"]: w for w in D["roads"] + D["rails"]}; pts = []
    for i in ids:
        p = [tuple(q) for q in W[i]["pts"]]
        if pts and math.dist(pts[-1], p[-1]) < math.dist(pts[-1], p[0]): p = p[::-1]
        pts += p if not pts or math.dist(pts[-1], p[0]) > 0.01 else p[1:]
    return pts

class Path:
    """Arc-length polyline, sampled every 1 m with ground z from a ray cast onto allowed surfaces."""
    def __init__(self, pts, side, hit_ok, sc):
        self.s = [0.0]
        for a, b in zip(pts, pts[1:]): self.s.append(self.s[-1] + math.dist(a, b))
        self.pts, self.side, self.L = pts, side, self.s[-1]
        dg = bpy.context.evaluated_depsgraph_get(); self.z = []
        for i in range(int(self.L) + 2):
            x, y = self.xy(float(i)); self.z.append(ray_z(sc, dg, x, y, hit_ok))
        zs = [z for z in self.z if z is not None]; med = sorted(zs)[len(zs)//2] if zs else 0.0
        self.z = [med if z is None else z for z in self.z]
    def seg(self, s):
        s = max(0.0, min(self.L, s))
        for i in range(len(self.s) - 1):
            if s <= self.s[i+1] or i == len(self.s) - 2: return i, (s - self.s[i]) / max(1e-6, self.s[i+1] - self.s[i])
    def tan(self, s):
        i, _ = self.seg(s); a, b = self.pts[i], self.pts[i+1]; d = Vector((b[0]-a[0], b[1]-a[1], 0)); return d.normalized()
    def xy(self, s):
        i, u = self.seg(s); a, b = self.pts[i], self.pts[i+1]; t = self.tan(s)
        return a[0] + (b[0]-a[0])*u - t.y*self.side, a[1] + (b[1]-a[1])*u + t.x*self.side
    def at(self, s):
        x, y = self.xy(s); k = max(0.0, min(len(self.z) - 1.001, max(0.0, min(self.L, s)))); i = int(k)
        z = self.z[i]*(1-(k-i)) + self.z[i+1]*(k-i); return Vector((x, y, z)), self.tan(s)
    def s_at_x(self, x):   # first arc length where the centre line crosses world x
        for i, (a, b) in enumerate(zip(self.pts, self.pts[1:])):
            if (a[0]-x)*(b[0]-x) <= 0 and a[0] != b[0]: return self.s[i] + (self.s[i+1]-self.s[i])*(x-a[0])/(b[0]-a[0])
        return self.L/2

def ray_z(sc, dg, x, y, ok):
    o = Vector((x, y, 300.0))
    for _ in range(12):
        hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg, o, Vector((0, 0, -1)))
        if not hit: return None
        if ok(ob): return loc.z
        o = loc - Vector((0, 0, 0.01))
    return None

def in_col(ob, name): return any(c.name == name for c in ob.users_collection)
HIT = {"car": lambda o: in_col(o, "Roads_Terrain_Water") and not o.name.startswith(("canal", "water")),
       "walk": lambda o: in_col(o, "Roads_Terrain_Water") and not o.name.startswith(("canal", "water")),
       "train": lambda o: o.name.endswith("_deck") or "_deck" in o.name}

def load(rel, name, scale, stretch, col):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(K, rel))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type == "MESH" and o.name.startswith("Icosphere"): bpy.data.objects.remove(o)   # Kenney helper sphere
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); col.objects.link(root)
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None: o.parent = root
    root.scale = (scale, scale*stretch, scale); return root, new

def length_y(root):
    inv = root.matrix_world.inverted(); ys = [(inv @ (m.matrix_world @ Vector(c))).y for m in root.children_recursive if m.type == "MESH" for c in m.bound_box]
    return (max(ys) - min(ys)) * root.scale.y if ys else 0.0

def setup(sc=None):
    """Create LIFE_* actors once (idempotent: re-uses an existing LIFE collection). Returns actor list for update()."""
    sc = sc or bpy.context.scene; D = json.load(open(os.path.join(HERE, "scene_data.json")))
    col = bpy.data.collections.get("LIFE")
    if col:   # rebuild cleanly
        for o in list(col.objects): bpy.data.objects.remove(o)
    else: col = bpy.data.collections.new("LIFE"); sc.collection.children.link(col)
    paths, actors = {}, []
    for name, kind, asset, ways, v, side, tpass, scale, stretch in ACTORS:
        key = (tuple(ways), side)
        if key not in paths: paths[key] = Path(chain(ways, D), side, HIT[kind], sc)
        P = paths[key]; s_pass = P.s_at_x(HERO_X)
        parts = []
        for j, a in enumerate(asset if isinstance(asset, list) else [asset]):
            r, objs = load(a, f"{name}_{j}", scale, stretch, col); parts.append(r)
            for o in objs:
                if o.type == "ARMATURE" and kind == "walk":
                    act = next((x for x in bpy.data.actions if x.name.startswith("walk_") and o.name.split(".")[0] in x.name), None) or \
                          next((x for x in bpy.data.actions if x.name.startswith("walk_")), None)
                    if act:
                        o.animation_data_create(); o.animation_data.action = None
                        tr = o.animation_data.nla_tracks.new(); st = tr.strips.new("walk", 1 + int(tpass*7) % 13, act); st.repeat = 200
        bpy.context.view_layer.update(); gap = max(length_y(r) for r in parts) + 0.6   # carriage spacing from the model's real extent
        actors.append(dict(name=name, kind=kind, P=P, v=v, s0=s_pass - v*tpass, parts=parts, gap=gap))
    return actors

def update(actors, t, sc=None):
    """Pure: place every actor for time t (seconds). Walk cycles follow the scene frame (24 fps)."""
    sc = sc or bpy.context.scene; sc.frame_set(1 + int(round(t*24)))   # first, so existing fcurves can't overwrite the poses below
    for a in actors:
        for j, r in enumerate(a["parts"]):
            s = a["s0"] + a["v"]*t - j*a["gap"]*(1 if a["v"] >= 0 else -1)
            p, d = a["P"].at(s); d = d if a["v"] >= 0 else -d
            r.location = p; r.rotation_euler = d.to_track_quat("-Y", "Z").to_euler()   # Kenney models face -Y after glTF import
            r.hide_render = r.hide_viewport = not (0 <= s <= a["P"].L)
            for c in r.children_recursive: c.hide_render = r.hide_render

def clip_check(actors, times, sc=None):
    """Return list of (t, actor, object) where an actor mesh overlaps hero, viaduct piers/parapets/arches or lamps."""
    sc = sc or bpy.context.scene; bad = []
    obst = [o for o in sc.objects if o.type == "MESH" and (in_col(o, "Hero") or any(k in o.name for k in ("_pier", "_parapet", "_arch", "_spring", "Lamp", "lamp")))
            and not in_col(o, "HERO_cutters")]
    for t in times:
        update(actors, t, sc); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        for a in actors:
            for r in a["parts"]:
                if r.hide_render: continue
                for m in [c for c in r.children_recursive if c.type == "MESH"]:
                    e = m.evaluated_get(dg); me = e.to_mesh(); V = [m.matrix_world @ v.co for v in me.vertices]; F = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
                    if not V: continue
                    lo = Vector([min(v[i] for v in V) for i in range(3)]); hi = Vector([max(v[i] for v in V) for i in range(3)]); A = BVHTree.FromPolygons(V, F)
                    for o in obst:
                        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
                        if any(max(b[i] for b in bb) < lo[i] or min(b[i] for b in bb) > hi[i] for i in range(3)): continue
                        if A.overlap(BVHTree.FromObject(o, dg)): bad.append((t, a["name"], o.name))
    return bad

if __name__ == "__main__":
    import argparse
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(); ap.add_argument("--t", type=float, default=3.0); ap.add_argument("--check", action="store_true"); ap.add_argument("--save")
    a = ap.parse_args(A); act = setup()
    if a.check:
        bad = clip_check(act, [i*0.5 for i in range(27)]); print("LIFE_CLIP", len(bad), sorted(set((b[1], b[2]) for b in bad))[:20])
    update(act, a.t)
    for x in act: print("LIFE", x["name"], "path_m", round(x["P"].L, 1), "loc", [tuple(round(c, 2) for c in r.location) for r in x["parts"]], "visible", [not r.hide_render for r in x["parts"]])
    if a.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save), copy=True)
