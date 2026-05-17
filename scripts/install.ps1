# FeyaGate Skill — 一键在线安装脚本 (Windows PowerShell)
# 用法: iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
#   或: $env:FEYAGATE_INSTALL_DIR="D:\feyagate-skill"; iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
#
# 自动检测架构，从 fota.json 获取最新版本并安装。

param(
    [string]$Dir = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$FOTA_URL = "https://oneapi.sooncore.com/ota/fota.json"
$REPO_URL = "https://github.com/toddpan/feyagate-skill.git"
$FOTA_TYPE = "feyagate-skill-win"

if ($Dir) {
    $INSTALL_DIR = $Dir
} elseif ($env:FEYAGATE_INSTALL_DIR) {
    $INSTALL_DIR = $env:FEYAGATE_INSTALL_DIR
} else {
    $INSTALL_DIR = Join-Path $env:USERPROFILE "feyagate-skill"
}

# ── Helpers ───────────────────────────────────────────────────────────────────

function Write-Step($msg) {
    Write-Host ""
    Write-Host "▶ $msg" -ForegroundColor Cyan
}

function Write-Info($msg) {
    Write-Host "[INFO]  $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "[WARN]  $msg" -ForegroundColor Yellow
}

function Write-Err($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
}

# ── Help ──────────────────────────────────────────────────────────────────────

if ($Help) {
    Write-Host @"
FeyaGate Skill — 一键在线安装 (Windows)

用法:
  iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex
  powershell -ExecutionPolicy Bypass -File install.ps1 [-Dir <PATH>]

参数:
  -Dir <PATH>    安装目录 (默认: ~\feyagate-skill)
  -Help          显示帮助

环境变量:
  FEYAGATE_INSTALL_DIR    自定义安装目录
"@
    return
}

# ── Banner ────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  _____ _____  _   _   _    ____    _  _____ _____" -ForegroundColor Cyan
Write-Host " |  ___| ____|| \ | | / \  / ___|  / \|_   _| ____|" -ForegroundColor Cyan
Write-Host " | |_  |  _|  |  \| |/ _ \| |  _  / _ \ | | |  _|" -ForegroundColor Cyan
Write-Host " |  _| | |___ | |\  / ___ \ |_| |/ ___ \| | | |___" -ForegroundColor Cyan
Write-Host " |_|   |_____||_| \_/_/   \_\____/_/   \_\_| |_____|" -ForegroundColor Cyan
Write-Host "                          S K I L L" -ForegroundColor Cyan
Write-Host ""
Write-Info "FeyaGate Skill 一键安装程序 (Windows)"
Write-Host ""

# ── Platform detection ────────────────────────────────────────────────────────

$ARCH_LABEL = "x86_64"
if ([Environment]::Is64BitOperatingSystem -eq $false) {
    Write-Err "仅支持 64 位 Windows"
    exit 1
}
if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") {
    $ARCH_LABEL = "arm64"
}
Write-Info "系统: Windows $ARCH_LABEL"

# ── Step 1: Fetch latest version ─────────────────────────────────────────────

Write-Step "正在获取最新版本信息..."

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $fotaJson = Invoke-RestMethod -Uri $FOTA_URL -UseBasicParsing
} catch {
    Write-Err "无法获取版本信息: $FOTA_URL"
    Write-Err $_.Exception.Message
    exit 1
}

$entry = $fotaJson | Where-Object { $_.type -eq $FOTA_TYPE }

if (-not $entry) {
    Write-Err "未找到 $FOTA_TYPE 的发布信息"
    $available = ($fotaJson | Where-Object { $_.type -like "feyagate-skill-*" } | ForEach-Object { $_.type }) -join ", "
    Write-Err "可用平台: $available"
    exit 1
}

$VERSION = $entry.version
$DOWNLOAD_URL = $entry.url
$FILE_MD5 = $entry.md5

Write-Info "最新版本: v$VERSION"
Write-Info "下载地址: $DOWNLOAD_URL"

# ── Step 2: Prepare install directory ─────────────────────────────────────────

$IS_REINSTALL = $false
$LOCAL_VER = "0.0.0"
$versionFile = Join-Path $INSTALL_DIR "data\version.json"
if ((Test-Path (Join-Path $INSTALL_DIR ".git")) -and (Test-Path $versionFile)) {
    try {
        $verData = Get-Content $versionFile -Raw | ConvertFrom-Json
        $LOCAL_VER = $verData.version
        $IS_REINSTALL = $true
    } catch {}
}

Write-Step "准备安装目录: $INSTALL_DIR"

