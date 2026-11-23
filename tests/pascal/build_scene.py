#!/usr/bin/env python3
"""Build the Two Bed in the *local* Pascal Editor (MCP on loopback, no account, no hosted MCP).

Walls come from tests/pascal/layout_pascal.json (independent plan-px trace).
Scale: metres_per_px = sqrt(63 m² / outline_px_area). Ceiling 3.0 m UNSOURCED.
"""
from __future__ import annotations
import json, math, os, time, urllib.request
from pathlib import Path

HOME = Path(os.environ.get("PASCAL_HOME", Path(__file__).parent / ".pascal"))
LAYOUT = Path(__file__).parent / "layout_pascal.json"
SOURCED_M2 = 63.0
CEIL_M = 3.0  # UNSOURCED

def shoelace(pts):
    n=len(pts)
    return abs(sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1] for i in range(n)))/2

class MCP:
    def __init__(self):
        self.token = (HOME/"run/mcp-token").read_text().strip()
        self.url = "http://127.0.0.1:" + str(json.loads((HOME/"run/mcp.json").read_text())["port"]) + "/mcp"
        self.session=None
        self.n=0
    def call(self, method, params=None, notify=False, timeout=60):
        self.n += 1
        body={"jsonrpc":"2.0","method":method}
        if not notify: body["id"]=self.n
        if params is not None: body["params"]=params
        req=urllib.request.Request(self.url, data=json.dumps(body).encode(), method="POST")
        req.add_header("Content-Type","application/json")
        req.add_header("Accept","application/json, text/event-stream")
        req.add_header("Authorization","Bearer "+self.token)
        if self.session: req.add_header("Mcp-Session-Id", self.session)
        try:
            r=urllib.request.urlopen(req, timeout=timeout)
        except Exception as e:
            raw=e.read() if hasattr(e,"read") else str(e).encode()
            return {"error":{"code":getattr(e,"code",None),"body":raw.decode()[:4000]}}
        sid=r.headers.get("mcp-session-id") or r.headers.get("Mcp-Session-Id")
        if sid: self.session=sid
        raw=r.read().decode(); data=None
        for line in raw.splitlines():
            if line.startswith("data:"):
                data=json.loads(line[5:].strip())
        return data or {}
    def tool(self, name, arguments=None, timeout=60):
        res=self.call("tools/call", {"name":name, "arguments":arguments or {}}, timeout=timeout)
        return res

def px_to_m_factory(outline, k):
    cx=sum(p[0] for p in outline)/len(outline)
    cy=sum(p[1] for p in outline)/len(outline)
    def conv(p):
        # Pascal plan is [x,z] metres. Image y down → z down would flip the plan;
        # flip y so the entrance (max y) is at +z? v4 used -y so north (small y) is +Y.
        # Use the same: x=(px-cx)*K, z=-(py-cy)*K so the plan is not mirrored vs #14.
        return [(p[0]-cx)*k, -(p[1]-cy)*k]
    return conv, (cx,cy)

