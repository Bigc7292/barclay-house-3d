# Barclay House Two Bed v2 (critic round 1 fixes). Outline + rooms SCALED FROM RIGHTMOVE PLAN IMAGE (apt02_fp.png), APPROXIMATE,
# total floor area fixed to sourced 63 m2. Finishes/furniture follow Rightmove CGI marketing images (scheme spec), illustrative.
# Unsourced: clear ceiling height (3.0 m used; floor-to-floor 3.663 m sourced), window positions, all furniture dimensions.
import bpy, bmesh, math, mathutils, sys, os
from mathutils import Vector
import furniture_cc0
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TX=os.path.join(ROOT,"interior","tex")+os.sep
OUT=os.path.join(ROOT,"interior","live")+os.sep
OUT=next((a.split('=',1)[1].rstrip('/')+'/' for a in sys.argv if a.startswith('--out=')),OUT); os.makedirs(OUT,exist_ok=True)   # lane/polish
import json
# lane/polish fixes (default all): 2 bathroom vanity/basin/mirror off the corner, 3 beds off the windows, 4 wall material, 5 art, 6 bake denoise+AO.
# (fix 1, storage block, is now the CC0 shelf from lane/furniture in this pipeline; the texture fix is applied to twobed_v5 by polish_v5.py)
_fx=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--fix=')),'2,3,4,5,6,7')   # 7: bathroom stone-look tile + window street backdrop (reference gate)
FIX=set() if _fx=='none' else {int(x) for x in _fx.split(',') if x}
print("FIX",sorted(FIX))
HDRI=os.path.join(ROOT,"hdri.exr")
SHOTS_R9=os.path.join(ROOT,"web","shots","r9")
P=[(12,62),(92,50),(98,40),(228,22),(262,180),(262,345),(18,345),(18,185)]
def parea(P): return abs(sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P))))/2
K=math.sqrt(63.0/parea(P)); CX,CY=137,190; CEIL=3.0; T=0.12
def m(x,y): return Vector(((x-CX)*K,-(y-CY)*K,0))
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
# ---------- materials (glTF-exportable: Principled + image textures only)
def mat(n,c,r=0.5,met=0,img=None,emit=None,ew=0,alpha=1,trans=0,nor=None):
    M=bpy.data.materials.new(n);M.use_nodes=True;N=M.node_tree.nodes;b=N["Principled BSDF"];L=M.node_tree.links
    b.inputs["Base Color"].default_value=(*c,1);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=met
    if img:
        i=N.new("ShaderNodeTexImage");i.image=bpy.data.images.load(TX+img);L.new(i.outputs[0],b.inputs["Base Color"])
    if nor:
        i=N.new("ShaderNodeTexImage");i.image=bpy.data.images.load(TX+nor);i.image.colorspace_settings.name="Non-Color"
        nm=N.new("ShaderNodeNormalMap");nm.inputs[0].default_value=0.4;L.new(i.outputs[0],nm.inputs[1]);L.new(nm.outputs[0],b.inputs["Normal"])
    if emit: b.inputs["Emission Color"].default_value=(*emit,1);b.inputs["Emission Strength"].default_value=ew
    if trans: b.inputs["Transmission Weight"].default_value=trans
    if alpha<1: b.inputs["Alpha"].default_value=alpha; M.blend_method='BLEND' if hasattr(M,'blend_method') else None
    return M
OAK=mat("Floor_light_oak",(1,1,1),0.55,img="oak_light_diff.jpg",nor="wood_floor_nor_gl.jpg")
OAKG=mat("Floor_pale_grey_woodlook_kitchen",(1,1,1),0.55,img="oak_grey_diff.jpg",nor="wood_floor_nor_gl.jpg")
TILE=mat("Tile_grey_600x1200",(1,1,1),0.3,img=("tile_stone_grey_p5.jpg" if 7 in FIX else "tile_light_r4.jpg"))
# fix4: wall albedo V 0.86->0.74 (less washed), matte 0.92
WALL=mat("Wall_warm_white",(0.74,0.71,0.66) if 4 in FIX else (0.86,0.83,0.78),0.92 if 4 in FIX else 0.85); CEILM=mat("Ceiling_warm_white",(0.9,0.88,0.84),0.9)
SKIRT=mat("Skirting_white_satin",(0.92,0.91,0.88),0.35)
WUNIT=mat("Kitchen_handleless_white",(0.9,0.89,0.86),0.3); DARK=mat("Peninsula_graphite",(0.042,0.042,0.045),0.5); QUARTZ=mat("Quartz_white",(0.88,0.88,0.87),0.25)
WTOP=mat("Worktop_white",(0.93,0.93,0.92),0.2); BLK=mat("Appliance_black_gloss",(0.015,0.015,0.017),0.12)
STEEL=mat("Stainless_steel",(0.8,0.8,0.8),0.22,1); CHROME=mat("Chrome",(0.9,0.9,0.9),0.05,1)
LED=mat("LED_strip_3000K",(1,0.85,0.65),0.5,emit=(1,0.78,0.55),ew=40)
NAVY=mat("Navy_velvet",(1,1,1),0.75,img="velvet_navy_diff.jpg"); BOUC=mat("Cream_boucle",(1,1,1),0.95,img="boucle_diff.jpg")
OAKF=mat("Oak_furniture",(0.62,0.42,0.24),0.5,img="oak_light_diff.jpg"); BMET=mat("Black_metal",(0.02,0.02,0.02),0.35,0.8)
LIN=mat("Bedding_white",(0.93,0.93,0.91),0.9); RUG=mat("Rug_cream",(0.86,0.82,0.74),1.0)
WHITEP=mat("Sanitary_white",(0.95,0.95,0.95),0.08); GREYV=mat("Vanity_grey",(0.45,0.45,0.46),0.4)
GLASS=mat("Glass_clear",(0.95,0.97,0.97),0.02,trans=1); WGLASS=mat("Window_glass_clear",(0.95,0.97,1),0.02,trans=1); SKY=mat("Window_backdrop_sky_UNSOURCED_VIEW",(1,1,1),1,img=("sky_backdrop_p5.jpg" if 7 in FIX else "sky_backdrop_r4.jpg")); SKY.node_tree.links.new(SKY.node_tree.nodes["Image Texture"].outputs[0],SKY.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]); SKY.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value=1.2
FRAME=mat("Window_frame_black_steel",(0.015,0.015,0.015),0.4,0.6); DOOR=mat("Door_white",(0.9,0.9,0.88),0.4)
GLOBE=mat("Globe_pendant_opal",(1,0.97,0.92),0.3,emit=(1,0.8,0.6),ew=4); LAMPS=mat("Lamp_shade_opal",(1,0.97,0.92),0.3,emit=(1,0.8,0.6),ew=3)
LEAF=mat("Plant_leaf",(0.08,0.25,0.07),0.6); POT=mat("Pot_terracotta",(0.55,0.32,0.2),0.8); TVS=mat("TV_screen",(0.01,0.01,0.012),0.08)
DLM=mat("Downlight_3000K",(1,0.9,0.75),0.3,emit=(1,0.78,0.55),ew=15)
ART=[mat(f"Art_{i}_illustrative",(1,1,1),0.6,img=(f"art_p5_{i}.jpg" if 5 in FIX else f"art_r4_{i}.jpg")) for i in (1,2,3)]  # fix5: crisp sRGB 1024x1365 (tex/make_polish_tex.py)
# ---------- helpers
def obj_from(bm,n,M):
    me=bpy.data.meshes.new(n);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(n,me);sc.collection.objects.link(o);o.data.materials.append(M);return o
