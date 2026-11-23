#!/bin/bash
# Copy-test for trick #19. Never saves a .blend; never writes official out/ GLBs.
set -euo pipefail
cd "$(dirname "$0")/../.."
BLENDER="${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}"
SRC=${1:-out/barclay_scene.blend}
COPY=tests/meshhealth/barclay_scene.blend
# use an existing copy if present; otherwise copy (not committed)
if [ ! -f "$COPY" ]; then cp -p "$SRC" "$COPY"; fi
MT0=$(stat -c %Y "$COPY")
MH_OUT="$PWD/tests/meshhealth" "$BLENDER" -b "$COPY" --python mesh_health.py
MT1=$(stat -c %Y "$COPY")
[ "$MT0" = "$MT1" ] || { echo "FAIL: test blend mtime changed"; exit 2; }
echo "COPY-TEST blend unchanged"
