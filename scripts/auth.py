#!/usr/bin/env python3
"""
Enhanced auth script with better UX and error handling
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen

# ANSI 颜色代码
COLORS = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'cyan': '\033[96m',
    'bold': '\033[1m',
}

def color(color_name, text):
    """应用颜色到文本"""
    return f"{COLORS.get(color_name, '')}{text}{COLORS['reset']}"

MCP_HOST = "127.0.0.1"
MCP_PORT = 38080


def read_port_from_config():
    """Try to read http_port from config/config.yaml"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    if config_path.exists():
        import re
        text = config_path.read_text()
        m = re.search(r'http_port:\s*(\d+)', text)
        if m:
            return int(m.group(1))
    return 38080


def mcp_call(tool, arguments=None):
    """调用 MCP API"""
    # 映射旧工具名到新工具名（兼容性）
    tool_map = {
        "auth/status": "xiaomi/auth_status",
        "auth/url": "xiaomi/auth_url",
        "auth/callback": "xiaomi/auth_callback",
    }
    tool = tool_map.get(tool, tool)

    url = f"http://{MCP_HOST}:{MCP_PORT}/mcp/http"
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }
    req = Request(url, data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        return json.loads(result["result"]["content"][0]["text"])
    except Exception as e:
        return {"error": str(e)}

def check_status():
    """检查授权状态"""
    status = mcp_call("auth/status")
    authorized = status.get("authorized", False)
    remaining = status.get("remaining_seconds", 0)

    if authorized:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        days = hours // 24
        hours = hours % 24
        time_str = f"{days}天" if days > 0 else ""
        time_str += f"{hours}小时{mins}分钟" if hours > 0 or mins > 0 else "即将过期"
        print(color('green', f"✅ 已授权，剩余时间: {time_str}"))
        return True
    else:
        print(color('red', "❌ 未授权"))
        return False

def get_auth_url():
    """获取授权链接"""
    result = mcp_call("auth/url")
    return result.get("url", "")

def extract_code_from_input(user_input):
    """从用户输入中提取 OAuth code，支持完整 URL 或纯 code"""
    user_input = user_input.strip()
    if user_input.startswith("http://") or user_input.startswith("https://"):
        parsed = urlparse(user_input)
        params = parse_qs(parsed.query)
        code_list = params.get("code", [])
        if not code_list:
            return None, "URL 中未找到 code 参数"
        return code_list[0], None
    return user_input, None


def submit_code(code):
    """提交授权码"""
    code, err = extract_code_from_input(code)
    if err:
        print(color('red', f"❌ {err}"))
        return False
    print(color('yellow', f"正在提交授权码: {code[:10]}..."))
    result = mcp_call("auth/callback", {"code": code})

    # 关键改进：API 返回 success=true 但不意味着最终成功
    # 需要重新检查状态来确认
    if "error" in result:
        print(color('red', f"❌ 授权失败: {result['error']}"))
        return False

    # 验证最终状态
    time.sleep(1)  # 等待状态更新
    if check_status():
        return True
    else:
        print(color('yellow', "⚠️  授权码已提交，但状态未更新。可能是："))
        print(color('yellow', "   1. 授权码已使用过（一次性）"))
        print(color('yellow', "   2. 授权码格式不正确"))
        print(color('yellow', "   3. 网络延迟，稍后重试"))
        return False

def interactive_flow():
    """交互式授权流程"""
    print(color('bold', "=" * 60))
    print(color('blue', "🔐 米家账号授权流程"))
    print(color('bold', "=" * 60))
    print()

    # 步骤 1: 检查当前状态
    print(color('blue', "📋 Step 1: 检查当前授权状态"))
    print("-" * 60)
    if check_status():
        print()
        print(color('yellow', "提示: 当前已授权，如需重新授权请等待 token 过期或手动删除 token 文件"))
        print(color('yellow', "Token 文件位置见 config/config.yaml 中的 token_file 配置"))
        return

    print()

    # 步骤 2: 获取授权链接
    print(color('blue', "📋 Step 2: 获取授权链接"))
    print("-" * 60)
    auth_url = get_auth_url()
    if not auth_url:
        print(color('red', "❌ 无法获取授权链接，请检查 MCP 服务是否运行"))
        return

    print(color('green', "✅ 授权链接已生成"))
    print()
    print(color('yellow', "请在浏览器中打开以下链接："))
    print()
    print(f"  {color('cyan', auth_url)}")
    print()
    print(color('yellow', "登录后浏览器会跳转到:"))
    print(f"  {color('cyan', 'https://127.0.0.1/?code=...')}")
    print()
    print(color('bold green', "✅ 页面显示'无法访问'是正常的，请复制地址栏的完整 URL"))
    print()

    # 步骤 3: 等待用户输入
    print(color('blue', "📋 Step 3: 提交授权码"))
    print("-" * 60)
    print(color('yellow', "⚠️  重要提示："))
    print(color('yellow', "   - 授权码是【一次性】的，只能使用一次"))
    print(color('yellow', "   - 请勿重复使用相同的授权码"))
    print(color('yellow', "   - 必须包含 code 和 state 两个参数"))
    print()

    code = input("请输入完整的回调 URL（包含 code 参数）: ").strip()

    if not code:
        print(color('red', "❌ 未输入授权码"))
        return

    # 步骤 4: 提交并验证
    print()
    if submit_code(code):
        print()
        print(color('bold green', "🎉 授权流程完成！"))

def main():
    parser = argparse.ArgumentParser(
        description="米家账号授权工具（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/auth.py              # 交互式授权
  python3 scripts/auth.py --status    # 查看授权状态
  python3 scripts/auth.py --code CODE  # 提交授权码（非交互）

注意：OAuth 授权码只能使用一次，请勿重复使用。
        """)
    parser.add_argument("--host", type=str, default=None,
                       help="MCP 服务地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None,
                       help="MCP 服务端口 (默认: 从 config.yaml 读取)")
    parser.add_argument("--status", action="store_true",
                       help="查看授权状态")
    parser.add_argument("--code", type=str,
                       help="直接提交授权码（非交互模式）")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="显示详细输出")

    args = parser.parse_args()

    global MCP_HOST, MCP_PORT
    if args.host:
        MCP_HOST = args.host
    if args.port:
        MCP_PORT = args.port
    else:
        MCP_PORT = read_port_from_config()

    if args.status:
        print(color('bold', "=== 授权状态检查 ==="))
        print()
        check_status()
        return

    if args.code:
        print(color('bold', "=== 提交授权码（非交互模式） ==="))
        print()
        if submit_code(args.code):
            print()
            print(color('bold green', "✅ 授权成功！"))
            check_status()
        return

    # 默认：交互式流程
    interactive_flow()

if __name__ == "__main__":
    main()
