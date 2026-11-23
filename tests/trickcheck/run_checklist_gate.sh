#!/usr/bin/env bash
# Trick #15 smoke: must FAIL overall on current R4 (open defects) and finish <30s.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
START=$(date +%s)
python3 checks.py --all
END=$(date +%s)
echo "wall_s=$((END-START))"
test $((END-START)) -lt 30
