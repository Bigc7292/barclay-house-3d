#!/usr/bin/env python3
"""mesh_health.py — Blender mesh-health gate (trick #19).

Checklist idea from arjun988/blender-skills (MIT):
  https://github.com/arjun988/blender-skills
  .claude/skills/references/validation-checklist.md
Own script, £0, Blender GPL. Claude Code from the source post is not used.

Usage:
  blender -b out/barclay_scene.blend --python mesh_health.py
  MH_OUT=tests/meshhealth blender -b tests/meshhealth/barclay_scene.blend --python mesh_health.py

Read-only: bmesh copies only; never writes the .blend (AGENTS rule 5).
Writes $MH_OUT/mesh_health.md and mesh_health.json (default: <repo>/out/).
Exit 0 if Blockers == 0 (PASS), else 1 (FAIL).
"""
from __future__ import annotations
import bpy, bmesh, hashlib, json, os, re, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("MH_OUT") or os.environ.get("BOUT") or os.path.join(ROOT, "out")
DOT_RE = re.compile(r"\.\d{3}$")
SKIP_COLL = {"HERO_cutters", "LIFE"}
DUP_DIST = 0.0001  # 0.1 mm
ZERO_AREA = 1e-12
SCALE_EPS = 1e-5


def _repo_path(p: str) -> str:
    try:
        return os.path.relpath(p, ROOT)
    except Exception:
        return p


def exported_meshes():
    out = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.data is None:
            continue
        if o.name.startswith("cut"):
            continue
        cols = [c.name for c in o.users_collection]
        if not cols:
            continue
        if all(c in SKIP_COLL or c.startswith("HERO_cutters") for c in cols):
            continue
        if any(c in SKIP_COLL or c.startswith("HERO_cutters") for c in cols):
            continue
        out.append(o)
    return out


def is_hero(o) -> bool:
    return any(c.name == "Hero" for c in o.users_collection)


def is_visible(o) -> bool:
    return (not o.hide_render) and (not o.hide_get())


def coll_name(o) -> str:
    cols = [c.name for c in o.users_collection]
    for prefer in ("Hero", "Buildings", "Rail_Viaduct", "Roads_Terrain_Water", "Trees_Furniture"):
        if prefer in cols:
            return prefer
    return cols[0] if cols else ""


def inconsistent_edges(bm) -> int:
    n = 0
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        a, b = e.verts
        dirs = []
        for f in e.link_faces:
            d = 0
            loop = f.loops[0]
            for _ in range(len(f.verts)):
                if loop.vert == a and loop.link_loop_next.vert == b:
                    d = 1
                    break
                if loop.vert == b and loop.link_loop_next.vert == a:
                    d = -1
                    break
                loop = loop.link_loop_next
            dirs.append(d)
        if dirs[0] and dirs[1] and dirs[0] == dirs[1]:
            n += 1
    return n


def mesh_fingerprint(o) -> str:
    me = o.data
    h = hashlib.sha1()
    h.update(f"{len(me.vertices)}|{len(me.edges)}|{len(me.polygons)}|".encode())
    mats = tuple((s.material.name if s.material else "") for s in o.material_slots)
    h.update(repr(mats).encode())
    # 0.1 mm-rounded local bbox + a stride sample of verts (full hash on small meshes)
    if not me.vertices:
        h.update(b"empty")
        return h.hexdigest()
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    bbox = tuple(round(v, 4) for v in (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))
    h.update(repr(bbox).encode())
    n = len(me.vertices)
    step = 1 if n <= 4000 else max(1, n // 2000)
    for i, v in enumerate(me.vertices):
        if i % step == 0:
            h.update(repr((round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))).encode())
    return h.hexdigest()