$hasGit = Get-Command git -ErrorAction SilentlyContinue

if (Test-Path (Join-Path $INSTALL_DIR ".git")) {
    if ($IS_REINSTALL) {
        Write-Info "检测到已有安装 (v$LOCAL_VER)，正在更新..."
    } else {
        Write-Info "目录已存在且包含 git 仓库，正在更新..."
    }
    Push-Location $INSTALL_DIR
    # Stash local changes before pulling
    try { git stash --include-untracked -q 2>&1 | Out-Null } catch {}
    try {
        $pullOutput = git pull --rebase 2>&1
        if ($pullOutput -match "Already up to date") {
            Write-Info "仓库已是最新"
        } elseif ($pullOutput -match "Fast-forward|Updating") {
            Write-Info "仓库已更新:"
            $pullOutput | Where-Object { $_ -match "Fast-forward|Updating [0-9a-f]" } | ForEach-Object {
                Write-Info "  $_"
            }
        }
    } catch {
        Write-Warn "git pull 失败: $($_.Exception.Message)"
        Write-Warn "继续安装，但脚本可能不是最新版本..."
    }
    try { git stash pop -q 2>&1 | Out-Null } catch {}
    Pop-Location
} elseif (Test-Path $INSTALL_DIR) {
    Write-Info "目录已存在但不含 git 仓库"
    if ($hasGit) {
        Write-Info "正在初始化仓库并拉取最新脚本..."
        Push-Location $INSTALL_DIR
        try {
            git init 2>&1 | Out-Null
            git remote add origin $REPO_URL 2>$null
            git fetch --depth=1 origin main 2>&1 | Out-Null
            git checkout -f -b main FETCH_HEAD 2>&1 | Out-Null
        } catch {
            Write-Warn "git 初始化失败，将使用现有脚本继续安装..."
        }
        Pop-Location
    } else {
        Write-Info "将更新二进制文件（脚本不会更新，建议安装 git）"
    }
} elseif ($hasGit) {
    Write-Info "正在克隆 feyagate-skill 仓库..."
    try {
        git clone $REPO_URL $INSTALL_DIR 2>&1 | Select-Object -Last 3
    } catch {
        Write-Warn "git clone 失败，将创建基本目录结构..."
        New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
    }
} else {
    Write-Info "git 不可用，创建基本目录结构..."
    New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
}

foreach ($sub in @("packages", "bin", "lib", "data", "config")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $INSTALL_DIR $sub) | Out-Null
}

# ── Step 3: Download release package ─────────────────────────────────────────

$ARCHIVE_NAME = [System.IO.Path]::GetFileName($DOWNLOAD_URL)
$ARCHIVE_PATH = Join-Path $INSTALL_DIR "packages\$ARCHIVE_NAME"

Write-Step "正在下载 v${VERSION} ($ARCHIVE_NAME)..."

$needDownload = $true
if (Test-Path $ARCHIVE_PATH) {
    # Verify MD5 of existing file before skipping download
    if ($FILE_MD5 -and $FILE_MD5 -ne "") {
        $existingMD5 = (Get-FileHash -Path $ARCHIVE_PATH -Algorithm MD5).Hash.ToLower()
        if ($existingMD5 -eq $FILE_MD5.ToLower()) {
            Write-Info "文件已存在且校验通过，跳过下载"
            $needDownload = $false
        } else {
            Write-Warn "已有文件 MD5 不匹配，重新下载..."
            Remove-Item $ARCHIVE_PATH -Force
        }
    } else {
        Write-Info "文件已存在，跳过下载"
        $needDownload = $false
    }
}

if ($needDownload) {
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $ARCHIVE_PATH -UseBasicParsing
        $ProgressPreference = 'Continue'
        $size = [math]::Round((Get-Item $ARCHIVE_PATH).Length / 1MB, 1)
        Write-Info "下载完成 (${size} MB)"
    } catch {
        Write-Err "下载失败: $($_.Exception.Message)"
        exit 1
    }
}

# ── Cleanup old package files ────────────────────────────────────────────────

$pkgDir = Join-Path $INSTALL_DIR "packages"
if (Test-Path $pkgDir) {
    Get-ChildItem -Path $pkgDir -Filter "miloco-mcp-server-*" -File | ForEach-Object {
        if ($_.Name -ne $ARCHIVE_NAME) {
            Write-Info "清理旧版本包: $($_.Name)"
            Remove-Item $_.FullName -Force
        }
    }
}

# ── Step 4: Verify MD5 ───────────────────────────────────────────────────────

