"""Tests for feyagate_skill.service module."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from feyagate_skill.service import (
    _is_running,
    _read_port,
    do_start,
    do_stop,
    do_status,
    do_log,
)


class TestIsRunning:
    """Test PID file process detection."""

    def _run_is_running(self, tmp_path):
        """Helper: mock _install_dir to point at tmp_path, then call _is_running."""
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            return _is_running()

    def test_not_running_no_pid_file(self, tmp_path):
        (tmp_path / "data").mkdir()
        result, pid = self._run_is_running(tmp_path)
        assert result is False
        assert pid is None

    def test_not_running_invalid_pid(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        pid_file = data_dir / "miloco-mcp-server.pid"
        pid_file.write_text("not_a_number", encoding="utf-8")
        result, pid = self._run_is_running(tmp_path)
        assert result is False
        assert pid is None

    def test_not_running_no_such_process(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        pid_file = data_dir / "miloco-mcp-server.pid"
        pid_file.write_text("999999", encoding="utf-8")

        def mock_kill(pid, sig):
            raise ProcessLookupError()

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("os.kill", side_effect=mock_kill):
            result, pid = _is_running()
        assert result is False
        assert pid is None

    def test_running(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        pid_file = data_dir / "miloco-mcp-server.pid"
        pid_file.write_text("12345", encoding="utf-8")
        mock_kill = MagicMock()

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("os.kill", mock_kill):
            result, pid = _is_running()
        assert result is True
        assert pid == 12345
        mock_kill.assert_called_once_with(12345, 0)

    def test_permission_denied(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        pid_file = data_dir / "miloco-mcp-server.pid"
        pid_file.write_text("12345", encoding="utf-8")

        def mock_kill(pid, sig):
            raise PermissionError("Permission denied")

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("os.kill", side_effect=mock_kill):
            result, pid = _is_running()
        assert result is True
        assert pid is None


class TestReadPort:
    """Test config port reading."""

    def test_reads_from_config(self):
        with patch("feyagate_skill.service.get_http_port", return_value=9999):
            assert _read_port() == 9999

    def test_fallback_on_error(self):
        with patch("feyagate_skill.service.get_http_port", side_effect=OSError("config error")):
            assert _read_port() == 38080


class TestDoStart:
    """Test service start."""

    def test_missing_binary(self, tmp_path):
        # Create dirs but no binary
        (tmp_path / "bin").mkdir()
        (tmp_path / "config").mkdir()
        (tmp_path / "data").mkdir()
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            assert do_start() is False

    def test_missing_config(self, tmp_path):
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")
        (tmp_path / "data").mkdir()
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            assert do_start() is False

    def test_already_running(self, tmp_path):
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "config.yaml").write_text(
            "server:\n  http_port: 38080\n", encoding="utf-8"
        )
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "miloco-mcp-server.pid").write_text("12345", encoding="utf-8")

        mock_kill = MagicMock()  # process appears running

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("os.kill", mock_kill):
            assert do_start() is True

    def test_start_subprocess_fails(self, tmp_path):
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin" / "miloco-mcp-server").write_text("#!/bin/sh", encoding="utf-8")
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "config.yaml").write_text(
            "server:\n  http_port: 38080\n", encoding="utf-8"
        )
        (tmp_path / "data").mkdir()

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("feyagate_skill.service.subprocess.Popen", side_effect=OSError("Permission denied")):
            assert do_start(port=38080) is False


class TestDoStop:
    """Test service stop."""

    def _setup_pid(self, tmp_path, pid=12345):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "miloco-mcp-server.pid").write_text(str(pid), encoding="utf-8")

    def test_not_running(self, tmp_path):
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            assert do_stop() is True

    def test_stop_graceful(self, tmp_path):
        self._setup_pid(tmp_path)

        # _is_running: alive at entry, then dead on the first wait-loop check.
        running_seq = [(True, 12345), (False, None)]

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("feyagate_skill.service._is_running", side_effect=running_seq), \
             patch("feyagate_skill.service._terminate", return_value=True) as mock_term, \
             patch("feyagate_skill.service.time.sleep"):
            assert do_stop() is True
        # Graceful request delivered; no forced kill needed.
        mock_term.assert_called_once_with(12345, force=False)

    def test_stop_force_kill(self, tmp_path):
        self._setup_pid(tmp_path)

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("feyagate_skill.service._is_running", return_value=(True, 12345)), \
             patch("feyagate_skill.service._terminate", return_value=True) as mock_term, \
             patch("feyagate_skill.service.time.sleep"):
            assert do_stop() is True
        # Process never died → graceful (force=False) then forced (force=True).
        calls = [c.kwargs.get("force") for c in mock_term.call_args_list]
        assert True in calls  # a forced kill was attempted


class TestDoStatus:
    """Test status display."""

    def test_stopped(self, tmp_path, capsys):
        (tmp_path / "data").mkdir()
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            do_status()
        captured = capsys.readouterr()
        assert "STOPPED" in captured.out

    def test_running_health_fail(self, tmp_path, capsys):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "miloco-mcp-server.pid").write_text("12345", encoding="utf-8")

        mock_kill = MagicMock()

        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("os.kill", mock_kill), \
             patch("urllib.request.urlopen", side_effect=URLError("refused")):
            do_status()
        captured = capsys.readouterr()
        assert "RUNNING" in captured.out
        assert "NOT RESPONDING" in captured.out


class TestDoLog:
    """Test log display."""

    def test_no_log_file(self, tmp_path, capsys):
        (tmp_path / "data").mkdir()
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            do_log()
        captured = capsys.readouterr()
        assert "No log file found" in captured.out

    def test_with_log_file(self, tmp_path, capsys):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        log_file = data_dir / "miloco-mcp-server.log"
        log_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path):
            do_log(lines=2)
        captured = capsys.readouterr()
        assert "line 2" in captured.out
        assert "line 3" in captured.out

    def test_log_file_not_readable(self, tmp_path, capsys):
        # This test verifies graceful handling when log file can't be read.
        # On Linux as root, permission checks are bypassed, so we mock
        # the file read to simulate a read error instead.
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        log_file = data_dir / "miloco-mcp-server.log"
        log_file.write_text("test\n", encoding="utf-8")
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            do_log()

    def test_log_windows_mode(self, tmp_path, capsys):
        """Verify Windows branch reads file directly (no `tail`)."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        log_file = data_dir / "miloco-mcp-server.log"
        log_file.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        with patch("feyagate_skill.service._install_dir", return_value=tmp_path), \
             patch("sys.platform", "win32"):
            do_log(lines=2)
        captured = capsys.readouterr()
        assert "beta" in captured.out
        assert "gamma" in captured.out
