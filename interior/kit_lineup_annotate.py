#!/usr/bin/env python3
"""Annotate kit_lineup raw strips (Pillow). Called after kit_lineup.py in Blender."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "assets", "_lineup_raw", "meta.json")
path = sys.argv[1] if len(sys.argv) > 1 else META
data = json.load(open(path))

def font(name, size):
    p = f"/usr/share/fonts/truetype/dejavu/{name}.ttf"
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default()

FONT = font("DejaVuSans", 18)
FONT_S = font("DejaVuSans", 14)
FONT_T = font("DejaVuSans-Bold", 20)
FONT_H = font("DejaVuSans-Bold", 22)

def annotate(raw, recs, span, ortho_w, title, out):
    im = Image.open(raw).convert("RGB")
    W, H = im.size
    cam_x = span / 2
    def x_to_px(x):
        return int(round((x - (cam_x - ortho_w / 2)) / ortho_w * W))
    band = 110 if title else 80
    canvas = Image.new("RGB", (W, H + band), (46, 47, 50))
    canvas.paste(im, (0, 0))
    draw = ImageDraw.Draw(canvas)
    if title:
        draw.text((16, H + 6), title, fill=(230, 230, 228), font=FONT_T)
    def tw(text, f):
        try:
            return draw.textlength(text, font=f)
        except Exception:
            return len(text) * 7
    placed = []
    for rec in recs:
        cx = x_to_px(rec["x"])
        label, dim = rec["label"], f"{rec['w']:.2f}×{rec['d']:.2f}×{rec['h']:.2f} m"
        y0 = H + (30 if title else 8)
        # Stagger if this label would overlap the previous one.
        if placed:
            prev_cx, prev_w = placed[-1]
            if abs(cx - prev_cx) < (prev_w + tw(label, FONT)) / 2 + 8:
                y0 += 22
        placed.append((cx, tw(label, FONT)))
        draw.text((cx - tw(label, FONT) / 2, y0), label, fill=(235, 235, 232), font=FONT)
        draw.text((cx - tw(dim, FONT_S) / 2, y0 + 20), dim, fill=(180, 180, 176), font=FONT_S)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    canvas.save(out)
    print("ANNOTATED", out, canvas.size)
    return canvas

anns = []
for item in data["meta"]:
    im = annotate(**item)
    anns.append((item, im))

# overall stack: last two records are overall_a / overall_b
a_path = data["meta"][-2]["out"]
b_path = data["meta"][-1]["out"]
ia, ib = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
W = max(ia.size[0], ib.size[0])
def pad(im, W):
    if im.size[0] == W:
        return im
    c = Image.new("RGB", (W, im.size[1]), (46, 47, 50))
    c.paste(im, ((W - im.size[0]) // 2, 0))
    return c
ia, ib = pad(ia, W), pad(ib, W)
header_h = 44
out = Image.new("RGB", (W, header_h + ia.size[1] + ib.size[1] + 8), (46, 47, 50))
draw = ImageDraw.Draw(out)
draw.text((20, 10), "Barclay House Two Bed  ·  CC0 furniture kit  ·  real-world metres, 1 m bar",
          fill=(235, 235, 232), font=FONT_H)
out.paste(ia, (0, header_h))
out.paste(ib, (0, header_h + ia.size[1] + 8))
overall = data["overall"]
out.save(overall)
print("OVERALL", overall, out.size)
