# Two Bed, furnished. Room layout SCALED FROM RIGHTMOVE PLAN IMAGE (Apt 02/03), APPROXIMATE; total fixed to sourced 63 m2.
# Floor-to-floor 3.663 m (E05) used as wall height (clear ceiling height NOT FOUND). Furniture: Poly Haven CC0 models + simple boxes
# for items with no CC0 model (beds, kitchen, bathroom). Bed size = UK standard double 135x190 cm (standard, not sourced to the flat).
import bpy, math, os
A="/workspace/barclay/interior/assets/"; TX="/workspace/barclay/interior/tex/"
ROOMS={ # name: (x0,y0,x1,y1) px on 270x350 plan image
 "Bedroom_1":(12,50,120,185),"Bedroom_2":(120,30,262,150),"Living":(140,150,262,240),"Kitchen_Dining":(155,240,262,345),
 "Storage":(15,200,90,270),"Bathroom":(15,270,85,345),"Entrance_hall":(85,190,155,345)}
# entrance hall px rect overlaps nothing else except Living gap; compute scale on listed areas
pxA=sum((r[2]-r[0])*(r[3]-r[1]) for r in ROOMS.values()); K=math.sqrt(63.0/pxA); H=3.663; T=0.1
CX,CY=137,190
def m(px,py): return ((px-CX)*K, -(py-CY)*K)
bpy.ops.wm.read_factory_settings(use_empty=True)
def pmat(n,c,r=0.5,met=0,tex=None,scale=1):
    M=bpy.data.materials.new(n);M.use_nodes=True;N=M.node_tree.nodes;b=N["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*c,1);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=met
    if tex:
        tc=N.new("ShaderNodeTexCoord");mp=N.new("ShaderNodeMapping");mp.inputs["Scale"].default_value=(scale,scale,scale)
        M.node_tree.links.new(tc.outputs["UV"],mp.inputs[0])
        for k,slot in (("diff","Base Color"),("rough","Roughness")):
            i=N.new("ShaderNodeTexImage");i.image=bpy.data.images.load(TX+f"{tex}_{k}.jpg")
            if k!="diff": i.image.colorspace_settings.name="Non-Color"
            M.node_tree.links.new(mp.outputs[0],i.inputs[0]);M.node_tree.links.new(i.outputs[0],b.inputs[slot])
        i=N.new("ShaderNodeTexImage");i.image=bpy.data.images.load(TX+f"{tex}_nor_gl.jpg");i.image.colorspace_settings.name="Non-Color"
        nm=N.new("ShaderNodeNormalMap");M.node_tree.links.new(mp.outputs[0],i.inputs[0]);M.node_tree.links.new(i.outputs[0],nm.inputs[1]);M.node_tree.links.new(nm.outputs[0],b.inputs["Normal"])
    return M
WOOD=pmat("Floor_oak_PolyHaven_wood_floor",(1,1,1),tex="wood_floor",scale=0.5)
TILE=pmat("Floor_tile_grey",(0.55,0.55,0.56),0.35)
WALL=pmat("Wall_paint_white",(0.88,0.87,0.84),0.9)
WHITE=pmat("Gloss_white",(0.9,0.9,0.9),0.15)
ANTH=pmat("Kitchen_anthracite",(0.08,0.085,0.09),0.35)
WORK=pmat("Worktop_light",(0.75,0.72,0.66),0.3)
STEEL=pmat("Steel",(0.8,0.8,0.8),0.25,1)
GLASS=pmat("Shower_glass",(0.9,0.95,0.95),0.02); GLASS.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value=1
FAB=pmat("Bed_fabric_grey",(0.35,0.36,0.38),0.95); LIN=pmat("Bed_linen_white",(0.92,0.92,0.9),0.9)
def box(n,x0,y0,x1,y1,z0,z1,M):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2));o=bpy.context.object;o.name=n
    o.scale=(abs(x1-x0),abs(y1-y0),z1-z0);bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.modifier_add(type='BEVEL');o.modifiers[-1].width=0.01;o.modifiers[-1].segments=2
    o.data.materials.append(M);
    bpy.ops.object.shade_smooth_by_angle() if hasattr(bpy.ops.object,'shade_smooth_by_angle') else None
    return o