def main():
    layout=json.loads(LAYOUT.read_text())
    outline=layout["outline"]
    A=shoelace(outline)
    K=math.sqrt(SOURCED_M2/A)
    to_m, origin = px_to_m_factory(outline, K)
    m=MCP()
    init=m.call("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"barclay-interior","version":"0"}})
    m.call("notifications/initialized", notify=True)
    print("init", "error" in init, bool(m.session))

    # New empty scene / project (local, private). create_project may want auth — try anyway, then clear_scene.
    out={}
    out["create_project"]=m.tool("create_project", {"name":"Barclay House Two Bed (local test)","isPrivate":True})
    print("create_project", json.dumps(out["create_project"])[:500])
    out["list_scenes_before"]=m.tool("list_scenes", {})
    out["clear"]=m.tool("clear_scene", {})
    print("clear", json.dumps(out["clear"])[:400])
    out["levels"]=m.tool("list_levels", {})
    print("levels", json.dumps(out["levels"])[:800])

    # If no building/level, add_level should create one
    levels_txt=json.dumps(out["levels"])
    if "level" not in levels_txt.lower() or "[]" in levels_txt:
        out["add_level"]=m.tool("add_level", {"name":"Ground","height":CEIL_M})
        print("add_level", json.dumps(out["add_level"])[:800])
        out["levels"]=m.tool("list_levels", {})
        print("levels2", json.dumps(out["levels"])[:800])

    # Parse level id from the tool result (content is often text JSON)
    def extract_text(res):
        if not res: return ""
        r=res.get("result") or res
        content=r.get("content") if isinstance(r,dict) else None
        if isinstance(content, list) and content:
            return "\n".join(c.get("text","") if isinstance(c,dict) else str(c) for c in content)
        return json.dumps(r)[:5000]

    # try to find a level id
    import re
    blob=extract_text(out["levels"]) + extract_text(out.get("add_level"))
    ids=re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", blob)
    print("uuids", ids)
    level_id=ids[0] if ids else None

    wall_ids=[]
    for w in layout["walls"]:
        a=to_m(w["a"]); b=to_m(w["b"])
        thick_m=(w.get("thickness_px") or 5)*K
        args={"start":a,"end":b,"thickness":thick_m,"height":CEIL_M}
        if level_id: args["levelId"]=level_id
        res=m.tool("add_wall", args)
        txt=extract_text(res)
        wids=re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", txt)
        wall_ids.append({"name":w["name"],"id":wids[-1] if wids else None,"resp":txt[:300]})
        print("add_wall", w["name"], "id", wall_ids[-1]["id"], "ok", "error" not in txt.lower())

    # Doors: for walls with gaps, place a door at the gap midpoint as t along the wall.
    doors=[]
    for w, meta in zip(layout["walls"], wall_ids):
        if not w.get("gaps") or not meta["id"]:
            continue
        ax,ay=w["a"]; bx,by=w["b"]
        L=math.hypot(bx-ax, by-ay) or 1
        for g in w["gaps"]:
            mid=(g[0]+g[1])/2
            t=max(0.02, min(0.98, mid/L))
            width_m=(g[1]-g[0])*K
            args={"wallId":meta["id"],"t":t,"width":width_m,"height":2.1}  # 2.1 m door height: modelling value, UNSOURCED (same family as #14)
            res=m.tool("add_door", args)
            doors.append({"wall":w["name"],"t":t,"width_m":width_m,"resp":extract_text(res)[:400]})
            print("add_door", w["name"], "t", round(t,3), "w", round(width_m,3), doors[-1]["resp"][:200])

    out["save"]=m.tool("save_scene", {"name":"barclay-twobed-pascal","saveMode":"checkpoint","includeCurrentScene":True})
    print("save", extract_text(out["save"])[:800])
    out["export_json"]=m.tool("export_json", {"pretty":True})
    ej=extract_text(out["export_json"])
    Path(__file__).parent.joinpath("out/pascal_scene.json").write_text(ej if ej.startswith("{") or ej.startswith("[") else json.dumps(out["export_json"], indent=2))
    print("export_json bytes", len(ej))
    out["export_glb"]=m.tool("export_glb", {})
    print("export_glb", extract_text(out["export_glb"])[:800])
    out["list_scenes"]=m.tool("list_scenes", {})
    print("list_scenes", extract_text(out["list_scenes"])[:800])
    out["verify"]=m.tool("verify_scene", {})
    print("verify", extract_text(out["verify"])[:800])
    report={"K":K,"origin_px":origin,"ceil_m_UNSOURCED":CEIL_M,"walls":wall_ids,"doors":doors,
            "save":extract_text(out["save"])[:1000],
            "export_glb":extract_text(out["export_glb"])[:1000],
            "list_scenes":extract_text(out["list_scenes"])[:1000]}
    Path(__file__).parent.joinpath("out/pascal_build.json").write_text(json.dumps(report, indent=2))
    print("done")

if __name__=="__main__":
    main()
