"""Shared YAML configuration loader with error handling."""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_config(path: str | Path | None = None) -> dict:
    """Load and parse config.yaml, returning a dict (never raises).

    Args:
        path: Path to config.yaml. Defaults to
              ``~/.feyagate/config/config.yaml``.

    Returns:
        Configuration dict. Returns ``{}`` on any error.
    """
    if path is None:
        from . import DEFAULT_INSTALL_DIR
        path = Path(DEFAULT_INSTALL_DIR) / "config" / "config.yaml"

    path = Path(path)
    try:
        if not path.exists():
            logger.warning("Config file not found: %s", path)
            return {}
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError as exc:
        logger.error("YAML parse error in %s: %s", path, exc)
        return {}
    except OSError as exc:
        logger.error("Cannot read config %s: %s", path, exc)
        return {}


def get_http_port(config_path: str | Path | None = None) -> int:
    """Return the configured http_port (default 38080)."""
    cfg = load_config(config_path)
    return int(cfg.get("server", {}).get("http_port", 38080))


def get_ws_port(config_path: str | Path | None = None) -> int:
    """Return the configured ws_port (default 8765)."""
    cfg = load_config(config_path)
    return int(cfg.get("server", {}).get("ws_port", 8765))