def inspect(o):
    me = o.data
    issue = []  # (severity, check, count, detail)
    hero = is_hero(o)
    vis = is_visible(o)

    sx, sy, sz = o.scale
    if sx < 0 or sy < 0 or sz < 0 or (o.matrix_local.determinant() < 0 and min(sx, sy, sz) < 0):
        issue.append(("Blocker", "negative_scale", 1, f"scale=({sx:.4f},{sy:.4f},{sz:.4f})"))
    elif abs(sx - 1) > SCALE_EPS or abs(sy - 1) > SCALE_EPS or abs(sz - 1) > SCALE_EPS:
        issue.append(("Major", "unapplied_scale", 1, f"scale=({sx:.4f},{sy:.4f},{sz:.4f})"))

    if DOT_RE.search(o.name):
        issue.append(("Major" if hero else "Minor", "dot001_name", 1, o.name))

    unused = 0
    used = {p.material_index for p in me.polygons} if me.polygons else set()
    for i, slot in enumerate(o.material_slots):
        if slot.material is None or i not in used:
            unused += 1
    if unused:
        issue.append(("Minor", "unused_material_slots", unused, f"{unused} unused of {len(o.material_slots)}"))

    if not me.polygons and not me.vertices:
        return issue, {"verts": 0, "faces": 0, "tris": 0}

    bm = bmesh.new()
    try:
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        # Boundary edges of open shells (kerbs, facades) are not defects.
        # True non-manifold = an edge used by 3+ faces, or a non-boundary
        # vertex whose fan is not manifold.
        nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
        nonman += sum(1 for v in bm.verts if (not v.is_manifold) and (not v.is_boundary) and v.link_edges)
        loose_v = sum(1 for v in bm.verts if not v.link_edges)
        loose_e = sum(1 for e in bm.edges if not e.link_faces)
        zero = sum(1 for f in bm.faces if f.calc_area() < ZERO_AREA)
        # dry-run: find_doubles returns a map, does not weld, does not write the mesh
        doubles = 0
        if bm.verts:
            ret = bmesh.ops.find_doubles(bm, verts=list(bm.verts), dist=DUP_DIST)
            doubles = len(ret.get("targetmap") or {})
        inconsist = inconsistent_edges(bm)
    finally:
        bm.free()

    if nonman:
        sev = "Blocker" if hero else "Major"
        issue.append((sev, "non_manifold", nonman, f"{nonman} non-manifold edges"))
    if inconsist:
        sev = "Blocker" if (hero and vis) else ("Major" if hero else "Minor")
        issue.append((sev, "flipped_normals", inconsist, f"{inconsist} inconsistent shared edges"))
    if loose_v or loose_e:
        sev = "Major" if hero else "Minor"
        issue.append((sev, "loose_geom", loose_v + loose_e, f"{loose_v} loose verts, {loose_e} loose edges"))
    if doubles:
        sev = "Major" if hero else "Minor"
        issue.append((sev, "duplicate_verts", doubles, f"{doubles} verts within {DUP_DIST*1000:.1f} mm"))
    if zero:
        sev = "Major" if hero else "Minor"
        issue.append((sev, "zero_area_faces", zero, f"{zero} faces with area < {ZERO_AREA}"))

    stats = {"verts": len(me.vertices), "faces": len(me.polygons), "tris": sum(len(p.vertices) - 2 for p in me.polygons)}
    return issue, stats


