# Brochure triage (PROPOSED - needs human review)
classifier: clip:ViT-B-32/laion2b_s34b_b79k | ocr: rapidocr | {'model_load': 3.8, 'classify': 14.2, 'plan_ocr': 20.6, 'total': 38.6}

| source | page | label | method |
|---|---|---|---|
| s4c5tvdfq0syslhg.pdf | 1 | other | clip |
| s4c5tvdfq0syslhg.pdf | 2 | other | clip |
| s4c5tvdfq0syslhg.pdf | 3 | other | clip |
| s4c5tvdfq0syslhg.pdf | 4 | other | clip |
| s4c5tvdfq0syslhg.pdf | 5 | other | clip |
| s4c5tvdfq0syslhg.pdf | 6 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 7 | other | clip |
| s4c5tvdfq0syslhg.pdf | 8 | other | clip |
| s4c5tvdfq0syslhg.pdf | 9 | other | clip |
| s4c5tvdfq0syslhg.pdf | 10 | other | clip |
| s4c5tvdfq0syslhg.pdf | 11 | other | clip |
| s4c5tvdfq0syslhg.pdf | 12 | other | clip |
| s4c5tvdfq0syslhg.pdf | 13 | other | clip |
| s4c5tvdfq0syslhg.pdf | 14 | other | clip |
| s4c5tvdfq0syslhg.pdf | 15 | other | clip |
| s4c5tvdfq0syslhg.pdf | 16 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 17 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 18 | other | clip |
| s4c5tvdfq0syslhg.pdf | 19 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 20 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 21 | exterior | clip |
| s4c5tvdfq0syslhg.pdf | 22 | other | clip |
| s4c5tvdfq0syslhg.pdf | 23 | exterior | clip |
| s4c5tvdfq0syslhg.pdf | 24 | exterior | clip |
| s4c5tvdfq0syslhg.pdf | 25 | other | clip |
| s4c5tvdfq0syslhg.pdf | 26 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 27 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 28 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 29 | other | clip |
| s4c5tvdfq0syslhg.pdf | 30 | other | clip |
| s4c5tvdfq0syslhg.pdf | 31 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 32 | floor_plan | clip |
| s4c5tvdfq0syslhg.pdf | 33 | other | clip |
| s4c5tvdfq0syslhg.pdf | 34 | other | clip |
| s4c5tvdfq0syslhg.pdf | 35 | other | clip |
| s4c5tvdfq0syslhg.pdf | 36 | other | clip |
| s4c5tvdfq0syslhg.pdf | 37 | exterior | clip |
| s4c5tvdfq0syslhg.pdf | 38 | other | clip |
| s4c5tvdfq0syslhg.pdf | 39 | other | clip |
| s4c5tvdfq0syslhg.pdf | 40 | exterior | clip |
| s4c5tvdfq0syslhg.pdf | 41 | exterior | clip |
| loopnet_Barclay_House_Plans.pdf | 1 | exterior | clip |
| loopnet_Barclay_House_Plans.pdf | 2 | other | clip |
| loopnet_Barclay_House_Plans.pdf | 3 | floor_plan | clip |
| loopnet_Barclay_House_Plans.pdf | 4 | floor_plan | clip |

## Room sizes read from plans (check against the plan before use)
| source | page | room (guess) | size | method | conf |
|---|---|---|---|---|---|
| s4c5tvdfq0syslhg.pdf | 32 | WC | 1500 × 2972 | rapidocr | 0.99 |
| s4c5tvdfq0syslhg.pdf | 32 | BEDROOM 1 | 4225 × 5135 | rapidocr | 1.0 |
| loopnet_Barclay_House_Plans.pdf | 3 | ? | 2040 × 1389 | textlayer | 1.0 |
