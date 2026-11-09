# Off Plan Reconstruct: cc0-kit-normalizer
Date: 2026-11-07 · Source note: notes/2117798412703953143.md
Status: proposed · Briefed: nobody (no Off Plan Reconstruct agent)
Decisions: grounded against profiles/offplan.md (main unchanged since 2026-09-24 20:33 UTC+4)

WHAT: AnyKit's "art department" checks (https://github.com/apekshik/anykit, MIT; KIT.md) applied to free CC0 furniture instead of paid generators: one style brief, real-world scale, bottom-centre origin, front −Y, glass transmissive, triangle budget + LOD1, lineup render with scale bar, critic pass.
WHY: profile gap "furniture = proxies"; backlog #5 (Poly Haven/Kenney CC0 furniture) and #16 (Blender MCP dressing) mix assets from different sources → wrong sizes, random facing, style drift (AnyKit reply: "unit scale and PBR maps still drift"). AnyKit itself costs ≈$25/kit (fal + Meshy + Tripo + Claude) → blocked: cost; the method is free. Head-to-head: AnyKit generation = better cohesion, paid; CC0 + normaliser = slightly less cohesive, £0, licence-clean → hybrid (method only). Lenses: quality gain, viz gain, efficiency gain (LOD1 lighter GLBs), UX none.
HOW:
1) scripts/blender/kit_normalize.py (Blender -b -P): for each CC0 asset in assets/furniture/: apply transforms; scale so height (or W×D for boxy items) = value from a small `furniture_dims.json` (sourced typical dims, e.g. BS/IKEA spec pages, URL per row); origin to bottom-centre; rotate front to −Y; glass materials → transmission 1.0.
2) Decimate to a per-category triangle budget; LOD1 at ~25%; textures ≤2K (gltf-transform resize).
3) Shared materials: map wood/fabric/metal to a 6-material palette so gltf-transform dedup merges them (cuts texture budget).
4) lineup.py renders all items in a row with a 1 m scale bar → out/kit_lineup.png; reviewer (human or #15 render-review) flags outliers; fix and re-run.
5) Export per-item GLB + kit.json {id, source URL, licence, dims, tris}; reconstruct/#16 dressing picks from kit.json only.
CHANGES (owner: whoever picks up Off Plan — no agent exists): new scripts/blender/kit_normalize.py, lineup.py, data/furniture_dims.json, assets/furniture/kit.json; src/lib/materials.ts (palette map); dressing in #16 reads kit.json.
PIPELINE FIT: asset prep before #5/#16 dressing; outputs flagged "inferred" like all furniture; dossierHash unaffected.
EFFORT S-M · RISK low (offline asset prep) · ROLLBACK keep proxies (current behaviour).
LICENSE: AnyKit MIT (method/reference only); Poly Haven/Kenney CC0; Blender GPL (outputs free). Do not use Meshy/Tripo outputs.
COST: £0.
SUCCESS: lineup shows all items at correct relative scale (bed ≈2.0 m, door 2.04 m) and facing −Y; GLB furniture tris −60%+ via LOD1 in walk mode; validator 0 errors.
