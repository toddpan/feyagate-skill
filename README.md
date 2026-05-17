# FeyaGate Skill

基于 [miloco-mcp-server](https://gitee.com/panjyang/miloco-mcp-server) 的 MCP Skill 封装，提供小米/米家智能设备控制、摄像头监控、小爱音箱控制等能力。

**官网：** [www.feyagate.com](https://www.feyagate.com)

## 项目结构

```
feyagate-skill/
├── SKILL.md                    # AI Agent Skill 定义（MCP 工具描述）
├── README.md                   # 项目说明（本文件）
├── QUICKSTART.md               # 快速开始指南
├── reference.md                # 完整 MCP API 参考
│
├── config/                     # 配置模板（入版本控制）
│   ├── config.yaml.example     # 配置示例
│   └── camera_extra_info.yaml  # 摄像头附加信息
│
├── scripts/                    # 管理脚本（入版本控制）
│   ├── install.sh / install.ps1  # 一键在线安装（官方发布）
│   ├── upgrade.sh / upgrade.ps1  # 在线升级（版本对比、备份回滚）
│   ├── setup.sh / setup.bat    # 自动检测平台 + 解压发布包
│   ├── verify.sh / verify.bat  # 验证安装完整性
│   ├── start.sh / start.bat    # 启动服务
│   ├── stop.sh / stop.bat      # 停止服务
│   ├── health_check.sh / .bat  # 健康检查
│   ├── auth.py                 # 米家 OAuth 授权（跨平台）
│   ├── snapshot.py             # 摄像头抓拍工具
│   └── scheduled_analysis.py   # 定时 AI 分析
│
├── packages/                   # 放入下载的发布包（gitignored）
├── bin/                        # 二进制文件（setup 自动填充，gitignored）
├── lib/                        # 动态库（setup 自动填充，gitignored）
├── data/                       # 运行时数据（gitignored）
└── webui/                      # Web UI（setup 自动解压，gitignored）
```

## 平台支持

| 平台 | 发布包格式 | 二进制 | 动态库 |
|------|-----------|--------|--------|
| macOS Intel | `miloco-mcp-server-*-Darwin-x86_64.tar.gz` | `bin/miloco-mcp-server` | `lib/*.dylib` |
| macOS ARM | `miloco-mcp-server-*-Darwin-arm64.tar.gz` | `bin/miloco-mcp-server` | `lib/*.dylib` |
| Linux x86_64 | `miloco-mcp-server-*-Linux-x86_64.tar.gz` | `bin/miloco-mcp-server` | `lib/*.so` |
| Windows x64 | `miloco-mcp-server-*-Windows-x86_64.zip` | `bin/miloco-mcp-server.exe` | `lib/*.dll` |

## 安装

### 方式一：一键在线安装（推荐）

自动从服务器获取最新版本，下载、解压、配置一步到位：

**macOS / Linux:**

```bash
curl -fsSL https://gitee.com/panzuji/feyagate-skill/raw/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
iwr -useb https://gitee.com/panzuji/feyagate-skill/raw/main/scripts/install.ps1 | iex
```

自定义安装目录：

```bash
# macOS / Linux
curl -fsSL https://gitee.com/panzuji/feyagate-skill/raw/main/scripts/install.sh | bash -s -- --dir ~/my-skill

# Windows
$env:FEYAGATE_INSTALL_DIR="D:\my-skill"; iwr -useb https://gitee.com/panzuji/feyagate-skill/raw/main/scripts/install.ps1 | iex
```

安装脚本会自动：
1. 从 [fota.json](https://oneapi.sooncore.com/ota/fota.json) 获取最新版本信息
2. 克隆 feyagate-skill 仓库（含脚本和配置模板）
3. 下载对应平台的二进制发布包并校验 MD5
4. 解压二进制文件到 `bin/`，动态库到 `lib/`，WebUI 到 `webui/`
5. 创建默认 `config/config.yaml` 和 `data/` 目录

### 方式二：手动安装

#### Step 1: 克隆仓库

```bash
git clone https://gitee.com/panzuji/feyagate-skill.git
cd feyagate-skill
```

#### Step 2: 下载发布包

**从官网下载：** 访问 [www.feyagate.com](https://www.feyagate.com) 下载对应平台的 Skill 包，放入 `packages/` 目录。

**直接下载链接：**

```bash
# macOS Intel
curl -L -o packages/miloco-mcp-server-VERSION-Darwin-x86_64.tar.gz \
  "https://oneapi.sooncore.com/ota/feyagate-skill/miloco-mcp-server-VERSION-Darwin-x86_64.tar.gz"

# Linux x86_64
curl -L -o packages/miloco-mcp-server-VERSION-Linux-x86_64.tar.gz \
  "https://oneapi.sooncore.com/ota/feyagate-skill/miloco-mcp-server-VERSION-Linux-x86_64.tar.gz"

# Windows x64
curl -L -o packages/miloco-mcp-server-VERSION-Windows-x86_64.zip \
  "https://oneapi.sooncore.com/ota/feyagate-skill/miloco-mcp-server-VERSION-Windows-x86_64.zip"
```

> 提示：最新版本信息可通过 https://oneapi.sooncore.com/ota/fota.json 获取（搜索 `feyagate-skill-*` 类型的条目）。

#### Step 3: 运行 Setup

```bash
# macOS / Linux
bash scripts/setup.sh

# Windows
scripts\setup.bat

# 或指定包路径
bash scripts/setup.sh --package /path/to/miloco-mcp-server-*.tar.gz
```

#### Step 4: 配置

编辑 `config/config.yaml`，设置云端区域等参数：

```yaml
server:
  http_port: 38080
  bind_address: "0.0.0.0"
auth:
  cloud_server: "cn"      # cn / de / sg / us / ru / i2
```

### 启动并授权

```bash
bash scripts/start.sh                # 启动 MCP Server
python3 scripts/auth.py              # 首次授权米家账号
bash scripts/health_check.sh         # 验证状态
```

## 服务管理

| 操作 | macOS / Linux | Windows |
|------|---------------|---------|
| 安装/解压 | `bash scripts/setup.sh` | `scripts\setup.bat` |
| 验证安装 | `bash scripts/verify.sh` | `scripts\verify.bat` |
| 启动 | `bash scripts/start.sh` | `scripts\start.bat` |
| 停止 | `bash scripts/stop.sh` | `scripts\stop.bat` |
| 健康检查 | `bash scripts/health_check.sh` | `scripts\health_check.bat` |
| 自定义端口 | `bash scripts/start.sh --port 9090` | `scripts\start.bat --port 9090` |
| 在线升级 | `bash scripts/upgrade.sh` | `powershell -File scripts\upgrade.ps1` |
| 检查更新 | `bash scripts/upgrade.sh --check` | `powershell -File scripts\upgrade.ps1 -Check` |

## MCP 工具概览

| 类别 | 工具 | 说明 |
|------|------|------|
| **设备发现** | device/list, device/specs, platform/status, gateway/info | 跨平台设备管理与状态查询 |
| **小米控制** | xiaomi/get_properties, xiaomi/set_property, xiaomi/execute_action | MIOT 协议设备读写与动作 |
| **小米授权** | xiaomi/auth_status, xiaomi/auth_url, xiaomi/auth_callback | OAuth 授权管理 |
| **场景** | scene/list, scene/trigger | 跨平台场景管理 |
| **小爱音箱** | xiaoai/tts, xiaoai/play_music, xiaoai/control | TTS、音乐、语音控制 |
| **摄像头** | xiaomi/camera_list, xiaomi/camera_connect, xiaomi/camera_snapshot 等 | P2P 连接、JPEG 抓拍 |
| **涂鸦** | tuya/get_properties, tuya/set_property | 涂鸦设备控制 |
| **美的** | midea/get_properties, midea/set_property, midea/execute_action | 美的设备控制 |
| **易微联** | ewelink/get_properties, ewelink/set_property, ewelink/execute_action | eWeLink 设备控制 |
| **房间** | room/list, room/set_device | 房间管理 |
| **记忆** | memory/read, memory/add, memory/search, memory/note 等 | 长期记忆与每日笔记 |
| **定时任务** | schedule/add, schedule/list, schedule/get 等 | 定时调度 |
| **串口/GPIO** | serial/*, gpio/* | 扩展设备控制 |

详细 API 文档见 [SKILL.md](SKILL.md)、[FeyaGate_MCP_API.md](FeyaGate_MCP_API.md) 和 [FeyaGate_HTTP_API.md](FeyaGate_HTTP_API.md)。

## 升级

### 在线升级（推荐）

自动从服务器获取最新版本，支持版本对比、备份回滚和服务生命周期管理：

**检查是否有新版本：**

```bash
# macOS / Linux
bash scripts/upgrade.sh --check

# Windows
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Check
```

**执行升级：**

```bash
# macOS / Linux（交互式确认）
bash scripts/upgrade.sh

# macOS / Linux（非交互模式，适合自动化）
bash scripts/upgrade.sh --yes

# Windows（交互式确认）
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1

# Windows（非交互模式）
powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Yes
```

升级流程：停止服务 → 备份 bin/ + lib/ → 下载新版本 → MD5 校验 → 解压安装 → 写入版本号 → 重启服务 → 健康检查。任何步骤失败将自动回滚到备份版本。

### 手动升级

当在线升级不可用时，可手动操作：

```bash
bash scripts/stop.sh                                          # 停止当前服务
cp ~/Downloads/miloco-mcp-server-NEW-VERSION.tar.gz packages/  # 放入新包
bash scripts/setup.sh                                          # 重新解压（覆盖 bin/ lib/）
bash scripts/start.sh                                          # 启动新版本
```

## 开发者：打包发布包

如果你需要从源码编译并打包：

```bash
# 在 miloco-mcp-server 项目中
cd miloco-mcp-server
bash build-desktop-mac.sh --build --server-only   # macOS
# 或
bash build-desktop-linux.sh --build --server-only  # Linux

# 产出: app/release/miloco-mcp-server-VERSION-OS-ARCH.tar.gz
```

## 许可证

MIT License
