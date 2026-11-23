#!/bin/bash
# Copy-test for trick #22. Opens official out/barclay_scene.blend READ-ONLY.
# Never overwrites official exports. Does not deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
mkdir -p tests/suncheck/out
python3 sun_check.py --render
echo "SUNCHECK RUN DONE"
