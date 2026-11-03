# Barclay House time-of-day rig. Stored inside the .blend as Text "barclay_tod.py" (Register ticked):
# it registers itself on load when Blender's "Auto Run Python Scripts" is allowed; otherwise open the
# Scripting tab, select barclay_tod.py and press Run Script once. Panel: 3D Viewport > N sidebar > "Barclay".
import bpy, math
LAT, LON = 53.4741, -2.2442          # Barclay House (OSM way 100646649)
PRESETS = {  # name: (hour, res, samples)
 "sunrise": (6.75, "4096x2304", 384), "morning": (9.0, "4096x2304", 256), "midday": (15.5, "4096x2304", 256),
 "golden_hour": (18.5, "4096x2304", 384), "dusk": (19.75, "4096x2304", 512), "night": (23.0, "4096x2304", 512)}
def doy(month, day): return sum([31,28,31,30,31,30,31,31,30,31,30,31][:month-1]) + day
def is_bst(month, day): return (month, day) >= (3, 29) and (month, day) < (10, 25)   # approx. UK summer time
def sun_pos(hour_local, month, day):
    n = doy(month, day); hr = hour_local - (1 if is_bst(month, day) else 0)       # -> UTC
    g = 2*math.pi/365*(n-1+(hr-12)/24)
    eqt = 229.18*(0.000075+0.001868*math.cos(g)-0.032077*math.sin(g)-0.014615*math.cos(2*g)-0.040849*math.sin(2*g))
    dec = 0.006918-0.399912*math.cos(g)+0.070257*math.sin(g)-0.006758*math.cos(2*g)+0.000907*math.sin(2*g)-0.002697*math.cos(3*g)+0.00148*math.sin(3*g)
    tst = hr*60+eqt+4*LON; ha = math.radians(tst/4-180); la = math.radians(LAT)
    ce = math.sin(la)*math.sin(dec)+math.cos(la)*math.cos(dec)*math.cos(ha); el = math.asin(max(-1, min(1, ce)))
    az = math.atan2(math.sin(ha), math.cos(ha)*math.sin(la)-math.tan(dec)*math.cos(la)) + math.pi   # from north, clockwise
    return math.degrees(el), math.degrees(az) % 360
def kelvin_rgb(k):
    t = k/100.0
    r = 1.0 if t <= 66 else min(1, max(0, 329.7*((t-60)**-0.1332)/255))
    g = min(1, max(0, (99.47*math.log(t)-161.12)/255 if t <= 66 else 288.12*((t-60)**-0.0755)/255))
    b = 1.0 if t >= 66 else (0 if t <= 19 else min(1, max(0, (138.52*math.log(t-10)-305.04)/255)))
    return (r, g, b)
def apply(self=None, context=None):
    sc = bpy.context.scene if context is None else context.scene
    h, mo, dy = sc.barclay_time, sc.barclay_month, sc.barclay_day
    el, az = sun_pos(h, mo, dy)
    sun = bpy.data.objects.get("Sun")
    if sun:   # Blender: sun shines along local -Z; scene +Y = grid north (BNG)
        sun.rotation_euler = (math.radians(90-el), 0, math.radians(180-az))
        day = max(0.0, math.sin(math.radians(el)))
        sun.data.energy = 4.0*min(1, day*2.5) if el > -1 else 0.0
        sun.data.color = kelvin_rgb(2000 + 4500*min(1, max(0, el)/35))
    w = sc.world
    if w and w.use_nodes:
        nt = w.node_tree; sky = nt.nodes.get("SKY"); mix = nt.nodes.get("SKY_HDRI_MIX"); night = nt.nodes.get("NIGHT")
        if sky:
            sky.sun_elevation = math.radians(el); sky.sun_rotation = math.radians(az); sky.sun_disc = el > -1
            sky.air_density = 1.0 + sc.barclay_haze*2; sky.dust_density = 0.5 + sc.barclay_haze*8
        if mix: mix.inputs[0].default_value = max(0.0, sc.barclay_clouds-0.5)*2
        cc = nt.nodes.get("CLOUD_COVER")
        if cc: cc.inputs[1].default_value = 0.6 - 0.25*sc.barclay_clouds
        bgS = nt.nodes.get("BG_SKY")
        if bgS: bgS.inputs[1].default_value = 0.35 if el > 0 else max(0.0, 0.35*(1+el/8))
        if night: night.inputs[1].default_value = 0.12 if el < 0 else 0.0; night.inputs[0].default_value = (0.012, 0.025, 0.09, 1)
        bgH = nt.nodes.get("BG_HDRI")
        if bgH: bgH.inputs[1].default_value = 0.6*max(0.0, min(1.0, (el+4)/14.0))
    glow = sc.barclay_glow if sc.barclay_glow_manual else max(0.0, min(1.0, (2.0 - el)/8.0))
    for m in bpy.data.materials:
        if m.use_nodes and "GLOW" in m.node_tree.nodes: m.node_tree.nodes["GLOW"].outputs[0].default_value = glow*0.3
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name.startswith("StreetLight"): o.data.energy = (1500 if "uplight" in o.name else 400)*glow
    if not sc.barclay_exposure_manual:
        sc.view_settings.exposure = -0.5 if el > 20 else (0.4 if el > 5 else (0.8 if el > -4 else 1.2))
    cam = bpy.data.objects.get(sc.barclay_camera)
    if cam: sc.camera = cam
