"""FeyaGate Skill - MCP Smart Home Gateway for AI Agents."""

__version__ = "1.2.24"
__author__ = "panzuji"

DEFAULT_INSTALL_DIR = "~/.feyagate"
FOTA_URL = "https://oneapi.sooncore.com/ota/fota.json"
# Prebuilt miloco-mcp-server binaries are published as GitHub Releases.
# The release tag matches this package version: 1.2.16 -> v1.2.16.
SERVER_RELEASE_REPO = "toddpan/miloco-mcp-server-releases"
SERVER_RELEASE_BASE = (
    "https://github.com/toddpan/miloco-mcp-server-releases/releases/download"
)
MCP_DEFAULT_PORT = 38080
MCP_DEFAULT_HOST = "127.0.0.1"

__all__ = [
    "__version__",
    "__author__",
    "DEFAULT_INSTALL_DIR",
    "FOTA_URL",
    "SERVER_RELEASE_REPO",
    "SERVER_RELEASE_BASE",
    "MCP_DEFAULT_PORT",
    "MCP_DEFAULT_HOST",
]
