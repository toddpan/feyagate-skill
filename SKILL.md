---
name: feyagate
description: MCP smart home gateway for AI agents. Multi-platform IoT device control via MCP protocol.
sub_skills:
  - name: feyagate-xiaomi
    file: skills/xiaomi.md
    trigger: Xiaomi, Mi Home, MIOT, 小米, camera, P2P, XiaoAI, 小爱, TTS, speaker, 摄像头
  - name: feyagate-tuya
    file: skills/tuya.md
    trigger: Tuya, Smart Life, 涂鸦, DP code, QR auth
  - name: feyagate-midea
    file: skills/midea.md
    trigger: Midea, 美居, 美的, AC, air conditioner, 空调
  - name: feyagate-ewelink
    file: skills/ewelink.md
    trigger: eWeLink, Sonoff, iTEAD, switch, relay
  - name: feyagate-automation
    file: skills/automation.md
    trigger: schedule, timer, trigger, automation, room, memory, note, 定时, 自动化, 房间, 记忆
  - name: feyagate-extension
    file: skills/extension.md
    trigger: serial, RS485, UART, GPIO, Xiaozhi, 小智, license, config, stats, 统计
---

# FeyaGate Skill — MCP Smart Home Gateway for AI Agents

MCP-based multi-platform smart home gateway supporting Xiaomi, Tuya, Midea, eWeLink, Serial, and GPIO. Compatible with OpenClaw, Claude Code, Hermes, Codex, Windsurf, Copilot, 小智AI and other MCP-compatible AI agents.

## Before Using Any Tool

Run this check **before** calling any FeyaGate MCP tool:

```bash
feyagate status
```

- If status is **RUNNING** → proceed with tool calls.
- If status is **STOPPED** or command not found → run `feyagate start` first. If `feyagate` is not installed, run `pip install feyagate-skill && feyagate setup && feyagate start`.

**Dual API endpoints:**

| Endpoint | Protocol | URL |
|----------|----------|-----|
| MCP (PC proxy) | Streamable HTTP JSON-RPC 2.0 | `http://localhost:38080/mcp/http` |
| MCP (ESP32 gateway) | WebSocket / Streamable HTTP | `ws://<gateway>:8765/mcp` / `http://<gateway>:8765/mcp/http` |
| HTTP REST (ESP32 gateway) | REST API | `http://<gateway>:8080/api/v1/...` |

> **Note:** The PC proxy (miloco-mcp-server) provides all gateway MCP tools plus additional extensions (camera P2P, Xiaomi auth, etc.).

## Quick Start

```bash
pip install feyagate-skill       # Step 1: Install Python package
feyagate setup                   # Step 2: Download MCP server binary (~30MB)
feyagate start                   #        Start service (localhost:38080)
feyagate install-claude          # Step 3: Register with your AI agent
feyagate auth                    # Step 4: Authorize smart home platform
```

> **Linux** may need system deps first: `sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7`

Other agent install commands: `install-cursor`, `install-openclaw`, `install-hermes`, `install-codex`, `install-windsurf`, `install-copilot`

Full step-by-step guide: [QUICKSTART.md](QUICKSTART.md)

## Server Lifecycle (CLI)

| Action | Command |
|--------|---------|
| Install binary | `feyagate setup [--dir PATH]` |
| Start | `feyagate start [--port PORT]` |
| Stop | `feyagate stop` |
| Restart | `feyagate restart [--port PORT]` |
| Status | `feyagate status` |
| Logs | `feyagate log [-n 50]` |
| Upgrade | `feyagate upgrade` |
| Auth Xiaomi | `feyagate auth [--status] [--code CODE]` |

### Manual Scripts (Advanced)

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

## Sub-Skill Loading Guide (for AI agents)

This skill uses a modular structure. The main skill defines cross-platform tools; platform-specific tools are in sub-skill files.

**Loading strategy:**
1. **Always load** this main SKILL.md first — it provides the core cross-platform tools and MCP endpoint info.
2. **Load sub-skills on demand** based on the user's intent. Each sub-skill's `trigger` keywords (listed in frontmatter `sub_skills`) indicate when to load it.
3. **Cross-platform workflow** (no sub-skill needed): `device/list` → `device/specs` → identify platform → load corresponding sub-skill for control operations.

| Sub-Skill | File | When to Load | Covers |
|-----------|------|-------------|--------|
| **feyagate-xiaomi** | [skills/xiaomi.md](skills/xiaomi.md) | Xiaomi/Mi Home devices, cameras, XiaoAI speakers | MIOT device control, OAuth auth, camera P2P, XiaoAI TTS/music |
| **feyagate-tuya** | [skills/tuya.md](skills/tuya.md) | Tuya/Smart Life devices | DP property read/write, QR code auth |
| **feyagate-midea** | [skills/midea.md](skills/midea.md) | Midea/美的 appliances | AC/appliance control, account auth |
| **feyagate-ewelink** | [skills/ewelink.md](skills/ewelink.md) | eWeLink/Sonoff devices | Switch control, multi-channel |
| **feyagate-automation** | [skills/automation.md](skills/automation.md) | Scheduling, automation, rooms, memory | Schedule, trigger engine, room, memory, skill system |
| **feyagate-extension** | [skills/extension.md](skills/extension.md) | Serial, GPIO, license, config | Serial, GPIO, Xiaozhi AI, license, config, stats |

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
| `command not found: feyagate` | `pip install feyagate-skill` |
| `FeyaGate not installed` | `feyagate setup` |
| `connection refused` | `feyagate start` |
| `authorized: false` | `feyagate auth` (Xiaomi) or use platform-specific auth tool |
| `cannot open shared object file` | `sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7` (Linux) |
| `Tool not found` | Check tool name (see `tools/list` output) |
| `key 'device_id' not found` | Platform tools use `device_id`; cross-platform `device/specs` uses `deviceId` |
| `license_required` error | Set license key via `license/set` tool |
| Library load error | `ldd ~/.feyagate/bin/miloco-mcp-server \| grep "not found"` |

Full API reference: [FeyaGate_MCP_API.md](FeyaGate_MCP_API.md), [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md)
