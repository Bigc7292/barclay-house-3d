# Barclay House Two Bed v2 (critic round 1 fixes). Outline + rooms SCALED FROM RIGHTMOVE PLAN IMAGE (apt02_fp.png), APPROXIMATE,
# total floor area fixed to sourced 63 m2. Finishes/furniture follow Rightmove CGI marketing images (scheme spec), illustrative.
# Unsourced: clear ceiling height (3.0 m used; floor-to-floor 3.663 m sourced), window positions, all furniture dimensions.
import bpy, bmesh, math, mathutils, sys
from mathutils import Vector
TX="/workspace/barclay/interior/tex/"; OUT="/workspace/barclay/interior/live/"
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
TILE=mat("Tile_grey_600x1200",(1,1,1),0.3,img="tile_600x1200_diff.jpg")
WALL=mat("Wall_warm_white",(0.86,0.83,0.78),0.85); CEILM=mat("Ceiling_warm_white",(0.9,0.88,0.84),0.9)
SKIRT=mat("Skirting_white_satin",(0.92,0.91,0.88),0.35)
WUNIT=mat("Kitchen_handleless_white",(0.9,0.89,0.86),0.3); DARK=mat("Peninsula_graphite",(0.042,0.042,0.045),0.5); QUARTZ=mat("Quartz_white",(0.88,0.88,0.87),0.25)
WTOP=mat("Worktop_white",(0.93,0.93,0.92),0.2); BLK=mat("Appliance_black_gloss",(0.015,0.015,0.017),0.12)
STEEL=mat("Stainless_steel",(0.8,0.8,0.8),0.22,1); CHROME=mat("Chrome",(0.9,0.9,0.9),0.05,1)
LED=mat("LED_strip_3000K",(1,0.85,0.65),0.5,emit=(1,0.78,0.55),ew=40)
NAVY=mat("Navy_velvet",(1,1,1),0.75,img="velvet_navy_diff.jpg"); BOUC=mat("Cream_boucle",(1,1,1),0.95,img="boucle_diff.jpg")
OAKF=mat("Oak_furniture",(0.62,0.42,0.24),0.5,img="oak_light_diff.jpg"); BMET=mat("Black_metal",(0.02,0.02,0.02),0.35,0.8)
LIN=mat("Bedding_white",(0.93,0.93,0.91),0.9); RUG=mat("Rug_cream",(0.86,0.82,0.74),1.0)
WHITEP=mat("Sanitary_white",(0.95,0.95,0.95),0.08); GREYV=mat("Vanity_grey",(0.45,0.45,0.46),0.4)
GLASS=mat("Glass_clear",(0.95,0.97,0.97),0.02,trans=1); WGLASS=mat("Window_glass_clear",(0.95,0.97,1),0.02,trans=1); SKY=mat("Window_backdrop_sky_UNSOURCED_VIEW",(1,1,1),1,img="sky_backdrop.jpg"); SKY.node_tree.links.new(SKY.node_tree.nodes["Image Texture"].outputs[0],SKY.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]); SKY.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value=3
FRAME=mat("Window_frame_black_steel",(0.015,0.015,0.015),0.4,0.6); DOOR=mat("Door_white",(0.9,0.9,0.88),0.4)
GLOBE=mat("Globe_pendant_opal",(1,0.97,0.92),0.3,emit=(1,0.8,0.6),ew=4); LAMPS=mat("Lamp_shade_opal",(1,0.97,0.92),0.3,emit=(1,0.8,0.6),ew=3)
LEAF=mat("Plant_leaf",(0.08,0.25,0.07),0.6); POT=mat("Pot_terracotta",(0.55,0.32,0.2),0.8); TVS=mat("TV_screen",(0.01,0.01,0.012),0.08)
DLM=mat("Downlight_3000K",(1,0.9,0.75),0.3,emit=(1,0.78,0.55),ew=15)
ART=[mat(f"Art_{i}_illustrative",(1,1,1),0.6,img=f"art{i}.jpg") for i in (1,2,3)]
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
    c=c+nrm*(T/2+0.012); hr=w/2; hs=head-hr
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
    lp=c-nrm*(T+0.25); bpy.ops.object.light_add(type='AREA',location=(lp.x,lp.y,(sill+head)/2)); L_=bpy.context.object; L_.name=n+"_daylight"
    L_.data.shape='RECTANGLE'; L_.data.size=w; L_.data.size_y=head-sill; L_.data.energy=260; L_.data.color=(0.95,0.97,1)
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
# ---------- KITCHEN (right wall run, x≈262, y 240..345 px)
kx=m(262,0).x-T/2; ky0=m(0,343).y; ky1=m(0,238).y; L=ky1-ky0; n=int(L/0.6); y=ky0
for i in range(n):
    yc=ky0+0.3+i*0.6
    if i==1: box("Washing_machine_black",(kx-0.3,yc,0.43),(0.58,0.597,0.82),BLK); r_=cyl("WM_door_chrome_ring",(kx-0.595,yc,0.42),0.19,0.03,CHROME,40);r_.rotation_euler=(0,math.pi/2,0); g_=cyl("WM_door_glass_dark",(kx-0.605,yc,0.42),0.155,0.03,TVS,40);g_.rotation_euler=(0,math.pi/2,0); box("WM_control_panel",(kx-0.595,yc,0.79),(0.01,0.55,0.08),FRAME,0,0)
    else: box(f"Base_unit_{i}",(kx-0.3,yc,0.45),(0.58,0.597,0.78),WUNIT,0,0.002)
    box(f"Wall_unit_{i}",(kx-0.17,yc,1.95),(0.33,0.597,0.72),WUNIT,0,0.002)
