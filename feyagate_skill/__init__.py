"""FeyaGate Skill - MCP Smart Home Gateway for AI Agents."""

import os
from pathlib import Path

__version__ = "1.2.33"
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
# Temporary release switch: some GitHub assets do not publish a matching
# .sha256 file, so checksum verification is disabled for this version.
VERIFY_MILOCO_CHECKSUM = False
# Manually maintained archive filename templates for each published
# miloco-mcp-server build. Usually only SERVER_BINARY_VERSION needs to change;
# touch this map only if the upstream filename pattern changes again.
MILOCO_DOWNLOAD_FILES = {
    ("Linux", "x86_64"): "miloco-mcp-server-linux-x64-v{version}.tar.gz",
    ("Linux", "amd64"): "miloco-mcp-server-linux-x64-v{version}.tar.gz",
    ("Linux", "aarch64"): "miloco-mcp-server-linux-arm64-v{version}.tar.gz",
    ("Linux", "arm64"): "miloco-mcp-server-linux-arm64-v{version}.tar.gz",
    ("Darwin", "x86_64"): "miloco-mcp-server-mac-x64-v{version}.zip",
    ("Darwin", "arm64"): "miloco-mcp-server-mac-arm64-v{version}.zip",
    ("Windows", "AMD64"): "miloco-mcp-server-win-x64-v{version}.zip",
    ("Windows", "ARM64"): "miloco-mcp-server-win-x64-v{version}.zip",
}
MILOCO_DOWNLOAD_URLS = {
    key: f"{SERVER_RELEASE_BASE}/v{SERVER_BINARY_VERSION}/{template.format(version=SERVER_BINARY_VERSION)}"
    for key, template in MILOCO_DOWNLOAD_FILES.items()
}
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
    "VERIFY_MILOCO_CHECKSUM",
    "MILOCO_DOWNLOAD_FILES",
    "MILOCO_DOWNLOAD_URLS",
    "MCP_DEFAULT_PORT",
    "MCP_DEFAULT_HOST",
    "resolve_install_dir",
    "save_install_dir",
]
