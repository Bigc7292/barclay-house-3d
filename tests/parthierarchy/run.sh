#!/bin/bash
# Copy-test for trick #16. Never writes to out/ or web/.
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT="$PWD/tests/parthierarchy/out"
rm -rf "$OUT"
mkdir -p "$OUT"
BLENDER="${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}"
BOUT="$OUT/" "$BLENDER" -b -P tests/parthierarchy/test_parts.py
# make_mobile + validate against the copy only
OUT="$OUT" ./make_mobile.sh
OUT="$OUT" ./validate.sh
echo "COPY-TEST DONE"
