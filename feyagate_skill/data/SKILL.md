---
name: feyagate
description: MCP smart home gateway skill for AI agents (OpenClaw, Claude Code, Hermes, Codex, Windsurf, Copilot, 小智AI). Control multi-platform IoT devices via MCP protocol — supports Xiaomi/Mi Home, Tuya, Midea, eWeLink, Serial, and GPIO platforms. Provides cross-platform device discovery and control, MIOT device properties, XiaoAI speaker TTS/music, camera P2P streaming and snapshots, scheduled tasks, trigger automation, vision AI analysis, memory system, room management, and skill management. Use when working with smart home, IoT device control, home automation, Xiaomi, Tuya, Midea, eWeLink, MIOT protocol, cameras, surveillance, XiaoAI speakers, TTS, automation, scheduling, OpenClaw skill, Hermes skill, MCP server, MCP skill, or AI agent tool.
---

# FeyaGate Skill — MCP Smart Home Gateway for AI Agents

MCP-based multi-platform smart home gateway supporting Xiaomi, Tuya, Midea, eWeLink, Serial, and GPIO. Compatible with OpenClaw, Claude Code, Hermes, Codex, Windsurf, Copilot, 小智AI and other MCP-compatible AI agents.

**Dual API endpoints:**

| Endpoint | Protocol | URL |
|----------|----------|-----|
| MCP (PC proxy) | Streamable HTTP JSON-RPC 2.0 | `http://localhost:38080/mcp/http` |
| MCP (ESP32 gateway) | WebSocket / Streamable HTTP | `ws://<gateway>:8765/mcp` / `http://<gateway>:8765/mcp/http` |
| HTTP REST (ESP32 gateway) | REST API | `http://<gateway>:8080/api/v1/...` |

> **Note:** The PC proxy (miloco-mcp-server) provides all gateway MCP tools plus additional extensions (camera P2P, Xiaomi auth, etc.).

## Server Lifecycle

| Action | macOS/Linux | Windows |
|--------|-------------|---------|
| Install | `bash scripts/install.sh` | `scripts\install.ps1` |
| Setup | `bash scripts/setup.sh` | `scripts\setup.bat` |
| Start | `bash scripts/start.sh` | `scripts\start.bat` |
| Stop | `bash scripts/stop.sh` | `scripts\stop.bat` |
| Verify | `bash scripts/verify.sh` | `scripts\verify.bat` |
| Status | `bash scripts/health_check.sh` | `scripts\health_check.bat` |
| Custom port | `bash scripts/start.sh --port 9090` | `scripts\start.bat --port 9090` |
| Upgrade | `bash scripts/upgrade.sh` | `powershell -File scripts\upgrade.ps1` |
| Check updates | `bash scripts/upgrade.sh --check` | `powershell -File scripts\upgrade.ps1 -Check` |

### System Dependencies (Linux)

```bash
sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7
ldd bin/miloco-mcp-server | grep "not found"  # verify
```

## Cross-Platform Tools

Unified interfaces that work across all platforms. System auto-detects device platform.

| Tool | Arguments | Returns |
|------|-----------|---------|
| `device/list` | `filter` (string[]), `platform` (opt) | `devices[]` with `platform` field |
| `device/specs` | `deviceId` (string) | Platform-specific spec: properties, actions |
| `platform/status` | — | All platform connection/auth/sync status |
| `gateway/info` | — | Version, device count, ports |
| `scene/list` | `platform` (string) | `scenes[]` |
| `scene/trigger` | `platform` (string), `sceneId` (string) | Trigger result |

> **Parameter convention:** `device/specs` uses `deviceId` (camelCase); platform-specific tools (`xiaomi/*`, `tuya/*`, etc.) use `device_id` (snake_case).

## Platform Skill Modules

Detailed tool references are split into sub-skill files by platform. Load as needed:

| Module | File | Covers |
|--------|------|--------|
| **Xiaomi** | [skills/xiaomi.md](skills/xiaomi.md) | MIOT device control, OAuth auth, camera P2P, XiaoAI speaker |
| **Tuya** | [skills/tuya.md](skills/tuya.md) | DP property read/write, QR code auth |
| **Midea** | [skills/midea.md](skills/midea.md) | AC/appliance control, account auth |
| **eWeLink** | [skills/ewelink.md](skills/ewelink.md) | Sonoff/eWeLink switches, multi-channel |
| **Automation** | [skills/automation.md](skills/automation.md) | Schedule, trigger engine, room, memory, skill system |
| **Extension** | [skills/extension.md](skills/extension.md) | Serial, GPIO, Xiaozhi AI, license, config, stats |

## License System

- **Free edition**: Xiaomi platform only (device control, cameras, XiaoAI, MCP proxy)
- **Licensed edition**: All platforms (Xiaomi + Tuya + Midea + eWeLink)
- `tuya/set_property`, `midea/set_property`, `ewelink/set_property` return `license_required` on free edition
- `get_properties` and all other tools work without license

## Configuration

`config/config.yaml`:

```yaml
server:
  http_port: 38080
  ws_port: 8765
  bind_address: "0.0.0.0"
auth:
  cloud_server: "cn"      # cn / de / sg / us / ru / i2
  token_file: "data/auth_token.json"
camera:
  frame_interval: 500
  buffer_max_size: 20
  buffer_ttl: 300
  jpeg_quality: 90
tuya:
  token_file: "data/tuya_token.json"
midea:
  token_file: "data/midea_token.json"
ewelink:
  token_file: "data/ewelink_token.json"
xiaozhi:
  endpoint: ""            # ws:// or wss:// (empty = disabled)
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `connection refused` | Start server: `bash scripts/start.sh` |
| `authorized: false` | Authorize via `xiaomi/auth_url` → `xiaomi/auth_callback` |
| `cannot open shared object file` | `sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7` |
| `Tool not found` | Check tool name (see `tools/list` output) |
| `key 'device_id' not found` | Platform tools use `device_id`; cross-platform `device/specs` uses `deviceId` |
| `license_required` error | Set license key via `license/set` tool |
| Library load error | `ldd bin/miloco-mcp-server \| grep "not found"` |

Full API reference: [FeyaGate_MCP_API.md](FeyaGate_MCP_API.md), [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md)
