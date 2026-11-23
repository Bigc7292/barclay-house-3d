#!/usr/bin/env python3
"""Cut a short interior walkthrough MP4 from stills (ffmpeg, free).

Default stills: current live Two Bed renders in interior/live/, skipping
near-blank frames and falling back to earlier stills in the same folder
when a v3 room shot has no detail (the v3 bedrooms on origin/barclay are
washed-out walls). Slow Ken Burns pans + crossfades.

  python tests/reference/make_walkthrough.py
  python tests/reference/make_walkthrough.py --out tests/reference/walkthrough.mp4

H.264, yuv420p, +faststart, target <25 MB.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_OUT = os.path.join(HERE, "walkthrough.mp4")
MAX_BYTES = 25 * 1024 * 1024
W, H, FPS = 1280, 720, 25
HOLD = 3.2
FADE = 0.7
# A still is "blank" if a 160x100 downscale has almost no colours or edges.
# (v3 bedrooms are washed-out walls; v3 bathroom is bright white but has fittings.)
BLANK_UNIQ = 400
BLANK_GRAD = 0.5

# Tour order. Each entry is a list of repo-relative candidates (first usable wins).
DEFAULT_SEQUENCE = [
    ["interior/live/latest.png"],
    ["interior/live/v3_living.png", "interior/live/v2_living.png",
     "interior/live/closeup_living.png"],
    ["interior/live/closeup_living.png"],
    ["interior/live/closeup_living_kitchen.png"],
    ["interior/live/v3_kitchen.png", "interior/live/v2_kitchen.png"],
    ["interior/live/v3_bedroom1.png", "interior/live/v2_bedroom1.png"],
    ["interior/live/v3_bedroom2.png", "interior/live/closeup_bedroom2.png",
     "interior/live/v2_bedroom2.png"],
    ["interior/live/v3_bathroom.png", "interior/live/v2_bathroom.png"],
]


def still_stats(path: str) -> tuple[float, int, float]:
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im)
    small = np.asarray(im.resize((160, 100)))
    uniq = int(len(np.unique(small.reshape(-1, 3), axis=0)))
    grad = float(np.abs(np.diff(small.astype(np.int16), axis=1)).mean())
    return float(arr.std()), uniq, grad


def is_blank(path: str) -> bool:
    _std, uniq, grad = still_stats(path)
    return uniq < BLANK_UNIQ or grad < BLANK_GRAD


def pick_stills(sequence=None) -> list[str]:
    chosen = []
    seen = set()
    for candidates in (sequence or DEFAULT_SEQUENCE):
        picked = None
        for rel in candidates:
            path = rel if os.path.isabs(rel) else os.path.join(REPO, rel)
            if not os.path.isfile(path):
                continue
            if is_blank(path):
                std, uniq, grad = still_stats(path)
                print(f"skip blank/low-detail {rel} (std={std:.1f} uniq={uniq} grad={grad:.2f})",
                      file=sys.stderr)
                continue
            picked = path
            break
        if picked is None:
            print(f"no usable still in {candidates}", file=sys.stderr)
            continue
        key = os.path.abspath(picked)
        if key in seen:
            continue
        seen.add(key)
        chosen.append(picked)
    return chosen


def build_filter(n: int) -> str:
    frames = int(round(HOLD * FPS))
    parts = []
    for i in range(n):
        # Alternate zoom-in vs slight pan so cuts don't feel identical.
        if i % 2 == 0:
            z = f"min(zoom+0.0008,1.10)"
            x = "(iw-iw/zoom)/2"
            y = "(ih-ih/zoom)/2"
        else:
            z = "1.08"
            x = f"(iw-iw/zoom)*on/{frames}"
            y = "(ih-ih/zoom)/2"
        parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},zoompan=z='{z}':x='{x}':y='{y}':d={frames}:"
            f"s={W}x{H}:fps={FPS},format=yuv420p[v{i}]"
        )
    last = "v0"
    if n == 1:
        parts.append(f"[{last}]format=yuv420p[out]")
        return ";".join(parts)
    for i in range(1, n):
        offset = i * (HOLD - FADE)
        nxt = "out" if i == n - 1 else f"x{i}"
        parts.append(
            f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[{nxt}]"
        )
        last = nxt
    return ";".join(parts)


def render(stills: list[str], out_path: str) -> None:
    if len(stills) < 2:
        raise SystemExit(f"need at least 2 stills, got {len(stills)}")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    # One input frame per still. zoompan's d= expands that frame; looping
    # the still first makes d apply per looped frame and blows the duration.
    for path in stills:
        cmd += ["-i", path]
    cmd += [
        "-filter_complex", build_filter(len(stills)),
        "-map", "[out]",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-crf", "20",
        "-preset", "medium",
        out_path,
    ]
    print("ffmpeg", " ".join(cmd[1:8]), "...", out_path)
    subprocess.run(cmd, check=True, cwd=REPO)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output MP4 path")
    ap.add_argument("--stills", nargs="*", default=None,
                    help="Optional explicit still paths (repo-relative or abs)")
    args = ap.parse_args(argv)

    if args.stills:
        stills = []
        for rel in args.stills:
            path = rel if os.path.isabs(rel) else os.path.join(REPO, rel)
            if not os.path.isfile(path):
                raise SystemExit(f"missing still: {rel}")
            stills.append(path)
    else:
        stills = pick_stills()

    print("stills:")
    for p in stills:
        std, uniq, grad = still_stats(p)
        print(f"  {os.path.relpath(p, REPO)}  (std={std:.1f} uniq={uniq} grad={grad:.2f})")

    out_path = args.out if os.path.isabs(args.out) else os.path.join(REPO, args.out)
    # Write to a temp file first so a failed encode cannot leave a half MP4.
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=os.path.dirname(out_path) or ".") as tmp:
        tmp_path = tmp.name
    try:
        render(stills, tmp_path)
        size = os.path.getsize(tmp_path)
        if size > MAX_BYTES:
            os.unlink(tmp_path)
            raise SystemExit(f"MP4 is {size} bytes, over 25 MB cap")
        os.replace(tmp_path, out_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    size = os.path.getsize(out_path)
    print(f"Wrote {out_path}  {size} bytes ({size/1024/1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
