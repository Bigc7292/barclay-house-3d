"""camera_match.py - match a Blender camera to a reference photo/CGI (free, no add-ons needed).

Method (fSpy-style, but solved from point pairs instead of vanishing lines):
  1. You click/read >= 5 pixel positions in the reference image of points whose 3D position is known
     (building corners, roof/parapet line, ground corners). Coordinates may be given in WORLD metres or
     in HERO-FRONT-LOCAL metres (x along the Whitworth St W facade from its left/west corner,
     y into the building, z above street) - the script converts using the HERO_front_frame empty.
  2. A Levenberg-Marquardt solve finds focal length + camera rotation + position that minimise
     reprojection error (square pixels, principal point at centre or with shift_x/shift_y if --solve-shift).
  3. The camera gets the photo as a background image (viewport overlay), render resolution = photo size,
     and optionally a low-res render + 50/50 overlay PNG + per-point error report are written.

Usage (ALWAYS on a copy of the .blend; -y lets the time-of-day panel script run):
  blender -b -y tests/scene_copy.blend -P camera_match.py -- --ref refs/plans_p1_cgi.png \
      --points tests/cgi_points.json --cam Cam_Match --render tests/match_render.png --scale 0.5 \
      --save tests/scene_copy_matched.blend
  Manual FOV mode (no solve): --fov-h 54 --loc x,y,z --look x,y,z
Via Blender MCP: execute_blender_code with  exec(open('/workspace/barclay/camera_match.py').read(),
  {'__name__':'camera_match'})  then call  match(ref, points, cam_name='Cam_Match')  - then SAVE AS a copy.
Points JSON: {"frame":"hero"|"world", "points":[{"name":"FL_top","xyz":[0,0,20.13],"px":[440,237]}, ...]}
"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Matrix, Vector, Euler

def _to_world(pts, frame):
    if frame == "world": return [Vector(p["xyz"]) for p in pts]
    mw = bpy.data.objects["HERO_front_frame"].matrix_world
    return [mw @ Vector(p["xyz"]) for p in pts]

def _project(params, X, W, H, sensor=36.0, solve_shift=False):
    f, rx, ry, rz, tx, ty, tz = params[:7]; sx, sy = (params[7], params[8]) if solve_shift else (0.0, 0.0)
    R = np.array(Euler((rx, ry, rz), "XYZ").to_matrix())
    Pc = (X - np.array([tx, ty, tz])) @ R           # world -> camera (columns of R are cam axes)
    fpx = f / sensor * max(W, H)                     # Blender sensor_fit AUTO: sensor spans the longer side
    z = -Pc[:, 2]
    u = W / 2 + sx * max(W, H) + fpx * Pc[:, 0] / z
    v = H / 2 - sy * max(W, H) - fpx * Pc[:, 1] / z
    return np.stack([u, v], 1), z

def solve(Xw, px, W, H, init, solve_shift=False, iters=400):
    X = np.array([list(p) for p in Xw]); U = np.array(px, float)
    p = np.array(list(init) + ([0.0, 0.0] if solve_shift else []), float); lam = 1e-2
    def res(q):
        uv, z = _project(q, X, W, H, solve_shift=solve_shift)
        return (uv - U).ravel() + np.where(np.repeat(z, 2) <= 0, 1e4, 0)
    r = res(p)
    for _ in range(iters):
        J = np.zeros((r.size, p.size))
        for k in range(p.size):
            d = np.zeros_like(p); d[k] = 1e-6 * max(1.0, abs(p[k])); J[:, k] = (res(p + d) - r) / d[k]
        A = J.T @ J; g = J.T @ r
        step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
        r2 = res(p + step)
        if r2 @ r2 < r @ r: p, r, lam = p + step, r2, lam * 0.3
        else: lam *= 10
        if np.linalg.norm(step) < 1e-9 or lam > 1e12: break
    rms = float(np.sqrt(np.mean(r.reshape(-1, 2) ** 2 @ np.ones(2))))
    return p, rms, r.reshape(-1, 2)

def look_at_euler(loc, tgt):
    return (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler("XYZ")

def get_cam(name):
    sc = bpy.context.scene
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(o)
    o.data.sensor_width = 36.0; o.data.sensor_fit = "AUTO"; o.data.clip_end = 3000
    return o

def set_reference(cam, ref, alpha=0.5):
    img = bpy.data.images.load(os.path.abspath(ref), check_existing=True)
    cam.data.show_background_images = True; cam.data.background_images.clear()
    bg = cam.data.background_images.new(); bg.image = img; bg.alpha = alpha; bg.display_depth = "FRONT"; bg.frame_method = "FIT"
    r = bpy.context.scene.render; r.resolution_x, r.resolution_y = img.size; r.resolution_percentage = 100
    return img.size

def manual(cam, ref, fov_h, loc, look):
    W, H = set_reference(cam, ref)
    cam.data.lens = 36.0 / (2 * math.tan(math.radians(fov_h) / 2)) * (max(W, H) / W)
    cam.location = loc; cam.rotation_euler = look_at_euler(loc, look)

def match(ref, points, cam_name="Cam_Match", init_loc=None, init_look=None, init_f=35.0, solve_shift=False):
    data = json.load(open(points)) if isinstance(points, str) else points
    cam = get_cam(cam_name); W, H = set_reference(cam, ref)
    Xw = _to_world(data["points"], data.get("frame", "hero")); px = [p["px"] for p in data["points"]]
    c = sum(Xw, Vector()) / len(Xw)
    if init_loc is None:      # start in front of the hero facade, eye height, ~3x building size away
        fr = bpy.data.objects.get("HERO_front_frame")
        out = (fr.matrix_world.to_3x3() @ Vector((0, -1, 0))) if fr else Vector((0, -1, 0))
        span = max((a - b).length for a in Xw for b in Xw); init_loc = Vector((c.x, c.y, 0)) + out * span * 2.5 + Vector((0, 0, 1.7))
    e = look_at_euler(init_loc, init_look or c)
    best = None
    for f0 in (init_f, 18, 28, 50, 85):            # multi-start on focal length
        p, rms, res = solve(Xw, px, W, H, [f0, e.x, e.y, e.z, *init_loc], solve_shift)
        if best is None or rms < best[1]: best = (p, rms, res)
    p, rms, res = best
    cam.data.lens = float(p[0]); cam.rotation_euler = Euler(tuple(p[1:4]), "XYZ"); cam.location = tuple(p[4:7])
    if solve_shift: cam.data.shift_x, cam.data.shift_y = float(p[7]), float(p[8])
    bpy.context.scene.camera = cam
    # clearance check: is the solved camera inside/behind scene geometry (e.g. set-dressing piers)?
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene; blockers = {}
    for t in Xw:
        d = t - cam.location; hit = sc.ray_cast(dg, cam.location, d.normalized(), distance=d.length - 0.5)
        if hit[0]: blockers[hit[4].name] = round((hit[1] - cam.location).length, 2)
    report = {"blockers_between_camera_and_points": blockers,"camera": cam_name, "lens_mm": round(float(p[0]), 2),
              "hfov_deg": round(math.degrees(2 * math.atan(36.0 / 2 / p[0] * W / max(W, H))), 2),
              "location": [round(float(v), 2) for v in p[4:7]], "rotation_deg": [round(math.degrees(v), 2) for v in p[1:4]],
              "rms_px": round(rms, 2), "per_point_px": {d["name"]: [round(float(a), 1), round(float(b), 1)] for d, (a, b) in zip(data["points"], res)},
              "image": [W, H]}
    print("CAMERA_MATCH", json.dumps(report)); return report

def hide_near(cam, dist):
    """Hide (render only) meshes whose bounding box is within dist m of the camera - for solved cameras that land
    inside set-dressing (e.g. un-sourced viaduct piers). Returns names hidden."""
    out = []; c = cam.location
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render: continue
        bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
        q = Vector([min(max(c[i], min(b[i] for b in bb)), max(b[i] for b in bb)) for i in range(3)])
        if (q - c).length < dist and not o.name.startswith(("HERO", "Terrain")): o.hide_render = True; out.append(o.name)
    return out

def apply_tod(preset="midday"):
    """Use the scene's Barclay time-of-day panel (tod_panel.py) so the match render is lit; keeps our camera."""
    sc = bpy.context.scene; cam = sc.camera; t = bpy.data.texts.get("barclay_tod.py")
    if t is None or not hasattr(sc, "barclay_time"):
        if t: t.as_module()
    if t is None: return
    m = t.as_module(); res = (sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples)
    m.set_preset(sc, preset); sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = res
    try: sc.barclay_camera = cam.name
    except Exception: pass
    m.apply(None, bpy.context); sc.camera = cam

