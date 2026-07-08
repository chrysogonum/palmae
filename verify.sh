#!/usr/bin/env bash
# Completion check for the Quercus vertical slice — the condition the /goal
# scaling phase drives toward. Green here == the slice is sound.
set -euo pipefail
cd "$(dirname "$0")"

echo "== frontend: type-check + production build =="
npm run build --prefix frontend >/dev/null
echo "   OK"

echo "== api + data invariants (pytest) =="
( cd api && PYTHONPATH=. ../.venv/bin/pytest tests/ -q )

echo ""
echo "✅ ALL GREEN — vertical slice verified (build clean, contracts + data invariants pass)."
