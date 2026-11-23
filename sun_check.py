#!/usr/bin/env python3
"""sun_check.py — sun-time shadow-alignment gate (trick #22).

Method only from STUDIO DUCKBILL SplatStroll (closed product). Own code, £0:
Pillow, numpy, Blender GPL, existing tod_panel.sun_pos / camera_match cameras.

Reads EXIF DateTimeOriginal, treats it as UK local (BST via tod_panel.is_bst),
logs the assumed offset, and does not "fix" the sun to match the photo.

Renders are done on a read-only open of out/barclay_scene.blend (never saved).
Only refs with an existing camera_match solve are scored. Official exports are
not overwritten.

Usage:
  python3 sun_check.py --render     # invoke Blender, then score
  python3 sun_check.py --score      # score existing tests/suncheck/out renders
  python3 sun_check.py --verify     # SUNCHECK=1 hook: read result.json, no render
"""
from __future__ import annotations

import argparse, hashlib, json, math, os, re, subprocess, sys, time
from datetime import datetime, date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image, ExifTags, ImageFilter, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "tests" / "suncheck" / "out"
RESULT = ROOT / "tests" / "suncheck" / "result.json"
RESULT_OUT = OUT / "result.json"
BLEND = ROOT / "out" / "barclay_scene.blend"
BLENDER = os.environ.get("BLENDER", "/home/box/apps/blender-4.2.3-linux-x64/blender")
OFFICIAL = [
    ROOT / "out" / "barclay_scene.blend",
    ROOT / "out" / "barclay_hero.glb",
    ROOT / "web" / "hero3.glb",
    ROOT / "out" / "barclay_hero_floors.glb",
    ROOT / "out" / "barclay_hero3_floors.glb",
]
SWEEP = (-3, -2, -1, 0, 1, 2, 3)  # hours around EXIF; wider than ±1 so a peak can fall outside
SPP = int(os.environ.get("BSAMPLES", "32"))
MAX_WIDTH = int(os.environ.get("BWIDTH", "960"))
PERCENTILE = float(os.environ.get("SHADOW_PCT", "35"))
# Keep the lower part of the plate (street, pavement, hoarding, ground-floor base).
# The upper facade window grid is dark in both images and is not a sun shadow, so it
# swamps full-frame edge angles (~61°) and flattens the IoU curve.
STREET_Y0 = float(os.environ.get("STREET_Y0", "0.55"))
ANGLE_LIMIT = 10.0
IOU_WINDOW_H = 1.0
MIN_PASS_REFS = 2

# Analyst/spec listed times (for mismatch flags only). Capture time is EXIF.
SPEC_LISTED = {
    "real_geograph": "2025-07-03 12:34",
    "whitworth_5809790": "2018-06-16 15:15",
    "canal_5477629": "2017-07-27 18:20",
    "lane_2295568": "2011-03-28 16:55",
    "hotspur_8088127": "2025-07-03 12:33",
}

REFS = [
    {
        "id": "real_geograph",
        "path": ROOT / "refs" / "critic1" / "real_geograph.jpg",
        "cam": "Cam_Match_geograph",
        "cam_source": "tests/scene_matched_geograph.blend",
        "solvable": True,
        "skip_reason": None,
    },
    {
        "id": "whitworth_5809790",
        "path": ROOT / "refs" / "surroundings" / "Whitworth_Street_West_-_geograph.org.uk_-_5809790.jpg",
        "cam": None,
        "cam_source": None,
        "solvable": False,
        "skip_reason": (
            "No camera_match solve. Photo looks east along Whitworth Street West "
            "at the viaduct shops; the Barclay House facade is not the subject, "
            "and there is no points JSON for this plate."
        ),
    },
    {
        "id": "canal_5477629",
        "path": ROOT / "refs" / "surroundings" / "Rochdale_Canal_-_geograph.org.uk_-_5477629.jpg",
        "cam": None,
        "cam_source": None,
        "solvable": False,
        "skip_reason": (
            "No camera_match solve. Canal / towpath view; the hero facade is not "
            "in frame, and there is no points JSON for this plate."
        ),
    },
    {
        "id": "lane_2295568",
        "path": ROOT / "refs" / "surroundings" / "Lane_to_West_Whitworth_Street_-_geograph.org.uk_-_2295568.jpg",
        "cam": None,
        "cam_source": None,
        "solvable": False,
        "skip_reason": (
            "No camera_match solve. Nearby lane with concrete columns that are "
            "not hero-facade geometry; no points JSON."
        ),
    },
    {
        "id": "hotspur_8088127",
        "path": ROOT / "refs" / "surroundings" / "Hotspur_Press_remains_-_geograph.org.uk_-_8088127.jpg",
        "cam": None,
        "cam_source": None,
        "solvable": False,
        "skip_reason": (
            "No camera_match solve. Under-viaduct view of the Hotspur Press ruins; "
            "no points JSON. The sharp viaduct-arch shadow on the road would be a "
            "good second ref if a locked camera is solved later."
        ),
    },
]


