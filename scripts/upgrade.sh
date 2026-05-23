#!/usr/bin/env bash
# FeyaGate Skill — 在线升级脚本 (macOS / Linux)
#
# 用法:
#   bash scripts/upgrade.sh              # 交互式升级
#   bash scripts/upgrade.sh --check      # 仅检查是否有新版本
#   bash scripts/upgrade.sh --yes        # 非交互模式，自动确认升级
#
# 流程: 检测平台 → 读取本地版本 → 获取远程最新版本 → 对比 →
#       停止服务 → 备份 → 下载 → MD5校验 → 解压安装 → 写版本 →
#       重启 → 健康检查 (失败则自动回滚)
set -euo pipefail

FOTA_URL="https://oneapi.sooncore.com/ota/fota.json"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/data"
BIN_DIR="$ROOT_DIR/bin"
LIB_DIR="$ROOT_DIR/lib"
PKG_DIR="$ROOT_DIR/packages"
BACKUP_DIR="$DATA_DIR/upgrade_backup"
VERSION_FILE="$DATA_DIR/version.json"

LOCAL_VERSION=""
CHECK_ONLY=false
AUTO_YES=false

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$*" >&2; }
step()  { printf "\n${CYAN}▶ %s${NC}\n" "$*"; }

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --check) CHECK_ONLY=true; shift ;;
        --yes)   AUTO_YES=true; shift ;;
        -h|--help)
            cat <<'EOF'
FeyaGate Skill — 在线升级

用法:
  bash scripts/upgrade.sh              交互式升级
  bash scripts/upgrade.sh --check      仅检查是否有新版本
  bash scripts/upgrade.sh --yes        非交互模式，自动确认升级
  bash scripts/upgrade.sh --help       显示帮助
EOF
            exit 0 ;;
        *) error "未知参数: $1"; exit 1 ;;
    esac
done

# ── Platform detection (reuse install.sh logic) ──────────────────────────────
detect_platform() {
    local os arch fota_type os_label arch_label

    case "$(uname -s)" in
        Darwin) os="mac";   os_label="Darwin"  ;;
        Linux)  os="linux"; os_label="Linux"   ;;
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

# ── HTTP helpers (reuse install.sh logic) ─────────────────────────────────────
fetch_text() {
    local url="$1"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url"
    elif command -v wget &>/dev/null; then
        wget -qO- "$url"
    fi
}

download() {
    local url="$1" dest="$2"
    if command -v curl &>/dev/null; then
        curl -fSL --progress-bar -o "$dest" "$url"
    elif command -v wget &>/dev/null; then
        wget -q --show-progress -O "$dest" "$url"
    fi
}

# ── JSON parsing (reuse install.sh logic) ─────────────────────────────────────
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
    echo "$json" | tr '{},' '\n' | grep -A1 "\"type\":.*\"$fota_type\"" | \
        grep "\"$field\"" | sed 's/.*"'"$field"'"\s*:\s*"\([^"]*\)".*/\1/'
}
}

