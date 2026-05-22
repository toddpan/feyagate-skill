#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "==> Cleaning old build artifacts..."
rm -rf dist/ build/ *.egg-info feyagate_skill.egg-info

echo "==> Building package..."
python -m build

echo ""
echo "==> Build complete. Artifacts:"
ls -lh dist/
echo ""
echo "Run scripts/publish.sh to publish to PyPI."
