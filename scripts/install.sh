#!/usr/bin/env bash
# FeyaGate Skill — 一键在线安装
# curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash
set -euo pipefail

INSTALL_DIR="${FEYAGATE_INSTALL_DIR:-$HOME/.feyagate}"
VERBOSE=0
TOTAL_STEPS=4

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { printf "${GREEN}[✓]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
error() { printf "${RED}[✗]${NC} %s\n" "$*" >&2; }

CURRENT_STEP=""
CURRENT_STEP_MSG=""
step_n() {
    local n="$1"; shift
    CURRENT_STEP="$n"
    CURRENT_STEP_MSG="$*"
    printf "\n${CYAN}${BOLD}[${n}/${TOTAL_STEPS}]${NC} %s\n" "$*"
}

# Safety net
on_error() {
    local code=$?
    error "安装意外中断（退出码 ${code}）。"
    [ -n "$CURRENT_STEP" ] && error "中断位置：第 ${CURRENT_STEP}/${TOTAL_STEPS} 步 — ${CURRENT_STEP_MSG}"
    error "请检查上方日志后重试；若仍失败，请访问 https://www.feyagate.com 获取帮助。"
}
trap on_error ERR

# ── Args ──────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)     INSTALL_DIR="$2"; shift 2 ;;
        --verbose) VERBOSE=1; shift ;;
        -h|--help)
            cat <<'EOF'
FeyaGate 一键安装

  curl -fsSL https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.sh | bash

自动完成：安装命令行工具 → 下载网关程序 → 启动服务

选项:
  --dir <路径>   安装目录（默认 ~/.feyagate）
  --verbose      显示详细日志
EOF
            exit 0 ;;
        *) error "未知参数: $1（可用 --help 查看帮助）"; exit 1 ;;
    esac
done

export PATH="${HOME}/.local/bin:${PATH}"

# ── Platform ──────────────────────────────────────────────────────────────────
case "$(uname -s)" in
    Darwin|Linux) ;;
    MINGW*|MSYS*|CYGWIN*)
        error "Windows 请用 PowerShell 安装："
        error '  iwr -useb https://raw.githubusercontent.com/toddpan/feyagate-skill/main/scripts/install.ps1 | iex'
        exit 1 ;;
    *) error "暂不支持此系统: $(uname -s)"; exit 1 ;;
esac

find_python() {
    for cmd in python3 python; do
        command -v "$cmd" &>/dev/null && { echo "$cmd"; return 0; }
    done
    return 1
}

find_pip() {
    local py="$1"
    "$py" -m pip --version &>/dev/null 2>&1 && { echo "$py -m pip"; return 0; }
    command -v pip3 &>/dev/null && { echo "pip3"; return 0; }
    command -v pip &>/dev/null && { echo "pip"; return 0; }
    return 1
}

install_feyagate() {
    local pkg="feyagate-skill"
    local vflag=""
    [ "$VERBOSE" = 1 ] && vflag="-v"

    PYTHON="$(find_python)" || { error "未找到 Python"; return 1; }

    PIP="$(find_pip "$PYTHON")" || { error "未找到 pip"; return 1; }

    # 检测是否在虚拟环境内（venv/conda）
    local USER_FLAG=""
    if "$PYTHON" -c 'import sys; sys.exit(0 if (sys.prefix != sys.base_prefix or hasattr(sys,"real_prefix")) else 1)' 2>/dev/null; then
        USER_FLAG=""
    fi

    local errlog; errlog="$(mktemp)"
    # shellcheck disable=SC2086
    if $PIP install -U $USER_FLAG $vflag "$pkg" 2>"$errlog"; then
        rm -f "$errlog"
        return 0
    fi

    # PEP 668 fallback
    if grep -q "externally-managed" "$errlog" 2>/dev/null; then
        warn "检测到系统级 Python (PEP 668)，改用 --break-system-packages"
        # shellcheck disable=SC2086
        if $PIP install -U $USER_FLAG --break-system-packages $vflag "$pkg"; then
            rm -f "$errlog"
            return 0
        fi
    else
        cat "$errlog" >&2
    fi
    rm -f "$errlog"
    return 1
}

was_running() {
    local pid_file="$INSTALL_DIR/data/miloco-mcp-server.pid"
    [ -f "$pid_file" ] || return 1
    kill -0 "$(cat "$pid_file")" 2>/dev/null
}

run_feyagate() {
    if command -v feyagate &>/dev/null; then
        feyagate "$@"
    else
        local py
        py="$(find_python)" || { error "找不到 feyagate 命令"; return 127; }
        "$py" -m feyagate_skill.cli "$@"
    fi
}

