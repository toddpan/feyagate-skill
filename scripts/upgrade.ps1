# FeyaGate Skill — 在线升级脚本 (Windows PowerShell)
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1              # 交互式升级
#   powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Check       # 仅检查是否有新版本
#   powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Yes         # 非交互模式，自动确认升级
#
# 流程: 检测平台 → 读取本地版本 → 获取远程最新版本 → 对比 →
#       停止服务 → 备份 → 下载 → MD5校验 → 解压安装 → 写版本 →
#       重启 → 健康检查 (失败则自动回滚)

param(
    [switch]$Check,
    [switch]$Yes,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$FOTA_URL = "https://oneapi.sooncore.com/ota/fota.json"
$FOTA_TYPE = "feyagate-skill-win"

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DATA_DIR = Join-Path $ROOT_DIR "data"
$BIN_DIR = Join-Path $ROOT_DIR "bin"
$LIB_DIR = Join-Path $ROOT_DIR "lib"
$PKG_DIR = Join-Path $ROOT_DIR "packages"
$BACKUP_DIR = Join-Path $DATA_DIR "upgrade_backup"
$VERSION_FILE = Join-Path $DATA_DIR "version.json"

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
FeyaGate Skill — 在线升级 (Windows)

用法:
  powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1              交互式升级
  powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Check       仅检查是否有新版本
  powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Yes         非交互模式，自动确认升级
  powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Help        显示帮助
"@
    return
}

# ── Platform detection ────────────────────────────────────────────────────────

$ARCH_LABEL = "x86_64"
if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") {
    $ARCH_LABEL = "arm64"
}
Write-Info "系统: Windows $ARCH_LABEL"
Write-Info "安装目录: $ROOT_DIR"

# ── Read local version ────────────────────────────────────────────────────────

$LOCAL_VERSION = ""

if (Test-Path $VERSION_FILE) {
    try {
        $verData = Get-Content $VERSION_FILE -Raw | ConvertFrom-Json
        $LOCAL_VERSION = $verData.version
    } catch {}
}

# Fallback: parse from package filename
if (-not $LOCAL_VERSION -and (Test-Path $PKG_DIR)) {
    $pkg = Get-ChildItem -Path $PKG_DIR -Filter "miloco-mcp-server-*.zip" -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($pkg) {
        $match = [regex]::Match($pkg.Name, 'miloco-mcp-server-(\d+\.\d+\.\d+)')
        if ($match.Success) {
            $LOCAL_VERSION = $match.Groups[1].Value
        }
    }
}

if (-not $LOCAL_VERSION) {
    $LOCAL_VERSION = "0.0.0"
}

Write-Info "当前版本: v$LOCAL_VERSION"

# ── Fetch latest version from fota.json ──────────────────────────────────────

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
    exit 1
}

$REMOTE_VERSION = $entry.version
$DOWNLOAD_URL = $entry.url
$FILE_MD5 = $entry.md5
$RELEASE_NOTES = $entry.release_notes

Write-Info "最新版本: v$REMOTE_VERSION"

if ($RELEASE_NOTES) {
    Write-Info "更新说明: $RELEASE_NOTES"
}

# ── Version comparison ───────────────────────────────────────────────────────

function Compare-Versions($v1, $v2) {
    if ($v1 -eq $v2) { return 0 }
    $a1 = $v1 -split '\.'
    $a2 = $v2 -split '\.'
    $len = [Math]::Max($a1.Length, $a2.Length)
    for ($i = 0; $i -lt $len; $i++) {
        $n1 = if ($i -lt $a1.Length) { [int]$a1[$i] } else { 0 }
        $n2 = if ($i -lt $a2.Length) { [int]$a2[$i] } else { 0 }
        if ($n1 -gt $n2) { return 1 }
        if ($n1 -lt $n2) { return 2 }
    }
    return 0
}

$cmp = Compare-Versions $REMOTE_VERSION $LOCAL_VERSION

if ($cmp -eq 0) {
    Write-Info "当前已是最新版本 (v$LOCAL_VERSION)，无需升级。"
    return
} elseif ($cmp -eq 2) {
    Write-Warn "当前版本 (v$LOCAL_VERSION) 比远程版本 (v$REMOTE_VERSION) 更新。"
    Write-Warn "如需降级请手动处理。"
    return
}

# ── Check-only mode ──────────────────────────────────────────────────────────

if ($Check) {
    Write-Host ""
    Write-Host "  当前版本: v$LOCAL_VERSION" -ForegroundColor Yellow
    Write-Host "  最新版本: v$REMOTE_VERSION" -ForegroundColor Green
    if ($RELEASE_NOTES) {
        Write-Host "  更新说明: $RELEASE_NOTES"
    }
    Write-Host ""
    Write-Info "发现新版本！运行以下命令升级:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\upgrade.ps1 -Yes"
    return
}

