"""lane/polish r10: window-view backdrop, generated (no photo): canal-side Manchester street look - towpath + railing,
Rochdale-canal-style dark water with reflections, red-brick warehouse facades with sandstone bands, soft cloudy sky.
ILLUSTRATIVE / UNSOURCED: not the real view from Barclay House. Output: sky_backdrop_p10.jpg (768x1536)."""
import numpy as np
from PIL import Image, ImageFilter
rng=np.random.default_rng(10); W,H=768,1536
y=np.linspace(0,1,H)[:,None,None]
img=np.zeros((H,W,3))
# sky (top), soft clouds
sky=np.array([0.52,0.62,0.76])*(1-y)+np.array([0.80,0.84,0.88])*y
n=rng.random((H//32+2,W//32+2)); cl=np.array(Image.fromarray((n*255).astype(np.uint8)).resize((W,H),Image.BICUBIC))/255.
img[:]=sky*(1-0.25*np.clip(cl-0.45,0,1)[...,None]*2)+0.25*np.clip(cl-0.45,0,1)[...,None]*2*np.array([0.93,0.93,0.94])
def tex(h,w,base,var=0.06,seed=0):
    r=np.random.default_rng(seed); t=np.ones((h,w,3))*base
    t*= (1+var*(r.random((h,w,1))-0.5)); return t
# facades opposite bank: y from top 0.14..0.66 (depends on building)
x0=0; k=0
while x0<W:
    bw=int(rng.integers(150,260)); top=int(H*rng.uniform(0.10,0.24)); bot=int(H*0.66)
    brick=np.array(rng.choice([[0.50,0.24,0.17],[0.56,0.29,0.20],[0.44,0.22,0.17],[0.62,0.36,0.26]]))
    f=tex(bot-top,min(bw,W-x0),brick,0.10,k)
    hh,ww=f.shape[:2]
    for yy in range(0,hh,6): f[yy:yy+1]*=0.82            # mortar courses
    for yy in range(0,hh,int(hh/5)): f[yy:yy+10]=tex(min(10,hh-yy),ww,np.array([0.74,0.66,0.52]),0.05,k+50)   # sandstone string courses
    f[:14]=tex(14,ww,np.array([0.70,0.63,0.50]),0.05,k+70)    # cornice
    # windows: tall sash grid
    cols=max(2,ww//58); fl=5
    for c in range(cols):
        wx=int((c+0.5)*ww/cols)-14
        for r in range(fl):
            wy=int(hh*0.08+r*(hh*0.9/fl)); wh=int(hh*0.9/fl*0.58)
            if wy+wh>=hh-4: continue
            g=0.16+0.10*rng.random(); f[wy:wy+wh,wx:wx+28]=np.array([g,g+0.03,g+0.06])+0.25*np.linspace(0,1,wh)[:,None,None]*rng.random()*0.4
            f[wy+wh//2:wy+wh//2+2,wx:wx+28]=0.86; f[wy:wy+wh,wx+13:wx+15]=0.86     # glazing bars
            f[wy+wh:wy+wh+4,wx-2:wx+30]=np.array([0.78,0.72,0.60])                  # sill
    img[top:bot,x0:x0+ww]=f; x0+=ww; k+=1
# canal edge coping + water
wt,wb=int(H*0.66),int(H*0.84)
img[wt:wt+10]=tex(10,W,np.array([0.55,0.53,0.50]),0.08,90)
refl=np.flipud(img[2*wt-wb+10:wt])
water=0.45*refl[:wb-wt-10]+0.55*np.array([0.10,0.16,0.14])
ripple=(np.sin(np.linspace(0,90,wb-wt-10))[:,None]*0.5+0.5)*np.random.default_rng(3).random((wb-wt-10,W))
img[wt+10:wb]=water*(0.85+0.3*ripple[...,None]*0.5)
# towpath (stone setts) + black railing in the foreground
img[wb:]=tex(H-wb,W,np.array([0.42,0.40,0.37]),0.18,91)
for yy in range(wb,H,14): img[yy:yy+2]*=0.7
ry=int(H*0.80); img[ry:ry+8]=0.06; img[ry+60:ry+64]=0.06
for xx in range(0,W,64): img[ry:wb+40,xx:xx+6]=0.07
out=Image.fromarray((np.clip(img,0,1)**(1/1.0)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
out.save("sky_backdrop_p10.jpg",quality=88); print("ok",out.size)
