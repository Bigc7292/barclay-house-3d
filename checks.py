#!/usr/bin/env python3
"""checks.py — per-element reference-checklist gate (trick #15).

Hybrid with ref_check.py: this scores named facade elements yes/partial/no
from numpy/Pillow pixel stats on masked crops; then optionally runs the
existing aggregate edge F1.

Usage:
  python3 checks.py --cam street
  python3 checks.py --cam hero --cam street --cam viaduct
  python3 checks.py --cam street --render tests/r3_street.png
  python3 checks.py --all

Zero cost: stdlib + numpy + Pillow only. Method only from the cutaway post;
the unverified cutaway skill is NOT used. mcp-for-blender is MIT (bridge
reference only).
"""
from __future__ import annotations
import argparse, json, os, sys, time, warnings
warnings.filterwarnings("ignore")

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
YES, PARTIAL, NO = "yes", "partial", "no"

# Thresholds from the brief: ≥80% of ref → yes; 60–80% → partial; <60% → no.
RATIO_YES, RATIO_PARTIAL = 0.80, 0.60
# Absolute salmon wash (fraction of crop). Tuned so R3 street parapet fails,
# real brick refs pass, and the open R4 viaduct sunlit tops stay partial/no.
SALMON_YES, SALMON_PARTIAL = 0.05, 0.15


def _open_rgb(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def _crop_frac(im: Image.Image, box):
    """box = [x0,y0,x1,y1] in 0..1 fractions of the image."""
    w, h = im.size
    x0, y0, x1, y1 = box
    return im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))


def _hsv_stats(arr: np.ndarray):
    """arr HxWx3 float/uint8 RGB → dict of pixel stats (no OpenCV)."""
    from PIL import ImageFilter, ImageOps  # local; Pillow already imported
    a = arr.astype(np.float32)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    v = mx / 255.0
    sat = np.where(mx == 0, 0.0, (mx - mn) / np.maximum(mx, 1.0))
    d = np.maximum(mx - mn, 1e-6)
    hue = np.zeros_like(mx)
    m = mx == r
    hue[m] = (60.0 * ((g - b) / d) % 360.0)[m]
    m = mx == g
    hue[m] = (60.0 * ((b - r) / d) + 120.0)[m]
    m = mx == b
    hue[m] = (60.0 * ((r - g) / d) + 240.0)[m]
    # Edge density: share of FIND_EDGES pixels (same family as ref_check.py).
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    e = ImageOps.grayscale(im).filter(ImageFilter.GaussianBlur(1)).filter(
        ImageFilter.FIND_EDGES
    )
    edge = float((np.asarray(e) > 40).mean())
    # High-frequency excess: edge after strong blur. Rubble/noise keeps
    # high HF; smooth ashlar + carved mid-scale detail drops more.
    e_c = ImageOps.grayscale(im.filter(ImageFilter.GaussianBlur(3))).filter(
        ImageFilter.FIND_EDGES
    )
    edge_c = float((np.asarray(e_c) > 40).mean())
    hf = edge / max(edge_c, 1e-6)
    dark = float((v < 0.35).mean())
    # Salmon / washed orange-pink brick under double sun (R3/R4 critic):
    # bright, red>blue by a margin, hue in the orange band.
    brickish = (r > g) & (g >= b * 0.85) & (r > 60)
    salmon = brickish & (v > 0.45) & (hue >= 5) & (hue <= 50) & ((r - b) > 40)
    dark_brick = brickish & (v < 0.45) & (hue >= 0) & (hue <= 40)
    return {
        "mean_rgb": (float(r.mean()), float(g.mean()), float(b.mean())),
        "mean_v": float(v.mean()),
        "mean_sat": float(sat.mean()),
        "median_hue": float(np.median(hue)),
        "dark_share": dark,
        "edge": float(edge),
        "hf": float(hf),
        "luma_std": float(v.std()),
        "salmon_frac": float(salmon.mean()),
        "dark_brick_frac": float(dark_brick.mean()),
    }


