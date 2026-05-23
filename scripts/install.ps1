# FeyaGate Skill — 一键在线安装 (Windows)
# iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex

param(
    [string]$Dir = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$TotalSteps = 4

if ($Dir) {
    $INSTALL_DIR = $Dir
} elseif ($env:FEYAGATE_INSTALL_DIR) {
    $INSTALL_DIR = $env:FEYAGATE_INSTALL_DIR
} else {
    $INSTALL_DIR = Join-Path $env:USERPROFILE ".feyagate"
}

function Write-StepN($n, $msg) {
    Write-Host ""
    Write-Host "[$n/$TotalSteps] $msg" -ForegroundColor Cyan
}

function Write-Ok($msg)  { Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[✗] $msg" -ForegroundColor Red }

function Find-Python {
    foreach ($cmd in @("python", "python3", "py")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            try {
                $ver = & $cmd -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
                if ($LASTEXITCODE -eq 0) { return @{ Cmd = $cmd; Version = $ver } }
            } catch {}
        }
    }
    return $null
}

function Invoke-Feyagate {
    param([string[]]$Args)
    $feyagate = Get-Command feyagate -ErrorAction SilentlyContinue
    if ($feyagate) {
        & feyagate @Args
        return $LASTEXITCODE
    }
    $py = Find-Python
    if (-not $py) { Write-Err "找不到 feyagate 命令"; return 1 }
    & $py.Cmd -m feyagate_skill.cli @Args
    return $LASTEXITCODE
}

function Test-WasRunning {
    $pidFile = Join-Path $INSTALL_DIR "data\miloco-mcp-server.pid"
    if (-not (Test-Path $pidFile)) { return $false }
    try {
        $pid = Get-Content $pidFile
        return $null -ne (Get-Process -Id $pid -ErrorAction SilentlyContinue)
    } catch { return $false }
}

function Show-NextSteps {
    Write-Host ""
    Write-Host "接下来请做 3 件事：" -ForegroundColor White
    Write-Host ""
    Write-Host "  ① 接入 AI 助手（选一个，装完要重启 AI）："
    Write-Host "       Cursor:       feyagate install-cursor"
    Write-Host "       Claude Code:  feyagate install-claude"
    Write-Host "       OpenClaw:     feyagate install-openclaw"
    Write-Host "       Hermes:       feyagate install-hermes"
    Write-Host "       其他助手:     feyagate --help"
    Write-Host ""
    Write-Host "  ② 登录小米/米家:   feyagate auth"
    Write-Host "  ③ 确认已启动:     feyagate status"
    Write-Host ""
    Write-Host "  网页管理: http://localhost:38080"
    Write-Host "  帮助文档: https://www.feyagate.com"
    Write-Host ""
}

if ($Help) {
    Write-Host @"
FeyaGate 一键安装 (Windows)

  iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex

自动完成：安装命令行工具 → 下载网关程序 → 启动服务
"@
    return
}

# ── Welcome ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host '  _____                 ____       _' -ForegroundColor Cyan
Write-Host ' |  ___|__ _   _  __ _ / ___| __ _| |_ ___' -ForegroundColor Cyan
Write-Host ' | |_ / _ \ | | |/ _` | |  _ / _` | __/ _ \' -ForegroundColor Cyan
Write-Host ' |  _|  __/ |_| | (_| | |_| | (_| | ||  __/' -ForegroundColor Cyan
Write-Host ' |_|  \___|\__, |\__,_|\____|\__,_|\__\___|' -ForegroundColor Cyan
Write-Host '           |___/' -ForegroundColor Cyan
Write-Host ""
Write-Info "FeyaGate 智能家居网关 — 自动安装"
Write-Host ""
Write-Host "  即将自动完成（约 2～5 分钟，需联网）："
Write-Host "    ① 安装 feyagate 命令行工具"
Write-Host "    ② 下载智能家居网关程序"
Write-Host "    ③ 启动后台服务"
Write-Host ""

$pyInfo = Find-Python
if (-not $pyInfo) {
    Write-Err "未检测到 Python。请先安装 Python 3.9+："
    Write-Host "       https://www.python.org/downloads/"
    Write-Host "       安装时务必勾选 Add Python to PATH"
    exit 1
}

$pyCmd = $pyInfo.Cmd
$verCheck = & $pyCmd -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Err "Python 版本过低，需要 3.9 或更高"
    exit 1
}

if (Get-Command pip -ErrorAction SilentlyContinue) { $pipCmd = "pip" }
elseif (Get-Command pip3 -ErrorAction SilentlyContinue) { $pipCmd = "pip3" }
else { $pipCmd = "$pyCmd -m pip" }

$pipScripts = & $pyCmd -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>$null
if ($pipScripts -and (Test-Path $pipScripts)) {
    $env:PATH = "$pipScripts;$env:PATH"
}

# ── [1/4] pip ─────────────────────────────────────────────────────────────────
Write-StepN 1 "安装 feyagate 命令行工具…"

try {
    if ($pipCmd -match " -m pip$") {
        Invoke-Expression "$pipCmd install --force-reinstall feyagate-skill"
    } else {
        & $pipCmd install --force-reinstall feyagate-skill
    }
} catch {
    Write-Err "安装失败。请检查网络，或稍后重试。"
    exit 1
}

if (Get-Command feyagate -ErrorAction SilentlyContinue) {
    $verOut = & feyagate --version 2>&1
    Write-Ok "命令行工具已就绪 $verOut"
} else {
    Write-Warn "feyagate 未加入 PATH，将使用 python -m 方式调用"
}

# ── [2/4] stop ────────────────────────────────────────────────────────────────
if (Test-WasRunning) {
    Write-StepN 2 "更新前先停止旧服务…"
    Invoke-Feyagate @("stop") | Out-Null
    Write-Ok "旧服务已停止"
} else {
    Write-StepN 2 "准备安装网关程序…"
    Write-Ok "跳过（无正在运行的服务）"
}

# ── [3/4] setup ───────────────────────────────────────────────────────────────
Write-StepN 3 "下载并安装网关程序（约 30MB，请稍候）…"

if ((Invoke-Feyagate @("setup", "--dir", $INSTALL_DIR)) -ne 0) {
    Write-Err "下载或安装失败。请检查网络后重试。"
    exit 1
}

$binExe = Join-Path $INSTALL_DIR "bin\miloco-mcp-server.exe"
$installOk = Test-Path $binExe

# ── [4/4] start ───────────────────────────────────────────────────────────────
Write-StepN 4 "启动智能家居网关服务…"

if ((Invoke-Feyagate @("start")) -eq 0) {
    Write-Ok "服务已启动"
} else {
    Write-Warn "自动启动未成功，请手动运行: feyagate start"
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ✓ 安装完成！" -ForegroundColor Green

if (-not $installOk) {
    Write-Warn "网关程序可能未完整安装，请查看上方报错信息"
    exit 1
}

Show-NextSteps