# ── Confirm upgrade ──────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  即将升级: v$LOCAL_VERSION → v$REMOTE_VERSION" -ForegroundColor White

if (-not $Yes) {
    $answer = Read-Host "确认升级？[y/N]"
    if ($answer -notmatch '^[yY]') {
        Write-Info "已取消升级。"
        return
    }
}

# ── Stop service ─────────────────────────────────────────────────────────────

$WAS_RUNNING = $false
$pidFile = Join-Path $DATA_DIR "miloco-mcp-server.pid"

if (Test-Path $pidFile) {
    try {
        $procId = Get-Content $pidFile
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            $WAS_RUNNING = $true
            Write-Step "停止服务..."
            $stopBat = Join-Path $ROOT_DIR "scripts\stop.bat"
            if (Test-Path $stopBat) {
                Push-Location $ROOT_DIR
                & cmd /c "scripts\stop.bat" 2>&1 | Out-Null
                Pop-Location
            } else {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            }
            Write-Info "服务已停止"
        }
    } catch {}
}

if (-not $WAS_RUNNING) {
    # Also check for running process by name
    $proc = Get-Process -Name "miloco-mcp-server" -ErrorAction SilentlyContinue
    if ($proc) {
        $WAS_RUNNING = $true
        Write-Step "停止服务..."
        Stop-Process -Name "miloco-mcp-server" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Info "服务已停止"
    } else {
        Write-Info "服务未运行，跳过停止步骤"
    }
}

# ── Backup current version ───────────────────────────────────────────────────

Write-Step "备份当前版本..."

if (Test-Path $BACKUP_DIR) {
    Remove-Item $BACKUP_DIR -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null

$binExe = Join-Path $BIN_DIR "miloco-mcp-server.exe"
if (Test-Path $binExe) {
    Copy-Item $binExe -Destination $BACKUP_DIR -Force
    Write-Info "备份 bin\miloco-mcp-server.exe ✓"
}

if (Test-Path $LIB_DIR) {
    $libFiles = Get-ChildItem -Path $LIB_DIR -File -ErrorAction SilentlyContinue
    if ($libFiles) {
        $libBackup = Join-Path $BACKUP_DIR "lib"
        New-Item -ItemType Directory -Force -Path $libBackup | Out-Null
        Copy-Item $libFiles -Destination $libBackup -Force
        Write-Info "备份 lib\ ($($libFiles.Count) files) ✓"
    }
}

if (Test-Path $VERSION_FILE) {
    Copy-Item $VERSION_FILE -Destination (Join-Path $BACKUP_DIR "version.json.bak") -Force
}

# ── Download new package ─────────────────────────────────────────────────────

$ARCHIVE_NAME = [System.IO.Path]::GetFileName($DOWNLOAD_URL)
$ARCHIVE_PATH = Join-Path $PKG_DIR $ARCHIVE_NAME

Write-Step "正在下载 v${REMOTE_VERSION} ($ARCHIVE_NAME)..."

New-Item -ItemType Directory -Force -Path $PKG_DIR | Out-Null

if (Test-Path $ARCHIVE_PATH) {
    Write-Info "文件已存在，跳过下载"
} else {
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $ARCHIVE_PATH -UseBasicParsing
        $ProgressPreference = 'Continue'
        $size = [math]::Round((Get-Item $ARCHIVE_PATH).Length / 1MB, 1)
        Write-Info "下载完成 (${size} MB)"
    } catch {
        Write-Err "下载失败: $($_.Exception.Message)"
        # Rollback
        if ($WAS_RUNNING) {
            Invoke-Rollback
        } else {
            Remove-Item $BACKUP_DIR -Recurse -Force -ErrorAction SilentlyContinue
        }
        exit 1
    }
}

# ── Verify MD5 ───────────────────────────────────────────────────────────────

if ($FILE_MD5 -and $FILE_MD5 -ne "") {
    Write-Step "校验文件完整性..."
    $localMD5 = (Get-FileHash -Path $ARCHIVE_PATH -Algorithm MD5).Hash.ToLower()
    if ($localMD5 -eq $FILE_MD5.ToLower()) {
        Write-Info "MD5 校验通过 ✓"
    } else {
        Write-Err "MD5 不匹配 (期望: $FILE_MD5, 实际: $localMD5)"
        Write-Err "文件可能已损坏，正在删除并回滚..."
        Remove-Item $ARCHIVE_PATH -Force -ErrorAction SilentlyContinue
        if ($WAS_RUNNING) {
            Invoke-Rollback
            Start-ServiceAfterUpgrade
        } else {
            Invoke-Rollback
        }
        exit 1
    }
}

