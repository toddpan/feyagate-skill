# FeyaGate Skill — 快速开始

## 一键安装（推荐）

打开终端，复制粘贴一行命令即可完成安装：

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

默认安装到 `~/feyagate-skill`，自定义目录：

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash -s -- --dir ~/my-skill
```

## 手动安装

### macOS / Linux

```bash
git clone https://github.com/toddpan/feyagate-skill.git
cd feyagate-skill

# 下载发布包（Linux x86_64 为例，请替换为最新版本号）
mkdir -p packages
curl -L -o packages/miloco-mcp-server-VERSION-Linux-x86_64.tar.gz \
  "https://oneapi.sooncore.com/ota/feyagate-skill/miloco-mcp-server-VERSION-Linux-x86_64.tar.gz"

# 安装（自动检测平台、解压、初始化）
bash scripts/setup.sh
```

### Windows

```cmd
git clone https://github.com/toddpan/feyagate-skill.git
cd feyagate-skill

:: 将下载的 .zip 放入 packages\ 目录
copy %USERPROFILE%\Downloads\miloco-mcp-server-*-Windows-x86_64.zip packages\

:: 安装
scripts\setup.bat
```

## 安装系统依赖

一键安装脚本**不包含**系统级动态库。启动前请确保安装以下依赖，否则会报 `cannot open shared object file` 错误。

**Ubuntu / Debian:**

```bash
sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7
```

> 若上述包名在你的发行版版本中不可用，可通过 `apt-cache search libfmt` 等命令查找对应包名。macOS 和 Windows 用户一般无需手动安装。

验证依赖是否满足：

```bash
ldd bin/miloco-mcp-server | grep "not found"
# 无输出则表示依赖齐全
```

## 启动服务

```bash
# macOS / Linux
bash scripts/start.sh

# Windows
scripts\start.bat
```

服务运行在: `http://localhost:38080/mcp/http`

## 米家账号授权（首次必须）

### 方式一：直接 API 调用（推荐）

```bash
# 1. 获取授权链接
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"xiaomi/auth_url","arguments":{}}}' \
  | python3 -m json.tool

# 2. 在浏览器中打开返回的 URL，登录米家账号

# 3. 登录后浏览器跳转到 https://127.0.0.1/?code=...（显示"无法访问"正常）
#    复制浏览器地址栏的完整 URL

# 4. 提交授权码（将下面的 CODE 替换为实际获取的 code 值）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"xiaomi/auth_callback","arguments":{"code":"CODE"}}}' \
  | python3 -m json.tool

# 5. 验证授权状态
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"xiaomi/auth_status","arguments":{}}}' \
  | python3 -m json.tool
```

### 方式二：使用 auth.py 脚本

```bash
python3 scripts/auth.py --status    # 检查授权状态
python3 scripts/auth.py             # 交互式授权
```

授权流程：
1. 获取授权链接（`xiaomi/auth_url`）
2. 在浏览器中打开链接，登录米家账号
3. 登录后浏览器跳转到 `https://127.0.0.1/?code=...`（显示"无法访问"正常）
4. 复制浏览器地址栏的完整 URL
5. 提取 `code` 参数，通过 `xiaomi/auth_callback` 完成授权

## 涂鸦平台授权

涂鸦 (Tuya) 使用 App 扫码授权，需要涂鸦智能或 Smart Life App。

### 1. 获取用户代码

在涂鸦智能 / Smart Life App 中：
- 打开 **我的 → 设置 → 账号与安全**
- 找到**用户代码**（如 `AxNmcp2`）

### 2. 生成二维码

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth/tuya_qr","arguments":{"user_code":"YOUR_USER_CODE"}}}' \
  | python3 -m json.tool
```

返回 `qr_url` 和 `token`（有效期 5 分钟）。

### 3. 扫码授权

将返回的 `qr_url` 转为二维码图片，用涂鸦 App 扫描并确认授权。

### 4. 查询扫码状态

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"auth/tuya_qr_status","arguments":{"token":"QR_TOKEN","user_code":"YOUR_USER_CODE"}}}' \
  | python3 -m json.tool
```

返回 `"status": "success"` 表示授权成功。

### 5. 刷新设备列表

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"tuya/refresh","arguments":{}}}' \
  | python3 -m json.tool
