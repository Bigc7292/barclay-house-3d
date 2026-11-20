# lane/polish: procedural textures (PIL only, free). Illustrative, not sourced.
#  storage_front_diff.jpg / storage_front_nor_gl.png : painted door/drawer front for the storage unit (defect 1, texture-only, no model swap)
#  art_p5_{1,2,3}.jpg : crisp high-contrast illustrative art, sRGB, 1024x1365 (defect 5)
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
D=__file__.rsplit('/',1)[0]+'/'
# ---------------- storage front: 1.74 m x 2.20 m
W_M,H_M=1.74,2.20; PX=900; W,H=int(W_M*PX),int(H_M*PX)   # 1566 x 1980
def mm(v): return int(round(v*PX))
h=np.ones((H,W),np.float32)          # height: 1 = door face, 0 = groove/recess
alb=np.zeros((H,W,3),np.float32); alb[:]=(0.88,0.87,0.84)   # warm white satin (matches Kitchen_handleless_white family)
def rect(a,x0,y0,x1,y1,v): a[H-mm(y1):H-mm(y0),mm(x0):mm(x1)]=v      # metres, y up from floor
G=0.004  # 4 mm shadow gap
col=[(0.0,0.58),(0.58,1.16),(1.16,1.74)]
# plinth recess 0..0.10 (dark, set back)
rect(h,0,0,W_M,0.10,0.0); rect(alb,0,0,W_M,0.10,(0.10,0.10,0.11))
# top band
rect(h,0,2.17,W_M,2.20,0.6)
fronts=[]  # (x0,y0,x1,y1)
fronts+=[(col[0][0],0.10,col[0][1],2.17),(col[1][0],0.10,col[1][1],2.17)]
fronts+=[(col[2][0],1.10,col[2][1],2.17)]+[(col[2][0],0.10+i*0.3333,col[2][1],0.10+(i+1)*0.3333) for i in range(3)]
# grooves: everything in carcass zone is groove, then fronts raised
rect(h,0,0.10,W_M,2.17,0.0); rect(alb,0,0.10,W_M,2.17,(0.30,0.29,0.28))
for (x0,y0,x1,y1) in fronts:
    rect(h,x0+G/2,y0+G/2,x1-G/2,y1-G/2,1.0); rect(alb,x0+G/2,y0+G/2,x1-G/2,y1-G/2,(0.88,0.87,0.84))
# handles: brushed dark bronze bars (vertical on tall doors, horizontal on drawers)
HC=(0.12,0.10,0.08)
def bar(x0,y0,x1,y1):
    rect(h,x0,y0,x1,y1,1.6); rect(alb,x0,y0,x1,y1,HC)
    rect(alb,x0+0.003,y0+0.003,x0+(x1-x0)*0.45,y1-0.003,(0.30,0.26,0.21))   # highlight strip
bar(0.58-0.045,0.95,0.58-0.025,1.25); bar(0.58+0.025,0.95,0.58+0.045,1.25)      # pair on tall doors (meeting stiles)
bar(1.16+0.04,1.13,1.16+0.06,1.43)                                                # top door of right column
for i in range(3):
    yt=0.10+(i+1)*0.3333; bar(1.45-0.13,yt-0.075,1.45+0.13,yt-0.055)              # drawer pulls
