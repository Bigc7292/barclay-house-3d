# Barclay House — Interior bot backup

Backup of the Interior / Two Bed viewer work for Colin (Driven Data Dynamics).

## Live site

- Viewer: https://barclay-house-viewer.vercel.app  
- Walk mode (Floorplan 3D): https://barclay-house-viewer.vercel.app/floorplan3d/2bed.html  
- Vercel project: `barclay-house-viewer` (production)

## Placement plan

- Cursor Page: [Barclay House – Interior Placement Plan (Phase 1)](https://cursor.com/canvas/store-d06abf8d-aea3-48db-a461-1bb0fe77ba8e/93a50d88-b7ed-4a31-a6b5-b1b004cf5595) (private to owner)

## What’s in this branch

| Path | Contents |
|------|----------|
| `interior/` | Research (`FINDINGS.md`), `critic_log.md`, Blender build scripts (`build_twobed_v4.py` current), textures, plan extracts, DWG folder, `das_unit_areas.txt`, live bake outputs |
| `web/` | three.js viewer (`src/app.js` → bundled `app.js`), GLBs (hero/context/twobed + mobile/`_mo` variants), `floorplan3d/` Walk mode (MIT notice under `vendor/floorplan-3d/LICENSE`), `deploy.sh`, `vercel.json` |
| `web/shots/` | Playwright / Blender verification stills (r3–r10, dining checks) |
| `refs/critic1/` | Critic reference images when present |

**Not** the exterior bot’s large `/out/` exports or `barclay-house-archive` (that repo’s `main` drives Vercel — do not push there).

## How to rebuild

### 1. Blender Two Bed (baked lightmap)

```bash
# bpy in ~/bvenv (pip bpy 5.x)
cd /workspace/barclay/interior
~/bvenv/bin/python build_twobed_v4.py --noshots --res=3072 --bs=160 --expo=1.35
# writes live/twobed_raw.glb + bake_atlas.png
```

Optional stills: drop `--noshots`, or use `--only v3_living` etc.

### 2. Compress for web

```bash
cd /workspace/barclay/web
npx -y @gltf-transform/cli@4 optimize ../interior/live/twobed_raw.glb twobed.glb \
  --compress meshopt --texture-compress webp --texture-size 3072 \
  --simplify false --join false --flatten false
npx -y @gltf-transform/cli@4 optimize ../interior/live/twobed_raw.glb twobed_m.glb \
  --compress meshopt --texture-compress webp --texture-size 2048 \
  --simplify false --join false --flatten false
# keep Ceiling_BAKED separate: --join false --flatten false is required for dollhouse lid hide
```

Re-copy exterior assets (read-only from exterior bot): `bash prep_ext.sh` (and use exterior bot’s `out/mobile/*_mobile.glb` → `hero_m` / `context_m`, then meshopt `hero_mo` / `context_mo` if regenerating).

### 3. Bundle viewer

```bash
cd /workspace/barclay/web/src
npx esbuild app.js --bundle --minify --format=iife --outfile=../app.js
# bump ?v= in index.html
```

### 4. Vercel deploy (connector)

Project `barclay-house-viewer`, **production**, files at **site root** (not under `vercel-live/`). See `web/deploy.sh` for the file list and sha/size helper.

Typical set: `index.html`, `app.js`, `apt02_fp.png`, `vercel.json`, `hero.glb`, `context.glb`, `hero_m.glb`, `context_m.glb`, `hero_mo.glb`, `context_mo.glb`, `twobed.glb`, `twobed_m.glb`, `env.hdr`, `env_m.hdr`, `floorplan3d/**`, `vendor/floorplan-3d/LICENSE`.

Upload large files via `upload_file` (sha1 + size), then `create_deployment` with ≤4 `$file:` args. Do **not** push this branch to a repo whose `main` is the Vercel Git integration for the live site.

## Open issues (interior)

- Bathroom: basin/vanity/mirror often clipped at frame edge; shower head not always in shot.
- Bedrooms: headboards sit in front of windows; wardrobes often out of frame; ~3.2 m room depth limits “3 m pull-back”.
- Bake: wall/ceiling seams, bright washed walls, pale art, small white dots at downlight positions.
- Dollhouse: sky backdrop panels can stick above wall tops.
- Layout scaled from plan image (approximate); 3.0 m ceiling **UNSOURCED**; window positions / exterior view **UNSOURCED**; furniture illustrative.
- Storage shelving is a plain stand-in block; no balcony/garden (NOT FOUND).
- Mobile UI: some presets / Back to exterior sit off-screen until horizontal scroll.
- Exterior facade defects belong to the exterior bot (ground-floor colour discontinuity, missing ornament, etc.).

## Licenses

- three.js r160 vendored under `web/floorplan3d/vendor/three-r160/` (MIT).
- Floorplan 3D interaction patterns: MIT, see `web/vendor/floorplan-3d/LICENSE` (wy51ai/floorplan-3d).
