# 用 OpenClaw + FeyaGate 让 AI 助手直接控制你的米家、涂鸦智能家居

> 写代码写到一半，突然想开个灯？对 AI 说一句「把客厅灯打开」就行了。

---

## 什么是 FeyaGate？

[FeyaGate](https://www.feyagate.com) 是一个基于 MCP（Model Context Protocol）协议的智能家居网关。它做了一件很简单但很酷的事情：**让你的 AI 编程助手（OpenClaw、Claude Code、Cursor 等）能直接控制你家里的智能设备**。

支持的平台：

| 平台 | 设备类型 |
|------|---------|
| **小米/米家** | 灯、空调、扫地机、摄像头、小爱音箱… |
| **涂鸦（Tuya）** | 开关、插座、传感器、灯具… |
| **美的（Midea）** | 空调、全屋家电… |
| **易微联（eWeLink）** | Sonoff 开关、继电器… |
| **串口/GPIO** | RS485、UART、树莓派 GPIO… |

架构非常清晰：

```
┌─────────────┐     MCP 协议       ┌──────────────────┐    各平台协议     ┌──────────┐
│  OpenClaw   │ ◄───────────────► │  FeyaGate 网关   │ ◄───────────────► │ 智能设备 │
│  (AI 助手)  │  本机 38080 端口   │  (Go 二进制)     │                   │ 灯/空调等 │
└─────────────┘                    └──────────────────┘                   └──────────┘
```

你对 AI 说「开灯」→ AI 调用 FeyaGate MCP 工具 → 设备执行。整个过程不需要你写任何代码。

---

## 为什么选择 OpenClaw？

OpenClaw 是一款支持 MCP 协议的 AI 编程助手。它能读取项目里的 Skill 文件，自动发现并调用 FeyaGate 提供的 76 个智能家居工具。

和其他 AI 助手（Claude Code、Cursor 等）相比，OpenClaw 的优势在于它是开源的，社区活跃，且对 MCP 工具的调用非常自然——你只需要用自然语言描述你想要什么，它就会自动选择合适的工具。

---

## 安装教程（5 分钟搞定）

### 前置条件

- Mac / Linux / Windows 任意系统
- Python 3.9+（[下载地址](https://www.python.org/downloads/)）
- 已安装 OpenClaw

### 第一步：一条命令安装 FeyaGate

打开终端，复制粘贴下面这整行命令：

**Mac / Linux：**

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows（PowerShell）：**

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

这条命令会自动完成三件事：
1. 安装 `feyagate` 命令行工具（从 PyPI 下载）
2. 下载智能家居网关程序（约 30MB）
3. 启动后台服务（监听 `localhost:38080`）

安装完成后你会看到类似这样的输出：

```
  ✓ 安装完成！
```

### 第二步：把 FeyaGate 接入 OpenClaw

运行这条命令：

```bash
feyagate install-openclaw
```

这条命令会在 `~/.openclaw/skills/feyagate` 创建一个符号链接，指向 FeyaGate 的 Skill 文件。OpenClaw 启动后会自动读取这些 Skill，知道怎么调用智能家居工具。

> **重要：** 运行完这条命令后，需要**重启 OpenClaw**，Skill 才会生效。

### 第三步：登录你的智能设备平台

#### 小米/米家（最常用）

```bash
feyagate auth
```

运行后会弹出一个小米 OAuth 授权页面，在浏览器中登录你的小米账号，授权完成后把回调 URL 粘贴回终端即可。

#### 涂鸦（Tuya）

需要先在涂鸦智能 App 中找到你的 User Code：**我的 → 设置 → 账号与安全 → 用户码**，然后运行：

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"auth/tuya_qr",
      "arguments":{"user_code":"你的用户码"}
    }
  }' | python3 -m json.tool
```

返回的 `qr_url` 用涂鸦智能 App 扫码即可完成授权。

#### 美的（Midea）

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"auth/midea_login",
      "arguments":{"account":"手机号或邮箱", "password":"密码"}
    }
  }' | python3 -m json.tool
```

#### 易微联（eWeLink）

```bash
curl -s -X POST http://localhost:38080/mcp/http \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"auth/ewelink_login",
      "arguments":{"email":"邮箱", "password":"密码", "country_code":"+86"}
    }
  }' | python3 -m json.tool
```

### 第四步：验证一切正常

```bash
feyagate status
```

看到 `RUNNING` 就说明网关已经在运行了。

也可以打开浏览器访问 **http://localhost:38080** 查看 Web 管理面板。

---

## 实际使用：让 AI 帮你操控智能家居

装好之后，打开 OpenClaw，直接用自然语言对话就行。

### 场景 1：列出家中所有设备

你对 OpenClaw 说：

> 「帮我列出家里所有的智能设备」

OpenClaw 会调用 `device/list` 工具，返回所有设备的名称、型号、平台、在线状态：

```
找到 23 个设备：
- 客厅灯（小米，yeelink.light.lamp1）在线
- 主卧空调（小米，chuangmi.aircondition.v1）在线
- 浴室插座（涂鸦，智能插座）在线
- 书房台灯（易微联，Sonoff B05）在线
...
```

### 场景 2：开灯/关灯

> 「把客厅灯打开」

OpenClaw 会先调用 `device/specs` 查询设备规格，找到对应的 `siid` 和 `piid`，然后调用 `xiaomi/set_property` 执行操作：

```
已将「客厅灯」打开 ✓
```

### 场景 3：调节空调温度

> 「把主卧空调调到 26 度，制冷模式」

