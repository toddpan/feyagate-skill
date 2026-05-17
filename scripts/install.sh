#!/usr/bin/env bash
# FeyaGate Skill — 一键在线安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
#   或: curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash -s -- --dir ~/my-skill
#
# 自动检测平台/架构，从 fota.json 获取最新版本并安装。
set -euo pipefail

FOTA_URL="https://oneapi.sooncore.com/ota/fota.json"
INSTALL_DIR="${FEYAGATE_INSTALL_DIR:-$HOME/feyagate-skill}"
REPO_URL="https://github.com/toddpan/feyagate-skill.git"
VERBOSE=0

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$*" >&2; }
step()  { printf "\n${CYAN}▶ %s${NC}\n" "$*"; }
debug() { [ "$VERBOSE" = 1 ] && printf "${BLUE}[DEBUG]${NC} %s\n" "$*" || true; }

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)       INSTALL_DIR="$2"; shift 2 ;;
        --verbose)   VERBOSE=1; shift ;;
        -h|--help)
            cat <<'EOF'
FeyaGate Skill — 一键在线安装

用法:
  curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
  curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash -s -- [选项]

选项:
  --dir <PATH>    安装目录 (默认: ~/feyagate-skill)
  --verbose       显示详细输出
  -h, --help      显示帮助

环境变量:
  FEYAGATE_INSTALL_DIR    自定义安装目录
EOF
            exit 0 ;;
        *) error "未知参数: $1"; exit 1 ;;
    esac
done

# ── Platform detection ────────────────────────────────────────────────────────
detect_platform() {
    local os arch fota_type os_label arch_label

    case "$(uname -s)" in
        Darwin) os="mac";   os_label="Darwin"  ;;
        Linux)  os="linux"; os_label="Linux"   ;;
        MINGW*|MSYS*|CYGWIN*)
            error "Windows 请使用 PowerShell 安装:"
            error "  iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex"
            exit 1 ;;
        *) error "不支持的操作系统: $(uname -s)"; exit 1 ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64)  arch="x64";  arch_label="x86_64" ;;
        arm64|aarch64) arch="arm64"; arch_label="arm64"  ;;
        *)             arch="x64";   arch_label="$(uname -m)" ;;
    esac

    PLATFORM="$os"
    ARCH="$arch"
    OS_LABEL="$os_label"
    ARCH_LABEL="$arch_label"
    FOTA_TYPE="feyagate-skill-${os}-${arch}"
}

# ── Dependency check ──────────────────────────────────────────────────────────
check_deps() {
    local missing=()

    if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
        missing+=("curl 或 wget")
    fi

    if ! command -v tar &>/dev/null; then
        missing+=("tar")
    fi

    if ! command -v git &>/dev/null; then
        warn "未安装 git，将跳过克隆仓库步骤（仅下载二进制包）"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        error "缺少必要工具: ${missing[*]}"
        error "请先安装后重试"
        exit 1
    fi
}

# ── HTTP download helper ──────────────────────────────────────────────────────
download() {
    local url="$1" dest="$2"
    if command -v curl &>/dev/null; then
        curl -fSL --progress-bar -o "$dest" "$url"
    elif command -v wget &>/dev/null; then
        wget -q --show-progress -O "$dest" "$url"
    fi
}

fetch_text() {
    local url="$1"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url"
    elif command -v wget &>/dev/null; then
        wget -qO- "$url"
    fi
}

# ── JSON parsing (no jq dependency) ───────────────────────────────────────────
parse_fota_field() {
    local json="$1" fota_type="$2" field="$3"
    echo "$json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    if item.get('type') == '$fota_type':
        print(item.get('$field', ''))
        break
" 2>/dev/null || echo "$json" | python -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    if item.get('type') == '$fota_type':
        print(item.get('$field', ''))
        break
" 2>/dev/null || {
    # Fallback: basic grep/sed extraction
    echo "$json" | tr '{},' '\n' | grep -A1 "\"type\":.*\"$fota_type\"" | \
        grep "\"$field\"" | sed 's/.*"'"$field"'"\s*:\s*"\([^"]*\)".*/\1/'
}
}

# ── Service management ────────────────────────────────────────────────────────
is_service_running() {
    local pid_file="$INSTALL_DIR/data/miloco-mcp-server.pid"
    [ -f "$pid_file" ] || return 1
    local pid
    pid="$(cat "$pid_file")"
    kill -0 "$pid" 2>/dev/null
}

stop_service() {
    if [ -f "$INSTALL_DIR/scripts/stop.sh" ]; then
        bash "$INSTALL_DIR/scripts/stop.sh" 2>/dev/null || true
    else
        local pid_file="$INSTALL_DIR/data/miloco-mcp-server.pid"
        if [ -f "$pid_file" ]; then
            local pid
            pid="$(cat "$pid_file")"
            kill "$pid" 2>/dev/null || true
            sleep 2
            kill -9 "$pid" 2>/dev/null || true
            rm -f "$pid_file"
        fi
    fi
}

