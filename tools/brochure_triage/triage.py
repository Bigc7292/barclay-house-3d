"""Brochure page triage: label every page (floor_plan / exterior / interior / other) and read printed
room sizes from plan images. Free, CPU-only, no API keys, nothing leaves the machine.

Output is a PROPOSAL for human review (status "proposed_needs_human_review"). It never edits the
project's canonical/approved files.

  python tools/brochure_triage/triage.py <pdf> [<pdf> ...] --out <dir>
      [--classifier auto|clip|local] [--ocr auto|rapidocr|tesseract|textlayer] [--dpi 200]

classifier auto = CLIP zero-shot (open_clip ViT-B-32/laion2b) when installed, else the local
keyword/image-stats classifier (port of offplan-reconstruct classify.ts). Both apply the
empty-page rule (little text + flat colour -> other).
ocr auto = RapidOCR (PP-OCR ONNX) when installed, else tesseract when on PATH, else the PDF
text layer only. The PDF text layer is always read too; results are merged and de-duplicated.
"""
import argparse, io, json, os, re, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
import pymupdf
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import local_classify  # noqa: E402

CLASSES = ["floor_plan", "exterior", "interior", "other"]
PROMPTS = {
    "floor_plan": ["an architectural floor plan drawing of a house", "a black and white 2D floor plan with rooms and walls", "a brochure page showing villa floor plans for ground and first floor"],
    "exterior": ["an exterior 3D render of a modern villa facade", "a photo of the outside of a townhouse building with sky and garden", "an architectural rendering of a house exterior front view"],
    "interior": ["an interior render of a living room, bedroom, kitchen or bathroom", "a photo inside a luxury home with furniture", "an interior design visualization of a room"],
    "other": ["a brochure page with mostly text", "a map or aerial masterplan of a community", "a lifestyle photo of people, nature or plants", "a logo on a plain background", "an amenity photo of a swimming pool, lagoon or park", "a page of icons and infographics"],
}
DIM = re.compile(r"(\d{1,2}[.,]\d{1,2})\s*m?\s*[x×X*]\s*(\d{1,2}[.,]\d{1,2})(?:\s*m\b)?|(\d{4})\s*[x×X]\s*(\d{4})")  # 4.00×6.00, 9.50m x 2.40m, 3600x4200 (mm)
ROOM = local_classify.ROOM


def page_stats(img: Image.Image) -> dict:
    a = np.asarray(img.convert("RGB").resize((128, 128)), dtype=np.float32)
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    g = a.mean(axis=2)
    edges = (np.abs(np.diff(g, axis=1)) > 40).mean()
    return {"white_ratio": float((mn > 225).mean()), "saturation": float(sat.mean()),
            "color_std": float(a.reshape(-1, 3).std(axis=0).mean()), "edge_density": float(edges), "gray_std": float(g.std())}


def empty_page(text: str, st: dict) -> bool:
    """Existing offplan-reconstruct rule (near-empty divider -> other), widened to flat coloured dividers."""
    return len(re.sub(r"\s", "", text)) < 40 and (st["white_ratio"] > 0.8 or st["gray_std"] < 22)


class Clip:
    def __init__(self):
        import torch, open_clip
        torch.set_num_threads(os.cpu_count() or 4)
        self.torch = torch
        self.model, _, self.pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        self.model.eval(); tok = open_clip.get_tokenizer("ViT-B-32")
        with torch.no_grad():
            self.te = []
            for c in CLASSES:
                e = self.model.encode_text(tok(PROMPTS[c])); self.te.append(e / e.norm(dim=-1, keepdim=True))

    def __call__(self, img):
        with self.torch.no_grad():
            ie = self.model.encode_image(self.pre(img).unsqueeze(0)); ie = ie / ie.norm(dim=-1, keepdim=True)
            sims = {c: float((ie @ e.T).max()) for c, e in zip(CLASSES, self.te)}
        return max(sims, key=sims.get), sims


def make_ocr(kind):
    if kind in ("auto", "rapidocr"):
        try:
            from rapidocr import RapidOCR
            eng = RapidOCR()
            def run(img):
                r = eng(np.asarray(img.convert("RGB")))
                return [(t, [float(v) for v in np.asarray(b).reshape(-1, 2).min(0).tolist() + np.asarray(b).reshape(-1, 2).max(0).tolist()], float(s))
                        for t, b, s in zip(r.txts or [], r.boxes if r.boxes is not None else [], r.scores or [])]
            return "rapidocr", run
        except ImportError:
            if kind == "rapidocr": raise
    if kind in ("auto", "tesseract") and shutil.which("tesseract"):
        def run(img):
            p = "/tmp/_triage_ocr.png"; img.save(p)
            out = subprocess.run(["tesseract", p, "stdout", "--psm", "11", "tsv"], capture_output=True, text=True, timeout=180).stdout
            rows = []
            for line in out.splitlines()[1:]:
                c = line.split("\t")
                if len(c) >= 12 and c[11].strip() and float(c[10]) > 45:
                    l, t, w, h = map(float, c[6:10]); rows.append((c[11], [l, t, l + w, t + h], float(c[10]) / 100))
            return rows
        return "tesseract", run
    return "textlayer", None


def join_lines(items):
    """Merge '5.95 X' + '4.97' style wrapped dimension labels into one item."""
    items = sorted(items, key=lambda x: (x[1][1], x[1][0])); out, used = [], set()
    for i, (t, b, s) in enumerate(items):
        if i in used: continue
        if re.search(r"\d[.,]\d{1,2}\s*m?\s*[x×X]\s*$", t):
            h = b[3] - b[1]
            for j in range(i + 1, len(items)):
                t2, b2, s2 = items[j]
                if j not in used and 0 <= b2[1] - b[3] < 1.5 * h and abs((b2[0] + b2[2]) / 2 - (b[0] + b[2]) / 2) < 3 * h and re.match(r"^\s*\d{1,2}[.,]\d{1,2}", t2):
                    used.add(j); t, b, s = f"{t} {t2}", [min(b[0], b2[0]), b[1], max(b[2], b2[2]), b2[3]], min(s, s2); break
        out.append((t, b, s))
    return out


