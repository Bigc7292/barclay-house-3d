import bpy, sys, json, math, numpy as np
sys.argv=[sys.argv[0]]; ns={'__name__':'camera_match'}; exec(open('/workspace/barclay/camera_match.py').read(), ns)
from mathutils import Vector
cam=bpy.data.objects["Cam_Street"]; W,H=1280,720
true=[cam.data.lens,*cam.rotation_euler,*cam.location]
pts=[[0,0,20.13],[0,0,0],[37.54,0,20.13],[37.54,0,0],[-0.4,26,20.13],[-0.4,26,0],[18.77,0,10]]
Xw=ns['_to_world']([{"xyz":p} for p in pts],"hero"); uv,_=ns['_project'](np.array(true),np.array([list(v) for v in Xw]),W,H)
init=[30,*ns['look_at_euler'](Vector(true[4:])+Vector((15,-20,5)),sum(Xw,Vector())/7),*(Vector(true[4:])+Vector((15,-20,5)))]
p,rms,_=ns['solve'](Xw,uv.tolist(),W,H,init)
print("SELFTEST true_lens",round(true[0],2),"got",round(p[0],2),"loc_err_m",round(float(np.linalg.norm(p[4:7]-np.array(true[4:7]))),3),"rms_px",round(rms,4))
