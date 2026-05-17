# FeyaGate HTTP REST API 文档

> **网关版本**: v1.2.14+  
> **基础 URL**: `http://<网关IP>:8080` 或 `http://feyagate.local:8080`  
> **Content-Type**: `application/json`  
> **CORS**: 全局开放 `Access-Control-Allow-Origin: *`

---

## 目录

- [1. 鉴权说明](#1-鉴权说明)
- [2. 错误码定义](#2-错误码定义)
- [3. 系统管理](#3-系统管理)
- [4. WiFi 管理](#4-wifi-管理)
- [5. 平台认证](#5-平台认证)
- [6. 设备管理](#6-设备管理)
- [7. 设备控制](#7-设备控制)
- [8. 场景管理](#8-场景管理)
- [9. MCP 配置](#9-mcp-配置)
- [10. 小智平台](#10-小智平台)
- [11. MCP 代理](#11-mcp-代理)
- [12. 记忆管理](#12-记忆管理)
- [13. 技能管理](#13-技能管理)
- [14. 定时任务](#14-定时任务)
- [15. OTA 管理](#15-ota-管理)
- [16. 设备授权](#16-设备授权)
- [17. GPIO 开关](#17-gpio-开关)

---

## 1. 鉴权说明

当前版本所有 API 端点**无需鉴权**，在局域网内可直接调用。  
生产环境建议通过路由器防火墙限制访问。

---

## 2. 错误码定义

所有接口统一返回 JSON 格式：

```json
// 成功
{"code": 200, "message": "ok", "data": { ... }}

// 失败
{"code": 400, "message": "错误描述", "data": null}
```

| HTTP 状态码 | 含义 |
|-------------|------|
| 200 | 成功 |
| 201 | 已创建 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 3. 系统管理

### 3.1 获取网关基本信息

```
GET /api/v1/gateway/info
```

**响应示例**:
```json
{
  "version": "v1.2.14",
  "chipModel": "ESP32-S3",
  "flashSize": 16777216,
  "psramSize": 8388608,
  "macAddress": "AA:BB:CC:DD:EE:FF",
  "uptime": 3600,
  "freeHeap": 125000,
  "freePsram": 6200000,
  "mcpPort": 8765,
  "apiPort": 8080
}
```

### 3.2 获取系统状态

```
GET /api/v1/gateway/status
```

**响应示例**:
```json
{
  "freeHeap": 125000,
  "minFreeHeap": 98000,
  "freePsram": 6200000,
  "minFreePsram": 5100000,
  "uptime": 3600,
  "taskCount": 18,
  "sdkVersion": "5.5.0"
}
```

### 3.3 重启网关

```
POST /api/v1/gateway/restart
Content-Type: application/json
```

**请求体**: 无需参数

**响应**:
```json
{"code": 200, "message": "网关将在 3 秒后重启", "data": null}
```

### 3.4 重新配网

```
POST /api/v1/gateway/reprovision
```

触发 BluFi 蓝牙配网模式（等同于长按 GPIO5），网关将重启进入配网状态。

### 3.5 获取/设置/清除授权

```
GET    /api/v1/gateway/license
POST   /api/v1/gateway/license
DELETE /api/v1/gateway/license
```

**GET 响应**:
```json
{
  "edition": "pro",
  "status": "active",
  "product": "feyagate_ty1",
  "licenseKey": "FG-xxxx-xxxx-xxxx"
}
```

**POST 请求体**:
```json
{
  "license_key": "FG-XXXX-XXXX-XXXX",
  "product": "feyagate_ty1"
}
```

---

## 4. WiFi 管理

### 4.1 获取 WiFi 状态

```
GET /api/v1/wifi/status
```

**响应**:
```json
{
  "connected": true,
  "ssid": "MyHome",
  "bssid": "AA:BB:CC:DD:EE:FF",
  "rssi": -52,
  "ip": "192.168.1.100",
  "gateway": "192.168.1.1",
  "subnet": "255.255.255.0",
  "dns": "192.168.1.1",
  "mode": "STA"
}
```

### 4.2 配置 WiFi

```
POST /api/v1/wifi/config
```

**请求体**:
```json
{
  "ssid": "MyHome",
  "password": "12345678"
}
```

### 4.3 扫描附近 AP

```
GET /api/v1/wifi/scan
```

**响应**:
```json
[
  {"ssid": "MyHome", "bssid": "AA:BB:CC:DD:EE:FF", "rssi": -52, "channel": 6, "secure": true},
  {"ssid": "Neighbor", "bssid": "11:22:33:44:55:66", "rssi": -78, "channel": 11, "secure": true}
]
```

---

## 5. 平台认证

### 5.1 获取所有平台状态

```
GET /api/v1/platform/status
```

**响应**:
```json
{
  "xiaomi": {"connected": true, "authenticated": true, "deviceCount": 24},
  "tuya": {"connected": false, "authenticated": false, "deviceCount": 0},
  "midea": {"connected": true, "authenticated": true, "deviceCount": 8},
  "ewelink": {"connected": false, "authenticated": false, "deviceCount": 0},
  "ha": {"connected": false, "authenticated": false, "deviceCount": 0},
  "serial": {"connected": true, "authenticated": false, "deviceCount": 2},
  "gpio": {"connected": true, "authenticated": false, "deviceCount": 4}
}
```

### 5.2 小米平台

```
POST   /api/v1/platform/xiaomi/token      # 保存 Token
DELETE /api/v1/platform/xiaomi/token      # 清除 Token
GET    /api/v1/platform/xiaomi/oauth-url  # 获取 OAuth URL
GET    /api/v1/platform/xiaomi/login?code=xxx  # OAuth 回调
```

**POST Token 请求体**:
```json
{
  "access_token": "xxx",
  "refresh_token": "xxx",
  "uid": "123456"
}
```

### 5.3 涂鸦平台

```
POST   /api/v1/platform/tuya/token       # 保存 Token
DELETE /api/v1/platform/tuya/token       # 清除 Token
```

### 5.4 美的平台

```
POST   /api/v1/platform/midea/login      # 登录
DELETE /api/v1/platform/midea/token      # 清除 Token
GET    /api/v1/platform/midea/homes      # 获取家庭列表
POST   /api/v1/platform/midea/home       # 选择家庭
```

**登录请求体**:
```json
{
  "account": "13800138000",
  "password": "your_password",
  "cloud": "cn"
}
```

### 5.5 易微联 (eWeLink)

```
POST   /api/v1/platform/ewelink/login     # 登录
DELETE /api/v1/platform/ewelink/token     # 清除 Token
```

**登录请求体**:
```json
{
  "email": "user@example.com",
  "password": "your_password",
  "countryCode": "86"
}
```

### 5.6 HomeAssistant

```
POST   /api/v1/platform/ha/connect     # 连接 HA
DELETE /api/v1/platform/ha/token       # 清除连接
GET    /api/v1/platform/ha/status      # 连接状态
GET    /api/v1/platform/ha/services    # 可用服务列表
```

**连接请求体**:
```json
{
  "host": "192.168.1.50",
  "port": 8123,
  "access_token": "eyJhbGciOiJIUzI1NiJ9.xxx.yyy"
}
```

---

## 6. 设备管理

### 6.1 获取已导入设备列表

```
GET /api/v1/devices
```

**响应**: 设备数组，每项包含 `deviceId`, `name`, `platform`, `room`, `model`, `category` 等字段。

### 6.2 获取云端设备列表

```
GET /api/v1/devices/cloud?platform=xiaomi
```

**参数**:
| 参数 | 说明 |
|------|------|
| `platform` | 平台名称: `xiaomi`, `tuya`, `midea`, `ewelink`, `ha` |

### 6.3 刷新/导入/删除设备

```
POST /api/v1/devices/refresh   # 刷新云端设备
POST /api/v1/devices/import    # 导入设备
DELETE /api/v1/devices/:id     # 删除设备
```

**导入设备请求体**:
```json
{
  "deviceId": "xxx",
  "platform": "xiaomi"
}
```

### 6.4 规格缓存

```
POST /api/v1/devices/specs/refresh?id=xxx   # 刷新指定设备规格
POST /api/v1/devices/specs/clear             # 清除全部规格缓存
```

---

## 7. 设备控制

### 7.1 查询设备属性

```
GET /api/v1/devices/:id/properties
```

**响应**: 属性键值对 JSON 字符串。

### 7.2 获取设备规格

```
GET /api/v1/devices/:id/specs
```

返回设备的属性列表、可用 action 及参数格式（JSON Schema）。

### 7.3 控制设备（设置属性）

```
POST /api/v1/devices/:id/control
Content-Type: application/json
```

**请求体**: 平台相关，以下为小米示例:
```json
{
  "siid": 2,
  "piid": 1,
  "value": true
}
```

### 7.4 执行设备动作

```
POST /api/v1/devices/:id/action
Content-Type: application/json
```

**请求体** (小米示例):
```json
{
  "siid": 3,
  "aiid": 1,
  "params": [{"piid": 1, "value": true}]
}
```

---

## 8. 场景管理

### 8.1 获取场景列表

```
GET /api/v1/scenes?platform=xiaomi
```

**参数**: `platform` — 平台名称 (可选)

### 8.2 触发场景

```
POST /api/v1/scenes/:id/trigger?platform=xiaomi
```

---

## 9. MCP 配置

### 9.1 获取 MCP 状态

```
GET /api/v1/mcp/status
```

**响应**:
```json
{
  "running": true,
  "port": 8765,
  "clientCount": 2,
  "toolCount": 27
}
```

### 9.2 配置 MCP

```
POST /api/v1/mcp/config
```

---

## 10. 小智平台

### 10.1 获取/配置/连接/断开

```
GET    /api/v1/xiaozhi/status
POST   /api/v1/xiaozhi/config
POST   /api/v1/xiaozhi/connect
POST   /api/v1/xiaozhi/disconnect
POST   /api/v1/xiaozhi/add
POST   /api/v1/xiaozhi/remove
```

**配置请求体**:
```json
{
  "endpoint": "wss://your-endpoint",
  "enabled": true
}
```

---

## 11. MCP 代理

### 11.1 代理服务管理

```
GET    /api/v1/mcpproxy/status           # 代理状态
GET    /api/v1/mcpproxy/tools            # 所有工具列表
POST   /api/v1/mcpproxy/services         # 添加代理
DELETE /api/v1/mcpproxy/services/:id     # 删除代理
POST   /api/v1/mcpproxy/reconnect?id=xxx # 重连
POST   /api/v1/mcpproxy/config           # 保存完整配置
```

**添加代理请求体**:
```json
{
  "id": "proxy1",
  "name": "Coze MCP",
  "type": "sse",
  "url": "https://api.coze.cn/open_api/bot/run/",
  "apiKey": "pat_xxx",
  "prefix": "coze_"
}
```

---

## 12. 记忆管理

### 12.1 记忆 CRUD

```
GET    /api/v1/memory?category=xxx       # 读取记忆列表
POST   /api/v1/memory                    # 添加记忆
PUT    /api/v1/memory                    # 更新记忆
DELETE /api/v1/memory?id=N               # 删除记忆
GET    /api/v1/memory/search?keyword=xxx # 搜索记忆
GET    /api/v1/memory/daily              # 读取今日笔记
POST   /api/v1/memory/daily              # 添加今日笔记
```

**添加记忆请求体**:
```json
{
  "content": "用户偏好: 客厅灯喜欢暖色光",
  "category": "偏好"
}
```

---

## 13. 技能管理

### 13.1 技能 CRUD

```
GET    /api/v1/skills?category=xxx       # 获取技能列表
GET    /api/v1/skills/:id                # 读取技能内容
POST   /api/v1/skills/manage             # 管理技能
POST   /api/v1/skills/import             # 导入标准 SKILL.md
GET    /api/v1/skills/:id/export         # 导出技能
```

**管理技能请求体**:
```json
{
  "action": "add",
  "id": "smart_light",
  "name": "智能灯光控制",
  "description": "根据用户习惯自动调节灯光",
  "content": "# 正文内容",
  "category": "home",
  "always": false
}
```

---

## 14. 定时任务

### 14.1 任务 CRUD

```
GET    /api/v1/schedules?status=xxx      # 获取任务列表
POST   /api/v1/schedules                 # 添加任务
GET    /api/v1/schedules/:id             # 获取任务详情
POST   /api/v1/schedules/:id             # 修改任务
DELETE /api/v1/schedules/:id             # 删除任务
POST   /api/v1/schedules/:id/cancel      # 取消任务
```

**添加任务请求体**:
```json
{
  "name": "睡前关灯",
  "scheduledTime": "2026-05-16T23:00:00+08:00",
  "toolName": "xiaomi/set_property",
  "toolArgs": "{\"device_id\":\"xxx\",\"siid\":2,\"piid\":1,\"value\":false}",
  "repeat": "daily"
}
```

---

## 15. OTA 管理

```
GET  /api/v1/ota/status    # OTA 状态
POST /api/v1/ota/rollback  # 回滚到上一版本
```

---

## 16. 设备授权

```
GET    /api/v1/gateway/license   # 同 3.5
POST   /api/v1/gateway/license
DELETE /api/v1/gateway/license
```

---

## 17. GPIO 开关

### 17.1 GPIO 管理

```
GET    /api/v1/gpio/switches                # 获取 GPIO 开关列表
POST   /api/v1/gpio/switches                # 添加 GPIO 开关
GET    /api/v1/gpio/switches/:device_id     # 获取开关状态
DELETE /api/v1/gpio/switches/:device_id     # 移除开关
POST   /api/v1/gpio/switches/set            # 设置开关状态
POST   /api/v1/gpio/switches/toggle         # 切换开关状态
```

**添加 GPIO 开关请求体**:
```json
{
  "gpio_num": 2,
  "name": "网关LED",
  "active_high": true
}
```

**设置开关状态请求体**:
```json
{
  "device_id": "gpio_2",
  "state": true
}
```
