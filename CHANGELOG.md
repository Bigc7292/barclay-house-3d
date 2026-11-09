# CHANGELOG

## 2026-11-09 08:40 UTC+4 — perf/viewer-speed (live viewer speed fix)
Branch `perf/viewer-speed` (based on `feat/floorplan3d-2bed`). Deployed to production: dpl_8EvCfXUL1o2q4JfpdSKPzzHfEHxa → https://barclay-house-viewer.vercel.app

Root causes (main viewer, web/src/app.js):
- Redrew the full scene + 2048 PCF shadow pass every frame, even when idle (shadow pass doubled draw calls).
- 53 street-lamp PointLights always in every shader (intensity 0 in daytime still costs per pixel).
- Desktop logarithmicDepthBuffer + preserveDrawingBuffer (kills early-z, extra bandwidth).
- Phones: near 0.02 / far 5000 without log depth → z-fighting flicker ("glitchy"); DPR up to 2.
- Phone GLBs hero_m/context_m were NOT meshopt-compressed (4.7 MB context_m was bigger than desktop's).
- "Back to exterior" button visible on phones in exterior view (CSS override of .x).

Changes:
- Render on demand (OrbitControls change / fly / walk-look / autorotate / loads); skip when tab hidden.
- Shadow map static: autoUpdate=false, redrawn only on time-of-day or model load.
- DPR cap 1.5 phone / 2 desktop + adaptive step-down (to 1) if motion runs < ~30 fps.
- Dropped logDepth + preserveDrawingBuffer; near/far per mode (ext 0.1/2500, interior 0.03/300).
- Lamps: nearest 12 (desktop) / 6 (phone), lights only added at dusk/night.
- Phones load hero_mo.glb / context_mo.glb (dedup + meshopt medium of hero_m/context_m; validator 0 errors). Old files kept.
- Interior GLB loads after the exterior (or first with ?m=i).
- web/vercel.json cache headers (glb/hdr/js 1 h + SWR 7 d; html no-cache).
- floorplan3d/2bed.html: DPR cap 1.5 on phones, no preserveDrawingBuffer.

Measured (headless Chromium, SwiftShader software GL, so absolute FPS is low; compare ratios). Live before → live after:
- Desktop 1600x900: load 5.36 → 5.36 MB; ready 2.8 → 2.4 s (first view); orbit FPS 0.1 → 1.6; draws/frame 20 → 11; tris/frame 322k → 162k; idle redraws ~93/s → 0.
- Pixel 7 + 4x CPU throttle: load 4.02 → 2.97 MB; ready 5.6 → 2.8 s; FPS 0.3 → 3.8; canvas 824x1678 → 618x1258; idle redraws ~145/s → 0.
- Walk mode (phone): FPS 4.9 → 13.3. Console errors: 0 before and after.