# ── Semantic version comparison ───────────────────────────────────────────────
# Returns: 0 = equal, 1 = $1 > $2, 2 = $1 < $2
compare_versions() {
    local v1="$1" v2="$2"

    if [ "$v1" = "$v2" ]; then
        echo "0"
        return
    fi

    local IFS='.'
    read -ra a1 <<< "$v1"
    read -ra a2 <<< "$v2"

    local len=${#a1[@]}
    [ ${#a2[@]} -gt $len ] && len=${#a2[@]}

    for ((i = 0; i < len; i++)); do
        local n1="${a1[$i]:-0}"
        local n2="${a2[$i]:-0}"
        if [ "$n1" -gt "$n2" ] 2>/dev/null; then
            echo "1"; return
        elif [ "$n1" -lt "$n2" ] 2>/dev/null; then
            echo "2"; return
        fi
    done
    echo "0"
}

# ── Read local version ────────────────────────────────────────────────────────
get_local_version() {
    if [ -f "$VERSION_FILE" ]; then
        LOCAL_VERSION="$(parse_fota_field "$(cat "$VERSION_FILE")" "local" "version" 2>/dev/null || true)"
        if [ -z "$LOCAL_VERSION" ]; then
            # version.json is a simple object, not an array — parse directly
            LOCAL_VERSION="$(python3 -c "
import json
with open('$VERSION_FILE') as f:
    d = json.load(f)
print(d.get('version', ''))
" 2>/dev/null || true)"
        fi
    fi

    # Fallback: try to parse from package filename in packages/
    if [ -z "$LOCAL_VERSION" ] && [ -d "$PKG_DIR" ]; then
        local pkg
        pkg="$(ls -t "$PKG_DIR"/miloco-mcp-server-*.tar.gz "$PKG_DIR"/miloco-mcp-server-*.zip 2>/dev/null | head -1)"
        if [ -n "$pkg" ]; then
            LOCAL_VERSION="$(basename "$pkg" | sed -E 's/miloco-mcp-server-([0-9]+\.[0-9]+\.[0-9]+).*/\1/' | head -1)"
        fi
    fi

    # Last resort
    if [ -z "$LOCAL_VERSION" ]; then
        LOCAL_VERSION="0.0.0"
    fi
}

# ── Write version.json ───────────────────────────────────────────────────────
write_version_file() {
    local ver="$1" pkg_name="$2"
    mkdir -p "$DATA_DIR"
    cat > "$VERSION_FILE" <<EOF
{
  "version": "$ver",
  "platform": "$OS_LABEL-$ARCH_LABEL",
  "fota_type": "$FOTA_TYPE",
  "package": "$pkg_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# ── Service management ────────────────────────────────────────────────────────
is_service_running() {
    local pid_file="$DATA_DIR/miloco-mcp-server.pid"
    [ -f "$pid_file" ] || return 1
    local pid
    pid="$(cat "$pid_file")"
    kill -0 "$pid" 2>/dev/null
}

stop_service() {
    if [ -f "$ROOT_DIR/scripts/stop.sh" ]; then
        bash "$ROOT_DIR/scripts/stop.sh" 2>/dev/null || true
    else
        local pid_file="$DATA_DIR/miloco-mcp-server.pid"
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
    if [ -f "$ROOT_DIR/scripts/start.sh" ]; then
        bash "$ROOT_DIR/scripts/start.sh" 2>/dev/null
    fi
}

health_check() {
    local port=38080
    local config_file="$ROOT_DIR/config/config.yaml"
    if [ -f "$config_file" ]; then
        local cfg_port
        cfg_port="$(grep -E '^\s*http_port:' "$config_file" | head -1 | sed 's/.*: *//' | tr -d ' ')"
        [ -n "$cfg_port" ] && port="$cfg_port"
    fi

    for i in $(seq 1 5); do
        sleep 2
        local code
        code="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$port/health" 2>/dev/null || echo "000")"
        if [ "$code" = "200" ]; then
            return 0
        fi
    done
    return 1
}

# ── Backup & Rollback ─────────────────────────────────────────────────────────
backup_current() {
    rm -rf "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"

    if [ -f "$BIN_DIR/miloco-mcp-server" ]; then
        cp "$BIN_DIR/miloco-mcp-server" "$BACKUP_DIR/"
        info "备份 bin/miloco-mcp-server ✓"
    fi

    if [ -d "$LIB_DIR" ] && [ "$(ls -A "$LIB_DIR" 2>/dev/null)" ]; then
        mkdir -p "$BACKUP_DIR/lib"
        cp "$LIB_DIR"/* "$BACKUP_DIR/lib/" 2>/dev/null || true
        info "备份 lib/ ($(ls -1 "$BACKUP_DIR/lib" | wc -l | tr -d ' ') files) ✓"
    fi

    if [ -f "$VERSION_FILE" ]; then
        cp "$VERSION_FILE" "$BACKUP_DIR/version.json.bak"
    fi
}

rollback() {
    error "升级失败，正在回滚到之前的版本..."

    if [ -f "$BACKUP_DIR/miloco-mcp-server" ]; then
        cp "$BACKUP_DIR/miloco-mcp-server" "$BIN_DIR/"
        chmod +x "$BIN_DIR/miloco-mcp-server"
        info "已恢复 bin/miloco-mcp-server"
    fi

    if [ -d "$BACKUP_DIR/lib" ]; then
        rm -rf "$LIB_DIR"/*
        cp "$BACKUP_DIR/lib"/* "$LIB_DIR/" 2>/dev/null || true
        info "已恢复 lib/"
    fi

    if [ -f "$BACKUP_DIR/version.json.bak" ]; then
        cp "$BACKUP_DIR/version.json.bak" "$VERSION_FILE"
        info "已恢复 data/version.json"
    fi

    rm -rf "$BACKUP_DIR"
    error "回滚完成。请检查服务状态。"
}

cleanup_backup() {
    rm -rf "$BACKUP_DIR"
}

# ── Main ──────────────────────────────────────────────────────────────────────

printf "\n${BOLD}${CYAN}"
cat <<'BANNER'
  _____                 ____       _
 |  ___|__ _   _  __ _ / ___| __ _| |_ ___
 | |_ / _ \ | | |/ _` | |  _ / _` | __/ _ \
 |  _|  __/ |_| | (_| | |_| | (_| | ||  __/
 |_|  \___|\__, |\__,_|\____|\__,_|\__\___|
           |___/                            — Upgrade
BANNER
printf "${NC}\n"

detect_platform
info "系统: ${OS_LABEL} ${ARCH_LABEL}"
info "安装目录: $ROOT_DIR"

get_local_version
info "当前版本: v${LOCAL_VERSION}"

# ── Step 1: Fetch latest version from fota.json ──────────────────────────────
step "正在获取最新版本信息..."

FOTA_JSON="$(fetch_text "$FOTA_URL")" || {
    error "无法获取版本信息: $FOTA_URL"
    exit 1
}

REMOTE_VERSION="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "version")"
DOWNLOAD_URL="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "url")"
FILE_MD5="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "md5")"
RELEASE_NOTES="$(parse_fota_field "$FOTA_JSON" "$FOTA_TYPE" "release_notes")"

if [ -z "$REMOTE_VERSION" ] || [ -z "$DOWNLOAD_URL" ]; then
    error "未找到 $FOTA_TYPE 的发布信息"
    exit 1
fi

printf "${GREEN}[INFO]${NC}  最新版本: ${BOLD}v${REMOTE_VERSION}${NC}\n"

if [ -n "$RELEASE_NOTES" ]; then
    info "更新说明: $RELEASE_NOTES"
fi

# ── Step 2: Version comparison ───────────────────────────────────────────────
CMP="$(compare_versions "$REMOTE_VERSION" "$LOCAL_VERSION")"

if [ "$CMP" = "0" ]; then
    info "当前已是最新版本 (v${LOCAL_VERSION})，无需升级。"
    exit 0
elif [ "$CMP" = "2" ]; then
    warn "当前版本 (v${LOCAL_VERSION}) 比远程版本 (v${REMOTE_VERSION}) 更新。"
    warn "如需降级请手动处理。"
    exit 0
fi

# ── Step 3: Check-only mode ──────────────────────────────────────────────────
if [ "$CHECK_ONLY" = true ]; then
    echo ""
    printf "  当前版本: ${YELLOW}v${LOCAL_VERSION}${NC}\n"
    printf "  最新版本: ${GREEN}${BOLD}v${REMOTE_VERSION}${NC}\n"
    if [ -n "$RELEASE_NOTES" ]; then
        printf "  更新说明: ${RELEASE_NOTES}\n"
    fi
    echo ""
    info "发现新版本！运行以下命令升级:"
    echo "  bash scripts/upgrade.sh          # 交互式"
    echo "  bash scripts/upgrade.sh --yes    # 非交互"
    exit 0
fi

# ── Step 4: Confirm upgrade ──────────────────────────────────────────────────
echo ""
printf "  ${BOLD}即将升级: v${LOCAL_VERSION} → v${REMOTE_VERSION}${NC}\n"

if [ "$AUTO_YES" != true ]; then
    printf "${YELLOW}确认升级？[y/N]${NC} "
    read -r answer
    case "$answer" in
        [yY]|[yY][eE][sS]) ;;
        *) info "已取消升级。"; exit 0 ;;
    esac
fi

# ── Step 5: Stop service ─────────────────────────────────────────────────────
WAS_RUNNING=false
if is_service_running; then
    WAS_RUNNING=true
    step "停止服务..."
    stop_service
    info "服务已停止"
else
    info "服务未运行，跳过停止步骤"
fi

# ── Step 6: Backup current binary and libraries ──────────────────────────────
step "备份当前版本..."
backup_current

# ── Step 7: Download new package ─────────────────────────────────────────────
ARCHIVE_NAME="$(basename "$DOWNLOAD_URL")"
ARCHIVE_PATH="$PKG_DIR/$ARCHIVE_NAME"

step "正在下载 v${REMOTE_VERSION} (${ARCHIVE_NAME})..."

mkdir -p "$PKG_DIR"

if [ -f "$ARCHIVE_PATH" ]; then
    info "文件已存在，跳过下载"
else
    download "$DOWNLOAD_URL" "$ARCHIVE_PATH" || true
    if [ ! -f "$ARCHIVE_PATH" ] || [ ! -s "$ARCHIVE_PATH" ]; then
        rm -f "$ARCHIVE_PATH"
        error "下载失败: $DOWNLOAD_URL"
        if [ "$WAS_RUNNING" = true ]; then
            rollback
        else
            cleanup_backup
        fi
        exit 1
    fi
    info "下载完成 ($(du -h "$ARCHIVE_PATH" | awk '{print $1}'))"
fi

# ── Step 8: Verify MD5 ───────────────────────────────────────────────────────
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
            error "MD5 不匹配 (期望: $FILE_MD5, 实际: $LOCAL_MD5)"
            error "文件可能已损坏，正在删除并回滚..."
            rm -f "$ARCHIVE_PATH"
            if [ "$WAS_RUNNING" = true ]; then
                rollback
                start_service || true
            else
                rollback
            fi
            exit 1
        fi
    else
        warn "无法计算 MD5 (缺少 md5sum/md5 工具)，跳过校验"
    fi
fi

# ── Step 9: Extract and install ──────────────────────────────────────────────
step "正在解压安装..."

if [ -f "$ROOT_DIR/scripts/setup.sh" ]; then
    bash "$ROOT_DIR/scripts/setup.sh" --package "$ARCHIVE_PATH" || {
        error "setup.sh 解压失败"
        if [ "$WAS_RUNNING" = true ]; then
            rollback
            start_service || true
        else
            rollback
        fi
        exit 1
    }
else
    # Inline fallback extraction
    TMP_DIR="$(mktemp -d)"
    case "$ARCHIVE_PATH" in
        *.tar.gz|*.tgz) tar xzf "$ARCHIVE_PATH" -C "$TMP_DIR" ;;
        *.zip)          unzip -qo "$ARCHIVE_PATH" -d "$TMP_DIR" ;;
    esac

    INNER="$(find "$TMP_DIR" -maxdepth 1 -mindepth 1 -type d | head -1)"
    [ -z "$INNER" ] && INNER="$TMP_DIR"

    for bin_path in "$INNER/miloco-mcp-server" "$INNER/bin/miloco-mcp-server"; do
        if [ -f "$bin_path" ]; then
            cp "$bin_path" "$BIN_DIR/"
            chmod +x "$BIN_DIR/miloco-mcp-server"
            break
        fi
    done

    if [ -d "$INNER/lib" ]; then
        cp "$INNER/lib"/* "$LIB_DIR/" 2>/dev/null || true
    fi

    [ ! -e "$BIN_DIR/lib" ] && ln -sf ../lib "$BIN_DIR/lib"

    if [ -d "$INNER/webui" ]; then
        rm -rf "$ROOT_DIR/webui"
        cp -r "$INNER/webui" "$ROOT_DIR/webui"
    fi

    rm -rf "$TMP_DIR"
fi

# ── Step 10: Write version.json ──────────────────────────────────────────────
write_version_file "$REMOTE_VERSION" "$ARCHIVE_NAME"
info "版本信息已写入 data/version.json"

# ── Step 11: Restart service (if it was running) ─────────────────────────────
if [ "$WAS_RUNNING" = true ]; then
    step "重启服务..."
    start_service || {
        error "服务启动失败，正在回滚..."
        rollback
        start_service || error "回滚后服务仍无法启动，请手动检查"
        exit 1
    }

    step "健康检查..."
    if health_check; then
        info "健康检查通过 ✓"
    else
        warn "健康检查未通过，服务可能仍在初始化中"
        warn "请手动检查: bash scripts/health_check.sh"
    fi
fi

# ── Step 12: Cleanup ─────────────────────────────────────────────────────────
cleanup_backup

echo ""
printf "${GREEN}${BOLD}"
cat <<'DONE'
╔══════════════════════════════════════════════╗
║     FeyaGate Skill 升级完成！               ║
╚══════════════════════════════════════════════╝
DONE
printf "${NC}\n"

info "版本: v${LOCAL_VERSION} → v${REMOTE_VERSION}"
if [ "$WAS_RUNNING" = true ]; then
    info "服务已重启并运行中"
fi
echo ""
