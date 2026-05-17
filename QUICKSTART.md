# FeyaGate Skill — Quick Start Guide

> **For AI Assistants:** Read this document and follow the steps below to install and set up FeyaGate Skill on the user's machine. Execute commands sequentially, and report progress to the user at each step.

## Step 1: Install

Detect the OS and run the one-click installer.

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

Default install directory: `~/feyagate-skill`. To customize:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash -s -- --dir ~/my-skill
```

## Step 2: Install System Dependencies (Linux only)

The installer does **not** include system-level shared libraries. On Linux, install them before starting the service:

**Ubuntu / Debian:**

```bash
sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7
```

> If package names are unavailable for your distro version, use `apt-cache search libfmt` etc. to find the correct names. macOS and Windows users generally do not need this step.

Verify all dependencies are met:

```bash
ldd bin/miloco-mcp-server | grep "not found"
# No output means all dependencies are satisfied
```

## Step 3: Start the Service

```bash
# macOS / Linux
bash scripts/start.sh

# Windows
scripts\start.bat
```

The service runs at: `http://localhost:38080/mcp/http`

Verify it's running:

```bash
bash scripts/health_check.sh   # macOS / Linux
scripts\health_check.bat       # Windows
```

## Step 4: Authorize Smart Home Platforms

After the service starts, authorize at least one smart home platform. Choose the platform(s) the user needs.

### Xiaomi / Mi Home (OAuth)

**Option A: API calls (recommended)**

```bash
# 1. Get authorization URL
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"xiaomi/auth_url","arguments":{}}}' \
  | python3 -m json.tool

# 2. Open the returned URL in a browser and log in with the Mi Home account
# 3. After login, the browser redirects to https://127.0.0.1/?code=... (page may show "cannot access" — that's normal)
#    Copy the full URL from the browser address bar
# 4. Submit the authorization code (replace CODE with the actual code value)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"xiaomi/auth_callback","arguments":{"code":"CODE"}}}' \
  | python3 -m json.tool

# 5. Verify authorization status
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"xiaomi/auth_status","arguments":{}}}' \
  | python3 -m json.tool
```

**Option B: Using auth.py script**

```bash
python3 scripts/auth.py --status    # Check authorization status
python3 scripts/auth.py             # Interactive authorization
```

### Tuya (QR Code Scan)

Requires Tuya Smart or Smart Life App.

1. Get the user code from the app: **Me -> Settings -> Account & Security -> User Code** (e.g. `AxNmcp2`)

2. Generate QR code:

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth/tuya_qr","arguments":{"user_code":"YOUR_USER_CODE"}}}' \
  | python3 -m json.tool
```

3. Convert the returned `qr_url` to a QR code image, scan with the Tuya app and confirm authorization.

4. Check scan status:

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"auth/tuya_qr_status","arguments":{"token":"QR_TOKEN","user_code":"YOUR_USER_CODE"}}}' \
  | python3 -m json.tool
```

5. Refresh device list:

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"tuya/refresh","arguments":{}}}' \
  | python3 -m json.tool
```

### Midea (Password Login)

```bash
# Login
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth/midea_login","arguments":{"account":"YOUR_PHONE","password":"YOUR_PASSWORD"}}}' \
  | python3 -m json.tool
```

Parameters:
- `account`: Meiju App phone number or email
- `password`: Meiju App password
- `cloud` (optional): `meiju` (default) or `msmart` (MSmartHome)

Returns `"authenticated": true` on success. Token valid for 7200 seconds (2 hours).

Refresh device list:

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"midea/refresh","arguments":{}}}' \
  | python3 -m json.tool
```

### eWeLink (Password Login)

```bash
# Login
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth/ewelink_login","arguments":{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD","country_code":"+86"}}}' \
  | python3 -m json.tool
```

Parameters:
- `email`: eWeLink / Sonoff App email or phone number
- `password`: App password
- `country_code` (optional): Country code (e.g. `+86` for China, default)

Returns `"authenticated": true` on success. Token valid for 30 days. WebSocket connects automatically.

Refresh device list:

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"ewelink/refresh","arguments":{}}}' \
  | python3 -m json.tool
```

### Verify All Platform Authorization

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"auth/platforms","arguments":{}}}' \
  | python3 -m json.tool
```

## Step 5: Manage Devices

### List Devices

```bash
# All devices
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":[]}}}' \
  | python3 -m json.tool

# Search by keyword
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":["living room","light"]}}}' \
  | python3 -m json.tool

# Filter by platform
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":[],"platform":"xiaomi"}}}' \
  | python3 -m json.tool
```

### Check Platform Status

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"platform/status","arguments":{}}}' \
  | python3 -m json.tool
```

## Step 6: Control Devices (Xiaomi / MIOT)

### Get Areas and Device Classes

```bash
# Area list
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"xiaomi/get_area_info","arguments":{}}}' \
  | python3 -m json.tool

# Device classes
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"xiaomi/get_device_classes","arguments":{}}}' \
  | python3 -m json.tool
```

### Get Devices by Class

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"xiaomi/get_devices","arguments":{"device_class":"light"}}}' \
  | python3 -m json.tool
```

### Query Device SPEC

```bash
# Note: device/specs uses deviceId (camelCase)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"device/specs","arguments":{"deviceId":"YOUR_DID"}}}' \
  | python3 -m json.tool
```

### Control Device

