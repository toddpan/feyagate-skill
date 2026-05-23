# FeyaGate — MCP Smart Home Gateway for AI Agents

[中文](#中文) | [English](#english)

[![MCP](https://img.shields.io/badge/Protocol-MCP-blue)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/badge/PyPI-feyagate--skill-blue)](#)
[![AI Agents](https://img.shields.io/badge/AI_Agents-8-green)](#)
[![IoT Platforms](https://img.shields.io/badge/IoT-Xiaomi%20%7C%20Tuya%20%7C%20Midea%20%7C%20eWeLink-orange)](#)

> Let your AI coding assistant control smart home devices — lights, cameras, AC, speakers — directly through MCP protocol.

**Website:** [www.feyagate.com](https://www.feyagate.com)

---

<a id="english"></a>

## Features

- **Multi-platform IoT control** — Xiaomi/Mi Home, Tuya, Midea, eWeLink, Serial, GPIO
- **Camera P2P streaming** — real-time snapshots, AI vision analysis
- **Xiao AI speaker** — TTS, music playback, voice commands
- **Automation** — scheduled tasks, trigger engine, room management
- **Memory system** — persistent notes and long-term memory for AI agents
- **8 AI agents supported** — Claude Code, Cursor, OpenClaw, Hermes, Codex, Windsurf, Copilot, 小智AI

## Install — 4 Steps

```
pip install feyagate-skill  →  feyagate setup  →  feyagate start  →  feyagate install-<agent>
```

Then authorize your smart home account:

```bash
feyagate auth                 # Xiaomi OAuth (interactive)
```

> **Linux** may need system deps first: `sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7`

## Connect to Your AI Agent

One command per agent. Run this **before** authorizing platforms. Restart the agent after install.

| Agent | Command |
|:------|:--------|
| Claude Code | `feyagate install-claude` |
| Cursor | `feyagate install-cursor` |
| OpenClaw | `feyagate install-openclaw` |
| Hermes | `feyagate install-hermes` |
| Codex | `feyagate install-codex` |
| Windsurf | `feyagate install-windsurf` |
| Copilot | `feyagate install-copilot` |

## CLI Commands

| Action | Command |
|:-------|:--------|
| Install binary | `feyagate setup [--dir PATH]` |
| Start | `feyagate start [--port PORT]` |
| Stop | `feyagate stop` |
| Restart | `feyagate restart [--port PORT]` |
| Status | `feyagate status` |
| Logs | `feyagate log [-n 50]` |
| Auth Xiaomi | `feyagate auth [--status] [--code CODE]` |
| Camera snapshot | `feyagate snapshot --list` / `--camera-id DID --connect --count 3` |
| Scheduled analysis | `feyagate scheduled --camera-id DID --interval 300 --auto-connect` |
| Upgrade server | `feyagate upgrade` |
| Upgrade package | `pip install --upgrade feyagate-skill` |

## MCP Tools at a Glance

| Category | Tools |
|:---------|:------|
| **Device Discovery** | `device/list` `device/specs` `platform/status` `gateway/info` |
| **Xiaomi** | `xiaomi/get_properties` `xiaomi/set_property` `xiaomi/execute_action` |
| **Xiaomi Auth** | `xiaomi/auth_url` `xiaomi/auth_callback` `xiaomi/auth_status` |
| **Xiao AI Speaker** | `xiaoai/tts` `xiaoai/play_music` `xiaoai/control` |
| **Camera** | `xiaomi/camera_list` `xiaomi/camera_connect` `xiaomi/camera_snapshot` `xiaomi/camera_vision_chat` |
| **Tuya** | `tuya/get_properties` `tuya/set_property` `auth/tuya_qr` |
| **Midea** | `midea/get_properties` `midea/set_property` `midea/execute_action` `auth/midea_login` |
| **eWeLink** | `ewelink/get_properties` `ewelink/set_property` `ewelink/execute_action` `auth/ewelink_login` |
| **Scenes** | `scene/list` `scene/trigger` |
| **Rooms** | `room/list` `room/set_device` |
| **Schedule** | `schedule/add` `schedule/list` `schedule/get` `schedule/update` `schedule/delete` |
| **Trigger** | `trigger/create` `trigger/list` `trigger/toggle` `trigger/logs` |
| **Memory** | `memory/read` `memory/add` `memory/search` `memory/note` `memory/today` |
| **Serial / GPIO** | `serial/*` `gpio/*` |

> Full API docs: [SKILL.md](SKILL.md) | [QUICKSTART.md](QUICKSTART.md)

## How It Works

```
┌─────────────┐     MCP Protocol      ┌──────────────────┐     MIOT/DP/etc     ┌──────────┐
│  AI Agent   │ ◄──────────────────► │  feyagate server  │ ◄──────────────────► │  IoT     │
│ (Claude etc)│   localhost:38080     │  (miloco-mcp)     │                      │  Devices │
└─────────────┘                       └──────────────────┘                      └──────────┘
```

AI agents call MCP tools → FeyaGate translates to platform-specific protocols → devices respond.

## Let AI Install For You

Copy-paste this prompt to your AI assistant:

```
Please read https://github.com/toddpan/feyagate-skill/blob/main/QUICKSTART.md and follow the instructions to install and set up FeyaGate Skill on my machine.
```

## License

MIT License

---

<a id="中文"></a>

## 功能特点

- **多平台 IoT 控制** — 小米/米家、涂鸦 Tuya、美的 Midea、eWeLink、串口、GPIO
- **摄像头 P2P 实时监控** — 抓拍、AI 视觉分析
- **小爱音箱控制** — TTS 语音播报、音乐播放、语音指令
- **自动化** — 定时任务、触发引擎、房间管理
- **记忆系统** — 持久化笔记和长期记忆
- **支持 8 款 AI 助手** — Claude Code、Cursor、OpenClaw、Hermes、Codex、Windsurf、Copilot、小智AI

## 安装 — 4 步

```
pip install feyagate-skill  →  feyagate setup  →  feyagate start  →  feyagate install-<agent>
```

然后授权你的智能家居账号：

```bash
feyagate auth                 # 小米 OAuth 授权（交互式）
```

> **Linux** 可能需要先装系统依赖：`sudo apt-get install -y libfmt8 libmosquitto1 libyaml-cpp0.7`

## 接入 AI 助手

一条命令搞定，**在授权平台之前**运行。装完重启 AI 助手即可。

| AI 助手 | 命令 |
|:--------|:-----|
| Claude Code | `feyagate install-claude` |
| Cursor | `feyagate install-cursor` |
| OpenClaw | `feyagate install-openclaw` |
| Hermes | `feyagate install-hermes` |
| Codex | `feyagate install-codex` |
| Windsurf | `feyagate install-windsurf` |
| Copilot | `feyagate install-copilot` |

## 命令速查

| 操作 | 命令 |
|:-----|:-----|
| 安装二进制 | `feyagate setup [--dir PATH]` |
| 启动 | `feyagate start [--port PORT]` |
| 停止 | `feyagate stop` |
| 重启 | `feyagate restart [--port PORT]` |
| 状态 | `feyagate status` |
| 日志 | `feyagate log [-n 50]` |
| 小米授权 | `feyagate auth [--status] [--code CODE]` |
| 摄像头抓拍 | `feyagate snapshot --list` / `--camera-id DID --connect --count 3` |
| 定时分析 | `feyagate scheduled --camera-id DID --interval 300 --auto-connect` |
| 升级服务器 | `feyagate upgrade` |
| 升级包 | `pip install --upgrade feyagate-skill` |

## MCP 工具一览

| 类别 | 工具 |
|:-----|:-----|
| **设备发现** | `device/list` `device/specs` `platform/status` `gateway/info` |
| **小米控制** | `xiaomi/get_properties` `xiaomi/set_property` `xiaomi/execute_action` |
| **小米授权** | `xiaomi/auth_url` `xiaomi/auth_callback` `xiaomi/auth_status` |
| **小爱音箱** | `xiaoai/tts` `xiaoai/play_music` `xiaoai/control` |
| **摄像头** | `xiaomi/camera_list` `xiaomi/camera_connect` `xiaomi/camera_snapshot` `xiaomi/camera_vision_chat` |
| **涂鸦** | `tuya/get_properties` `tuya/set_property` `auth/tuya_qr` |
| **美的** | `midea/get_properties` `midea/set_property` `midea/execute_action` `auth/midea_login` |
| **易微联** | `ewelink/get_properties` `ewelink/set_property` `ewelink/execute_action` `auth/ewelink_login` |
| **场景** | `scene/list` `scene/trigger` |
| **房间** | `room/list` `room/set_device` |
| **定时** | `schedule/add` `schedule/list` `schedule/get` `schedule/update` `schedule/delete` |
| **触发器** | `trigger/create` `trigger/list` `trigger/toggle` `trigger/logs` |
| **记忆** | `memory/read` `memory/add` `memory/search` `memory/note` `memory/today` |
| **串口 / GPIO** | `serial/*` `gpio/*` |

> 完整文档：[SKILL.md](SKILL.md) | [QUICKSTART.md](QUICKSTART.md)

## 工作原理

```
┌─────────────┐     MCP 协议       ┌──────────────────┐    MIOT/DP 等     ┌──────────┐
│  AI 助手    │ ◄───────────────► │  feyagate 服务器  │ ◄───────────────► │  IoT     │
│ (Claude 等) │  localhost:38080  │  (miloco-mcp)     │                   │  设备    │
└─────────────┘                    └──────────────────┘                   └──────────┘
```

AI 助手调用 MCP 工具 → FeyaGate 翻译为各平台协议 → 设备响应。

## 让 AI 帮你安装

复制以下提示词发给你的 AI 助手：

```
请阅读 https://github.com/toddpan/feyagate-skill/blob/main/QUICKSTART.md 并按照指南在我的机器上安装和配置 FeyaGate Skill。
```

## 许可证

MIT License
