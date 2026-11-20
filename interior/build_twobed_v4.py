# Barclay House Two Bed walk-mode model (v4 builder, lane/walls 2026-11-20 retrace).
# GEOMETRY: walls, doors, windows, rooms, joinery and furniture positions come ONLY from
#   interior/trace/twobed_trace.json (measured on the Rightmove 92163630 plan apt02_fp.png)
#   via interior/trace/twobed_layout.py. Scale = sqrt(63 m2 / internal floor px2): total area
#   63 m2 BY CONSTRUCTION (plan prints no dimensions).
# STAND-INS (NOT FOUND in any source): clear ceiling 3.0 m (floor-to-floor 3.663 m sourced),
#   partition thickness 0.10 m, door/opening head 2.1 m, window sill 0.5 / head 2.75 m and frame
#   pattern, joinery/furniture heights, all finishes (Rightmove CGI marketing look, illustrative).
import bpy, bmesh, math, mathutils, sys, os
from mathutils import Vector
_HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(_HERE)
sys.path.insert(0,os.path.join(_HERE,"trace")); import twobed_layout as LY
TX=os.path.join(_HERE,"tex")+"/"; OUT=os.path.join(_HERE,"live")+"/"
K=LY.K; CX,CY=LY.CX,LY.CY; CEIL=LY.CEIL; T=LY.T_PART
P=[tuple(p) for p in LY.TRACE["outline"]]
def parea(P): return abs(sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P))))/2
def m(x,y): return Vector(((x-CX)*K,-(y-CY)*K,0))
def V(t): return Vector((t[0],t[1],0))
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
TILE=mat("Tile_grey_600x1200",(1,1,1),0.3,img="tile_light_r4.jpg")
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
GLASS=mat("Glass_clear",(0.95,0.97,0.97),0.02,trans=1); WGLASS=mat("Window_glass_clear",(0.95,0.97,1),0.02,trans=1); SKY=mat("Window_backdrop_sky_UNSOURCED_VIEW",(1,1,1),1,img="sky_backdrop_r4.jpg"); SKY.node_tree.links.new(SKY.node_tree.nodes["Image Texture"].outputs[0],SKY.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]); SKY.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value=1.2
FRAME=mat("Window_frame_black_steel",(0.015,0.015,0.015),0.4,0.6); DOOR=mat("Door_white",(0.9,0.9,0.88),0.4)
GLOBE=mat("Globe_pendant_opal",(1,0.97,0.92),0.3,emit=(1,0.8,0.6),ew=4); LAMPS=mat("Lamp_shade_opal",(1,0.97,0.92),0.3,emit=(1,0.8,0.6),ew=3)
LEAF=mat("Plant_leaf",(0.08,0.25,0.07),0.6); POT=mat("Pot_terracotta",(0.55,0.32,0.2),0.8); TVS=mat("TV_screen",(0.01,0.01,0.012),0.08)
DLM=mat("Downlight_3000K",(1,0.9,0.75),0.3,emit=(1,0.78,0.55),ew=15)
ART=[mat(f"Art_{i}_illustrative",(1,1,1),0.6,img=f"art_r4_{i}.jpg") for i in (1,2,3)]
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
def room_poly(rid): return [m(*q) for q in next(r for r in LY.TRACE["rooms"] if r["id"]==rid)["poly"]]
# ---------- floor: ONE continuous slab (internal faces = 63 m2), plus finish inlays on the traced rooms
poly_slab("Floor_continuous_oak",OUTL,-0.05,0.0,OAK,1.2)
poly_slab("Floor_kitchen_pale_grey",room_poly("i_kitchen"),0.0,0.003,OAKG,1.2)
poly_slab("Floor_bathroom_tile",room_poly("i_bath"),0.0,0.004,TILE,1.2)
poly_slab("Ceiling",OUTL,CEIL,CEIL+0.05,CEILM,2)
# ---------- walls (exterior ink width from plan; partitions 0.10 m STAND-IN); door/opening gaps from plan
for w in LY.walls_bl():
    seg(w["name"],V(w["a"]),V(w["b"]),CEIL,WALL,t=w["t"],gaps=tuple(tuple(g) for g in w["gaps"]))