# ── Extract and install ──────────────────────────────────────────────────────

Write-Step "正在解压安装..."

$setupBat = Join-Path $ROOT_DIR "scripts\setup.bat"

if (Test-Path $setupBat) {
    Push-Location $ROOT_DIR
    & cmd /c "scripts\setup.bat" 2>&1
    Pop-Location
} else {
    $TMP_DIR = Join-Path $env:TEMP "feyagate-upgrade-$(Get-Random)"
    New-Item -ItemType Directory -Force -Path $TMP_DIR | Out-Null

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
        $webuiDst = Join-Path $ROOT_DIR "webui"
        if (Test-Path $webuiDst) { Remove-Item $webuiDst -Recurse -Force }
        Copy-Item $webuiSrc -Destination $webuiDst -Recurse
        Write-Info "webui\ ✓"
    }

    Remove-Item $TMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
}

# ── Write version.json ───────────────────────────────────────────────────────

$versionData = @{
    version    = $REMOTE_VERSION
    platform   = "Windows-$ARCH_LABEL"
    fota_type  = $FOTA_TYPE
    package    = $ARCHIVE_NAME
    timestamp  = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

New-Item -ItemType Directory -Force -Path $DATA_DIR | Out-Null
$versionData | Out-File -FilePath $VERSION_FILE -Encoding UTF8
Write-Info "版本信息已写入 data\version.json"

# ── Restart service (if it was running) ──────────────────────────────────────

function Start-ServiceAfterUpgrade {
    $startBat = Join-Path $ROOT_DIR "scripts\start.bat"
    if (Test-Path $startBat) {
        Push-Location $ROOT_DIR
        & cmd /c "scripts\start.bat" 2>&1
        Pop-Location
    }
}

function Invoke-Rollback {
    Write-Err "升级失败，正在回滚到之前的版本..."

    $backupExe = Join-Path $BACKUP_DIR "miloco-mcp-server.exe"
    if (Test-Path $backupExe) {
        Copy-Item $backupExe -Destination $BIN_DIR -Force
        Write-Info "已恢复 bin\miloco-mcp-server.exe"
    }

    $backupLib = Join-Path $BACKUP_DIR "lib"
    if (Test-Path $backupLib) {
        Get-ChildItem -Path $LIB_DIR -File -ErrorAction SilentlyContinue | Remove-Item -Force
        Get-ChildItem $backupLib -File | ForEach-Object {
            Copy-Item $_.FullName -Destination $LIB_DIR -Force
        }
        Write-Info "已恢复 lib\"
    }

    $backupVer = Join-Path $BACKUP_DIR "version.json.bak"
    if (Test-Path $backupVer) {
        Copy-Item $backupVer -Destination $VERSION_FILE -Force
        Write-Info "已恢复 data\version.json"
    }

    Remove-Item $BACKUP_DIR -Recurse -Force -ErrorAction SilentlyContinue
    Write-Err "回滚完成。请检查服务状态。"
}

if ($WAS_RUNNING) {
    Write-Step "重启服务..."
    try {
        Start-ServiceAfterUpgrade
    } catch {
        Write-Err "服务启动失败，正在回滚..."
        Invoke-Rollback
        Start-ServiceAfterUpgrade
        exit 1
    }

    Write-Step "健康检查..."
    Start-Sleep -Seconds 2

    $port = 38080
    $configFile = Join-Path $ROOT_DIR "config\config.yaml"
    if (Test-Path $configFile) {
        $content = Get-Content $configFile -Raw
        $m = [regex]::Match($content, 'http_port:\s*(\d+)')
        if ($m.Success) { $port = [int]$m.Groups[1].Value }
    }

    $healthy = $false
    for ($i = 0; $i -lt 5; $i++) {
        Start-Sleep -Seconds 2
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        } catch {}
    }

    if ($healthy) {
        Write-Info "健康检查通过 ✓"
    } else {
        Write-Warn "健康检查未通过，服务可能仍在初始化中"
        Write-Warn "请手动检查: scripts\health_check.bat"
    }
}

# ── Cleanup backup ────────────────────────────────────────────────────────────

Remove-Item $BACKUP_DIR -Recurse -Force -ErrorAction SilentlyContinue

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     FeyaGate Skill 升级完成！               ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Info "版本: v$LOCAL_VERSION → v$REMOTE_VERSION"
if ($WAS_RUNNING) {
    Write-Info "服务已重启并运行中"
}
Write-Host ""