box("Plinth",(kx-0.29,(ky0+ky1)/2,0.04),(0.55,L,0.08),DARK,0,0)
box("Worktop",(kx-0.31,ky0+n*0.3,0.88),(0.62,n*0.6,0.04),WTOP,0,0.002)
box("LED_strip_under_wall_units",(kx-0.3,ky0+n*0.3,1.585),(0.02,n*0.6,0.01),LED,0,0)
box("Microwave_frame_black",(kx-0.336,ky0+0.3+3*0.6,1.95),(0.012,0.58,0.4),BLK,0,0.003); box("Microwave_glass_face",(kx-0.344,ky0+0.3+3*0.6-0.06,1.95),(0.004,0.4,0.3),TVS,0,0); box("Microwave_controls",(kx-0.344,ky0+0.3+3*0.6+0.21,1.95),(0.004,0.1,0.3),FRAME,0,0)
sk=ky0+0.3+2*0.6; box("Sink_steel",(kx-0.33,sk,0.895),(0.42,0.5,0.012),STEEL,0,0.002)
cyl("Tap_body",(kx-0.08,sk,1.08),0.018,0.38,CHROME,20)
for k in range(10):
    a=math.pi*k/9; q=Vector((kx-0.08-0.11*(1-math.cos(a)),sk,1.27+0.11*math.sin(a))); sph("Tap_gooseneck_arc",q,0.016,CHROME)