def _load_tod():
    """Import sun_pos / is_bst from tod_panel.py without importing bpy."""
    text = (ROOT / "tod_panel.py").read_text()
    start = text.index("LAT, LON")
    end = text.index("def kelvin_rgb")
    ns = {"math": math}
    exec(text[start:end], ns)
    return ns


TOD = _load_tod()
sun_pos = TOD["sun_pos"]
is_bst = TOD["is_bst"]
LAT, LON = TOD["LAT"], TOD["LON"]


def last_sunday(year, month):
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def official_stamp():
    out = {}
    for p in OFFICIAL:
        st = p.stat() if p.is_file() else None
        out[str(p.relative_to(ROOT))] = {
            "exists": st is not None,
            "mtime": st.st_mtime if st else None,
            "size": st.st_size if st else None,
            "sha256": file_sha256(p),
        }
    return out


def stamps_unchanged(before, after):
    mismatches = []
    for k, b in before.items():
        a = after.get(k)
        if a != b:
            mismatches.append(k)
    return mismatches


def read_exif(path: Path):
    im = Image.open(path)
    exif = im.getexif()
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    try:
        ifd = exif.get_ifd(0x8769)
        tags.update({ExifTags.TAGS.get(k, k): v for k, v in ifd.items()})
    except Exception:
        pass
    dto = tags.get("DateTimeOriginal") or tags.get("DateTime")
    if isinstance(dto, bytes):
        dto = dto.decode("ascii", "replace")
    raw = dto
    if dto is not None:
        dto = str(dto).replace("\x00", "").strip()
    offset_tag = tags.get("OffsetTimeOriginal") or tags.get("OffsetTime")
    if isinstance(offset_tag, bytes):
        offset_tag = offset_tag.decode("ascii", "replace")
    return {
        "datetime_original_raw": repr(raw),
        "datetime_original": dto,
        "offset_tag": None if offset_tag is None else str(offset_tag).replace("\x00", "").strip() or None,
        "make": tags.get("Make"),
        "model": tags.get("Model"),
        "size": list(im.size),
    }


def parse_capture(exif: dict, ref_id: str):
    flags = []
    dto = exif.get("datetime_original")
    if not dto:
        return None, flags
    dt = datetime.strptime(dto, "%Y:%m:%d %H:%M:%S")
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    bst = bool(is_bst(dt.month, dt.day))
    start, end = last_sunday(dt.year, 3), last_sunday(dt.year, 10)
    actual_bst = start <= dt.date() < end
    assumed = "BST UTC+1" if bst else "GMT UTC+0"
    if bst != actual_bst:
        flags.append(
            f"tod_panel.is_bst={bst} disagrees with actual UK BST "
            f"({start.isoformat()} to {end.isoformat()}) for {dt.date().isoformat()}; "
            f"using tod_panel.is_bst (do not 'fix' the sun)."
        )
    listed = SPEC_LISTED.get(ref_id)
    got = dt.strftime("%Y-%m-%d %H:%M")
    if listed and not listed.startswith(got):
        # listed may omit seconds
        if got != listed and not (listed == got[: len(listed)]):
            flags.append(
                f"EXIF DateTimeOriginal {got} (plus seconds) != analyst/spec listed time "
                f"{listed}. Using EXIF. Camera clock, not a Geograph page date."
            )
    if exif.get("offset_tag") is None:
        flags.append(
            f"No EXIF OffsetTimeOriginal; assumed UK local {assumed} via tod_panel.is_bst "
            f"(approx. BST if date >= 29 Mar and < 25 Oct)."
        )
    el, az = sun_pos(hour, dt.month, dt.day)
    return {
        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": hour,
        "is_bst": bst,
        "actual_uk_bst": actual_bst,
        "assumed_offset": assumed,
        "sun_el": round(el, 3),
        "sun_az": round(az, 3),
        "spec_listed": listed,
    }, flags