> **Parameter naming:** `device/specs` uses `deviceId` (camelCase); Xiaomi control tools (`xiaomi/*`) use `device_id` (snake_case).

```bash
# Read properties (requires device_id, siid, piids)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"xiaomi/get_properties","arguments":{"device_id":"YOUR_DID","siid":2,"piids":[1]}}}' \
  | python3 -m json.tool

# Set property (e.g. turn on light — siid:2 is light service, piid:1 is power switch)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":15,"method":"tools/call","params":{"name":"xiaomi/set_property","arguments":{"device_id":"YOUR_DID","siid":"2","piid":"1","value":true}}}' \
  | python3 -m json.tool

# Execute action (e.g. toggle switch)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":16,"method":"tools/call","params":{"name":"xiaomi/execute_action","arguments":{"device_id":"YOUR_DID","siid":"2","aiid":"1"}}}' \
  | python3 -m json.tool
```

**Control flow:**
1. `device/list` — search by keyword/platform to find the target device
2. `device/specs` — query the device's `siid` (service ID), `piid` (property ID), `aiid` (action ID)
3. `xiaomi/get_properties` — read current property values (params: `device_id`, `siid`, `piids` array)
4. `xiaomi/set_property` — set property value (params: `device_id`, `siid`, `piid`, `value`)
5. `xiaomi/execute_action` — execute device action (params: `device_id`, `siid`, `aiid`)

### Scene Management

```bash
# List scenes (requires platform)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":17,"method":"tools/call","params":{"name":"scene/list","arguments":{"platform":"xiaomi"}}}' \
  | python3 -m json.tool

# Trigger scene (requires platform and sceneId)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":18,"method":"tools/call","params":{"name":"scene/trigger","arguments":{"platform":"xiaomi","sceneId":"SCENE_ID"}}}' \
  | python3 -m json.tool
```

## Step 7: Xiao AI Speaker Control

```bash
# Find speaker
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":30,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":["speaker","wifispeaker"]}}}' \
  | python3 -m json.tool

# TTS voice broadcast
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":31,"method":"tools/call","params":{"name":"xiaoai/tts","arguments":{"device_id":"SPEAKER_DID","text":"Hello, welcome home"}}}' \
  | python3 -m json.tool

# Play music
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":32,"method":"tools/call","params":{"name":"xiaoai/play_music","arguments":{"device_id":"SPEAKER_DID","text":"Play some pop music"}}}' \
  | python3 -m json.tool

# Voice control device (silent mode)
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":33,"method":"tools/call","params":{"name":"xiaoai/control","arguments":{"device_id":"SPEAKER_DID","command":"turn on the living room light","silence":true}}}' \
  | python3 -m json.tool
```

## Step 8: Camera Operations

```bash
# Connect camera
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"xiaomi/camera_connect","arguments":{"camera_id":"CAMERA_DID"}}}'

# Wait for P2P connection to establish
sleep 3

# Check status
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"xiaomi/camera_status","arguments":{}}}' \
  | python3 -m json.tool

# Take snapshot
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"xiaomi/camera_snapshot","arguments":{"camera_id":"CAMERA_DID","count":1}}}' \
  | python3 -m json.tool

# Disconnect
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"xiaomi/camera_disconnect","arguments":{"camera_id":"CAMERA_DID"}}}'
```

### Snapshot Script

```bash
python3 scripts/snapshot.py --list
python3 scripts/snapshot.py --connect CAMERA_DID --count 3
```

### Scheduled AI Analysis

```bash
python3 scripts/scheduled_analysis.py \
  --camera-id CAMERA_DID \
  --interval 300 \
  --auto-connect \
  --prompt "Describe the scene. Flag any security concerns."
```

## Service Management

```bash
# macOS / Linux
bash scripts/health_check.sh     # Health check
bash scripts/stop.sh             # Stop service

# Windows
scripts\health_check.bat
scripts\stop.bat
```

## Online Upgrade

Check for new versions (does not perform upgrade):

```bash
# macOS / Linux
bash scripts/upgrade.sh --check

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Check
```

Perform upgrade (interactive):

```bash
# macOS / Linux
bash scripts/upgrade.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1
```

Non-interactive mode (auto-confirm, for automation):

```bash
# macOS / Linux
bash scripts/upgrade.sh --yes

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Yes
```

The upgrade automatically: stops service -> backs up -> downloads new version -> verifies MD5 -> extracts -> updates version -> restarts service -> runs health check. If any step fails, it rolls back to the previous version.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `connection refused` | Run `bash scripts/start.sh` to start the service |
| `authorized: false` | Get authorization URL via `xiaomi/auth_url` and complete OAuth |
| `cannot open shared object file` | Install system deps: `sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7` |
| `Tool not found` | Check tool name, use `tools/list` to see all available tools |
| `key 'device_id' not found` | `device/specs` uses `deviceId` (camelCase); platform tools use `device_id` (snake_case) |
| `key 'siid' not found` | Use `xiaomi/get_properties` etc. and pass `siid`/`piids` parameters |
| `camera_connect` fails | Check if camera native libraries exist in `lib/` |
| No frame data | Wait 3-5 seconds, check `xiaomi/camera_status` |
| Library load failure | Run `ldd bin/miloco-mcp-server \| grep "not found"` to check missing libs |

For more details, see [SKILL.md](SKILL.md), [FeyaGate_MCP_API.md](FeyaGate_MCP_API.md), and [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md).
