#!/usr/bin/env bash
# FeyaGate Skill — Cross-platform Setup
#
# Detects OS/arch, finds the matching release package in packages/,
# extracts binary → bin/, libraries → lib/, webui → webui/.
#
# Usage:
#   bash scripts/setup.sh                          # auto-detect from packages/
#   bash scripts/setup.sh --package path/to/xxx.tar.gz   # specify archive directly
#   bash scripts/setup.sh --help
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$ROOT_DIR/packages"
BIN_DIR="$ROOT_DIR/bin"
LIB_DIR="$ROOT_DIR/lib"
DATA_DIR="$ROOT_DIR/data"
CONFIG_DIR="$ROOT_DIR/config"

ARCHIVE=""

# ── Helpers ──────────────────────────────────────────────────────────────────

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

find_package() {
    local platform="$1"
    local found=""

    if [ -d "$PKG_DIR" ]; then
        for f in "$PKG_DIR"/miloco-mcp-server-*"${platform}"*.tar.gz \
                 "$PKG_DIR"/miloco-mcp-server-*"${platform}"*.zip; do
            [ -f "$f" ] && found="$f" && break
        done
    fi

    if [ -z "$found" ]; then
        for f in "$ROOT_DIR"/miloco-mcp-server-*"${platform}"*.tar.gz \
                 "$ROOT_DIR"/miloco-mcp-server-*"${platform}"*.zip; do
            [ -f "$f" ] && found="$f" && break
        done
    fi

    echo "$found"
}