cyl("Tap_outlet",(kx-0.30,sk,1.23),0.016,0.08,CHROME,16)
box("Induction_hob_black",(kx-0.33,ky0+0.3,0.902),(0.52,0.56,0.006),BLK,0,0.002)
if n*0.6<L-0.62: box("Tall_unit",(kx-0.3,ky0+n*0.6+0.3,CEIL/2-0.15),(0.58,0.597,CEIL-0.4),WUNIT,0,0.002)
# dark peninsula with built-in black oven (Apt 02/03 photos)
pz=m(0,250).y; px0=kx-0.6; box("Peninsula_dark",(px0-0.9,pz,0.45),(1.8,0.6,0.9),DARK,0,0.003)
box("Peninsula_top_white_quartz",(px0-0.9,pz,0.915),(1.84,0.64,0.03),QUARTZ,0,0.002); box("Oven_black_built_in",(px0-0.4,pz-0.301,0.45),(0.58,0.01,0.58),BLK,0,0)
# ---------- LIVING / DINING
lc=m(205,195); sofa_y=lc.y; sx=m(255,0).x-0.5
def sofa(c,ang):
    g=[box("Sofa_base",(0.02,0,0.25),(0.92,2.0,0.2),NAVY,0,0.04),box("Sofa_back",(0.38,0,0.58),(0.18,2.0,0.5),NAVY,0,0.07)]
    for sd in (-1,1):
        a=cyl("Sofa_bolster_arm",(0.0,sd*1.06,0.42),0.13,0.92,NAVY,32);a.rotation_euler=(0,math.pi/2,0);g.append(a)
        g.append(box("Sofa_arm_panel",(0.0,sd*1.06,0.27),(0.92,0.24,0.3),NAVY,0,0.05))
    for j in (-0.62,0,0.62):
        g.append(box("Sofa_seat_cushion_deep",(-0.06,j,0.44),(0.72,0.61,0.18),NAVY,0,0.07))
        g.append(box("Sofa_back_cushion",(0.24,j,0.72),(0.2,0.6,0.46),NAVY,0,0.09))
    for j in (-0.75,0.75): g.append(box("Sofa_scatter_cushion_cream",(0.15,j,0.7),(0.12,0.42,0.42),BOUC,0,0.06))
    for a,b in ((-0.38,-0.95),(0.38,-0.95),(-0.38,0.95),(0.38,0.95)): g.append(cyl("Sofa_leg_tapered_black",(a,b,0.075),0.018,0.15,BMET,16,0.012))
    e=bpy.data.objects.new("Sofa_navy_velvet_3seat",None);sc.collection.objects.link(e)
    for o in g: o.parent=e
    e.location=c;e.rotation_euler[2]=ang