OpenClaw 自动执行：
1. 查询设备规格 → 找到温度属性（siid=2, piid=5）和模式属性（siid=2, piid=3）
2. 设置温度为 26
3. 设置模式为制冷

```
已将「主卧空调」温度设为 26°C，模式设为制冷 ✓
```

### 场景 4：跨平台控制

> 「把所有灯都关了」

FeyaGate 会自动识别每个灯属于哪个平台，调用对应的工具：

```
已关闭 5 盏灯：
- 小米：客厅灯 ✓
- 小米：卧室灯 ✓
- 涂鸦：厨房灯 ✓
- 易微联：书房台灯 ✓
- 小米：阳台灯 ✓
```

### 场景 5：摄像头抓拍 + AI 分析

> 「帮我看看客厅摄像头现在拍到了什么」

OpenClaw 会依次调用：
1. `xiaomi/camera_connect` — 建立 P2P 连接
2. `xiaomi/camera_snapshot` — 抓拍一张图片
3. 将图片交给视觉模型分析

```
客厅摄像头当前画面：
- 画面中有 1 人坐在沙发上
- 客厅灯已打开
- 电视正在播放
- 室温约 25°C
```

### 场景 6：让小爱音箱说话

> 「让小爱音箱说：欢迎回家」

```
已通过小爱音箱播报：「欢迎回家」 ✓
```

还可以播放音乐：「让小爱放一首周杰伦的歌」，或者语音控制：「让小爱把客厅灯打开」。

### 场景 7：设置定时任务

> 「每天晚上 10 点帮我关掉客厅灯」

OpenClaw 会调用 `schedule/add` 创建一个定时任务：

```
已创建定时任务：每天 22:00 关闭客厅灯 ✓
```

---

## 进阶玩法

### 查看设备详细规格

不确定某个设备支持哪些操作？让 AI 帮你查：

> 「空调支持哪些功能？」

OpenClaw 调用 `device/specs` 返回完整的 MIOT 规格，包括所有属性（温度、模式、风速等）和动作（开机、关机等）。

### 触发场景

> 「帮我执行离家模式」

```
已触发「离家模式」场景 ✓
（关闭所有灯、关闭空调、打开扫地机）
```

### 摄像头持续监控

通过 CLI 命令可以设置定时抓拍分析：

```bash
feyagate scheduled --camera-id CAMERA_DID --interval 300
```

每 5 分钟自动抓拍一次，配合视觉 AI 进行分析。

### Web 管理面板

浏览器打开 **http://localhost:38080**，可以：
- 查看所有设备列表和在线状态
- 查看各平台授权状态
- 查看网关版本信息
- 管理配置

---

## 常见问题

**Q：安装时报错 `command not found: feyagate`**

确保 Python 3.9+ 已安装，并且 `pip` 在 PATH 中。运行 `python3 --version` 检查。

**Q：`feyagate status` 显示 STOPPED**

运行 `feyagate start` 启动服务。

**Q：AI 助手说找不到工具**

1. 确认已运行 `feyagate install-openclaw`
2. 重启 OpenClaw
3. 检查 `~/.openclaw/skills/feyagate` 符号链接是否存在

**Q：小米设备控制失败**

运行 `feyagate auth` 重新授权。Token 过期后需要重新登录。

**Q：涂鸦设备提示 `license_required`**

FeyaGate 免费版支持小米平台全功能。涂鸦、美的、易微联需要授权版。详情查看 [feyagate.com](https://www.feyagate.com)。

**Q：怎么升级到最新版？**

```bash
pip install --upgrade feyagate-skill
feyagate update
```

---

## 完整工具列表（76 个）

FeyaGate 提供了 76 个 MCP 工具，覆盖以下类别：

| 类别 | 工具示例 |
|------|---------|
| 设备发现 | `device/list`、`device/specs`、`platform/status` |
| 小米控制 | `xiaomi/get_properties`、`xiaomi/set_property`、`xiaomi/execute_action` |
| 涂鸦控制 | `tuya/get_property`、`tuya/set_property` |
| 美的控制 | `midea/get_property`、`midea/set_property` |
| 易微联控制 | `ewelink/get_property`、`ewelink/set_property` |
| 小爱音箱 | `xiaoai/tts`、`xiaoai/play_music`、`xiaoai/control` |
| 摄像头 | `xiaomi/camera_list`、`xiaomi/camera_connect`、`xiaomi/camera_snapshot`、`xiaomi/camera_vision_chat` |
| 场景 | `xiaomi/scene_list`、`xiaomi/scene_trigger` |
| 定时 | `schedule/add`、`schedule/list`、`schedule/delete` |
| 触发器 | `trigger/add`、`trigger/list`（摄像头+自然语言条件） |
| 认证 | `auth/platforms`、`auth/tuya_qr`、`auth/midea_login` |
| 配置 | `config/get`、`config/set`、`config/set_vision` |

完整 API 文档见：[FeyaGate_MCP_API.md](https://github.com/toddpan/feyagate-skill/blob/main/FeyaGate_MCP_API.md)

---

## 总结

整个流程非常简单：

1. **一条命令**安装 FeyaGate（`curl ... | bash`）
2. **一条命令**接入 OpenClaw（`feyagate install-openclaw`）
3. **登录**你的智能设备平台（`feyagate auth`）
4. **用自然语言**和 AI 对话，控制家里的设备

从此以后，写代码写累了，对 AI 说一句「帮我把灯关了」就行。

---

**项目地址：** [https://github.com/toddpan/feyagate-skill](https://github.com/toddpan/feyagate-skill)

**官网：** [https://www.feyagate.com](https://www.feyagate.com)

**协议：** MIT License
