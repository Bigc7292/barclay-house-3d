#!/usr/bin/env python3
"""Two Bed interior reference-checklist gate (trick #15).

Scores room renders against Rightmove 92163630 CGI photos.
Free libs only: stdlib + numpy + Pillow (via repo checks.py).

  python tests/reference/score.py --renders <dir>
  python tests/reference/score.py --renders <dir> --output /tmp/result.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

import checks  # noqa: E402
from PIL import Image  # noqa: E402
import numpy as np  # noqa: E402

YES, PARTIAL, NO = checks.YES, checks.PARTIAL, checks.NO
RATIO_YES, RATIO_PARTIAL = checks.RATIO_YES, checks.RATIO_PARTIAL
DEFAULT_CHECKLIST = os.path.join(HERE, "checklist.json")
DEFAULT_OUTPUT = os.path.join(HERE, "result.json")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

# Filename aliases used to find a room render in --renders.
ROOM_ALIASES = {
    "living": ["living"],
    "kitchen": ["kitchen"],
    "bedroom1": ["bedroom1", "bed1", "bedroom_1"],
    "bedroom2": ["bedroom2", "bed2", "bedroom_2"],
    "bathroom": ["bathroom", "bath"],
}


def load_checklist(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def ref_by_id(spec: dict) -> dict:
    return {p["id"]: p for p in spec["cgi_photos"]}


def resolve_path(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def _stem(name: str) -> str:
    return os.path.splitext(name)[0].lower()


def _alias_match_rank(stem: str, aliases: list[str]):
    """Return a sortable (priority, version) or None if no match.

    Priority 4: vN_<alias> (highest version wins, e.g. v3_living over v2_living)
    Priority 3: exact <alias>
    Priority 2: closeup_<alias> (not closeup_<alias>_...)
    Priority 1: stem endswith _<alias> (desktop_01_i_living, etc.)
    """
    for alias in aliases:
        m = re.fullmatch(rf"v(\d+)_{re.escape(alias)}", stem)
        if m:
            return (4, int(m.group(1)))
        if stem == alias:
            return (3, 0)
        if stem == f"closeup_{alias}":
            return (2, 0)
        if re.search(rf"(^|_){re.escape(alias)}$", stem):
            return (1, 0)
    return None


def list_images(renders_dir: str) -> list[str]:
    out = []
    for name in os.listdir(renders_dir):
        if os.path.splitext(name)[1].lower() in IMAGE_EXT:
            if os.path.isfile(os.path.join(renders_dir, name)):
                out.append(name)
    return out


def resolve_room(renders_dir: str, room: str) -> str | None:
    aliases = ROOM_ALIASES[room]
    ranked = []
    for name in list_images(renders_dir):
        rank = _alias_match_rank(_stem(name), aliases)
        if rank is not None:
            ranked.append((rank, name))
    if not ranked:
        return None
    ranked.sort(key=lambda t: (t[0][0], t[0][1], t[1]), reverse=True)
    return os.path.join(renders_dir, ranked[0][1])


def score_value_ratio(render_im: Image.Image, ref_im: Image.Image, row: dict):
    """Bidirectional mean-value match (method: mean value vs reference)."""
    r_crop = checks._crop_frac(render_im, row["render_crop"])
    f_crop = checks._crop_frac(ref_im, row["ref_crop"])
    r_crop, f_crop = checks._common_size(r_crop, f_crop)
    rs = checks._hsv_stats(np.asarray(r_crop))
    fs = checks._hsv_stats(np.asarray(f_crop))
    rv, fv = rs["mean_v"], fs["mean_v"]
    bidir = min(rv, fv) / max(fv, rv, 1e-9)
    if bidir >= RATIO_YES:
        st = YES
    elif bidir >= RATIO_PARTIAL:
        st = PARTIAL
    else:
        st = NO
    metric = f"mean_v {rv:.3f}/{fv:.3f} bidir={bidir:.2f}"
    return st, {"score": bidir, "metric": metric, "status": st, "rule": "value_ratio",
                "render": rs, "ref": fs}


# Absolute luma-std floor (V in 0..1). Photoreal CGI has more edges than a
# low-poly render, so presence is not a render/ref edge ratio. Below this
# the crop is a flat wall / blown-out void and colour agreement is ignored.
PRESENCE_STD = 0.05


def _apply_presence(st: str, detail: dict) -> tuple:
    """Colour-only rules cannot pass if the crop has no structure (blank wall)."""
    if detail.get("rule") not in {"hue_proximity", "value_ratio"}:
        return st, detail
    rs = detail["render"]
    std = float(rs["luma_std"])
    detail["metric"] = f"{detail['metric']} luma_std={std:.3f}"
    if std < PRESENCE_STD:
        st = NO
        detail["status"] = st
    return st, detail


def score_row(render_im: Image.Image, ref_im: Image.Image, row: dict):
    if row["rule"] == "value_ratio":
        st, detail = score_value_ratio(render_im, ref_im, row)
    else:
        st, detail = checks.score_element(render_im, ref_im, row)
    return _apply_presence(st, detail)


def score_norm(rule: str, detail: dict) -> float:
    """Map a row's numeric metric onto 0..1 for the overall mean."""
    raw = float(detail.get("score", 0.0))
    if rule == "hue_proximity":
        # raw is |dHue| in degrees; 0 deg -> 1.0, 90 deg -> 0.
        return max(0.0, 1.0 - raw / 90.0)
    # Ratio-like rules: cap at 1 so overshoot does not inflate the mean.
    return max(0.0, min(1.0, raw))


