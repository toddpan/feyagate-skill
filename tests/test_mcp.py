"""Tests for feyagate_skill.mcp module."""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from feyagate_skill.mcp import (
    mcp_call,
    async_mcp_call,
    async_mcp_batch,
    async_close,
)


def _make_valid_response():
    """Create a mock urlopen response for a successful MCP call."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "result": {
            "content": [{"text": json.dumps({"devices": []})}],
        },
    })
    resp = MagicMock()
    resp.read.return_value = payload.encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda *a: None
    return resp


def _make_error_response():
    """Create a mock urlopen response for an MCP error."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": "Tool not found"},
    })
    resp = MagicMock()
    resp.read.return_value = payload.encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda *a: None
    return resp


class TestMcpCall:
    """Test synchronous MCP tool calls."""

    def test_successful_call(self):
        mock_resp = _make_valid_response()
        with patch("feyagate_skill.mcp.urlopen", return_value=mock_resp):
            result = mcp_call("localhost", 38080, "xiaomi/get_properties", {"device_id": "123"})
        assert isinstance(result, dict)
        assert "devices" in result
        assert result["devices"] == []

    def test_error_response(self):
        mock_resp = _make_error_response()
        with patch("feyagate_skill.mcp.urlopen", return_value=mock_resp):
            result = mcp_call("localhost", 38080, "nonexistent/tool")
        assert "error" in result
        assert result["error"]["code"] == -32601

    def test_connection_refused(self):
        with patch("feyagate_skill.mcp.urlopen", side_effect=URLError("Connection refused")):
            result = mcp_call("localhost", 38080, "xiaomi/get_properties")
        assert "error" in result
        assert "Connection" in result["error"] or "Network" in result["error"]

    def test_invalid_json_response(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not valid json at all"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None
        with patch("feyagate_skill.mcp.urlopen", return_value=mock_resp):
            result = mcp_call("localhost", 38080, "xiaomi/get_properties")
        assert "error" in result
        assert "JSON" in result["error"]

    def test_bad_response_structure(self):
        payload = json.dumps({"jsonrpc": "2.0", "result": {"unexpected_field": True}})
        mock_resp = MagicMock()
        mock_resp.read.return_value = payload.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None
        with patch("feyagate_skill.mcp.urlopen", return_value=mock_resp):
            result = mcp_call("localhost", 38080, "xiaomi/get_properties")
        assert isinstance(result, dict)

    def test_none_arguments(self):
        mock_resp = _make_valid_response()
        with patch("feyagate_skill.mcp.urlopen", return_value=mock_resp):
            result = mcp_call("localhost", 38080, "xiaomi/get_properties", None)
        assert isinstance(result, dict)

    def test_empty_arguments(self):
        mock_resp = _make_valid_response()
        with patch("feyagate_skill.mcp.urlopen", return_value=mock_resp):
            result = mcp_call("localhost", 38080, "xiaomi/get_properties", {})
        assert isinstance(result, dict)


class TestReadPortFromConfig:
    """Test port reading from config."""

    def test_reads_port(self, tmp_path):
        from feyagate_skill.mcp import read_port_from_config
        config = tmp_path / "config.yaml"
        config.write_text("server:\n  http_port: 38080\n  ws_port: 8765\n", encoding="utf-8")
        assert read_port_from_config(config) == 38080

    def test_returns_none_for_missing_file(self):
        from feyagate_skill.mcp import read_port_from_config
        assert read_port_from_config(Path("/nonexistent/config.yaml")) is None

    def test_returns_default_when_missing(self, tmp_path):
        from feyagate_skill.mcp import read_port_from_config
        config = tmp_path / "minimal.yaml"
        config.write_text("server:\n  ws_port: 8765\n", encoding="utf-8")
        assert read_port_from_config(config) == 38080


class TestAsyncMcpCall:
    """Test asynchronous MCP tool calls."""

    def _run_async(self, coro):
        """Run async code using asyncio.run (always creates fresh loop)."""
        return asyncio.run(coro)

    def test_aiohttp_available(self):
        """When aiohttp is available, gets connection error (no server)."""
        try:
            import aiohttp  # noqa: F401
        except ImportError:
            pytest.skip("aiohttp not available")

        result = self._run_async(async_mcp_call("127.0.0.1", 19999, "test"))
        assert "error" in result

    def test_aiohttp_not_available(self):
        """When aiohttp is not available, returns informative error."""
        import feyagate_skill.mcp as mcp_mod
        orig_client = mcp_mod._aiohttp_client
        orig_available = mcp_mod._AIOHTTP_AVAILABLE

        try:
            mcp_mod._AIOHTTP_AVAILABLE = False
            mcp_mod._aiohttp_client = None

            result = self._run_async(async_mcp_call("localhost", 38080, "test"))
            assert result == {"error": "aiohttp not installed; use mcp_call() for sync"}
        finally:
            mcp_mod._AIOHTTP_AVAILABLE = orig_available
            mcp_mod._aiohttp_client = orig_client


class TestAsyncMcpBatch:
    """Test concurrent MCP batch calls."""

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_batch_no_aiohttp(self):
        """When aiohttp not installed, returns errors for all calls."""
        import feyagate_skill.mcp as mcp_mod
        orig_client = mcp_mod._aiohttp_client
        orig_available = mcp_mod._AIOHTTP_AVAILABLE

        try:
            mcp_mod._AIOHTTP_AVAILABLE = False
            mcp_mod._aiohttp_client = None

            result = self._run_async(async_mcp_batch(
                "localhost", 38080,
                [("tool1", None), ("tool2", {"key": "val"})],
            ))
            assert len(result) == 2
            for r in result:
                assert "error" in r
                assert "aiohttp" in r["error"]
        finally:
            mcp_mod._AIOHTTP_AVAILABLE = orig_available
            mcp_mod._aiohttp_client = orig_client

    def test_batch_with_aiohttp(self):
        """With aiohttp, batch calls return errors (no server)."""
        try:
            import aiohttp  # noqa: F401
        except ImportError:
            pytest.skip("aiohttp not available")

        result = self._run_async(async_mcp_batch(
            "127.0.0.1", 19999,
            [("tool1", None)],
        ))
        assert len(result) == 1
        assert "error" in result[0]


class TestAsyncClose:
    """Test async resource cleanup."""

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_close_no_error(self):
        self._run_async(async_close())


class TestBuildPayload:
    """Test JSON-RPC payload construction."""

    def test_minimal_payload(self):
        import feyagate_skill.mcp as mcp_mod
        payload = mcp_mod._build_payload("test_tool", None)
        data = json.loads(payload)
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "tools/call"
        assert data["params"]["name"] == "test_tool"
        assert data["params"]["arguments"] == {}

    def test_payload_with_args(self):
        import feyagate_skill.mcp as mcp_mod
        payload = mcp_mod._build_payload("test_tool", {"key": "val"})
        data = json.loads(payload)
        assert data["params"]["arguments"] == {"key": "val"}


class TestParseResponse:
    """Test response parsing."""

    def test_valid_response(self):
        import feyagate_skill.mcp as mcp_mod
        raw = json.dumps({
            "result": {"content": [{"text": json.dumps({"ok": True})}]},
        }).encode()
        result = mcp_mod._parse_response(raw)
        assert result == {"ok": True}

    def test_error_response(self):
        import feyagate_skill.mcp as mcp_mod
        raw = json.dumps({
            "error": {"code": -32601, "message": "Not found"},
        }).encode()
        result = mcp_mod._parse_response(raw)
        assert "error" in result

    def test_invalid_json(self):
        import feyagate_skill.mcp as mcp_mod
        result = mcp_mod._parse_response(b"not json")
        assert "error" in result

    def test_broken_structure(self):
        import feyagate_skill.mcp as mcp_mod
        raw = json.dumps({
            "result": {"content": []},
        }).encode()
        result = mcp_mod._parse_response(raw)
        assert isinstance(result, dict)