# ---------- windows: glazed spans exactly as drawn (two glass lines pier to pier); sill/head STAND-IN
CEN=sum(OUTL,Vector())/len(OUTL)
def rect_window(n,a,b,depth,sill,head):
    d=b-a;L=d.length;u=d/L;ang=math.atan2(d.y,d.x);c=(a+b)/2;nrm=Vector((-u.y,u.x,0))
    if (CEN-c).dot(nrm)<0: nrm=-nrm            # inward
    box(n+"_wall_below_sill",(c.x,c.y,sill/2),(L,depth,sill),WALL,ang,0)
    box(n+"_wall_above_head",(c.x,c.y,(head+CEIL)/2),(L,depth,CEIL-head),WALL,ang,0)
    box(n+"_glass_daylight",(c.x,c.y,(sill+head)/2),(L,0.01,head-sill),WGLASS,ang,0)
    q=c+nrm*(depth/2+0.01); box(n+"_sill_board",(q.x,q.y,sill-0.015),(L,0.06,0.03),SKIRT,ang,0)
    nm=max(2,round(L/0.8)); fw=0.05
    for k in range(nm+1):
        p=a+u*(L*k/nm); box(n+"_mullion",(p.x,p.y,(sill+head)/2),(fw if 0<k<nm else 0.08,0.05,head-sill),FRAME,ang,0)
    for z in (sill,sill+(head-sill)*0.62,head): box(n+"_transom",(c.x,c.y,z),(L,0.05,fw),FRAME,ang,0)
    bp=c-nrm*(depth/2+0.6); box(n+"_backdrop",(bp.x,bp.y,(sill+head)/2),(L+1.2,0.01,head-sill+1.0),SKY,ang,0)
    lp=c-nrm*(depth/2+0.45); bpy.ops.object.light_add(type='AREA',location=(lp.x,lp.y,(sill+head)/2)); L_=bpy.context.object; L_.name=n+"_daylight"
    L_.data.shape='RECTANGLE'; L_.data.size=L; L_.data.size_y=head-sill; L_.data.energy=90*L; L_.data.color=(0.95,0.97,1)
    L_.rotation_euler=Vector((0,0,1)).rotation_difference(nrm).to_euler()
for wd in LY.windows_bl(): rect_window(wd["name"],V(wd["a"]),V(wd["b"]),wd["depth"],wd["sill"],wd["head"])
# ---------- doors (hinge, width, open angle all from the plan symbols; leaf height STAND-IN)
def door(n,hinge,ang_open,w):
    o=box(n,(0,0,1.05),(w,0.04,2.08),DOOR,0,0.003)
    e=bpy.data.objects.new(n+"_pivot",None);sc.collection.objects.link(e);e.location=(hinge.x,hinge.y,0);o.parent=e;o.location=(w/2,0,1.05)
    e.rotation_euler[2]=ang_open
for d in LY.doors_bl(): door(d["name"],V(d["hinge"]),d["open"],d["w"]-0.01)
# ---------- joinery drawn on the plan (heights STAND-IN)
JM={"Wardrobe_bed2":OAKF,"Wardrobe_living_W":WUNIT,"Wardrobe_living_C":WUNIT,"TV_unit":OAKF}
for j in LY.joinery_bl():
    pts=[V(p) for p in j["poly"]]
    if j["name"].startswith("Kitchen_run"):
        poly_slab(j["name"]+"_plinth",pts,0.0,0.08,DARK,1.2); poly_slab(j["name"]+"_base_units",pts,0.08,0.86,WUNIT,1.2); poly_slab(j["name"]+"_worktop",pts,0.86,0.9,WTOP,1.2)
    elif j["name"]=="Entrance_steps":
        for ty in (278,286,295): a,b=m(122,ty),m(161,ty); c=(a+b)/2; box("Step_nosing_line_RISERS_NOT_FOUND",(c.x,c.y,0.004),((b-a).length,0.04,0.008),DARK,0,0)
    else: poly_slab(j["name"],pts,0.0,j["h"],JM[j["name"]],1.2)
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
FUR={f["name"]:f for f in LY.furniture()}
def FC(n): return V(FUR[n]["c"])
# ---------- KITCHEN (L-shaped run as drawn: south wall x 161-253, east leg y 277-321)
a,b=m(161,343.5),m(253.5,343.5); c=(a+b)/2; L_=(b-a).length
box("Wall_units_south",(c.x,c.y+0.18,1.81),(L_-0.02,0.35,0.72),WUNIT,0,0.002)
box("LED_strip_under_wall_units",(c.x,c.y+0.3,1.445),(L_-0.1,0.02,0.01),LED,0,0)
h=FC("Hob"); box("Induction_hob_black",(h.x,h.y,0.903),(0.52,0.5,0.006),BLK,0,0.002)
s=FC("Sink"); box("Sink_steel",(s.x,s.y,0.905),(0.42,0.36,0.012),STEEL,0,0.002); cyl("Tap_body",(s.x+0.2,s.y,1.08),0.018,0.36,CHROME,20); cyl("Tap_outlet",(s.x+0.05,s.y,1.24),0.016,0.06,CHROME,16)
for k in range(10):
    a_=math.pi*k/9; q=Vector((s.x+0.2-0.15*(1-math.cos(a_)),s.y,1.26+0.1*math.sin(a_))); sph("Tap_gooseneck_arc",q,0.016,CHROME)