start_service() {
    if [ -f "$INSTALL_DIR/scripts/start.sh" ]; then
        bash "$INSTALL_DIR/scripts/start.sh" 2>/dev/null
    fi
}

# ── Read local version ────────────────────────────────────────────────────────
get_local_version() {
    local ver=""
    local vf="$INSTALL_DIR/data/version.json"
    if [ -f "$vf" ]; then
        ver="$(python3 -c "import json; print(json.load(open('$vf')).get('version',''))" 2>/dev/null || true)"
    fi
    echo "${ver:-0.0.0}"
}

# ── Main ──────────────────────────────────────────────────────────────────────

printf "\n${BOLD}${CYAN}"
cat <<'BANNER'
  _____ _____  _   _   _    ____    _  _____ _____
 |  ___| ____|| \ | | / \  / ___|  / \|_   _| ____|
 | |_  |  _|  |  \| |/ _ \| |  _  / _ \ | | |  _|
 |  _| | |___ | |\  / ___ \ |_| |/ ___ \| | | |___
 |_|   |_____||_| \_/_/   \_\____/_/   \_\_| |_____|
                          S K I L L
BANNER
printf "${NC}\n"
info "FeyaGate Skill 一键安装程序"
echo ""

detect_platform
info "系统: ${OS_LABEL} ${ARCH_LABEL}"

check_deps

# ── Step 1: Fetch latest version from fota.json ──────────────────────────────
step "正在获取最新版本信息..."

FOTA_JSON="$(fetch_text "$FOTA_URL")" || {
    error "无法获取版本信息: $FOTA_URL"
    exit 1
}

VERSION="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "version")"
DOWNLOAD_URL="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "url")"
FILE_MD5="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "md5")"