print_next_steps() {
    echo ""
    printf "${BOLD}接下来请做 3 件事：${NC}\n"
    echo ""
    echo "  ① 接入 AI 助手（选一个，装完要重启 AI）："
    echo "       Cursor:       feyagate install-cursor"
    echo "       Claude Code:  feyagate install-claude"
    echo "       OpenClaw:     feyagate install-openclaw"
    echo "       Hermes:       feyagate install-hermes"
    echo "       其他助手:     feyagate --help"
    echo ""
    echo "  ② 登录小米/米家:   feyagate auth"
    echo "  ③ 确认已启动:     feyagate status"
    echo ""
    echo "  网页管理: http://localhost:38080"
    echo "  帮助文档: https://www.feyagate.com"
    echo ""
}

# ── Welcome ───────────────────────────────────────────────────────────────────
printf "\n${BOLD}${CYAN}"
cat <<'BANNER'
  _____                 ____       _
 |  ___|__ _   _  __ _ / ___| __ _| |_ ___
 | |_ / _ \ | | |/ _` | |  _ / _` | __/ _ \
 |  _|  __/ |_| | (_| | |_| | (_| | ||  __/
 |_|  \___|\__, |\__,_|\____|\__,_|\__\___|
           |___/
BANNER
printf "${NC}\n"
info "FeyaGate 智能家居网关 — 自动安装"
echo ""
echo "  即将自动完成（约 2～5 分钟，需联网）："
echo "    ① 安装 feyagate 命令行工具"
echo "    ② 下载智能家居网关程序"
echo "    ③ 启动后台服务"
echo ""

# ── [1/4] pip install ─────────────────────────────────────────────────────────
step_n 1 "安装 feyagate 命令行工具…"

if ! install_feyagate; then
    error "安装失败。请检查网络，或稍后重试。"
    exit 1
fi

command -v feyagate &>/dev/null || export PATH="${HOME}/.local/bin:${PATH}"
info "命令行工具已就绪 $(run_feyagate --version 2>/dev/null || true)"

# ── [2/4] stop old service ────────────────────────────────────────────────────
if was_running; then
    step_n 2 "更新前先停止旧服务…"
    run_feyagate stop 2>/dev/null || true
    info "旧服务已停止"
else
    step_n 2 "准备安装网关程序…"
    info "跳过（无正在运行的服务）"
fi

# ── [3/4] setup ───────────────────────────────────────────────────────────────
step_n 3 "下载并安装网关程序（约 30MB，请稍候）…"

run_feyagate setup --dir "$INSTALL_DIR" || true

if [ ! -x "$INSTALL_DIR/bin/miloco-mcp-server" ]; then
    error "网关程序下载或安装失败（未找到可执行文件）。"
    error "请检查网络后重试：用 --verbose 可查看详细日志。"
    exit 1
fi
info "网关程序已安装"

if [ "$VERBOSE" = 1 ]; then
    [ -f "$INSTALL_DIR/config/config.yaml" ] && info "配置文件已就绪"
    [ -d "$INSTALL_DIR/webui" ] && info "管理页面已就绪"
fi

# ── [4/4] start ───────────────────────────────────────────────────────────────
step_n 4 "启动智能家居网关服务…"

run_feyagate start || true
if was_running; then
    info "服务已启动"
else
    warn "自动启动未成功，请稍后手动运行: feyagate start"
    warn "排查命令: feyagate log"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
printf "${GREEN}${BOLD}  ✓ 安装完成！${NC}\n"

# 检查 PATH 中的 feyagate 版本是否一致
installed_ver="$(run_feyagate --version 2>/dev/null || true)"
if ! command -v feyagate &>/dev/null; then
    echo ""
    warn "feyagate 命令尚未加入 PATH。请将下面这行加入你的 shell 配置（~/.zshrc 或 ~/.bashrc）："
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    warn "或在当前终端先执行该命令，再运行下面的步骤。"
else
    path_ver="$(feyagate --version 2>/dev/null || true)"
    if [ -n "$installed_ver" ] && [ -n "$path_ver" ] && [ "$path_ver" != "$installed_ver" ]; then
        echo ""
        warn "检测到 PATH 中存在另一个旧版 feyagate，可能覆盖刚安装的新版本："
        warn "    PATH 中的版本: ${path_ver}（位置: $(command -v feyagate)）"
        warn "    本次安装版本: ${installed_ver}"
        warn "建议删除旧副本，或确保 ~/.local/bin 在 PATH 中靠前；"
        warn "否则下面的 feyagate 命令会运行旧版本。"
    fi
fi

print_next_steps