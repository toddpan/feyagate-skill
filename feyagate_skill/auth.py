"""Xiaomi account authorization tool."""

import json
import logging
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from . import MCP_DEFAULT_HOST, MCP_DEFAULT_PORT
from .mcp import mcp_call

logger = logging.getLogger(__name__)

COLORS = {
    'reset': '\033[0m', 'red': '\033[91m', 'green': '\033[92m',
    'yellow': '\033[93m', 'blue': '\033[94m', 'cyan': '\033[96m',
    'bold': '\033[1m',
}


def _c(name, text):
    return f"{COLORS.get(name, '')}{text}{COLORS['reset']}"


def _tool_map(tool):
    mapping = {
        "auth/status": "xiaomi/auth_status",
        "auth/url": "xiaomi/auth_url",
        "auth/callback": "xiaomi/auth_callback",
    }
    return mapping.get(tool, tool)


def _mcp(host, port, tool, arguments=None):
    return mcp_call(host, port, _tool_map(tool), arguments)


def check_status(host, port):
    status = _mcp(host, port, "auth/status")
    authorized = status.get("authorized", False)
    remaining = status.get("remaining_seconds", 0)

    if authorized:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        days = hours // 24
        hours = hours % 24
        time_str = f"{days}d " if days > 0 else ""
        time_str += f"{hours}h {mins}m" if hours > 0 or mins > 0 else "expiring soon"
        print(_c('green', f"  Authorized, remaining: {time_str}"))
        return True
    else:
        print(_c('red', "  Not authorized"))
        return False


def get_auth_url(host, port):
    result = _mcp(host, port, "auth/url")
    if "error" in result:
        logger.error("Auth URL request failed: %s", result["error"])
    return result.get("url", "")


def submit_code(host, port, code):
    code_input = code.strip()
    if code_input.startswith("http://") or code_input.startswith("https://"):
        parsed = urlparse(code_input)
        params = parse_qs(parsed.query)
        code_list = params.get("code", [])
        if not code_list:
            print(_c('red', "  No 'code' parameter found in URL"))
            return False
        code_input = code_list[0]

    print(_c('yellow', f"  Submitting auth code: {code_input[:10]}..."))
    try:
        result = _mcp(host, port, "auth/callback", {"code": code_input})
    except Exception as exc:
        logger.error("Auth callback error: %s", exc)
        print(_c('red', f"  Auth failed: {exc}"))
        return False

    if "error" in result:
        print(_c('red', f"  Auth failed: {result['error']}"))
        return False

    time.sleep(1)
    try:
        if check_status(host, port):
            return True
    except Exception as exc:
        logger.warning("Status check after auth failed: %s", exc)
    print(_c('yellow', "  Code submitted but status not updated."))
    return False


def do_auth(host=None, port=None, code=None, status_only=False):
    """Run the auth flow."""
    host = host or MCP_DEFAULT_HOST
    port = port or MCP_DEFAULT_PORT

    if status_only:
        print("=== Auth Status ===")
        check_status(host, port)
        return

    if code:
        print("=== Submit Auth Code ===")
        if submit_code(host, port, code):
            print(_c('green', "\nAuthorization successful!"))
        return

    # Interactive flow
    print("=" * 50)
    print(_c('blue', "  Xiaomi Account Authorization"))
    print("=" * 50)
    print()

    print("Step 1: Check current status")
    if check_status(host, port):
        print(_c('yellow', "\nAlready authorized. Re-auth after token expires."))
        return

    print()
    print("Step 2: Get authorization URL")
    auth_url = get_auth_url(host, port)
    if not auth_url:
        print(_c('red', "  Cannot get auth URL. Is MCP server running?"))
        return

    print(_c('green', "  Auth URL generated"))
    print(f"\n  {_c('cyan', auth_url)}")
    print(_c('yellow', "\n  Open URL in browser, then copy the full redirect URL"))
    print(_c('yellow', "  (The 'page not found' error is normal)"))
    print()

    print("Step 3: Submit auth code")
    callback_url = input("Paste the full callback URL: ").strip()
    if not callback_url:
        print(_c('red', "  No input"))
        return

    if submit_code(host, port, callback_url):
        print(_c('green', "\nAuthorization complete!"))