def box(n,c,s,M,rz=0,bev=0.004):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,vec=s,verts=bm.verts)
    uv=bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        ax=max(range(3),key=lambda i:abs(f.normal[i]))
        for l in f.loops:
            co=l.vert.co; a,b=[(co.y,co.z),(co.x,co.z),(co.x,co.y)][ax]; l[uv].uv=(a/1.2,b/1.2)
    o=obj_from(bm,n,M);o.location=c;o.rotation_euler[2]=rz
    if bev: md=o.modifiers.new("b","BEVEL");md.width=bev;md.segments=2;md.limit_method='ANGLE'
    return o
def uv_front(o,plain=(0.15,0.55)):
    """lane/polish: map the +/-X face of a box 0..1 across its bbox (texture shows whole image, right way round); other faces -> plain texel"""
    me=o.data; uv=me.uv_layers[0]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
    y0,y1,z0,z1=min(ys),max(ys),min(zs),max(zs)
    for f in me.polygons:
        for li in f.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            if abs(f.normal.x)>0.7: uu=(co.y-y0)/(y1-y0); uv.data[li].uv=(uu if f.normal.x>0 else 1-uu,(co.z-z0)/(z1-z0))
            else: uv.data[li].uv=(plain[0]+0.002*(co.y-y0)/(y1-y0),plain[1]+0.002*(co.z-z0)/(z1-z0))
    return o
def cyl(n,c,r,h,M,seg=32,r2=None):
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r if r2 is None else r2,depth=h)
    o=obj_from(bm,n,M);o.location=c;return o
def sph(n,c,r,M,sx=1,sy=1,sz=1):
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=32,v_segments=16,radius=r);o=obj_from(bm,n,M);o.location=c;o.scale=(sx,sy,sz)
    for f in o.data.polygons: f.use_smooth=True
    return o
def seg(n,a,b,h,M,t=T,z0=0,gaps=()):
    """wall from a to b (metres, Vectors), optional gaps [(s0,s1) metres along]"""
    d=b-a;L=d.length;ang=math.atan2(d.y,d.x);u=d/L;cuts=[0]+[g for gp in gaps for g in gp]+[L];out=[]
    for i in range(0,len(cuts),2):
        s0,s1=cuts[i],cuts[i+1]
        if s1-s0<0.02: continue
        c=a+u*((s0+s1)/2);out.append(box(f"{n}",(c.x,c.y,z0+h/2),(s1-s0,t,h),M,ang,0))
        if M is WALL: box(f"{n}_skirting",(c.x,c.y,0.05),(s1-s0,t+0.024,0.1),SKIRT,ang,0.002)
    for g in gaps:  # lintel above door
        if z0==0 and h>2.1:
            c=a+u*((g[0]+g[1])/2);box(f"{n}_lintel",(c.x,c.y,(2.1+h)/2),(g[1]-g[0],t,h-2.1),M,ang,0)
    return out
