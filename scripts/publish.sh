#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

if [ -z "$1" ]; then
    echo "Usage: $0 <pypi|testpypi>"
    echo ""
    echo "  pypi      - Publish to https://pypi.org"
    echo "  testpypi  - Publish to https://test.pypi.org"
    exit 1
fi

TARGET="$1"

if [ ! -d "dist" ] || [ -z "$(ls -A dist/ 2>/dev/null)" ]; then
    echo "==> No dist/ found. Building first..."
    bash "$SCRIPT_DIR/build.sh"
fi

# Ensure twine is installed
pip install twine -q

# Read token from env or prompt
if [ "$TARGET" = "pypi" ]; then
    if [ -z "$PYPI_TOKEN" ]; then
        echo "Enter PyPI API token (or set PYPI_TOKEN env var):"
        read -rs PYPI_TOKEN
    fi
    REPOSITORY="pypi"
elif [ "$TARGET" = "testpypi" ]; then
    if [ -z "$TEST_PYPI_TOKEN" ]; then
        echo "Enter TestPyPI API token (or set TEST_PYPI_TOKEN env var):"
        read -rs TEST_PYPI_TOKEN
        PYPI_TOKEN="$TEST_PYPI_TOKEN"
    fi
    REPOSITORY="testpypi"
else
    echo "Unknown target: $TARGET. Use 'pypi' or 'testpypi'."
    exit 1
fi

echo ""
echo "==> Publishing to $REPOSITORY..."
twine upload --repository "$REPOSITORY" dist/* -u __token__ -p "$PYPI_TOKEN"

echo ""
echo "==> Published successfully!"
if [ "$TARGET" = "pypi" ]; then
    echo "    https://pypi.org/project/feyagate-skill/"
else
    echo "    https://test.pypi.org/project/feyagate-skill/"
fi
