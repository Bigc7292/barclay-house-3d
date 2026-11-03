# Builds surroundings_data.json: OSM street furniture/POIs (Overpass, 250 m) + LIDAR-derived trees + viaduct/rail geometry. Local BNG metres, origin = hero centroid (same as prep.py).
import json, numpy as np, tifffile as T, warnings, math
from pyproj import Transformer; from matplotlib.path import Path; from scipy import ndimage as ndi
warnings.filterwarnings("ignore"); tr=Transformer.from_crs(4326,27700,always_xy=True)
SD=json.load(open('scene_data.json')); OE,ON=SD['origin_bng']; G0=SD['street_odn']
dsm=T.imread('lidar/dsm.tif').astype(float); dtm=T.imread('lidar/dtm.tif').astype(float)
dsm[dsm<-1e30]=np.nan; dtm[dtm<-1e30]=np.nan; nd=dsm-dtm; E0,N0=383580,397940; H,W=nd.shape
OV=json.load(open('data/overpass_250m.json')); SRC=open('data/overpass_src.txt').read().strip()
loc=lambda lon,lat:(lambda e,n:(round(e-OE,2),round(n-ON,2)))(*tr.transform(lon,lat))
def samp(a,x,y):
    r,c=int(N0-(y+ON)),int((x+OE)-E0); return round(float(a[r,c]),2) if 0<=r<H and 0<=c<W and a[r,c]==a[r,c] else None
KEEP={'highway':{'street_lamp','crossing','traffic_signals','bus_stop','give_way','stop','elevator'},'natural':{'tree'},
 'barrier':{'kerb','bollard','gate','lift_gate','fence'},'amenity':{'bench','waste_basket','bicycle_parking','post_box','telephone','recycling','fountain','taxi','atm','vending_machine','bicycle_rental','motorcycle_parking','toilets','public_bookcase','parking_entrance'},
 'man_made':None,'advertising':None,'traffic_sign':None,'railway':None}
furn=[];pois=[]
for e in OV['elements']:
    if e['type']!='node': continue
    t=e.get('tags',{}); p=loc(e['lon'],e['lat']); g=samp(dtm,*p); rec={'osm':'node/%d'%e['id'],'xy':p,'z_ground':round(g-G0,2) if g else None,'tags':t}
    if any(k in t and (v is None or t[k] in v) for k,v in KEEP.items()): furn.append(rec)
    elif any(k in t for k in('shop','amenity','leisure','tourism','office','craft')) or 'name' in t: pois.append(rec)
# buildings w/ address + names from Overpass ways
blds=[]
for e in OV['elements']:
    if e['type']=='way' and 'building' in e.get('tags',{}):
        t=e['tags']; xy=[loc(g['lon'],g['lat']) for g in e['geometry']]; cx=np.mean([a for a,b in xy]); cy=np.mean([b for a,b in xy])
        blds.append({'osm':'way/%d'%e['id'],'centroid':[round(cx,1),round(cy,1)],'dist':round(math.hypot(cx,cy),1),'tags':t})
# LIDAR trees: nDSM 2.5-30 m outside building footprints, rail/viaduct buffer; blobs >=4 px
mask=(nd>2.5)&(nd<30)
yy,xx=np.mgrid[0:H,0:W]; P=np.c_[E0+xx.ravel()+.5,N0-yy.ravel()-.5]
bm=np.zeros(H*W,bool)
for b in SD['buildings']:
    pts=[(x+OE,y+ON) for x,y in b['pts']]; xs=[a for a,_ in pts]; ys=[c for _,c in pts]
    sel=(P[:,0]>min(xs)-2)&(P[:,0]<max(xs)+2)&(P[:,1]>min(ys)-2)&(P[:,1]<max(ys)+2)
    if sel.any(): bm[np.where(sel)[0][Path(pts).contains_points(P[sel])]]=True
