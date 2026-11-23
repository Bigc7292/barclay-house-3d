import json, re, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = [
    ROOT / "out" / "barclay_hero3_floors.glb",
    ROOT / "tests" / "hero3_floors" / "out" / "barclay_hero3_floors.glb",
    ROOT / "tests" / "hero3_floors" / "out" / "mobile" / "barclay_hero_mobile.glb",
]
if len(sys.argv) > 1:
    paths = [Path(p) for p in sys.argv[1:]]


def glb_json(path):
    with open(path, "rb") as f:
        magic, ver, length = struct.unpack("<4sII", f.read(12))
        chunk_len, chunk_type = struct.unpack("<I4s", f.read(8))
        return json.loads(f.read(chunk_len))

plan = json.loads((ROOT / "parts_plan.json").read_text())
required = plan["required_in_glb"]
out = {}
fail = False
for p in paths:
    rel = str(p if not str(p).startswith(str(ROOT)) else p.relative_to(ROOT))
    if not p.is_file():
        out[rel] = {"missing": True}
        print(rel, "MISSING")
        if "barclay_hero3_floors.glb" in rel or rel.endswith("barclay_hero.glb"):
            fail = True
        continue
    j = glb_json(p)
    names = [n.get("name") or "" for n in j.get("nodes", [])]
    floors = [n for n in names if n.startswith("Floor_")]
    doors = [n for n in names if n.startswith("Door_")]
    dotted = [n for n in names if re.search(r"\.\d{3}$", n)]
    missing = [n for n in required if n not in names]
    out[rel] = {
        "size_bytes": p.stat().st_size,
        "nodes": names,
        "Floor_*": floors,
        "Door_*": doors,
        "required_missing": missing,
        "dotted": dotted,
        "has_Building": "Building" in names,
    }
    print(rel, "bytes", p.stat().st_size)
    print("  nodes:", names)
    print("  Floor_*:", floors)
    print("  Door_*:", doors)
    print("  Building:", "Building" in names)
    print("  missing required:", missing)
    print("  dotted:", dotted)
    is_mobile = p.name.endswith("barclay_hero_mobile.glb")
    if is_mobile:
        need = [n for n in required if n.startswith("Floor_") or n.startswith("Door_")]
        miss = [n for n in need if n not in names]
        if miss or dotted:
            print("mobile missing Floor/Door or has dotted names:", miss or dotted)
            fail = True
    else:
        if missing or dotted:
            print("hero missing required or has dotted names:", missing or dotted)
            fail = True

dest = ROOT / "tests" / "hero3_floors" / "out" / "nodes.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out, indent=2))
if fail:
    raise SystemExit("required names missing")