def main():
    t0 = time.time()
    blend = bpy.data.filepath
    mtime0 = os.path.getmtime(blend) if blend and os.path.isfile(blend) else None
    # hard guard: never save
    def _blocked_save(*_a, **_k):
        raise RuntimeError("mesh_health.py is read-only and must not save the .blend")
    if hasattr(bpy.ops.wm, "save_mainfile"):
        bpy.ops.wm.save_mainfile = _blocked_save  # type: ignore
        bpy.ops.wm.save_as_mainfile = _blocked_save  # type: ignore

    objs = exported_meshes()
    issues = []
    per_obj_stats = {}
    fingerprints = {}  # fp -> list of (name, mesh_name, mesh_ptr)
    n_hero = 0
    for o in objs:
        if is_hero(o):
            n_hero += 1
        found, stats = inspect(o)
        per_obj_stats[o.name] = stats
        col = coll_name(o)
        for sev, check, count, detail in found:
            issues.append({
                "object": o.name,
                "collection": col,
                "hero": is_hero(o),
                "severity": sev,
                "check": check,
                "count": count,
                "detail": detail,
            })
        if o.data and o.data.vertices:
            fp = mesh_fingerprint(o)
            fingerprints.setdefault(fp, []).append((o.name, o.data.name, o.data.as_pointer()))

    dup_groups = []
    unshared_groups = 0
    unshared_objects = 0
    already_shared = 0
    for fp, members in fingerprints.items():
        if len(members) < 2:
            continue
        ptrs = {p for _, _, p in members}
        names = [n for n, _, _ in members]
        shared = len(ptrs) == 1
        if shared:
            already_shared += 1
        else:
            unshared_groups += 1
            unshared_objects += len(members)
            # one Minor row for the group (instancing candidate, register #7)
            issues.append({
                "object": names[0],
                "collection": "",
                "hero": False,
                "severity": "Minor",
                "check": "duplicate_mesh_unshared",
                "count": len(members),
                "detail": f"{len(members)} copies, {len(ptrs)} unique datablocks (instancing candidate)",
            })
        dup_groups.append({
            "count": len(members),
            "unique_datablocks": len(ptrs),
            "shared_data": shared,
            "objects": names[:20],
            "objects_truncated": max(0, len(names) - 20),
        })

    blockers = [i for i in issues if i["severity"] == "Blocker"]
    majors = [i for i in issues if i["severity"] == "Major"]
    minors = [i for i in issues if i["severity"] == "Minor"]
    elapsed = time.time() - t0
    status = "PASS" if not blockers else "FAIL"

    def tally(rows):
        d = {}
        for r in rows:
            d[r["check"]] = d.get(r["check"], 0) + 1
        return d

    os.makedirs(OUT_DIR, exist_ok=True)
    report = {
        "trick": 19,
        "source": "https://github.com/arjun988/blender-skills (MIT, checklist idea only)",
        "blend": _repo_path(blend) if blend else "",
        "seconds": round(elapsed, 3),
        "objects_checked": len(objs),
        "hero_objects": n_hero,
        "status": status,
        "blockers": len(blockers),
        "majors": len(majors),
        "minors": len(minors),
        "counts_by_check": {
            "Blocker": tally(blockers),
            "Major": tally(majors),
            "Minor": tally(minors),
        },
        "duplicate_groups_total": len(dup_groups),
        "duplicate_groups_unshared": unshared_groups,
        "duplicate_objects_unshared": unshared_objects,
        "duplicate_groups_already_shared": already_shared,
        "issues": {
            "blockers": blockers,
            "majors_by_check": {
                k: {"count": v, "sample": [r for r in majors if r["check"] == k][:15]}
                for k, v in tally(majors).items()
            },
            "minors_by_check": tally(minors),
            "minors_sample": [m for m in minors if m["check"] == "duplicate_mesh_unshared"][:50],
            "majors_total": len(majors),
            "minors_total": len(minors),
        },
        "duplicate_groups_unshared_list": [g for g in dup_groups if not g["shared_data"]],
        "blend_saved": False,
    }
    json_path = os.path.join(OUT_DIR, "mesh_health.json")
    md_path = os.path.join(OUT_DIR, "mesh_health.md")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=1)

    def lines_for(rows, limit=80):
        out = []
        for r in rows[:limit]:
            out.append(f"- **{r['check']}** `{r['object']}` ({r['collection'] or '—'}): {r['detail']}")
        if len(rows) > limit:
            out.append(f"- … {len(rows) - limit} more")
        return out

    md = []
    md.append("# Mesh health (trick #19)")
    md.append("")
    md.append(f"Blend: `{report['blend']}`")
    md.append("Script is read-only: the .blend was not saved.")
    md.append("Checklist idea: [arjun988/blender-skills](https://github.com/arjun988/blender-skills) (MIT). Own script, £0.")
    md.append("")
    md.append(f"**Status: {status}** in {elapsed:.2f}s — Blockers {len(blockers)}, Majors {len(majors)}, Minors {len(minors)}.")
    md.append(f"Objects checked: {len(objs)} (Hero {n_hero}).")
    md.append(f"Duplicate-mesh groups (register #7): **{unshared_groups} unshared** ({unshared_objects} objects, {already_shared} groups already share datablocks).")
    md.append("")
    md.append("Severity: Blocker = flipped/inconsistent normals on visible Hero faces, non-manifold on Hero, or negative scale. Unapplied positive scale, Hero loose/dup/zero-area, Hero `*.001` names = Major. Unused slots, surroundings leftovers, unshared duplicate groups = Minor. Unapplied rotation is not flagged (objects are parented/placed).")
    md.append("")
    md.append("## Blockers")
    md.extend(lines_for(blockers) if blockers else ["- none"])
    md.append("")
    md.append("## Majors")
    if not majors:
        md.append("- none")
    else:
        for k, v in sorted(tally(majors).items()):
            sample = [r for r in majors if r["check"] == k]
            names = ", ".join("`"+r["object"]+"`" for r in sample[:8])
            extra = "…" if v > 8 else ""
            note = ""
            if k == "dot001_name":
                note = " These predate the #16 unique-name pass; the saved blend was not rebuilt."
            md.append(f"- **{k}**: {v} objects (e.g. {names}{extra}).{note}")
    md.append("")
    md.append("## Minors (summary)")
    for k, v in sorted(tally(minors).items()):
        md.append(f"- **{k}**: {v}")
    if unshared_groups:
        md.append("")
        md.append("### Unshared duplicate-mesh groups (instancing candidates, #7)")
        shown = [g for g in dup_groups if not g["shared_data"]]
        for g in shown[:25]:
            sample = ", ".join(g["objects"][:6])
            extra = f" +{g['objects_truncated']}" if g["objects_truncated"] else ""
            md.append(f"- {g['count']} copies / {g['unique_datablocks']} datablocks: {sample}{extra}")
        if len(shown) > 25:
            md.append(f"- … {len(shown) - 25} more groups (see JSON)")
    md.append("")
    text = "\n".join(md) + "\n"
    with open(md_path, "w") as f:
        f.write(text)

    mtime1 = os.path.getmtime(blend) if blend and os.path.isfile(blend) else None
    unchanged = (mtime0 == mtime1)
    print(text)
    print(f"MESHHEALTH status={status} blockers={len(blockers)} majors={len(majors)} minors={len(minors)} "
          f"dup_unshared={unshared_groups} seconds={elapsed:.2f} blend_unchanged={unchanged} "
          f"md={_repo_path(md_path)} json={_repo_path(json_path)}")
    if not unchanged:
        print("ERROR: blend mtime changed; script must not save", file=sys.stderr)
        return 2
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
