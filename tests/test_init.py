"""Tests for feyagate_skill.__init__.py."""

import feyagate_skill


class TestPackageInit:
    """Test package-level exports."""

    def test_version(self):
        assert isinstance(feyagate_skill.__version__, str)
        assert feyagate_skill.__version__ == "1.2.2"

    def test_author(self):
        assert feyagate_skill.__author__ == "panzuji"

    def test_default_install_dir(self):
        assert feyagate_skill.DEFAULT_INSTALL_DIR == "~/.feyagate"

    def test_mcp_defaults(self):
        assert feyagate_skill.MCP_DEFAULT_PORT == 38080
        assert feyagate_skill.MCP_DEFAULT_HOST == "127.0.0.1"

    def test_fota_url(self):
        assert feyagate_skill.FOTA_URL == "https://oneapi.sooncore.com/ota/fota.json"

    def test_all_exports(self):
        assert "__version__" in feyagate_skill.__all__
        assert "__author__" in feyagate_skill.__all__
        assert "DEFAULT_INSTALL_DIR" in feyagate_skill.__all__
        assert "FOTA_URL" in feyagate_skill.__all__
        assert "MCP_DEFAULT_PORT" in feyagate_skill.__all__
        assert "MCP_DEFAULT_HOST" in feyagate_skill.__all__
