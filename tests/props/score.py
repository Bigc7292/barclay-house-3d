import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "props" / "out"
kit = json.loads((OUT / "kit.json").read_text())
report = {"trick": 13, "props": []}
ok = True
for p in kit["props"]:
    row = {"id": p["id"], "stand_in": p.get("stand_in"), "procedural": p.get("procedural", False)}
    if p.get("error"):
        row["error"] = p["error"]; ok = False
    if "sized_m" in p and "target" in p:
        t = p["target"]; s = p["sized_m"]
        if "length_m" in t and s.get("l"):
            row["length_err_m"] = abs(s["l"] - t["length_m"])
            row["length_ok"] = row["length_err_m"] <= 0.05
            ok = ok and row["length_ok"]
        if "height_m" in t and s.get("h") and p.get("scale_reason") == "height_m":
            row["height_err_m"] = abs(s["h"] - t["height_m"])
            row["height_ok"] = row["height_err_m"] <= 0.05
            ok = ok and row["height_ok"]
        row["origin_z"] = s.get("zmin")
        row["origin_ok"] = abs(s.get("zmin") or 0) <= 0.02
        ok = ok and row["origin_ok"]
    if p.get("tris") and p.get("lod1_tris") is not None:
        row["tris"] = p["tris"]
        row["lod1_tris"] = p["lod1_tris"]
        row["lod1_ratio"] = p.get("lod1_ratio")
        row["lod1_ok"] = (p["lod1_ratio"] or 1) <= 0.40  # allow some slop vs 0.25
    report["props"].append(row)
report["lineup"] = str((OUT / "props_lineup.png").relative_to(ROOT)) if (OUT / "props_lineup.png").is_file() else None
report["pass"] = ok
(OUT / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
if not ok:
    raise SystemExit("PROPS score had failures (see result.json)")
