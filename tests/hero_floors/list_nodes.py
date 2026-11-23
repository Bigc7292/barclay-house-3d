import json, os, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = [
    ROOT / "out" / "barclay_hero_floors.glb",
    ROOT / "tests" / "hero_floors" / "out" / "mobile" / "barclay_hero_mobile.glb",
]

def glb_json(path):
    with open(path, "rb") as f:
        magic, ver, length = struct.unpack("<4sII", f.read(12))
        chunk_len, chunk_type = struct.unpack("<I4s", f.read(8))
        return json.loads(f.read(chunk_len))

plan = json.loads((ROOT / "parts_plan.json").read_text())
required = plan["required_in_glb"]
out = {}
for p in paths:
    if not p.is_file():
        out[str(p.relative_to(ROOT))] = {"missing": True}
        continue
    j = glb_json(p)
    names = [n.get("name") or "" for n in j.get("nodes", [])]
    floors = [n for n in names if n.startswith("Floor_")]
    doors = [n for n in names if n.startswith("Door_")]
    dotted = [n for n in names if __import__("re").search(r"\.\d{3}$", n)]
    missing = [n for n in required if n not in names]
    out[str(p.relative_to(ROOT))] = {
        "size_bytes": p.stat().st_size,
        "nodes": names,
        "Floor_*": floors,
        "Door_*": doors,
        "required_missing": missing,
        "dotted": dotted,
    }
    print(p.relative_to(ROOT), "bytes", p.stat().st_size)
    print("  Floor_*:", floors)
    print("  Door_*:", doors)
    print("  missing required:", missing)
    print("  dotted:", dotted)
(ROOT / "tests" / "hero_floors" / "out" / "nodes.json").write_text(json.dumps(out, indent=2))
# Full hero must have every parts_plan name. Mobile is allowed to drop the
# Building empty (make_mobile may prune empties) but must keep Floor_* / Door_*.
hero_fail = False
for path, v in out.items():
    if v.get("missing"):
        continue
    if path.endswith("barclay_hero_mobile.glb"):
        need = [n for n in required if n.startswith("Floor_") or n.startswith("Door_")]
        miss = [n for n in need if n not in v.get("Floor_*", []) + v.get("Door_*", []) and n not in v.get("nodes", [])]
        if miss or v.get("dotted"):
            print("mobile missing Floor/Door or has dotted names:", miss or v.get("dotted"))
            hero_fail = True
    else:
        if v.get("required_missing") or v.get("dotted"):
            print("hero missing required or has dotted names:", v.get("required_missing") or v.get("dotted"))
            hero_fail = True
if hero_fail:
    raise SystemExit("required names missing")
