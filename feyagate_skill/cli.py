"""FeyaGate Skill CLI - Main entry point."""

import argparse
import os
import platform as _platform
import sys
from pathlib import Path

from . import __version__, DEFAULT_INSTALL_DIR, MCP_DEFAULT_PORT


def _install_skill(skills_dir, agent_name):
    """Create skill symlink for an AI agent.

    Args:
        skills_dir: Path to the agent's skills directory.
        agent_name: Display name for the agent (used in output messages).

    Returns:
        True on success, False on failure.
    """
    install_dir = Path(os.path.expanduser(DEFAULT_INSTALL_DIR))
    if not install_dir.exists():
        print("ERROR: FeyaGate not installed. Run: feyagate setup")
        return False

    skills_dir = Path(skills_dir)
    link = skills_dir / "feyagate"

    try:
        skills_dir.mkdir(parents=True, exist_ok=True)

        if link.is_symlink() or link.exists():
            link.unlink()

        link.symlink_to(install_dir)
        print(f"Skill installed: {link} -> {install_dir}")
        print()
        print(f"Restart {agent_name} to load the skill.")
        return True
    except OSError as exc:
        print(f"ERROR: Failed to create symlink: {exc}")
        return False


def _install_claude():
    return _install_skill(Path.home() / ".claude" / "skills", "Claude Code")


def _install_cursor():
    return _install_skill(Path.home() / ".cursor" / "skills", "Cursor")


def _install_openclaw():
    return _install_skill(Path.home() / ".openclaw" / "skills", "OpenClaw")


def _install_hermes():
    return _install_skill(Path.home() / ".hermes" / "skills", "Hermes Agent")


def _install_windsurf():
    return _install_skill(Path.home() / ".codeium" / "windsurf" / "skills", "Windsurf")


def _install_copilot():
    system = _platform.system()
    if system == "Darwin":
        vscode_dir = Path.home() / "Library" / "Application Support" / "Code"
    elif system == "Windows":
        vscode_dir = Path.home() / "AppData" / "Roaming" / "Code"
    else:
        vscode_dir = Path.home() / ".config" / "Code"
    return _install_skill(vscode_dir / "skills", "VS Code")


def _install_codex():
    return _install_skill(Path.home() / ".codex" / "skills", "Codex CLI")


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
    sub.add_parser("install-claude", help="Install FeyaGate skill commands for Claude Code")

    # install-cursor
    sub.add_parser("install-cursor", help="Install FeyaGate skill commands for Cursor")

    # install-openclaw
    sub.add_parser("install-openclaw", help="Install FeyaGate skill commands for OpenClaw")

    # install-hermes
    sub.add_parser("install-hermes", help="Install FeyaGate skill commands for Hermes Agent")

    # install-windsurf
    sub.add_parser("install-windsurf", help="Install FeyaGate skill commands for Windsurf")

    # install-copilot
    sub.add_parser("install-copilot", help="Install FeyaGate skill commands for GitHub Copilot (VS Code)")

    # install-codex
    sub.add_parser("install-codex", help="Install FeyaGate skill commands for OpenAI Codex CLI")

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

    elif args.command == "install-windsurf":
        _install_windsurf()

    elif args.command == "install-copilot":
        _install_copilot()

    elif args.command == "install-codex":
        _install_codex()

    elif args.command == "upgrade":
        from .installer import do_setup
        do_setup()


if __name__ == "__main__":
    main()
