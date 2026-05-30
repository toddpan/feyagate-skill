"""Start/stop MCP server service."""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import DEFAULT_INSTALL_DIR, MCP_DEFAULT_PORT, resolve_install_dir
from .config import get_http_port

logger = logging.getLogger(__name__)


def _install_dir():
    return resolve_install_dir()


def _read_port():
    """Return configured http_port, falling back to default."""
    try:
        return get_http_port()
    except Exception as exc:
        logger.warning("Failed to read port from config, using default: %s", exc)
        return MCP_DEFAULT_PORT


def _is_running():
    """Check if server process is alive via PID file.

    Returns:
        Tuple ``(is_running, pid_or_None)``.
    """
    pid_file = _install_dir() / "data" / "miloco-mcp-server.pid"
    if not pid_file.exists():
        return False, None
    try:
        raw = pid_file.read_text().strip()
        pid = int(raw)
    except (ValueError, OSError) as exc:
        logger.warning("Invalid PID in %s: %s", pid_file, exc)
        return False, None

    if sys.platform == "win32":
        # os.kill(pid, 0) is unreliable on Windows; query the task list instead.
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=10,
            )
            return (str(pid) in out.stdout), (pid if str(pid) in out.stdout else None)
        except Exception:
            return False, None

    try:
        os.kill(pid, 0)  # check if alive
        return True, pid
    except ProcessLookupError:
        return False, None
    except PermissionError:
        # Process exists but we lack permission to signal it
        return True, None
    except OSError:
        return False, None


def do_start(port=None):
    """Start the MCP server.

    Returns:
        True on success, False on failure.
    """
    install_dir = _install_dir()
    bin_name = "miloco-mcp-server.exe" if sys.platform == "win32" else "miloco-mcp-server"
    binary = install_dir / "bin" / bin_name
    config = install_dir / "config" / "config.yaml"
    pid_file = install_dir / "data" / "miloco-mcp-server.pid"
    log_file = install_dir / "data" / "miloco-mcp-server.log"
    lib_dir = install_dir / "lib"

    if not binary.exists():
        logger.error("MCP server binary not found. Run: feyagate setup")
        print("ERROR: MCP server binary not found. Run: feyagate setup")
        return False

    running, pid = _is_running()
    if running:
        print(f"Already running (PID {pid})")
        return True

    if not config.exists():
        logger.error("config/config.yaml not found. Run: feyagate setup")
        print("ERROR: config/config.yaml not found. Run: feyagate setup")
        return False

    try:
        (install_dir / "data").mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("Cannot create data directory %s: %s", install_dir / "data", exc)
        print(f"ERROR: Cannot create data directory: {exc}")
        return False

    # Set library path (Windows uses PATH for DLLs)
    env = os.environ.copy()
    if lib_dir.exists():
        if sys.platform == "darwin":
            env["DYLD_LIBRARY_PATH"] = str(lib_dir) + os.pathsep + env.get("DYLD_LIBRARY_PATH", "")
        elif sys.platform == "win32":
            existing = env.get("PATH", "")
            env["PATH"] = str(lib_dir) + os.pathsep + existing
        else:
            env["LD_LIBRARY_PATH"] = str(lib_dir) + os.pathsep + env.get("LD_LIBRARY_PATH", "")

    config_port = _read_port()
    if port and port != config_port:
        print(f"WARNING: --port only affects the health check URL. The binary reads its port from config.yaml (currently {config_port}).")
        print(f"  To change the listening port, edit: {config}")
    port = port or config_port

    print(f"Starting miloco-mcp-server (port {port})...")
    try:
        with open(log_file, "w") as log_fh:
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    [str(binary), "--config", str(config)],
                    cwd=str(install_dir),
                    stdout=log_fh,
                    stderr=subprocess.STDOUT,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                proc = subprocess.Popen(
                    [str(binary), "--config", str(config)],
                    cwd=str(install_dir),
                    stdout=log_fh,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                )
    except OSError as exc:
        logger.error("Failed to start server: %s", exc)
        print(f"ERROR: Failed to start server: {exc}")
        return False

    pid_file.write_text(str(proc.pid))

    # Wait for health check
    from urllib.error import URLError
    from urllib.request import urlopen

    health_url = f"http://localhost:{port}/health"
    for i in range(10):
        time.sleep(1)
        if proc.poll() is not None:
            code = proc.returncode
            logger.error("Server exited during startup with code %d", code)
            print(f"FAILED: Server exited with code {code}")
            print("Check log: feyagate log")
            pid_file.unlink(missing_ok=True)
            return False
        try:
            resp = urlopen(health_url, timeout=2)
            if resp.status == 200:
                print(f"OK (PID {proc.pid}) http://localhost:{port}/mcp/http")
                return True
        except URLError:
            pass

    print(f"Started (PID {proc.pid}), waiting for health check...")
    print(f"  Endpoint: http://localhost:{port}/mcp/http")
    return True


