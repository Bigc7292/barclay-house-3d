# Two Bed (Barclay House) single-unit massing. SOURCED: area 63 m2 (barclay-house.com, Rightmove 679/681 sq ft),
# GF->1st floor-to-floor 3.663 m (E05 via Page). UNSOURCED: square footprint proportions (sqrt of area). Layout NOT FOUND.
import bpy, math
AREA=63.0; H=3.663; S=math.sqrt(AREA); T=0.1
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(n,c,a=1):
    m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*c,1); b.inputs["Alpha"].default_value=a; return m
def box(n,sx,sy,sz,loc,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=n; o.scale=(sx,sy,sz)
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); return o
fm=mat("floor_finish_unsourced",(0.55,0.40,0.26)); fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=0.45
box("Floor_63m2",S,S,0.05,(0,0,-0.025),fm)
box("Slab",S+0.6,S+0.6,0.3,(0,0,-0.2),mat("slab",(0.35,0.35,0.37)))
w=mat("wall_plaster_unsourced",(0.92,0.91,0.88)); w.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=0.85
box("Wall_N",S,T,H,(0,S/2,H/2),w); box("Wall_W",T,S,H,(-S/2,0,H/2),w); box("Wall_E",T,S,H,(S/2,0,H/2),w)
box("Wall_S_low",S,T,1.0,(0,-S/2,0.5),w)
bpy.ops.object.camera_add(location=(S*1.3,-S*1.6,S*1.3)); c=bpy.context.object
d=-c.location; c.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=c
bpy.ops.object.light_add(type='SUN',location=(0,0,10),rotation=(0.7,0.2,0.9)); bpy.context.object.data.energy=3.5; bpy.context.object.data.angle=0.05
bpy.ops.object.light_add(type='AREA',location=(0,0,H-0.05)); a=bpy.context.object.data; a.size=S*0.8; a.energy=600; a.color=(1,0.93,0.85)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=256; sc.cycles.use_denoising=True; sc.view_settings.view_transform='AgX'; sc.cycles.device='CPU'
sc.render.resolution_x=1200; sc.render.resolution_y=800; sc.world=bpy.data.worlds.new("w"); sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0.8,0.86,0.95,1); sc.world.node_tree.nodes['Background'].inputs[1].default_value=0.6
sc.render.filepath="/workspace/barclay/interior/live/latest.png"; bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(filepath="/workspace/barclay/interior/live/twobed.glb",export_format='GLB')
print("SIDE",S)