```

### 验证授权状态

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"auth/platforms","arguments":{}}}' \
  | python3 -m json.tool
```

## 美的平台授权

美的 (Midea) 使用美居 App 账号密码登录。

### 1. 登录

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth/midea_login","arguments":{"account":"YOUR_PHONE","password":"YOUR_PASSWORD"}}}' \
  | python3 -m json.tool
```

参数说明：
- `account`：美居 App 的手机号或邮箱
- `password`：美居 App 密码
- `cloud`（可选）：`meiju`（美居，默认）或 `msmart`（MSmartHome）

返回 `"authenticated": true` 表示登录成功，token 有效期 7200 秒（2 小时）。

### 2. 刷新设备列表

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"midea/refresh","arguments":{}}}' \
  | python3 -m json.tool
```

### 3. 列出美的设备

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":[],"platform":"midea"}}}' \
  | python3 -m json.tool
```

## 易微联平台授权

易微联 (eWeLink) 使用邮箱/手机号和密码登录。

### 1. 登录

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth/ewelink_login","arguments":{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD","country_code":"+86"}}}' \
  | python3 -m json.tool
```

参数说明：
- `email`：eWeLink / Sonoff App 的邮箱或手机号
- `password`：App 密码
- `country_code`（可选）：国家代码（如 `+86` 中国，默认）

返回 `"authenticated": true` 表示登录成功，token 有效期 30 天，WebSocket 自动连接。

### 2. 刷新设备列表

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"ewelink/refresh","arguments":{}}}' \
  | python3 -m json.tool
```

### 3. 列出易微联设备

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":[],"platform":"ewelink"}}}' \
  | python3 -m json.tool
```

## 设备管理

### 列出所有设备

```bash
# 列出全部设备
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":[]}}}' \
  | python3 -m json.tool

# 按关键词搜索（如：客厅的灯）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":["客厅","灯"]}}}' \
  | python3 -m json.tool

# 按平台过滤
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":[],"platform":"xiaomi"}}}' \
  | python3 -m json.tool
```

### 查看平台状态

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"platform/status","arguments":{}}}' \
  | python3 -m json.tool
```

## MIOT 设备控制

### 获取区域和设备类别

```bash
# 区域列表
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"xiaomi/get_area_info","arguments":{}}}' \
  | python3 -m json.tool

# 设备类别
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"xiaomi/get_device_classes","arguments":{}}}' \
  | python3 -m json.tool
```

### 按类别获取设备

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"xiaomi/get_devices","arguments":{"device_class":"light"}}}' \
  | python3 -m json.tool
```

### 查询设备 SPEC

```bash
# 注意：device/specs 使用 deviceId（camelCase）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"device/specs","arguments":{"deviceId":"YOUR_DID"}}}' \
  | python3 -m json.tool
```

### 控制设备

> **参数命名规则：** `device/specs` 使用 `deviceId`（camelCase）；小米设备控制工具（`xiaomi/*`）使用 `device_id`（snake_case）。

```bash
# 读取属性（需要 device_id、siid、piids）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"xiaomi/get_properties","arguments":{"device_id":"YOUR_DID","siid":2,"piids":[1]}}}' \
  | python3 -m json.tool

# 设置属性（例: 开灯 — siid:2 是灯服务，piid:1 是开关）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":15,"method":"tools/call","params":{"name":"xiaomi/set_property","arguments":{"device_id":"YOUR_DID","siid":"2","piid":"1","value":true}}}' \
  | python3 -m json.tool

# 执行动作（例: Toggle 开关切换）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":16,"method":"tools/call","params":{"name":"xiaomi/execute_action","arguments":{"device_id":"YOUR_DID","siid":"2","aiid":"1"}}}' \
  | python3 -m json.tool
```

**控制流程说明：**
1. `device/list` — 按关键词/平台搜索找到目标设备
2. `device/specs` — 查询设备的 `siid`（服务ID）、`piid`（属性ID）、`aiid`（动作ID）定义
3. `xiaomi/get_properties` — 读取属性当前值（参数：`device_id`, `siid`, `piids` 数组）
4. `xiaomi/set_property` — 设置属性值（参数：`device_id`, `siid`, `piid`, `value`）
5. `xiaomi/execute_action` — 执行设备动作（参数：`device_id`, `siid`, `aiid`）

### 场景管理

