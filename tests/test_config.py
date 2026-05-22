"""Tests for feyagate_skill.config module."""

import pytest

from feyagate_skill.config import load_config, get_http_port, get_ws_port


class TestLoadConfig:
    """Test the YAML config loader."""

    def test_load_valid_config(self, tmp_path):
        config_dir = tmp_path / "feyagate" / "config"
        config_dir.mkdir(parents=True)
        config = config_dir / "config.yaml"
        config.write_text(
            "server:\n  http_port: 38080\n  ws_port: 8765\n  bind_address: 0.0.0.0\nauth:\n  cloud_server: cn\n",
            encoding="utf-8",
        )
        result = load_config(config)
        assert isinstance(result, dict)
        assert result["server"]["http_port"] == 38080
        assert result["auth"]["cloud_server"] == "cn"

    def test_load_missing_file(self):
        result = load_config("/nonexistent/path/config.yaml")
        assert result == {}

    def test_load_invalid_yaml(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("{invalid yaml: [", encoding="utf-8")
        result = load_config(config)
        assert result == {}

    def test_load_empty_file(self, tmp_path):
        config = tmp_path / "empty.yaml"
        config.write_text("", encoding="utf-8")
        result = load_config(config)
        assert result == {}

    def test_load_non_dict_yaml(self, tmp_path):
        config = tmp_path / "list.yaml"
        config.write_text("- item1\n- item2\n", encoding="utf-8")
        result = load_config(config)
        assert result == {}


class TestGetHttpPort:
    """Test the http_port accessor."""

    def test_returns_configured_port(self, tmp_path):
        config_dir = tmp_path / "feyagate" / "config"
        config_dir.mkdir(parents=True)
        config = config_dir / "config.yaml"
        config.write_text("server:\n  http_port: 9999\n", encoding="utf-8")
        assert get_http_port(config) == 9999

    def test_returns_default_when_missing(self, tmp_path):
        config = tmp_path / "minimal.yaml"
        config.write_text("server:\n  ws_port: 8765\n", encoding="utf-8")
        assert get_http_port(config) == 38080

    def test_returns_default_when_missing_server_key(self):
        assert get_http_port("/nonexistent/config.yaml") == 38080


class TestGetWsPort:
    """Test the ws_port accessor."""

    def test_returns_configured_port(self, tmp_path):
        config_dir = tmp_path / "feyagate" / "config"
        config_dir.mkdir(parents=True)
        config = config_dir / "config.yaml"
        config.write_text("server:\n  ws_port: 9999\n", encoding="utf-8")
        assert get_ws_port(config) == 9999

    def test_returns_default_when_missing(self, tmp_path):
        config = tmp_path / "minimal.yaml"
        config.write_text("server:\n  http_port: 38080\n", encoding="utf-8")
        assert get_ws_port(config) == 8765
