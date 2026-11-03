"""ref_check.py - render-vs-reference check (teardown review rule 1: build against a reference, compare frame by frame).
System python3 + Pillow. Writes <render>_check.png: [reference | render | 50% blend | edges: ref=red, render=cyan]
and prints an edge-agreement score (0..1, higher = silhouettes/window lines line up better).
  python3 ref_check.py tests/match_render.png refs/plans_p1_cgi.png
Use after camera_match.py (same camera/resolution), and re-run after every model change: the score must not drop."""
import sys, warnings; warnings.filterwarnings("ignore")
from PIL import Image, ImageChops, ImageFilter, ImageOps
def edges(im, thr=40):
    e = ImageOps.grayscale(im).filter(ImageFilter.GaussianBlur(1)).filter(ImageFilter.FIND_EDGES)
    return e.point(lambda v: 255 if v > thr else 0)
def check(render, ref, out=None):
    a = Image.open(render).convert("RGB"); b = Image.open(ref).convert("RGB").resize(a.size)
    ea, eb = edges(a), edges(b)
    ea_d, eb_d = ea.filter(ImageFilter.MaxFilter(5)), eb.filter(ImageFilter.MaxFilter(5))   # 2 px tolerance
    hit = lambda x, y: sum(ImageChops.multiply(x, y).point(lambda v: 1 if v else 0).getdata())
    na, nb = max(1, sum(ea.point(lambda v: 1 if v else 0).getdata())), max(1, sum(eb.point(lambda v: 1 if v else 0).getdata()))
    precision, recall = hit(ea, eb_d) / na, hit(eb, ea_d) / nb
    f1 = 0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    W, H = a.size; sheet = Image.new("RGB", (W * 4, H))
    ov = Image.merge("RGB", (eb, ea, ea))
    for i, im in enumerate((b, a, Image.blend(a, b, 0.5), ov)): sheet.paste(im, (i * W, 0))
    out = out or render.rsplit(".", 1)[0] + "_check.png"; sheet.save(out)
    print(f"REF_CHECK edge_F1={f1:.3f} precision={precision:.3f} recall={recall:.3f} -> {out}"); return f1
if __name__ == "__main__": check(*sys.argv[1:4])
