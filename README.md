# Barclay House 3D (35 Whitworth St W, Manchester M1 5NG)
Photorealistic exterior + surroundings model (Blender -> GLB) and web viewer (`web/`, deployed at https://barclay-house-viewer.vercel.app). Interior/apartments in `interior/`.
## Resume
1. Read `AGENTS.md` (= CLAUDE.md = GROK.md) first: hard rules (free only, no estimates, sourced facts), fixed pipeline, lessons.
2. Then `critic_log.md`, `tricks_register.md`, `x_tricks.md`, `optimizer_log.md`, `PLAN.md`, `TOOLS.md`.
3. Pipeline: source facts -> build one change set (Blender scripts) -> render locked camera + `ref_check.py` -> critic round -> export, `./make_mobile.sh`, `./validate.sh` (must PASS) -> redeploy viewer -> `./backup.sh "msg"`.
Layout: `out/` exports (GLB/FBX/renders), `out/mobile/` phone GLBs, `web/` viewer, `lidar/` EA LIDAR, `textures/`, `refs/` reference photos, `docs/`, `tests/` experiments. See SETUP.md.
