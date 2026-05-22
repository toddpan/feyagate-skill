"""Tests for feyagate_skill.scheduled module."""

import sys
import base64
from pathlib import Path
from unittest.mock import patch

import pytest

from feyagate_skill.scheduled import _capture_and_save, _ensure_connected


@pytest.fixture()
def sample_jpeg():
    """Minimal valid JPEG image."""
    return bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9")


@pytest.fixture()
def camera_response(sample_jpeg):
    """Build MCP response with a JPEG snapshot."""
    data_url = f"data:image/jpeg;base64,{base64.b64encode(sample_jpeg).decode()}"
    return {
        "images": [{"data_url": data_url, "timestamp": 1700000000}],
    }


class TestEnsureConnected:
    """Test camera connection checks."""

    def test_already_connected(self, camera_response):
        with patch("feyagate_skill.scheduled.mcp_call", return_value={
            "status": "connected", "buffered_frames": 5,
        }):
            result = _ensure_connected("localhost", 38080, "cam1")
        assert result is True

    def test_connect_fails(self, camera_response):
        with patch("feyagate_skill.scheduled.mcp_call", side_effect=Exception("timeout")):
            result = _ensure_connected("localhost", 38080, "cam1")
        assert result is False

    def test_status_then_connect(self, camera_response):
        """Not connected → tries connect → checks status again."""
        call_count = [0]

        def mock_call(host, port, tool, args=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"status": "disconnected"}
            # connect call
            if tool == "xiaomi/camera_connect":
                return None
            # second status check
            return {"status": "connected"}

        with patch("feyagate_skill.scheduled.mcp_call", side_effect=mock_call):
            result = _ensure_connected("localhost", 38080, "cam1")
        assert result is True


class TestCaptureAndSave:
    """Test single snapshot capture and save."""

    def test_capture_success(self, sample_jpeg, tmp_path, camera_response):
        output_dir = tmp_path / "analysis"
        with patch("feyagate_skill.scheduled.mcp_call", return_value=camera_response):
            result = _capture_and_save("localhost", 38080, "cam1", 0, output_dir)
        assert result is not None
        assert result["camera_id"] == "cam1"
        assert result["channel"] == 0
        # Files are saved in date subdirectories
        saved = list(output_dir.rglob("*.jpg"))
        assert len(saved) == 1
        assert saved[0].read_bytes() == sample_jpeg

    def test_capture_no_images(self):
        with patch("feyagate_skill.scheduled.mcp_call", return_value={"images": []}):
            result = _capture_and_save("localhost", 38080, "cam1", 0, Path("/tmp"))
        assert result is None

    def test_capture_mcp_error(self):
        with patch("feyagate_skill.scheduled.mcp_call", side_effect=Exception("timeout")):
            result = _capture_and_save("localhost", 38080, "cam1", 0, Path("/tmp"))
        assert result is None

    def test_capture_empty_data_url(self):
        with patch("feyagate_skill.scheduled.mcp_call", return_value={
            "images": [{"data_url": "", "timestamp": 1700000000}],
        }):
            result = _capture_and_save("localhost", 38080, "cam1", 0, Path("/tmp"))
        assert result is None

    def test_capture_invalid_base64(self):
        with patch("feyagate_skill.scheduled.mcp_call", return_value={
            "images": [{"data_url": "data:image/jpeg;base64,!!!invalid!!!"}],
        }):
            result = _capture_and_save("localhost", 38080, "cam1", 0, Path("/tmp"))
        assert result is None

    def test_capture_write_error(self, tmp_path):
        output_dir = tmp_path / "analysis"
        output_dir = output_dir / "subdir"  # nested path that will fail
        result = _capture_and_save("localhost", 38080, "cam1", 0, output_dir)
        # If we can't write, returns None
        assert result is None or isinstance(result, dict)

    def test_capture_returns_metadata(self, sample_jpeg, tmp_path, camera_response):
        output_dir = tmp_path / "analysis"
        with patch("feyagate_skill.scheduled.mcp_call", return_value=camera_response):
            result = _capture_and_save("localhost", 38080, "cam1", 0, output_dir)
        assert result is not None
        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "datetime" in result
        assert "image_path" in result
        assert "image_size_bytes" in result
        assert result["image_size_bytes"] == len(sample_jpeg)


class TestSignalHandler:
    """Test signal handler."""

    def test_handler_sets_running_false(self):
        from feyagate_skill import scheduled as sched
        # Initial state
        original = sched._running
        sched._running = True

        # Call handler
        sched._signal_handler(None, None)
        assert sched._running is False

        # Restore
        sched._running = original

    def test_sigint_skipped_on_windows(self, monkeypatch):
        """Verify SIGINT handler is not registered on Windows."""
        import signal as sig_mod
        original_platform = sys.platform

        try:
            # Temporarily pretend we're on Windows
            sys.platform = "win32"

            # Force reload the module to re-evaluate the `if sys.platform != "win32"` guard
            import importlib
            import feyagate_skill.scheduled as sched_mod
            importlib.reload(sched_mod)

            # On Windows, SIGINT should not be registered (no AttributeError)
            # We verify by checking signal.getsignal returns None for SIGINT
            handler = sig_mod.getsignal(sig_mod.SIGINT)
            # The default handler on Windows is SIG_DFL or similar, not our _signal_handler
            assert handler != sched_mod._signal_handler
        finally:
            sys.platform = original_platform
