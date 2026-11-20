"""Build side-by-sides and compare_result.json from cmp_{hero3,floors}_*.png."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "hero3_floors" / "out"
sys.path.insert(0, str(ROOT))
import ref_check

CAMS = ("street", "facade", "entrance", "lintel")


def main():
    result = {}
    for cam in CAMS:
        a_path = OUT / f"cmp_hero3_{cam}.png"
        b_path = OUT / f"cmp_floors_{cam}.png"
        a = Image.open(a_path).convert("RGB")
        b = Image.open(b_path).convert("RGB")
        A = np.asarray(a, np.float32)
        B = np.asarray(b, np.float32)
        d = np.abs(A - B)
        f1 = ref_check.check(str(a_path), str(b_path), str(OUT / f"cmp_refcheck_{cam}.png"))
        result[cam] = {
            "mean_abs_255": float(d.mean()),
            "pct_px_gt2": float((d.max(2) > 2).mean() * 100),
            "pct_px_gt8": float((d.max(2) > 8).mean() * 100),
            "f1": float(f1),
            "max": float(d.max()),
        }
        # 8x exaggerated diff
        vis = np.clip(d * 8, 0, 255).astype(np.uint8)
        Image.fromarray(vis).save(OUT / f"cmp_diff_x8_{cam}.png")
        w, h = a.size
        ss = Image.new("RGB", (w * 2 + 16, h), (20, 20, 20))
        ss.paste(a, (0, 0))
        ss.paste(b, (w + 16, 0))
        dest = OUT / f"cmp_side_{cam}.jpg"
        ss.resize((1600, int(1600 * ss.size[1] / ss.size[0]))).save(dest, quality=90)
        print(
            f"{cam}: mean {result[cam]['mean_abs_255']:.4f}/255, "
            f"{result[cam]['pct_px_gt2']:.3f}% px>2, F1 {result[cam]['f1']:.6f}"
        )
    (OUT / "compare_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("wrote", OUT / "compare_result.json")


if __name__ == "__main__":
    main()
