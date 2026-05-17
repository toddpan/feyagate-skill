#!/usr/bin/env bash
# FeyaGate Skill — Verify installation
# Checks that binary, libraries, and config are in place.
# Run setup.sh first to extract the release package.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== FeyaGate Skill — Verify ==="
echo "Root: $ROOT_DIR"
echo ""

ERRORS=0

# Detect binary name
BIN_NAME="miloco-mcp-server"
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) BIN_NAME="miloco-mcp-server.exe" ;; esac
BIN="$ROOT_DIR/bin/$BIN_NAME"

if [ -f "$BIN" ]; then
    chmod +x "$BIN" 2>/dev/null || true
    echo "[OK] Binary: bin/$BIN_NAME ($(du -h "$BIN" | awk '{print $1}'))"
else
    echo "[FAIL] Binary not found: bin/$BIN_NAME"
    echo "       Run: bash scripts/setup.sh"
    ERRORS=$((ERRORS + 1))
fi

LIB_DIR="$ROOT_DIR/lib"
if [ -d "$LIB_DIR" ]; then
    count="$(ls -1 "$LIB_DIR" 2>/dev/null | grep -v '\.gitkeep' | wc -l | tr -d ' ')"
    if [ "$count" -gt 0 ]; then
        echo "[OK] Libraries: $count files in lib/"
    else
        echo "[WARN] lib/ is empty"
    fi
else
    echo "[WARN] lib/ directory not found"
fi

CONFIG="$ROOT_DIR/config/config.yaml"
if [ -f "$CONFIG" ]; then
    echo "[OK] Config: config/config.yaml"
elif [ -f "$ROOT_DIR/config/config.yaml.example" ]; then
    cp "$ROOT_DIR/config/config.yaml.example" "$CONFIG"
    echo "[OK] Created config/config.yaml from example"
else
    echo "[FAIL] No config found"
    ERRORS=$((ERRORS + 1))
fi

mkdir -p "$ROOT_DIR/data"
echo "[OK] Data directory: data/"

if [ -d "$ROOT_DIR/webui" ]; then
    echo "[OK] WebUI: webui/"
fi

# Check system shared library dependencies (Linux only)
if [ "$(uname -s)" = "Linux" ]; then
    MISSING="$(ldd "$BIN" 2>/dev/null | grep "not found" || true)"
    if [ -n "$MISSING" ]; then
        echo ""
        echo "[WARN] Missing shared libraries:"
        echo "$MISSING" | sed 's/^/       /'
        echo "       Fix: sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7"
        ERRORS=$((ERRORS + 1))
    else
        echo "[OK] Shared library dependencies satisfied"
    fi
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
    echo "FAILED: $ERRORS errors. Run: bash scripts/setup.sh"
    exit 1
else
    echo "All checks passed."
    echo "Next: edit config/config.yaml, then: bash scripts/start.sh"
fi