if ($FILE_MD5 -and $FILE_MD5 -ne "") {
    Write-Step "校验文件完整性..."
    $localMD5 = (Get-FileHash -Path $ARCHIVE_PATH -Algorithm MD5).Hash.ToLower()
    if ($localMD5 -eq $FILE_MD5.ToLower()) {
        Write-Info "MD5 校验通过 ✓"
    } else {
        Write-Warn "MD5 不匹配 (期望: $FILE_MD5, 实际: $localMD5)"
        Write-Warn "文件可能已损坏，建议删除后重试"
    }
}

# ── Step 5: Extract ──────────────────────────────────────────────────────────

# Stop service before overwriting binary
$WAS_RUNNING = $false
$pidFile = Join-Path $INSTALL_DIR "data\miloco-mcp-server.pid"
if (Test-Path $pidFile) {
    try {
        $pid = Get-Content $pidFile
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            $WAS_RUNNING = $true
            Write-Step "停止服务..."
            $stopBat = Join-Path $INSTALL_DIR "scripts\stop.bat"
            if (Test-Path $stopBat) {
                Push-Location $INSTALL_DIR
                & cmd /c "scripts\stop.bat" 2>&1 | Out-Null
                Pop-Location
            } else {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            }
            Write-Info "服务已停止"
        }
    } catch {}
}
if (-not $WAS_RUNNING) {
    $proc = Get-Process -Name "miloco-mcp-server" -ErrorAction SilentlyContinue
    if ($proc) {
        $WAS_RUNNING = $true
        Write-Step "停止服务..."
        Stop-Process -Name "miloco-mcp-server" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Info "服务已停止"
    }
}

Write-Step "正在解压安装..."

$setupBat = Join-Path $INSTALL_DIR "scripts\setup.bat"

if (Test-Path $setupBat) {
    Write-Info "使用 setup.bat 解压..."
    Push-Location $INSTALL_DIR
    & cmd /c "scripts\setup.bat" 2>&1
    Pop-Location
} else {
    Write-Info "直接解压..."
    $TMP_DIR = Join-Path $env:TEMP "feyagate-skill-$(Get-Random)"
    New-Item -ItemType Directory -Force -Path $TMP_DIR | Out-Null

    $BIN_DIR = Join-Path $INSTALL_DIR "bin"
    $LIB_DIR = Join-Path $INSTALL_DIR "lib"

    if ($ARCHIVE_PATH -match "\.zip$") {
        Expand-Archive -Path $ARCHIVE_PATH -DestinationPath $TMP_DIR -Force
    } elseif ($ARCHIVE_PATH -match "\.(tar\.gz|tgz)$") {
        tar xzf $ARCHIVE_PATH -C $TMP_DIR 2>&1 | Out-Null
    }

    $inner = Get-ChildItem -Path $TMP_DIR -Directory | Select-Object -First 1
    if (-not $inner) { $innerPath = $TMP_DIR } else { $innerPath = $inner.FullName }

    # Binary
    $binFile = Join-Path $innerPath "miloco-mcp-server.exe"
    if (-not (Test-Path $binFile)) { $binFile = Join-Path $innerPath "bin\miloco-mcp-server.exe" }
    if (Test-Path $binFile) {
        Copy-Item $binFile -Destination $BIN_DIR -Force
        Write-Info "bin\miloco-mcp-server.exe ✓"
    } else {
        $binFileNoExt = Join-Path $innerPath "miloco-mcp-server"
        if (Test-Path $binFileNoExt) {
            Copy-Item $binFileNoExt -Destination (Join-Path $BIN_DIR "miloco-mcp-server.exe") -Force
            Write-Info "bin\miloco-mcp-server.exe ✓"
        } else {
            Write-Warn "未找到 miloco-mcp-server 可执行文件"
        }
    }

    # Libraries
    $libSrc = Join-Path $innerPath "lib"
    if (Test-Path $libSrc) {
        Get-ChildItem $libSrc -File | ForEach-Object {
            Copy-Item $_.FullName -Destination $LIB_DIR -Force
        }
        $libCount = (Get-ChildItem $LIB_DIR -File).Count
        Write-Info "lib\ ($libCount files) ✓"
    }

    # WebUI
    $webuiSrc = Join-Path $innerPath "webui"
    if (Test-Path $webuiSrc) {
        $webuiDst = Join-Path $INSTALL_DIR "webui"
        if (Test-Path $webuiDst) { Remove-Item $webuiDst -Recurse -Force }
        Copy-Item $webuiSrc -Destination $webuiDst -Recurse
        Write-Info "webui\ ✓"
    }

    Remove-Item $TMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
}

