import json, sys
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import ref_check

OUT = ROOT / "tests" / "disp" / "out"


def arr(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)


def pixel_stats(a, b):
    d = np.abs(a - b)
    return {"mean_abs_255": float(d.mean()), "pct_px_changed_gt2": float((d.max(axis=2) > 2.0).mean() * 100.0)}


def main():
    off = next(OUT.glob("disp_off_Cam_Street_*.png"))
    on = next(OUT.glob("disp_on_Cam_Street_*.png"))
    a, b = arr(off), arr(on)
    report = {"trick": 8, "street_pixel": pixel_stats(a, b)}
    official = ROOT / "out" / "render_street_4096x2304.png"
    if official.is_file():
        report["ref_check_off_vs_official"] = {"f1": ref_check.check(str(off), str(official), str(OUT / "disp_off_official_check.png"))}
        report["ref_check_on_vs_official"] = {"f1": ref_check.check(str(on), str(official), str(OUT / "disp_on_official_check.png"))}
    refg = ROOT / "refs" / "critic1" / "real_geograph.jpg"
    # stone / terracotta crop means
    H, W = a.shape[:2]
    report["stone_base_mean_off"] = a[int(H*0.62):int(H*0.82), int(W*0.3):int(W*0.7)].mean(axis=(0,1)).tolist()
    report["stone_base_mean_on"] = b[int(H*0.62):int(H*0.82), int(W*0.3):int(W*0.7)].mean(axis=(0,1)).tolist()
    report["terracotta_mean_off"] = a[int(H*0.22):int(H*0.50), int(W*0.3):int(W*0.7)].mean(axis=(0,1)).tolist()
    report["terracotta_mean_on"] = b[int(H*0.22):int(H*0.50), int(W*0.3):int(W*0.7)].mean(axis=(0,1)).tolist()
    for tag in ("off", "on"):
        tp = OUT / f"disp_{tag}_times.json"
        if tp.is_file():
            report[f"times_{tag}"] = json.loads(tp.read_text())
    off_t = report.get("times_off", {}).get("times", {}).get("Cam_Street", {}).get("s")
    on_t = report.get("times_on", {}).get("times", {}).get("Cam_Street", {}).get("s")
    if off_t and on_t:
        report["time_ratio"] = on_t / off_t
        report["time_ok_le_2x"] = (on_t / off_t) <= 2.0
    rss = report.get("times_on", {}).get("times", {}).get("Cam_Street", {}).get("maxrss_mb")
    report["maxrss_mb_on"] = rss
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