def render_overlay(ref, out_png, scale=0.5, samples=16, tod="midday"):
    sc = bpy.context.scene; r = sc.render
    if tod: apply_tod(tod)
    r.resolution_percentage = int(scale * 100); r.filepath = out_png; r.image_settings.file_format = "PNG"
    if r.engine == "CYCLES": sc.cycles.samples = samples
    bpy.ops.render.render(write_still=True)
    try:
        from PIL import Image
    except ImportError:
        import subprocess   # Blender's python has no PIL: use the system python3 (Pillow) instead
        subprocess.run(["python3", "-c", "import sys;from PIL import Image;a=Image.open(sys.argv[1]).convert('RGB');"
                        "b=Image.open(sys.argv[2]).convert('RGB').resize(a.size);Image.blend(a,b,0.5).save(sys.argv[3])",
                        out_png, ref, out_png.replace(".png", "_overlay.png")], check=False); return
    a = Image.open(out_png).convert("RGB"); b = Image.open(ref).convert("RGB").resize(a.size)
    Image.blend(a, b, 0.5).save(out_png.replace(".png", "_overlay.png"))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap.add_argument("--ref", required=True); ap.add_argument("--points"); ap.add_argument("--cam", default="Cam_Match")
    ap.add_argument("--fov-h", type=float); ap.add_argument("--loc"); ap.add_argument("--look")
    ap.add_argument("--solve-shift", action="store_true"); ap.add_argument("--render"); ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--samples", type=int, default=16); ap.add_argument("--tod", default="midday"); ap.add_argument("--save"); ap.add_argument("--hide-near", type=float, help="hide_render meshes within N m of the camera (only for the test render)"); ap.add_argument("--clip-start", type=float, help="metres; skip geometry hugging the camera")
    a = ap.parse_args(A); vec = lambda s: Vector([float(x) for x in s.split(",")])
    if a.points: match(a.ref, a.points, a.cam, solve_shift=a.solve_shift)
    else: manual(get_cam(a.cam), a.ref, a.fov_h, vec(a.loc), vec(a.look)); bpy.context.scene.camera = bpy.data.objects[a.cam]
    if a.clip_start: bpy.data.objects[a.cam].data.clip_start = a.clip_start
    if a.hide_near: print("HIDDEN_NEAR_CAMERA", hide_near(bpy.data.objects[a.cam], a.hide_near))
    if a.render: render_overlay(a.ref, os.path.abspath(a.render), a.scale, a.samples, a.tod)
    if a.save:
        assert not os.path.abspath(a.save).endswith("out/barclay_scene.blend"), "refusing to overwrite the master scene"
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save), copy=True)