R={k:(m(v[0],v[3])+m(v[2],v[1])) for k,v in ROOMS.items()}  # x0,y0,x1,y1 metres (y up = north on image top)
allx=[v[0] for v in R.values()]+[v[2] for v in R.values()];ally=[v[1] for v in R.values()]+[v[3] for v in R.values()]
box("Floor_base_under_gaps",min(allx),min(ally),max(allx),max(ally),-0.04,-0.005,WOOD)
for k,(x0,y0,x1,y1) in R.items():
    box("Floor_"+k,x0,y0,x1,y1,-0.02,0,TILE if k=="Bathroom" else WOOD)
# walls: perimeter of each room, door gaps (0.9 m) on given side
DOOR={"Bedroom_1":"E","Bedroom_2":"S","Storage":"E","Bathroom":"E","Living":None,"Kitchen_Dining":None,"Entrance_hall":"S"}
OPEN={"Living":"WS","Kitchen_Dining":"NW","Entrance_hall":"NE"}  # open-plan sides (no wall) per plan
for k,(X0,Y0,X1,Y1) in R.items():
    x0,y0,x1,y1=X0+T/2,Y0+T/2,X1-T/2,Y1-T/2
    for side,(a,b,c,d) in {"N":(x0,y1,x1,y1),"S":(x0,y0,x1,y0),"W":(x0,y0,x0,y1),"E":(x1,y0,x1,y1)}.items():
        if side in OPEN.get(k,""): continue
        hz=(b==d); L=(c-a) if hz else (d-b)
        segs=[(0,L)]
        if DOOR.get(k)==side and L>1.2: segs=[(0,L/2-0.45),(L/2+0.45,L)]
        for s0,s1 in segs:
            if hz: box(f"Wall_{k}_{side}",a+s0,b-T/2,a+s1,b+T/2,0,H,WALL)
            else: box(f"Wall_{k}_{side}",a-T/2,b+s0,a+T/2,b+s1,0,H,WALL)
def imp(name,loc,rot=0,target_w=None):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=A+f"{name}/{name}.gltf"); objs=bpy.context.selected_objects
    root=[o for o in objs if o.parent is None]
    for o in root: o.location=(loc[0],loc[1],0); o.rotation_euler[2]=math.radians(rot)
    if target_w:
        bpy.context.view_layer.update(); import mathutils
        xs=[(ob.matrix_world@mathutils.Vector(c)) for ob in objs if ob.type=='MESH' for c in ob.bound_box]
        w=max(max(v.x for v in xs)-min(v.x for v in xs),max(v.y for v in xs)-min(v.y for v in xs)); f=target_w/w
        for o in root: o.scale=(o.scale[0]*f,o.scale[1]*f,o.scale[2]*f)
    return objs
def bed(n,cx,cy,rot):
    w,l=1.35,1.9; c,s=math.cos(math.radians(rot)),math.sin(math.radians(rot))
    o1=box(n+"_ottoman_base",-w/2,-l/2,w/2,l/2,0,0.35,FAB);o2=box(n+"_mattress",-w/2+0.02,-l/2+0.02,w/2-0.02,l/2-0.05,0.35,0.6,LIN)
    o3=box(n+"_winged_headboard",-w/2-0.08,l/2-0.05,w/2+0.08,l/2+0.05,0,1.2,FAB)
    for o in (o1,o2,o3): o.location=(cx,cy,o.location.z); o.rotation_euler[2]=math.radians(rot)