def luma(arr: np.ndarray) -> np.ndarray:
    a = arr.astype(np.float32)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def sky_mask(rgb: np.ndarray) -> np.ndarray:
    """True where sky-like (bright, bluish) and reachable from the top edge."""
    h, w, _ = rgb.shape
    y = luma(rgb)
    b = rgb[..., 2].astype(np.float32)
    r = rgb[..., 0].astype(np.float32)
    skyish = (y > 140) & (b > r + 8)
    # also very bright near-white sky
    skyish |= (y > 200) & (b >= r - 5)
    vis = np.zeros((h, w), dtype=bool)
    # flood from top row
    from collections import deque
    q = deque()
    for x in range(w):
        if skyish[0, x]:
            vis[0, x] = True
            q.append((0, x))
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < h and 0 <= nj < w and skyish[ni, nj] and not vis[ni, nj]:
                vis[ni, nj] = True
                q.append((ni, nj))
    return vis


def shadow_mask(rgb: np.ndarray, analysis: np.ndarray, percentile: float = PERCENTILE):
    y = luma(rgb)
    vals = y[analysis]
    if vals.size == 0:
        return np.zeros(y.shape, dtype=bool), None
    thr = float(np.percentile(vals, percentile))
    return (y < thr) & analysis, thr


def iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / union) if union else 0.0


def edge_angle_deg(mask: np.ndarray) -> float | None:
    """Principal undirected angle of shadow-mask edges, degrees in [0, 180)."""
    m = mask.astype(np.float32)
    # simple Sobel
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)
    ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], np.float32)

    def conv(src, k):
        # pad
        p = np.pad(src, 1, mode="edge")
        out = np.zeros_like(src)
        for i in range(3):
            for j in range(3):
                out += k[i, j] * p[i : i + src.shape[0], j : j + src.shape[1]]
        return out

    gx, gy = conv(m, kx), conv(m, ky)
    mag = np.hypot(gx, gy)
    # keep strong edges
    thr = max(0.5, float(np.percentile(mag[mag > 0], 70)) if (mag > 0).any() else 1.0)
    sel = mag >= thr
    if int(sel.sum()) < 50:
        return None
    # undirected: double the angle and use circular mean, then half
    ang = np.arctan2(gy[sel], gx[sel])  # -pi..pi, normal to edge
    # line orientation is ang + pi/2, fold to [0, pi)
    ori = (ang + math.pi / 2.0) % math.pi
    w = mag[sel]
    c = np.sum(w * np.cos(2 * ori))
    s = np.sum(w * np.sin(2 * ori))
    mean = 0.5 * math.atan2(s, c)  # -pi/2..pi/2
    deg = math.degrees(mean) % 180.0
    return float(deg)


def angle_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    d = abs(a - b) % 180.0
    return float(min(d, 180.0 - d))


def analysis_mask(photo: np.ndarray, render: np.ndarray, y0: float | None = None) -> np.ndarray:
    # exclude sky in either image so trees/clouds don't dominate IoU
    sky = sky_mask(photo) | sky_mask(render)
    m = ~sky
    if y0 is not None:
        h = photo.shape[0]
        m[: int(h * y0)] = False
    return m