wm=FC("Washing_machine"); fy=m(0,321).y+0.006   # front of the south run (plan line y=321)
box("Washing_machine_front_black",(wm.x,fy,0.47),(0.597,0.012,0.78),BLK,0,0)
r_=cyl("WM_door_chrome_ring",(wm.x,fy+0.02,0.45),0.19,0.03,CHROME,40);r_.rotation_euler=(math.pi/2,0,0)
g_=cyl("WM_door_glass_dark",(wm.x,fy+0.03,0.45),0.155,0.03,TVS,40);g_.rotation_euler=(math.pi/2,0,0)
# ---------- LIVING / DINING
def sofa(c,ang,sy=1.0,sx=1.0):
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
    e.location=c;e.rotation_euler[2]=ang;e.scale=(sx,sy,1)
sf=FUR["Sofa_navy_velvet_3seat"]; sofa((sf["c"][0],sf["c"][1],0),0,sy=sf["s"][1]/2.36,sx=sf["s"][0]/0.94)   # plan footprint 53 x 29 px
rg=FC("Rug_cream"); box("Rug_cream",(rg.x,rg.y,0.006),(1.5,2.0,0.012),RUG,0,0.003)
ct=FC("Coffee_table_oak_top"); box("Coffee_table_oak_top",(ct.x,ct.y,0.42),(0.55,1.05,0.035),OAKF,0,0.006)
for a,b in ((-0.27,-0.5),(0.27,-0.5),(-0.27,0.5),(0.27,0.5)): box("Coffee_table_black_metal_leg",(ct.x+a*0.95,ct.y+b*0.97,0.2),(0.02,0.02,0.4),BMET,0,0)
box("Coffee_table_shelf_oak",(ct.x,ct.y,0.13),(0.5,1.0,0.02),OAKF,0,0.004); box("Coffee_book",(ct.x+0.1,ct.y-0.25,0.455),(0.22,0.3,0.03),RUG,0,0.003)
tv=FC("TV_on_media_unit"); tvx=m(137,0).x-0.12   # screen faces the sofa (+X); media unit = plan box x 122-137
box("TV_stand_post",(tvx,tv.y,0.52),(0.03,0.06,0.14),BMET,0,0)
box("TV_bezel_black_facing_sofa",(tvx,tv.y,0.92),(0.04,1.12,0.66),BLK,0,0.004); box("TV_screen",(tvx+0.021,tv.y,0.93),(0.002,1.08,0.61),TVS,0,0)
ax=m(253.5,0).x-0.02; box("Art_living_frame",(ax,sf["c"][1],1.6),(0.03,0.8,1.05),BMET,0,0); box("Art_living",(ax-0.02,sf["c"][1],1.6),(0.01,0.72,0.97),ART[1],0,0)
pp=FC("Plant_pot"); cyl("Plant_pot",(pp.x,pp.y,0.2),0.18,0.4,POT,24,0.14)
for j in range(9): a=j*0.7; sph("Plant_leaf",(pp.x+0.25*math.cos(a)*(j%3)/2,pp.y+0.25*math.sin(a)*(j%3)/2,0.75+0.12*(j%4)),0.18,LEAF,1.2,0.5,0.25)
dt=FUR["Dining_table_oak"]; dc=V(dt["c"]); tw,td=dt["s"]
box("Dining_table_oak_top",(dc.x,dc.y,0.74),(tw,td,0.035),OAKF,0,0.006)
for sx_ in (-1,1): box("Dining_table_leg_black",(dc.x+sx_*(tw/2-0.08),dc.y,0.36),(0.04,td-0.12,0.72),BMET,0,0)
def tub(c,ang):
    e=bpy.data.objects.new("Tub_chair_cream_boucle",None);sc.collection.objects.link(e)
    s=cyl("Tub_seat",(0,0,0.45),0.26,0.1,BOUC,32);s.parent=e
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=False,segments=32,radius1=0.27,radius2=0.29,depth=0.35)
    for v in list(bm.verts):
        if math.atan2(v.co.y,v.co.x)<-0.2*math.pi and math.atan2(v.co.y,v.co.x)>-0.8*math.pi: bm.verts.remove(v)
    bk=obj_from(bm,"Tub_back",BOUC);bk.location=(0,0,0.67);bk.parent=e;md=bk.modifiers.new("s","SOLIDIFY");md.thickness=0.06
    for a in range(4): q=a*math.pi/2+math.pi/4; cyl("Tub_leg_black",(0.2*math.cos(q),0.2*math.sin(q),0.2),0.012,0.4,BMET).parent=e
    e.location=c;e.rotation_euler[2]=ang
