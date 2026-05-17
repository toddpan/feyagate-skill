#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PORT=38080
CONFIG_FILE="$ROOT_DIR/config/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    CFG_PORT="$(grep -E '^\s*http_port:' "$CONFIG_FILE" | head -1 | sed 's/.*: *//' | tr -d ' ')"
    [ -n "$CFG_PORT" ] && PORT="$CFG_PORT"
fi
[ "${1:-}" = "--port" ] && PORT="$2"

BASE="http://localhost:$PORT"
echo "=== Health Check ($BASE) ==="

CODE="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/health" 2>/dev/null || echo "000")"
[ "$CODE" != "200" ] && echo "[FAIL] HTTP $CODE — not running" && exit 1
echo "[OK] HTTP 200"

mcp() {
    curl -s -X POST "$BASE/mcp/http" -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$1\",\"arguments\":${2:-{}}}}" 2>/dev/null
}

mcp "xiaomi/auth_status" | python3 -c "
import sys,json
r=json.load(sys.stdin);d=json.loads(r['result']['content'][0]['text'])
a=d.get('authorized',False);s=d.get('remaining_seconds',0)
print(f'[{\"OK\" if a else \"WARN\"}] Xiaomi Auth: {\"Yes\" if a else \"No\"} (region={d.get(\"cloud_server\",\"?\")}){f\", token {s//3600}h\" if a else \"\"}')" 2>/dev/null || true

mcp "device/list" '{"filter":[]}' | python3 -c "
import sys,json
r=json.load(sys.stdin);d=json.loads(r['result']['content'][0]['text'])
devs=d.get('devices',[])
platforms=set(x.get('platform','?') for x in devs)
print(f'[OK] Devices: {d.get(\"total\",0)} total ({', '.join(f'{p}:{sum(1 for x in devs if x.get(\"platform\")==p)}' for p in sorted(platforms))})')
" 2>/dev/null || true
