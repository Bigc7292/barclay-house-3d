# Barclay House: reference-checklist-gate
Date: 2026-11-09 · Source note: notes/2119285434060603642.md
Status: proposed · Owner: Barclay House 3D (interior variant: Barclay House Interior) · Briefed: priority-true message to Barclay House 3D (queued in report; certify before adopting)

WHAT: machine-scored "reference checklist" gate from the Claude+Blender 'cutaway' workflow (post https://x.com/i/status/2119285434060603642 → article https://x.com/rektwild/status/2119281630632145093; Blender bridge https://github.com/ahujasid/mcp-for-blender MIT): each locked-camera render is scored per named element yes/partial/no against refs/ crops, plus a pixel-statistics threshold that must pass before a round can be accepted; explicit "done criteria".
WHY: today camera_match.py + ref_check.py give one aggregate edge/colour score and critic_log.md lists defects in prose (R3/R4 "soot and weathering" stand-in, parapet reads salmon). A per-element pass/fail list makes each fix targeted and makes "done" objective. Head-to-head: ref_check score = global, cheap; checklist = element-level, auditable → hybrid, keep ref_check. Lenses: quality gain, efficiency gain (fewer blind rounds), viz none, UX none.
HOW:
1) Create refs/checklist_<cam>.json per locked camera: rows {element, ref_crop, rule, status}. Elements only from sourced reference photos (NO ESTIMATES): e.g. cornice, oriel, doorcase, parapet, viaduct arch, canal edge.
2) New checks.py (numpy/Pillow, no new deps): per row compute stats on the render crop vs ref crop (dark-pixel share, mean hue/value, edge density); thresholds: pass if ≥80% of the reference stat (the cutaway figure, tune on R4), partial 60–80%, no <60%.
3) Output out/checklist_<cam>.md with yes/partial/no per row; gate = no "no" rows and ≤2 "partial"; the round stops for human approval at round 2 (existing one-fix-per-pass rule, x_tricks #1).
4) Done criteria block appended to AGENTS.md step 6: measured bounds/tris within budget, checklist gate pass, human saw one multi-angle view, no stray .001 objects.
5) Interior bot: rows come from the approved CAD plan (room count/sizes, door positions), not images.
CHANGES: new checks.py + refs/checklist_*.json; ref_check.py call at end of run; critic_log.md entry; AGENTS.md step 6 done-criteria. Owner: Barclay House 3D.
EFFORT S · RISK low (read-only analysis of renders) · ROLLBACK delete checks.py call; ref_check unchanged.
LICENSE: Blender GPL, mcp-for-blender MIT, numpy/Pillow permissive. The 'cutaway' skill repo itself is unverified/unlicensed → NOT used, method re-implemented.
COST: £0 (ChatGPT reference image and LUFS audio steps not needed).
SUCCESS: gate runs on street + viaduct cams; fails the pre-R4 parapet-salmon case and passes R4 values; critic_log cites checklist rows instead of prose.
