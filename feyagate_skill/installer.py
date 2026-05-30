"""Binary download and installation from fota.json."""

import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from . import FOTA_URL, SERVER_RELEASE_BASE, __version__

logger = logging.getLogger(__name__)

FOTA_TYPE_MAP = {
    ("Linux", "x86_64"): "feyagate-skill-linux-x64",
    ("Linux", "amd64"): "feyagate-skill-linux-x64",
    ("Darwin", "x86_64"): "feyagate-skill-mac-x64",
    ("Darwin", "arm64"): "feyagate-skill-mac-arm64",
    ("Windows", "AMD64"): "feyagate-skill-win",
    ("Windows", "ARM64"): "feyagate-skill-win",
}

# Platform tag used in GitHub release asset names, e.g. miloco-mcp-server-win-x64-v1.2.16.zip
# Matches feyagate-desktop/scripts/download-server.js and scripts/install.sh.
RELEASE_TAG_MAP = {
    ("Linux", "x86_64"): "linux-x64",
    ("Linux", "amd64"): "linux-x64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Linux", "arm64"): "linux-arm64",
    ("Darwin", "x86_64"): "mac-x64",
    ("Darwin", "arm64"): "mac-arm64",
    ("Windows", "AMD64"): "win-x64",
    ("Windows", "ARM64"): "win-arm64",
}


def _detect_release_tag():
    """Return the GitHub release platform tag for the current machine."""
    key = (platform.system(), platform.machine())
    if key in RELEASE_TAG_MAP:
        return RELEASE_TAG_MAP[key]
    # fallback: x64 for the detected OS
    return f"{platform.system().lower()}-x64"


def _github_archive_url(version, release_tag):
    """Build the GitHub Releases download URL for the server archive.

    Only Windows uses .zip; all Unix platforms (macOS/Linux) use .tar.gz to
    preserve symlinks, file permissions, and POSIX path separators. A Windows
    zip built with backslash separators cannot be extracted correctly on Unix.
    """
    ext = "zip" if release_tag.startswith("win") else "tar.gz"
    archive = f"miloco-mcp-server-{release_tag}-v{version}.{ext}"
    return f"{SERVER_RELEASE_BASE}/v{version}/{archive}", archive


def _detect_fota_type():
    os_name = platform.system()
    arch = platform.machine()
    key = (os_name, arch)
    if key in FOTA_TYPE_MAP:
        return FOTA_TYPE_MAP[key], os_name, arch
    # fallback
    fota = f"feyagate-skill-{os_name.lower()}-x64"
    return fota, os_name, arch


def _parse_relaxed_json(text):
    """Parse JavaScript-style object notation with unquoted keys/values."""
    import re
    # Process line by line: quote unquoted keys and values
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        # Match lines like:  key: value  or  key: value,
        m = re.match(r'^(\w+)\s*:\s*(.*?)(,?)$', stripped)
        if m:
            key, val, comma = m.groups()
            val = val.strip()
            # Quote value unless it's a JSON literal (true/false/null/number)
            if val in ('true', 'false', 'null') or val == '':
                if val == '':
                    val = '""'
            else:
                try:
                    json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    val = json.dumps(val)
            indent = line[:len(line) - len(line.lstrip())]
            lines.append(f'{indent}"{key}": {val}{comma}')
        else:
            lines.append(line)
    return json.loads('\n'.join(lines))


def _fetch_fota():
    """Fetch version info from FOTA server.

    Returns:
        Parsed JSON list of release entries.

    Raises:
        Exception: On network or parse failure.
    """
    from urllib.error import URLError
    from urllib.request import urlopen
    try:
        with urlopen(FOTA_URL, timeout=15) as resp:
            data = resp.read().decode("utf-8")
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return _parse_relaxed_json(data)
    except URLError as exc:
        raise RuntimeError(f"Cannot reach FOTA server: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid FOTA response: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Network error fetching FOTA: {exc}") from exc


