"""Export a NEW hero GLB with Floor_* / Door_* names (tricks #5 / #16).

Opens official out/barclay_scene.blend READ-ONLY, applies parts_plan in memory,
exports to BOUT (never out/barclay_hero.glb, never saves the .blend).
"""
import bpy, os, sys, json

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, HERE)
os.chdir(HERE)
OUT = os.environ.get("BOUT", os.path.join(HERE, "tests", "hero_floors", "out"))
os.makedirs(OUT, exist_ok=True)
os.environ["BOUT"] = OUT if OUT.endswith("/") else OUT + "/"

import parts_plan
hero_c = bpy.data.collections.get("Hero")
result = parts_plan.apply(bpy, collection=hero_c)
print("PARTS_APPLY", result)

present = {o.name for o in bpy.data.objects}
required = parts_plan.required_names()
missing = [n for n in required if n not in present]
dotted = [n for n in present if __import__("re").search(r"\.\d{3}$", n) and any(c.name == "Hero" for c in bpy.data.objects[n].users_collection)]
print("AFTER APPLY missing:", missing)
print("AFTER APPLY hero dotted count:", len(dotted))

import export_glb
export_glb.main()
print("EXPORT to", os.environ["BOUT"])
# never save
