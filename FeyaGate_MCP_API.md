# FeyaGate MCP WebSocket API 文档

> **网关版本**: v1.2.14+  
> **协议**: MCP (Model Context Protocol) JSON-RPC 2.0  
> **WebSocket 端点**: `ws://<网关IP>:8765/mcp`  
> **Streamable HTTP 端点**: `POST http://<网关IP>:8765/mcp/http`  
> **协议版本**: `2025-03-26`

---

## 目录

- [1. 连接指南](#1-连接指南)
- [2. JSON-RPC 2.0 规范](#2-json-rpc-20-规范)
- [3. 初始化 (initialize)](#3-初始化-initialize)
- [4. 内置 Tools (27 个)](#4-内置-tools-27-个)
- [5. 错误码](#5-错误码)
- [6. 小智平台集成](#6-小智平台集成)

---

## 1. 连接指南

### WebSocket 连接

```javascript
// JavaScript 示例
const ws = new WebSocket('ws://feyagate.local:8765/mcp');

ws.onopen = () => {
  // 发送 initialize 握手
  ws.send(JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "MyApp", version: "1.0.0" }
    }
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log('收到:', msg);
};
```

### Streamable HTTP 连接

```bash
curl -X POST http://feyagate.local:8765/mcp/http \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{}}}'
```

初始化成功后，响应头会附带 `Mcp-Session-Id`，后续请求携带该 Header 可维持会话。

---

## 2. JSON-RPC 2.0 规范

### 请求结构

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "device/list",
    "arguments": { "filter": ["客厅", "灯"] }
  }
}
```

### 成功响应

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"deviceId\":\"xxx\",\"name\":\"客厅主灯\",...}]"
      }
    ],
    "isError": false
  }
}
```

### 错误响应

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Tool not found: unknown/tool"
  }
}
```

---

## 3. 初始化 (initialize)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": { "name": "MyClient", "version": "1.0.0" }
  }
}
```

**响应**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": { "tools": {}, "resources": {} },
    "serverInfo": { "name": "FeyaGate-Gateway", "version": "v1.2.14" }
  }
}
```

---

## 4. 内置 Tools (27 个)

所有工具通过 `tools/list` 获取元信息，通过 `tools/call` 执行。

### 4.1 通用工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `device/list` | 获取智能设备列表（支持关键词过滤 + 平台过滤） | `filter` |
| `device/specs` | 查询指定设备的规格说明书（属性/action 列表） | `deviceId` |

#### `device/list`

列出所有已导入的智能设备，支持关键词模糊匹配（子串、分词、模糊字符）。

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filter` | `string[]` | ✅ | 过滤关键词，如 `["客厅", "灯"]`，匹配 name/room/model/category/deviceId/platform |
| `platform` | `string` | ❌ | 平台过滤: `xiaomi` / `tuya` / `midea` / `ewelink` / `serial` / `gpio` |

**中文平台别名自动映射**: `串口` → `serial`, `GPIO` → `gpio`, `小米` → `xiaomi`, `涂鸦` → `tuya`

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "device/list",
    "arguments": { "filter": ["客厅"], "platform": "xiaomi" }
  }
}
```

#### `device/specs`

查询设备的规格说明书，返回属性列表（siid/piid/DP code）、Action 定义及参数格式。

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `deviceId` | `string` | ✅ | 设备 ID |

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "device/specs",
    "arguments": { "deviceId": "xxx" }
  }
}
```

---

### 4.2 场景管理

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `scene/list` | 获取指定平台的场景列表 | `platform` |
| `scene/trigger` | 触发执行指定场景 | `platform`, `sceneId` |

---

### 4.3 状态查询

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `platform/status` | 查看各 IoT 平台连接/认证/设备同步状态 | — |
| `gateway/info` | 获取网关系统信息（固件版本、设备总数/在线数、MCP 端口等） | — |

---

### 4.4 小米 (Xiaomi) 平台工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `xiaomi/get_properties` | 读取小米设备属性（siid + piids） | `device_id`, `siid`, `piids` |
| `xiaomi/set_property` | 设置小米设备属性（开关、亮度、色温等） | `device_id`, `siid`, `piid`, `value` |
| `xiaomi/execute_action` | 执行小米设备动作（重启、校准、自清洁等） | `device_id`, `siid`, `aiid` |