bm=ndi.binary_dilation(bm.reshape(H,W),iterations=2)
rm=np.zeros((H,W),bool)
for rl in SD['rails']:
    for (x0,y0),(x1,y1) in zip(rl['pts'],rl['pts'][1:]):
        L=max(1,int(math.dist((x0,y0),(x1,y1))))
        for k in range(L+1):
            x=x0+(x1-x0)*k/L; y=y0+(y1-y0)*k/L; r,c=int(N0-(y+ON)),int((x+OE)-E0)
            if 0<=r<H and 0<=c<W: rm[max(r-7,0):r+8,max(c-7,0):c+8]=True
# roughness: trees are spiky (high local std), flat walls/vehicles not
sd=ndi.generic_filter(np.nan_to_num(dsm),np.std,size=3)
m=mask&~bm&~rm&(sd>0.4); lab,n=ndi.label(m)
trees=[]
for i,sl in enumerate(ndi.find_objects(lab),1):
    reg=lab[sl]==i; a=int(reg.sum())
    if a<4 or a>400: continue
    r,c=ndi.center_of_mass(reg); r+=sl[0].start; c+=sl[1].start; x=E0+c+.5-OE; y=N0-r-.5-ON
    if math.hypot(x,y)>260: continue
    h=float(np.nanmax(nd[sl][reg])); trees.append({'xy':[round(x,2),round(y,2)],'height':round(h,1),'canopy_d':round(2*math.sqrt(a/math.pi),1),'px':a,'z_ground':samp(dtm,x,y) and round(samp(dtm,x,y)-G0,2),'src':'EA LIDAR 1 m DSM-DTM blob (measured)'})
osm_trees=[f for f in furn if f['tags'].get('natural')=='tree']
for t in trees: t['osm_match']=min([math.dist(t['xy'],o['xy']) for o in osm_trees] or [99])<4
rails=[{'osm':'way/'+r['id'],'k':r['k'],'bridge':r.get('bridge'),'name':r.get('name'),'pts':r['pts'],'deck_z_dsm':r['z']} for r in SD['rails']]
vz=[z for r in SD['rails'] if r.get('bridge')=='viaduct' for z in r['z'] if z and 5<z<16]
out={'origin':'local BNG metres, origin hero centroid E%.2f N%.2f; z rel. street ODN %.2f m'%(OE,ON,G0),
 'sources':{'osm':SRC+' (Overpass, around:250 m of 53.47415,-2.24419, fetched 2026-11-03, ODbL)','lidar':'EA National LIDAR Programme 1 m DSM/DTM via WCS (lidar/*.tif, OGL v3) https://environment.data.gov.uk/survey','base':'scene_data.json (prep.py)'},
 'furniture':furn,'pois':pois,'buildings_osm':sorted(blds,key=lambda b:b['dist']),'trees_lidar':trees,'rails':rails,
 'viaduct':{'deck_z_median':round(float(np.median(vz)),2) if vz else None,'n_samples':len(vz),'src':'EA LIDAR DSM along OSM railway=rail bridge=viaduct','arch_span':'NOT FOUND (stand-in 9 m)','pier_w':'NOT FOUND (stand-in 1.8 m)'},
 'not_in_osm':['highway=street_lamp: 0 nodes in 250 m -> lamp positions are stand-in','traffic_sign: none','bin positions: %d waste_basket only'%sum(f['tags'].get('amenity')=='waste_basket' for f in furn)]}
json.dump(out,open('surroundings_data.json.tmp','w'),indent=0); import os; os.replace('surroundings_data.json.tmp','surroundings_data.json')
from collections import Counter
print('furn',len(furn),Counter(next((k+'='+f['tags'][k] for k in KEEP if k in f['tags']),'?') for f in furn).most_common(20))
print('pois',len(pois),'blds',len(blds),'lidar trees',len(trees),'matched osm',sum(t['osm_match'] for t in trees),'viaduct',out['viaduct'])
