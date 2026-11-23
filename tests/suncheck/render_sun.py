"""Read-only sun-check renders. Never saves the official .blend."""
import bpy, json, os, sys, time
from math import radians

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
# --jobs PATH --out PATH --samples N --width N
opts = {}
i = 0
while i < len(argv):
    if argv[i].startswith("--") and i + 1 < len(argv):
        opts[argv[i][2:]] = argv[i + 1]
        i += 2
    else:
        i += 1

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, HERE)
os.chdir(HERE)

OUT = opts.get("out", os.path.join(HERE, "tests", "suncheck", "out"))
os.makedirs(OUT, exist_ok=True)
jobs = json.load(open(opts["jobs"]))
SAMPLES = int(opts.get("samples", "32"))
MAX_W = int(opts.get("width", "960"))

# Use repo tod_panel (source of truth), not only the text block inside the blend.
import tod_panel
try:
    tod_panel.register()
except ValueError:
    pass

sc = bpy.context.scene
# Append locked cameras if missing.
needed = {j["cam"]: j.get("cam_source") for j in jobs if j.get("cam")}
for cam_name, src in needed.items():
    if cam_name in bpy.data.objects:
        continue
    if not src:
        print("MISSING_CAM_SOURCE", cam_name)
        continue
    src_abs = os.path.join(HERE, src)
    bpy.ops.wm.append(
        filepath=os.path.join(src_abs, "Object", cam_name),
        directory=os.path.join(src_abs, "Object") + "/",
        filename=cam_name,
    )
    print("APPENDED", cam_name, "from", src)

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.use_adaptive_sampling = True
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
# Clear sun for a readable shadow test; haze stays at the panel default.
if hasattr(sc, "barclay_clouds"):
    sc.barclay_clouds = 0.0

# The locked Geograph camera sits inside unsourced neighbour / viaduct
# set-dressing (camera_match blockers). hide_near(8) segfaulted Cycles/Embree
# on this scene, so we clip the hugging geometry instead (same idea, no flag
# changes). This session never saves the official blend.
times = {}
for job in jobs:
    cam = bpy.data.objects.get(job["cam"])
    if cam is None or cam.type != "CAMERA":
        print("MISSING cam", job["cam"], "for", job["id"])
        continue
    clip = float(job.get("clip_start") or 4.0)
    old_clip = cam.data.clip_start
    cam.data.clip_start = max(cam.data.clip_start, clip)
    print("CLIP_START", job["id"], "from", old_clip, "to", cam.data.clip_start)
    sc.camera = cam
    # Photo aspect: do not stretch a 4:3 plate into 16:9. Size comes from the
    # jobs file (Blender's Python has no Pillow).
    pw, ph = int(job["width"]), int(job["height"])
    if pw >= ph:
        W, H = MAX_W, max(1, int(round(MAX_W * ph / pw)))
    else:
        H, W = MAX_W, max(1, int(round(MAX_W * pw / ph)))
    sc.render.resolution_x, sc.render.resolution_y = W, H
    if hasattr(sc, "barclay_month"):
        sc.barclay_month = int(job["month"])
        sc.barclay_day = int(job["day"])
        try:
            sc.barclay_camera = cam.name
        except Exception:
            pass
    for off, hour in zip(job["offsets"], job["hours"]):
        if hasattr(sc, "barclay_time"):
            sc.barclay_time = float(hour)
            tod_panel.apply(None, bpy.context)
        else:
            # scripts didn't register; apply from repo module after setting attrs
            print("NO_TOD_PROPS — applying sun_pos directly")
            el, az = tod_panel.sun_pos(float(hour), int(job["month"]), int(job["day"]))
            sun = bpy.data.objects.get("Sun")
            if sun:
                sun.rotation_euler = (radians(90 - el), 0, radians(180 - az))
                day = max(0.0, __import__("math").sin(radians(el)))
                sun.data.energy = 4.0 * min(1, day * 2.5) if el > -1 else 0.0
        sc.camera = cam
        dest = os.path.join(OUT, f"render_{job['id']}_off{off:+d}.png")
        sc.render.filepath = dest
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        times[f"{job['id']}_off{off:+d}"] = dt
        print(f"RENDER {job['id']} off={off:+d} h={hour:.4f} {W}x{H} spp={SAMPLES} time={dt:.1f}s -> {dest}")

json.dump({"times": times, "samples": SAMPLES}, open(os.path.join(OUT, "render_times.json"), "w"), indent=2)
print("SUNCHECK_RENDER_DONE")
# never bpy.ops.wm.save*