def set_preset(sc, name):
    h, res, spp = PRESETS[name]; sc.barclay_time = h
    x, y = res.split("x"); sc.render.resolution_x, sc.render.resolution_y = int(x), int(y); sc.cycles.samples = spp
def cams(self, context): return [(o.name, o.name, "") for o in bpy.data.objects if o.type == "CAMERA"] or [("None", "None", "")]
class BARCLAY_OT_preset(bpy.types.Operator):
    bl_idname = "barclay.preset"; bl_label = "Apply preset"; name: bpy.props.StringProperty()
    def execute(self, context): set_preset(context.scene, self.name); return {"FINISHED"}
class BARCLAY_OT_render(bpy.types.Operator):
    bl_idname = "barclay.render_presets"; bl_label = "Render all presets (slow)"
    def execute(self, context):
        import os; sc = context.scene; d = bpy.path.abspath("//renders")
        os.makedirs(d, exist_ok=True)
        for n in PRESETS:
            set_preset(sc, n); sc.render.filepath = os.path.join(d, f"tod_{n}_{sc.barclay_camera}.png"); bpy.ops.render.render(write_still=True)
        return {"FINISHED"}
class BARCLAY_PT_panel(bpy.types.Panel):
    bl_label = "Barclay time of day"; bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Barclay"
    def draw(self, context):
        sc = context.scene; L = self.layout
        L.prop(sc, "barclay_time", slider=True); r = L.row(); r.prop(sc, "barclay_month"); r.prop(sc, "barclay_day")
        el, az = sun_pos(sc.barclay_time, sc.barclay_month, sc.barclay_day); L.label(text=f"Sun elev {el:.1f}°, az {az:.0f}°")
        g = L.grid_flow(columns=3)
        for n in PRESETS: g.operator("barclay.preset", text=n.replace("_", " ")).name = n
        L.prop(sc, "barclay_camera"); L.prop(sc, "barclay_clouds", slider=True); L.prop(sc, "barclay_haze", slider=True)
        L.prop(sc, "barclay_glow_manual"); c = L.column(); c.enabled = sc.barclay_glow_manual; c.prop(sc, "barclay_glow", slider=True)
        L.prop(sc, "barclay_exposure_manual"); c = L.column(); c.enabled = sc.barclay_exposure_manual; c.prop(sc.view_settings, "exposure")
        L.operator("barclay.render_presets")
P = bpy.props; S = bpy.types.Scene
def register():
    S.barclay_time = P.FloatProperty(name="Time of day (h)", min=0, max=24, default=13.0, update=apply)
    S.barclay_month = P.IntProperty(name="Month", min=1, max=12, default=6, update=apply)
    S.barclay_day = P.IntProperty(name="Day", min=1, max=31, default=21, update=apply)
    S.barclay_clouds = P.FloatProperty(name="Clouds (overcast HDRI mix)", min=0, max=1, default=0.0, update=apply)
    S.barclay_haze = P.FloatProperty(name="Haze", min=0, max=1, default=0.2, update=apply)
    S.barclay_glow_manual = P.BoolProperty(name="Manual window glow", default=False, update=apply)
    S.barclay_glow = P.FloatProperty(name="Window/street light glow", min=0, max=1, default=0.0, update=apply)
    S.barclay_exposure_manual = P.BoolProperty(name="Manual exposure", default=False, update=apply)
    S.barclay_camera = P.EnumProperty(name="Camera", items=cams, update=apply)
    for c in (BARCLAY_OT_preset, BARCLAY_OT_render, BARCLAY_PT_panel): bpy.utils.register_class(c)
try: register()
except ValueError: pass   # already registered
