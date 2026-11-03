# nDSM = EA LIDAR Composite FZ DSM 1m - DTM 1m (OGL). Per-building median / p95 / max inside footprint.
import json, numpy as np, tifffile as T, warnings; warnings.filterwarnings("ignore")
from pyproj import Transformer
from matplotlib.path import Path
t=Transformer.from_crs(4326,27700,always_xy=True)
dsm=T.imread('lidar/dsm.tif').astype(float); dtm=T.imread('lidar/dtm.tif').astype(float)
dsm[dsm<-1e30]=np.nan; dtm[dtm<-1e30]=np.nan
E0,N0=383580,397940; nd=dsm-dtm
H,W=nd.shape; yy,xx=np.mgrid[0:H,0:W]; pts=np.c_[(E0+xx.ravel()+.5),(N0-yy.ravel()-.5)]
gj=json.load(open('area.geojson')); out={}
for f in gj['features']:
  p=f['properties']
  if 'building' not in p or f['geometry']['type']!='Polygon': continue
  ring=[t.transform(*c) for c in f['geometry']['coordinates'][0]]
  xs=[r[0] for r in ring]; ys=[r[1] for r in ring]
  c0,c1=int(min(xs)-E0),int(max(xs)-E0)+1; r0,r1=int(N0-max(ys)),int(N0-min(ys))+1
  if c0<0 or r0<0 or c1>W or r1>H: continue
  sub=np.c_[(E0+xx[r0:r1,c0:c1].ravel()+.5),(N0-yy[r0:r1,c0:c1].ravel()-.5)]
  m=Path(ring).contains_points(sub)
  v=nd[r0:r1,c0:c1].ravel()[m]; v=v[~np.isnan(v)]
  if len(v)<4: continue
  g=dtm[r0:r1,c0:c1].ravel()[m]
  p['lidar_h_median']=round(float(np.median(v)),2); p['lidar_h_p95']=round(float(np.percentile(v,95)),2)
  p['lidar_h_max']=round(float(v.max()),2); p['lidar_ground_m_odn']=round(float(np.nanmedian(g)),2); p['lidar_px']=int(len(v))
  if p.get('osm_id')=='100646649': print('HERO',{k:p[k] for k in p if k.startswith('lidar')}, 'dsm max ODN',round(float(np.nanmax(dsm[r0:r1,c0:c1].ravel()[m])),2))
json.dump(gj,open('area.geojson','w'))
print('buildings with lidar',sum('lidar_h_median' in f['properties'] for f in gj['features']))
for f in gj['features']:
  p=f['properties']
  if p.get('osm_id') in('204921679','737719731','136999879'): print(p['osm_id'],p.get('building:levels'),p.get('lidar_h_median'),p.get('lidar_h_p95'))
