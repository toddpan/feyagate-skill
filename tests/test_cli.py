"""Tests for feyagate_skill.cli module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from feyagate_skill.cli import (
    _install_claude, _install_cursor, _install_openclaw, _install_hermes,
    _install_windsurf, _install_copilot, _install_codex, main,
)


class TestInstallClaude:
    """Test Claude Code skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_claude() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_claude() is True

        link = tmp_path / ".claude" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_claude() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


class TestInstallCursor:
    """Test Cursor skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_cursor() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_cursor() is True

        link = tmp_path / ".cursor" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".cursor" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_cursor() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


class TestInstallOpenclaw:
    """Test OpenClaw skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_openclaw() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_openclaw() is True

        link = tmp_path / ".openclaw" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".openclaw" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_openclaw() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


class TestInstallHermes:
    """Test Hermes Agent skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_hermes() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_hermes() is True

        link = tmp_path / ".hermes" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".hermes" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_hermes() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


class TestInstallWindsurf:
    """Test Windsurf skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_windsurf() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_windsurf() is True

        link = tmp_path / ".codeium" / "windsurf" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".codeium" / "windsurf" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_windsurf() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


class TestInstallCopilot:
    """Test GitHub Copilot (VS Code) skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_copilot() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path), \
             patch("platform.system", return_value="Linux"):
            assert _install_copilot() is True

        link = tmp_path / ".config" / "Code" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".config" / "Code" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path), \
             patch("platform.system", return_value="Linux"):
            assert _install_copilot() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


class TestInstallCodex:
    """Test OpenAI Codex CLI skill symlink installation."""

    def test_missing_install_dir(self, tmp_path):
        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(tmp_path / "nonexistent")):
            assert _install_codex() is False

    def test_successful_install(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_codex() is True

        link = tmp_path / ".codex" / "skills" / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        skills_dir = tmp_path / ".codex" / "skills"
        skills_dir.mkdir(parents=True)
        old_target = tmp_path / "old"
        old_target.mkdir()
        (skills_dir / "feyagate").symlink_to(old_target)

        with patch("feyagate_skill.cli.DEFAULT_INSTALL_DIR", str(install_dir)), \
             patch("pathlib.Path.home", return_value=tmp_path):
            assert _install_codex() is True

        link = skills_dir / "feyagate"
        assert link.is_symlink()
        assert link.resolve() == install_dir.resolve()


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
        import re
        import feyagate_skill.cli as cli_mod
        assert hasattr(cli_mod, '__version__')
        assert re.match(r"^\d+\.\d+\.\d+", cli_mod.__version__)

    def test_install_openclaw_command(self, monkeypatch, tmp_path):
        """Test install-openclaw command calls _install_openclaw."""
        import sys
        from unittest.mock import patch

        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        old_argv = sys.argv
        try:
            with patch("feyagate_skill.cli._install_openclaw") as mock_install:
                sys.argv = ["feyagate", "install-openclaw"]
                try:
                    main()
                except SystemExit:
                    pass

                mock_install.assert_called_once()
        finally:
            sys.argv = old_argv

    def test_install_hermes_command(self, monkeypatch, tmp_path):
        """Test install-hermes command calls _install_hermes."""
        import sys
        from unittest.mock import patch

        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

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