def run(renders_dir: str, output_path: str, checklist_path: str) -> dict:
    renders_dir = os.path.abspath(renders_dir)
    if not os.path.isdir(renders_dir):
        raise FileNotFoundError(f"renders dir not found: {renders_dir}")

    spec = load_checklist(checklist_path)
    photos = ref_by_id(spec)

    rooms = sorted({el["room"] for el in spec["elements"]})
    resolved = {room: resolve_room(renders_dir, room) for room in rooms}

    render_imgs: dict[str, Image.Image] = {}
    ref_imgs: dict[str, Image.Image] = {}
    for room, path in resolved.items():
        if path and os.path.exists(path):
            render_imgs[room] = checks._open_rgb(path)
    for pid, photo in photos.items():
        path = resolve_path(photo["file"])
        if os.path.exists(path):
            ref_imgs[pid] = checks._open_rgb(path)

    items = []
    statuses = []
    norms = []
    for row in spec["elements"]:
        room = row["room"]
        ref_id = row["ref_id"]
        photo = photos[ref_id]
        render_path = resolved.get(room)
        missing = []
        if not render_path:
            missing.append(f"no {room} render in {renders_dir}")
        if ref_id not in ref_imgs:
            missing.append(f"missing CGI {photo['file']}")

        if missing:
            st, raw, metric, norm = NO, 0.0, "; ".join(missing), 0.0
        else:
            st, detail = score_row(render_imgs[room], ref_imgs[ref_id], row)
            raw = float(detail["score"])
            metric = detail["metric"]
            norm = score_norm(row["rule"], detail)
            # Blank/flat crops: colour luck must not inflate the overall score.
            rs = detail.get("render") or {}
            if st == NO and float(rs.get("luma_std", 1.0)) < PRESENCE_STD:
                norm = 0.0

        statuses.append(st)
        norms.append(norm)
        items.append({
            "element": row["element"],
            "room": room,
            "rule": row["rule"],
            "status": st,
            "score": round(raw, 4),
            "score_norm": round(norm, 4),
            "metric": metric,
            "render": os.path.relpath(render_path, REPO) if render_path else None,
            "ref": photo["file"],
            "ref_url": photo["url"],
            "source": row.get("source", ""),
        })

    ok, n_no, n_partial = checks.gate_verdict(statuses)
    n_yes = sum(1 for s in statuses if s == YES)
    overall = float(sum(norms) / len(norms)) if norms else 0.0
    result = {
        "listing": spec["listing"],
        "listing_url": spec.get("listing_url"),
        "renders_dir": os.path.relpath(renders_dir, REPO)
        if os.path.commonpath([renders_dir, REPO]) == REPO
        else renders_dir,
        "resolved_renders": {
            room: (os.path.relpath(path, REPO) if path else None)
            for room, path in resolved.items()
        },
        "cgi_urls": [
            {"id": p["id"], "room": p["room"], "url": p["url"], "file": p["file"],
             "caption": p.get("caption", "")}
            for p in spec["cgi_photos"]
        ],
        "items": items,
        "counts": {"yes": n_yes, "partial": n_partial, "no": n_no, "total": len(items)},
        "score": round(overall, 4),
        "score_pct": round(overall * 100.0, 1),
        "gate": {
            "pass": ok,
            "verdict": "PASS" if ok else "FAIL",
            "threshold": "no 'no' rows and <=2 'partial'",
            "yes_ratio": RATIO_YES,
            "partial_ratio": RATIO_PARTIAL,
        },
        "method": (
            "trick #15; /home/box/x-bookmarks/implementations/barclay/"
            "2026-11-09-reference-checklist-gate.md; x_tricks.md #15"
        ),
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return result


def format_report(result: dict) -> str:
    g = result["gate"]
    c = result["counts"]
    lines = [
        f"Checklist gate — Two Bed vs Rightmove {result['listing']}",
        f"Renders: {result['renders_dir']}",
        f"Resolved: {result['resolved_renders']}",
        f"Score: {result['score_pct']}% (mean item score_norm)",
        (
            f"Gate: {g['verdict']}  yes={c['yes']} partial={c['partial']} "
            f"no={c['no']}  (need {g['threshold']})"
        ),
        "",
        f"{'element':<28} {'status':<8} {'score_norm':>10}  metric",
        "-" * 88,
    ]
    for it in result["items"]:
        lines.append(
            f"{it['element']:<28} {it['status']:<8} {it['score_norm']:>10.3f}  {it['metric']}"
        )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    t0 = time.time()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--renders", required=True,
                    help="Directory of Two Bed interior renders to score")
    ap.add_argument("--output", default=DEFAULT_OUTPUT,
                    help=f"JSON output path (default: {DEFAULT_OUTPUT})")
    ap.add_argument("--checklist", default=DEFAULT_CHECKLIST,
                    help="Checklist JSON (default: tests/reference/checklist.json)")
    args = ap.parse_args(argv)
    result = run(args.renders, args.output, args.checklist)
    print(format_report(result))
    print(f"Wrote {args.output}  ELAPSED {time.time() - t0:.2f}s")
    return 0 if result["gate"]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
