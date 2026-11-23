"""Copy-test for trick #16 named part hierarchy.
Creates a tiny Hero stand-in (not the real building), applies parts_plan,
exports to tests/parthierarchy/out (never overwrites out/ or web/ GLBs).
Run: blender -b -P tests/parthierarchy/test_parts.py
"""
import bpy, os, sys, mathutils

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, HERE)
os.chdir(HERE)
os.environ.setdefault("BOUT", os.path.join(HERE, "tests", "parthierarchy", "out") + "/")

# fresh scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
hero_c = bpy.data.collections.new("Hero")
sc.collection.children.link(hero_c)
surr_c = bpy.data.collections.new("Surr")
sc.collection.children.link(surr_c)

def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    return m

def box(name, x0, x1, y0, y1, z0, z1, m, c, parent=None):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    o = bpy.data.objects.new(name, me); o.data.materials.append(m); c.objects.link(o)
    if parent: o.parent = parent
    return o

fm = mat("Floor_slab", (0.5,0.5,0.5))
stone = mat("Portland_stone_base", (0.58,0.52,0.40))
terr = mat("White_glazed_faience_Burmantofts", (0.55,0.47,0.33))
door = mat("Door_dark", (0.03,0.03,0.03))
glass = mat("Glass", (0.01,0.012,0.015))
frame = mat("Window_frame_dark", (0.78,0.78,0.75))
nb = mat("Test_neighbour", (0.6,0.6,0.6))  # not in export remap tables, no texture load

# Floor slabs at sourced-style levels (stand-in numbers for the copy only; labelled below)
LEVELS = [0.0, 2.1, 5.76, 9.69, 12.98, 16.3]  # test copy; real scene uses E05/DAS
for i, z in enumerate(LEVELS):
    fl = box(f"Floor_{i:02d}", -2, 2, -1, 1, z-0.2, z, fm, hero_c)
    fl["level_m_above_street"] = z
    fl["source"] = "stand-in" if i == 0 else "test copy of E05/DAS levels"

box("HERO_front_stone_base", -2, 2, -1.2, -1.0, 0, LEVELS[1], stone, hero_c)
box("HERO_front_terracotta", -2, 2, -1.15, -1.0, LEVELS[1], LEVELS[-1], terr, hero_c)
# two windows per upper floor + GF
for i, z0 in enumerate([0.4, LEVELS[1]+0.3, LEVELS[2]+0.3, LEVELS[3]+0.3, LEVELS[4]+0.3]):
    box("HERO_glass", -0.4, 0.4, -1.25, -1.18, z0, z0+1.2, glass, hero_c)
    box("HERO_frame", -0.45, -0.4, -1.28, -1.18, z0, z0+1.2, frame, hero_c)
    box("HERO_glass", 0.8, 1.4, -1.25, -1.18, z0, z0+1.2, glass, hero_c)  # will become .001
box("HERO_door_left", -0.4, -0.02, -1.3, -1.22, 0.0, 2.0, door, hero_c)
box("HERO_door_right", 0.02, 0.4, -1.3, -1.22, 0.0, 2.0, door, hero_c)
box("HERO_door_lintel", -0.45, 0.45, -1.3, -1.22, 2.0, 2.2, stone, hero_c)
box("HERO_doorcase", -0.55, -0.45, -1.35, -1.22, 0.0, 2.2, stone, hero_c)
box("HERO_doorcase", 0.45, 0.55, -1.35, -1.22, 0.0, 2.2, stone, hero_c)  # .001
box("HERO_cornice", -2.1, 2.1, -1.4, -1.0, LEVELS[-1]-0.4, LEVELS[-1], terr, hero_c)
box("HERO_parapet", -2.1, 2.1, -1.2, -1.0, LEVELS[-1], LEVELS[-1]+0.25, terr, hero_c)
box("Neighbour_box", 10, 12, -1, 1, 0, 8, nb, surr_c)

import parts_plan
result = parts_plan.apply(bpy, collection=hero_c)
print("APPLY", result)

# doors may already have been created as HERO_door_* — apply renames them
present = {o.name for o in bpy.data.objects}
missing = [n for n in parts_plan.required_names() if n not in present]
print("AFTER APPLY missing:", missing)
dotted = [n for n in present if __import__("re").search(r"\.\d{3}$", n)]
print("AFTER APPLY dotted:", dotted)
if missing or dotted:
    raise SystemExit(f"apply failed missing={missing} dotted={dotted}")

import export_glb
export_glb.main()
print("EXPORT to", os.environ["BOUT"])
