"""Score weather2 off vs on: pixel change, ref_check vs Geograph, parapet crop."""
import json, os, sys
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import ref_check

OUT = ROOT / "tests" / "weather2" / "out"
REF_G = ROOT / "refs" / "critic1" / "real_geograph.jpg"
# R4 p3 locked-cam scores (critic_log.md)
R4 = {"geograph": {"f1": 0.625, "precision": 0.685, "recall": 0.575}}


def arr(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)


def pixel_stats(a, b):
    d = np.abs(a - b)
    mean = float(d.mean())
    pct = float((d.max(axis=2) > 2.0).mean() * 100.0)
    return {"mean_abs_255": mean, "pct_px_changed_gt2": pct}


def crop_mean(im, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    return im[y0:y1, x0:x1].mean(axis=(0, 1)).tolist()


def main():
    # expected files
    street_off = next(OUT.glob("w2_off_Cam_Street_*.png"))
    street_on = next(OUT.glob("w2_on_Cam_Street_*.png"))
    via_off = next(OUT.glob("w2_off_Cam_Viaduct_*.png"))
    via_on = next(OUT.glob("w2_on_Cam_Viaduct_*.png"))
    geo_off = list(OUT.glob("w2_off_Cam_Match_geograph_*.png"))
    geo_on = list(OUT.glob("w2_on_Cam_Match_geograph_*.png"))

    report = {"trick": 12, "official_blend_untouched": True}
    a, b = arr(street_off), arr(street_on)
    report["street_pixel"] = pixel_stats(a, b)
    H, W = a.shape[:2]
    # parapet is the top band of the facade in Cam_Street (official still)
    report["street_parapet_mean_off"] = crop_mean(a, (W * 0.25, H * 0.04, W * 0.75, H * 0.14))
    report["street_parapet_mean_on"] = crop_mean(b, (W * 0.25, H * 0.04, W * 0.75, H * 0.14))
    report["street_facade_mean_off"] = crop_mean(a, (W * 0.30, H * 0.20, W * 0.70, H * 0.50))
    report["street_facade_mean_on"] = crop_mean(b, (W * 0.30, H * 0.20, W * 0.70, H * 0.50))

    c, d = arr(via_off), arr(via_on)
    report["viaduct_pixel"] = pixel_stats(c, d)

    # close-up crops from the street on/off pair
    crops = {
        "doorcase": (0.42, 0.55, 0.58, 0.95),
        "oriel": (0.10, 0.18, 0.28, 0.55),
        "cornice": (0.30, 0.02, 0.70, 0.22),
        "parapet": (0.25, 0.02, 0.75, 0.14),
    }
    for name, (u0, v0, u1, v1) in crops.items():
        box = (int(W * u0), int(H * v0), int(W * u1), int(H * v1))
        Image.fromarray(a[box[1]:box[3], box[0]:box[2]].astype(np.uint8)).save(OUT / f"crop_off_{name}.png")
        Image.fromarray(b[box[1]:box[3], box[0]:box[2]].astype(np.uint8)).save(OUT / f"crop_on_{name}.png")

    def score(render, ref, label):
        out = OUT / f"{label}_check.png"
        # ref_check.check prints and returns f1; also re-run to capture p/r from stdout later
        f1 = ref_check.check(str(render), str(ref), str(out))
        return {"f1": f1, "sheet": str(out.relative_to(ROOT))}

    report["ref_check"] = {}
    if geo_off and geo_on and REF_G.is_file():
        report["ref_check"]["geograph_off"] = score(geo_off[0], REF_G, "geograph_off")
        report["ref_check"]["geograph_on"] = score(geo_on[0], REF_G, "geograph_on")
        report["ref_check"]["r4_geograph_f1"] = R4["geograph"]["f1"]

    # also street vs official 4K still (same camera, different res — resized by ref_check)
    official = ROOT / "out" / "render_street_4096x2304.png"
    if official.is_file():
        report["ref_check"]["street_vs_official_off"] = score(street_off, official, "street_official_off")
        report["ref_check"]["street_vs_official_on"] = score(street_on, official, "street_official_on")

    for tag in ("off", "on"):
        tp = OUT / f"w2_{tag}_times.json"
        if tp.is_file():
            report[f"times_{tag}"] = json.loads(tp.read_text())

    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