def do_stop():
    """Stop the MCP server. Returns True on success."""
    running, pid = _is_running()
    if not running:
        print("Server is not running")
        return True

    if pid is None:
        print("ERROR: Server is running but PID is unavailable (permission denied). Stop it manually.")
        return False

    print(f"Stopping miloco-mcp-server (PID {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError as exc:
        logger.error("Failed to send SIGTERM to PID %d: %s", pid, exc)

    for _ in range(10):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pid_file = _install_dir() / "data" / "miloco-mcp-server.pid"
            pid_file.unlink(missing_ok=True)
            print("Stopped")
            return True
        except OSError as exc:
            logger.warning("Unexpected error checking PID %d: %s", pid, exc)

   # Force kill
    logger.warning("Graceful stop timed out, sending SIGKILL to PID %d", pid)
    try:
        if sys.platform == "win32":
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, AttributeError):
        pass
    except OSError as exc:
        logger.error("Failed to SIGKILL PID %d: %s", pid, exc)
    pid_file = _install_dir() / "data" / "miloco-mcp-server.pid"
    pid_file.unlink(missing_ok=True)
    print("Force stopped")
    return True


def do_status():
    """Show server status."""
    install_dir = _install_dir()

    # Version
    version_file = install_dir / "data" / "version.json"
    try:
        if version_file.exists():
            info = json.loads(version_file.read_text(encoding="utf-8"))
            print(f"Version: {info.get('version', '?')}")
            print(f"Platform: {info.get('platform', '?')}")
        else:
            print("Version: (not installed)")
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read version file: %s", exc)
        print("Version: (error reading)")

    print(f"Install dir: {install_dir}")

    # Running?
    running, pid = _is_running()
    if running:
        print(f"Status: RUNNING (PID {pid})")
    else:
        print("Status: STOPPED")
        return

    # Health check
    port = _read_port()
    from urllib.error import URLError
    from urllib.request import urlopen
    try:
        resp = urlopen(f"http://localhost:{port}/health", timeout=3)
        print(f"Health: OK (HTTP {resp.status})")
    except URLError:
        print("Health: NOT RESPONDING")

    print(f"Endpoint: http://localhost:{port}/mcp/http")
    print(f"WebUI:    http://localhost:{port}")


def do_log(lines=30):
    """Show server log."""
    log_file = _install_dir() / "data" / "miloco-mcp-server.log"
    if not log_file.exists():
        print("No log file found")
        return

    if sys.platform == "win32":
        # Windows: read last N lines with Python (no `tail` command)
        try:
            content = log_file.read_text(encoding="utf-8", errors="replace")
            all_lines = content.splitlines()
            for line in all_lines[-lines:]:
                print(line)
        except OSError as exc:
            logger.error("Failed to read log: %s", exc)
            print(f"Error reading log: {exc}")
    else:
        result = subprocess.run(
            ["tail", "-n", str(lines), str(log_file)],
            capture_output=True, text=True,
        )
        if result.returncode != 0 and not result.stdout:
            logger.error("Failed to read log: %s", result.stderr)
            print(f"Error reading log: {result.stderr.strip()}")
        print(result.stdout)
