#!/usr/bin/env bash
# FeyaGate Skill — Cross-platform Setup (clone/offline path)
#
# Thin wrapper that delegates all extraction/checksum/signing to the Python
# installer (feyagate_skill.installer.do_setup), so there is ONE implementation
# instead of a parallel shell copy. This gives the clone path the same
# integrity checks and macOS quarantine/codesign handling as the online path.
#
# It only adds the offline value: auto-discover a pre-downloaded archive in
# packages/ (or the repo root) and install in-place into the repo directory.
#
# Usage:
#   bash scripts/setup.sh                          # auto-detect from packages/
#   bash scripts/setup.sh --package path/to/xxx.tar.gz   # specify archive directly
#   bash scripts/setup.sh --help
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$ROOT_DIR/packages"

ARCHIVE=""

detect_platform() {
    local os arch
    case "$(uname -s)" in
        Darwin) os="Darwin"  ;;
        Linux)  os="Linux"   ;;
        MINGW*|MSYS*|CYGWIN*) os="Windows" ;;
        *)      echo "ERROR: Unsupported OS: $(uname -s)"; exit 1 ;;
    esac
    arch="$(uname -m)"
    echo "${os}-${arch}"
}

# Windows `python3` is often a Microsoft Store stub; pick a real interpreter.
detect_python() {
    local candidates
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) candidates=(python python3 py) ;;
        *)                    candidates=(python3 python) ;;
    esac
    for c in "${candidates[@]}"; do
        if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
            echo "$c"; return 0
        fi
    done
    return 1
}

find_package() {
    local platform="$1"
    local found=""
    local d
    for d in "$PKG_DIR" "$ROOT_DIR"; do
        [ -d "$d" ] || continue
        for f in "$d"/miloco-mcp-server-*"${platform}"*.tar.gz \
                 "$d"/miloco-mcp-server-*"${platform}"*.zip; do
            [ -f "$f" ] && found="$f" && break 2
        done
    done
    echo "$found"
}

show_help() {
    cat <<'HELP'
FeyaGate Skill — Setup (clone/offline path)

Usage:
  bash scripts/setup.sh                              Auto-detect platform and package
  bash scripts/setup.sh --package <archive>          Specify archive path directly
  bash scripts/setup.sh --help                       Show this help

The script delegates extraction to the Python installer
(python -m feyagate_skill.cli setup --package <archive> --dir <repo>),
so checksum verification and macOS signing are handled the same way as the
online installer. It installs in-place into the repo directory.

Package naming convention (place in packages/):
  miloco-mcp-server-{VERSION}-Darwin-x86_64.tar.gz     macOS Intel
  miloco-mcp-server-{VERSION}-Darwin-arm64.tar.gz       macOS Apple Silicon
  miloco-mcp-server-{VERSION}-Linux-x86_64.tar.gz       Linux x86_64
  miloco-mcp-server-{VERSION}-Windows-x86_64.zip        Windows x86_64

Download from: https://github.com/toddpan/miloco-mcp-server-releases/releases
HELP
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --package)  ARCHIVE="$2"; shift 2 ;;
        -h|--help)  show_help; exit 0 ;;
        *)          echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

PLATFORM="$(detect_platform)"
echo "=== FeyaGate Skill — Setup ==="
echo "Platform: $PLATFORM"
echo "Root:     $ROOT_DIR"
echo ""

if [ -z "$ARCHIVE" ]; then
    ARCHIVE="$(find_package "$PLATFORM")"
fi

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo "ERROR: No matching release package found for $PLATFORM"
    echo ""
    echo "Place the release package in packages/:"
    echo "  packages/miloco-mcp-server-VERSION-${PLATFORM}.tar.gz"
    echo ""
    echo "Or specify it directly:"
    echo "  bash scripts/setup.sh --package /path/to/miloco-mcp-server-*.tar.gz"
    echo ""
    echo "Download from: https://github.com/toddpan/miloco-mcp-server-releases/releases"
    exit 1
fi

PYTHON="$(detect_python)" || {
    echo "ERROR: No usable Python interpreter found (need Python 3.9+)."
    echo "       The clone-path setup delegates to the Python installer."
    exit 1
}
echo "Python:  $PYTHON ($("$PYTHON" --version 2>&1))"
echo "Package: $ARCHIVE"
echo ""

# Delegate to the single Python installer. --dir installs in-place into the
# repo so the clone-path start/stop scripts find bin/, config/, etc. here.
cd "$ROOT_DIR"
exec "$PYTHON" -m feyagate_skill.cli setup --dir "$ROOT_DIR" --package "$ARCHIVE"
