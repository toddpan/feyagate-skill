"""FeyaGate Skill CLI - Main entry point."""

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, DEFAULT_INSTALL_DIR, MCP_DEFAULT_PORT


def _install_claude():
    """Configure Claude Code MCP settings."""
    import json as _json
    claude_config = Path.home() / ".claude.json"
    install_dir = Path(os.path.expanduser(DEFAULT_INSTALL_DIR))
    binary = install_dir / "bin" / "miloco-mcp-server"

    if not binary.exists():
        print("ERROR: MCP server not installed. Run: feyagate setup")
        return False

    try:
        config = {}
        if claude_config.exists():
            try:
                config = _json.loads(claude_config.read_text(encoding="utf-8"))
            except (OSError, _json.JSONDecodeError) as exc:
                print(f"Warning: Cannot read {claude_config}: {exc}")

        mcp_servers = config.setdefault("mcpServers", {})
        mcp_servers["feyagate"] = {
            "type": "streamable-http",
            "url": "http://localhost:38080/mcp/http",
        }

        claude_config.write_text(
            _json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Added 'feyagate' MCP server to {claude_config}")
        print(f"  URL: http://localhost:38080/mcp/http")
        print()
        print("Make sure to start the server: feyagate start")
        return True
    except OSError as exc:
        print(f"ERROR: Failed to write config: {exc}")
        return False


def _install_cursor():
    """Configure Cursor MCP settings."""
    import json as _json
    cursor_config = Path.home() / ".cursor" / "mcp.json"
    install_dir = Path(os.path.expanduser(DEFAULT_INSTALL_DIR))
    binary = install_dir / "bin" / "miloco-mcp-server"

    if not binary.exists():
        print("ERROR: MCP server not installed. Run: feyagate setup")
        return False

    try:
        cursor_config.parent.mkdir(parents=True, exist_ok=True)

        config = {}
        if cursor_config.exists():
            try:
                config = _json.loads(cursor_config.read_text(encoding="utf-8"))
            except (OSError, _json.JSONDecodeError) as exc:
                print(f"Warning: Cannot read {cursor_config}: {exc}")

        mcp_servers = config.setdefault("mcpServers", {})
        mcp_servers["feyagate"] = {
            "type": "streamable-http",
            "url": "http://localhost:38080/mcp/http",
        }

        cursor_config.write_text(
            _json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Added 'feyagate' MCP server to {cursor_config}")
        print(f"  URL: http://localhost:38080/mcp/http")
        print()
        print("Make sure to start the server: feyagate start")
        return True
    except OSError as exc:
        print(f"ERROR: Failed to write config: {exc}")
        return False


def _install_openclaw():
    """Configure OpenClaw MCP settings."""
    import json as _json

    openclaw_config = Path.home() / ".openclaw" / "openclaw.json"
    install_dir = Path(os.path.expanduser(DEFAULT_INSTALL_DIR))
    binary = install_dir / "bin" / "miloco-mcp-server"

    if not binary.exists():
        print("ERROR: MCP server not installed. Run: feyagate setup")
        return False

    try:
        config = {}
        if openclaw_config.exists():
            try:
                config = _json.loads(openclaw_config.read_text(encoding="utf-8"))
            except (OSError, _json.JSONDecodeError) as exc:
                print(f"Warning: Cannot read {openclaw_config}: {exc}")

        if not isinstance(config, dict):
            config = {}

        mcp_servers = config.setdefault("mcpServers", {})
        mcp_servers["feyagate"] = {
            "type": "streamable-http",
            "url": "http://localhost:38080/mcp/http",
        }

        openclaw_config.write_text(
            _json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Added 'feyagate' MCP server to {openclaw_config}")
        print(f"  URL: http://localhost:38080/mcp/http")
        print()
        print("Make sure to start the server: feyagate start")
        return True
    except OSError as exc:
        print(f"ERROR: Failed to write config: {exc}")
        return False


def _install_hermes():
    """Configure Hermes Agent MCP settings."""
    import yaml

    hermes_config = Path.home() / ".hermes" / "config.yaml"
    install_dir = Path(os.path.expanduser(DEFAULT_INSTALL_DIR))
    binary = install_dir / "bin" / "miloco-mcp-server"

    if not binary.exists():
        print("ERROR: MCP server not installed. Run: feyagate setup")
        return False

    try:
        config = {}
        if hermes_config.exists():
            try:
                content = hermes_config.read_text(encoding="utf-8")
                config = yaml.safe_load(content) or {}
            except (OSError, Exception) as exc:
                print(f"Warning: Cannot read {hermes_config}: {exc}")

        if not isinstance(config, dict):
            config = {}

        # Hermes MCP servers config: mcp.servers.<name>
        mcp_config = config.setdefault("mcp", {})
        servers = mcp_config.setdefault("servers", {})
        servers["feyagate"] = {
            "url": "http://localhost:38080/mcp/http",
            "transport": "http",
        }

        hermes_config.parent.mkdir(parents=True, exist_ok=True)
        with open(hermes_config, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"Added 'feyagate' MCP server to {hermes_config}")
        print(f"  URL: http://localhost:38080/mcp/http")
        print()
        print("Make sure to start the server: feyagate start")
        return True
    except OSError as exc:
        print(f"ERROR: Failed to write config: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(
        prog="feyagate",
        description="FeyaGate Skill - MCP Smart Home Gateway for AI Agents",
    )
    parser.add_argument("--version", action="version", version=f"feyagate-skill {__version__}")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # setup
    p_setup = sub.add_parser("setup", help="Download and install MCP server binary")
    p_setup.add_argument("--dir", default=None, help="Install directory (default: ~/.feyagate)")

    # start
    p_start = sub.add_parser("start", help="Start MCP server")
    p_start.add_argument("--port", type=int, default=None, help="HTTP port (default: from config)")

    # stop
    sub.add_parser("stop", help="Stop MCP server")

    # restart
    p_restart = sub.add_parser("restart", help="Restart MCP server")
    p_restart.add_argument("--port", type=int, default=None, help="HTTP port")

    # status
    sub.add_parser("status", help="Show server status")

    # log
    p_log = sub.add_parser("log", help="Show server log")
    p_log.add_argument("-n", "--lines", type=int, default=30, help="Number of lines")

    # auth
    p_auth = sub.add_parser("auth", help="Xiaomi account authorization")
    p_auth.add_argument("--host", default=None, help="MCP host")
    p_auth.add_argument("--port", type=int, default=None, help="MCP port")
    p_auth.add_argument("--status", action="store_true", help="Check auth status only")
    p_auth.add_argument("--code", default=None, help="Submit auth code directly")

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Camera snapshot capture")
    p_snap.add_argument("--host", default=None)
    p_snap.add_argument("--port", type=int, default=None)
    p_snap.add_argument("--list", action="store_true", help="List cameras")
    p_snap.add_argument("--camera-id", default=None, help="Camera DID")
    p_snap.add_argument("--connect", action="store_true", help="Connect before snapshot")
    p_snap.add_argument("--channel", type=int, default=0)
    p_snap.add_argument("--count", type=int, default=1)
    p_snap.add_argument("--output-dir", default=None)

    # scheduled
    p_sched = sub.add_parser("scheduled", help="Scheduled camera analysis")
    p_sched.add_argument("--host", default=None)
    p_sched.add_argument("--port", type=int, default=None)
    p_sched.add_argument("--camera-id", action="append", required=True, help="Camera DID (repeatable)")
    p_sched.add_argument("--channel", type=int, default=0)
    p_sched.add_argument("--interval", type=int, default=300, help="Seconds between captures")
    p_sched.add_argument("--output-dir", default=None)
    p_sched.add_argument("--prompt", default="", help="AI analysis prompt")
    p_sched.add_argument("--auto-connect", action="store_true")
    p_sched.add_argument("--max-runs", type=int, default=0, help="0 = unlimited")
    p_sched.add_argument("--one-shot", action="store_true")

    # install-claude
    sub.add_parser("install-claude", help="Configure Claude Code MCP settings")

    # install-cursor
    sub.add_parser("install-cursor", help="Configure Cursor MCP settings")

    # install-openclaw
    sub.add_parser("install-openclaw", help="Configure OpenClaw MCP settings")

    # install-hermes
    sub.add_parser("install-hermes", help="Configure Hermes Agent MCP settings")

    # upgrade
    sub.add_parser("upgrade", help="Upgrade MCP server to latest version")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "setup":
        from .installer import do_setup
        do_setup(args.dir)

    elif args.command == "start":
        from .service import do_start
        do_start(args.port)

    elif args.command == "stop":
        from .service import do_stop
        do_stop()

    elif args.command == "restart":
        from .service import do_stop, do_start
        do_stop()
        do_start(args.port)

    elif args.command == "status":
        from .service import do_status
        do_status()

    elif args.command == "log":
        from .service import do_log
        do_log(args.lines)

    elif args.command == "auth":
        from .auth import do_auth
        do_auth(host=args.host, port=args.port, code=args.code, status_only=args.status)

    elif args.command == "snapshot":
        from .snapshot import do_snapshot
        do_snapshot(
            host=args.host, port=args.port, camera_id=args.camera_id,
            connect=args.connect, channel=args.channel, count=args.count,
            output_dir=args.output_dir, list_cameras=args.list,
        )

    elif args.command == "scheduled":
        from .scheduled import do_scheduled
        do_scheduled(
            host=args.host, port=args.port, camera_ids=args.camera_id,
            channel=args.channel, interval=args.interval,
            output_dir=args.output_dir, prompt=args.prompt,
            auto_connect=args.auto_connect, max_runs=args.max_runs,
            one_shot=args.one_shot,
        )

    elif args.command == "install-claude":
        _install_claude()

    elif args.command == "install-cursor":
        _install_cursor()

    elif args.command == "install-openclaw":
        _install_openclaw()

    elif args.command == "install-hermes":
        _install_hermes()

    elif args.command == "upgrade":
        from .installer import do_setup
        do_setup()


if __name__ == "__main__":
    main()
