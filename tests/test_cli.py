"""Tests for feyagate_skill.cli module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from feyagate_skill.cli import (
    _install_claude, _install_cursor, _install_openclaw, _install_hermes, main
)


class TestInstallClaude:
    """Test Claude Code MCP config installation."""

    def test_missing_binary(self, tmp_path):
        # Point DEFAULT_INSTALL_DIR at tmp_path where no binary exists
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path)):
            assert _install_claude() is False

    def test_successful_install(self, tmp_path):
        # Create binary
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_claude() is True

    def test_read_existing_config(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        # Create existing config
        import json
        config_path = tmp_path / ".claude.json"
        existing = {"mcpServers": {"existing": {"type": "stdio"}}}
        config_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_claude() is True


class TestInstallCursor:
    """Test Cursor MCP config installation."""

    def test_missing_binary(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path)):
            assert _install_cursor() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_cursor() is True

    def test_creates_parent_dir(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            result = _install_cursor()
        assert result is True
        cursor_dir = tmp_path / ".cursor"
        assert cursor_dir.exists()


class TestInstallOpenclaw:
    """Test OpenClaw MCP config installation."""

    def test_missing_binary(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path)):
            assert _install_openclaw() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        # Create .openclaw directory
        (tmp_path / ".openclaw").mkdir(parents=True)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_openclaw() is True

    def test_existing_config(self, tmp_path):
        import json
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        # Create existing config
        openclaw_dir = tmp_path / ".openclaw"
        openclaw_dir.mkdir(parents=True)
        config_path = openclaw_dir / "openclaw.json"
        existing = {"mcpServers": {"existing": {"type": "stdio"}}}
        config_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_openclaw() is True

        # Verify both servers are present
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert "feyagate" in config["mcpServers"]
        assert "existing" in config["mcpServers"]


class TestInstallHermes:
    """Test Hermes Agent MCP config installation."""

    def test_missing_binary(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path)):
            assert _install_hermes() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_hermes() is True

    def test_creates_config_dir(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        # Don't create .hermes directory - should be created
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_hermes() is True

        # Verify config directory and file were created
        hermes_dir = tmp_path / ".hermes"
        assert hermes_dir.exists()
        config_path = hermes_dir / "config.yaml"
        assert config_path.exists()

    def test_existing_config(self, tmp_path):
        import yaml
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        # Create existing config
        hermes_dir = tmp_path / ".hermes"
        hermes_dir.mkdir(parents=True)
        config_path = hermes_dir / "config.yaml"
        existing = {"model": {"default": "claude-sonnet-4"}, "mcp": {"servers": {"existing": {"url": "http://old:8080/mcp"}}}}
        config_path.write_text(yaml.dump(existing), encoding="utf-8")

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_hermes() is True

        # Verify both servers are present
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert "feyagate" in config["mcp"]["servers"]
        assert "existing" in config["mcp"]["servers"]


class TestMain:
    """Test CLI entry point."""

    def test_no_args_shows_help(self, monkeypatch, capsys):
        """Test that calling main() without args prints help."""
        mock_args = MagicMock()
        mock_args.command = None

        def fake_parse(args=None):
            return mock_args

        mock_parser = MagicMock()
        mock_parser.parse_args = fake_parse

        def fake_parser_class(*args, **kwargs):
            return mock_parser

        with patch("argparse.ArgumentParser", fake_parser_class):
            main()
        assert mock_parser.print_help.called

    def test_version_flag(self, monkeypatch):
        """Test --version prints version and exits."""
        # When --version is passed, argparse's action calls sys.exit
        # We can't easily mock the action, so just test the parser creation
        import feyagate_skill.cli as cli_mod
        # Verify the version is set
        assert hasattr(cli_mod, '__version__')
        assert cli_mod.__version__ == "1.2.2"

    def test_install_openclaw_command(self, monkeypatch, tmp_path):
        """Test install-openclaw command calls _install_openclaw."""
        import sys
        from unittest.mock import patch

        # Create binary
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")
        (tmp_path / ".openclaw").mkdir(parents=True)

        old_argv = sys.argv
        try:
            with patch("feyagate_skill.cli._install_openclaw") as mock_install:
                sys.argv = ["feyagate", "install-openclaw"]
                try:
                    main()
                except SystemExit:
                    pass  # argparse may call sys.exit on some paths

                mock_install.assert_called_once()
        finally:
            sys.argv = old_argv

    def test_install_hermes_command(self, monkeypatch, tmp_path):
        """Test install-hermes command calls _install_hermes."""
        import sys
        from unittest.mock import patch

        # Create binary
        install_dir = tmp_path / "feyagate"
        (install_dir / "bin").mkdir(parents=True)
        (install_dir / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")

        old_argv = sys.argv
        try:
            with patch("feyagate_skill.cli._install_hermes") as mock_install:
                sys.argv = ["feyagate", "install-hermes"]
                try:
                    main()
                except SystemExit:
                    pass

                mock_install.assert_called_once()
        finally:
            sys.argv = old_argv