# soft edge AO painted into grooves (darken face near gaps)
hb=Image.fromarray((np.clip(h,0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
ao=0.82+0.18*(np.asarray(hb,np.float32)/255)
alb*=np.where(h[...,None]>=0.99,ao[...,None],1.0)
# subtle satin paint grain
rng=np.random.default_rng(7); alb*=1+rng.normal(0,0.008,(H,W,1)).astype(np.float32)
Image.fromarray((np.clip(alb,0,1)**(1/2.2)*255).astype(np.uint8)).save(D+'storage_front_diff.jpg',quality=92)
# normal map (OpenGL, +Y up) from blurred height
hs=np.asarray(Image.fromarray((np.clip(h/1.6,0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)),np.float32)/255
gy,gx=np.gradient(hs); s=6.0; n=np.dstack([-gx*s,gy*s,np.ones_like(hs)]); n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save(D+'storage_front_nor_gl.png')
# ---------------- art (drawn at 2x then downsampled = crisp anti-aliased edges)
AW,AH=1024,1365; S=2
def canvas(bg): im=Image.new('RGB',(AW*S,AH*S),bg); return im,ImageDraw.Draw(im)
def save(im,n): im.resize((AW,AH),Image.LANCZOS).save(D+n,quality=93,subsampling=0)
# 1: mid-century arcs, navy / ochre / terracotta on warm paper
im,d=canvas((236,228,212)); w,hh=AW*S,AH*S
d.rectangle([0,int(hh*0.62),w,hh],fill=(24,38,74))
d.pieslice([int(w*0.10),int(hh*0.30),int(w*0.90),int(hh*0.94)],180,360,fill=(206,148,46))
d.pieslice([int(w*0.28),int(hh*0.46),int(w*0.72),int(hh*0.78)],180,360,fill=(176,74,44))
d.ellipse([int(w*0.60),int(hh*0.10),int(w*0.80),int(hh*0.10)+int(w*0.20)],fill=(20,20,22))
for k in range(5): y=int(hh*(0.70+k*0.05)); d.line([int(w*0.08),y,int(w*0.92),y],fill=(236,228,212),width=6*S)
save(im,'art_p5_1.jpg')
# 2: bold black line landscape + one orange sun on off-white
im,d=canvas((242,238,230))
for k in range(9):
    pts=[(x, int(hh*(0.35+k*0.065)+math.sin(x/w*math.pi*2*(1+k%3)+k)*hh*0.03)) for x in range(0,w+1,8)]
    d.line(pts,fill=(16,16,18),width=(10 if k%2==0 else 4)*S)
d.ellipse([int(w*0.58),int(hh*0.08),int(w*0.86),int(hh*0.08)+int(w*0.28)],fill=(226,92,34))
save(im,'art_p5_2.jpg')
# 3: geometric colour-block (Bauhaus-like) with strong value contrast
im,d=canvas((232,226,214))
d.rectangle([int(w*0.08),int(hh*0.08),int(w*0.55),int(hh*0.55)],fill=(28,44,86))
d.rectangle([int(w*0.45),int(hh*0.45),int(w*0.92),int(hh*0.92)],fill=(196,64,40))
d.ellipse([int(w*0.30),int(hh*0.30),int(w*0.70),int(hh*0.30)+int(w*0.40)],fill=(224,170,52))
d.polygon([(int(w*0.08),int(hh*0.92)),(int(w*0.40),int(hh*0.62)),(int(w*0.40),int(hh*0.92))],fill=(18,18,20))
save(im,'art_p5_3.jpg')
print('ok',W,H)
# ---------------- bathroom tile: grey stone-look 600x1200 porcelain (texture spans 1.2 m = box() UV tile), visible grout + veining (score: grey surfaces / fittings edges)
TS=1024; rng=np.random.default_rng(11)
def fbm(n,oct=5):
    out=np.zeros((n,n),np.float32)
    for o in range(oct):
        f=2**o*4; g=rng.random((f+1,f+1)).astype(np.float32)
        im=np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize((n,n),Image.BICUBIC),np.float32)/255
        out+=im/(2**o)
    return out/out.max()
v=fbm(TS); vein=np.abs(np.sin((np.linspace(0,1,TS)[None,:]*7+v*5)*math.pi)); vein=1-np.clip(vein*6,0,1)
base=0.50+0.10*(v-0.5)-0.16*vein
t=np.dstack([base*1.0,base*1.0,base*1.03])
gp=max(2,int(0.004/1.2*TS))
for x in (0,TS//2): t[:,max(0,x-gp//2):x+gp//2+1]=0.30
t[0:gp,:]=0.30; t[-gp:,:]=0.30
Image.fromarray((np.clip(t,0,1)**(1/2.2)*255).astype(np.uint8)).save(D+'tile_stone_grey_p5.jpg',quality=90)
# ---------------- window backdrop: street facades opposite (illustrative, view UNSOURCED) instead of a soft sky (score: window grid edges)
BW,BH=1024,2048; im=Image.new('RGB',(BW,BH)); d=ImageDraw.Draw(im)
for y in range(BH//3): c=int(150+70*y/(BH/3)); d.line([0,y,BW,y],fill=(c-30,c-10,min(255,c+25)))
x=0; k=0
while x<BW:
    w=int(rng.integers(220,420)); top=int(rng.integers(BH//6,BH//3)); col=[(150,92,70),(188,170,140),(120,80,62),(170,150,120)][k%4]
    d.rectangle([x,top,x+w,BH],fill=col)
    for yy in range(top+60,BH-80,150):
        for xx in range(x+30,x+w-60,90): d.rectangle([xx,yy,xx+50,yy+95],fill=(40,48,58)); d.line([xx+25,yy,xx+25,yy+95],fill=(225,225,220),width=4); d.line([xx,yy+47,xx+50,yy+47],fill=(225,225,220),width=4)
    x+=w; k+=1
im.save(D+'sky_backdrop_p5.jpg',quality=88)
print('tile+backdrop ok')
