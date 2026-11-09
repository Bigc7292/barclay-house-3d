"""Before/after scorer for brochure_triage.
  python tools/brochure_triage/eval/eval.py <ground_truth.json> <triage.json> [--baseline <offplan ingest-test output.txt> ...]
Baseline = text printed by offplan-reconstruct `npx tsx scripts/ingest-test.ts <pdf>` (its local classifier)."""
import json, re, sys, argparse
MAP = {"unit_plan": "floor_plan", "typical_floor": "floor_plan", "furniture_layout": "floor_plan", "cgi_exterior": "exterior", "elevation": "exterior", "cgi_interior": "interior"}

def gt_pages(gt):
    out = {}
    for src, g in gt["sources"].items():
        for p in range(1, g["pages"] + 1):
            if p in g.get("exclude", []): continue
            out[(src, p)] = next((c for c in ("floor_plan", "exterior", "interior") if p in g.get(c, [])), "other")
    return out

def score(gt, pred):
    res = {}
    for c in ("floor_plan", "exterior", "interior"):
        n = sum(v == c for v in gt.values())
        if n == 0 and not any(pred.get(k) == c for k in gt): continue
        tp = sum(1 for k, v in gt.items() if v == c and pred.get(k) == c); fp = sum(1 for k, v in gt.items() if v != c and pred.get(k) == c)
        res[c] = f"{tp}/{n} found, {fp} false"
    res["accuracy"] = f"{sum(pred.get(k) == v for k, v in gt.items())}/{len(gt)}"
    return res

def baseline(files, names):
    pred = {}
    for f, src in zip(files, names):
        for line in open(f):
            m = re.match(r"^p(\d+) (\S*)", line)
            if m: pred[(src, int(m.group(1)))] = next((l for l in (MAP.get(x, "other") for x in m.group(2).split(",")) if l != "other"), "other")
    return pred

def norm(d):
    a, b = re.findall(r"\d+(?:\.\d+)?", d)[:2]; return frozenset([f"{float(a):.2f}", f"{float(b):.2f}"])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gt"); ap.add_argument("triage"); ap.add_argument("--baseline", nargs="*", default=[]); a = ap.parse_args()
    gt = json.load(open(a.gt)); t = json.load(open(a.triage)); g = gt_pages(gt)
    after = {(x["source"], x["page"]): x["label"] for x in t["pages"]}
    out = {"after": score(g, after), "after_errors": [f"{k[0][:12]} p{k[1]}: truth {v}, got {after.get(k)}" for k, v in g.items() if after.get(k) != v]}
    if a.baseline: out["before"] = score(g, baseline(a.baseline, list(gt["sources"])))
    out["room_sizes_after"] = len(t["plan_dims"]); out["room_sizes_with_room_name"] = sum(1 for d in t["plan_dims"] if d["room_guess"])
    if "dims_truth" in gt:  # list of {"page", "label", "dims"} transcribed by hand
        found = {}
        for d in t["plan_dims"]: found.setdefault(d["page"], []).append(norm(d["dims"]))
        hit = [x for x in gt["dims_truth"] if norm(x["dims"]) in found.get(x["page"], [])]
        out["hand_transcribed_sizes_recovered"] = f"{len(hit)}/{len(gt['dims_truth'])}"
        truth = {(x["page"], norm(x["dims"])) for x in gt["dims_truth"]}
        extra = [d for d in t["plan_dims"] if (d["page"], norm(d["dims"])) not in truth]
        out["sizes_not_in_hand_transcript"] = len(extra)
    print(json.dumps(out, indent=1, ensure_ascii=False))