sofa((sx,sofa_y,0),0)
box("Rug_cream",(sx-1.35,sofa_y,0.006),(1.7,2.3,0.012),RUG,0,0.003)
ct=Vector((sx-1.35,sofa_y,0)); box("Coffee_table_oak_top",(ct.x,ct.y,0.42),(0.55,1.05,0.035),OAKF,0,0.006)
for a,b in ((-0.27,-0.5),(0.27,-0.5),(-0.27,0.5),(0.27,0.5)): box("Coffee_table_black_metal_leg",(ct.x+a*0.95,ct.y+b*0.97,0.2),(0.02,0.02,0.4),BMET,0,0)
box("Coffee_table_shelf_oak",(ct.x,ct.y,0.13),(0.5,1.0,0.02),OAKF,0,0.004); box("Coffee_book",(ct.x+0.1,ct.y-0.25,0.455),(0.22,0.3,0.03),RUG,0,0.003)
tvx=m(150,0).x+0.25; box("TV_bench_oak",(tvx,sofa_y,0.36),(0.4,1.5,0.32),OAKF,0,0.006)
for a,b in ((-0.16,-0.7),(0.16,-0.7),(-0.16,0.7),(0.16,0.7)): cyl("TV_bench_leg_black",(tvx+a,sofa_y+b,0.1),0.015,0.2,BMET,12)
box("TV_bench_door_gap",(tvx+0.201,sofa_y,0.36),(0.002,0.004,0.3),BMET,0,0)
box("TV_stand_black",(tvx,sofa_y,0.55),(0.18,0.3,0.02),BMET,0,0); box("TV_stand_post",(tvx-0.02,sofa_y,0.62),(0.03,0.06,0.14),BMET,0,0)
box("TV_bezel_black_facing_sofa",(tvx-0.02,sofa_y,0.98),(0.04,1.12,0.66),BLK,0,0.004); box("TV_screen",(tvx+0.001,sofa_y,0.99),(0.002,1.08,0.61),TVS,0,0)
box("Art_living_frame",(sx+0.44,sofa_y,1.6),(0.03,0.8,1.05),BMET,0,0); box("Art_living",(sx+0.42,sofa_y,1.6),(0.01,0.72,0.97),ART[1],0,0)
pp=Vector((sx,sofa_y+1.4,0)); cyl("Plant_pot",(pp.x,pp.y,0.2),0.18,0.4,POT,24,0.14)
for j in range(9): a=j*0.7; sph("Plant_leaf",(pp.x+0.25*math.cos(a)*(j%3)/2,pp.y+0.25*math.sin(a)*(j%3)/2,0.75+0.12*(j%4)),0.18,LEAF,1.2,0.5,0.25)
dc=Vector((m(190,0).x,m(0,305).y,0))
cyl("Dining_table_oak_top",(dc.x,dc.y,0.74),0.45,0.035,OAKF,48); cyl("Dining_table_pedestal_black",(dc.x,dc.y,0.37),0.04,0.72,BMET); cyl("Dining_table_foot",(dc.x,dc.y,0.015),0.25,0.03,BMET)
def tub(c,ang):
    e=bpy.data.objects.new("Tub_chair_cream_boucle",None);sc.collection.objects.link(e)
    s=cyl("Tub_seat",(0,0,0.45),0.26,0.1,BOUC,32);s.parent=e
    b=bpy.data.objects.new("x",None)
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=False,segments=32,radius1=0.27,radius2=0.29,depth=0.35)
    for v in list(bm.verts):
        if math.atan2(v.co.y,v.co.x)<-0.2*math.pi and math.atan2(v.co.y,v.co.x)>-0.8*math.pi: bm.verts.remove(v)
    bk=obj_from(bm,"Tub_back",BOUC);bk.location=(0,0,0.67);bk.parent=e;md=bk.modifiers.new("s","SOLIDIFY");md.thickness=0.06
    for a in range(4): q=a*math.pi/2+math.pi/4; cyl("Tub_leg_black",(0.2*math.cos(q),0.2*math.sin(q),0.2),0.012,0.4,BMET).parent=e
    e.location=c;e.rotation_euler[2]=ang
for j,a in enumerate((0,math.pi/2,math.pi,3*math.pi/2)): tub((dc.x+0.72*math.cos(a),dc.y+0.72*math.sin(a),0),a+math.pi/2)
cyl("Pendant_cord",(dc.x,dc.y,(CEIL+1.75)/2),0.004,CEIL-1.75,BMET); sph("Globe_pendant_white",(dc.x,dc.y,1.6),0.2,GLOBE)
bpy.ops.object.light_add(type='POINT',location=(dc.x,dc.y,1.55));bpy.context.object.name="Pendant_light";bpy.context.object.data.energy=40;bpy.context.object.data.color=(1,0.78,0.55)
# ---------- BEDROOMS
def bed(n,c,ang):
    e=bpy.data.objects.new(n,None);sc.collection.objects.link(e);W,Lb=1.45,2.05
    for o in (box("Bed_base_navy_velvet",(0,0,0.2),(W,Lb,0.32),NAVY,0,0.03),box("Mattress_white",(0,-0.03,0.47),(W-0.08,Lb-0.1,0.22),LIN,0,0.05),
              box("Duvet_white",(0,-0.2,0.6),(W-0.02,1.45,0.08),LIN,0,0.04),box("Throw_navy_folded",(0,-0.72,0.655),(W+0.06,0.5,0.03),NAVY,0,0.012),box("Throw_drape_L",(-W/2-0.04,-0.72,0.5),(0.025,0.5,0.3),NAVY,0,0.01),box("Throw_drape_R",(W/2+0.04,-0.72,0.5),(0.025,0.5,0.3),NAVY,0,0.01),
              box("Pillow",(-0.34,0.82,0.66),(0.62,0.32,0.15),LIN,0,0.07),box("Pillow",(0.34,0.82,0.66),(0.62,0.32,0.15),LIN,0,0.07),box("Pillow_front",(-0.34,0.72,0.74),(0.6,0.14,0.36),LIN,0,0.07),box("Pillow_front",(0.34,0.72,0.74),(0.6,0.14,0.36),LIN,0,0.07),box("Scatter_cushion_navy",(-0.22,0.6,0.74),(0.36,0.12,0.34),NAVY,0,0.06),box("Scatter_cushion_navy",(0.22,0.6,0.74),(0.36,0.12,0.34),NAVY,0,0.06),
              box("Cushion_navy",(0,0.62,0.7),(0.4,0.14,0.32),NAVY,0,0.06)): o.parent=e
    for k in range(9):
        sp=(W+0.1)/9; x=-W/2-0.05+sp/2+k*sp
        o=cyl("Headboard_channel_flute_navy",(x,Lb/2+0.06,0.6),sp/2+0.004,1.1,NAVY,20);o.scale=(1,0.7,1);o.parent=e
        t=sph("Headboard_flute_top",(x,Lb/2+0.06,1.15),sp/2+0.004,NAVY,1,0.7,0.6);t.parent=e
    box("Headboard_backing",(0,Lb/2+0.1,0.6),(W+0.1,0.04,1.15),NAVY,0,0.01).parent=e
    e.location=c;e.rotation_euler[2]=ang
