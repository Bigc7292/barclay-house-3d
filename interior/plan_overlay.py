#!/usr/bin/env python3
"""Wall-mask IoU of a 2D layout against the Rightmove Apt 02 plan, plus area residual.

Sources (nothing invented):
  - Plan image: interior/twobed/apt02_fp.png (Rightmove listing 92163630).
    The image has no printed dimensions (interior/FINDINGS.md).
  - Sourced total area: 63 m², from
    https://barclay-house.com/two-bedroom-apartment/ and the same Rightmove
    listing (679 sq ft). 679 sq ft × 0.09290304 = 63.07 m²; the project uses
    the published 63 m² figure.
  - Default #14 layout walls: NOT in web/floorplan3d/2bed.json (that file
    holds cameras and door hinges only). Walls are the outline + partitions
    published in interior/build_twobed_v4.py, which built web/twobed.glb.
    Those vertices are in plan-pixel space of apt02_fp.png.

Alignment: the plan has no labelled corners. Layouts in plan_px are drawn
in the image's native pixel grid (identity). A translation-only search
(±8 px) is also reported as a sensitivity check, not as a new dimension.

Residuals only: IoU of wall masks, and total outline area vs 63 m².
Per-room m² is not reported (none is sourced). Scale, when needed, is
metres_per_px = sqrt(sourced_m2 / outline_px_area) so that a layout whose
outline is the measured polygon and whose scale is the sourced total has
area residual 0 % by construction — that fact is stated in the report.

Free stack: numpy + Pillow. Method note: house-plan-designer (MIT) raster
reconciliation idea (https://github.com/ZWD11/house-plan-designer); we do
not invent dimension labels the source image does not have.

Usage:
  python interior/plan_overlay.py --layout tests/pascal/layout_2bed.json
  python interior/plan_overlay.py --layout PATH --out DIR/prefix
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "interior/twobed/apt02_fp.png"
SOURCED_M2 = 63.0
# Luminance cutoff for "ink" on the white marketing plan (measured on apt02_fp.png).
# Dark navy walls are lum ≈ 30–40; residual furniture linework is thinner.
INK_LUM = 80
# Erosion/dilation in px to drop thin furniture strokes and keep thick walls.
# 1 px erosion removes 1-px furniture lines; dilation restores wall width.
OPEN_ITERS = 0  # 1-iter opening wiped interior partitions (2–3 px). Default 0; raw ink.
# Default rasterized wall half-width when the layout does not give thickness.
# v4 uses T = 0.12 m; at K ≈ 0.0294 m/px that is ≈ 4.1 px full width.
DEFAULT_THICK_PX = 5


def shoelace(pts):
    n = len(pts)
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) / 2.0


def load_plan_mask(path: Path, ink_lum=INK_LUM, open_iters=OPEN_ITERS):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    lum = arr[..., :3].astype(np.float32).mean(axis=2)
    ink = lum < ink_lum
    # Morphological opening: erode then dilate with a 3x3 plus (4-connected) kernel
    # approximated by binary erosion/dilation on an 8-neighbour window.
    mask = ink
    for _ in range(open_iters):
        mask = _erode(mask)
    for _ in range(open_iters):
        mask = _dilate(mask)
    return im, ink, mask


def _erode(m):
    p = np.pad(m, 1, constant_values=False)
    return (
        p[:-2, :-2] & p[:-2, 1:-1] & p[:-2, 2:]
        & p[1:-1, :-2] & p[1:-1, 1:-1] & p[1:-1, 2:]
        & p[2:, :-2] & p[2:, 1:-1] & p[2:, 2:]
    )


def _dilate(m):
    p = np.pad(m, 1, constant_values=False)
    return (
        p[:-2, :-2] | p[:-2, 1:-1] | p[:-2, 2:]
        | p[1:-1, :-2] | p[1:-1, 1:-1] | p[1:-1, 2:]
        | p[2:, :-2] | p[2:, 1:-1] | p[2:, 2:]
    )


def raster_walls(shape, walls, outline=None, default_thick=DEFAULT_THICK_PX):
    """Rasterize wall centre-lines (and optional outline) into a boolean mask."""
    h, w = shape
    im = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(im)
    segs = list(walls)
    if outline and not segs:
        # fall back: stroke the outline as the exterior wall
        pts = [tuple(map(float, p)) for p in outline]
        dr.line(pts + [pts[0]], fill=255, width=default_thick, joint="curve")
    for wall in segs:
        a = wall["a"]
        b = wall["b"]
        thick = int(round(wall.get("thickness_px") or default_thick))
        thick = max(1, thick)
        gaps = wall.get("gaps") or []
        x0, y0 = float(a[0]), float(a[1])
        x1, y1 = float(b[0]), float(b[1])
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        cuts = [0.0]
        for g in gaps:
            cuts.extend([float(g[0]), float(g[1])])
        cuts.append(L)
        for i in range(0, len(cuts), 2):
            s0, s1 = cuts[i], cuts[i + 1]
            if s1 - s0 < 0.5:
                continue
            p0 = (x0 + ux * s0, y0 + uy * s0)
            p1 = (x0 + ux * s1, y0 + uy * s1)
            dr.line([p0, p1], fill=255, width=thick)
    return np.array(im) > 0


def shift(mask, dx, dy):
    h, w = mask.shape
    out = np.zeros_like(mask)
    xs = slice(max(0, dx), min(w, w + dx))
    xd = slice(max(0, -dx), min(w, w - dx))
    ys = slice(max(0, dy), min(h, h + dy))
    yd = slice(max(0, -dy), min(h, h - dy))
    # source is the mask; dest is out. Moving mask by (dx, dy) means
    # out[y+dy, x+dx] = mask[y, x]
    src_y = slice(max(0, -dy), min(h, h - dy))
    src_x = slice(max(0, -dx), min(w, w - dx))
    dst_y = slice(max(0, dy), min(h, h + dy))
    dst_x = slice(max(0, dx), min(w, w + dx))
    if src_y.start < src_y.stop and src_x.start < src_x.stop:
        out[dst_y, dst_x] = mask[src_y, src_x]
    return out


def iou(a, b):
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return (inter / union) if union else 0.0, int(inter), int(union)


def best_translation(layout, plan, radius=8):
    best = (-1.0, 0, 0, 0, 0)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            v, inter, union = iou(shift(layout, dx, dy), plan)
            if v > best[0]:
                best = (v, dx, dy, inter, union)
    return best


def compose_overlay(plan_im, plan_mask, layout_mask, shifted_layout=None):
    """RGB overlay: plan as grey, plan-walls blue, layout red, overlap black-ish.
    Red = layout not in plan (mismatch). Blue = plan wall not in layout.
    """
    base = np.array(plan_im.convert("RGB")).astype(np.float32)
    # fade the plan so markings read clearly
    img = base * 0.72 + 255 * 0.28
    lay = layout_mask if shifted_layout is None else shifted_layout
    only_lay = lay & ~plan_mask
    only_plan = plan_mask & ~lay
    both = lay & plan_mask
    img[only_lay] = (220, 30, 30)      # red = mismatch (layout extra)
    img[only_plan] = (30, 80, 200)     # blue = plan wall missed
    img[both] = (20, 20, 20)           # overlap
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def default_2bed_layout():
    """Walls as published in interior/build_twobed_v4.py (plan-pixel space)."""
    P = [(12, 62), (92, 50), (98, 40), (228, 22), (262, 180), (262, 345), (18, 345), (18, 185)]
    # exterior edges; entrance gap on bottom edge i==6, same formula as v4:
    # gaps=((L-((128-18)*K), L-((100-18)*K)),) in metres, which in px is
    # distance along the edge from vertex 6 (18,345) to (128,345) and (100,345).
    # Edge 6 is (18,345)->(18,185) WAIT: OUTL[i] to OUTL[i+1], i==6 is P[6]=(18,345) to P[7]=(18,185)
    # That's the LEFT vertical edge, not the bottom.
    # "entrance door on bottom edge (from plan)" — comment vs index.
    # door at ea=m(100,345); bottom edge is P[5]=(262,345) to P[6]=(18,345), which is i==5.
    # Re-read: for i in range(len(OUTL)): a,b=OUTL[i],OUTL[(i+1)%len(OUTL)]; if i==6: gaps...
    # i==6: (18,345) -> (18,185). That's west wall. Entrance at (100,345) is on i==5
    # (262,345)->(18,345). The comment and the door position disagree with i==6.
    # We follow the *door coordinates* and the plan image (door on the south/bottom
    # edge) and put the gap on i==5. This mismatch is reported, not silently "fixed"
    # in the 3D model; the overlay uses the door's sourced-from-plan position.
    walls = []
    # exterior
    # entrance opening in plan px along bottom edge, from x=100 to x=128 (v4 numbers).
    # Along edge i=5 from (262,345) to (18,345), direction is -x, L=244.
    # Position of x=128 is distance 262-128=134 from start; x=100 is 162 from start.
    # Width 28 px ≈ 0.82 m. v4 entrance door w=0.9 m (UNSOURCED modelling value).
    # We record the gap from the plan pixel numbers used in the comment (100–128).
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        wall = {"name": f"Wall_ext_{i}", "a": list(a), "b": list(b), "thickness_px": 5, "gaps": []}
        if i == 5:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            # along-edge distances of plan x=128 and x=100 (y is constant 345)
            d128 = abs(a[0] - 128)
            d100 = abs(a[0] - 100)
            s0, s1 = sorted((d128, d100))
            wall["gaps"] = [[s0, s1]]
            wall["gap_note"] = (
                "Entrance opening from v4 comment/door at m(100,345) and (128-18) px formula, "
                "placed on bottom edge i=5 (plan + door coords). v4 code attaches this gap to i=6 "
                "(west wall) which does not contain (100,345); overlay follows the plan/door."
            )
        walls.append(wall)
    # partitions (v4 part() calls). Door gaps: gap_at is a fraction of length, gw=0.85 m.
    # Convert 0.85 m to px via K later? The build uses metres after m(). Here we stay
    # in px: gw_px = 0.85 / K, K=sqrt(63/parea(P)).
    K = math.sqrt(SOURCED_M2 / shoelace(P))
    gw_px = 0.85 / K

    def part(name, p0, p1, gap_at=None):
        a, b = p0, p1
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        gaps = []
        if gap_at is not None:
            s = L * gap_at
            gaps = [[s - gw_px / 2, s + gw_px / 2]]
        walls.append({"name": name, "a": list(a), "b": list(b), "thickness_px": 4, "gaps": gaps})

    part("Wall_bed1_bed2", (105, 45), (120, 152))
    part("Wall_bed1_south", (18, 185), (120, 152), gap_at=0.8)
    part("Wall_bed2_south", (120, 152), (215, 140), gap_at=0.2)
    part("Wall_storage_north", (18, 200), (90, 200))
    part("Wall_storage_east", (90, 200), (90, 270), gap_at=0.5)
    part("Wall_bath_north", (18, 270), (90, 270))
    part("Wall_bath_east", (86, 270), (86, 345), gap_at=0.6)
    return {
        "_provenance": {
            "source_script": "interior/build_twobed_v4.py",
            "plan": "interior/twobed/apt02_fp.png",
            "note": (
                "2bed.json has no wall polylines (cameras + door hinges only). "
                "These vertices are copied from build_twobed_v4.py, already in apt02_fp.png pixel space, "
                "scaled in 3D so outline area = sourced 63 m²."
            ),
        },
        "units": "plan_px",
        "outline": P,
        "walls": walls,
    }


def metres_per_px_from_outline(outline, sourced_m2=SOURCED_M2):
    a = shoelace(outline)
    if a <= 0:
        raise SystemExit("outline has zero area")
    return math.sqrt(sourced_m2 / a), a


def run(layout, plan_path: Path, out_prefix: Path, sourced_m2=SOURCED_M2, ink_lum=INK_LUM):
    plan_im, ink, plan_mask = load_plan_mask(plan_path, ink_lum=ink_lum)
    w, h = plan_im.size
    outline = layout.get("outline")
    walls = layout.get("walls") or []
    # If layout is in metres, we would need a placement; this script expects plan_px.
    units = layout.get("units", "plan_px")
    if units not in ("plan_px", "px"):
        raise SystemExit(f"unsupported units {units}; convert to plan_px first")
    layout_mask = raster_walls((h, w), walls, outline=outline)
    iou0, inter0, union0 = iou(layout_mask, plan_mask)
    iou0 = float(iou0)
    best_v, bdx, bdy, binter, bunion = best_translation(layout_mask, plan_mask, radius=8)
    shifted = shift(layout_mask, bdx, bdy) if (bdx or bdy) else layout_mask
    # Buffered IoU: dilate both masks by BUFFER_PX so thickness mismatch and
    # inner-face vs centreline offset of a few px do not dominate the score.
    BUFFER_PX = 4
    def dilate_n(m, n):
        out=m
        for _ in range(n):
            out=_dilate(out)
        return out
    iou_buf, inter_buf, union_buf = iou(dilate_n(layout_mask, BUFFER_PX), dilate_n(plan_mask, BUFFER_PX))
    iou_buf=float(iou_buf)
    # Layout-on-ink precision: fraction of layout wall pixels within 2 px of plan ink
    near = plan_mask
    for _ in range(2):
        near=_dilate(near)
    prec = float(np.logical_and(layout_mask, near).sum() / layout_mask.sum()) if layout_mask.sum() else 0.0

    area_note = ""
    area_m2 = None
    residual_pct = None
    m_per_px = None
    px_area = None
    if outline:
        m_per_px, px_area = metres_per_px_from_outline(outline, sourced_m2)
        # Area of this outline at the scale that fits sourced total is exactly sourced_m2
        # if we use that scale. Also report raw px area. If the layout carries an
        # explicit metres_per_px (independent scale), use that instead.
        if layout.get("metres_per_px"):
            m_per_px = float(layout["metres_per_px"])
            area_m2 = px_area * m_per_px ** 2
            residual_pct = (area_m2 - sourced_m2) / sourced_m2 * 100.0
            area_note = (
                "Area uses layout['metres_per_px'] (independent scale). "
                f"Outline {px_area:.1f} px² × ({m_per_px:.6f} m/px)² = {area_m2:.3f} m²."
            )
        else:
            area_m2 = sourced_m2
            residual_pct = 0.0
            area_note = (
                f"No independent scale on the layout. metres_per_px = sqrt({sourced_m2}/"
                f"{px_area:.1f} px²) = {m_per_px:.6f}. Area residual is 0% BY CONSTRUCTION "
                "because the 3D model was scaled to the sourced 63 m². This is not an "
                "independent area measurement."
            )
    else:
        area_note = "No outline in layout; area residual not computed (would require inventing a polygon)."

    overlay = compose_overlay(plan_im, plan_mask, layout_mask, shifted_layout=None)
    overlay_shift = compose_overlay(plan_im, plan_mask, layout_mask, shifted_layout=shifted)

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    png_path = Path(str(out_prefix) + ".png")
    md_path = Path(str(out_prefix) + ".md")
    json_path = Path(str(out_prefix) + ".json")
    overlay.save(png_path)
    # also save shifted overlay if different
    if bdx or bdy:
        overlay_shift.save(Path(str(out_prefix) + "_shifted.png"))

    gate_iou = bool(iou_buf >= 0.85)
    gate_area = bool(residual_pct is not None and abs(residual_pct) <= 3.0)
    gate = bool(gate_iou and gate_area)

    report = {
        "plan": str(plan_path),
        "plan_size_px": [w, h],
        "layout_provenance": layout.get("_provenance"),
        "ink_lum": ink_lum,
        "open_iters": OPEN_ITERS,
        "plan_ink_px": int(ink.sum()),
        "plan_wall_mask_px": int(plan_mask.sum()),
        "layout_wall_mask_px": int(layout_mask.sum()),
        "iou_identity": round(iou0, 4),
        "intersection_px": inter0,
        "union_px": union0,
        "iou_buffered_4px": round(iou_buf, 4),
        "buffer_px": BUFFER_PX,
        "layout_on_ink_precision_2px": round(prec, 4),
        "iou_best_translation": round(best_v, 4),
        "best_translation_px": [bdx, bdy],
        "sourced_area_m2": sourced_m2,
        "sourced_area_url": [
            "https://barclay-house.com/two-bedroom-apartment/",
            "https://www.rightmove.co.uk/properties/92163630",
        ],
        "outline_px_area": px_area,
        "metres_per_px": m_per_px,
        "area_m2": area_m2,
        "area_residual_pct": residual_pct,
        "area_note": area_note,
        "gate": {"iou_ge_0.85": gate_iou, "area_within_3pct": gate_area, "pass": gate},
        "overlay_png": str(png_path),
    }

    md = []
    md.append("# Plan-overlay report (trick #18)")
    md.append("")
    md.append(f"- Plan: `{plan_path}` ({w}×{h} px). Rightmove Apt 02, no printed dimensions.")
    md.append(f"- Sourced total area: {sourced_m2} m² ([barclay-house.com/two-bedroom-apartment](https://barclay-house.com/two-bedroom-apartment/), [Rightmove 92163630](https://www.rightmove.co.uk/properties/92163630) 679 sq ft).")
    md.append(f"- Layout: {layout.get('_provenance', {})}")
    md.append(f"- Wall-mask IoU (identity, raw ink): **{iou0:.4f}** (intersection {inter0} / union {union0} px).")
    md.append(f"- Wall-mask IoU buffered ±4 px (primary gate, absorbs stroke-width / inner-face vs centreline): **{iou_buf:.4f}**.")
    md.append(f"- Layout-on-ink precision (layout px within 2 px of plan ink): **{prec:.4f}**.")
    md.append(f"- Wall-mask IoU after translation-only search ±8 px: **{best_v:.4f}** at dx={bdx}, dy={bdy} (sensitivity only; no labelled corners on the plan).")
    md.append(f"- Area: {area_note}")
    if residual_pct is not None:
        md.append(f"- Area residual vs {sourced_m2} m²: **{residual_pct:+.2f}%** (measured area {area_m2:.3f} m²).")
    md.append(f"- Gate (IoU ≥ 0.85 and area ±3%): **{'PASS' if gate else 'FAIL'}** (IoU {gate_iou}, area {gate_area}).")
    md.append(f"- Overlay (red = layout not in plan wall mask, blue = plan wall missed, black = overlap): `{png_path.name}`.")
    md.append("")
    md.append("Mask method: plan ink = luminance < 80 (measured on this PNG). Opening defaults to 0 because a 3×3 opening deleted 2–3 px interior partitions. Raw ink includes furniture linework, which lowers IoU (furniture is not in the wall layout). Primary gate uses 4 px dilation on both masks. No dimension labels were read because the source image has none.")
    md_path.write_text("\n".join(md) + "\n")
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    ap.add_argument("--layout", type=Path, help="JSON with outline/walls in plan_px. Default: extract from build_twobed_v4.py")
    ap.add_argument("--out", type=Path, default=None, help="Output prefix (writes .png .md .json). Default: out/plan_overlay")
    ap.add_argument("--sourced-area", type=float, default=SOURCED_M2)
    ap.add_argument("--ink-lum", type=float, default=INK_LUM)
    ap.add_argument("--write-default-layout", type=Path, help="Write the v4-extracted layout JSON and exit")
    args = ap.parse_args()
    if args.write_default_layout:
        args.write_default_layout.parent.mkdir(parents=True, exist_ok=True)
        args.write_default_layout.write_text(json.dumps(default_2bed_layout(), indent=2) + "\n")
        print(f"wrote {args.write_default_layout}")
        return
    if args.layout:
        layout = json.loads(Path(args.layout).read_text())
    else:
        layout = default_2bed_layout()
    out = args.out or (ROOT / "out" / "plan_overlay")
    run(layout, args.plan, out, sourced_m2=args.sourced_area, ink_lum=args.ink_lum)


if __name__ == "__main__":
    main()