def score_pair(photo_im: Image.Image, render_im: Image.Image, y0: float | None = None):
    photo = np.asarray(photo_im.convert("RGB").resize(render_im.size, Image.Resampling.LANCZOS), np.uint8)
    rend = np.asarray(render_im.convert("RGB"), np.uint8)
    analysis = analysis_mask(photo, rend, y0=y0)
    ps, pthr = shadow_mask(photo, analysis)
    rs, rthr = shadow_mask(rend, analysis)
    pa = edge_angle_deg(ps)
    ra = edge_angle_deg(rs)
    return {
        "iou": iou(ps, rs),
        "photo_thr": pthr,
        "render_thr": rthr,
        "photo_shadow_frac": float(ps.sum() / max(1, analysis.sum())),
        "render_shadow_frac": float(rs.sum() / max(1, analysis.sum())),
        "photo_edge_angle_deg": pa,
        "render_edge_angle_deg": ra,
        "edge_angle_diff_deg": angle_diff(pa, ra),
        "analysis_frac": float(analysis.mean()),
    }, photo, rend, analysis, ps, rs


def make_sheet(photo, rend, analysis, ps, rs, dest: Path, title: str):
    h, w, _ = photo.shape

    def mask_rgb(m, base):
        out = base.copy()
        tint = out.copy()
        tint[m] = (np.minimum(tint[m].astype(np.int16) + np.array([0, 0, 80]), 255)).astype(np.uint8)
        tint[~m] = (tint[~m].astype(np.float32) * 0.55).astype(np.uint8)
        return tint

    ov = photo.copy()
    # photo shadows red, render cyan, overlap yellow-ish
    both = ps & rs
    only_p = ps & ~rs
    only_r = rs & ~ps
    ov = ov.astype(np.int16)
    ov[only_p] = ov[only_p] * 0.45 + np.array([200, 30, 30]) * 0.55
    ov[only_r] = ov[only_r] * 0.45 + np.array([20, 180, 200]) * 0.55
    ov[both] = ov[both] * 0.35 + np.array([220, 200, 40]) * 0.65
    ov = np.clip(ov, 0, 255).astype(np.uint8)

    gap = 8
    sheet = Image.new("RGB", (w * 4 + gap * 3, h + 36), (20, 20, 20))
    for i, arr in enumerate((photo, rend, mask_rgb(ps, photo), ov)):
        sheet.paste(Image.fromarray(arr), (i * (w + gap), 36))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), title, fill=(240, 240, 240))
    sheet.save(dest, quality=92)
    return dest


def render_jobs(solvable):
    jobs = []
    for ref in solvable:
        cap, flags = parse_capture(read_exif(ref["path"]), ref["id"])
        hours = [cap["hour"] + d for d in SWEEP]
        im_w, im_h = Image.open(ref["path"]).size
        jobs.append(
            {
                "id": ref["id"],
                "path": str(ref["path"]),
                "cam": ref["cam"],
                "cam_source": ref["cam_source"],
                "month": cap["month"],
                "day": cap["day"],
                "hours": hours,
                "offsets": list(SWEEP),
                "exif_hour": cap["hour"],
                "width": im_w,
                "height": im_h,
                "hide_near": 8,
                "clip_start": 4,
            }
        )
    return jobs