def _ratio_status(render_val: float, ref_val: float, higher_is_better=True):
    """Map render/ref ratio onto yes/partial/no. Protect against tiny ref."""
    if ref_val <= 1e-9:
        # No signal in ref: fall back to absolute render value presence.
        if higher_is_better:
            return (YES, 1.0) if render_val > 0 else (NO, 0.0)
        return (YES, 1.0) if render_val <= 1e-9 else (NO, 0.0)
    ratio = render_val / ref_val
    if not higher_is_better:
        # Lower-is-better: invert (e.g. unwanted wash). Cap for display.
        if render_val <= ref_val * 1.25:
            return YES, min(ratio, 9.99)
        if render_val <= ref_val * 2.0:
            return PARTIAL, min(ratio, 9.99)
        return NO, min(ratio, 9.99)
    if ratio >= RATIO_YES:
        return YES, ratio
    if ratio >= RATIO_PARTIAL:
        return PARTIAL, ratio
    return NO, ratio


def _salmon_status(frac: float):
    if frac <= SALMON_YES:
        return YES, frac
    if frac <= SALMON_PARTIAL:
        return PARTIAL, frac
    return NO, frac


def _common_size(a: Image.Image, b: Image.Image, max_edge: int = 384):
    """Resize both crops to the same modest size so upscaling a tiny ref
    does not wipe its edges (which falsely inflates render/ref ratios)."""
    # Target: min of the two long-edges, capped at max_edge.
    la = max(a.size)
    lb = max(b.size)
    target = max(64, min(la, lb, max_edge))
    def fit(im):
        w, h = im.size
        scale = target / max(w, h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return im.resize((nw, nh), Image.Resampling.BILINEAR)
    return fit(a), fit(b)


def score_element(render_im: Image.Image, ref_im: Image.Image, row: dict):
    """Score one checklist row. Returns (status, detail_dict)."""
    r_crop = _crop_frac(render_im, row["render_crop"])
    f_crop = _crop_frac(ref_im, row["ref_crop"])
    r_crop, f_crop = _common_size(r_crop, f_crop)
    rs = _hsv_stats(np.asarray(r_crop))
    fs = _hsv_stats(np.asarray(f_crop))
    rule = row["rule"]
    detail = {"render": rs, "ref": fs, "rule": rule}

    if rule == "edge_ratio":
        # Facade detail: ashlar joints, arcade voussoirs, glazing bars, shields.
        st, ratio = _ratio_status(rs["edge"], fs["edge"], higher_is_better=True)
        detail["score"] = ratio
        detail["metric"] = f"edge {rs['edge']:.4f}/{fs['edge']:.4f}={ratio:.2f}"
    elif rule == "dark_ratio":
        st, ratio = _ratio_status(rs["dark_share"], fs["dark_share"], True)
        detail["score"] = ratio
        detail["metric"] = (
            f"dark {rs['dark_share']:.3f}/{fs['dark_share']:.3f}={ratio:.2f}"
        )
    elif rule == "max_salmon":
        st, frac = _salmon_status(rs["salmon_frac"])
        detail["score"] = frac
        detail["metric"] = (
            f"salmon_frac={frac:.3f} (ref={fs['salmon_frac']:.3f}) "
            f"dark_brick={rs['dark_brick_frac']:.3f}/{fs['dark_brick_frac']:.3f}"
        )
    elif rule == "hf_excess":
        # Lower HF-excess vs ref is better (punish rubble/noise tiling).
        # yes ≤1.20×, partial ≤1.45×, no above — tuned on R4 ashlar crops.
        ratio = rs["hf"] / max(fs["hf"], 1e-6)
        detail["score"] = ratio
        detail["metric"] = f"hf {rs['hf']:.2f}/{fs['hf']:.2f}={ratio:.2f}"
        if ratio <= 1.20:
            st = YES
        elif ratio <= 1.45:
            st = PARTIAL
        else:
            st = NO
    elif rule == "arcade_quality":
        # Need enough edge structure AND not rubble-noisy.
        st_e, re = _ratio_status(rs["edge"], fs["edge"], True)
        ratio_hf = rs["hf"] / max(fs["hf"], 1e-6)
        if ratio_hf <= 1.20:
            st_h = YES
        elif ratio_hf <= 1.45:
            st_h = PARTIAL
        else:
            st_h = NO
        order = {YES: 2, PARTIAL: 1, NO: 0}
        st = st_e if order[st_e] <= order[st_h] else st_h
        detail["score"] = min(re, 1.0 / max(ratio_hf, 1e-6))
        detail["metric"] = f"edge={re:.2f} hf_excess={ratio_hf:.2f}"
    elif rule == "relief_detail":
        # Carved shields: enough edge vs ref, and HF not noise-dominated.
        st_e, re = _ratio_status(rs["edge"], fs["edge"], True)
        ratio_hf = rs["hf"] / max(fs["hf"], 1e-6)
        if ratio_hf <= 1.35:
            st_h = YES
        elif ratio_hf <= 1.60:
            st_h = PARTIAL
        else:
            st_h = NO
        order = {YES: 2, PARTIAL: 1, NO: 0}
        st = st_e if order[st_e] <= order[st_h] else st_h
        detail["score"] = re
        detail["metric"] = f"edge={re:.2f} hf_excess={ratio_hf:.2f}"
    elif rule == "hue_proximity":
        # Circular hue distance; yes if within 30°, partial 60°, else no.
        dh = abs(rs["median_hue"] - fs["median_hue"])
        dh = min(dh, 360.0 - dh)
        detail["score"] = dh
        detail["metric"] = f"|Δhue|={dh:.1f}° (r={rs['median_hue']:.0f} f={fs['median_hue']:.0f})"
        if dh <= 30:
            st = YES
        elif dh <= 60:
            st = PARTIAL
        else:
            st = NO
    elif rule == "hybrid_edge_dark":
        # Require both edge and dark-share ratios (arcade depth + glazing).
        st_e, re = _ratio_status(rs["edge"], fs["edge"], True)
        st_d, rd = _ratio_status(rs["dark_share"], fs["dark_share"], True)
        detail["score"] = min(re, rd)
        detail["metric"] = f"edge={re:.2f} dark={rd:.2f}"
        order = {YES: 2, PARTIAL: 1, NO: 0}
        st = st_e if order[st_e] <= order[st_d] else st_d
    else:
        raise ValueError(f"unknown rule: {rule}")

    detail["status"] = st
    return st, detail


def gate_verdict(statuses):
    """Gate = no 'no' rows and ≤2 'partial'."""
    n_no = sum(1 for s in statuses if s == NO)
    n_partial = sum(1 for s in statuses if s == PARTIAL)
    ok = n_no == 0 and n_partial <= 2
    return ok, n_no, n_partial


def run_ref_check(render_path: str, ref_path: str, out_path: str | None, max_w: int = 1280):
    """Hybrid call into existing ref_check.py (aggregate edge F1).

    Downscale to max_w first so the gate stays under the <30 s budget on 4K.
    """
    sys.path.insert(0, ROOT)
    import ref_check  # noqa: WPS433
    import tempfile

    def down(path):
        im = Image.open(path).convert("RGB")
        if im.size[0] <= max_w:
            return path, None
        nh = int(im.size[1] * (max_w / im.size[0]))
        im = im.resize((max_w, nh), Image.Resampling.BILINEAR)
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        im.save(tmp)
        return tmp, tmp

    r2, t1 = down(render_path)
    f2, t2 = down(ref_path)
    try:
        return ref_check.check(r2, f2, out_path)
    finally:
        for t in (t1, t2):
            if t and os.path.exists(t):
                os.unlink(t)


def load_checklist(cam: str) -> dict:
    path = os.path.join(ROOT, "refs", f"checklist_{cam}.json")
    with open(path) as f:
        return json.load(f)


def resolve_path(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def run_camera(cam: str, render_override: str | None = None, skip_ref_check: bool = False):
    spec = load_checklist(cam)
    render_path = resolve_path(render_override or spec["render"])
    ref_path = resolve_path(spec["ref"])
    if not os.path.exists(render_path):
        raise FileNotFoundError(render_path)
    if not os.path.exists(ref_path):
        raise FileNotFoundError(ref_path)

    render_im = _open_rgb(render_path)
    ref_im = _open_rgb(ref_path)

    rows_out = []
    statuses = []
    for row in spec["elements"]:
        st, detail = score_element(render_im, ref_im, row)
        statuses.append(st)
        rows_out.append(
            {
                "element": row["element"],
                "rule": row["rule"],
                "status": st,
                "metric": detail["metric"],
                "critic_note": row.get("critic_note", ""),
                "source": row.get("source", ""),
            }
        )

    ok, n_no, n_partial = gate_verdict(statuses)
    f1 = None
    if not skip_ref_check:
        out_sheet = os.path.join(ROOT, "out", f"checklist_{cam}_refcheck.png")
        os.makedirs(os.path.dirname(out_sheet), exist_ok=True)
        try:
            f1 = run_ref_check(render_path, ref_path, out_sheet)
        except Exception as exc:  # keep checklist usable even if sheet fails
            f1 = None
            print(f"WARN ref_check failed: {exc}", file=sys.stderr)

    # Markdown report
    lines = [
        f"# Checklist gate — {cam}",
        f"Render: `{os.path.relpath(render_path, ROOT)}`",
        f"Ref: `{os.path.relpath(ref_path, ROOT)}`",
        f"Gate: {'PASS' if ok else 'FAIL'} (no={n_no}, partial={n_partial}; "
        f"need no 'no' and ≤2 'partial')",
    ]
    if f1 is not None:
        lines.append(f"Hybrid ref_check edge_F1={f1:.3f}")
    lines += ["", "| element | status | metric | critic note |",
              "|---|---|---|---|"]
    for r in rows_out:
        lines.append(
            f"| {r['element']} | **{r['status']}** | {r['metric']} | {r['critic_note']} |"
        )
    lines.append("")
    report = "\n".join(lines) + "\n"
    out_md = os.path.join(ROOT, "out", f"checklist_{cam}.md")
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w") as f:
        f.write(report)

    print(report)
    return {
        "cam": cam,
        "gate_pass": ok,
        "n_no": n_no,
        "n_partial": n_partial,
        "rows": rows_out,
        "ref_check_f1": f1,
        "report": out_md,
    }


def main(argv=None):
    t0 = time.time()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cam", action="append", dest="cams",
                    help="Camera id (street, hero, viaduct). Repeatable.")
    ap.add_argument("--all", action="store_true", help="Run street+hero+viaduct")
    ap.add_argument("--render", default=None,
                    help="Override render path (for known-bad tests)")
    ap.add_argument("--skip-ref-check", action="store_true")
    args = ap.parse_args(argv)
    cams = args.cams or []
    if args.all:
        cams = ["street", "hero", "viaduct"]
    if not cams:
        ap.error("pass --cam or --all")

    results = []
    for cam in cams:
        results.append(run_camera(cam, args.render, args.skip_ref_check))

    elapsed = time.time() - t0
    any_fail = any(not r["gate_pass"] for r in results)
    print(f"ELAPSED {elapsed:.2f}s  OVERALL_GATE={'FAIL' if any_fail else 'PASS'}")
    # Non-zero exit if any camera fails the gate (useful in CI / validate).
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
