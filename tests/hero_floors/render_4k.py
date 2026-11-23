"""4K street still from the official blend (read-only) for look comparison."""
import bpy, os, sys, time

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, HERE)
OUT = os.environ.get("BOUT", os.path.join(HERE, "tests", "hero_floors", "out"))
os.makedirs(OUT, exist_ok=True)
W, H = [int(x) for x in os.environ.get("BRES", "4096x2304").split("x")]
SAMPLES = int(os.environ.get("BSAMPLES", "128"))
cam = bpy.data.objects.get(os.environ.get("BCAM", "Cam_Street"))
sc = bpy.context.scene
sc.camera = cam
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
path = os.path.join(OUT, f"render_street_{W}x{H}.png")
sc.render.filepath = path
t = time.time()
bpy.ops.render.render(write_still=True)
print(f"RENDER_4K {cam.name} {W}x{H} spp={SAMPLES} time={time.time()-t:.1f}s -> {path}")
