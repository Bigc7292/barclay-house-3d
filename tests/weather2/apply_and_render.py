"""Copy-test for trick #12. Never writes official out/ or the official .blend.
Open a COPY of out/barclay_scene.blend, optionally apply weather2, render stills.
Env: BWEATHER2=1 to apply, BRES, BSAMPLES, BCAMS, BOUT (output dir).
"""
import bpy, os, sys, time, shutil, json

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, HERE)
os.chdir(HERE)

OUT = os.environ.get("BOUT", os.path.join(HERE, "tests", "weather2", "out"))
os.makedirs(OUT, exist_ok=True)
APPLY = os.environ.get("BWEATHER2") == "1"
tag = "on" if APPLY else "off"
W, H = [int(x) for x in os.environ.get("BRES", "960x540").split("x")]
SAMPLES = int(os.environ.get("BSAMPLES", "64"))
CAMS = os.environ.get("BCAMS", "Cam_Street,Cam_Match_geograph,Cam_Viaduct").split(",")

# Append locked match camera from the geograph solve, if missing.
if "Cam_Match_geograph" not in bpy.data.objects:
    src = os.path.join(HERE, "tests", "scene_matched_geograph.blend")
    if os.path.isfile(src):
        bpy.ops.wm.append(
            filepath=os.path.join(src, "Object", "Cam_Match_geograph"),
            directory=os.path.join(src, "Object") + "/",
            filename="Cam_Match_geograph",
        )
        print("APPENDED Cam_Match_geograph")

if APPLY:
    import weather2
    done = weather2.apply_all()
    print("WEATHER2 applied:", done)

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
# Do not save this .blend.

times = {}
for name in CAMS:
    cam = bpy.data.objects.get(name)
    if cam is None or cam.type != "CAMERA":
        print("MISSING cam", name)
        continue
    sc.camera = cam
    path = os.path.join(OUT, f"w2_{tag}_{name}_{W}x{H}.png")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    times[name] = dt
    print(f"RENDER {tag} {name} {W}x{H} spp={SAMPLES} time={dt:.1f}s -> {path}")

json.dump({"tag": tag, "res": [W, H], "samples": SAMPLES, "times": times, "applied": APPLY},
          open(os.path.join(OUT, f"w2_{tag}_times.json"), "w"), indent=1)
print("WEATHER2_TEST_DONE", tag)
# never bpy.ops.wm.save*
