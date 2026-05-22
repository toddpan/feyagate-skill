"""Tests for feyagate_skill.snapshot module."""

import base64
from pathlib import Path
from unittest.mock import patch

import pytest

from feyagate_skill.snapshot import do_snapshot


@pytest.fixture()
def sample_jpeg():
    """Create a minimal valid JPEG image (1x1 pixel)."""
    return bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9")


@pytest.fixture()
def camera_response(sample_jpeg):
    """Build MCP response with a JPEG snapshot."""
    data_url = f"data:image/jpeg;base64,{base64.b64encode(sample_jpeg).decode()}"
    return {
        "images": [{"data_url": data_url, "timestamp": 1700000000}],
    }


class TestListCameras:
    """Test camera listing."""

    def test_list_success(self, sample_jpeg, capsys):
        cameras = [
            {"name": "Front Door", "did": "123", "model": "xiaomi.camera",
             "camera_status": "connected", "home_name": "Home", "room_name": "Entrance"},
        ]
        with patch("feyagate_skill.snapshot.mcp_call", return_value={"cameras": cameras}):
            do_snapshot("localhost", 38080, list_cameras=True)
        captured = capsys.readouterr()
        assert "Front Door" in captured.out
        assert "123" in captured.out
        assert "xiaomi.camera" in captured.out

    def test_list_no_cameras(self, capsys):
        with patch("feyagate_skill.snapshot.mcp_call", return_value={"cameras": []}):
            do_snapshot("localhost", 38080, list_cameras=True)
        captured = capsys.readouterr()
        assert "No cameras found" in captured.out

    def test_list_error(self, capsys):
        with patch("feyagate_skill.snapshot.mcp_call", return_value={"error": "not authorized"}):
            do_snapshot("localhost", 38080, list_cameras=True)
        captured = capsys.readouterr()
        assert "not authorized" in captured.out


class TestSnapshotCapture:
    """Test snapshot capture."""

    def test_capture_success(self, sample_jpeg, tmp_path, capsys, camera_response):
        output_dir = tmp_path / "snapshots"
        output_dir.mkdir(parents=True)
        with patch("feyagate_skill.snapshot.mcp_call", return_value=camera_response):
            do_snapshot(
                "localhost", 38080,
                camera_id="cam1", channel=0, count=1,
                output_dir=str(output_dir),
            )
        captured = capsys.readouterr()
        assert "Saved:" in captured.out
        saved_files = list(output_dir.glob("*.jpg"))
        assert len(saved_files) == 1
        assert saved_files[0].read_bytes() == sample_jpeg

    def test_snapshot_no_images(self, capsys):
        with patch("feyagate_skill.snapshot.mcp_call", return_value={"images": []}):
            do_snapshot("localhost", 38080, camera_id="cam1")
        captured = capsys.readouterr()
        assert "No images returned" in captured.out

    def test_snapshot_error(self, capsys):
        with patch("feyagate_skill.snapshot.mcp_call", return_value={"error": "camera not found"}):
            do_snapshot("localhost", 38080, camera_id="cam1")
        captured = capsys.readouterr()
        assert "camera not found" in captured.out

    def test_snapshot_missing_camera_id(self, capsys):
        do_snapshot("localhost", 38080)
        captured = capsys.readouterr()
        assert "--camera-id required" in captured.out

    def test_snapshot_empty_data_url(self, tmp_path, capsys):
        output_dir = tmp_path / "snapshots"
        output_dir.mkdir(parents=True)
        result = {"images": [{"data_url": "", "timestamp": 1700000000}]}
        with patch("feyagate_skill.snapshot.mcp_call", return_value=result):
            do_snapshot("localhost", 38080, camera_id="cam1", output_dir=str(output_dir))
        captured = capsys.readouterr()
        # Should handle gracefully - 0/1 captured
        assert "0/1" in captured.out

    def test_snapshot_invalid_base64(self, tmp_path, capsys):
        output_dir = tmp_path / "snapshots"
        output_dir.mkdir(parents=True)
        # Valid data_url format but invalid base64 content
        result = {"images": [{"data_url": "data:image/jpeg;base64,!!!not-valid-base64!!!"}]}
        with patch("feyagate_skill.snapshot.mcp_call", return_value=result):
            do_snapshot("localhost", 38080, camera_id="cam1", output_dir=str(output_dir))
        captured = capsys.readouterr()
        assert "0/1" in captured.out

    def test_snapshot_multiple_images(self, sample_jpeg, tmp_path):
        output_dir = tmp_path / "snapshots"
        output_dir.mkdir(parents=True)
        images = [
            {"data_url": f"data:image/jpeg;base64,{base64.b64encode(sample_jpeg).decode()}",
             "timestamp": 1700000000 + i}
            for i in range(3)
        ]
        result = {"images": images}
        with patch("feyagate_skill.snapshot.mcp_call", return_value=result):
            do_snapshot("localhost", 38080, camera_id="cam1", count=3, output_dir=str(output_dir))
        saved_files = list(output_dir.glob("*.jpg"))
        assert len(saved_files) == 3

    def test_snapshot_connect_fails(self, capsys):
        with patch("feyagate_skill.snapshot.mcp_call", side_effect=[
            {"success": False, "message": "P2P error"},
        ]):
            do_snapshot("localhost", 38080, camera_id="cam1", connect=True)
        captured = capsys.readouterr()
        assert "Connection failed" in captured.out


class TestSnapshotMcpErrors:
    """Test MCP call error handling in snapshot."""

    def test_mcp_call_raises(self, capsys):
        with patch("feyagate_skill.snapshot.mcp_call", side_effect=Exception("connection refused")):
            do_snapshot("localhost", 38080, camera_id="cam1", connect=True)
        captured = capsys.readouterr()
        assert "Connection failed" in captured.out
