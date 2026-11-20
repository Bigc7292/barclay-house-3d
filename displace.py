"""Trick #8: true Cycles displacement from derived height maps, street cam only.

Behind BDISP=1: connect a Displacement node from the derived 16-bit height
maps (scale 0.004–0.01 m) on Portland stone, terracotta, and neighbour
brick. Default method is BUMP: true displacement + adaptive subdiv
(BDISP_ADAPTIVE=1, method BOTH, dicing 2 px) tears the booleaned street
facade (see tests/disp/RESULT.md). Default (flag off) leaves the official
look unchanged. Stills / street camera only; not baked into the GLB.

Moss/weeds on the viaduct are optional (BDISP_MOSS=1) and are stand-in
scatter; they are off for the street-cam displacement certification.

Free: Blender GPL, height maps from derive_height.py (CC0 sources).
"""
from __future__ import annotations
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Scale in metres (trick brief: 0.004–0.01). Stone is already rusticated in
# geometry, so keep its texture displacement modest.
SCALES = {
    "Portland_stone_base": 0.006,
    "White_glazed_faience_Burmantofts": 0.004,
    "Neighbour_red_brick": 0.006,
}

# Facade slabs that face the street camera. Also accept parts_plan names.
FACADE = (
    "HERO_front_stone_base",
    "HERO_front_terracotta",
    "Facade_01",
    "Facade_upper",
)

HEIGHT_FOLDERS = {
    "Portland_stone_base": "stone",
    "White_glazed_faience_Burmantofts": "terracotta",
    "Neighbour_red_brick": "brick",
}


def enabled():
    return os.environ.get("BDISP") == "1"


def _height_path(folder):
    p = os.path.join(HERE, "textures", folder, "height.png")
    return p if os.path.isfile(p) else None


def hook_material(m, scale, folder):
    """Add a Displacement node from textures/<folder>/height.png. Idempotent.

    Uses a dedicated Object-space mapping (never reuse weather()/pbr mappings)
    and a scalar Color->BW conversion so Cycles cannot treat the height as a
    vector displacement. Sets material.displacement_method to BUMP (Blender 4.2+;
    m.cycles.displacement_method no longer exists). BOTH + adaptive
    subdiv is gated behind BDISP_ADAPTIVE=1 and is known-unsafe on
    the booleaned facade slabs — see tests/disp/RESULT.md.
    """
    if m is None or not m.use_nodes:
        return False
    nt = m.node_tree
    if nt.nodes.get("BDISP_HEIGHT"):
        m.displacement_method = "BUMP"
        return True
    hp = _height_path(folder)
    if not hp:
        return False
    out = nt.nodes.get("Material Output") or next(
        (n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial"), None
    )
    if out is None:
        return False
    import bpy
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.name = "BDISP_COORD"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name = "BDISP_HEIGHT"
    tex.image = bpy.data.images.load(hp, check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    tex.projection = "BOX"
    tex.projection_blend = 0.2
    nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    bw.name = "BDISP_BW"
    nt.links.new(tex.outputs["Color"], bw.inputs[0])
    d = nt.nodes.new("ShaderNodeDisplacement")
    d.name = "BDISP_DISP"
    d.space = "OBJECT"
    d.inputs["Midlevel"].default_value = 0.5
    d.inputs["Scale"].default_value = float(scale)
    nt.links.new(bw.outputs[0], d.inputs["Height"])
    # Only the Displacement socket — never touch Surface.
    disp_in = out.inputs.get("Displacement") or out.inputs[2]
    nt.links.new(d.outputs[0], disp_in)
    m.displacement_method = "BUMP"
    return True



def adaptive_enabled():
    import os
    return os.environ.get("BDISP_ADAPTIVE", "0") == "1"


def apply_adaptive(sc):
    """Experimental adaptive subdiv on hero facade objects only.

    Does not apply the live BOOLEAN:windows cutters. Applying them (and
    Catmull-Clark on the result) melted the facade even at constant Height
    0.5. A SIMPLE subdiv modifier is appended after the existing boolean
    so Cycles can dice for 0.004-0.01 m displacement without smoothing
    the cut openings. In-memory only (the official .blend is never saved).
    """
    sc.cycles.feature_set = "EXPERIMENTAL"
    sc.cycles.dicing_rate = 2.0
    import bpy
    n = 0
    for name in FACADE:
        o = bpy.data.objects.get(name)
        if o is None or o.type != "MESH":
            continue
        if not any(m.name == "BDISP" for m in o.modifiers):
            md = o.modifiers.new("BDISP", "SUBSURF")
            md.subdivision_type = "SIMPLE"
            md.levels = 0
            md.render_levels = 0
        o.cycles.use_adaptive_subdivision = True
        n += 1
    return n



def apply_all(sc=None):
    """Hook materials + adaptive subdiv. No-op unless BDISP=1 (callers may
    still call hook_material in tests). Does not save the .blend."""
    import bpy
    sc = sc or bpy.context.scene
    hooked = []
    for name, folder in HEIGHT_FOLDERS.items():
        m = bpy.data.materials.get(name)
        if hook_material(m, SCALES.get(name, 0.006), folder):
            hooked.append(name)
    nobj = 0
    if adaptive_enabled():
        nobj = apply_adaptive(sc)
        for name in HEIGHT_FOLDERS:
            m = bpy.data.materials.get(name)
            if m is not None:
                m.displacement_method = "BOTH"
    return hooked, nobj


def maybe_apply(sc=None):
    if not enabled():
        return [], 0
    return apply_all(sc)
