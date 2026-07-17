# FeyaGate MCP Server — API Reference

## Transport

- **Protocol**: JSON-RPC 2.0 over HTTP (MCP Streamable HTTP)
- **Endpoint**: `POST /mcp/http`
- **Health**: `GET /health` → `{"status":"ok"}`
- **Content-Type**: `application/json`

## JSON-RPC Envelope

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": { ... }
  }
}
```

System methods: `initialize`, `tools/list`, `ping`, `notifications/initialized`.

---

## Cross-Platform Tools

### device/list

Unified device list across all platforms (Xiaomi, Tuya, Midea, eWeLink).

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `platform` | string | No | Filter by platform: `xiaomi` / `tuya` / `midea` / `ewelink` |
| `filter` | string[] | No | Keywords to filter device names/models/rooms |

**Response**:
```json
{
  "devices": [
    {
      "id": "123456789",
      "name": "客厅灯",
      "model": "yeelink.light.lamp4",
      "platform": "xiaomi",
      "online": true,
      "category": "light",
      "home_name": "我的家",
      "room_name": "客厅"
    }
  ],
  "total": 15
}
```

---

### device/specs

Get device specification (auto-detects platform from deviceId).

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deviceId` | string | Yes | Device ID |

**Response (Xiaomi)**:
```json
{
  "success": true,
  "platform": "xiaomi",
  "spec": {
    "services": [
      {
        "siid": 2,
        "description": "Light",
        "properties": [
          { "piid": 1, "description": "Switch Status", "format": "bool", "access": ["read", "write"] },
          { "piid": 2, "description": "Brightness", "format": "uint8", "value-range": [1, 100, 1] }
        ],
        "actions": [
          { "aiid": 1, "description": "Toggle", "in": [] }
        ]
      }
    ]
  }
}
```

**Response (Tuya)**: Returns DP code definitions.
**Response (Midea/eWeLink)**: Returns property name definitions.

---

### auth/platforms

Get authentication status for all platforms.

**Arguments**: None

**Response**:
```json
[
  { "platform_id": "xiaomi", "platform_name": "米家", "authenticated": true },
  { "platform_id": "tuya", "platform_name": "涂鸦", "authenticated": false },
  { "platform_id": "midea", "platform_name": "美的", "authenticated": false },
  { "platform_id": "ewelink", "platform_name": "易微联", "authenticated": false }
]
```

---

### gateway/info

Get gateway system information.

**Arguments**: None

**Response**:
```json
{
  "name": "FeyaGate Virtual Gateway",
  "version": "1.0.0",
  "platform": "Darwin-x86_64",
  "device_id": "99C40EA467EE",
  "camera_supported": true,
  "license": { "edition": "free", "status": "free" }
}
```

---

## Xiaomi Platform Tools

### xiaomi/auth_status

**Arguments**: None

**Response**:
```json
{ "authorized": true, "remaining_seconds": 86400, "cloud_server": "cn" }
```

### xiaomi/auth_url

**Arguments**: None → Returns OAuth login URL.

### xiaomi/auth_callback

**Arguments**: `code` (string) → Exchange OAuth code for token.

### xiaomi/refresh

**Arguments**: None → Re-fetch device list from cloud.

**Response**:
```json
{ "success": true, "device_count": 15, "camera_count": 3 }
```

### xiaomi/get_area_info

**Arguments**: None → Room/area list.

### xiaomi/get_device_classes

**Arguments**: None → Device class list with counts.

### xiaomi/get_devices

**Arguments**: `area_id` (opt), `device_class` (opt) → Filtered device list.

### xiaomi/scene_list / xiaomi/scene_trigger

List and trigger Xiaomi manual scenes.

---

### get_xiaomi_device_properties

Read Xiaomi device property values.

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deviceId` | string | Yes | Device DID |
| `siid` | integer | Yes | Service ID |
| `piids` | integer[] | Yes | Property ID list |

**Response**:
```json
{
  "properties": [
    { "did": "123456789", "siid": 2, "piid": 1, "code": 0, "value": true }
  ]
}
```

### set_xiaomi_device_property

Set Xiaomi device property value.

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deviceId` | string | Yes | Device DID |
| `siid` | integer | Yes | Service ID |
| `piid` | integer | Yes | Property ID |
| `value` | any | Yes | Property value (bool/number/string) |

**Response**:
```json
{ "success": true, "data": { "code": 0, "did": "123456789", "siid": 2, "piid": 1 } }
```

### execute_xiaomi_device_action

Execute Xiaomi device action.