if [ -z "$VERSION" ] || [ -z "$DOWNLOAD_URL" ]; then
    error "未找到 $FOTA_TYPE 的发布信息"
    error "可用平台: $(echo "$FOTA_JSON" | grep -o '"feyagate-skill-[^"]*"' | tr '\n' ' ')"
    exit 1
fi

printf "${GREEN}[INFO]${NC}  最新版本: ${BOLD}v${VERSION}${NC}\n"
info "下载地址: $DOWNLOAD_URL"

# ── Step 2: Clone or create install directory ─────────────────────────────────
IS_REINSTALL=false
LOCAL_VER="$(get_local_version)"

step "准备安装目录: $INSTALL_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    IS_REINSTALL=true
    info "检测到已有安装 (v${LOCAL_VER})，正在更新..."
    # Stash local changes before pulling to avoid conflicts
    (cd "$INSTALL_DIR" && git stash --include-untracked -q 2>/dev/null || true)
    PULL_OUTPUT="$(cd "$INSTALL_DIR" && git pull --rebase 2>&1)" || {
        warn "git pull 失败: $PULL_OUTPUT"
        warn "继续安装，但脚本可能不是最新版本..."
    }
    (cd "$INSTALL_DIR" && git stash pop -q 2>/dev/null || true)
    if echo "$PULL_OUTPUT" | grep -q "Already up to date"; then
        info "仓库已是最新"
    elif echo "$PULL_OUTPUT" | grep -q "Fast-forward\|Updating"; then
        info "仓库已更新:"
        echo "$PULL_OUTPUT" | grep -E "^Fast-forward|Updating [0-9a-f]+\.\.[0-9a-f]+" | while read -r line; do
            info "  $line"
        done
    fi
elif [ -d "$INSTALL_DIR" ]; then
    info "目录已存在但不含 git 仓库"
    if command -v git &>/dev/null; then
        info "正在初始化仓库并拉取最新脚本..."
        (cd "$INSTALL_DIR" && git init && git remote add origin "$REPO_URL" 2>/dev/null || true \
            && git fetch --depth=1 origin main 2>&1 \
            && git checkout -f -b main FETCH_HEAD 2>&1) || {
            warn "git 初始化失败，将使用现有脚本继续安装..."
        }
    else
        info "将更新二进制文件（脚本不会更新，建议安装 git）"
    fi
elif command -v git &>/dev/null; then
    info "正在克隆 feyagate-skill 仓库..."
    git clone "$REPO_URL" "$INSTALL_DIR" 2>&1 | tail -3 || {
        warn "git clone 失败，将创建基本目录结构..."
        mkdir -p "$INSTALL_DIR"
    }
else
    info "git 不可用，创建基本目录结构..."
    mkdir -p "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"/{packages,bin,lib,data,config}

# ── Step 3: Download release package ─────────────────────────────────────────
ARCHIVE_NAME="$(basename "$DOWNLOAD_URL")"
ARCHIVE_PATH="$INSTALL_DIR/packages/$ARCHIVE_NAME"

step "正在下载 v${VERSION} (${ARCHIVE_NAME})..."

NEED_DOWNLOAD=true
if [ -f "$ARCHIVE_PATH" ]; then
    # Verify MD5 of existing file before skipping download
    if [ -n "$FILE_MD5" ] && [ "$FILE_MD5" != "None" ]; then
        EXISTING_MD5=""
        if command -v md5sum &>/dev/null; then
            EXISTING_MD5="$(md5sum "$ARCHIVE_PATH" | awk '{print $1}')"
        elif command -v md5 &>/dev/null; then
            EXISTING_MD5="$(md5 -q "$ARCHIVE_PATH")"
        fi
        if [ -n "$EXISTING_MD5" ] && [ "$EXISTING_MD5" = "$FILE_MD5" ]; then
            info "文件已存在且校验通过，跳过下载"
            NEED_DOWNLOAD=false
        else
            warn "已有文件 MD5 不匹配，重新下载..."
            rm -f "$ARCHIVE_PATH"
        fi
    else
        info "文件已存在，跳过下载"
        NEED_DOWNLOAD=false
    fi
fi

if [ "$NEED_DOWNLOAD" = true ]; then
    download "$DOWNLOAD_URL" "$ARCHIVE_PATH" || true
    if [ ! -f "$ARCHIVE_PATH" ] || [ ! -s "$ARCHIVE_PATH" ]; then
        rm -f "$ARCHIVE_PATH"
        error "下载失败: $DOWNLOAD_URL"
        error "该平台的发布包可能尚未上传，请检查:"
        error "  https://www.feyagate.com (下载页面)"
        error "  https://oneapi.sooncore.com/ota/fota.json (版本信息)"
        exit 1
    fi
    info "下载完成 ($(du -h "$ARCHIVE_PATH" | awk '{print $1}'))"
fi

# ── Cleanup old package files ────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/packages" ]; then
    for old_pkg in "$INSTALL_DIR/packages"/miloco-mcp-server-*.tar.gz \
                   "$INSTALL_DIR/packages"/miloco-mcp-server-*.zip; do
        [ -f "$old_pkg" ] || continue
        [ "$(basename "$old_pkg")" = "$ARCHIVE_NAME" ] && continue
        info "清理旧版本包: $(basename "$old_pkg")"
        rm -f "$old_pkg"
    done
fi

# ── Step 4: Verify MD5 (if available) ────────────────────────────────────────
if [ -n "$FILE_MD5" ] && [ "$FILE_MD5" != "None" ]; then
    step "校验文件完整性..."
    LOCAL_MD5=""
    if command -v md5sum &>/dev/null; then
        LOCAL_MD5="$(md5sum "$ARCHIVE_PATH" | awk '{print $1}')"
    elif command -v md5 &>/dev/null; then
        LOCAL_MD5="$(md5 -q "$ARCHIVE_PATH")"
    fi

    if [ -n "$LOCAL_MD5" ]; then
        if [ "$LOCAL_MD5" = "$FILE_MD5" ]; then
            info "MD5 校验通过 ✓"
        else
            warn "MD5 不匹配 (期望: $FILE_MD5, 实际: $LOCAL_MD5)"
            warn "文件可能已损坏，建议删除后重试"
        fi
    fi
fi

# ── Step 5: Extract (reuse setup.sh if available, otherwise inline) ──────────
# Stop service before overwriting binary
WAS_RUNNING=false
if is_service_running; then
    WAS_RUNNING=true
    step "停止服务..."
    stop_service
    info "服务已停止"
fi

step "正在解压安装..."

BIN_DIR="$INSTALL_DIR/bin"
LIB_DIR="$INSTALL_DIR/lib"

if [ -f "$INSTALL_DIR/scripts/setup.sh" ]; then
    info "使用 setup.sh 解压..."
    bash "$INSTALL_DIR/scripts/setup.sh" --package "$ARCHIVE_PATH" || true
else
    info "直接解压..."
    TMP_DIR="$(mktemp -d)"

    case "$ARCHIVE_PATH" in
        *.tar.gz|*.tgz) tar xzf "$ARCHIVE_PATH" -C "$TMP_DIR" ;;
        *.zip)          unzip -qo "$ARCHIVE_PATH" -d "$TMP_DIR" ;;
    esac

    INNER="$(find "$TMP_DIR" -maxdepth 1 -mindepth 1 -type d | head -1)"
    [ -z "$INNER" ] && INNER="$TMP_DIR"

    # Binary
    for bin_path in "$INNER/miloco-mcp-server" "$INNER/bin/miloco-mcp-server"; do
        if [ -f "$bin_path" ]; then
            cp "$bin_path" "$BIN_DIR/"
            chmod +x "$BIN_DIR/miloco-mcp-server"
            info "bin/miloco-mcp-server ✓"
            break
        fi
    done

    # Libraries
    if [ -d "$INNER/lib" ]; then
        cp "$INNER/lib"/* "$LIB_DIR/" 2>/dev/null || true
        info "lib/ ($(ls -1 "$LIB_DIR" | wc -l | tr -d ' ') files) ✓"
    fi

    # bin/lib symlink for rpath
    [ ! -e "$BIN_DIR/lib" ] && ln -sf ../lib "$BIN_DIR/lib"

    # WebUI
    if [ -d "$INNER/webui" ]; then
        rm -rf "$INSTALL_DIR/webui"
        cp -r "$INNER/webui" "$INSTALL_DIR/webui"
        info "webui/ ✓"
    fi

    rm -rf "$TMP_DIR"
fi

# ── Step 6: Initialize config ────────────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/config/config.yaml" ]; then
    if [ -f "$INSTALL_DIR/config/config.yaml.example" ]; then
        cp "$INSTALL_DIR/config/config.yaml.example" "$INSTALL_DIR/config/config.yaml"
        info "config/config.yaml (从示例创建) ✓"
    else
        cat > "$INSTALL_DIR/config/config.yaml" <<'YAML'
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
YAML
        info "config/config.yaml (默认配置) ✓"
    fi
fi

# ── Step 7: Verify installation ──────────────────────────────────────────────
step "验证安装..."

BIN_NAME="miloco-mcp-server"
INSTALL_OK=true

if [ -x "$BIN_DIR/$BIN_NAME" ]; then
    info "Binary: bin/$BIN_NAME ($(du -h "$BIN_DIR/$BIN_NAME" | awk '{print $1}')) ✓"
else
    error "Binary 未找到: bin/$BIN_NAME"
    INSTALL_OK=false
fi

LIB_COUNT="$(ls -1 "$LIB_DIR" 2>/dev/null | { grep -v '\.gitkeep' || true; } | wc -l | tr -d ' ')"
info "Libraries: $LIB_COUNT files ✓"

if [ -f "$INSTALL_DIR/config/config.yaml" ]; then
    info "Config: config/config.yaml ✓"
fi

if [ -d "$INSTALL_DIR/webui" ]; then
    info "WebUI: webui/ ✓"
fi

# ── Write version info ────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR/data"
cat > "$INSTALL_DIR/data/version.json" <<EOF
{
  "version": "$VERSION",
  "platform": "$OS_LABEL-$ARCH_LABEL",
  "fota_type": "$FOTA_TYPE",
  "package": "$(basename "$DOWNLOAD_URL")",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
info "版本信息已写入 data/version.json"

# ── Restart service if it was running before ─────────────────────────────────
if [ "$WAS_RUNNING" = true ]; then
    step "重启服务..."
    start_service || warn "服务重启失败，请手动启动: bash scripts/start.sh"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
printf "${GREEN}${BOLD}"
if [ "$IS_REINSTALL" = true ]; then
    cat <<'DONE'
╔══════════════════════════════════════════════╗
║     FeyaGate Skill 更新完成！               ║
╚══════════════════════════════════════════════╝
DONE
else
    cat <<'DONE'
╔══════════════════════════════════════════════╗
║     FeyaGate Skill 安装完成！               ║
╚══════════════════════════════════════════════╝
DONE
fi
printf "${NC}\n"

info "安装目录: $INSTALL_DIR"
if [ "$IS_REINSTALL" = true ]; then
    info "版本: v${LOCAL_VER} → v${VERSION}"
else
    info "版本: v${VERSION}"
fi
echo ""
if [ "$IS_REINSTALL" = true ]; then
    printf "${BOLD}更新已完成"
    if [ "$WAS_RUNNING" = true ]; then
        printf "，服务已重启${NC}\n"
    else
        printf "${NC}\n"
        echo "  启动服务: bash scripts/start.sh"
    fi
else
    printf "${BOLD}下一步:${NC}\n"
    echo "  1. 进入目录:       cd $INSTALL_DIR"
    echo "  2. 编辑配置:       nano config/config.yaml"
    echo "  3. 启动服务:       bash scripts/start.sh"
    echo "  4. 首次授权:       python3 scripts/auth.py"
    echo "  5. 健康检查:       bash scripts/health_check.sh"
fi
echo ""
echo "  服务地址: http://localhost:38080/mcp/http"
echo "  WebUI:    http://localhost:38080"
echo ""
info "详细文档: https://www.feyagate.com"
echo ""

if [ "$INSTALL_OK" = false ]; then
    warn "安装可能不完整，请检查上方的错误信息"
    exit 1
fi