for k in range(4): f=FUR[f"Tub_chair_{k}"]; tub((f["c"][0],f["c"][1],0),f["rot"])
# --- geometric chair facing check (print + assert): opening must face the nearest table edge
_chairs=[o for o in sc.objects if o.name.startswith("Tub_chair_cream_boucle") and o.parent is None]
print("CHAIR_COUNT",len(_chairs)); assert len(_chairs)==4, f"expected 4 chairs, got {len(_chairs)}"
for e in _chairs:
    ang=e.rotation_euler[2]; pos=e.location.copy()
    open_dir=Vector((math.sin(ang),-math.cos(ang),0)).normalized()
    q=Vector((min(max(pos.x,dc.x-tw/2),dc.x+tw/2),min(max(pos.y,dc.y-td/2),dc.y+td/2),0)); to_table=(q-pos); to_table.z=0; to_table.normalize()
    dot=open_dir.dot(to_table); ok=dot>0.9
    print(f"CHAIR_CHECK name={e.name} pos=({pos.x:.3f},{pos.y:.3f}) rot_z={ang:.4f} dot={dot:.3f} PASS={ok}"); assert ok, "chair facing failed geometric check"
print("CHAIR_CHECK_ALL_PASS")
cyl("Pendant_cord",(dc.x,dc.y,(CEIL+1.75)/2),0.004,CEIL-1.75,BMET); sph("Globe_pendant_white",(dc.x,dc.y,1.6),0.2,GLOBE)
bpy.ops.object.light_add(type='POINT',location=(dc.x,dc.y,1.55));bpy.context.object.name="Pendant_light";bpy.context.object.data.energy=40;bpy.context.object.data.color=(1,0.78,0.55)
# ---------- BEDROOMS (bed footprint = drawn foot edge to the drawn head wall)
def bed(n,c,ang,W=1.45,Lb=2.05):
    e=bpy.data.objects.new(n,None);sc.collection.objects.link(e)
    for o in (box("Bed_base_navy_velvet",(0,0,0.2),(W,Lb,0.32),NAVY,0,0.03),box("Mattress_white",(0,-0.03,0.47),(W-0.08,Lb-0.1,0.22),LIN,0,0.05),
              box("Duvet_white",(0,-0.2,0.6),(W-0.02,Lb*0.7,0.08),LIN,0,0.04),box("Throw_navy_folded",(0,-Lb*0.35,0.655),(W+0.06,0.5,0.03),NAVY,0,0.012),
              box("Pillow",(-W*0.23,Lb/2-0.2,0.66),(W*0.42,0.32,0.15),LIN,0,0.07),box("Pillow",(W*0.23,Lb/2-0.2,0.66),(W*0.42,0.32,0.15),LIN,0,0.07),
              box("Cushion_navy",(0,Lb/2-0.4,0.7),(0.4,0.14,0.32),NAVY,0,0.06)): o.parent=e
    for k in range(9):
        sp=(W+0.1)/9; x=-W/2-0.05+sp/2+k*sp
        o=cyl("Headboard_channel_flute_navy",(x,Lb/2+0.06,0.6),sp/2+0.004,1.1,NAVY,20);o.scale=(1,0.7,1);o.parent=e
        t=sph("Headboard_flute_top",(x,Lb/2+0.06,1.15),sp/2+0.004,NAVY,1,0.7,0.6);t.parent=e
    box("Headboard_backing",(0,Lb/2+0.1,0.6),(W+0.1,0.04,1.15),NAVY,0,0.01).parent=e
    e.location=c;e.rotation_euler[2]=ang
