#!/usr/bin/env bash
# Usage: ./backup.sh "message"   |   ./backup.sh --check  (exit 1 if uncommitted/unpushed)
set -u; cd "$(dirname "$0")"
if [ "${1:-}" = "--check" ]; then
  git fetch -q origin 2>/dev/null; d=$(git status --porcelain | wc -l); a=$(git rev-list --count origin/main..main 2>/dev/null || echo "?")
  echo "uncommitted=$d unpushed=$a"; [ "$d" = 0 ] && [ "$a" = 0 ]; exit; fi
big=$(find . -path ./.git -prune -o -type f -size +99M -print); [ -n "$big" ] && { echo "BLOCK: >99MB files (GitHub limit): $big"; exit 1; }
git add -A
git diff --cached --quiet || git commit -qm "$(date '+%F %H:%M %Z') ${1:-auto backup}"
if git push -q origin main 2>&1; then echo "PUSH OK $(git rev-parse --short HEAD)"; else echo "PUSH FAILED (committed locally)"; exit 1; fi
git log --oneline -1; git count-objects -vH | grep size-pack
