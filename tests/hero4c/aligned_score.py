"""Aligned re-score of the street checklist rows (round 5).
Render and photo come from the same solved camera (Cam_Match_geograph, rms 14.2 px), so ONE crop box
is applied to both images (the stock checks.py rows use different boxes per image because Cam_Street is not matched).
Usage: python3 tests/hero4c/aligned_score.py <render.png> [<render2.png> ...]"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import checks
from PIL import Image
REF = "refs/critic1/real_geograph.jpg"
ROWS = [  # boxes picked on the photo; hoarding starts ~y0.73, so crops stop above it
    {"element": "ground_floor_ashlar", "rule": "hf_excess", "box": [0.73, 0.60, 0.86, 0.72]},       # plain wall bay east of the arcade (+ shield)
    {"element": "ground_floor_ashlar_west", "rule": "hf_excess", "box": [0.06, 0.61, 0.29, 0.66]},  # band + voussoir zone over west arches
    {"element": "arcade", "rule": "arcade_quality", "box": [0.40, 0.60, 0.72, 0.73]},               # east arcade, 3 arches
]
ref = checks._open_rgb(REF)
out = {}
for rp in sys.argv[1:]:
    im = checks._open_rgb(rp).resize(ref.size, Image.Resampling.LANCZOS)
    res = {}
    for row in ROWS:
        st, d = checks.score_element(im, ref, {"rule": row["rule"], "render_crop": row["box"], "ref_crop": row["box"]})
        res[row["element"]] = {"status": st, "metric": d["metric"], "hf_render": round(d["render"]["hf"], 3), "hf_ref": round(d["ref"]["hf"], 3),
                               "edge_render": round(d["render"]["edge"], 4), "edge_ref": round(d["ref"]["edge"], 4)}
    out[os.path.basename(rp)] = res
print(json.dumps(out, indent=1))