**小米 `set_property` 示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "xiaomi/set_property",
    "arguments": { "device_id": "xxx", "siid": "2", "piid": "1", "value": true }
  }
}
```

---

### 4.5 涂鸦 (Tuya) 平台工具

#### 授权工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `auth/tuya_qr` | 获取涂鸦 QR 码授权，返回 qr_url 和 token | `user_code` |
| `auth/tuya_qr_status` | 查询 QR 码扫码授权状态 | `token`, `user_code` |
| `tuya/refresh` | 刷新涂鸦设备列表（授权后调用） | — |
| `auth/tuya_logout` | 退出涂鸦平台授权 | — |

**QR 码授权流程**:

1. 在涂鸦智能 / Smart Life App 中获取用户代码：**我的 → 设置 → 账号与安全**
2. 调用 `auth/tuya_qr`，传入 `user_code`，获取 `qr_url` 和 `token`（有效期 5 分钟）
3. 将 `qr_url` 转为二维码图片，用涂鸦 App 扫描并确认
4. 调用 `auth/tuya_qr_status` 轮询扫码状态，返回 `"status": "success"` 表示授权成功
5. 调用 `tuya/refresh` 刷新设备列表

#### 设备控制工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `tuya/get_properties` | 读取涂鸦设备 DP 属性（不传 codes 返回全部） | `device_id` |
| `tuya/set_property` | 设置涂鸦设备 DP 属性值 | `device_id`, `code`, `value` |

---

### 4.6 美的 (Midea) 平台工具

#### 授权工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `auth/midea_login` | 美的账号密码登录（美居/MSmartHome） | `account`, `password` |
| `midea/refresh` | 刷新美的设备列表（登录后调用） | — |
| `auth/midea_logout` | 退出美的平台授权 | — |

**账号登录流程**:

1. 调用 `auth/midea_login`，传入美居 App 的 `account`（手机号/邮箱）和 `password`
2. 可选参数 `cloud`: `meiju`（美居，默认）或 `msmart`（MSmartHome）
3. 登录成功后自动选择家庭，token 有效期 7200 秒（2 小时）
4. 调用 `midea/refresh` 刷新设备列表

**登录示例**:
```json
{
  "name": "auth/midea_login",
  "arguments": {
    "account": "13800138000",
    "password": "your_password",
    "cloud": "meiju"
  }
}
```

#### 设备控制工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `midea/get_properties` | 读取美的设备属性（电源、温度、模式、风速等） | `device_id` |
| `midea/set_property` | 设置美的设备属性 | `device_id`, `property`, `value` |
| `midea/execute_action` | 执行美的设备动作 | `device_id`, `action` |

**美的属性常用值**:
- `power`: `0` / `1` (关/开)
- `temperature`: 数字 (如 `26`)
- `mode`: 字符串 (如 `cool`, `heat`, `auto`)
- `fan_speed`: 字符串 (如 `low`, `medium`, `high`)

---

### 4.7 易微联 (eWeLink) 平台工具

#### 授权工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `auth/ewelink_login` | 易微联账号密码登录 | `email`, `password` |
| `ewelink/refresh` | 刷新易微联设备列表（登录后调用） | — |
| `auth/ewelink_logout` | 退出易微联平台授权 | — |

**账号登录流程**:

1. 调用 `auth/ewelink_login`，传入 eWeLink App 的 `email`（邮箱/手机号）和 `password`
2. 可选参数 `country_code`: 国家代码（如 `+86` 中国，`+1` 美国）
3. 登录成功后自动建立 WebSocket 连接，token 有效期 2592000 秒（30 天）
4. 调用 `ewelink/refresh` 刷新设备列表

**登录示例**:
```json
{
  "name": "auth/ewelink_login",
  "arguments": {
    "email": "user@example.com",
    "password": "your_password",
    "country_code": "+86"
  }
}
```

#### 设备控制工具

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `ewelink/get_properties` | 读取易微联设备属性 | `device_id` |
| `ewelink/set_property` | 设置易微联设备属性 | `device_id`, `property`, `value` |
| `ewelink/execute_action` | 执行易微联设备动作 | `device_id`, `action` |

**易微联 `set_property`**:
- `switch`: `on` / `off`
- `switches`: JSON 数组, 如 `[{"switch": "on", "outlet": 0}]` (多路开关)

---

### 4.8 房间管理

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `room/list` | 获取去重后的房间名称列表 | — |
| `room/set_device` | 批量设置设备所属房间 | `device_ids`, `room_name` |

---

### 4.9 小爱音箱控制

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `xiaoai/play_music` | 控制小爱音箱播放音乐/故事/调整音量 | `device_id`, `text` |
| `xiaoai/tts` | 通过小爱音箱朗读文本 (TTS) | `device_id`, `text` |
| `xiaoai/control` | 通过小爱音箱语音指令间接控制设备 | `device_id`, `command` |

**小爱 `control` 示例**:
```json
{
  "name": "xiaoai/control",
  "arguments": { "device_id": "xxx", "command": "打开客厅灯", "silence": true }
}
```

---

### 4.10 记忆系统

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `memory/read` | 读取长期记忆 | — |
| `memory/add` | 添加长期记忆 | `content` |
| `memory/update` | 更新记忆条目 | `id`, `content` |
| `memory/delete` | 删除记忆条目 | `id` |
| `memory/search` | 关键词搜索记忆 | `keyword` |
| `memory/note` | 添加今日笔记 | `content` |
| `memory/today` | 读取今日笔记 | — |

**存储格式**:
- **长期记忆**: `/spiffs/MEMORY.md` — 自由格式 Markdown，整体读写
- **每日笔记**: `/spiffs/mem_YYYY-MM-DD.md` — 每天独立文件，追加模式

---

### 4.11 技能系统

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `skill/list` | 获取可用技能列表 | — |
| `skill/read` | 读取技能详细指令 | `id` |
| `skill/manage` | 管理技能 (添加/更新/删除) | `action` + 其他 |

**技能存储**: 索引 `/spiffs/skills.json`，内容 `/spiffs/skill_{id}.md`

---

### 4.12 定时任务

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `schedule/add` | 添加定时任务 (一次性/重复) | `name`, `scheduledTime`, `toolName`, `toolArgs` |
| `schedule/list` | 获取任务列表 | — |
| `schedule/get` | 获取单个任务详情 | `id` |
| `schedule/update` | 修改任务时间/重复设置 | `id` + 其他 |
| `schedule/delete` | 删除任务 | `id` |
| `schedule/cancel` | 取消待执行任务 | `id` |

**重复类型**: `none` / `daily` / `weekdays` / `weekends` / `weekly` / `custom_days`

---

### 4.13 串口扩展设备

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `serial/get_properties` | 读取串口设备属性 | `device_id`, `siid`, `piids` |
| `serial/set_property` | 设置串口设备属性 | `device_id`, `siid`, `piid`, `value` |
| `serial/execute_action` | 执行串口设备动作 | `device_id`, `siid`, `aiid` |

---

### 4.14 GPIO 设备

| 工具名称 | 描述 | 必填参数 |
|---------|------|---------|
| `gpio/get_properties` | 读取 GPIO 设备属性 | `device_id`, `siid`, `piids` |
| `gpio/set_property` | 设置 GPIO 设备属性 | `device_id`, `siid`, `piid`, `value` |
| `gpio/execute_action` | 执行 GPIO 设备动作 | `device_id`, `siid`, `aiid` |

---

## 5. 错误码

遵循 JSON-RPC 2.0 标准错误码 + MCP 扩展:

| 错误码 | 含义 |
|--------|------|
| `-32700` | 解析错误 (Invalid JSON) |
| `-32601` | 方法/工具不存在 |
| `-32602` | 参数错误 (缺少必填参数) |
| `-32603` | 内部错误 (服务器异常) |
| `-32600` | 非法请求 |

---

## 6. 小智平台集成

FeyaGate 内置 `XiaozhiManager`，管理最多 3 个并行小智 AI 连接。

### 工作流

1. 小智客户端通过 WebSocket 连接 FeyaGate MCP Server
2. `XiaozhiManager` 将网关所有已注册工具同步到小智工具注册表
3. 小智 AI 解析用户意图 → 调用 MCP `tools/call` → FeyaGate 执行 → 结果返回小智 → 小智语音播报

### 工具同步

每次小智客户端连接成功后，`McpServer.registerToolsToXiaozhi()` 自动将全部 27 个内置工具注册到小智工具集。

### 通知机制

网关可通过 `McpServer.broadcastNotification()` 向所有已连接客户端推送事件（如设备状态变更、定时任务执行结果等）。

---

## 附录 A: 完整请求/响应示例

### 查询客厅所有设备

```bash
curl -X POST http://feyagate.local:8765/mcp/http \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {}
    }
  }'
```

### 控制小米设备

```bash
curl -X POST http://feyagate.local:8765/mcp/http \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "xiaomi/set_property",
      "arguments": {
        "device_id": "1234567890",
        "siid": "2",
        "piid": "1",
        "value": true
      }
    }
  }'
```

### 添加记忆

```bash
curl -X POST http://feyagate.local:8765/mcp/http \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "memory/add",
      "arguments": {
        "content": "用户偏好: 晚上 10 点后喜欢把客厅灯调暗到 30%",
        "category": "偏好"
      }
    }
  }'
```
