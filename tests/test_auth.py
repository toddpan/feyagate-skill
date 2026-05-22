"""Tests for feyagate_skill.auth module."""

from unittest.mock import MagicMock, patch

import pytest

from feyagate_skill.auth import check_status, get_auth_url, submit_code, do_auth


class TestCheckStatus:
    """Test auth status checking."""

    def test_authorized(self):
        with patch("feyagate_skill.auth._mcp", return_value={"authorized": True, "remaining_seconds": 86400}):
            result = check_status("localhost", 38080)
        assert result is True

    def test_not_authorized(self):
        with patch("feyagate_skill.auth._mcp", return_value={"authorized": False, "remaining_seconds": 0}):
            result = check_status("localhost", 38080)
        assert result is False


class TestGetAuthUrl:
    """Test auth URL retrieval."""

    def test_returns_url(self):
        with patch("feyagate_skill.auth._mcp", return_value={"url": "https://mi.com/auth?code=abc"}):
            result = get_auth_url("localhost", 38080)
        assert "https://mi.com/auth" in result

    def test_returns_empty_on_error(self):
        with patch("feyagate_skill.auth._mcp", return_value={"error": "auth failed"}):
            result = get_auth_url("localhost", 38080)
        assert result == ""


class TestSubmitCode:
    """Test auth code submission."""

    def test_submit_plain_code(self):
        with patch("feyagate_skill.auth._mcp", return_value={}), \
             patch("feyagate_skill.auth.check_status", return_value=False):
            result = submit_code("localhost", 38080, "abc123")
        assert result is False  # check_status returned False

    def test_submit_url_with_code(self):
        with patch("feyagate_skill.auth._mcp", return_value={}), \
             patch("feyagate_skill.auth.check_status", return_value=True):
            result = submit_code("localhost", 38080, "https://example.com/callback?code=xyz")
        assert result is True

    def test_submit_url_without_code(self):
        with patch("feyagate_skill.auth._mcp", return_value={}):
            result = submit_code("localhost", 38080, "https://example.com/callback")
        assert result is False

    def test_submit_callback_error(self):
        with patch("feyagate_skill.auth._mcp", side_effect=Exception("timeout")):
            result = submit_code("localhost", 38080, "abc123")
        assert result is False


class TestDoAuth:
    """Test the full auth flow."""

    def test_status_only(self, capsys):
        with patch("feyagate_skill.auth._mcp", return_value={"authorized": True, "remaining_seconds": 3600}):
            do_auth("localhost", 38080, status_only=True)
        captured = capsys.readouterr()
        assert "Auth Status" in captured.out
        assert "Authorized" in captured.out

    def test_submit_code_only(self, capsys):
        with patch("feyagate_skill.auth._mcp", return_value={}), \
             patch("feyagate_skill.auth.check_status", return_value=True):
            do_auth("localhost", 38080, code="abc123")
        captured = capsys.readouterr()
        assert "Authorization successful" in captured.out

    def test_already_authorized(self, capsys):
        with patch("feyagate_skill.auth._mcp", return_value={"authorized": True, "remaining_seconds": 7200}):
            do_auth("localhost", 38080)
        captured = capsys.readouterr()
        assert "Already authorized" in captured.out