def poly_slab(n,pts,z0,z1,M,uvs=2.0):
    bm=bmesh.new();vs=[bm.verts.new((p.x,p.y,z1)) for p in pts];f=bm.faces.new(vs)
    ext=bmesh.ops.extrude_face_region(bm,geom=[f]);bmesh.ops.translate(bm,vec=(0,0,z0-z1),verts=[v for v in ext['geom'] if isinstance(v,bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);uv=bm.loops.layers.uv.new()
    for fc in bm.faces:
        for l in fc.loops: l[uv].uv=(l.vert.co.x/uvs,l.vert.co.y/uvs)
    return obj_from(bm,n,M)
def rect(x0,y0,x1,y1): return [m(x0,y1),m(x1,y1),m(x1,y0),m(x0,y0)]
OUTL=[m(*p) for p in P]
# ---------- floor: ONE continuous slab under whole unit, plus finish inlays
poly_slab("Floor_continuous_oak",OUTL,-0.05,0.0,OAK,1.2)
poly_slab("Floor_kitchen_pale_grey",rect(156,242,260,343),0.0,0.003,OAKG,1.2)
poly_slab("Floor_bathroom_tile",rect(19,271,85,344),0.0,0.004,TILE,1.2)
poly_slab("Ceiling",OUTL,CEIL,CEIL+0.05,CEILM,2)
# ---------- exterior walls (polygon edges), windows on edges flagged (positions UNSOURCED)
WIN={1:None,3:None,4:None}  # edge index -> window
def arched_window(n,a,b,frac,w,sill=0.5,head=2.75):
    d=(b-a);L=d.length;u=d/L;nrm=Vector((-u.y,u.x,0));c=a+u*(L*frac);ang=math.atan2(d.y,d.x)
    # inward normal: towards polygon centroid
    cen=sum(OUTL,Vector())/len(OUTL)
    if (cen-c).dot(nrm)<0: nrm=-nrm
    RD=0.30; c=c+nrm*(T/2+0.012)-nrm*RD; hr=w/2; hs=head-hr
    for sd in (-1,1):
        q=c+u*(sd*(hr+0.015))+nrm*(RD/2); box(n+"_reveal_side",(q.x,q.y,(sill+hs)/2),(0.03,RD+0.02,hs-sill),SKIRT,ang,0)
    q=c+nrm*(RD/2); box(n+"_reveal_sill",(q.x,q.y,sill-0.015),(w+0.06,RD+0.04,0.03),SKIRT,ang,0)
    for k in range(16):
        t0=math.pi*k/16;t1=math.pi*(k+1)/16;p0=Vector((math.cos(t0)*(hr+0.015),math.sin(t0)*(hr+0.015)));p1=Vector((math.cos(t1)*(hr+0.015),math.sin(t1)*(hr+0.015)));pm=(p0+p1)/2
        q=c+u*pm.x+nrm*(RD/2);box(n+"_reveal_soffit",(q.x,q.y,hs+pm.y),((p1-p0).length+0.02,RD+0.02,0.03),SKIRT,ang,0).rotation_euler=(0,-(t0+t1)/2+math.pi/2,ang)
    box(n+"_glass_daylight",(c.x,c.y,(sill+hs)/2),(w,0.01,hs-sill),WGLASS,ang,0)
    bm=bmesh.new();bmesh.ops.create_circle(bm,cap_ends=True,segments=32,radius=hr);o=obj_from(bm,n+"_glass_arch",WGLASS)
    for v in o.data.vertices:
        if v.co.y<0: v.co.y=0
    o.location=(c.x,c.y,hs);o.rotation_euler=(math.pi/2,0,ang)
    fw=0.05
    for k in range(5): xo=-hr+k*w/4; p=c+u*xo; box(n+"_mullion",(p.x,p.y,(sill+hs)/2),(fw,0.04,hs-sill),FRAME,ang,0)
    for z in (sill,sill+(hs-sill)/3,sill+2*(hs-sill)/3,hs): box(n+"_transom",(c.x,c.y,z),(w,0.04,fw),FRAME,ang,0)
    for sd in (-1,1): q=c+u*(sd*hr); box(n+"_jamb",(q.x,q.y,(sill+hs)/2),(0.07,T+0.02,hs-sill),FRAME,ang,0)
    for k in range(24):
        t0=math.pi*k/24;t1=math.pi*(k+1)/24;p0=Vector((math.cos(t0)*hr,math.sin(t0)*hr));p1=Vector((math.cos(t1)*hr,math.sin(t1)*hr));pm=(p0+p1)/2
        q=c+u*pm.x;box(n+"_arch_frame",(q.x,q.y,hs+pm.y),((p1-p0).length+0.01,0.04,fw),FRAME,ang,0).rotation_euler=(0,-(t0+t1)/2+math.pi/2,ang)
    box(n+"_sill",(c.x,c.y,sill-0.02),(w+0.1,0.08,0.04),SKIRT,ang,0)
    bp=c-nrm*(T+0.6); box(n+"_backdrop",(bp.x,bp.y,(sill+head)/2),(w+1.2,0.01,head-sill+1.0),SKY,ang,0)
    lp=c-nrm*(T+0.45); bpy.ops.object.light_add(type='AREA',location=(lp.x,lp.y,(sill+head)/2)); L_=bpy.context.object; L_.name=n+"_daylight"
    L_.data.shape='RECTANGLE'; L_.data.size=w; L_.data.size_y=head-sill; L_.data.energy=180; L_.data.color=(0.95,0.97,1)
    L_.rotation_euler=Vector((0,0,1)).rotation_difference(nrm).to_euler()
for i in range(len(OUTL)):
    a,b=OUTL[i],OUTL[(i+1)%len(OUTL)]; L=(b-a).length
    gaps=()
    if i==6: gaps=((L-((128-18)*K),L-((100-18)*K)),)  # entrance door on bottom edge (from plan)
    WS={0:(0.5,1.3),2:(0.5,1.6),3:(0.72,1.6)}
    if i in WS:
        fr,w=WS[i]; s0,s1=L*fr-w/2,L*fr+w/2; d=(b-a).normalized(); ang=math.atan2(d.y,d.x)
        seg(f"Wall_ext_{i}",a,b,CEIL,WALL,gaps=((s0,s1),))
        # wall below sill and above arch head
        c=a+d*(L*fr); box(f"Wall_ext_{i}_below_sill",(c.x,c.y,0.25),(w,T,0.5),WALL,ang,0); box(f"Wall_ext_{i}_above_head",(c.x,c.y,(2.75+CEIL)/2),(w,T,CEIL-2.75),WALL,ang,0)
        # spandrels (square corners above the arch springing, rendered as wall)
        for sd in (-1,1):
            q=c+d*(sd*w*0.36); box(f"Wall_ext_{i}_spandrel",(q.x,q.y,2.75-w/4+0.01),(w*0.28,T,w/2*0.5),WALL,ang,0)
        arched_window(f"Window_{i}_POSITION_UNSOURCED",a,b,fr,w)
    else: seg(f"Wall_ext_{i}",a,b,CEIL,WALL,gaps=gaps)



# ---------- partitions (traced from plan image), door gaps 0.85 m
def part(n,p0,p1,gap_at=None,gw=0.85):
    a,b=m(*p0),m(*p1);L=(b-a).length;g=()
    if gap_at is not None: s=L*gap_at;g=((s-gw/2,s+gw/2),)
    seg(n,a,b,CEIL,WALL,gaps=g);return a,b,g
B12=part("Wall_bed1_bed2",(105,45),(120,152))
B1S=part("Wall_bed1_south",(18,185),(120,152),gap_at=0.8)
B2S=part("Wall_bed2_south",(120,152),(215,140),gap_at=0.2)
part("Wall_storage_north",(18,200),(90,200)); ST=part("Wall_storage_east",(90,200),(90,270),gap_at=0.5)
part("Wall_bath_north",(18,270),(90,270)); BA=part("Wall_bath_east",(86,270),(86,345),gap_at=0.6)
def door(n,hinge,ang_closed,w=0.8,openang=95):
    o=box(n,(0,0,1.05),(w,0.04,2.08),DOOR,0,0.003);
    e=bpy.data.objects.new(n+"_pivot",None);sc.collection.objects.link(e);e.location=(hinge.x,hinge.y,0);o.parent=e;o.location=(w/2,0,1.05)
    e.rotation_euler[2]=ang_closed+math.radians(openang)
def door_in(wall,side=1,openang=-95):
    a,b,g=wall;u=(b-a).normalized();h=a+u*g[0][0];door(f"Door_{wall[0].x:.1f}",h,math.atan2(u.y,u.x),openang=openang*side)
door_in(B1S,1);door_in(B2S,1,95);door_in(ST,1,95);door_in(BA,1,95)
ent=OUTL[6]+(OUTL[5]-OUTL[6]).normalized()*0.0; ea=m(100,345); door("Door_entrance",ea,0,0.9,80)
# ---------- downlights (recessed) + glTF point lights 3000K
import itertools
def inside(p,poly):
    c=False;j=len(poly)-1
    for i in range(len(poly)):
        if ((poly[i].y>p.y)!=(poly[j].y>p.y)) and (p.x<(poly[j].x-poly[i].x)*(p.y-poly[i].y)/(poly[j].y-poly[i].y)+poly[i].x): c=not c
        j=i
    return c
xs=[p.x for p in OUTL];ys=[p.y for p in OUTL];k=0
x=min(xs)+0.9
while x<max(xs):
    y=min(ys)+0.9
    while y<max(ys):
        if inside(Vector((x,y)),OUTL):
            cyl(f"Downlight_{k}",(x,y,CEIL-0.003),0.045,0.006,DLM)
            bpy.ops.object.light_add(type='POINT',location=(x,y,CEIL-0.08));l=bpy.context.object;l.name=f"DL_light_{k}";l.data.energy=55;l.data.color=(1,0.78,0.55);l.data.shadow_soft_size=0.05;k+=1
        y+=1.6
    x+=1.6
# ---------- FURNITURE (CC0 module; existing positions/rotations preserved)
_furn_mats=dict(WUNIT=WUNIT,DARK=DARK,QUARTZ=QUARTZ,WTOP=WTOP,BLK=BLK,STEEL=STEEL,CHROME=CHROME,
                LED=LED,NAVY=NAVY,BOUC=BOUC,OAKF=OAKF,LIN=LIN,WHITEP=WHITEP,GREYV=GREYV,GLASS=GLASS,
                BMET=BMET,LAMPS=LAMPS,TILE=TILE,TVS=TVS,FRAME=FRAME)
# lane/polish placement (fix3 beds, fix2 vanity): passed to furniture_cc0.place_all as overrides; models unchanged
LAYOUT={"_note":"lane/polish fix3: beds moved off the windows, heads on the walls shown in interior/twobed/apt02_fp.png (bed1 head on the bed1/bed2 partition, bed2 head on the east wall). fix2: vanity+mirror centre x. Blender Z-up metres; twobed_v5 uses the same frame (interior/polish_v5.py).","groups":[]}
def _wallbed(a,b,t,bs_off,want_west=True):
    u=(b-a).normalized(); n=Vector((-u.y,u.x,0))
    if (n.x<0)!=want_west: n=-n
    wp=a+u*t; ang=math.atan2(n.x,-n.y)                 # bed local +Y (headboard) -> -n (into wall)
    c=wp+n*(T/2+0.12+1.025+0.01); sides=[wp+n*(T/2+0.2+0.03)+u*s for s in (-bs_off,bs_off)]
    return (c.x,c.y,ang),[(q.x,q.y,ang) for q in sides]
_b1,_b2=m(55,105),m(185,70)
_o1=(_b1.x,m(0,62).y-1.15,0.0); _o1s=[(_b1.x-1.0,m(0,62).y-0.35,0.0),(_b1.x+1.0,m(0,62).y-0.35,0.0)]
_o2=(_b2.x,m(0,40).y-1.3,0.06); _o2s=[(_b2.x-1.0,m(0,40).y-0.45,0.06),(_b2.x+1.0,m(0,40).y-0.5,0.06)]
POLISH={}
if 3 in FIX:
    _a,_b=m(105,45),m(120,152); _n1,_n1s=_wallbed(_a,_b,(_b-_a).length*(95-45)/107,1.0)
    _n2,_n2s=_wallbed(OUTL[3],OUTL[4],1.30,0.96)   # east wall: bedsides fit between north wall and window jamb
    POLISH.update(bed1=_n1,bed1_sides=_n1s,bed2=_n2,bed2_sides=_n2s)
else: _n1,_n1s,_n2,_n2s=_o1,_o1s,_o2,_o2s
for k_,o_,n_ in [("bed",_o1,_n1)]+[("bedside",a_,b_) for a_,b_ in zip(_o1s,_n1s)]+[("bed",_o2,_n2)]+[("bedside",a_,b_) for a_,b_ in zip(_o2s,_n2s)]:
    LAYOUT["groups"].append({"kind":k_,"old":[round(v,4) for v in o_],"new":[round(v,4) for v in n_]})
if 2 in FIX: POLISH["vanity_x"]=m(19,344).x+1.145   # off the NE corner (was beside the camera / frame edge), clear of the WC
placed=furniture_cc0.place_all(dict(sc=sc,m=m,T=T,CEIL=CEIL,box=box,cyl=cyl,sph=sph,mats=_furn_mats,Vector=Vector,math=math,ROOT=ROOT,polish=POLISH))
kx,ky0,ky1,sx,sofa_y,ct,tvx,dc,b1,b2=placed["kx"],placed["ky0"],placed["ky1"],placed["sx"],placed["sofa_y"],placed["ct"],placed["tvx"],placed["dc"],placed["b1"],placed["b2"]
bx0,by0,bx1,by1,wcy,wx0,vx=placed["bx0"],placed["by0"],placed["bx1"],placed["by1"],placed["wcy"],placed["wx0"],placed["vx"]
bx1=m(85,271).x   # lane/polish: placed["bx1"] returns by1 (typo in furniture_cc0 return dict); recompute here

# decorations that stay procedural (no suitable standalone CC0 model, or not in the swap list)
box("Rug_cream",(sx-1.35,sofa_y,0.006),(1.7,2.3,0.012),RUG,0,0.003)
box("Coffee_book",(ct.x+0.1,ct.y-0.25,0.455),(0.22,0.3,0.03),RUG,0,0.003)
box("TV_stand_black",(tvx,sofa_y,0.55),(0.18,0.3,0.02),BMET,0,0); box("TV_stand_post",(tvx-0.02,sofa_y,0.62),(0.03,0.06,0.14),BMET,0,0)
box("TV_bezel_black_facing_sofa",(tvx-0.02,sofa_y,0.98),(0.04,1.12,0.66),BLK,0,0.004); box("TV_screen",(tvx+0.001,sofa_y,0.99),(0.002,1.08,0.61),TVS,0,0)
box("Art_living_frame",(sx+0.44,sofa_y,1.6),(0.03,0.8,1.05),BMET,0,0); _a=box("Art_living",(sx+0.42,sofa_y,1.6),(0.01,0.72,0.97),ART[1],0,0)
if 5 in FIX: uv_front(_a)
pp=Vector((sx,sofa_y+1.4,0)); cyl("Plant_pot",(pp.x,pp.y,0.2),0.18,0.4,POT,24,0.14)
for j in range(9): a=j*0.7; sph("Plant_leaf",(pp.x+0.25*math.cos(a)*(j%3)/2,pp.y+0.25*math.sin(a)*(j%3)/2,0.75+0.12*(j%4)),0.18,LEAF,1.2,0.5,0.25)

# --- geometric chair facing check (print + assert) ---
_chairs=[o for o in sc.objects if o.name.startswith("Tub_chair_cream_boucle") and o.parent is None]
print("CHAIR_COUNT",len(_chairs))
assert len(_chairs)==4, f"expected 4 chairs, got {len(_chairs)}"
for e in _chairs:
    ang=e.rotation_euler[2]; pos=e.location.copy()
    # opening = local -Y after Z rot; backrest = local +Y
    open_dir=Vector((math.sin(ang),-math.cos(ang),0)).normalized()
    back_dir=Vector((-math.sin(ang),math.cos(ang),0)).normalized()
    to_table=(dc-pos); to_table.z=0; to_table.normalize()
    dot=open_dir.dot(to_table)
    d_back=(pos+back_dir*0.25-dc).length; d_open=(pos+open_dir*0.25-dc).length
    ok=dot>0.9 and d_back>d_open
    print(f"CHAIR_CHECK name={e.name} pos=({pos.x:.3f},{pos.y:.3f},{pos.z:.3f}) rot_z={ang:.4f} open_dir=({open_dir.x:.3f},{open_dir.y:.3f}) to_table=({to_table.x:.3f},{to_table.y:.3f}) dot={dot:.3f} d_back={d_back:.3f} d_open={d_open:.3f} PASS={ok}")
    assert ok, "chair facing failed geometric check"
print("CHAIR_CHECK_ALL_PASS")
# dining top-down + 3/4 Blender stills (always, even with --noshots, unless --only names other shots)
_skip_dining=("--only" in sys.argv and "dining_top" not in sys.argv and "dining_34" not in sys.argv)
if not _skip_dining:
    os.makedirs(SHOTS_R9,exist_ok=True)
    _sc=sc; _sc.render.engine='CYCLES'; _sc.cycles.samples=24; _sc.cycles.use_denoising=True
    _sc.render.resolution_x=1200; _sc.render.resolution_y=1200
    bpy.ops.object.camera_add(location=(dc.x,dc.y,5.0)); cam=bpy.context.object
    from mathutils import Euler
    cam.rotation_euler=Euler((0,0,0),'XYZ')
    cam.data.type='ORTHO'; cam.data.ortho_scale=3.2; _sc.camera=cam
    # hide ceiling so the top-down cam at z=5 is not looking at the slab
    if "Ceiling" in bpy.data.objects: bpy.data.objects["Ceiling"].hide_render=True
    _sc.render.filepath=os.path.join(SHOTS_R9,"dining_top.png"); bpy.ops.render.render(write_still=True); print("SHOT dining_top")
    cam.data.type='PERSP'; cam.data.lens=35
    cam.location=(dc.x+1.8, dc.y-1.8, 1.6)
    cam.rotation_euler=(Vector((dc.x,dc.y,0.7))-cam.location).to_track_quat('-Z','Y').to_euler()
    _sc.render.resolution_x=1400; _sc.render.resolution_y=1000
    if "Ceiling" in bpy.data.objects: bpy.data.objects["Ceiling"].hide_render=False
    _sc.render.filepath=os.path.join(SHOTS_R9,"dining_34.png"); bpy.ops.render.render(write_still=True); print("SHOT dining_34")
    bpy.data.objects.remove(cam, do_unlink=True)

cyl("Pendant_cord",(dc.x,dc.y,(CEIL+1.75)/2),0.004,CEIL-1.75,BMET); sph("Globe_pendant_white",(dc.x,dc.y,1.6),0.2,GLOBE)
bpy.ops.object.light_add(type='POINT',location=(dc.x,dc.y,1.55));bpy.context.object.name="Pendant_light";bpy.context.object.data.energy=40;bpy.context.object.data.color=(1,0.78,0.55)

# bedside lamps (point lights at the CC0 nightstand positions)
for (lx,ly) in ((b1.x-1.0,m(0,62).y-0.35),(b1.x+1.0,m(0,62).y-0.35),(b2.x-1.0,m(0,40).y-0.45),(b2.x+1.0,m(0,40).y-0.50)):
    bpy.ops.object.light_add(type='POINT',location=(lx,ly,0.85));bpy.context.object.data.energy=12;bpy.context.object.data.color=(1,0.75,0.5)

wx=m(15,0).x+T/2+0.02; box("Art_bed1_frame_side_wall",(wx,m(0,120).y,1.6),(0.03,0.6,0.8),BMET,0,0); _a=box("Art_bed1",(wx+0.016,m(0,120).y,1.6),(0.005,0.54,0.74),ART[0],0,0)
if 5 in FIX: uv_front(_a)

# bathroom wall tiles (architecture, not furniture) + towel rail / plant / light
for nm_,c,s in (("Bath_wall_tile_S",(bx0+(bx1-bx0)/2,by0+0.005+T/2,1.2),(bx1-bx0,0.01,2.4)),("Bath_wall_tile_W",(bx0+0.005+T/2,(by0+by1)/2,1.2),(0.01,by1-by0,2.4))): box(nm_,c,s,TILE,0,0)
tx=bx1-0.45; ty=by0+T/2+0.05
for sd in (-0.25,0.25): box("Towel_ladder_vertical_chrome",(tx+sd,ty,1.0),(0.03,0.03,1.2),CHROME,0,0.01)
for z in (0.5,0.65,0.8,0.95,1.1,1.25,1.4,1.55): box("Towel_ladder_bar_chrome",(tx,ty,z),(0.5,0.02,0.02),CHROME,0,0.006)
cyl("Bath_plant_pot",(bx0+T/2+0.1,wcy+0.5,1.12),0.06,0.1,WHITEP,16); sph("Bath_plant",(bx0+T/2+0.1,wcy+0.5,1.24),0.1,LEAF,1,1,0.8)
bpy.ops.object.light_add(type='AREA',location=((bx0+bx1)/2,(by0+by1)/2,CEIL-0.05));l=bpy.context.object;l.name="Bath_ceiling_panel";l.data.size=1.2;l.data.energy=70;l.data.color=(1,0.92,0.82)

# ---------- render setup
for o in sc.objects:
    if o.type=='MESH':
        for f in o.data.polygons: f.use_smooth=False
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in sc.view_settings.bl_rna.properties['look'].enum_items] else 'None'
sc.world=bpy.data.worlds.new("w");sc.world.use_nodes=True;bg=sc.world.node_tree.nodes['Background'];env=sc.world.node_tree.nodes.new("ShaderNodeTexEnvironment");env.image=bpy.data.images.load(HDRI);sc.world.node_tree.links.new(env.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=0.3
sc.render.resolution_x=1600;sc.render.resolution_y=1000
bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
def free(p,r=0.3):
    for d in [Vector(v) for v in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(.7,.7,0),(-.7,.7,0),(.7,-.7,0),(-.7,-.7,0))]:
        hit,loc,*_=sc.ray_cast(dg,p,d,distance=r)
        if hit: return False
    return True
def shot(name,loc,tgt,lens=20,ceiling=True):
    if "--noshots" in sys.argv or ("--only" in sys.argv and name not in sys.argv): return
    p=Vector(loc)
    if not free(p): 
        for dx,dy in itertools.product((-0.3,0,0.3,0.6,-0.6),(-0.3,0,0.3,0.6,-0.6)):
            q=p+Vector((dx,dy,0))
            if inside(q,OUTL) and free(q): p=q;break
        else: print("CAMERA COLLISION",name)
    bpy.data.objects["Ceiling"].hide_render=not ceiling
    bpy.ops.object.camera_add(location=p);c=bpy.context.object;c.rotation_euler=(Vector(tgt)-p).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;sc.camera=c
    sc.render.filepath=OUT+name+".png";bpy.ops.render.render(write_still=True);print("SHOT",name,tuple(round(v,2) for v in p))
def tj(v): return [round(v[0],2),round(v[2],2),round(-v[1],2)]
_hy=m(0,62).y
print("PRESET i_bed1",tj((b1.x+0.2,0.85,1.3)),tj((b1.x,_hy-0.6,0.8)))
_h2=m(0,40).y
print("PRESET i_bed2",tj((b2.x+0.1,1.6,1.3)),tj((b2.x-0.05,_h2-0.8,0.8)))
print("PRESET i_bath",tj((bx1-0.25,by0+0.4,1.55)),tj((bx0+0.45,by1-0.5,0.9)))
print("BATH",bx0,by0,bx1,by1)
E=1.5
shot("v3_living",(m(120,255).x,m(120,255).y,E),(sx,sofa_y+0.3,0.9),20)
json.dump(LAYOUT,open(ROOT+"/interior/polish_layout.json","w"),indent=1) if FIX>={2,3} else None
if not FIX:   # original r9 framing (bedroom cams sit against a wall -> blank stills)
    shot("v3_kitchen",(m(110,230).x,m(110,230).y,E),(kx,(ky0+ky1)/2,1.1),20)
    shot("v3_bedroom1",(b1.x+0.2,0.85,1.3),(b1.x,_hy-0.6,0.8),24)
    shot("v3_bedroom2",(b2.x+0.1,1.6,1.3),(b2.x-0.05,_h2-0.8,0.8),24)
    shot("v3_bathroom",(bx1-0.25,by0+0.4,1.55),(bx0+0.45,by1-0.5,0.9),14)
else:         # lane/polish: stills framed like the Rightmove CGI (bed square-on from the foot, kitchen run face-on, bathroom from the door)
    def _bedcam(n_,back):
        hd=Vector((-math.sin(n_[2]),math.cos(n_[2]),0)); c=Vector((n_[0],n_[1],0))
        return (tuple(c-hd*back)[:2]+(1.35,)),(tuple(c+hd*1.0)[:2]+(0.75,))
    _yc3=ky0+0.3+3*0.6
    shot("v3_kitchen",(kx-0.34-1.6,_yc3,1.6),(kx,_yc3,1.82),20)
    shot("v3_bedroom1",*_bedcam(_n1,1.65),17)
    shot("v3_bedroom2",*_bedcam(_n2,2.1),18)
    shot("v3_bathroom",(m(84,0).x-0.2,m(0,315).y,1.5),(bx0+0.3,m(0,302).y,0.85),15)
shot("latest",(0.6,-11,12),(0.2,0.3,0),26,ceiling=False)
# lane/polish: locked cameras = web viewer presets (web/src/app.js P.i_*), three.js (x,y,z) -> Blender (x,-z,y), vertical fov; no collision nudge
WEBCAMS={"w_living":([-0.5,1.5,1.91],[2.97,0.9,0.15],70),"w_bed1":([-2.0,1.3,-0.85],[-2.41,0.8,-3.17],70),"w_bed2":([1.5,1.3,-1.6],[1.36,0.8,-3.62],70),
         "w_bath":([-2.08,1.55,3.83],[-3.02,0.9,2.88],80),"w_store":([-1.09,1.5,1.32],[-3.0,1.0,1.32],80)}
def wshot(name):
    if not ("--wshots" in sys.argv and ("--only" not in sys.argv or name in sys.argv)): return
    p3,t3,fov=WEBCAMS[name]; p=Vector((p3[0],-p3[2],p3[1])); t=Vector((t3[0],-t3[2],t3[1]))
    bpy.data.objects["Ceiling"].hide_render=False; rx,ry=sc.render.resolution_x,sc.render.resolution_y; sc.render.resolution_x,sc.render.resolution_y=1280,800
    bpy.ops.object.camera_add(location=p);c=bpy.context.object;c.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();c.data.sensor_fit='VERTICAL';c.data.angle_y=math.radians(fov);sc.camera=c
    sc.render.filepath=OUT+name+".png";bpy.ops.render.render(write_still=True);print("WSHOT",name);sc.render.resolution_x,sc.render.resolution_y=rx,ry
for _k in WEBCAMS: wshot(_k)
bpy.data.objects["Ceiling"].hide_render=False
if "--nobake" in sys.argv: sys.exit(0)
# ===== BAKE lighting into one atlas so the web viewer matches Cycles =====
import numpy as np
KEEP_LIVE=lambda o: any(k in o.name for k in ("_glass","Shower_glass","Mirror_glass","_backdrop")) or (5 in FIX and o.name in ("Art_living","Art_bed1"))  # fix5: art keeps its own texture (atlas texels too coarse)
bpy.ops.object.select_all(action='DESELECT')
meshes=[o for o in sc.objects if o.type=='MESH' and not KEEP_LIVE(o)]
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.convert(target='MESH')            # applies bevel/solidify modifiers
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in bpy.context.selected_objects:
    if "UVMap" not in o.data.uv_layers: o.data.uv_layers.new(name="UVMap")
bpy.ops.object.join(); J=bpy.context.object; J.name="BAKED_interior"
J.data.uv_layers["UVMap"].active_render=True
bu=J.data.uv_layers.new(name="bake"); J.data.uv_layers.active=bu
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.004,area_weight=1.0,scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
RES=int(next((a.split('=')[1] for a in sys.argv if a.startswith('--res=')),4096))
img=bpy.data.images.new("bake",RES,RES,float_buffer=True)
for M in J.data.materials:
    n=M.node_tree.nodes.new("ShaderNodeTexImage");n.image=img;M.node_tree.nodes.active=n
sc.cycles.samples=int(next((a.split('=')[1] for a in sys.argv if a.startswith('--bs=')),96))
sc.render.bake.use_pass_direct=True;sc.render.bake.use_pass_indirect=True
sc.render.bake.use_pass_diffuse=True;sc.render.bake.use_pass_glossy=False;sc.render.bake.use_pass_transmission=True;sc.render.bake.use_pass_emit=True
sc.render.bake.margin=16; sc.cycles.use_denoising=False
bpy.ops.object.select_all(action='DESELECT');J.select_set(True);bpy.context.view_layer.objects.active=J
bpy.ops.object.bake(type='COMBINED');print("BAKED")
px=np.array(img.pixels[:]).reshape(RES,RES,4); rgb=px[...,:3]
EXPO=float(next((a.split('=')[1] for a in sys.argv if a.startswith('--expo=')),1.6))
from scipy.ndimage import gaussian_filter
cov=(px[...,3]>0.5).astype(float)
def _bake_to(name,typ,**kw):
    im=bpy.data.images.new(name,RES,RES,float_buffer=True)
    for M in J.data.materials: M.node_tree.nodes.active.image=im
    for k,v in kw.items(): setattr(sc.render.bake,k,v)
    bpy.ops.object.bake(type=typ); print("BAKED",name); return im
if 6 in FIX:   # fix6: OIDN denoise (albedo-guided, edge preserving) instead of blur -> no blotchy wall/ceiling seams; + baked AO (contact shadows)
    alb=_bake_to("bake_albedo","DIFFUSE",use_pass_direct=False,use_pass_indirect=False,use_pass_color=True)
    sc.world.light_settings.distance=0.6; sc.cycles.samples=64
    aoi=_bake_to("bake_ao","AO")
    dn=bpy.data.scenes.new("denoise"); dn.render.engine='BLENDER_WORKBENCH'; dn.render.resolution_x=dn.render.resolution_y=RES; dn.render.resolution_percentage=100
    cam_=bpy.data.objects.new("dncam",bpy.data.cameras.new("dncam")); dn.collection.objects.link(cam_); dn.camera=cam_
    ng=bpy.data.node_groups.new("DN","CompositorNodeTree"); dn.compositing_node_group=ng; dn.render.use_compositing=True
    ni=ng.nodes.new("CompositorNodeImage"); ni.image=img; na=ng.nodes.new("CompositorNodeImage"); na.image=alb; dd=ng.nodes.new("CompositorNodeDenoise")
    ng.interface.new_socket("Image",in_out='OUTPUT',socket_type='NodeSocketColor'); go=ng.nodes.new("NodeGroupOutput")
    ng.links.new(ni.outputs[0],dd.inputs["Image"]); ng.links.new(na.outputs[0],dd.inputs["Albedo"]); ng.links.new(dd.outputs[0],go.inputs[0])
    dn.render.image_settings.file_format='OPEN_EXR'; dn.render.filepath=OUT+"_bake_dn.exr"; bpy.ops.render.render(write_still=True,scene=dn.name)
    r_=bpy.data.images.load(OUT+"_bake_dn.exr"); d_=np.array(r_.pixels[:]).reshape(RES,RES,4)[...,:3]
    ao=np.array(aoi.pixels[:]).reshape(RES,RES,4)[...,0]; ao=gaussian_filter(ao*cov,1.0)/(gaussian_filter(cov,1.0)+1e-6)
    rgb[...]=np.where(cov[...,None]>0,d_,rgb)*(1-0.45*(1-np.clip(ao,0,1)))[...,None]
    os.remove(OUT+"_bake_dn.exr"); print("DENOISED+AO", float(ao[cov>0].mean()))
else:
  for ch in range(3):
    num=gaussian_filter(rgb[...,ch]*cov,1.6); den=gaussian_filter(cov,1.6)+1e-6
    rgb[...,ch]=np.where(cov>0,num/den,rgb[...,ch])
rgb=1-np.exp(-rgb*EXPO)                          # simple filmic shoulder; viewer shows it untonemapped
px[...,:3]=rgb; px[...,3]=1
out=bpy.data.images.new("bake_ldr",RES,RES); out.pixels=px.ravel().tolist() if RES<=2048 else px.ravel()
out.filepath_raw=OUT+"bake_atlas.png"; out.file_format='PNG'; out.save()
# single unlit-style material: base colour = baked atlas on 'bake' UV
for uvl in list(J.data.uv_layers):
    if uvl.name!="bake": J.data.uv_layers.remove(uvl)
CEIL_FACES=[f.index for f in J.data.polygons if J.data.materials[f.material_index].name=='Ceiling_warm_white']; print('ceil faces',len(CEIL_FACES))
J.data.materials.clear()
BM=bpy.data.materials.new("BAKED_lightmap");BM.use_nodes=True;N=BM.node_tree.nodes;b=N["Principled BSDF"];t=N.new("ShaderNodeTexImage");t.image=out
BM.node_tree.links.new(t.outputs[0],b.inputs["Base Color"]);b.inputs["Roughness"].default_value=1;J.data.materials.append(BM)
for f in J.data.polygons: f.material_index=0
import bmesh as _bm
bm=_bm.new(); bm.from_mesh(J.data); bm.faces.ensure_lookup_table()
for f in bm.faces: f.select=False
for i in CEIL_FACES: bm.faces[i].select=True
bm.to_mesh(J.data); bm.free()
bpy.ops.object.select_all(action='DESELECT');J.select_set(True);bpy.context.view_layer.objects.active=J
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
for o in sc.objects:
    if o.name.startswith("BAKED_interior") and o is not J: o.name="Ceiling_BAKED"; print("CEILING SPLIT",len(o.data.polygons))
bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=OUT+"twobed_raw.glb",export_format='GLB',use_selection=True,export_apply=True,export_lights=False,export_image_format='JPEG',export_jpeg_quality=92)
print("EXPORTED","K",K,"area",parea(P)*K*K)
