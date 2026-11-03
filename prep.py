# Preprocess OSM + EA LIDAR into local BNG metres (origin = hero centroid) -> scene_data.json
import json, numpy as np, tifffile as T, warnings, xml.etree.ElementTree as ET
from pyproj import Transformer; from matplotlib.path import Path
warnings.filterwarnings("ignore")
tr=Transformer.from_crs(4326,27700,always_xy=True)
OE,ON=383889.38,397518.84  # hero centroid BNG
dsm=T.imread('lidar/dsm.tif').astype(float); dtm=T.imread('lidar/dtm.tif').astype(float)
dsm[dsm<-1e30]=np.nan; dtm[dtm<-1e30]=np.nan; nd=dsm-dtm; E0,N0=383580,397940; H,W=nd.shape
def rc(e,n): return int(N0-n),int(e-E0)
def samp(a,e,n):
  r,c=rc(e,n); return float(a[r,c]) if 0<=r<H and 0<=c<W else np.nan
r=ET.parse('area.osm').getroot()
N={x.get('id'):tr.transform(float(x.get('lon')),float(x.get('lat'))) for x in r.iter('node')}
tags=lambda e:{t.get('k'):t.get('v') for t in e.iter('tag')}
G0=samp(dtm,OE,ON-25)  # street level in front of hero (Whitworth St W)
out={'origin_bng':[OE,ON],'street_odn':G0,'buildings':[],'roads':[],'rails':[],'water':[],'trees':[],'lamps':[]}
def num(v):
  try: return float(str(v).split()[0])
  except: return None
for w in r.iter('way'):
  t=tags(w); pts=[N[n.get('ref')] for n in w.iter('nd') if n.get('ref') in N]
  if len(pts)<2: continue
  loc=[(round(e-OE,2),round(n-ON,2)) for e,n in pts]
  if 'building' in t and pts[0]==pts[-1]:
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    r0,c0=rc(min(xs),max(ys)); r1,c1=rc(max(xs),min(ys)); r0=max(r0,0);c0=max(c0,0);r1=min(r1+1,H);c1=min(c1+1,W)
    rec={'id':w.get('id'),'pts':loc,'name':t.get('name',t.get('addr:housename',''))}
    if r1>r0 and c1>c0:
      yy,xx=np.mgrid[r0:r1,c0:c1]; m=Path(pts).contains_points(np.c_[E0+xx.ravel()+.5,N0-yy.ravel()-.5])
      v=nd[r0:r1,c0:c1].ravel()[m]; g=dtm[r0:r1,c0:c1].ravel()[m]; v=v[~np.isnan(v)]
      if len(v)>=4: rec.update(h=round(float(np.median(v)),2),h_p95=round(float(np.percentile(v,95)),2),base=round(float(np.nanmin(g))-G0,2),src='EA LIDAR nDSM median (measured)')
    if num(t.get('height')): rec.update(h=num(t['height']),src='OSM height tag')
    if 'h' not in rec and t.get('building:levels'): rec.update(levels=num(t['building:levels']),src='OSM levels only (no LIDAR px)')
    out['buildings'].append(rec)
  elif 'highway' in t:
    out['roads'].append({'id':w.get('id'),'pts':loc,'k':t['highway'],'name':t.get('name',''),'bridge':t.get('bridge'),'layer':t.get('layer'),'area':t.get('area')})
  elif t.get('railway') in('rail','light_rail','tram','platform'):
    zs=[]
    for e,n in pts: zs.append(samp(dsm,e,n)-G0)
    out['rails'].append({'id':w.get('id'),'pts':loc,'k':t['railway'],'bridge':t.get('bridge'),'z':[round(z,2) if z==z else None for z in zs],'name':t.get('name','')})
  elif (t.get('natural')=='water' or t.get('waterway') in('canal','riverbank') or t.get('landuse')=='basin'):
    out['water'].append({'id':w.get('id'),'pts':loc,'closed':pts[0]==pts[-1],'k':t.get('waterway',t.get('natural'))})
for n in r.iter('node'):
  t=tags(n)
  if not t: continue
  e,nn=N[n.get('id')]; p=(round(e-OE,2),round(nn-ON,2))
  if t.get('natural')=='tree': out['trees'].append(p+(round(samp(nd,e,nn),1),))
  if t.get('highway')=='street_lamp': out['lamps'].append(p)
# DTM grid 2 m, relative to street level
d=dtm[::2,::2]-G0; out['dtm']={'e0':E0-OE,'n0':N0-ON,'step':2,'rows':d.shape[0],'cols':d.shape[1],'z':[round(float(x),2) if x==x else 0 for x in d.ravel()]}
json.dump(out,open('scene_data.json','w'))
hb=[b for b in out['buildings'] if b['id']=='100646649'][0]
print('street ODN',round(G0,2),'hero',{k:hb.get(k) for k in('h','h_p95','base','src')},'bld',len(out['buildings']),'lidar',sum('LIDAR' in b.get('src','') for b in out['buildings']),'rails',len(out['rails']),'water',len(out['water']),'trees',len(out['trees']),'lamps',len(out['lamps']))
vz=[z for rl in out['rails'] if rl['bridge']=='viaduct' for z in rl['z'] if z is not None]
print('viaduct deck (DSM-street) median',np.median(vz) if vz else None, 'n',len(vz))
