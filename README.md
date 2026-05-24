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

**Prerequisites:** Mac / Linux / Windows · Python 3.9+ · Terminal or PowerShell

### Option 1 — One command (recommended)

Copy the **entire line** below, paste into Terminal, press Enter, and wait a few minutes:

**Mac / Linux** — open **Terminal** (Spotlight: type `Terminal`):

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows** — open **PowerShell**, paste and run:

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

> No Python yet? Install from [python.org](https://www.python.org/downloads/) and check **Add Python to PATH** on Windows.

> **Let AI do it for you?** Send this to Claude, Cursor, or any AI assistant:
> `Please read https://github.com/toddpan/feyagate-skill/blob/main/QUICKSTART.md and follow the instructions to install and set up FeyaGate Skill on my machine.`

### Option 2 — Install from PyPI (step by step)

```bash
pip install feyagate-skill    # 1. Install the CLI tool
feyagate setup              # 2. Download the gateway binary (~30MB)
feyagate start              # 3. Start the service
feyagate install-cursor     # 4. Connect your AI assistant (pick one)
feyagate auth               # 5. Sign in to Mi Home
```

### Option 3 — Install from source (developers)

```bash
git clone https://github.com/toddpan/feyagate-skill.git
cd feyagate-skill
pip install -e ".[dev]"     # Editable install with dev dependencies (pytest, etc.)
feyagate setup
feyagate start
feyagate install-cursor     # or install-claude, install-hermes, etc.
feyagate auth
```

### After install — connect your AI assistant

| Your AI assistant | Run this command |
|:------------------|:-----------------|
| Cursor | `feyagate install-cursor` |
| Claude Code | `feyagate install-claude` |
| OpenClaw | `feyagate install-openclaw` |
| Codex | `feyagate install-codex` |
| Windsurf | `feyagate install-windsurf` |
| Copilot (VS Code) | `feyagate install-copilot` |
| Hermes | `feyagate install-hermes` |

Then **restart your AI assistant** and try: *"List my smart home devices."*

- **Web dashboard:** [http://localhost:38080](http://localhost:38080)
- **Stuck?** See [QUICKSTART.md](QUICKSTART.md) troubleshooting

## CLI Commands

| Action | Command |
|:-------|:--------|
| Install gateway | `feyagate setup` |
| Start / stop | `feyagate start` · `feyagate stop` |
| Restart | `feyagate restart` |
| Status / logs | `feyagate status` · `feyagate log [-n 50]` |
| Mi Home login | `feyagate auth` |
| Camera snapshot | `feyagate snapshot --list` · `feyagate snapshot --camera-id ID --connect` |
| Scheduled capture | `feyagate scheduled --camera-id ID --interval 300` |
| Version | `feyagate --version` |
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

> Full API reference: [SKILL.md](SKILL.md) · [FeyaGate_MCP_API.md](FeyaGate_MCP_API.md) · [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md)

## How It Works

```
┌─────────────┐     MCP Protocol      ┌──────────────────┐     MIOT/DP/etc     ┌──────────┐
│  AI Agent   │ ◄──────────────────► │  feyagate server  │ ◄──────────────────► │  IoT     │
│ (Claude etc)│   localhost:38080     │  (miloco-mcp)     │                      │  Devices │
└─────────────┘                       └──────────────────┘                      └──────────┘
```

## Development

```bash
git clone https://github.com/toddpan/feyagate-skill.git
cd feyagate-skill
pip install -e ".[dev]"
pytest                        # run all tests
pytest tests/test_cli.py      # run single file
pytest tests/test_cli.py::TestClass::test_method  # run single test
bash scripts/build.sh         # build PyPI package (outputs to dist/)
bash scripts/publish.sh pypi  # publish to PyPI (requires PYPI_TOKEN env var)
```

Tests use `pytest` with `unittest.mock`. Each module has a corresponding test file in `tests/` (e.g. `test_cli.py`, `test_service.py`, `test_installer.py`).

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

### 方式一：一条命令自动安装（推荐）

**复制下面整行**，粘贴到终端里按回车，等几分钟即可：

**Mac / Linux** — 打开「**终端**」（Mac 可按 `Command + 空格`，搜索「终端」）：

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows** — 打开 **PowerShell**，粘贴并运行：

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

> 还没有 Python？到 [python.org](https://www.python.org/downloads/) 下载安装；Windows 安装时务必勾选 **Add Python to PATH**。

> **想让 AI 帮你装？** 把下面这段话发给 Cursor、Claude 等 AI 助手：
> `请阅读 https://github.com/toddpan/feyagate-skill/blob/main/QUICKSTART.md 并按照指南在我的机器上安装和配置 FeyaGate Skill。`

### 方式二：从 PyPI 安装（逐步执行）

```bash
pip install feyagate-skill    # 1. 安装命令行工具
feyagate setup              # 2. 下载网关程序（约 30MB，需联网）
feyagate start              # 3. 启动服务
feyagate install-cursor     # 4. 接入 AI 助手（按下表选一个）
feyagate auth               # 5. 登录小米账号
```

### 方式三：从源码安装（开发者）

```bash
git clone https://github.com/toddpan/feyagate-skill.git
cd feyagate-skill
pip install -e ".[dev]"     # 可编辑安装，含开发依赖（pytest 等），代码修改即时生效
feyagate setup
feyagate start
feyagate install-cursor     # 或 install-claude、install-hermes 等
feyagate auth
```

### 装好之后 — 让 AI 助手认识 FeyaGate

| 你用的 AI 助手 | 运行这条命令 |
|:---------------|:-------------|
| Cursor | `feyagate install-cursor` |
| Claude Code | `feyagate install-claude` |
| OpenClaw | `feyagate install-openclaw` |
| Codex | `feyagate install-codex` |
| Windsurf | `feyagate install-windsurf` |
| Copilot（VS Code） | `feyagate install-copilot` |
| Hermes | `feyagate install-hermes` |

完成后 **重启你的 AI 助手**，试着说：「列出我家的智能设备」。

- **网页管理：** 浏览器打开 [http://localhost:38080](http://localhost:38080)
- **遇到问题？** 查看 [QUICKSTART.md](QUICKSTART.md) 故障排除

## 常用命令

| 想做什么 | 命令 |
|:---------|:-----|
| 下载/更新网关程序 | `feyagate setup` |
| 启动 / 停止 | `feyagate start` · `feyagate stop` |
| 重启 | `feyagate restart` |
| 查看状态 / 日志 | `feyagate status` · `feyagate log [-n 50]` |
| 登录米家 | `feyagate auth` |
| 摄像头抓拍 | `feyagate snapshot --list` · `feyagate snapshot --camera-id ID --connect` |
| 定时抓拍分析 | `feyagate scheduled --camera-id ID --interval 300` |
| 查看版本 | `feyagate --version` |
| 升级 | `feyagate upgrade` 或 `pip install --upgrade feyagate-skill` |

## MCP 工具一览

| 类别 | 工具 |
|:-----|:-----|
| **查设备** | `device/list` `device/specs` `platform/status` `gateway/info` |
| **小米控制** | `xiaomi/get_properties` `xiaomi/set_property` `xiaomi/execute_action` |
| **小爱音箱** | `xiaoai/tts` `xiaoai/play_music` `xiaoai/control` |
| **摄像头** | `xiaomi/camera_list` `xiaomi/camera_connect` `xiaomi/camera_snapshot` |
| **涂鸦 / 美的 / 易微联** | 各平台控制 + `auth/*` 登录 |
| **场景 / 房间 / 定时** | `scene/*` `room/*` `schedule/*` `trigger/*` |
| **记忆** | `memory/read` `memory/add` `memory/search` |

> 完整 API 文档：[SKILL.md](SKILL.md) · [FeyaGate_MCP_API.md](FeyaGate_MCP_API.md) · [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md)


## 工作原理

```
┌─────────────┐     MCP 协议       ┌──────────────────┐    各平台协议     ┌──────────┐
│  AI 助手    │ ◄───────────────► │  FeyaGate 网关   │ ◄───────────────► │ 智能设备 │
│ (Cursor 等) │  本机 38080 端口   │                  │                   │ 灯/空调等 │
└─────────────┘                    └──────────────────┘                   └──────────┘
```

你对 AI 说「开灯」→ AI 调用 FeyaGate → 设备执行。

## 开发

```bash
git clone https://github.com/toddpan/feyagate-skill.git
cd feyagate-skill
pip install -e ".[dev]"
pytest                        # 运行所有测试
pytest tests/test_cli.py      # 运行单个文件
pytest tests/test_cli.py::TestClass::test_method  # 运行单个测试
bash scripts/build.sh         # 打包（输出到 dist/）
bash scripts/publish.sh pypi  # 发布到 PyPI（需设置 PYPI_TOKEN 环境变量）
```

测试使用 `pytest` + `unittest.mock`。`tests/` 下每个模块对应一个测试文件（如 `test_cli.py`、`test_service.py`、`test_installer.py`）。

## 许可证

MIT License
