"""Build out/barclay_hero3_floors.glb: hero3.glb look + Floor_*/Door_*/Building names.

Never overwrites web/hero3.glb, out/barclay_hero.glb, out/barclay_scene.blend
or out/barclay_hero_floors.glb. Splits decoded hero3 meshes into storey / door
nodes using world AABBs from out/barclay_hero_floors.glb (same coordinate frame).
Floor_* slabs are not copied (they run through window openings). The storey
skin is on the Floor_* nodes themselves (so make_mobile keeps the names);
doors are children of Floor_01 so a raycast can walk up to Floor_*. Materials
and textures are copied from hero3 (dark front, black frames, BARCLAY HOUSE
lettering).
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parents[2]
HERO3 = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/hero3-inspect/hero3_decoded.glb")
FLOORS = HERE / "out" / "barclay_hero_floors.glb"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "tests" / "hero3_floors" / "out" / "barclay_hero3_floors.glb"

# Storey bands in glTF Y-up metres, from the Floor_* slabs / official children.
# Floor_00 only keeps the basement / Window_00 sill (below GF openings at Y=0.2).
# Floor_01 starts at the GF openings so arches, lettering and doors stay together.
# Floor_02 starts just below the oriel (official oriel is a Floor_02 child).
BANDS = [
    ("Floor_00", -10.0, 0.20),
    ("Floor_01", 0.20, 5.513),
    ("Floor_02", 5.513, 9.488),
    ("Floor_03", 9.488, 12.778),
    ("Floor_04", 12.778, 16.101),
    ("Floor_05", 16.101, 100.0),
]
# Door AABBs from barclay_hero_floors.glb (world), padded.
PAD = 0.04
DOOR_BOXES = {
    "Door_entrance_L_leaf": ((-1.453 - PAD, 0.0 - PAD, 14.969 - PAD), (-0.260 + PAD, 3.400 + PAD, 15.142 + PAD)),
    "Door_entrance_R_leaf": ((-0.247 - PAD, 0.0 - PAD, 15.064 - PAD), (0.946 + PAD, 3.400 + PAD, 15.237 + PAD)),
    "Door_entrance_frame": ((-1.927 - PAD, 0.0 - PAD, 14.962 - PAD), (1.371 + PAD, 5.323 + PAD, 15.720 + PAD)),
}


def load_glb(path):
    with open(path, "rb") as f:
        magic, ver, length = struct.unpack("<4sII", f.read(12))
        jlen, jtyp = struct.unpack("<I4s", f.read(8))
        j = json.loads(f.read(jlen))
        f.read((4 - (jlen % 4)) % 4)
        blen, btyp = struct.unpack("<I4s", f.read(8))
        b = f.read(blen)
    return j, b


def acc(j, b, ai):
    a = j["accessors"][ai]
    bv = j["bufferViews"][a["bufferView"]]
    dt = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a["componentType"]]
    nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    st = bv.get("byteStride")
    item = np.dtype(dt).itemsize * nc
    n = a["count"]
    if st and st != item:
        r = np.frombuffer(b, np.uint8, n * st, off).reshape(n, st)[:, :item].copy().view(dt).reshape(n, nc)
    else:
        r = np.frombuffer(b, dt, n * nc, off).reshape(n, nc).copy()
    return r.astype(np.float32 if a["type"] != "SCALAR" else (np.uint32 if dt != np.float32 else np.float32)), a


def trs_matrix(n):
    M = np.eye(4, dtype=np.float64)
    s = n.get("scale") or [1, 1, 1]
    r = n.get("rotation") or [0, 0, 0, 1]
    t = n.get("translation") or [0, 0, 0]
    x, y, z, w = r
    R = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )
    M[:3, :3] = R @ np.diag(s)
    M[:3, 3] = t
    if "matrix" in n:
        M = np.array(n["matrix"], dtype=np.float64).reshape(4, 4, order="F")
    return M


def world_mats(j):
    nodes = j["nodes"]
    parent = {i: None for i in range(len(nodes))}
    for i, n in enumerate(nodes):
        for c in n.get("children") or []:
            parent[c] = i
    cache = {}

    def wm(i):
        if i in cache:
            return cache[i]
        m = trs_matrix(nodes[i])
        if parent[i] is not None:
            m = wm(parent[i]) @ m
        cache[i] = m
        return m

    return [wm(i) for i in range(len(nodes))]


def in_box(p, box):
    (x0, y0, z0), (x1, y1, z1) = box
    return (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= y0) & (p[:, 1] <= y1) & (p[:, 2] >= z0) & (p[:, 2] <= z1)


def band_of(y):
    for name, lo, hi in BANDS:
        if lo <= y < hi:
            return name
    return BANDS[-1][0]


def bake_primitive(j, b, prim, M):
    pos, _ = acc(j, b, prim["attributes"]["POSITION"])
    pos = pos.astype(np.float64)
    homo = np.c_[pos, np.ones(len(pos))]
    wpos = (homo @ M.T)[:, :3].astype(np.float32)
    out = {"POSITION": wpos}
    if "NORMAL" in prim["attributes"]:
        nor, _ = acc(j, b, prim["attributes"]["NORMAL"])
        R = M[:3, :3]
        # normal: inverse-transpose of the 3x3
        # row-vector form of n' = (R^{-1})^T n : n_row @ R^{-1}
        nrm = nor.astype(np.float64) @ np.linalg.inv(R)
        n = np.linalg.norm(nrm, axis=1, keepdims=True)
        n = np.maximum(n, 1e-12)
        out["NORMAL"] = (nrm / n).astype(np.float32)
    if "TEXCOORD_0" in prim["attributes"]:
        uv, _ = acc(j, b, prim["attributes"]["TEXCOORD_0"])
        out["TEXCOORD_0"] = uv.astype(np.float32)
    if "indices" in prim:
        idx, _ = acc(j, b, prim["indices"])
        idx = idx.astype(np.int64).reshape(-1)
        if idx.size % 3:
            idx = idx[: idx.size - idx.size % 3]
        tris = idx.reshape(-1, 3)
    else:
        tris = np.arange(len(wpos), dtype=np.int64).reshape(-1, 3)
    return out, tris, prim.get("material", 0)


def remap(attrs, tris):
    used = np.unique(tris)
    inv = np.full(int(attrs["POSITION"].shape[0]), -1, dtype=np.int64)
    inv[used] = np.arange(len(used))
    new_attrs = {k: v[used] for k, v in attrs.items()}
    return new_attrs, inv[tris]


class Builder:
    def __init__(self):
        self.bin = bytearray()
        self.views = []
        self.accessors = []
        self.meshes = []
        self.nodes = []
        self.mesh_of = {}  # name -> mesh index (append prims)

    def _view(self, data: bytes, target=None):
        if len(self.bin) % 4:
            self.bin.extend(b"\x00" * (4 - len(self.bin) % 4))
        off = len(self.bin)
        self.bin.extend(data)
        if len(self.bin) % 4:
            self.bin.extend(b"\x00" * (4 - len(self.bin) % 4))
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target is not None:
            v["target"] = target
        self.views.append(v)
        return len(self.views) - 1

    def _accessor(self, arr, typ, component, target, normalized=False):
        arr = np.ascontiguousarray(arr)
        vi = self._view(arr.tobytes(), target)
        acc = {
            "bufferView": vi,
            "componentType": component,
            "count": int(arr.shape[0]),
            "type": typ,
        }
        if normalized:
            acc["normalized"] = True
        if typ != "SCALAR":
            acc["min"] = arr.min(0).astype(float).tolist()
            acc["max"] = arr.max(0).astype(float).tolist()
        self.accessors.append(acc)
        return len(self.accessors) - 1

    def add_primitive(self, mesh_name, attrs, tris, material):
        attrs, tris = remap(attrs, tris)
        prim = {"attributes": {}, "material": int(material), "mode": 4}
        prim["attributes"]["POSITION"] = self._accessor(attrs["POSITION"].astype(np.float32), "VEC3", 5126, 34962)
        if "NORMAL" in attrs:
            prim["attributes"]["NORMAL"] = self._accessor(attrs["NORMAL"].astype(np.float32), "VEC3", 5126, 34962)
        if "TEXCOORD_0" in attrs:
            prim["attributes"]["TEXCOORD_0"] = self._accessor(attrs["TEXCOORD_0"].astype(np.float32), "VEC2", 5126, 34962)
        nverts = attrs["POSITION"].shape[0]
        if nverts > 65535:
            idx = tris.astype(np.uint32).reshape(-1)
            ctype = 5125
        else:
            idx = tris.astype(np.uint16).reshape(-1)
            ctype = 5123
        prim["indices"] = self._accessor(idx, "SCALAR", ctype, 34963)
        if mesh_name in self.mesh_of:
            self.meshes[self.mesh_of[mesh_name]]["primitives"].append(prim)
        else:
            self.mesh_of[mesh_name] = len(self.meshes)
            self.meshes.append({"name": mesh_name, "primitives": [prim]})
        return self.mesh_of[mesh_name]

    def add_image_bytes(self, data: bytes):
        return self._view(data, None)


def main():
    hero_j, hero_b = load_glb(HERO3)
    floors_j, floors_b = load_glb(FLOORS)
    bld = Builder()

    # buckets: name -> list of (attrs, tris, material)
    buckets = {}

    def add(name, attrs, tris, material):
        if len(tris) == 0:
            return
        # drop zero-area triangles created at clip edges
        p = attrs["POSITION"][tris]
        area = np.linalg.norm(np.cross(p[:,1]-p[:,0], p[:,2]-p[:,0]), axis=1)
        tris = tris[area > 1e-12]
        if len(tris) == 0:
            return
        buckets.setdefault(name, []).append((attrs, tris, material))

    hero_wms = world_mats(hero_j)
    counts = {}
    for ni, n in enumerate(hero_j["nodes"]):
        if "mesh" not in n:
            continue
        M = hero_wms[ni]
        for prim in hero_j["meshes"][n["mesh"]]["primitives"]:
            attrs, tris, mat = bake_primitive(hero_j, hero_b, prim, M)
            C = attrs["POSITION"][tris].mean(axis=1)
            # door leaves first, then frame, then storey
            L = in_box(C, DOOR_BOXES["Door_entrance_L_leaf"])
            R = in_box(C, DOOR_BOXES["Door_entrance_R_leaf"])
            F = in_box(C, DOOR_BOXES["Door_entrance_frame"]) & ~L & ~R
            rest = ~(L | R | F)
            add("Door_entrance_L_leaf", attrs, tris[L], mat)
            add("Door_entrance_R_leaf", attrs, tris[R], mat)
            add("Door_entrance_frame", attrs, tris[F], mat)
            if rest.any():
                y = C[rest, 1]
                rem = tris[rest]
                for fname, lo, hi in BANDS:
                    sel = (y >= lo) & (y < hi)
                    add(fname, attrs, rem[sel], mat)
            for k, mask in (("L", L), ("R", R), ("frame", F)):
                counts[k] = counts.get(k, 0) + int(mask.sum())

    # Do not copy the official Floor_* slabs: they run through the window
    # openings and would show as extra planes. Storey skin lives on the
    # Floor_* nodes (required by parts_plan and kept by make_mobile).
    # Entrance doors are children of Floor_01 so a raycast can walk up.

    # emit meshes
    mesh_index = {}
    for name, items in buckets.items():
        for attrs, tris, mat in items:
            mi = bld.add_primitive(name, attrs, tris, mat)
            mesh_index[name] = mi

    # node graph: Building > Floor_* (with skin mesh) ; Floor_01 also has doors
    def node(name, mesh=None, children=None):
        n = {"name": name}
        if mesh is not None:
            n["mesh"] = mesh
        if children:
            n["children"] = children
        bld.nodes.append(n)
        return len(bld.nodes) - 1

    floor_ids = []
    for fname, lo, hi in BANDS:
        child_ids = []
        if fname == "Floor_01":
            for cn in (
                "Door_entrance_frame",
                "Door_entrance_L_leaf",
                "Door_entrance_R_leaf",
            ):
                if cn in mesh_index:
                    child_ids.append(node(cn, mesh_index[cn]))
        if fname not in mesh_index:
            raise SystemExit(f"missing storey mesh for {fname}")
        fi = node(fname, mesh_index[fname], child_ids or None)
        floor_ids.append(fi)
    building = node("Building", None, floor_ids)

    # copy hero3 materials / textures / images / samplers
    images = []
    for im in hero_j.get("images", []):
        bv = hero_j["bufferViews"][im["bufferView"]]
        data = hero_b[bv.get("byteOffset", 0) : bv.get("byteOffset", 0) + bv["byteLength"]]
        vi = bld.add_image_bytes(data)
        rec = {"bufferView": vi, "mimeType": im.get("mimeType", "image/webp")}
        if im.get("name"):
            rec["name"] = im["name"]
        images.append(rec)

    doc = {
        "asset": {"version": "2.0", "generator": "tests/hero3_floors/build_hero3_floors.py"},
        "scene": 0,
        "scenes": [{"name": "Scene", "nodes": [building]}],
        "nodes": bld.nodes,
        "meshes": bld.meshes,
        "materials": hero_j["materials"],
        "accessors": bld.accessors,
        "bufferViews": bld.views,
        "buffers": [{"byteLength": len(bld.bin)}],
        "images": images,
        "textures": hero_j.get("textures", []),
        "samplers": hero_j.get("samplers", []),
    }
    ext = []
    if hero_j.get("extensionsUsed"):
        # keep webp + clearcoat; drop meshopt / quantization (already decoded)
        for e in hero_j["extensionsUsed"]:
            if e in ("EXT_texture_webp", "KHR_materials_clearcoat"):
                ext.append(e)
    if ext:
        doc["extensionsUsed"] = ext
        doc["extensionsRequired"] = [e for e in ext if e == "EXT_texture_webp"]

    jb = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    if len(jb) % 4:
        jb += b" " * (4 - len(jb) % 4)
    blob = bytes(bld.bin)
    if len(blob) % 4:
        blob += b"\x00" * (4 - len(blob) % 4)
    length = 12 + 8 + len(jb) + 8 + len(blob)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, length))
        f.write(struct.pack("<I4s", len(jb), b"JSON"))
        f.write(jb)
        f.write(struct.pack("<I4s", len(blob), b"BIN\x00"))
        f.write(blob)

    # report
    names = [n["name"] for n in bld.nodes]
    print("WROTE", OUT, "bytes", OUT.stat().st_size)
    print("nodes", names)
    print("door tris", counts)
    print("meshes", [(m["name"], sum(len(p) for p in [m["primitives"]]), len(m["primitives"])) for m in bld.meshes])
    for name, items in buckets.items():
        nt = sum(len(t) for _, t, _ in items)
        print(f"  {name}: {nt} tris, {len(items)} prims")


if __name__ == "__main__":
    main()