def room_dims(items, page_w, page_h):
    """Pair each dimension string with the nearest room-name label above or left of it."""
    items = join_lines(items); names = [(t, b) for t, b, _ in items if ROOM.search(t) and not DIM.search(t)]
    found = []
    for t, b, s in items:
        for m in DIM.finditer(t):
            a, c = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
            label = re.sub(DIM, "", t).strip(" -:") if ROOM.search(t) else None
            if not label:
                cx, top, h = (b[0] + b[2]) / 2, b[1], max(b[3] - b[1], 1)
                cand = [(abs(cx - (nb[0] + nb[2]) / 2) + 2 * (top - nb[3]), nt) for nt, nb in names if -0.5 * h <= top - nb[3] <= 4 * h and abs(cx - (nb[0] + nb[2]) / 2) < 6 * h]
                label = min(cand)[1] if cand else None
            found.append({"room_guess": label, "dims": f"{a.replace(',', '.')} × {c.replace(',', '.')}", "ocr_conf": round(s, 2),
                          "bbox_norm": [round(b[0] / page_w, 4), round(b[1] / page_h, 4), round(b[2] / page_w, 4), round(b[3] / page_h, 4)]})
    return found


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pdfs", nargs="+"); ap.add_argument("--out", required=True)
    ap.add_argument("--classifier", default="auto", choices=["auto", "clip", "local"]); ap.add_argument("--ocr", default="auto", choices=["auto", "rapidocr", "tesseract", "textlayer"])
    ap.add_argument("--dpi", type=int, default=200); a = ap.parse_args()
    t0 = time.time(); clip = None; cls_name = "local"
    if a.classifier in ("auto", "clip"):
        try: clip = Clip(); cls_name = "clip:ViT-B-32/laion2b_s34b_b79k"
        except ImportError:
            if a.classifier == "clip": raise
    ocr_name, ocr = make_ocr(a.ocr); t_load = time.time() - t0
    result = {"status": "proposed_needs_human_review", "classifier": cls_name, "ocr": ocr_name, "sources": [], "pages": [], "plan_dims": []}
    t_cls = t_ocr = 0.0
    for pdf in a.pdfs:
        doc = pymupdf.open(pdf); result["sources"].append(str(pdf))
        for i, p in enumerate(doc, 1):
            t1 = time.time(); text = p.get_text()
            z = 448 / max(p.rect.width, p.rect.height)
            img = Image.open(io.BytesIO(p.get_pixmap(matrix=pymupdf.Matrix(z, z)).tobytes("png"))).convert("RGB")
            st = page_stats(img)
            if empty_page(text, st): label, scores, how = "other", {}, "empty-page rule"
            elif clip: label, scores = clip(img); how = "clip"
            else: label, scores = local_classify.classify(text, st); how = "local"
            t_cls += time.time() - t1
            result["pages"].append({"source": Path(pdf).name, "page": i, "label": label, "method": how, "scores": {k: round(v, 3) for k, v in scores.items()}})
            if label != "floor_plan": continue
            t2 = time.time()
            # text layer first (vector labels), then OCR of the rendered page (labels baked into images)
            lines = {}
            for w in p.get_text("words"):
                lines.setdefault((w[5], w[6]), []).append(w)
            tl = [(" ".join(x[4] for x in ws), [min(x[0] for x in ws), min(x[1] for x in ws), max(x[2] for x in ws), max(x[3] for x in ws)], 1.0) for ws in lines.values()]
            dims = [dict(d, method="textlayer") for d in room_dims(tl, p.rect.width, p.rect.height)]
            if ocr:
                pix = p.get_pixmap(dpi=a.dpi); big = Image.open(io.BytesIO(pix.tobytes("png")))
                seen = {(d["dims"], round(d["bbox_norm"][0], 2), round(d["bbox_norm"][1], 2)) for d in dims}
                for d in room_dims(ocr(big), big.width, big.height):
                    if (d["dims"], round(d["bbox_norm"][0], 2), round(d["bbox_norm"][1], 2)) not in seen: dims.append(dict(d, method=ocr_name))
            t_ocr += time.time() - t2
            result["plan_dims"] += [dict(d, source=Path(pdf).name, page=i) for d in dims]
    result["timing_s"] = {"model_load": round(t_load, 1), "classify": round(t_cls, 1), "plan_ocr": round(t_ocr, 1), "total": round(time.time() - t0, 1)}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "triage.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    md = ["# Brochure triage (PROPOSED - needs human review)", f"classifier: {cls_name} | ocr: {ocr_name} | {result['timing_s']}", "", "| source | page | label | method |", "|---|---|---|---|"]
    md += [f"| {x['source']} | {x['page']} | {x['label']} | {x['method']} |" for x in result["pages"]]
    md += ["", "## Room sizes read from plans (check against the plan before use)", "| source | page | room (guess) | size | method | conf |", "|---|---|---|---|---|---|"]
    md += [f"| {d['source']} | {d['page']} | {d['room_guess'] or '?'} | {d['dims']} | {d['method']} | {d['ocr_conf']} |" for d in result["plan_dims"]]
    (out / "review.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"pages": len(result["pages"]), "plan_pages": sum(x["label"] == "floor_plan" for x in result["pages"]), "room_sizes": len(result["plan_dims"]), **result["timing_s"], "classifier": cls_name, "ocr": ocr_name}))


if __name__ == "__main__":
    main()