```bash
# 列出场景（需指定 platform）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":17,"method":"tools/call","params":{"name":"scene/list","arguments":{"platform":"xiaomi"}}}' \
  | python3 -m json.tool

# 触发场景（需指定 platform 和 sceneId）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":18,"method":"tools/call","params":{"name":"scene/trigger","arguments":{"platform":"xiaomi","sceneId":"SCENE_ID"}}}' \
  | python3 -m json.tool
```

## 小爱音箱控制

```bash
# 查找音箱
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":30,"method":"tools/call","params":{"name":"device/list","arguments":{"filter":["音箱","wifispeaker"]}}}' \
  | python3 -m json.tool

# TTS 语音播报
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":31,"method":"tools/call","params":{"name":"xiaoai/tts","arguments":{"device_id":"SPEAKER_DID","text":"你好，欢迎回家"}}}' \
  | python3 -m json.tool

# 播放音乐
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":32,"method":"tools/call","params":{"name":"xiaoai/play_music","arguments":{"device_id":"SPEAKER_DID","text":"播放周杰伦的歌"}}}' \
  | python3 -m json.tool

# 语音控制设备（静默模式）
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":33,"method":"tools/call","params":{"name":"xiaoai/control","arguments":{"device_id":"SPEAKER_DID","command":"打开客厅灯","silence":true}}}' \
  | python3 -m json.tool
```

## 摄像头操作

```bash
# 连接摄像头
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"xiaomi/camera_connect","arguments":{"camera_id":"CAMERA_DID"}}}'

# 等待 P2P 建立
sleep 3

# 查看状态
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"xiaomi/camera_status","arguments":{}}}' \
  | python3 -m json.tool

# 拍摄快照
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"xiaomi/camera_snapshot","arguments":{"camera_id":"CAMERA_DID","count":1}}}' \
  | python3 -m json.tool

# 断开
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"xiaomi/camera_disconnect","arguments":{"camera_id":"CAMERA_DID"}}}'
```

### 脚本工具

```bash
python3 scripts/snapshot.py --list
python3 scripts/snapshot.py --connect CAMERA_DID --count 3
```

### 定时 AI 分析

```bash
python3 scripts/scheduled_analysis.py \
  --camera-id CAMERA_DID \
  --interval 300 \
  --auto-connect \
  --prompt "Describe the scene. Flag any security concerns."
```

## 服务管理

```bash
# macOS / Linux
bash scripts/health_check.sh     # 健康检查
bash scripts/stop.sh             # 停止服务

# Windows
scripts\health_check.bat
scripts\stop.bat
```

## 在线升级

检查是否有新版本（不执行升级）：

```bash
# macOS / Linux
bash scripts/upgrade.sh --check

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Check
```

执行升级（交互式确认）：

```bash
# macOS / Linux
bash scripts/upgrade.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1
```

非交互模式（自动确认，适合自动化/脚本调用）：

```bash
# macOS / Linux
bash scripts/upgrade.sh --yes

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Yes
```

升级流程自动执行：停止服务 → 备份 → 下载新版本 → MD5 校验 → 解压安装 → 更新版本号 → 重启服务 → 健康检查。如果任何步骤失败，将自动回滚到之前的版本。

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| `connection refused` | 运行 `bash scripts/start.sh` 启动服务 |
| `authorized: false` | 通过 `xiaomi/auth_url` 获取授权链接完成授权 |
| `cannot open shared object file` | 安装系统依赖：`sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7` |
| `Tool not found` | 检查工具名是否正确，使用 `tools/list` 查看所有可用工具 |
| `key 'device_id' not found` | `device/specs` 用 `deviceId`（camelCase）；平台工具用 `device_id`（snake_case） |
| `key 'siid' not found` | 需使用 `xiaomi/get_properties` 等工具，并传入 `siid`/`piids` 参数 |
| `camera_connect` 失败 | 检查 `lib/` 是否有摄像头原生库 |
| 无帧数据 | 等待 3-5 秒，检查 `xiaomi/camera_status` |
| 动态库加载失败 | 运行 `ldd bin/miloco-mcp-server \| grep "not found"` 查看缺失库 |

更多信息见 [SKILL.md](SKILL.md)、[FeyaGate_MCP_API.md](FeyaGate_MCP_API.md) 和 [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md)。
