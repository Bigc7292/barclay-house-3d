"""Trick #12: geometry-aware procedural grime (Cycles shader nodes).

AO-masked crevice soot, optional Pointiness edge wear, gravity drips under
overhangs. Applied after the existing weather() stand-in (hybrid). Behind
BWEATHER2=1 so the official look is unchanged when the flag is off.

AO and Pointiness are Cycles-only: stills/flythrough first. export_glb.py
remaps materials, so this is not baked into the GLB unless a later pass
bakes it (budget check required).

Free stack: Blender GPL. Method from mcp-for-blender photoreal recipe
(https://www.mcp-for-blender.com/blog/photorealistic-renders/), paid
Opus/ChatGPT steps not used.
"""
from __future__ import annotations
import os

# Sourced E05/DAS storey levels (same constants as build_scene.py).
# Sill/cornice *offsets* from the window placement in build_scene.py are
# visual stand-ins (E05 shows the bands, not a dimensioned sill drop).
GF_ABOVE_STREET = 102.20 - 100.10  # DAS lobby 102.20, street 100.10
STOREY_H = [3.663, 3.925, 3.290, 3.323, 3.480]  # E05
LEVELS = [GF_ABOVE_STREET + sum(STOREY_H[:i]) for i in range(len(STOREY_H) + 1)]
ROOF = LEVELS[-1]

# Object/world Z of ledges that shed drips. Mix of sourced storey bands
# and stand-in sill offsets used by build_scene.glass / cornice boxes.
def overhang_zs():
    zs = [
        0.6,   # GF arch sill z0 (stand-in offset)
        2.6,   # pavilion GF window head (stand-in)
        LEVELS[1],          # first-floor band / cornice (E05+DAS)
        LEVELS[1] + 0.75,   # floor-1 sill (stand-in offset)
        LEVELS[2] + 0.75,
        LEVELS[3] + 0.75,
        LEVELS[4] + 0.70,   # attic sill (stand-in offset)
        LEVELS[4],          # main cornice (E05)
        ROOF,               # parapet / roof cornice (E05)
    ]
    return zs


def _already(m):
    return m and m.node_tree and m.node_tree.nodes.get("WEATHER2_AO")


