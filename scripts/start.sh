#!/usr/bin/env bash
# FeyaGate Skill — Start MCP Server (macOS / Linux)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Read port from config.yaml, fallback to 38080
PORT=38080
CONFIG_FILE="$ROOT_DIR/config/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    CFG_PORT="$(grep -E '^\s*http_port:' "$CONFIG_FILE" | head -1 | sed 's/.*: *//' | tr -d ' ')"
    [ -n "$CFG_PORT" ] && PORT="$CFG_PORT"
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        *)      echo "Usage: bash scripts/start.sh [--port PORT]"; exit 1 ;;
    esac
done

BIN="$ROOT_DIR/bin/miloco-mcp-server"
CONFIG="$ROOT_DIR/config/config.yaml"
PID_FILE="$ROOT_DIR/data/miloco-mcp-server.pid"
LOG_FILE="$ROOT_DIR/data/miloco-mcp-server.log"
LIB_DIR="$ROOT_DIR/lib"

[ ! -x "$BIN" ] && echo "ERROR: bin/miloco-mcp-server not found. Run: bash scripts/setup.sh" && exit 1

if [ ! -f "$CONFIG" ] && [ -f "$ROOT_DIR/config/config.yaml.example" ]; then
    cp "$ROOT_DIR/config/config.yaml.example" "$CONFIG"
fi
[ ! -f "$CONFIG" ] && echo "ERROR: config/config.yaml not found" && exit 1

mkdir -p "$ROOT_DIR/data"

# Set library search path
if [ -d "$LIB_DIR" ]; then
    case "$(uname -s)" in
        Darwin) export DYLD_LIBRARY_PATH="$LIB_DIR:${DYLD_LIBRARY_PATH:-}" ;;
        *)      export LD_LIBRARY_PATH="$LIB_DIR:${LD_LIBRARY_PATH:-}" ;;
    esac
fi

# Check already running
if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE")"
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Already running (PID $OLD_PID). Stop first: bash scripts/stop.sh"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

echo "Starting miloco-mcp-server (port $PORT)..."
cd "$ROOT_DIR"
nohup "$BIN" --config "$CONFIG" > "$LOG_FILE" 2>&1 &
echo "$!" > "$PID_FILE"

PID="$(cat "$PID_FILE")"

# Wait for server to become healthy (up to 10s)
for i in $(seq 1 5); do
    sleep 2
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "FAILED to start. Log:"
        tail -10 "$LOG_FILE" 2>/dev/null
        rm -f "$PID_FILE"
        exit 1
    fi
    CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/health" 2>/dev/null || echo "000")"
    if [ "$CODE" = "200" ]; then
        echo "OK (PID $PID) http://localhost:$PORT/mcp/http"
        exit 0
    fi
done

echo "Started (PID $PID) but health check not responding yet."
echo "The server may still be initializing. Check: tail -f data/miloco-mcp-server.log"