# ── Step 6: Initialize config ────────────────────────────────────────────────

$configFile = Join-Path $INSTALL_DIR "config\config.yaml"
$configExample = Join-Path $INSTALL_DIR "config\config.yaml.example"

if (-not (Test-Path $configFile)) {
    if (Test-Path $configExample) {
        Copy-Item $configExample $configFile
        Write-Info "config\config.yaml (从示例创建) ✓"
    } else {
        @"
server:
  ws_port: 8765
  http_port: 38080
  bind_address: "0.0.0.0"
  webui_dir: "webui"

auth:
  cloud_server: "cn"
  token_file: "data/auth_token.json"

camera:
  frame_interval: 500
  buffer_max_size: 20
  buffer_ttl: 300
  reconnect_min: 3
  reconnect_max: 1200
  jpeg_quality: 90
"@ | Out-File -FilePath $configFile -Encoding UTF8
        Write-Info "config\config.yaml (默认配置) ✓"
    }
}

# ── Step 7: Verify ───────────────────────────────────────────────────────────

Write-Step "验证安装..."

$binExe = Join-Path $INSTALL_DIR "bin\miloco-mcp-server.exe"
if (Test-Path $binExe) {
    $size = [math]::Round((Get-Item $binExe).Length / 1MB, 1)
    Write-Info "Binary: bin\miloco-mcp-server.exe (${size} MB) ✓"
} else {
    Write-Err "Binary 未找到: bin\miloco-mcp-server.exe"
}

$libDir = Join-Path $INSTALL_DIR "lib"
if (Test-Path $libDir) {
    $libCount = (Get-ChildItem $libDir -File -ErrorAction SilentlyContinue).Count
    Write-Info "Libraries: $libCount files ✓"
}

if (Test-Path $configFile) {
    Write-Info "Config: config\config.yaml ✓"
}

$webuiDir = Join-Path $INSTALL_DIR "webui"
if (Test-Path $webuiDir) {
    Write-Info "WebUI: webui\ ✓"
}

# ── Write version info ────────────────────────────────────────────────────────

$versionData = @{
    version    = $VERSION
    platform   = "Windows-$ARCH_LABEL"
    fota_type  = $FOTA_TYPE
    package    = [System.IO.Path]::GetFileName($DOWNLOAD_URL)
    timestamp  = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

New-Item -ItemType Directory -Force -Path (Join-Path $INSTALL_DIR "data") | Out-Null
$versionData | Out-File -FilePath (Join-Path $INSTALL_DIR "data\version.json") -Encoding UTF8
Write-Info "版本信息已写入 data\version.json"

# ── Restart service if it was running before ─────────────────────────────────

if ($WAS_RUNNING) {
    Write-Step "重启服务..."
    $startBat = Join-Path $INSTALL_DIR "scripts\start.bat"
    if (Test-Path $startBat) {
        Push-Location $INSTALL_DIR
        & cmd /c "scripts\start.bat" 2>&1
        Pop-Location
    }
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
if ($IS_REINSTALL) {
    Write-Host "║     FeyaGate Skill 更新完成！               ║" -ForegroundColor Green
} else {
    Write-Host "║     FeyaGate Skill 安装完成！               ║" -ForegroundColor Green
}
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Info "安装目录: $INSTALL_DIR"
if ($IS_REINSTALL) {
    Write-Info "版本: v$LOCAL_VER → v$VERSION"
} else {
    Write-Info "版本: v$VERSION"
}
Write-Host ""

if ($IS_REINSTALL) {
    Write-Host "更新已完成" -NoNewline -ForegroundColor White
    if ($WAS_RUNNING) {
        Write-Host "，服务已重启" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "  启动服务: scripts\start.bat"
    }
} else {
    Write-Host "下一步:" -NoNewline -ForegroundColor White
    Write-Host ""
    Write-Host "  1. 进入目录:       cd $INSTALL_DIR"
    Write-Host "  2. 编辑配置:       notepad config\config.yaml"
    Write-Host "  3. 启动服务:       scripts\start.bat"
    Write-Host "  4. 首次授权:       python scripts\auth.py"
    Write-Host "  5. 健康检查:       scripts\health_check.bat"
}
Write-Host ""
Write-Host "  服务地址: http://localhost:38080/mcp/http"
Write-Host "  WebUI:    http://localhost:38080"
Write-Host ""
Write-Info "详细文档: https://www.feyagate.com"
Write-Host ""
