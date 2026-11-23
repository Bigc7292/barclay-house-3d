# tests/streetwater - x_tricks #9 street life + #10 canal water (2026-11-09)
Blender 4.2.3 Cycles CPU, 1280x720, 32 spp + denoise, locked cameras (Cam_Street; Cam_Canal_test from canal_cam.json; Cam_Life_test fixed in stills.py).
- base_*.png = original scene; before_*.png = terrain cut only; after_*.png = cut + Noise->Bump ripple + street life (t=3 s)
- before_life/after_life = Cam_Life_test without/with actors at t=5 s (cars on Whitworth St W, train on the viaduct)
- fly_life/, fly_life.mp4, fly_life_sheet.png = `flythrough.py --life` smoke run (320x180, 2 fps, 8 spp)
- out/ = test export of cut+ripple scene (export_glb.py BOUT=...), make_mobile.sh + validate.sh PASS (tests/validate_20261109_0743.jsonl). Full surroundings GLB (34.1 MB) deleted after validation (reproducible).
- web_*.png / web_check*.json = headless Chromium (SwiftShader) loads: 0 console errors in every run. "aftercut" = branch viewer + test-export surroundings (canal visible); "after" = branch viewer + current web/context.glb (canal still under terrain until re-export).
Re-create test blends: cp out/barclay_scene.blend tests/streetwater_copy.blend; blender -b -y tests/streetwater_copy.blend -P tests/streetwater/prep_blends.py (copies deleted: 3 x 50 MB).
