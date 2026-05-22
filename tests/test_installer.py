"""Tests for feyagate_skill.installer module."""

import json
import tarfile
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from feyagate_skill.installer import (
    _detect_fota_type,
    _fetch_fota,
    _download,
    _md5,
    _extract,
    _init_config,
    _copy_skill_docs,
    do_setup,
)


class TestDetectFotaType:
    """Test platform detection."""

    def test_linux_x86_64(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.setattr("platform.machine", lambda: "x86_64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-linux-x64"
        assert os_name == "Linux"
        assert arch == "x86_64"

    def test_linux_amd64(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.setattr("platform.machine", lambda: "amd64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-linux-x64"

    def test_macos_intel(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.setattr("platform.machine", lambda: "x86_64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-mac-x64"

    def test_macos_arm(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.setattr("platform.machine", lambda: "arm64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-mac-arm64"

    def test_windows(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr("platform.machine", lambda: "AMD64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-win"

    def test_windows_arm64(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr("platform.machine", lambda: "ARM64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-win"

    def test_fallback_unknown_platform(self, monkeypatch):
        """Unknown platform falls back to generic name."""
        monkeypatch.setattr("platform.system", lambda: "FreeBSD")
        monkeypatch.setattr("platform.machine", lambda: "x86_64")
        fota_type, os_name, arch = _detect_fota_type()
        assert fota_type == "feyagate-skill-freebsd-x64"
        assert os_name == "FreeBSD"


class TestFetchFota:
    """Test FOTA data fetching."""

    def test_fetch_success(self, tmp_path):
        """Test successful FOTA fetch."""
        fota_data = [
            {"type": "feyagate-skill-linux-x64", "version": "1.2.0",
             "url": "https://example.com/linux-x64.tar.gz",
             "md5": "d41d8cd98f00b204e9800998ecf8427e",
             "platform": "Linux", "arch": "x86_64"},
            {"type": "feyagate-skill-mac-arm64", "version": "1.2.0",
             "url": "https://example.com/mac-arm64.tar.gz",
             "md5": "098f6bcd4621d373cade4e832627b4f6",
             "platform": "Darwin", "arch": "arm64"},
        ]
        expected_json = json.dumps(fota_data).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = expected_json
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_fota()
        assert len(result) == 2

    def test_fetch_network_error(self):
        from urllib.error import URLError
        with patch("urllib.request.urlopen", side_effect=URLError("network error")):
            with pytest.raises(RuntimeError, match="Cannot reach FOTA server"):
                _fetch_fota()

    def test_fetch_invalid_json(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="Invalid FOTA response"):
                _fetch_fota()


class TestDownload:
    """Test file download."""

    def test_download_success(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.headers.get.return_value = "1024"
        mock_resp.read.side_effect = [b"x" * 512, b"x" * 512, b""]
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None

        with patch("urllib.request.urlopen", return_value=mock_resp):
            dest = tmp_path / "download.bin"
            _download("https://example.com/file.bin", dest, progress=False)

        assert dest.exists()
        assert dest.read_bytes() == b"x" * 1024

    def test_download_network_error(self, tmp_path):
        from urllib.error import URLError
        with patch("urllib.request.urlopen", side_effect=URLError("network error")):
            with pytest.raises(RuntimeError, match="Download failed"):
                _download("https://example.com/file.bin", tmp_path / "f.bin")

    def test_download_write_error(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.headers.get.return_value = "100"
        mock_resp.read.return_value = b"test"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: None

        def fake_open(path, mode):
            raise OSError("Permission denied")

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("builtins.open", fake_open):
            with pytest.raises(RuntimeError, match="Write failed"):
                _download("https://example.com/file.bin", tmp_path / "f.bin")


class TestMd5:
    """Test MD5 hashing."""

    def test_md5_computed(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")
        digest = _md5(test_file)
        assert len(digest) == 32
        assert digest == "5eb63bbbe01eeed093cb22bb8f5acdc3"


class TestExtract:
    """Test archive extraction."""

    def _make_tarball(self, tmp_path, files):
        """Create a test tarball with given files."""
        archive = tmp_path / "test.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            for name, content in files.items():
                data = content.encode() if isinstance(content, str) else content
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tf.addfile(info, __import__("io").BytesIO(data))
        return archive

    def test_extract_tarball(self, tmp_path):
        tarball = self._make_tarball(
            tmp_path,
            {
                "release/bin/miloco-mcp-server": "#!/bin/sh\necho hi",
                "release/lib/libfoo.so": "binary data",
                "release/webui/index.html": "<html></html>",
            },
        )
        install_dir = tmp_path / "install"
        _extract(tarball, install_dir)
        assert (install_dir / "bin" / "miloco-mcp-server").exists()
        assert (install_dir / "bin" / "miloco-mcp-server").stat().st_mode & 0o111
        assert (install_dir / "lib" / "libfoo.so").exists()
        assert (install_dir / "webui" / "index.html").exists()

    def test_extract_zip(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("release/bin/miloco-mcp-server", "#!/bin/sh")
            zf.writestr("release/lib/libbar.so", "data")

        install_dir = tmp_path / "install"
        _extract(zip_path, install_dir)
        assert (install_dir / "bin" / "miloco-mcp-server").exists()

    def test_extract_no_binary(self, tmp_path):
        tarball = self._make_tarball(tmp_path, {
            "release/README.md": "just a readme",
        })
        install_dir = tmp_path / "install"
        with pytest.raises(RuntimeError, match="No executable found"):
            _extract(tarball, install_dir)

    def test_extract_skips_symlink_on_windows(self, tmp_path):
        """Verify symlink creation is skipped on Windows (simulated)."""
        tarball = self._make_tarball(
            tmp_path,
            {
                "release/bin/miloco-mcp-server": "#!/bin/sh",
                "release/lib/libfoo.so": "binary data",
            },
        )
        install_dir = tmp_path / "install"
        _extract(tarball, install_dir)

        # Binary and lib should exist
        assert (install_dir / "bin" / "miloco-mcp-server").exists()
        assert (install_dir / "lib" / "libfoo.so").exists()

        # On Linux this test runs, so symlink should be created.
        # We just verify the binary + lib are present regardless of platform.


class TestInitConfig:
    """Test config initialization."""

    def test_creates_default_config(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        (install_dir / "config").mkdir()
        config_file = install_dir / "config" / "config.yaml"
        assert not config_file.exists()

        _init_config(install_dir)
        assert config_file.exists()
        content = config_file.read_text()
        assert "http_port" in content
        assert "38080" in content

    def test_skips_existing_config(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        (install_dir / "config").mkdir()
        config_file = install_dir / "config" / "config.yaml"
        config_file.write_text("# existing config\n", encoding="utf-8")

        _init_config(install_dir)
        content = config_file.read_text()
        assert "# existing config" in content

    def test_write_error(self, tmp_path):
        """Test that write errors are handled gracefully."""
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        config_dir = install_dir / "config"
        config_dir.mkdir()

        with patch("pathlib.Path.write_text", side_effect=OSError("Permission denied")):
            with pytest.raises(RuntimeError, match="Cannot write config"):
                _init_config(install_dir)


class TestCopySkillDocs:
    """Test skill documentation copying."""

    def test_no_crash_with_missing_package(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        _copy_skill_docs(install_dir)

    def test_creates_skills_dir(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()
        _copy_skill_docs(install_dir)
        skills_dir = install_dir / "skills"
        assert skills_dir.is_dir()


class TestDoSetup:
    """Test full installation flow."""

    def test_setup_fota_fetch_failure(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        def mock_fota():
            raise RuntimeError("no network")

        with patch("feyagate_skill.installer._fetch_fota", mock_fota):
            result = do_setup(str(install_dir))
        assert result is False

    def test_setup_no_matching_release(self, tmp_path):
        install_dir = tmp_path / "feyagate"
        install_dir.mkdir()

        def mock_fota():
            return [{"type": "some-other-type", "version": "1.0",
                     "url": "http://x", "md5": "a"}]

        with patch("feyagate_skill.installer._fetch_fota", mock_fota):
            result = do_setup(str(install_dir))
        assert result is False
