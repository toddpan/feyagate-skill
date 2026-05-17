#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/data/miloco-mcp-server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Server not running (no PID file)."
    exit 0
fi

PID="$(cat "$PID_FILE")"
if ! kill -0 "$PID" 2>/dev/null; then
    echo "Server not running (stale PID)."
    rm -f "$PID_FILE"
    exit 0
fi

echo "Stopping PID $PID..."
kill "$PID" 2>/dev/null || true

for i in $(seq 1 10); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 1
done

if kill -0 "$PID" 2>/dev/null; then
    echo "Force killing..."
    kill -9 "$PID" 2>/dev/null || true
fi

rm -f "$PID_FILE"
echo "Stopped."
