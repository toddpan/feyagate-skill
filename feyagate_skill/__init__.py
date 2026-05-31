"""FeyaGate Skill - MCP Smart Home Gateway for AI Agents."""

import os
from pathlib import Path

__version__ = "1.2.31"
__author__ = "panzuji"

DEFAULT_INSTALL_DIR = "~/.feyagate"
FOTA_URL = "https://oneapi.sooncore.com/ota/fota.json"
# Prebuilt miloco-mcp-server binaries are published as GitHub Releases.
# The release tag matches this package version: 1.2.16 -> v1.2.16.
SERVER_RELEASE_REPO = "toddpan/miloco-mcp-server-releases"
SERVER_RELEASE_BASE = (
    "https://github.com/toddpan/miloco-mcp-server-releases/releases/download"
)
# Version of the prebuilt server binary to download. Decoupled from the Python
# package __version__: bump this only when a new binary release exists for ALL
# platforms (mac-x64, mac-arm64, linux-x64, win-x64). Pinned here (not buried in
# installer.py) so it is the single obvious place to change on a binary release.
SERVER_BINARY_VERSION = "1.2.17"
MCP_DEFAULT_PORT = 38080
MCP_DEFAULT_HOST = "127.0.0.1"

# Fixed pointer file recording where `setup --dir` installed, so that later
# commands (start/stop/status/...) find the same directory regardless of cwd.
_POINTER_FILE = Path(os.path.expanduser("~/.config/feyagate/install_dir"))


def resolve_install_dir(explicit=None):
    """Return the active install directory.

    Precedence:
      1. explicit argument (e.g. `setup --dir X`)
      2. FEYAGATE_INSTALL_DIR environment variable
      3. pointer file written by a previous `setup`
      4. default ~/.feyagate

    The result is an absolute Path with ~ expanded.
    """
    if explicit:
        return Path(os.path.expanduser(explicit)).resolve()
    env = os.environ.get("FEYAGATE_INSTALL_DIR")
    if env:
        return Path(os.path.expanduser(env)).resolve()
    try:
        if _POINTER_FILE.is_file():
            saved = _POINTER_FILE.read_text(encoding="utf-8").strip()
            if saved:
                return Path(os.path.expanduser(saved)).resolve()
    except OSError:
        pass
    return Path(os.path.expanduser(DEFAULT_INSTALL_DIR)).resolve()


def save_install_dir(install_dir):
    """Persist the chosen install directory to the pointer file."""
    try:
        _POINTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        _POINTER_FILE.write_text(str(Path(install_dir).resolve()) + "\n", encoding="utf-8")
    except OSError:
        pass


__all__ = [
    "__version__",
    "__author__",
    "DEFAULT_INSTALL_DIR",
    "FOTA_URL",
    "SERVER_RELEASE_REPO",
    "SERVER_RELEASE_BASE",
    "SERVER_BINARY_VERSION",
    "MCP_DEFAULT_PORT",
    "MCP_DEFAULT_HOST",
    "resolve_install_dir",
    "save_install_dir",
]
