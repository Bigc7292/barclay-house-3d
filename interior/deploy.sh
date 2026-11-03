#!/bin/bash
# Re-export Two Bed + re-stage site in /workspace/barclay/web. Then the agent deploys via the Vercel connector
# (user-Vercel create_deployment, files = web/manifest.json, skipAutoDetectionConfirmation=1; public URL https://barclay-house-viewer.vercel.app, project barclay-house-viewer, target production) using files from web/manifest.json.
set -e
cd /workspace/barclay/interior && ~/bvenv/bin/python build_twobed.py >/dev/null 2>&1
W=/workspace/barclay/web; cp live/twobed.glb live/latest.png twobed/apt02_fp.png $W/
cp $W/ext_opt2.glb $W/exterior.glb  # 4.25 MB web version (connector limit 8 MB base64/file, 4 files/call)
cd $W && python3 - <<'P'
import json,base64
fs=["index.html","twobed.glb","exterior.glb","apt02_fp.png"]
out=[]
for f in fs:
    d=open(f,"rb").read()
    if f.endswith(".html"): out.append({"file":f,"data":d.decode(),"encoding":"utf-8"})
    else:
        open(f+".b64","w").write(base64.b64encode(d).decode()); out.append({"file":f,"data":"$file:/workspace/barclay/web/"+f+".b64","encoding":"base64"})
json.dump(out,open("manifest.json","w"),indent=1); print("staged",[ (f) for f in fs])
P
# Deploy steps (agent, via user-Vercel connector): model-viewer.min.js (pinned 4.0.0) and meshopt_decoder.js (0.22.0) are
# self-hosted; upload them with upload_file (sha1+size) then create_deployment project=barclay-house-viewer target=production
# with index.html, twobed.glb, exterior.glb, apt02_fp.png via $file and the two .js as sha refs. Verify: node /tmp/pw/t.mjs URL a.png b.png