def bedside(n,c,ang):
    e=bpy.data.objects.new("Bedside_table_oak",None);sc.collection.objects.link(e)
    for o in (box("Bedside_oak_body",(0,0,0.42),(0.45,0.4,0.32),OAKF),box("Bedside_drawer_line",(0,-0.201,0.42),(0.4,0.004,0.004),BMET,0,0)): o.parent=e
    for a,b in ((-0.2,-0.17),(0.2,-0.17),(-0.2,0.17),(0.2,0.17)): cyl("Bedside_leg_black",(a,b,0.13),0.012,0.26,BMET).parent=e
    cyl("Lamp_stem_black",(0,0,0.68),0.012,0.2,BMET).parent=e; s=sph("Lamp_mushroom_opal",(0,0,0.8),0.14,LAMPS,1,1,0.6);s.parent=e
    e.location=c;e.rotation_euler[2]=ang
    bpy.ops.object.light_add(type='POINT',location=(c[0],c[1],0.85));bpy.context.object.data.energy=12;bpy.context.object.data.color=(1,0.75,0.5)
for bn in ("Bed1_navy","Bed2_navy"):
    f=FUR[bn]; bed(bn,(f["c"][0],f["c"][1],0),f["rot"],f["W"],f["Lb"])
    for k in (0,1): g=FUR[f"{bn[:4]}_bedside_{k}"]; bedside(g["name"],(g["c"][0],g["c"][1],0),g["rot"])