**Arguments**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deviceId` | string | Yes | Device DID |
| `siid` | integer | Yes | Service ID |
| `aiid` | integer | Yes | Action ID |
| `params` | array | No | Action parameters |

---

## Camera Tools (Xiaomi)

### xiaomi/camera_list

**Arguments**: None → Camera list with status and channel info.

### xiaomi/camera_status

**Arguments**: `camera_id` (opt) → Connection status, buffered_frames.

### xiaomi/camera_connect

**Arguments**: `camera_id` → Establish P2P stream.

### xiaomi/camera_disconnect

**Arguments**: `camera_id` → Stop stream.

### xiaomi/camera_snapshot

**Arguments**: `camera_id`, `channel` (opt, default 0), `count` (opt, 1-10) → JPEG frames.

**Response**:
```json
{
  "camera_id": "123456789",
  "images": [
    { "data_url": "data:image/jpeg;base64,/9j/4AAQ...", "timestamp": 1711449600, "size_bytes": 45230 }
  ]
}
```

### xiaomi/camera_vision_chat

**Arguments**: `camera_id`, `query` → AI vision analysis of camera frame.

---

## XiaoAI Speaker Tools

### xiaoai/tts

Voice TTS announcement.

**Arguments**: `device_id`, `text`

### xiaoai/play_music

Play music or audio.

**Arguments**: `device_id`, `text` (natural language: "播放周杰伦的歌")

### xiaoai/control

Voice command for indirect device control.

**Arguments**: `device_id`, `command`, `silence` (opt, default true)

---

## Tuya Platform Tools

### auth/tuya_qr

**Arguments**: `user_code` → Generate QR code for Tuya app scanning.

### auth/tuya_qr_status

**Arguments**: `token`, `user_code` → Poll scan status.

### auth/tuya_logout

**Arguments**: None

### tuya/refresh

**Arguments**: None → Re-fetch Tuya devices.

### get_tuya_device_properties

**Arguments**: `deviceId` → All DP property values.

### set_tuya_device_property

**Arguments**: `deviceId`, `code` (DP code like `switch_1`), `value` → Set DP value.

**Free 90-day trial available** (platform login required); license required after trial expiry.

---

## Midea Platform Tools

### auth/midea_login

**Arguments**: `account`, `password`, `cloud` (opt)

### auth/midea_logout

### midea/refresh

### get_midea_device_properties

**Arguments**: `deviceId`

### set_midea_device_property

**Arguments**: `deviceId`, `property`, `value`

**Free trial / license required after expiry.**

---

## eWeLink Platform Tools

### auth/ewelink_login

**Arguments**: `email`, `password`, `country_code` (opt)

### auth/ewelink_logout

### ewelink/refresh

### get_ewelink_device_properties

**Arguments**: `deviceId`

### set_ewelink_device_property

**Arguments**: `deviceId`, `property`, `value`

**Free trial / license required after expiry.**

---

## Automation Tools

### Schedule

| Tool | Key Arguments |
|------|---------------|
| `schedule/add` | `name`, `scheduled_time` (ISO 8601, e.g. `2026-05-16T23:00:00+08:00`), `tool_name`, `tool_args` (JSON string), `repeat` (none/daily/weekdays/weekends/weekly/custom), `repeat_days` (JSON array string, 0=Sun) |
| `schedule/list` | `status` (opt) |
| `schedule/get` | `id` |
| `schedule/update` | `id`, fields to update |
| `schedule/delete` | `id` |
| `schedule/cancel` | `id` |

### Trigger Engine

| Tool | Key Arguments |
|------|---------------|
| `trigger/create` | `name`, `cameras`, `condition`, `actions` |
| `trigger/list` | — |
| `trigger/update` | `id`, fields to update |
| `trigger/delete` | `id` |
| `trigger/toggle` | `id`, `enabled` |
| `trigger/logs` | `limit`, `rule_id` (opt) |

---

## System Tools

### License

| Tool | Arguments |
|------|-----------|
| `license/status` | None → `{ edition, status, guidance }` |
| `license/set` | `license_key` (format: FG-XXXX-XXXX-XXXX), `product` (opt) |
| `license/clear` | None |

### Config

| Tool | Arguments |
|------|-----------|
| `config/get_vision` | None |
| `config/set_vision` | `enabled`, `api_key`, `base_url`, `model`, `temperature`, `max_tokens`, `timeout_seconds` |
| `config/get_trigger` | None |
| `config/set_trigger` | `enabled`, `interval_seconds`, `vision_img_count`, `motion_threshold` |

### Stats

| Tool | Arguments |
|------|-----------|
| `stats/token_usage` | `days` (opt) |
| `stats/token_records` | `limit` (opt) |
| `stats/trigger_summary` | `days` (opt) |
| `stats/dashboard` | None |

### Xiaozhi AI Platform

| Tool | Arguments |
|------|-----------|
| `xiaozhi/status` | None → connection state for all clients |
| `xiaozhi/list` | None → list configured endpoints |
| `xiaozhi/add` | `endpoint` (ws:// or wss:// URL) |
| `xiaozhi/remove` | `index` (int) |
| `xiaozhi/set_endpoint` | `endpoint` (opt, ws:// or wss:// URL; empty to disable) — legacy single-endpoint |

---

## Configuration Reference

```yaml
server:
  http_port: 38080
  bind_address: "0.0.0.0"
  webui_dir: "webui"

auth:
  cloud_server: "cn"
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
  endpoint: ""
  reconnect_interval_ms: 5000

vision:
  enabled: false
  api_key: ""
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o"

trigger:
  enabled: false
  interval_seconds: 2
  vision_img_count: 6
  motion_threshold: 5

memory:
  enabled: true
  data_dir: "data/memory"
  max_daily_files: 90

skill:
  enabled: true
  user_dir: "data/skills"
  builtin_dir: "skills"
```

## Error Responses

MCP errors follow JSON-RPC 2.0 error format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": { "code": -32602, "message": "camera_id is required" }
}
```

License-required errors:

```json
{
  "success": false,
  "error": "license_required",
  "message": "涂鸦平台免费试用已到期。米家仍可永久使用，其他平台需授权版解锁。",
  "guidance": "请联系代理商获取授权码(格式: FG-XXXX-XXXX-XXXX)，使用 license/set 工具写入后即可解锁全部平台。"
}
```
