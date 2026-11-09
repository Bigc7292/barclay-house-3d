# tests/streetwater_cut.blend = copy + terrain cut (baseline for the ripple A/B); tests/streetwater_ripple.blend = cut + ripple (for the export test)
import bpy, sys, os; R = "/workspace/barclay-wt-streetwater"; sys.path.insert(0, R); import water_ripple
t = bpy.data.objects["Terrain_EA_DTM"]; W = [o for o in bpy.data.objects if o.name.startswith("canal_")]
print("CUT", water_ripple.cut_terrain(t, W)); bpy.ops.wm.save_as_mainfile(filepath=R + "/tests/streetwater_cut.blend", copy=True)
print("RIPPLE", water_ripple.ripple(bpy.data.materials["Canal_water"])); bpy.ops.wm.save_as_mainfile(filepath=R + "/tests/streetwater_ripple.blend", copy=True)
