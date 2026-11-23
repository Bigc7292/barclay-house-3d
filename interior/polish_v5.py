# lane/polish: apply the Two Bed interior fixes to the main-viewer model web/twobed_v5.glb (no builder exists for v5 in the repo;
# its node names/positions match build_twobed_v4.py exactly, so the same layout numbers are reused from interior/polish_layout.json).
# Materials / placement / AO bake only: no wall geometry change, no furniture model swap.
# Usage: ~/bvenv/bin/python polish_v5.py --in=<decoded ORIGINAL v5 .glb (no meshopt)> --out=<raw .glb> [--ao=2048] [--fix=1,...,8]
# r10 (23 Nov, Colin): fix1 is now a CC0 model swap (Poly Haven Wooden Display Shelves 01, CC0) at the block's footprint; 7 window backdrop clamp+street/canal image; 8 downlight dots; 6 stronger AO, fewer seams.
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); TX=ROOT+"/interior/tex/"
arg=lambda k,d=None: next((a.split('=',1)[1] for a in sys.argv if a.startswith(f'--{k}=')),d)
IN,OUT=arg('in'),arg('out'); RES=int(arg('ao','2048')); FIX={int(x) for x in arg('fix','1,2,3,4,5,6,7,8').split(',')}
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
    b=bsdf(MATS["Wall_warm_white"]); b.inputs["Base Color"].default_value=(0.70,0.67,0.62,1); b.inputs["Roughness"].default_value=0.94; log.append("fix4 wall")   # r10: 0.74->0.70 (washed-out walls)
if 5 in FIX:   # art: crisp 1024x1365 sRGB, UVs cover the whole canvas
    for mn,obn,img in (("Art_1_illustrative","Art_bed1","art_p5_1.jpg"),("Art_2_illustrative","Art_living","art_p5_2.jpg")):
        M=MATS[mn]; t=next(n for n in M.node_tree.nodes if n.type=='TEX_IMAGE'); t.image=bpy.data.images.load(TX+img); t.image.colorspace_settings.name='sRGB'
        single(O[obn]); uv_front(O[obn]); bsdf(M).inputs["Roughness"].default_value=0.6
    log.append("fix5 art")
if 1 in FIX:   # storage: plain block -> CC0 Poly Haven "Wooden Display Shelves 01" (CC0, https://polyhaven.com/a/wooden_display_shelves_01), fitted to the block's footprint
    sys.path.insert(0,ROOT+"/interior"); import furniture_cc0 as FC
    o=O["Storage_shelving_white"]; W=[o.matrix_world@v.co for v in o.data.vertices]
    lo=Vector([min(w[i] for w in W) for i in range(3)]); hi=Vector([max(w[i] for w in W) for i in range(3)]); sz=hi-lo
    pr=FC.load_prototype("shelves",FC._ph("wooden_display_shelves_01"),front="+X",decimate_tris=3000)
    e=FC.instance("shelves","Storage_shelving_CC0_polyhaven_wooden_display_shelves_01",((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z),math.pi/2)   # front -Y -> +X (into the store)
    d=pr["cc0_final_dims"]; e.scale=(sz.y/d[0],sz.x/d[1],sz.z/d[2]); e["cc0_source"]="https://polyhaven.com/a/wooden_display_shelves_01"; e["licence"]="CC0"
    for ch in list(pr.children): bpy.data.objects.remove(ch,do_unlink=True)
    bpy.data.objects.remove(pr,do_unlink=True); bpy.data.objects.remove(o,do_unlink=True); O.pop("Storage_shelving_white")
    log.append(f"fix1 storage CC0 {tuple(round(x,3) for x in sz)}")
if 2 in FIX:   # vanity/basin/tap/mirror off the corner + no wall clipping: node TRS recorded in glTF Y-up frame -> Blender Z-up
    for k,v in LAY["vanity_nodes"].items():
        t,sc_=v["t"],v["s"]; o=O[k]; o.location=Vector((t[0],-t[2],t[1])); o.scale=Vector((sc_[0],sc_[2],sc_[1]))
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
if 7 in FIX:   # window backdrops: top clamped below the wall tops (dollhouse view) + plausible street/canal image, still UNSOURCED
    TOP=2.97; img=bpy.data.images.load(TX+"sky_backdrop_p10.jpg"); n=0
    for o in [o for o in sc.objects if o.type=='MESH' and o.name.endswith("_backdrop")]:
        single(o); mw=o.matrix_world; inv=mw.inverted(); W=[mw@v.co for v in o.data.vertices]; z0=min(w.z for w in W); z1=max(w.z for w in W)
        if z1>TOP:
            for v,w in zip(o.data.vertices,W): v.co=inv@Vector((w.x,w.y,z0+(w.z-z0)*(TOP-z0)/(z1-z0)))
        for M in o.data.materials:
            for t in M.node_tree.nodes:
                if t.type=='TEX_IMAGE': t.image=img
        n+=1
    log.append(f"fix7 backdrops {n}")
if 8 in FIX:   # downlights: emissive discs read as hard white dots in three (emissive clips) -> dim warm glow
    for M in {m for o in sc.objects if o.type=='MESH' and o.name.startswith("Downlight_") and not o.name.startswith("Downlight_trim") for m in o.data.materials if m}:
        b=bsdf(M); b.inputs["Base Color"].default_value=(0.78,0.74,0.68,1); b.inputs["Emission Color"].default_value=(1,0.84,0.62,1); b.inputs["Emission Strength"].default_value=0.28
    log.append("fix8 downlights")
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
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.008,area_weight=1.0,scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    img=bpy.data.images.new("ao_bake",RES,RES,float_buffer=True)
    used={m for o in aos for m in o.data.materials if m}
    for M in used:
        n=M.node_tree.nodes.new("ShaderNodeTexImage"); n.image=img; n.name="AO_BAKE"; M.node_tree.nodes.active=n
    sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=int(arg('aos','96'))
    if not sc.world: sc.world=bpy.data.worlds.new("w")
    sc.world.light_settings.distance=0.9; sc.render.bake.margin=16   # r10: longer AO reach + wider margin (fewer seams at island borders)
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
    a=np.clip(0.07+0.93*np.clip(a,0,1)**1.35,0,1)    # r10: stronger contact AO (floor 0.18->0.07, gamma 1.35); still never fully black
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