def bedside(c,ang):
    e=bpy.data.objects.new("Bedside_table_oak",None);sc.collection.objects.link(e)
    for o in (box("Bedside_oak_body",(0,0,0.42),(0.45,0.4,0.32),OAKF),box("Bedside_drawer_line",(0,-0.201,0.42),(0.4,0.004,0.004),BMET,0,0)): o.parent=e
    for a,b in ((-0.2,-0.17),(0.2,-0.17),(-0.2,0.17),(0.2,0.17)): cyl("Bedside_leg_black",(a,b,0.13),0.012,0.26,BMET).parent=e
    cyl("Lamp_stem_black",(0,0,0.68),0.012,0.2,BMET).parent=e; s=sph("Lamp_mushroom_opal",(0,0,0.8),0.14,LAMPS,1,1,0.6);s.parent=e
    e.location=c;e.rotation_euler[2]=ang
    bpy.ops.object.light_add(type='POINT',location=(c[0],c[1],0.85));bpy.context.object.data.energy=12;bpy.context.object.data.color=(1,0.75,0.5)
def wardrobe(c,ang):
    e=bpy.data.objects.new("Wardrobe_oak_2door",None);sc.collection.objects.link(e)
    for o in (box("Wardrobe_left_door",(-0.251,0,1.05),(0.5,0.58,2.1),OAKF,0,0.002),box("Wardrobe_right_door",(0.251,0,1.05),(0.5,0.58,2.1),OAKF,0,0.002),box("Wardrobe_plinth",(0,0,0.03),(1.0,0.55,0.06),BMET,0,0)): o.parent=e
    e.location=c;e.rotation_euler[2]=ang