extract_archive() {
    local archive="$1"
    local tmp_dir
    tmp_dir="$(mktemp -d)"

    echo "Extracting: $(basename "$archive")"

    case "$archive" in
        *.tar.gz|*.tgz) tar xzf "$archive" -C "$tmp_dir" ;;
        *.zip)          unzip -q "$archive" -d "$tmp_dir" ;;
        *) echo "ERROR: Unsupported archive format: $archive"; rm -rf "$tmp_dir"; exit 1 ;;
    esac

    # Find the extracted directory (usually miloco-mcp-server-VERSION-OS-ARCH/)
    local inner
    inner="$(find "$tmp_dir" -maxdepth 1 -mindepth 1 -type d | head -1)"
    if [ -z "$inner" ]; then
        inner="$tmp_dir"
    fi

    # ── Deploy binary ──
    mkdir -p "$BIN_DIR"
    if [ -f "$inner/miloco-mcp-server" ]; then
        cp "$inner/miloco-mcp-server" "$BIN_DIR/"
        chmod +x "$BIN_DIR/miloco-mcp-server"
        echo "  [OK] bin/miloco-mcp-server"
    elif [ -f "$inner/miloco-mcp-server.exe" ]; then
        cp "$inner/miloco-mcp-server.exe" "$BIN_DIR/"
        echo "  [OK] bin/miloco-mcp-server.exe"
    elif [ -f "$inner/bin/miloco-mcp-server" ]; then
        cp "$inner/bin/miloco-mcp-server" "$BIN_DIR/"
        chmod +x "$BIN_DIR/miloco-mcp-server"
        echo "  [OK] bin/miloco-mcp-server"
    else
        echo "  [WARN] Binary not found in archive"
    fi

    # ── Deploy libraries ──
    mkdir -p "$LIB_DIR"
    local lib_count=0
    if [ -d "$inner/lib" ]; then
        for f in "$inner/lib"/*; do
            [ -f "$f" ] || continue
            cp "$f" "$LIB_DIR/"
            lib_count=$((lib_count + 1))
        done
    fi
    echo "  [OK] lib/ ($lib_count libraries)"

    # ── Create bin/lib symlink for @executable_path/lib/ resolution (macOS) ──
    if [ ! -e "$BIN_DIR/lib" ]; then
        ln -s ../lib "$BIN_DIR/lib"
        echo "  [OK] bin/lib -> ../lib (rpath symlink)"
    fi

    # ── Deploy WebUI ──
    if [ -d "$inner/webui" ]; then
        rm -rf "$ROOT_DIR/webui"
        cp -r "$inner/webui" "$ROOT_DIR/webui"
        echo "  [OK] webui/"
    fi

    # ── Deploy default config (prefer our example over package default) ──
    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        if [ -f "$CONFIG_DIR/config.yaml.example" ]; then
            cp "$CONFIG_DIR/config.yaml.example" "$CONFIG_DIR/config.yaml"
            echo "  [OK] config/config.yaml (from skill example)"
        elif [ -f "$inner/config.yaml" ]; then
            cp "$inner/config.yaml" "$CONFIG_DIR/config.yaml"
            # Patch token_file path for skill directory layout
            sed -i.bak 's|token_file: "auth_token.json"|token_file: "data/auth_token.json"|' "$CONFIG_DIR/config.yaml" 2>/dev/null && rm -f "$CONFIG_DIR/config.yaml.bak"
            echo "  [OK] config/config.yaml (from package, patched)"
        fi
    fi

    rm -rf "$tmp_dir"
}

show_help() {
    cat <<'HELP'
FeyaGate Skill — Setup

Usage:
  bash scripts/setup.sh                              Auto-detect platform and package
  bash scripts/setup.sh --package <archive>          Specify archive path directly
  bash scripts/setup.sh --help                       Show this help

The script will:
  1. Detect your OS and architecture (Darwin-x86_64, Linux-x86_64, etc.)
  2. Find matching miloco-mcp-server-*-{OS}-{arch}.tar.gz in packages/
  3. Extract binary → bin/, libraries → lib/, webui → webui/
  4. Create config/config.yaml from example if not exists
  5. Create data/ directory

Package naming convention:
  miloco-mcp-server-{VERSION}-Darwin-x86_64.tar.gz     macOS Intel
  miloco-mcp-server-{VERSION}-Darwin-arm64.tar.gz       macOS Apple Silicon
  miloco-mcp-server-{VERSION}-Linux-x86_64.tar.gz       Linux x86_64
  miloco-mcp-server-{VERSION}-Windows-x86_64.zip        Windows x86_64

HELP
}

# ── Parse arguments ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --package)  ARCHIVE="$2"; shift 2 ;;
        -h|--help)  show_help; exit 0 ;;
        *)          echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# ── Main ─────────────────────────────────────────────────────────────────────

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
    echo "Please download the release package and place it in packages/ directory:"
    echo "  packages/miloco-mcp-server-VERSION-${PLATFORM}.tar.gz"
    echo ""
    echo "Or specify the archive directly:"
    echo "  bash scripts/setup.sh --package /path/to/miloco-mcp-server-*.tar.gz"
    echo ""
    echo "Download from: https://gitee.com/panjyang/miloco-mcp-server/releases"
    exit 1
fi

extract_archive "$ARCHIVE"

# ── Post-setup ───────────────────────────────────────────────────────────────

mkdir -p "$DATA_DIR"

if [ ! -f "$CONFIG_DIR/config.yaml" ] && [ -f "$CONFIG_DIR/config.yaml.example" ]; then
    cp "$CONFIG_DIR/config.yaml.example" "$CONFIG_DIR/config.yaml"
    echo "  [OK] config/config.yaml (from example)"
fi

# ── Verify ───────────────────────────────────────────────────────────────────
echo ""
echo "--- Verification ---"

BIN_NAME="miloco-mcp-server"
case "$PLATFORM" in Windows-*) BIN_NAME="miloco-mcp-server.exe" ;; esac

if [ -x "$BIN_DIR/$BIN_NAME" ] || [ -f "$BIN_DIR/$BIN_NAME" ]; then
    echo "[OK] Binary: bin/$BIN_NAME ($(du -h "$BIN_DIR/$BIN_NAME" | awk '{print $1}'))"
else
    echo "[FAIL] Binary not found: bin/$BIN_NAME"
fi

lib_count="$(ls -1 "$LIB_DIR" 2>/dev/null | { grep -v '\.gitkeep' || true; } | wc -l | tr -d ' ')"
echo "[OK] Libraries: $lib_count files in lib/"

if [ -f "$CONFIG_DIR/config.yaml" ]; then
    echo "[OK] Config: config/config.yaml"
else
    echo "[WARN] Config not found — create from config.yaml.example"
fi

echo "[OK] Data directory: data/"

if [ -d "$ROOT_DIR/webui" ]; then
    echo "[OK] WebUI: webui/"
fi

echo ""
echo "Setup complete! Next steps:"
echo "  1. Edit config/config.yaml (set cloud_server region)"
echo "  2. bash scripts/start.sh"
echo "  3. python3 scripts/auth.py  (first-time authorization)"
echo "  4. bash scripts/health_check.sh"