b1,b2=FC("Bed1_navy"),FC("Bed2_navy")
# art on the bedroom 1 west (raked) wall, half way along the inner face (7.5,84)-(25.4,179.6)
wa,wb=m(7.5,84),m(25.4,179.6); wc=(wa+wb)/2; wu=(wb-wa).normalized(); wn=Vector((wu.y,-wu.x,0))
if (b1-wc).dot(wn)<0: wn=-wn
q=wc+wn*0.02; box("Art_bed1_frame_side_wall",(q.x,q.y,1.6),(0.6,0.03,0.8),BMET,math.atan2(wu.y,wu.x),0); q=wc+wn*0.037; box("Art_bed1",(q.x,q.y,1.6),(0.54,0.005,0.74),ART[0],math.atan2(wu.y,wu.x),0)
# ---------- BATHROOM (plan: WC + basin on the west wall, walk-in shower zone south of the dashed line y=313)
bx0,by0=m(16.5,343.5).x,m(16.5,343.5).y; bx1,by1=m(84,264).x,m(84,264).y
sh=FUR["Shower_tray"]; box("Shower_tray",(sh["c"][0],sh["c"][1],0.02),(sh["s"][0],sh["s"][1],0.04),WHITEP,0,0.004)
cyl("Shower_riser_chrome",(bx0+0.45,by0+0.02,1.45),0.012,1.3,CHROME,12); box("Shower_arm_chrome",(bx0+0.45,by0+0.17,2.12),(0.025,0.32,0.025),CHROME,0,0.005); cyl("Shower_head",(bx0+0.45,by0+0.33,2.09),0.11,0.012,CHROME)
for nm_,c,s in (("Bath_wall_tile_S",(bx0+(bx1-bx0)/2,by0+0.005,1.2),((bx1-bx0)-T/2,0.01,2.4)),("Bath_wall_tile_W",(bx0+0.005,(by0+by1)/2,1.2),(0.01,by1-by0-T/2,2.4))): box(nm_,c,s,TILE,0,0)
wc_=FC("WC_pan"); box("WC_cistern_concealed_tile",(bx0+0.1,wc_.y,0.55),(0.2,0.6,1.1),TILE,0,0.004); box("WC_flush_plate_chrome",(bx0+0.204,wc_.y,0.85),(0.008,0.22,0.15),CHROME,0,0.002)
o=cyl("WC_bowl_rounded",(bx0+0.45,wc_.y,0.2),0.14,0.4,WHITEP,40,r2=0.185); o.scale=(1.3,1.0,1)
o=cyl("WC_seat_ring",(bx0+0.45,wc_.y,0.415),0.185,0.03,WHITEP,40); o.scale=(1.3,1.0,1)
o=cyl("WC_seat_opening_shadow",(bx0+0.47,wc_.y,0.432),0.1,0.004,GREYV,32); o.scale=(1.4,1.0,1)
vb=FC("Vanity_basin"); box("Vanity_grey_stone_look",(vb.x,vb.y,0.62),(0.46,0.55,0.3),GREYV,0,0.006); box("Basin_white_wallhung",(vb.x,vb.y,0.82),(0.42,0.5,0.12),WHITEP,0,0.04)
cyl("Basin_tap",(bx0+0.06,vb.y,0.95),0.012,0.14,CHROME,12)
box("Mirror_black_frame",(bx0+0.012,vb.y,1.55),(0.02,0.55,0.75),FRAME,0,0.002); box("Mirror_glass",(bx0+0.024,vb.y,1.55),(0.006,0.5,0.7),CHROME,0,0)
tx=m(32,0).x; ty=by1-T/2-0.03
for sd in (-0.2,0.2): box("Towel_ladder_vertical_chrome",(tx+sd,ty,1.0),(0.03,0.03,1.2),CHROME,0,0.01)
for z in (0.5,0.65,0.8,0.95,1.1,1.25,1.4,1.55): box("Towel_ladder_bar_chrome",(tx,ty,z),(0.4,0.02,0.02),CHROME,0,0.006)
bpy.ops.object.light_add(type='AREA',location=((bx0+bx1)/2,(by0+by1)/2,CEIL-0.05));l=bpy.context.object;l.name="Bath_ceiling_panel";l.data.size=1.2;l.data.energy=70;l.data.color=(1,0.92,0.82)
# storage shelving (illustrative) in the traced storage room
st=FUR["Storage_shelving_white"]; box("Storage_shelving_white",(st["c"][0],st["c"][1],1.1),(st["s"][0],st["s"][1],2.2),WUNIT,0,0.003)
# ---------- render setup
for o in sc.objects:
    if o.type=='MESH':
        for f in o.data.polygons: f.use_smooth=False
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in sc.view_settings.bl_rna.properties['look'].enum_items] else 'None'
sc.world=bpy.data.worlds.new("w");sc.world.use_nodes=True;bg=sc.world.node_tree.nodes['Background'];env=sc.world.node_tree.nodes.new("ShaderNodeTexEnvironment");env.image=bpy.data.images.load(os.path.join(ROOT,"hdri.exr"));sc.world.node_tree.links.new(env.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=0.3
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
def cam_bl(rid):
    p,t,hp,ht,f=LY.CAMS[rid]; return (m(*p).x,m(*p).y,hp),(m(*t).x,m(*t).y,ht)
for rid in LY.CAMS: print("PRESET",rid,*[tj(v) for v in cam_bl(rid)])
shot("v5_living",*cam_bl("i_living"),20)
shot("v5_kitchen",*cam_bl("i_kitchen"),20)
shot("v5_bedroom1",*cam_bl("i_bed1"),20)
shot("v5_bedroom2",*cam_bl("i_bed2"),20)
shot("v5_bathroom",*cam_bl("i_bath"),14)
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