# bedroom 1 (top-left): bed head against north wall
b1=m(55,105); bed("Bed1_navy",(b1.x,m(0,62).y-1.15,0),math.pi*0); 
bedside((b1.x-1.0,m(0,62).y-0.35,0),0); bedside((b1.x+1.0,m(0,62).y-0.35,0),0)
wardrobe((m(28,0).x+0.3,m(0,150).y,0),-math.pi/2)
wx=m(15,0).x+T/2+0.02; box("Art_bed1_frame_side_wall",(wx,m(0,120).y,1.6),(0.03,0.6,0.8),BMET,0,0); box("Art_bed1",(wx+0.016,m(0,120).y,1.6),(0.005,0.54,0.74),ART[0],0,0)
b2=m(185,70); bed("Bed2_navy",(b2.x,m(0,40).y-1.3,0),0.06)
bedside((b2.x-1.0,m(0,40).y-0.45,0),0.06); bedside((b2.x+1.0,m(0,40).y-0.5,0),0.06)
wardrobe((m(140,0).x,m(0,135).y,0),math.pi-0.12)
# ---------- BATHROOM
bx0,by0=m(19,344).x,m(19,344).y; bx1,by1=m(85,271).x,m(85,271).y
box("Shower_tray",(bx0+0.5,by0+0.5,0.025),(0.9,0.9,0.05),WHITEP)
box("Shower_glass_wall",(bx0+0.95,by0+0.5,1.05),(0.008,0.9,2.0),GLASS,0,0); cyl("Shower_head",(bx0+0.3,by0+0.3,2.05),0.1,0.01,CHROME)
for nm_,c,s in (("Bath_wall_tile_S",(bx0+(bx1-bx0)/2,by0+0.005+T/2,1.2),(bx1-bx0,0.01,2.4)),("Bath_wall_tile_W",(bx0+0.005+T/2,(by0+by1)/2,1.2),(0.01,by1-by0,2.4))): box(nm_,c,s,TILE,0,0)
bw=0.2; box("WC_boxing_half_wall",(bx0+T/2+bw/2,(by0+0.95+by1)/2,0.525),(bw,by1-by0-0.95,1.05),TILE,0,0.004)
box("WC_boxing_top_shelf",(bx0+T/2+bw/2+0.01,(by0+0.95+by1)/2,1.06),(bw+0.03,by1-by0-0.95,0.02),QUARTZ,0,0.002)
wcy=by1-0.65; box("WC_flush_plate_chrome",(bx0+T/2+bw+0.004,wcy,0.85),(0.008,0.22,0.15),CHROME,0,0.002)
box("WC_pan_back_to_wall",(bx0+T/2+bw+0.27,wcy,0.2),(0.52,0.37,0.4),WHITEP,0,0.07); box("WC_seat",(bx0+T/2+bw+0.29,wcy,0.415),(0.48,0.36,0.03),WHITEP,0,0.012)
vx=bx1-0.45; box("Vanity_grey_stone_look",(vx,by1-T/2-0.24,0.62),(0.6,0.46,0.3),GREYV,0,0.006); box("Basin_white_wallhung",(vx,by1-T/2-0.24,0.82),(0.56,0.42,0.12),WHITEP,0,0.04)
cyl("Basin_tap",(vx,by1-T/2-0.06,0.95),0.012,0.14,CHROME,12)
box("Mirror_black_frame",(vx,by1-T/2-0.012,1.55),(0.55,0.02,0.75),FRAME,0,0.002); box("Mirror_glass",(vx,by1-T/2-0.024,1.55),(0.5,0.006,0.7),CHROME,0,0)
tx=bx1-0.45; ty=by0+T/2+0.05
for sd in (-0.25,0.25): box("Towel_ladder_vertical_chrome",(tx+sd,ty,1.0),(0.03,0.03,1.2),CHROME,0,0.01)
for z in (0.5,0.65,0.8,0.95,1.1,1.25,1.4,1.55): box("Towel_ladder_bar_chrome",(tx,ty,z),(0.5,0.02,0.02),CHROME,0,0.006)
cyl("Bath_plant_pot",(bx0+T/2+0.1,wcy+0.5,1.12),0.06,0.1,WHITEP,16); sph("Bath_plant",(bx0+T/2+0.1,wcy+0.5,1.24),0.1,LEAF,1,1,0.8)
# storage shelving
s0=m(20,268);s1=m(88,202); box("Storage_shelving_white",(s0.x+0.25,(s0.y+s1.y)/2,1.1),(0.4,abs(s1.y-s0.y)-0.2,2.2),WUNIT,0,0.003)
# ---------- render setup
for o in sc.objects:
    if o.type=='MESH':
        for f in o.data.polygons: f.use_smooth=False
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in sc.view_settings.bl_rna.properties['look'].enum_items] else 'None'
sc.world=bpy.data.worlds.new("w");sc.world.use_nodes=True;bg=sc.world.node_tree.nodes['Background'];env=sc.world.node_tree.nodes.new("ShaderNodeTexEnvironment");env.image=bpy.data.images.load("/workspace/barclay/hdri.exr");sc.world.node_tree.links.new(env.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=0.3
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
E=1.5
shot("v3_living",(m(120,255).x,m(120,255).y,E),(sx,sofa_y+0.3,0.9),20)
shot("v3_kitchen",(m(110,230).x,m(110,230).y,E),(kx,(ky0+ky1)/2,1.1),20)
shot("v3_bedroom1",(m(85,160).x,m(85,160).y,E),(b1.x,m(0,62).y,0.9),18)
shot("v3_bedroom2",(m(215,128).x,m(215,128).y,E),(b2.x,m(0,40).y,0.9),18)
shot("v3_bathroom",(bx1-0.2,-3.95,1.45),(bx0+0.3,-2.9,0.85),15)
shot("latest",(0.6,-11,12),(0.2,0.3,0),26,ceiling=False)
bpy.data.objects["Ceiling"].hide_render=False
if "--nobake" in sys.argv: sys.exit(0)
# ===== BAKE lighting into one atlas so the web viewer matches Cycles =====
import numpy as np
KEEP_LIVE=lambda o: any(k in o.name for k in ("_glass","Shower_glass","Mirror_glass","_backdrop"))
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
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.0015,area_weight=1.0,scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
RES=int(next((a.split('=')[1] for a in sys.argv if a.startswith('--res=')),4096))
img=bpy.data.images.new("bake",RES,RES,float_buffer=True)
for M in J.data.materials:
    n=M.node_tree.nodes.new("ShaderNodeTexImage");n.image=img;M.node_tree.nodes.active=n
sc.cycles.samples=int(next((a.split('=')[1] for a in sys.argv if a.startswith('--bs=')),96))
sc.render.bake.use_pass_direct=True;sc.render.bake.use_pass_indirect=True
sc.render.bake.use_pass_diffuse=True;sc.render.bake.use_pass_glossy=False;sc.render.bake.use_pass_transmission=True;sc.render.bake.use_pass_emit=True
sc.render.bake.margin=6
bpy.ops.object.select_all(action='DESELECT');J.select_set(True);bpy.context.view_layer.objects.active=J
bpy.ops.object.bake(type='COMBINED');print("BAKED")
px=np.array(img.pixels[:]).reshape(RES,RES,4); rgb=px[...,:3]
EXPO=float(next((a.split('=')[1] for a in sys.argv if a.startswith('--expo=')),1.6))
rgb=1-np.exp(-rgb*EXPO)                          # simple filmic shoulder; viewer shows it untonemapped
px[...,:3]=rgb; px[...,3]=1
out=bpy.data.images.new("bake_ldr",RES,RES); out.pixels=px.ravel().tolist() if RES<=2048 else px.ravel()
out.filepath_raw=OUT+"bake_atlas.png"; out.file_format='PNG'; out.save()
# single unlit-style material: base colour = baked atlas on 'bake' UV
for uvl in list(J.data.uv_layers):
    if uvl.name!="bake": J.data.uv_layers.remove(uvl)
J.data.materials.clear()
BM=bpy.data.materials.new("BAKED_lightmap");BM.use_nodes=True;N=BM.node_tree.nodes;b=N["Principled BSDF"];t=N.new("ShaderNodeTexImage");t.image=out
BM.node_tree.links.new(t.outputs[0],b.inputs["Base Color"]);b.inputs["Roughness"].default_value=1;J.data.materials.append(BM)
for f in J.data.polygons: f.material_index=0
bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects: o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=OUT+"twobed_raw.glb",export_format='GLB',use_selection=True,export_apply=True,export_lights=False,export_image_format='JPEG',export_jpeg_quality=92)
print("EXPORTED","K",K,"area",parea(P)*K*K)
