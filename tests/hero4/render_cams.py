# blender -b -y <blend> -P tests/hero4/render_cams.py -- --out DIR --prefix P --cams street,facade,entrance,viaduct --res 1920x1080 --samples 64 [--camfile cams.json]
# Read-only on the blend (never saves). Adds Cam_Facade / Cam_Entrance in the hero front-frame (STAND-IN framings).
import bpy, sys, os, json, math, mathutils
A = sys.argv[sys.argv.index("--")+1:]; arg = lambda k, d=None: A[A.index(k)+1] if k in A else d
sc = bpy.context.scene; fr = bpy.data.objects["HERO_front_frame"]; bpy.context.view_layer.update(); mw = fr.matrix_world.copy()
W = 37.54; ex = 0.5*W
def L2W(x, y, z): return mw @ mathutils.Vector((x, y, z))
def cam(name, loc, tgt, lens, shift=0.0):
    o = bpy.data.objects.get(name)
    if o is None:
        cd = bpy.data.cameras.new(name); o = bpy.data.objects.new(name, cd); sc.collection.objects.link(o)
    o.data.lens = lens; o.data.shift_y = shift; o.data.clip_end = 3000; o.location = loc
    o.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
CAMS = {"street": "Cam_Street", "hero": "Cam_Hero_34", "viaduct": "Cam_Viaduct", "aerial": "Cam_Aerial",
        "facade": cam("Cam_Facade", L2W(W*0.62, -13.0, 7.5), L2W(W*0.62, 0, 10.5), 16).name,
        "entrance": cam("Cam_Entrance", L2W(ex+2.0, -9.0, 1.7), L2W(ex, 0, 3.6), 22).name,
        "geograph": "Cam_Match_geograph",
        "wsw_east": cam("Cam_Surr_WSW_east", mathutils.Vector((-30, -27.5, 1.7)), (60, -12, 4), 20).name,   # same framings as build_surroundings.py --render
        "shops_east": cam("Cam_R8b_shops_east", mathutils.Vector((25, -24, 1.7)), (75, -3, 2.8), 22).name,   # r8b: neighbour shopfronts / lamps / tree pits
        "shops_west": cam("Cam_R8b_shops_west", mathutils.Vector((-40, -24, 1.7)), (-95, -3, 2.8), 22).name,
        "close_west": cam("Cam_R8c_close_west", mathutils.Vector((-72, -20, 1.7)), (-95, -10, 3.5), 16).name,   # r8c: shopfronts ~10.6 m, lamp (-86,-24) ~14.6 m
        "close_east": cam("Cam_R8c_close_east", mathutils.Vector((60, -8, 1.7)), (80, -12, 3.0), 18).name,     # r8c: shopfronts 6.5-10 m, lamp (66,-9) ~6 m
        "wsw_west": cam("Cam_Surr_WSW_west", mathutils.Vector((70, -10, 1.7)), (-40, -28, 5), 20).name}
for cd_ in (arg("--camdef") or "").split(";"):   # ad-hoc: "Name:x,y,z:tx,ty,tz:lens[;...]" (STAND-IN framings)
    if cd_:
        n_, l_, t_, f_ = cd_.split(":"); CAMS[n_] = cam(n_, mathutils.Vector([float(v) for v in l_.split(",")]), [float(v) for v in t_.split(",")], float(f_)).name
cf = arg("--camfile")
if cf and os.path.exists(cf):   # copy a locked camera (e.g. Cam_Match_geograph) from another blend's dump
    for n, d in json.load(open(cf)).items():
        o = bpy.data.objects.get(n)
        if o is None: cd = bpy.data.cameras.new(n); o = bpy.data.objects.new(n, cd); sc.collection.objects.link(o)
        o.matrix_world = mathutils.Matrix(d["mw"]); o.data.lens = d["lens"]; o.data.sensor_width = d["sensor"]; o.data.shift_x, o.data.shift_y = d["shift"]
        o.data.clip_start = d.get("clip_start", 0.1); o.data.clip_end = 3000
if "--dumpcams" in A:
    out = {o.name: {"mw": [list(r) for r in o.matrix_world], "lens": o.data.lens, "sensor": o.data.sensor_width, "shift": [o.data.shift_x, o.data.shift_y], "clip_start": o.data.clip_start}
           for o in bpy.data.objects if o.type == "CAMERA"}
    json.dump(out, open(arg("--dumpcams"), "w"), indent=1); print("DUMPED", list(out)); sys.exit(0)
if arg("--frame-rgb"):   # diagnostic only (e.g. white bars as in the photo); never saved
    c_ = [float(v) for v in arg("--frame-rgb").split(",")]
    for m in bpy.data.materials:
        if m.name.startswith("Window_frame_dark") and m.use_nodes: m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*c_, 1); m.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.0
rx, ry = map(int, arg("--res", "1920x1080").split("x")); r = sc.render; r.resolution_x, r.resolution_y = rx, ry; r.resolution_percentage = 100
sc.cycles.samples = int(arg("--samples", 64)); sc.cycles.device = "CPU"
if "--denoise" in A: sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"   # fewer samples + OIDN for big stills on the shared CPU
od = arg("--out"); os.makedirs(od, exist_ok=True); pre = arg("--prefix", "r")
import time
for c in arg("--cams", "street,facade,entrance,viaduct").split(","):
    o = bpy.data.objects.get(CAMS.get(c, c))
    if o is None: print("NO CAMERA", c); continue
    sc.camera = o; t = time.time(); r.filepath = os.path.join(od, f"{pre}_{c}_{rx}x{ry}.png")
    bpy.ops.render.render(write_still=True); print(f"RENDER {c} {time.time()-t:.1f}s -> {r.filepath}", flush=True)
