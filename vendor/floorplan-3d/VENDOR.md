# Vendored: wy51ai/floorplan-3d
- Source: https://github.com/wy51ai/floorplan-3d (commit 730ec0923a018fdf38b4687c5ef385c7dcac451f, 2026-10-02 +0800), demo https://wy51ai.github.io/floorplan-3d/
- Licence: MIT, (c) 2026 wuyi. See LICENSE in this folder (kept unchanged).
- Local change: index.html importmap now points at ../../web/floorplan3d/vendor/three-r160/ (three.js 0.160.0, MIT) instead of cdn.jsdelivr.net. Nothing else changed.
- Used for: interaction patterns only (flyToRoom/camTween easing, bindJoystick, stepWalk/blocked collision, pick→door.open toggle), re-implemented in web/floorplan3d/2bed.html. Its sample floor plan data is NOT used anywhere in Barclay.
