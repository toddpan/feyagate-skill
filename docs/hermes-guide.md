# FeyaGate + Hermes 小白安装配置教程

> 从零开始，让 Hermes AI 助手控制你的智能家居设备。

## 你需要准备什么

| 准备项 | 说明 |
|:-------|:-----|
| 电脑 | Mac、Linux 或 Windows 都行 |
| Python | 版本 3.9 或更高（[下载地址](https://www.python.org/downloads/)） |
| Hermes | 已安装 Hermes Agent（[官网](https://hermes.ai)） |
| 智能设备 | 至少一个已绑定米家/涂鸦/美的/易微联的设备 |
| 网络 | 电脑能联网（安装时需要下载约 30MB 的网关程序） |

---

## 第一步：安装 FeyaGate Skill

打开终端（Mac 按 `Command + 空格`，搜索「终端」；Windows 打开 PowerShell）。

### 方式 A：一条命令搞定（推荐）

**Mac / Linux：**

```bash
curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
```

**Windows（PowerShell）：**

```powershell
iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
```

运行后等待 1-2 分钟，看到 `Setup complete` 就说明安装成功了。安装完跳到**第三步**。

### 方式 B：手动一步步来

如果一条命令没成功，或者你想了解每一步在做什么：

```bash
# 1. 安装 Python 包
pip install feyagate-skill

# 2. 验证安装成功
feyagate --version
```

看到版本号输出就说明装好了。如果提示 `command not found`，试试：
- Mac/Linux：关闭终端重新打开
- Windows：重启 PowerShell
- 或者用 `python -m feyagate_skill.cli --version`

---

## 第二步：下载网关并启动服务

```bash
# 下载 MCP 网关程序（约 30MB，需联网）
feyagate setup

# 启动服务
feyagate start

# 确认服务正在运行
feyagate status
```

看到类似下面的输出就说明成功了：

```
FeyaGate is running (PID: 12345)
Service URL: http://localhost:38080
```

如果提示 `not running`，检查：
- 再跑一次 `feyagate start`
- 看日志找原因：`feyagate log -n 20`

---

## 第三步：将 FeyaGate 接入 Hermes

这是关键一步——让 Hermes 能发现并使用 FeyaGate 的智能家居控制能力。

```bash
feyagate install-hermes
```

成功后会输出：

```
FeyaGate skill installed for Hermes Agent.
Please restart Hermes Agent to load the skill.
```

这条命令做了什么：在 `~/.hermes/skills/` 下创建了一个名为 `feyagate` 的快捷方式，指向 `~/.feyagate/`。Hermes 启动时会自动读取里面的技能描述文件。

**重要：装完后必须重启 Hermes，技能才会生效。**

---

## 第四步：登录智能家居平台

FeyaGate 需要你的账号授权才能控制设备。根据你用的平台选择：

### 小米 / 米家（最常用）

```bash
feyagate auth
```

终端会输出一个网址，类似：

```
Please open this URL in your browser:
https://account.xiaomi.com/oauth2/authorize?...
```

操作步骤：
1. 复制这个网址，粘贴到浏览器打开
2. 用你的小米账号登录
3. 登录成功后，浏览器地址栏会变成一个新的网址（以 `http://localhost` 开头）
4. 把这个新网址完整复制，粘贴回终端按回车

看到 `Authorization successful` 就大功告成了。

验证登录状态：

```bash
feyagate auth --status
```

### 涂鸦 / 美的 / 易微联

这些平台需要通过 Hermes 对话来完成授权（因为流程稍复杂）。等第五步验证 Hermes 能用后，对 Hermes 说：

- 涂鸦：「帮我登录涂鸦平台」
- 美的：「帮我登录美的平台」
- 易微联：「帮我登录易微联平台」

Hermes 会引导你完成。

---

## 第五步：验证一切正常

重启 Hermes 后，试着对它说：

> 「列出我的智能设备」

如果一切正常，Hermes 会返回你账号下绑定的设备列表，包括设备名称、类型、房间等信息。

### 更多你可以试的指令

| 你说的话 | Hermes 会做什么 |
|:---------|:---------------|
| 列出我的智能设备 | 调用 `device/list` 显示所有设备 |
| 打开客厅的灯 | 找到设备并调用 `set_xiaomi_device_property` |
| 把空调温度设为 26 度 | 读取设备规格并设置属性 |
| 用小爱音箱播放音乐 | 调用 `xiaoai/play_music` |
| 小爱播报"该吃饭了" | 调用 `xiaoai/tts` |
| 抓拍一下摄像头画面 | 调用 camera 相关工具 |
| 创建一个定时任务，每天早上 7 点开灯 | 调用 `schedule/*` 工具 |

---

## 日常管理命令

装好之后，这些命令会经常用到：

```bash
feyagate status       # 看服务是否在跑
feyagate stop         # 停止服务
feyagate start        # 启动服务
feyagate restart      # 重启服务
feyagate log -n 30    # 查看最近 30 行日志
feyagate update       # 升级到最新版本
```

网页管理界面：浏览器打开 http://localhost:38080

---

## 常见问题

### Q：`command not found: feyagate`

Python 的 scripts 目录不在系统 PATH 里。解决：

```bash
# Mac/Linux 试试
python3 -m pip install feyagate-skill
# 然后用完整路径
~/.local/bin/feyagate --version

# 或者把路径加到 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Windows 的话确保安装 Python 时勾选了「Add Python to PATH」。

### Q：`feyagate start` 后提示 not running

```bash
# 看日志
feyagate log -n 20

# 常见原因：端口被占用
lsof -i :38080        # Mac/Linux
netstat -ano | findstr 38080  # Windows
```

### Q：Hermes 重启后说不认识 FeyaGate 的命令

确认 symlink 存在：

```bash
ls -la ~/.hermes/skills/feyagate
```

应该看到箭头指向 `~/.feyagate`。如果不存在，重新跑：

```bash
feyagate install-hermes
```

### Q：设备列表为空

- 确认已完成授权：`feyagate auth --status`
- 确认账号下确实绑定了设备（打开米家 App 检查）
- 重启服务试试：`feyagate restart`

### Q：能列出设备，但控制失败

- 设备需要在线（检查 App 里设备状态）
- 设备和电脑需要在同一局域网（部分局域网设备）
- 查看日志定位错误：`feyagate log -n 50`

---

## 整体流程回顾

```
安装 Python 包          下载网关程序           启动服务
pip install ...    →   feyagate setup    →   feyagate start
                                                   ↓
   对 Hermes 说         重启 Hermes          接入 Hermes
  "列出我的设备"   ←   restart Hermes   ←   feyagate install-hermes
                                                   ↓
                                            登录智能家居平台
                                            feyagate auth
```

全部完成后，你就可以通过和 Hermes 对话来控制家里的智能设备了。
