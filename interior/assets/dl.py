import json,urllib.request,os,sys
import urllib.request as U
O=U.build_opener();O.addheaders=[("User-Agent","barclay-viewer/1.0")];U.install_opener(O)
for a in sys.argv[1:]:
    f=json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{a}",headers={"User-Agent":"barclay-viewer/1.0"})))
    g=f["gltf"]["1k"]["gltf"]; os.makedirs(a,exist_ok=True)
    urllib.request.urlretrieve(g["url"],f"{a}/{a}.gltf")
    for p,v in g.get("include",{}).items():
        os.makedirs(os.path.dirname(f"{a}/{p}") or a,exist_ok=True); urllib.request.urlretrieve(v["url"],f"{a}/{p}")
    print("ok",a)