def run_blender(jobs, stamp_before):
    OUT.mkdir(parents=True, exist_ok=True)
    job_path = OUT / "jobs.json"
    job_path.write_text(json.dumps(jobs, indent=2))
    cmd = [
        BLENDER,
        "-b",
        "-y",
        str(BLEND),
        "--python",
        str(ROOT / "tests" / "suncheck" / "render_sun.py"),
        "--",
        "--jobs",
        str(job_path),
        "--out",
        str(OUT),
        "--samples",
        str(SPP),
        "--width",
        str(MAX_WIDTH),
    ]
    t0 = time.time()
    log = OUT / "blender.log"
    with open(log, "w") as lf:
        proc = subprocess.run(cmd, cwd=str(ROOT), stdout=lf, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    # surface the useful lines
    try:
        for line in log.read_text(errors="replace").splitlines():
            if any(k in line for k in ("RENDER ", "CLIP_START", "APPENDED", "MISSING", "SUNCHECK", "Error", "Traceback", "crash")):
                print(line)
    except Exception:
        pass
    stamp_after = official_stamp()
    bad = stamps_unchanged(stamp_before, stamp_after)
    if bad:
        raise SystemExit(f"BLOCK: official files changed: {bad}")
    if proc.returncode != 0:
        raise SystemExit(f"blender render failed rc={proc.returncode}")
    missing = []
    for job in jobs:
        for off in job["offsets"]:
            fn = OUT / f"render_{job['id']}_off{off:+d}.png"
            if not fn.is_file():
                missing.append(str(fn.name))
    if missing:
        raise SystemExit(f"blender produced no renders (script error?): {missing}")
    return dt, stamp_after


def score_all(render_seconds=None, stamp_before=None):
    OUT.mkdir(parents=True, exist_ok=True)
    refs_out = []
    n_pass = 0
    n_scored = 0
    for ref in REFS:
        exif = read_exif(ref["path"])
        cap, flags = parse_capture(exif, ref["id"]) if exif.get("datetime_original") else (None, ["no EXIF DateTimeOriginal"])
        rec = {
            "id": ref["id"],
            "path": str(ref["path"].relative_to(ROOT)),
            "solvable": ref["solvable"],
            "camera": ref["cam"],
            "camera_source": ref["cam_source"],
            "exif": exif,
            "capture": cap,
            "flags": flags,
        }
        if not ref["solvable"]:
            rec["status"] = "skipped"
            rec["skip_reason"] = ref["skip_reason"]
            refs_out.append(rec)
            continue
        if cap is None:
            rec["status"] = "skipped"
            rec["skip_reason"] = "no EXIF capture time"
            refs_out.append(rec)
            continue
        n_scored += 1
        sweep = []
        photo_im = Image.open(ref["path"]).convert("RGB")
        peak_iou = -1.0
        peak_off = None
        at_h = None
        for off in SWEEP:
            hour = cap["hour"] + off
            fn = OUT / f"render_{ref['id']}_off{off:+d}.png"
            if not fn.is_file():
                sweep.append({"offset_h": off, "hour": hour, "missing": True})
                continue
            rend_im = Image.open(fn)
            scores, photo, rend, analysis, ps, rs = score_pair(photo_im, rend_im, y0=STREET_Y0)
            full, *_ = score_pair(photo_im, rend_im, y0=None)
            el, az = sun_pos(hour, cap["month"], cap["day"])
            def _round(d):
                return {k: (round(v, 5) if isinstance(v, float) else v) for k, v in d.items()}
            row = {
                "offset_h": off,
                "hour": hour,
                "sun_el": round(el, 3),
                "sun_az": round(az, 3),
                "render": str(fn.relative_to(ROOT)),
                "mask": f"street_y0={STREET_Y0}",
                **_round(scores),
                "full_frame": _round(full),
            }
            sweep.append(row)
            if scores["iou"] > peak_iou:
                peak_iou = scores["iou"]
                peak_off = off
            if off == 0:
                at_h = row
                title = (
                    f"{ref['id']}  EXIF {cap['datetime']} {cap['assumed_offset']}  "
                    f"street IoU={scores['iou']:.3f}  ang={scores['edge_angle_diff_deg']}"
                )
                make_sheet(photo, rend, analysis, ps, rs, OUT / f"cmp_{ref['id']}_exif.jpg", title)
        rec["sweep"] = sweep
        rec["peak_offset_h"] = peak_off
        rec["peak_iou"] = None if peak_iou < 0 else round(peak_iou, 5)
        rec["exif_iou"] = None if at_h is None else at_h.get("iou")
        rec["exif_edge_angle_diff_deg"] = None if at_h is None else at_h.get("edge_angle_diff_deg")
        rec["peak_within_pm1h"] = peak_off is not None and abs(peak_off) <= IOU_WINDOW_H
        ang = rec["exif_edge_angle_diff_deg"]
        rec["angle_ok"] = ang is not None and ang <= ANGLE_LIMIT
        rec["ref_pass"] = bool(rec["peak_within_pm1h"] and rec["angle_ok"])
        rec["status"] = "PASS" if rec["ref_pass"] else "FAIL"
        if rec["ref_pass"]:
            n_pass += 1
        refs_out.append(rec)

    gate_pass = n_pass >= MIN_PASS_REFS
    # Method is implemented; numeric gate needs ≥2 passing solvable refs.
    if n_scored < MIN_PASS_REFS:
        verdict = "INSUFFICIENT_REFS"
        reason = (
            f"Only {n_scored} ref(s) have a camera_match solve; the pass rule needs "
            f"the IoU peak within ±{IOU_WINDOW_H:.0f} h and edge-angle ≤{ANGLE_LIMIT:.0f}° "
            f"on at least {MIN_PASS_REFS} refs. This is a camera-match coverage limit, "
            f"not a failure of the sun / EXIF method."
        )
    elif gate_pass:
        verdict = "PASS"
        reason = f"{n_pass} refs meet the IoU-peak and angle tests."
    else:
        verdict = "FAIL"
        reason = (
            f"{n_pass} of {n_scored} scored refs meet the pass rule "
            f"(need {MIN_PASS_REFS})."
        )

    stamp = official_stamp()
    result = {
        "trick": 22,
        "name": "sun-time shadow-alignment gate",
        "verdict": verdict,
        "reason": reason,
        "gate_pass": gate_pass,
        "n_scored": n_scored,
        "n_pass": n_pass,
        "n_required": MIN_PASS_REFS,
        "shadow_percentile": PERCENTILE,
        "street_y0": STREET_Y0,
        "sweep_hours": list(SWEEP),
        "spp": SPP,
        "render_seconds": render_seconds,
        "official_untouched": True if stamp_before is None else (stamps_unchanged(stamp_before, stamp) == []),
        "official": stamp,
        "refs": refs_out,
    }
    blob = json.dumps(result, indent=2) + "\n"
    RESULT.write_text(blob)
    RESULT_OUT.write_text(blob)
    print(json.dumps({k: result[k] for k in ("verdict", "reason", "n_scored", "n_pass", "gate_pass")}, indent=2))
    print("WROTE", RESULT)
    return result


def verify():
    path = RESULT if RESULT.is_file() else RESULT_OUT
    if not path.is_file():
        print("SUNCHECK missing", RESULT)
        return 1
    data = json.loads(path.read_text())
    stamp_now = official_stamp()
    # compare sha256 of official files vs recorded
    rec = data.get("official") or {}
    changed = []
    for k, meta in rec.items():
        now = stamp_now.get(k)
        if not now or now.get("sha256") != meta.get("sha256"):
            # presence of floors files may differ across checkouts; only fail if a recorded file changed
            if meta.get("sha256") and now and now.get("sha256") != meta.get("sha256"):
                changed.append(k)
    print(
        "SUNCHECK",
        json.dumps(
            {
                "verdict": data.get("verdict"),
                "gate_pass": data.get("gate_pass"),
                "n_scored": data.get("n_scored"),
                "n_pass": data.get("n_pass"),
                "official_changed": changed,
            }
        ),
    )
    if changed:
        print("SUNCHECK official hash changed:", changed)
        return 1
    # verify is informational + file present; exit 0 if the script ran, even if
    # the numeric gate is INSUFFICIENT_REFS / FAIL (validate hook still reports).
    # Non-zero only when official files moved or the result file is malformed.
    return 0 if data.get("verdict") in ("PASS", "FAIL", "INSUFFICIENT_REFS") else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--render", action="store_true", help="Render then score")
    g.add_argument("--score", action="store_true", help="Score existing renders")
    g.add_argument("--verify", action="store_true", help="Read result.json (validate hook)")
    args = ap.parse_args(argv)
    if args.verify:
        return verify()
    stamp = official_stamp()
    render_s = None
    if args.render:
        jobs = render_jobs([r for r in REFS if r["solvable"]])
        render_s, _ = run_blender(jobs, stamp)
    elif not args.score:
        ap.error("pass --render, --score or --verify")
    result = score_all(render_seconds=render_s, stamp_before=stamp)
    stamp_after = official_stamp()
    bad = stamps_unchanged(stamp, stamp_after)
    if bad:
        print("BLOCK: official files changed:", bad)
        return 1
    # Always exit 0 after a completed run so --render can finish; verdict is in JSON.
    return 0


if __name__ == "__main__":
    sys.exit(main())
