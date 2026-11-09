# brochure_triage — free page classifier (CLIP) + room-size reader (RapidOCR)

Added 2026-11-09 on a separate feature branch at Colin's request (pt20u). It is additive: no existing
script, manifest, canonical/approved file or requirements file was changed. Output is a **proposal for
human review** (`status: proposed_needs_human_review`); it never writes into canonical/approved data.

## Use
```
pip install -r tools/brochure_triage/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python tools/brochure_triage/triage.py <brochure.pdf> [more.pdf] --out <dir>      # writes triage.json + review.md
python tools/brochure_triage/eval/selftest.py                                     # no-model unit checks
python tools/brochure_triage/eval/eval.py <gt.json> <dir>/triage.json [--baseline <offplan ingest-test txt>]
```
- `--classifier auto` (default): CLIP zero-shot (open_clip ViT-B-32 / laion2b, MIT) on CPU. Falls back to
  `local` = Python port of offplan-reconstruct's keyword + image-stats classifier when torch/open_clip are
  missing. Both apply the empty-page rule (under 40 characters of text and a flat colour -> `other`).
  This tool never calls a paid model; an upstream vision-model key (offplan-reconstruct) still takes priority there.
- `--ocr auto` (default): PDF text layer + RapidOCR (PP-OCR ONNX, Apache-2.0) on plan pages, merged and
  de-duplicated. Falls back to tesseract if on PATH, else text layer only (`--ocr textlayer`).
- Dimension formats: `4.00×6.00`, `5.95 X / 4.97` (wrapped), `9.50m x 2.40m`, `4225x5135` (mm).
  Each size is paired with the nearest room-name label above it (`room_guess`, can be empty).
- Cost: zero. First run downloads ~600 MB CLIP weights + ~15 MB OCR models (free, cached). CPU only, ~1 GB RAM.

## Barclay House results (2026-11-09)
Sources: `docs/s4c5tvdfq0syslhg.pdf` (Design and Access Statement, 41 pages) + `refs/loopnet_Barclay_House_Plans.pdf` (4 pages).
Barclay has no sales brochure; these are the closest documents with plans, CGIs and photos. 8 genuinely mixed DAS pages
(elevation drawings with photos, precedent collages, cover) are excluded from scoring (`eval/gt_barclay.json`).
Before = offplan-reconstruct `main` pipeline (`ingest-test.ts`, no model key); after = `triage.py` defaults.

| | Before | After (CLIP + RapidOCR) | Fallback (local + text layer) |
|---|---|---|---|
| Pages correct (37 scored) | 22/37 | **31/37** | 23/37 |
| Floor plans | 6/8, 5 false | **8/8**, 1 false | 6/8, 4 false |
| Exteriors (photos/CGIs) | 1/9 | 5/9, 1 false | 1/9 |
| Room sizes read | 1 (text layer) | 3 (2 by RapidOCR: WC 1500×2972, BEDROOM 1 4225×5135 on DAS p32, both correct by eye) | 1 |
| Runtime | 59 s (full ingest, both PDFs) | 38.6 s (warm) | 1.1 s |

Notes: the DAS exterior misses are small photos on text-heavy pages (p4, p5, p22, p36). CLIP sees the whole page as text.
UK planning drawings mostly print areas (m²), not room sizes, so there are few sizes to read. RapidOCR missed `ES 2235x2100` on p32.
Existing check `./validate.sh`: **PASS before and after** (reports in `results/2026-11-09/existing_validate_*.jsonl`).
`tests/floorplan3d/check.cjs` not run: it writes screenshots into `/workspace/barclay` (another bot's live worktree).
Per AGENTS.md, bots normally push to `barclay`; this feature branch was made separately on purpose (Colin: separate branches). No CHANGELOG.md edit, to avoid merge conflicts.
