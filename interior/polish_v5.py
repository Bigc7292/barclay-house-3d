# lane/polish: apply the Two Bed interior fixes to the main-viewer model web/twobed_v5.glb (no builder exists for v5 in the repo;
# its node names/positions match build_twobed_v4.py exactly, so the same layout numbers are reused from interior/polish_layout.json).
# Materials / placement / AO bake only: no wall geometry change, no furniture model swap.
# Usage: ~/bvenv/bin/python polish_v5.py --in=<decoded v5 .glb (no meshopt)> --out=<raw .glb> [--ao=2048] [--fix=1,2,3,4,5,6]
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); TX=ROOT+"/interior/tex/"
arg=lambda k,d=None: next((a.split('=',1)[1] for a in sys.argv if a.startswith(f'--{k}=')),d)
IN,OUT=arg('in'),arg('out'); RES=int(arg('ao','2048')); FIX={int(x) for x in arg('fix','1,2,3,4,5,6').split(',')}
LAY=json.load(open(ROOT+"/interior/polish_layout.json"))
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
bpy.ops.import_scene.gltf(filepath=IN)
O={o.name:o for o in sc.objects}; MATS=bpy.data.materials
def bsdf(M): return next(n for n in M.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def uv_front(o,plain=(0.15,0.55)):
    """+/-X world-facing faces -> 0..1 over their bbox (image upright, not mirrored); other faces -> one plain texel"""
    me=o.data; mw=o.matrix_world
    if not me.uv_layers: me.uv_layers.new(name="UVMap")
    uv=me.uv_layers[0]; W=[mw@v.co for v in me.vertices]
    ys=[w.y for w in W]; zs=[w.z for w in W]; y0,y1,z0,z1=min(ys),max(ys),min(zs),max(zs); R=mw.to_3x3()
    for f in me.polygons:
        nx=(R@f.normal).normalized().x
        for li in f.loop_indices:
            w=W[me.loops[li].vertex_index]
            if abs(nx)>0.7: uu=(w.y-y0)/(y1-y0); uv.data[li].uv=(uu if nx>0 else 1-uu,(w.z-z0)/(z1-z0))
            else: uv.data[li].uv=(plain[0]+0.002*(w.y-y0)/(y1-y0),plain[1]+0.002*(w.z-z0)/(z1-z0))
def single(o):
    if o.data.users>1: o.data=o.data.copy()
log=[]
if 4 in FIX:   # walls: albedo V 0.86->0.74, matte
    b=bsdf(MATS["Wall_warm_white"]); b.inputs["Base Color"].default_value=(0.74,0.71,0.66,1); b.inputs["Roughness"].default_value=0.92; log.append("fix4 wall")
if 5 in FIX:   # art: crisp 1024x1365 sRGB, UVs cover the whole canvas
    for mn,obn,img in (("Art_1_illustrative","Art_bed1","art_p5_1.jpg"),("Art_2_illustrative","Art_living","art_p5_2.jpg")):
        M=MATS[mn]; t=next(n for n in M.node_tree.nodes if n.type=='TEX_IMAGE'); t.image=bpy.data.images.load(TX+img); t.image.colorspace_settings.name='sRGB'
        single(O[obn]); uv_front(O[obn]); bsdf(M).inputs["Roughness"].default_value=0.6
    log.append("fix5 art")
if 1 in FIX:   # storage: same mesh, painted doors/drawers/handles/plinth + normal map
    M=bpy.data.materials.new("Storage_doors_white_satin"); M.use_nodes=True; N=M.node_tree.nodes; L=M.node_tree.links; b=N["Principled BSDF"]
    t=N.new("ShaderNodeTexImage"); t.image=bpy.data.images.load(TX+"storage_front_diff.jpg"); L.new(t.outputs[0],b.inputs["Base Color"]); b.inputs["Roughness"].default_value=0.4
    tn=N.new("ShaderNodeTexImage"); tn.image=bpy.data.images.load(TX+"storage_front_nor_gl.png"); tn.image.colorspace_settings.name="Non-Color"
    nm=N.new("ShaderNodeNormalMap"); L.new(tn.outputs[0],nm.inputs[1]); L.new(nm.outputs[0],b.inputs["Normal"])
    o=O["Storage_shelving_white"]; single(o); o.data.materials.clear(); o.data.materials.append(M); uv_front(o,(0.1,0.6)); log.append("fix1 storage")
if 2 in FIX:   # vanity/basin/tap/mirror: new centre (Blender Z-up) + size ratio vs v4 sizes
    OLD={"Vanity_grey_stone_look":(0.6,0.46,0.3),"Basin_white_wallhung":(0.56,0.42,0.12),"Mirror_black_frame":(0.55,0.02,0.75),"Mirror_glass":(0.5,0.006,0.7)}
    for k,(loc,size) in LAY["vanity"].items():
        o=O[k]; o.location=Vector(loc); print('VAN',k,tuple(round(x,4) for x in o.scale),tuple(round(x,3) for x in o.rotation_euler))
        if size: o.scale=Vector([o.scale[i]*size[i]/OLD[k][i] for i in range(3)])   # multiply: dequantized nodes carry a non-unit scale
    log.append("fix2 vanity")
if 3 in FIX:   # beds + bedsides: rigid move old pivot -> new pivot
    BEDP=("Bed_base","Mattress","Duvet","Throw","Pillow","Scatter_cushion","Cushion_navy","Headboard")
    taken=set()
    for g in LAY["groups"]:
        (ox,oy,oa),(nx,ny,na)=g["old"],g["new"]
        Mx=Matrix.Translation((nx,ny,0))@Matrix.Rotation(na-oa,4,'Z')@Matrix.Translation((-ox,-oy,0))
        pref,rad=(BEDP,1.5) if g["kind"]=="bed" else (("Bedside","Lamp_"),0.36)
        sel=[o for o in sc.objects if o.type=='MESH' and o.name not in taken and o.name.startswith(pref) and (Vector((o.matrix_world.translation.x-ox,o.matrix_world.translation.y-oy))).length<rad]
        for o in sel: o.matrix_world=Mx@o.matrix_world; taken.add(o.name)
        log.append(f"fix3 {g['kind']} moved {len(sel)}")
bpy.context.view_layer.update()
if 6 in FIX:   # baked AO -> glTF occlusion (TEXCOORD_1) on the large static surfaces; light, so +size stays small
    AOM={"Wall_warm_white","Ceiling_warm_white","Floor_light_oak","Floor_pale_grey_woodlook_kitchen","Skirting_white_satin","Oak_furniture","Sanitary_white",
         "Kitchen_handleless_white","Door_white","Rug_cream","Quartz_white","Tile_grey_600x1200","Peninsula_graphite","Worktop_white","Vanity_grey",
         "Appliance_black_gloss","Bedding_white","Storage_doors_white_satin"}
    aos=[o for o in sc.objects if o.type=='MESH' and any(m and m.name in AOM for m in o.data.materials)]
    for o in aos:
        single(o)
        if len(o.data.uv_layers)==0: o.data.uv_layers.new(name="UVMap")
        u=o.data.uv_layers.new(name="ao"); o.data.uv_layers.active=u
    bpy.ops.object.select_all(action='DESELECT')
    for o in aos: o.select_set(True)
    bpy.context.view_layer.objects.active=aos[0]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.004,area_weight=1.0,scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    img=bpy.data.images.new("ao_bake",RES,RES,float_buffer=True)
    used={m for o in aos for m in o.data.materials if m}
    for M in used:
        n=M.node_tree.nodes.new("ShaderNodeTexImage"); n.image=img; n.name="AO_BAKE"; M.node_tree.nodes.active=n
    sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=int(arg('aos','96'))
    if not sc.world: sc.world=bpy.data.worlds.new("w")
    sc.world.light_settings.distance=0.6; sc.render.bake.margin=8
    bpy.ops.object.bake(type='AO'); print("AO BAKED",len(aos),"objects",len(used),"materials")
    # OIDN denoise in a throwaway scene (compositor only)
    dn=bpy.data.scenes.new("dn"); dn.render.engine='BLENDER_WORKBENCH'; dn.render.resolution_x=dn.render.resolution_y=RES
    cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); dn.collection.objects.link(cam); dn.camera=cam
    ng=bpy.data.node_groups.new("DN","CompositorNodeTree"); dn.compositing_node_group=ng; dn.render.use_compositing=True
    ni=ng.nodes.new("CompositorNodeImage"); ni.image=img; dd=ng.nodes.new("CompositorNodeDenoise")
    ng.interface.new_socket("Image",in_out='OUTPUT',socket_type='NodeSocketColor'); go=ng.nodes.new("NodeGroupOutput")
    ng.links.new(ni.outputs[0],dd.inputs["Image"]); ng.links.new(dd.outputs[0],go.inputs[0])
    tmp=OUT+".ao_dn.exr"; dn.render.image_settings.file_format='OPEN_EXR'; dn.render.filepath=tmp; bpy.ops.render.render(write_still=True,scene=dn.name)
    a=np.array(bpy.data.images.load(tmp).pixels[:]).reshape(RES,RES,4)[...,0]; os.remove(tmp)
    a=np.clip(0.18+0.82*np.clip(a,0,1),0,1)           # keep a floor so corners never go black under the viewer's env/hemi light
    px=np.ones((RES,RES,4),np.float32); px[...,0]=px[...,1]=px[...,2]=a
    out=bpy.data.images.new("ao_v5",RES,RES); out.colorspace_settings.name='Non-Color'; out.pixels.foreach_set(px.ravel())
    out.filepath_raw=os.path.dirname(OUT)+"/ao_v5.png"; out.file_format='PNG'; out.save()
    g=bpy.data.node_groups.get('glTF Material Output') or bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
    if not g.interface.items_tree: g.interface.new_socket('Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
    for M in used:
        N=M.node_tree.nodes; L=M.node_tree.links; N.remove(N["AO_BAKE"])
        uvn=N.new("ShaderNodeUVMap"); uvn.uv_map="ao"; t=N.new("ShaderNodeTexImage"); t.image=out; sp=N.new("ShaderNodeSeparateColor")
        gn=N.new("ShaderNodeGroup"); gn.node_tree=g; L.new(uvn.outputs[0],t.inputs[0]); L.new(t.outputs[0],sp.inputs[0]); L.new(sp.outputs[0],gn.inputs[0])
    for o in aos: o.data.uv_layers.active=o.data.uv_layers[0]
    bpy.data.scenes.remove(dn)   # else the exporter writes an empty 2nd scene (validator EMPTY_ENTITY)
    log.append(f"fix6 AO {RES} on {len(aos)} objects")
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',export_image_format='AUTO',export_lights=False,export_cameras=False,export_yup=True)
print("POLISH_V5",log)