def _download(url, dest, progress=True):
    """Download file from url to dest with optional progress display.

    Args:
        url: Download URL.
        dest: Destination Path.
        progress: Show download progress bar.

    Raises:
        RuntimeError: On network or write failure.
    """
    from urllib.error import URLError
    from urllib.request import urlopen
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urlopen(url, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress and total > 0:
                        pct = downloaded * 100 // total
                        mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        sys.stdout.write(
                            f"\r  Downloading: {mb:.1f}/{total_mb:.1f} MB ({pct}%)"
                        )
                        sys.stdout.flush()

        if progress:
            print()  # newline after progress
    except URLError as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Write failed to {dest}: {exc}") from exc


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_sha256(url):
    """Fetch a .sha256 sidecar file; return the hex digest or None."""
    from urllib.request import urlopen
    try:
        with urlopen(url, timeout=30) as resp:
            if resp.status != 200:
                return None
            text = resp.read().decode("utf-8", "replace")
            return text.strip().split()[0].lower() if text.strip() else None
    except Exception:
        return None


def _macos_unquarantine_and_sign(bin_dir, lib_dir):
    """Clear quarantine attr and ad-hoc sign the binary + dylibs on macOS.

    Binaries downloaded over the network carry com.apple.quarantine, and the
    bundled .dylib files are unsigned. Without this, Gatekeeper kills the
    process on launch ("cannot be opened because the developer cannot be
    verified" / dyld code-signature errors). Best-effort: failures are logged
    but do not abort installation.
    """
    bin_dir = Path(bin_dir)
    lib_dir = Path(lib_dir)
    binary = bin_dir / "miloco-mcp-server"

    targets = [binary]
    if lib_dir.is_dir():
        targets += [
            p for p in lib_dir.iterdir()
            if p.is_file() and not p.is_symlink() and not p.name.startswith("._")
        ]

    # 1. Strip quarantine recursively (ignore "no such xattr" errors).
    for path in (binary, lib_dir):
        if path.exists():
            subprocess.run(
                ["xattr", "-rd", "com.apple.quarantine", str(path)],
                capture_output=True, check=False,
            )

    # 2. Ad-hoc sign each dylib first, then the binary last.
    signed = 0
    for target in targets:
        if not target.exists():
            continue
        result = subprocess.run(
            ["codesign", "--force", "--sign", "-", str(target)],
            capture_output=True, check=False,
        )
        if result.returncode == 0:
            signed += 1
        else:
            logger.warning(
                "codesign failed for %s: %s",
                target.name, result.stderr.decode("utf-8", "replace").strip(),
            )
    if signed:
        print(f"  [OK] macOS: cleared quarantine + ad-hoc signed {signed} file(s)")


def _extract(archive, install_dir):
    """Extract release archive to install_dir.

    Args:
        archive: Path to .tar.gz or .zip archive.
        install_dir: Destination installation directory.

    Raises:
        RuntimeError: On extraction or deployment failure.
    """
    install_dir = Path(install_dir)
    tmp = tempfile.mkdtemp()
    try:
        if str(archive).endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(tmp)
        else:
            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(tmp)

        # Find inner directory, ignoring macOS AppleDouble (._*) sidecar entries
        # that some tarballs include at the top level.
        entries = [
            e for e in Path(tmp).iterdir() if not e.name.startswith("._")
        ]
        inner = Path(tmp)
        dirs = [e for e in entries if e.is_dir()]
        if len(dirs) == 1:
            inner = dirs[0]

        # Deploy binary (handles both Unix `miloco-mcp-server` and Windows `.exe`)
        bin_dir = install_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        bin_name = "miloco-mcp-server.exe" if sys.platform == "win32" else "miloco-mcp-server"
        found_binary = False
        candidates = [
            bin_name,
            f"bin/{bin_name}",
            "miloco-mcp-server.exe",
            "miloco-mcp-server",
            "bin/miloco-mcp-server.exe",
            "bin/miloco-mcp-server",
        ]
        for candidate in candidates:
            src = inner / candidate
            if src.exists():
                dest = bin_dir / bin_name
                shutil.copy2(src, dest)
                if sys.platform != "win32":
                    dest.chmod(0o755)
                print(f"  [OK] bin/{bin_name}")
                found_binary = True
                break

        if not found_binary:
            raise RuntimeError(
                f"No executable found in archive. Contents: {[e.name for e in inner.iterdir()]}"
            )

        # Deploy libraries (preserve symlinks; skip macOS AppleDouble ._ files)
        lib_dir = install_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        inner_lib = inner / "lib"
        lib_count = 0
        if inner_lib.is_dir():
            # Two passes: copy real files first, then recreate symlinks so their
            # targets already exist. Skip ._* AppleDouble metadata files.
            for f in inner_lib.iterdir():
                if f.name.startswith("._"):
                    continue
                if f.is_symlink():
                    continue
                if f.is_file():
                    shutil.copy2(f, lib_dir / f.name)
                    lib_count += 1
            for f in inner_lib.iterdir():
                if f.name.startswith("._"):
                    continue
                if not f.is_symlink():
                    continue
                dest = lib_dir / f.name
                target = os.readlink(f)
                if dest.exists() or dest.is_symlink():
                    dest.unlink()
                try:
                    os.symlink(target, dest)
                    lib_count += 1
                except OSError:
                    # Fallback: copy the resolved file if symlink unsupported
                    resolved = inner_lib / target
                    if resolved.is_file():
                        shutil.copy2(resolved, dest)
                        lib_count += 1
        print(f"  [OK] lib/ ({lib_count} files)")

        # Create bin/lib symlink for rpath (skip on Windows)
        bin_lib = bin_dir / "lib"
        if not bin_lib.exists() and sys.platform != "win32":
            try:
                bin_lib.symlink_to(Path("../lib"))
            except OSError as exc:
                logger.warning("Cannot create lib symlink: %s", exc)

        # Deploy WebUI
        inner_webui = inner / "webui"
        if inner_webui.is_dir():
            webui_dir = install_dir / "webui"
            if webui_dir.exists():
                shutil.rmtree(webui_dir)
            shutil.copytree(inner_webui, webui_dir)
            print("  [OK] webui/")

        # macOS: clear quarantine + ad-hoc re-sign so Gatekeeper allows the
        # downloaded binary/dylibs to load (network downloads are quarantined
        # and the unsigned libs would otherwise be killed on launch).
        if sys.platform == "darwin":
            _macos_unquarantine_and_sign(bin_dir, lib_dir)

    except (zipfile.BadZipFile, tarfile.TarError) as exc:
        raise RuntimeError(f"Archive extraction failed: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"File operation failed: {exc}") from exc
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except OSError as exc:
            logger.warning("Failed to clean up temp dir %s: %s", tmp, exc)


def _init_config(install_dir):
    """Create config from template if not exists."""
    config_dir = Path(install_dir) / "config"
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        return

    config_dir.mkdir(parents=True, exist_ok=True)

    # Try package-bundled template
    try:
        from importlib.resources import files
        pkg_data = files("feyagate_skill") / "data" / "config.yaml.example"
        template = pkg_data.read_text(encoding="utf-8")
        config_file.write_text(template, encoding="utf-8")
        print("  [OK] config/config.yaml (from template)")
        return
    except Exception as exc:
        logger.warning("Package template failed, using default: %s", exc)

    # Fallback default config
    default_config = (
        'server:\n'
        '  ws_port: 8765\n'
        '  http_port: 38080\n'
        '  bind_address: "0.0.0.0"\n'
        '  webui_dir: "webui"\n\n'
        'auth:\n'
        '  cloud_server: "cn"\n'
        '  token_file: "data/auth_token.json"\n\n'
        'camera:\n'
        '  frame_interval: 500\n'
        '  buffer_max_size: 20\n'
        '  buffer_ttl: 300\n'
        '  reconnect_min: 3\n'
        '  reconnect_max: 1200\n'
        '  jpeg_quality: 90\n'
    )
    try:
        config_file.write_text(default_config, encoding="utf-8")
        print("  [OK] config/config.yaml (default)")
    except OSError as exc:
        raise RuntimeError(f"Cannot write config: {exc}") from exc


def _copy_skill_docs(install_dir):
    """Copy SKILL.md and skills/*.md to install dir."""
    install_dir = Path(install_dir)
    try:
        from importlib.resources import files
        pkg = files("feyagate_skill") / "data"

        # SKILL.md
        skill_md = pkg / "SKILL.md"
        if skill_md.is_file():
            target = install_dir / "SKILL.md"
            if not target.exists():
                target.write_text(skill_md.read_text(encoding="utf-8"), encoding="utf-8")

        # skills/*.md
        skills_dir = install_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        skills_pkg = pkg / "skills"
        if skills_pkg.is_dir():
            for f in skills_pkg.iterdir():
                if f.is_file() and f.suffix == ".md":
                    target = skills_dir / f.name
                    if not target.exists():
                        target.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to copy skill docs: %s", exc)


def do_setup(install_dir=None):
    """Download and install the MCP server binary.

    Returns:
        True on success, False on failure.
    """
    install_dir = Path(install_dir or os.path.expanduser("~/.feyagate"))
    install_dir.mkdir(parents=True, exist_ok=True)

    fota_type, os_name, arch = _detect_fota_type()
    release_tag = _detect_release_tag()
    print("FeyaGate Skill Setup")
    print(f"  Platform: {os_name}-{arch}")
    print(f"  Install:  {install_dir}")
    print()

    # The binary version is pinned to 1.2.16 (the latest available release).
    # Package versions 1.2.17+ are Python wrapper updates only.
    version = "1.2.16"

    # Optionally consult fota.json for an OTA fallback URL + md5 (best-effort).
    fota_url = ""
    expected_md5 = ""
    try:
        fota_data = _fetch_fota()
        for item in fota_data:
            if item.get("type") == fota_type:
                fota_url = item.get("url", "")
                expected_md5 = item.get("md5", "")
                break
    except RuntimeError as exc:
        logger.warning("fota.json unavailable, GitHub-only mode: %s", exc)

    # Primary source: GitHub Releases.
    download_url, archive_name = _github_archive_url(version, release_tag)
    expected_sha256 = _fetch_sha256(download_url + ".sha256")

    print(f"  Version:      v{version}")
    print(f"  Download URL: {download_url}")
    print()

    # Download
    archive_path = install_dir / "packages" / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    def _verify(path):
        if expected_sha256:
            return _sha256(path) == expected_sha256
        if expected_md5:
            return _md5(path) == expected_md5
        return None  # nothing to verify against

    need_download = True
    if archive_path.exists():
        ok = _verify(archive_path)
        if ok is True:
            print("Package already downloaded (checksum verified)")
            need_download = False
        elif ok is None:
            print("Package already downloaded")
            need_download = False

    if need_download:
        downloaded = False
        try:
            _download(download_url, archive_path)
            downloaded = True
        except RuntimeError as exc:
            print(f"\nWARNING: GitHub download failed: {exc}")
            if fota_url:
                print(f"  Falling back to OTA server: {fota_url}")
                try:
                    archive_name = fota_url.rsplit("/", 1)[-1]
                    archive_path = install_dir / "packages" / archive_name
                    _download(fota_url, archive_path)
                    download_url = fota_url
                    expected_sha256 = ""  # OTA uses md5
                    downloaded = True
                except RuntimeError as exc2:
                    print(f"\nERROR: {exc2}")
                    return False
            else:
                print(f"\nERROR: {exc}")
                return False

        if downloaded:
            ok = _verify(archive_path)
            if ok is False:
                print("WARNING: checksum mismatch — file may be corrupted")
            elif ok is True:
                print("  [OK] checksum verified")

    # Stop running server before overwriting binary
    from .service import _is_running, do_stop
    running, _pid = _is_running()
    if running:
        print("Stopping running server before upgrade...")
        do_stop()

    # Extract
    print("Extracting...")
    try:
        _extract(archive_path, install_dir)
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return False

    # Init config
    print("Initializing config...")
    try:
        _init_config(install_dir)
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return False

    # Copy skill docs
    _copy_skill_docs(install_dir)

    # Write version info
    data_dir = install_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    version_info = {
        "version": version,
        "platform": f"{os_name}-{arch}",
        "fota_type": fota_type,
        "package": archive_name,
    }
    try:
        (data_dir / "version.json").write_text(
            json.dumps(version_info, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("Cannot write version file: %s", exc)

    print()
    print(f"FeyaGate Skill v{version} installed successfully!")
    print(f"  Install dir: {install_dir}")
    print()
    print("Next steps:")
    print(f"  1. feyagate start          # Start MCP server")
    print(f"  2. feyagate install-claude # Install for Claude Code")
    print(f"  3. feyagate auth           # Authorize Xiaomi account")
    print(f"  4. feyagate status         # Check server status")
    return True