def weather2(m, soot=0.3, drip=0.25, edge=0.0, overhangs=None):
    """Add a geometry-aware grime layer to an existing Principled material.

    soot: how far AO-darkened crevices multiply the base colour (0.3 -> *0.7).
    drip: strength of Z-stretched streaks under overhangs.
    edge: Pointiness wear toward a lighter chip colour (terracotta only).
    overhangs: list of Z heights (object/world, metres). None -> no sill mask
    (AO + generic vertical noise only; use this on Viaduct_brick).
    """
    if m is None or not m.use_nodes or _already(m):
        return m
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        return m
    out = nt.nodes.get("Material Output") or next(
        (n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial"), None
    )

    # ---- current base colour ----
    col_in = b.inputs["Base Color"]
    src = col_in.links[0].from_socket if col_in.links else None

    # ---- AO crevice soot (Cycles) ----
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.name = "WEATHER2_AO"
    ao.inside = False
    ao.inputs["Distance"].default_value = 0.3
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(ao.outputs["AO"], inv.inputs[1])
    soot_amt = nt.nodes.new("ShaderNodeMath")
    soot_amt.operation = "MULTIPLY"
    soot_amt.inputs[1].default_value = soot
    nt.links.new(inv.outputs[0], soot_amt.inputs[0])
    soot_col = nt.nodes.new("ShaderNodeMix")
    soot_col.data_type = "RGBA"
    soot_col.blend_type = "MULTIPLY"
    nt.links.new(soot_amt.outputs[0], soot_col.inputs[0])
    if src:
        nt.links.new(src, soot_col.inputs[6])
    else:
        soot_col.inputs[6].default_value = col_in.default_value[:]
    soot_col.inputs[7].default_value = (1.0 - soot, 1.0 - soot, 1.0 - soot, 1.0)

    # ---- gravity drips: Z-stretched noise x below-overhang mask ----
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.5, 1.5, 0.05)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    drip_ramp = nt.nodes.new("ShaderNodeValToRGB")
    drip_ramp.color_ramp.elements[0].position = 0.40
    drip_ramp.color_ramp.elements[1].position = 0.70
    drip_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    drip_ramp.color_ramp.elements[1].color = (1.0 - drip, 1.0 - drip, 1.0 - drip, 1)
    nt.links.new(nz.outputs["Fac"], drip_ramp.inputs[0])

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep_n.inputs[0])
    under = nt.nodes.new("ShaderNodeMath")
    under.operation = "LESS_THAN"
    nt.links.new(sep_n.outputs[2], under.inputs[0])
    under.inputs[1].default_value = -0.3

    sep_z = nt.nodes.new("ShaderNodeSeparateXYZ")
    # Object Z == height on the hero facade (parent rotation is about Z only).
    nt.links.new(tc.outputs["Object"], sep_z.inputs[0])

    if overhangs:
        # Max of per-ledge "just below Z" bands (about 0.9 m of drip length, stand-in).
        acc = None
        for z in overhangs:
            lo = nt.nodes.new("ShaderNodeMath")
            lo.operation = "GREATER_THAN"
            nt.links.new(sep_z.outputs[2], lo.inputs[0])
            lo.inputs[1].default_value = z - 0.9
            hi = nt.nodes.new("ShaderNodeMath")
            hi.operation = "LESS_THAN"
            nt.links.new(sep_z.outputs[2], hi.inputs[0])
            hi.inputs[1].default_value = z
            band = nt.nodes.new("ShaderNodeMath")
            band.operation = "MULTIPLY"
            nt.links.new(lo.outputs[0], band.inputs[0])
            nt.links.new(hi.outputs[0], band.inputs[1])
            if acc is None:
                acc = band
            else:
                mx = nt.nodes.new("ShaderNodeMath")
                mx.operation = "MAXIMUM"
                nt.links.new(acc.outputs[0], mx.inputs[0])
                nt.links.new(band.outputs[0], mx.inputs[1])
                acc = mx
        # Undersides always get drips; walls only inside a below-ledge band.
        mask = nt.nodes.new("ShaderNodeMath")
        mask.operation = "MAXIMUM"
        nt.links.new(under.outputs[0], mask.inputs[0])
        nt.links.new(acc.outputs[0], mask.inputs[1])
        drip_fac = nt.nodes.new("ShaderNodeMath")
        drip_fac.operation = "MULTIPLY"
        drip_fac.inputs[1].default_value = 1.0
        nt.links.new(mask.outputs[0], drip_fac.inputs[0])
        # mix factor for the drip colour: mask * (1 - ramp) essentially via mix
        drip_mix = nt.nodes.new("ShaderNodeMix")
        drip_mix.data_type = "RGBA"
        drip_mix.blend_type = "MULTIPLY"
        nt.links.new(drip_fac.outputs[0], drip_mix.inputs[0])
        nt.links.new(soot_col.outputs[2], drip_mix.inputs[6])
        nt.links.new(drip_ramp.outputs[0], drip_mix.inputs[7])
        colour = drip_mix.outputs[2]
        grime_w = drip_fac  # used for roughness
    else:
        # No sill list: weak vertical streaks everywhere, stronger on undersides.
        drip_mix = nt.nodes.new("ShaderNodeMix")
        drip_mix.data_type = "RGBA"
        drip_mix.blend_type = "MULTIPLY"
        addf = nt.nodes.new("ShaderNodeMath")
        addf.operation = "MAXIMUM"
        nt.links.new(under.outputs[0], addf.inputs[0])
        addf.inputs[1].default_value = 0.25
        nt.links.new(addf.outputs[0], drip_mix.inputs[0])
        nt.links.new(soot_col.outputs[2], drip_mix.inputs[6])
        nt.links.new(drip_ramp.outputs[0], drip_mix.inputs[7])
        colour = drip_mix.outputs[2]
        grime_w = addf

    # ---- optional Pointiness chip (terracotta arrises) ----
    if edge and edge > 0:
        pt = nt.nodes.new("ShaderNodeMath")
        # Geometry.Pointiness is ~0.5 on flats, higher on convex edges
        pt.operation = "MULTIPLY"
        pt.inputs[1].default_value = edge
        # map pointiness 0.5..1.0 -> 0..edge
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = 0.52
        mr.inputs[2].default_value = 0.85
        mr.inputs[3].default_value = 0.0
        mr.inputs[4].default_value = edge
        nt.links.new(geo.outputs["Pointiness"], mr.inputs[0])
        chip = nt.nodes.new("ShaderNodeMix")
        chip.data_type = "RGBA"
        nt.links.new(mr.outputs[0], chip.inputs[0])
        nt.links.new(colour, chip.inputs[6])
        chip.inputs[7].default_value = (0.75, 0.68, 0.55, 1.0)  # lighter chip, stand-in
        colour = chip.outputs[2]

    nt.links.new(colour, b.inputs["Base Color"])

    # ---- +0.1 roughness in grime areas ----
    rough = b.inputs["Roughness"]
    rsrc = rough.links[0].from_socket if rough.links else None
    radd = nt.nodes.new("ShaderNodeMath")
    radd.operation = "ADD"
    if rsrc:
        nt.links.new(rsrc, radd.inputs[0])
    else:
        radd.inputs[0].default_value = rough.default_value
    rscale = nt.nodes.new("ShaderNodeMath")
    rscale.operation = "MULTIPLY"
    rscale.inputs[1].default_value = 0.1
    # grime weight: AO soot + drip mask
    gsum = nt.nodes.new("ShaderNodeMath")
    gsum.operation = "ADD"
    nt.links.new(soot_amt.outputs[0], gsum.inputs[0])
    nt.links.new(grime_w.outputs[0], gsum.inputs[1])
    gclamp = nt.nodes.new("ShaderNodeMath")
    gclamp.operation = "MINIMUM"
    nt.links.new(gsum.outputs[0], gclamp.inputs[0])
    gclamp.inputs[1].default_value = 1.0
    nt.links.new(gclamp.outputs[0], rscale.inputs[0])
    nt.links.new(rscale.outputs[0], radd.inputs[1])
    nt.links.new(radd.outputs[0], b.inputs["Roughness"])
    return m


# Materials the trick applies to (hero stone / faience + viaduct brick).
TARGETS = {
    "White_glazed_faience_Burmantofts": dict(soot=0.3, drip=0.25, edge=0.15),
    "Portland_stone_base": dict(soot=0.3, drip=0.25, edge=0.0),
    "Viaduct_brick": dict(soot=0.3, drip=0.25, edge=0.0, overhangs=None),
}


def apply_all(bpy_data=None):
    """Patch the three target materials in an already-built blend. Idempotent."""
    import bpy
    data = bpy_data or bpy.data
    zs = overhang_zs()
    done = []
    for name, kw in TARGETS.items():
        m = data.materials.get(name)
        if not m:
            continue
        kwargs = dict(kw)
        if "overhangs" not in kwargs:
            kwargs["overhangs"] = zs
        weather2(m, **kwargs)
        done.append(name)
    return done


def enabled():
    return os.environ.get("BWEATHER2") == "1"
