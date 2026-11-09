"""Locked-camera before/after stills for x_tricks #9 (life) + #10 (canal ripple). Run on a COPY:
blender -b -y tests/streetwater_copy.blend (must sit one level below the repo so //../textures resolves) -P tests/streetwater/stills.py -- --res 1280x720 --samples 32 --t 3"""
import bpy, os, sys, json, math, time
from mathutils import Vector
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, R)
import life_paths, water_ripple
A = sys.argv[sys.argv.index("--")+1:]; arg = lambda k, d: A[A.index(k)+1] if k in A else d
res, spp, T = arg("--res", "1280x720"), int(arg("--samples", 32)), float(arg("--t", 3)); OUT = os.path.join(R, "tests", "streetwater")
print("CAM_STREET", tuple(round(v, 2) for v in bpy.data.objects["Cam_Street"].location))
sc = bpy.context.scene; m = bpy.data.texts["barclay_tod.py"].as_module(); m.set_preset(sc, "midday"); m.apply(None, bpy.context)
sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in res.split("x")); sc.render.resolution_percentage = 100
sc.cycles.samples = spp; sc.cycles.use_denoising = True; sc.render.image_settings.file_format = "PNG"
# locked canal camera: nearest spot to the hero with open sky above, canal directly below and canal 25 m ahead (deterministic, data-only)
dg = bpy.context.evaluated_depsgraph_get(); pick = None; Wn = [o for o in bpy.data.objects if o.name.startswith("canal_")]
def on_water(p):
    h = sc.ray_cast(dg, p + Vector((0, 0, 60)), Vector((0, 0, -1))); return h[0] and h[4] in Wn, (h[1].z if h[0] else 0)
cand = sorted({(round(v.x), round(v.y)) for o in Wn for v in [o.matrix_world @ q.co for q in o.data.vertices] if abs(v.x) < 400 and abs(v.y) < 400}, key=lambda q: q[0]**2 + q[1]**2)
for (x, y) in cand:
    for dx, dy in ((0, 0), (2, 2), (-2, -2), (3, -3), (-3, 3)):
        ok, z = on_water(Vector((x + dx, y + dy, 0)))
        if not ok: continue
        p = Vector((x + dx, y + dy, z + 2.0))
        if sc.ray_cast(dg, p, Vector((0, 0, 1)))[0]: continue
        for a in range(0, 360, 15):
            d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0)); tg = p + d*25; ok2, z2 = on_water(tg)
            if ok2 and not sc.ray_cast(dg, p, (Vector((tg.x, tg.y, z2)) - p).normalized(), distance=(Vector((tg.x, tg.y, z2)) - p).length - 0.5)[0]:
                pick = (p, Vector((tg.x, tg.y, z2))); break
        if pick: break
    if pick: break
cc = bpy.data.objects.new("Cam_Canal_test", bpy.data.cameras.new("Cam_Canal_test")); sc.collection.objects.link(cc); cc.data.lens = 24
cc.location = pick[0]; cc.rotation_euler = (pick[1] - cc.location).to_track_quat("-Z", "Y").to_euler()
if "--camonly" in A: json.dump([list(pick[0]), list(pick[1])], open(os.path.join(OUT, "canal_cam.json"), "w")); print("CAM", pick); sys.exit(0)
if os.path.exists(os.path.join(OUT, "canal_cam.json")):   # reuse the locked camera across runs/blends
    c0, t0_ = json.load(open(os.path.join(OUT, "canal_cam.json"))); cc.location = Vector(c0); cc.rotation_euler = (Vector(t0_) - cc.location).to_track_quat("-Z", "Y").to_euler(); pick = (Vector(c0), Vector(t0_))
CAMS = {"street": bpy.data.objects["Cam_Street"], "canal": cc}
cl = bpy.data.objects.new("Cam_Life_test", bpy.data.cameras.new("Cam_Life_test")); sc.collection.objects.link(cl); cl.data.lens = 24   # locked: street level west of the hero, looking at road + viaduct
cl.location = Vector((-60.0, -14.0, 1.7)); cl.rotation_euler = (Vector((0.0, -28.0, 5.0)) - cl.location).to_track_quat("-Z", "Y").to_euler()
T2 = float(arg("--t2", 5))
log = {"res": res, "samples": spp, "t_life": T, "canal_cam": [list(cc.location), list(pick[1])]}
def shoot(tag):
    for k, c in CAMS.items():
        sc.camera = c; sc.render.filepath = os.path.join(OUT, f"{tag}_{k}_{res}.png"); t0 = time.time()
        bpy.ops.render.render(write_still=True); log[f"{tag}_{k}_s"] = round(time.time() - t0, 1)
tag0 = arg("--tag", "before")
if "--afteronly" not in A: shoot(tag0)
if "--baseonly" in A: json.dump(log, open(os.path.join(OUT, f"stills_log_{tag0}.json"), "w"), indent=1); sys.exit(0)
log["ripple_applied"] = water_ripple.ripple(bpy.data.materials["Canal_water"])
act = life_paths.setup(sc); log["clip"] = life_paths.clip_check(act, [i*0.5 for i in range(27)]); life_paths.update(act, T, sc)
log["actors"] = {a["name"]: [list(map(lambda v: round(v, 2), r.location)) for r in a["parts"]] for a in act}
shoot("after")
if "--life" in A:   # x_tricks #9: same locked life camera with and without actors, at t2
    sc.camera = cl
    for a_ in act:
        for r in a_["parts"]:
            r.hide_render = True
            for c in r.children_recursive: c.hide_render = True
    sc.render.filepath = os.path.join(OUT, f"before_life_{res}.png"); bpy.ops.render.render(write_still=True)
    life_paths.update(act, T2, sc); log["actors_t2"] = {a["name"]: [[round(v, 2) for v in r.location] + [not r.hide_render] for r in a["parts"]] for a in act}
    sc.render.filepath = os.path.join(OUT, f"after_life_{res}.png"); bpy.ops.render.render(write_still=True)
json.dump(log, open(os.path.join(OUT, "stills_log.json"), "w"), indent=1); print("STILLS_DONE", json.dumps(log)[:800])
