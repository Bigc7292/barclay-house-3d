"""flythrough.py - repeatable camera fly-through for the Barclay scene (teardown 'render(t)' contract in Blender).

Camera pose is a PURE function of t (no keyframes edited by hand, no randomness), driven by SCRIPT beats in
HERO-FRONT-LOCAL metres (x along the Whitworth St W facade from the west corner, y into the building, z above
street). Same script -> same frames every run. Writes <out>/timeline.json (beat times, teardown format) so
teardown's sheet.mjs can build review contact sheets per beat.

  blender -b -y tests/scene_copy.blend -P flythrough.py -- --out tests/fly --res 480x270 --fps 12 --samples 8 --tod golden_hour
  ffmpeg -y -framerate 12 -i tests/fly/f_%04d.png -c:v libx264 -pix_fmt yuv420p tests/fly/fly.mp4
  node ~/apps/addons/teardown/sheet.mjs --video tests/fly/fly.mp4 --timeline tests/fly/timeline.json --cols 3
If Blender crashes mid-run just re-run the same command: finished frames are skipped.
Add --life for x_tricks #9 street life (life_paths.py: Kenney CC0 car/van, train on the viaduct deck, walkers on the hero
footway, all on OSM geometry, pure function of t; stand-in sizes/speeds, illustrative). Add --keyframe to bake the path into a camera "Cam_Fly" (for interactive scrubbing/final renders) instead of rendering.
"""
import bpy, json, math, os, sys
from mathutils import Vector

SCRIPT = [  # (t seconds, beat name, camera xyz, look-at xyz)  - hero-local metres
    # v2 after the first review sheet: street-level beats kept between facade and viaduct (y -9..-12);
    # v1 beats at y -32..-40 were inside the viaduct piers/arches.
    (0.0, "approach_west",  (-30, -10, 1.7),  (18, 0, 8)),
    (3.0, "front_3q",       (-8, -11, 1.7),   (18, 0, 10)),
    (6.0, "entrance",       (18.8, -11, 1.7), (18.8, 0, 6)),
    (9.0, "rise_east",      (55, -12, 22),    (18, 5, 10)),
    (12.0, "aerial_viaduct",(30, -90, 70),    (18, 10, 5)),
]
DURATION = SCRIPT[-1][0] + 0.5   # hold the last beat so a +0.3 s review tile exists

def _smooth(a, b, u):
    u = u * u * (3 - 2 * u); return Vector(a).lerp(Vector(b), u)

def pose(t):
    """Pure: t -> (location, look_at) in hero-local metres."""
    t = max(0.0, min(DURATION, t))
    for (t0, _, c0, l0), (t1, _, c1, l1) in zip(SCRIPT, SCRIPT[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0); return _smooth(c0, c1, u), _smooth(l0, l1, u)
    return Vector(SCRIPT[-1][2]), Vector(SCRIPT[-1][3])

def place(cam, t, mw):
    c, l = pose(t); cam.location = mw @ c
    cam.rotation_euler = ((mw @ l) - cam.location).to_track_quat("-Z", "Y").to_euler()

def main(out, res="480x270", fps=12, samples=8, tod="midday", keyframe=False, lens=24.0, life=False):
    sc = bpy.context.scene; mw = bpy.data.objects["HERO_front_frame"].matrix_world.copy()
    cam = bpy.data.objects.get("Cam_Fly") or bpy.data.objects.new("Cam_Fly", bpy.data.cameras.new("Cam_Fly"))
    if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_end = 3000
    t_ = bpy.data.texts.get("barclay_tod.py")
    if t_ and tod:
        m = t_.as_module(); m.set_preset(sc, tod)
        try: sc.barclay_camera = cam.name
        except Exception: pass
        m.apply(None, bpy.context)
    sc.camera = cam; os.makedirs(out, exist_ok=True); actors = None
    if life:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import life_paths; actors = life_paths.setup(sc)
    def step(t):
        if actors: life_paths.update(actors, t, sc)   # sets the scene frame first (walk cycles)
        place(cam, t, mw)
    json.dump({"duration": DURATION, "fps": fps, "beats": {n: t for t, n, _, _ in SCRIPT}},
              open(os.path.join(out, "timeline.json"), "w"), indent=1)
    n = int(DURATION * fps) + 1
    if keyframe:
        sc.render.fps = fps; sc.frame_start, sc.frame_end = 1, n
        for i in range(n):
            step(i / fps)
            for o in [cam] + [r for a in (actors or []) for r in a["parts"]]:
                o.keyframe_insert("location", frame=i + 1); o.keyframe_insert("rotation_euler", frame=i + 1)
        return
    r = sc.render; r.resolution_x, r.resolution_y = (int(v) for v in res.split("x")); r.resolution_percentage = 100
    sc.cycles.samples = samples; r.image_settings.file_format = "PNG"
    for i in range(n):   # resumable: existing frames are skipped (Cycles/Embree can segfault on long headless loops)
        if os.path.exists(os.path.join(out, f"f_{i:04d}.png")): continue
        step(i / fps); r.filepath = os.path.join(out, f"f_{i:04d}.png"); bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    import argparse
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--res", default="480x270")
    ap.add_argument("--fps", type=int, default=12); ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--tod", default="midday"); ap.add_argument("--keyframe", action="store_true"); ap.add_argument("--lens", type=float, default=24.0)
    ap.add_argument("--life", action="store_true")
    a = ap.parse_args(A); main(os.path.abspath(a.out), a.res, a.fps, a.samples, a.tod, a.keyframe, a.lens, a.life)
