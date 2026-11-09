# Off Plan Reconstruct: walk-ux-room-flyto
Date: 2026-11-07 · Source note: notes/2117486428645138512.md (+ 2117679955241046376 door-open, 2117245383009050867 build-up reveal)
Status: proposed · Briefed: nobody (no Off Plan Reconstruct agent)
Decisions: grounded against profiles/offplan.md (main unchanged since 2026-09-24 20:33 UTC+4)

WHAT: buyer-friendly viewer ergonomics from Floorplan 3D (https://github.com/wy51ai/floorplan-3d, MIT, 3.6k★, live https://wy51ai.github.io/floorplan-3d/): room list → camera flies to room; first-person walk with virtual joystick on touch; click doors to open; full-height / cut-away wall toggle; room areas panel.
WHY: profile — Viewer3D.tsx has dollhouse/walk/plan/measure but walk is desktop-style and there is no per-room navigation; share page app/view/[id] is what buyers open on phones. Dossier already has rooms (schema.ts) and doors (reconstruct.ts), so no new data is needed. Head-to-head: Off Plan wins on evidence/determinism; Floorplan 3D wins on phone UX → hybrid (port patterns, keep dossier). Lenses: UX gain, viz gain (cut-away), efficiency none, quality none.
HOW:
1) Viewer3D.tsx: `flyToRoom(roomId)` — room bbox from reconstruct.ts output → tween camera position/target (drei CameraControls `fitToBox`, already a drei dep).
2) New RoomList.tsx beside ModelExplorer: room name, area m² (polygon area from schema.ts room geometry), evidence badge (cited/inferred); click → flyToRoom. Areas feed backlog #28 finish schedule (area × finish ×1.05 waste, Floorplan 3D convention).
3) Walk mode on touch: left-thumb virtual joystick (plain pointer events, ~80 lines) + drag-to-look; keep PointerLockControls/WASD on desktop; wall collision against reconstructed wall segments (2D segment test, as Floorplan 3D does).
4) Doors: each door node from export-glb.ts gets a pivot at its hinge; click/E toggles a 90° tween (no physics; PhysAg3D blocked: cost). Doors flagged inferred stay closed by default.
5) Cut-away walls: toggle lowering wall height to 1.0 m (shader clip plane or scaled wall meshes) for dollhouse view.
6) Optional (from Roomtone): share-page intro that reveals shell → rooms → furniture in 2 s (opacity/scale stagger), skippable.
CHANGES (owner: whoever picks up Off Plan — no agent exists): src/components/Viewer3D.tsx, new src/components/RoomList.tsx, src/lib/geom.ts (polygonArea, segment collision), src/lib/export-glb.ts (door pivot nodes), app/view/[id]/page.tsx, scripts/acceptance.ts (+ checks below).
PIPELINE FIT: viewer layer only, after export; dossierHash and reconstruct.ts untouched.
EFFORT S-M · RISK low (UI only; door pivots change GLB node tree → keep names stable for #2 instancing) · ROLLBACK revert components; door pivots behind flag `DOOR_PIVOTS=1`.
LICENSE: Floorplan 3D MIT — patterns re-implemented in TS; if any snippet is copied keep MIT notice. three/drei MIT.
COST: £0.
SUCCESS: on a phone (Playwright mobile emulation + #15 tour capture) user reaches every room in ≤2 taps; joystick walk ≥30 fps on mid GPU tier; acceptance 13/13 still passing + new check "every room has area and flyTo target".
