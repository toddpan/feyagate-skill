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

## Quick Start

**What you need:** A Mac, Linux, or Windows PC · Python 3.9+ · Terminal (Mac/Linux) or PowerShell (Windows)

### Option 1 — Let your AI install it (easiest)

Copy this into Claude, Cursor, or any AI assistant:

```
Please read https://github.com/toddpan/feyagate-skill/blob/main/QUICKSTART.md and follow the instructions to install and set up FeyaGate Skill on my machine.
```

### Option 2 — One command (recommended)

Copy the **entire line** below, paste into Terminal, press Enter, and wait a few minutes. The script installs everything and starts the service automatically.

**Mac / Linux** — open **Terminal** (Spotlight: type `Terminal`):

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows** — open **PowerShell**, paste and run:

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

> No Python yet? Install from [python.org](https://www.python.org/downloads/) and check **Add Python to PATH** on Windows.

### After install — 3 steps

| Step | What to do | Command |
|:-----|:-----------|:--------|
| **1** | Connect your AI assistant | See table below, e.g. `feyagate install-cursor` |
| **2** | Sign in to Mi Home (Xiaomi) | `feyagate auth` |
| **3** | Confirm it's running | `feyagate status` |

Then **restart your AI assistant** and try: *"List my smart home devices."*

- **Web dashboard:** [http://localhost:38080](http://localhost:38080)
- **Stuck?** See [QUICKSTART.md](QUICKSTART.md) troubleshooting

| Your AI assistant | Run this command |
|:------------------|:-----------------|
| Cursor | `feyagate install-cursor` |
| Claude Code | `feyagate install-claude` |
| OpenClaw | `feyagate install-openclaw` |
| Codex | `feyagate install-codex` |
| Windsurf | `feyagate install-windsurf` |
| Copilot (VS Code) | `feyagate install-copilot` |
| Hermes | `feyagate install-hermes` |

### Option 3 — Manual install

For users who prefer running commands step by step:

```bash
pip install feyagate-skill    # 1. Install the feyagate tool
feyagate setup              # 2. Download the gateway program (~30MB)
feyagate start              # 3. Start the service
feyagate install-cursor     # 4. Connect your AI assistant (pick one)
feyagate auth               # 5. Sign in to Mi Home
```

## CLI Commands

| Action | Command |
|:-------|:--------|
| Install gateway | `feyagate setup` |
| Start / stop | `feyagate start` · `feyagate stop` |
| Status / logs | `feyagate status` · `feyagate log` |
| Mi Home login | `feyagate auth` |
| Upgrade | `feyagate upgrade` or `pip install --upgrade feyagate-skill` |

## MCP Tools at a Glance

| Category | Tools |
|:---------|:------|
| **Device Discovery** | `device/list` `device/specs` `platform/status` `gateway/info` |
| **Xiaomi** | `xiaomi/get_properties` `xiaomi/set_property` `xiaomi/execute_action` |
| **Xiao AI Speaker** | `xiaoai/tts` `xiaoai/play_music` `xiaoai/control` |
| **Camera** | `xiaomi/camera_list` `xiaomi/camera_connect` `xiaomi/camera_snapshot` |
| **Tuya / Midea / eWeLink** | Platform tools + `auth/*` login helpers |
| **Scenes / Rooms / Schedule** | `scene/*` `room/*` `schedule/*` `trigger/*` |
| **Memory** | `memory/read` `memory/add` `memory/search` |

> Full API: [SKILL.md](SKILL.md) · [QUICKSTART.md](QUICKSTART.md)

## How It Works

```
┌─────────────┐     MCP Protocol      ┌──────────────────┐     MIOT/DP/etc     ┌──────────┐
│  AI Agent   │ ◄──────────────────► │  feyagate server  │ ◄──────────────────► │  IoT     │
│ (Claude etc)│   localhost:38080     │  (miloco-mcp)     │                      │  Devices │
└─────────────┘                       └──────────────────┘                      └──────────┘
```

## License

MIT License

---

<a id="中文"></a>

## 功能特点

- **多平台智能家居** — 小米/米家、涂鸦、美的、易微联、串口、GPIO
- **摄像头** — 实时抓拍、AI 视觉分析
- **小爱音箱** — 语音播报、放音乐、语音控制
- **自动化** — 定时任务、触发器、房间管理
- **记忆** — AI 可记住你的习惯和笔记
- **支持 8 款 AI 助手** — Cursor、Claude Code、OpenClaw、Codex、Windsurf、Copilot、Hermes、小智AI

## 快速开始

**准备：** 一台 Mac / Linux / Windows 电脑 · 已安装 [Python 3.9+](https://www.python.org/downloads/) · 能打开「终端」或 PowerShell

### 方式一：让 AI 帮你装（最省心）

把下面这段话复制发给 Cursor、Claude 等 AI 助手，它会按步骤帮你装好：

```
请阅读 https://github.com/toddpan/feyagate-skill/blob/main/QUICKSTART.md 并按照指南在我的机器上安装和配置 FeyaGate Skill。
```

### 方式二：一条命令自动安装（推荐）

**复制下面整行**，粘贴到终端里按回车，等几分钟即可。脚本会自动：安装工具 → 下载网关程序 → 启动服务。

**Mac / Linux** — 打开「**终端**」（Mac 可按 `Command + 空格`，搜索「终端」）：

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows** — 打开「**PowerShell**」（开始菜单搜索 PowerShell）：

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

> 还没有 Python？到 [python.org](https://www.python.org/downloads/) 下载安装；Windows 安装时务必勾选 **Add Python to PATH**。

### 装好之后，再做 3 件事

| 步骤 | 要做什么 | 命令 |
|:-----|:---------|:-----|
| **1** | 让 AI 助手认识 FeyaGate | 见下表，例如 `feyagate install-cursor` |
| **2** | 登录小米/米家账号 | `feyagate auth` |
| **3** | 确认服务已启动 | `feyagate status` |

完成后 **重启你的 AI 助手**，试着说：「列出我家的智能设备」。

- **网页管理：** 浏览器打开 [http://localhost:38080](http://localhost:38080)
- **遇到问题？** 查看 [QUICKSTART.md](QUICKSTART.md) 故障排除

| 你用的 AI 助手 | 运行这条命令 |
|:---------------|:-------------|
| Cursor | `feyagate install-cursor` |
| Claude Code | `feyagate install-claude` |
| OpenClaw | `feyagate install-openclaw` |
| Codex | `feyagate install-codex` |
| Windsurf | `feyagate install-windsurf` |
| Copilot（VS Code） | `feyagate install-copilot` |
| Hermes | `feyagate install-hermes` |

### 方式三：手动安装（熟悉命令行可选）

```bash
pip install feyagate-skill    # 1. 安装 feyagate 命令行工具
feyagate setup              # 2. 下载网关程序（约 30MB，需联网）
feyagate start              # 3. 启动服务
feyagate install-cursor     # 4. 接入 AI 助手（按上表选一个）
feyagate auth               # 5. 登录小米账号
```

## 常用命令

| 想做什么 | 命令 |
|:---------|:-----|
| 下载/更新网关程序 | `feyagate setup` |
| 启动 / 停止 | `feyagate start` · `feyagate stop` |
| 查看状态 / 日志 | `feyagate status` · `feyagate log` |
| 登录米家 | `feyagate auth` |
| 升级 | `feyagate upgrade` 或 `pip install --upgrade feyagate-skill` |

## MCP 工具一览

| 类别 | 工具 |
|:-----|:-----|
| **查设备** | `device/list` `device/specs` |
| **小米控制** | `xiaomi/get_properties` `xiaomi/set_property` |
| **小爱音箱** | `xiaoai/tts` `xiaoai/play_music` |
| **摄像头** | `xiaomi/camera_snapshot` 等 |
| **涂鸦 / 美的 / 易微联** | 各平台控制 + `auth/*` 登录 |
| **场景 / 房间 / 定时** | `scene/*` `room/*` `schedule/*` |


## 工作原理

```
┌─────────────┐     MCP 协议       ┌──────────────────┐    各平台协议     ┌──────────┐
│  AI 助手    │ ◄───────────────► │  FeyaGate 网关   │ ◄───────────────► │ 智能设备 │
│ (Cursor 等) │  本机 38080 端口   │                  │                   │ 灯/空调等 │
└─────────────┘                    └──────────────────┘                   └──────────┘
```

你对 AI 说「开灯」→ AI 调用 FeyaGate → 设备执行。

## 许可证

MIT License
