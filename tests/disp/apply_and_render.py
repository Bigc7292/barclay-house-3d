"""Copy-test for trick #8. Never writes official out/ or the official .blend.
Env: BDISP=1 to enable, BRES, BSAMPLES, BCAMS, BOUT, BTOD (optional preset).
"""
import bpy, os, sys, time, json

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, HERE)
os.chdir(HERE)

OUT = os.environ.get("BOUT", os.path.join(HERE, "tests", "disp", "out"))
os.makedirs(OUT, exist_ok=True)
APPLY = os.environ.get("BDISP") == "1"
tag = "on" if APPLY else "off"
W, H = [int(x) for x in os.environ.get("BRES", "960x540").split("x")]
SAMPLES = int(os.environ.get("BSAMPLES", "32"))
CAMS = os.environ.get("BCAMS", "Cam_Street").split(",")
TOD = os.environ.get("BTOD", "")

if "Cam_Match_geograph" not in bpy.data.objects:
    src = os.path.join(HERE, "tests", "scene_matched_geograph.blend")
    if os.path.isfile(src):
        bpy.ops.wm.append(
            filepath=os.path.join(src, "Object", "Cam_Match_geograph"),
            directory=os.path.join(src, "Object") + "/",
            filename="Cam_Match_geograph",
        )

if APPLY:
    import displace
    hooked, nobj = displace.apply_all(bpy.context.scene)
    print("BDISP applied materials=", hooked, "facade_objs=", nobj)

# optional ToD switch if the text is registered
if TOD:
    try:
        sc = bpy.context.scene
        if hasattr(sc, "barclay_camera"):
            # tod_panel may be missing (scripts disabled). Best-effort.
            pass
    except Exception as e:
        print("TOD skip", e)

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.use_adaptive_sampling = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.image_settings.file_format = "PNG"

import resource
times = {}
for name in CAMS:
    cam = bpy.data.objects.get(name)
    if cam is None or cam.type != "CAMERA":
        print("MISSING cam", name)
        continue
    sc.camera = cam
    path = os.path.join(OUT, f"disp_{tag}_{name}_{W}x{H}.png")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    times[name] = {"s": dt, "maxrss_mb": rss}
    print(f"RENDER {tag} {name} {W}x{H} spp={SAMPLES} time={dt:.1f}s rss={rss:.0f}MB -> {path}")

json.dump({"tag": tag, "res": [W, H], "samples": SAMPLES, "times": times, "applied": APPLY},
          open(os.path.join(OUT, f"disp_{tag}_times.json"), "w"), indent=1)
print("DISP_TEST_DONE", tag)