# Bedroom 1
x0,y0,x1,y1=R["Bedroom_1"]; bed("Bed1",(x0+x1)/2,(y0+y1)/2+0.2,0); imp("ClassicNightstand_01",(x0+0.4,y1-0.4)); imp("drawer_cabinet",(x1-0.5,y0+0.4),90)
x0,y0,x1,y1=R["Bedroom_2"]; bed("Bed2",(x0+x1)/2,(y0+y1)/2+0.2,0); imp("ClassicNightstand_01",(x1-0.4,y1-0.4)); imp("drawer_cabinet",(x0+0.5,y0+0.4),90)
x0,y0,x1,y1=R["Living"]; imp("sofa_02",(x1-0.6,(y0+y1)/2),90); imp("modern_coffee_table_01",((x0+x1)/2+0.3,(y0+y1)/2)); imp("modern_wooden_cabinet",(x0+0.35,(y0+y1)/2),-90)
x0,y0,x1,y1=R["Kitchen_Dining"]
box("Kitchen_base_units",x1-0.6,y0,x1,y1-0.3,0,0.87,ANTH); box("Worktop",x1-0.62,y0,x1,y1-0.3,0.87,0.91,WORK)
box("Hob",x1-0.5,(y0+y1)/2-0.3,x1-0.1,(y0+y1)/2+0.3,0.91,0.92,ANTH); box("Fridge_freezer_tall_unit",x1-0.6,y0,x1,y0+0.6,0,2.1,ANTH)
box("Wall_units",x1-0.35,y0+0.6,x1,y1-0.3,1.45,2.2,ANTH)
imp("round_wooden_table_01",((x0+x1)/2-0.5,(y0+y1)/2+0.3),0,0.9)
for i,(dx,dy,r) in enumerate([(-0.6,0,90),(0.6,0,-90),(0,0.6,180),(0,-0.6,0)]): imp("dining_chair_02",((x0+x1)/2-0.5+dx*1.2,(y0+y1)/2+0.3+dy*1.2),r)
x0,y0,x1,y1=R["Bathroom"]
box("Shower_tray",x0,y0,x0+0.9,y0+0.9,0,0.05,WHITE); box("Shower_screen",x0+0.9,y0,x0+0.91,y0+0.9,0.05,2.0,GLASS)
box("WC",x0+0.1,y1-0.7,x0+0.5,y1-0.1,0,0.42,WHITE); box("Basin",x1-0.5,y1-0.6,x1-0.05,y1-0.1,0.8,0.88,WHITE); box("Mirrored_cabinet",x1-0.5,y1-0.12,x1-0.05,y1-0.05,1.2,1.8,STEEL)
x0,y0,x1,y1=R["Storage"]; box("Storage_shelving",x0+0.05,y0+0.05,x0+0.4,y1-0.05,0,2.2,WORK)
# lights: one warm area light per room at ceiling
for k,(x0,y0,x1,y1) in R.items():
    bpy.ops.object.light_add(type='AREA',location=((x0+x1)/2,(y0+y1)/2,H-0.1));l=bpy.context.object;l.name="Light_"+k
    l.data.size=min(x1-x0,y1-y0)*0.5;l.data.energy=180*(x1-x0)*(y1-y0)/10;l.data.color=(1,0.9,0.78)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True;sc.view_settings.view_transform='AgX'
sc.world=bpy.data.worlds.new("w");sc.world.use_nodes=True;bg=sc.world.node_tree.nodes['Background']
env=sc.world.node_tree.nodes.new("ShaderNodeTexEnvironment");env.image=bpy.data.images.load("/workspace/barclay/hdri.exr");sc.world.node_tree.links.new(env.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=0.4
sc.render.resolution_x=1600;sc.render.resolution_y=1000
def shot(name,loc,tgt,lens=24):
    bpy.ops.object.camera_add(location=loc);c=bpy.context.object;import mathutils
    c.rotation_euler=(mathutils.Vector(tgt)-mathutils.Vector(loc)).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;sc.camera=c
    sc.render.filepath=f"/workspace/barclay/interior/live/{name}.png";bpy.ops.render.render(write_still=True)
shot("latest",(0.5,-9,10),(0.3,0.5,0),28)
xs=R["Kitchen_Dining"];shot("closeup_living_kitchen",(xs[0]+0.3,xs[1]+0.4,1.6),(xs[2]-0.5,xs[3]+2.5,0.9),16)
xs=R["Bedroom_2"];shot("closeup_bedroom2",(xs[0]+0.4,xs[1]+0.4,1.6),((xs[0]+xs[2])/2,(xs[1]+xs[3])/2+0.5,0.5),16)
# export: lights excluded (viewer adds its own)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type=='MESH': o.select_set(True)
bpy.ops.export_scene.gltf(filepath="/workspace/barclay/interior/live/twobed_raw.glb",export_format='GLB',use_selection=True,export_apply=True,export_image_format='JPEG')
print("K",K,"rooms",{k:round((v[2]-v[0])*(v[3]-v[1]),1) for k,v in R.items()})
