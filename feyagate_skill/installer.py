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

from . import FOTA_URL, __version__

logger = logging.getLogger(__name__)

FOTA_TYPE_MAP = {
    ("Linux", "x86_64"): "feyagate-skill-linux-x64",
    ("Linux", "amd64"): "feyagate-skill-linux-x64",
    ("Darwin", "x86_64"): "feyagate-skill-mac-x64",
    ("Darwin", "arm64"): "feyagate-skill-mac-arm64",
    ("Windows", "AMD64"): "feyagate-skill-win",
    ("Windows", "ARM64"): "feyagate-skill-win",
}


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

        # Find inner directory
        entries = list(Path(tmp).iterdir())
        inner = Path(tmp)
        if len(entries) == 1 and entries[0].is_dir():
            inner = entries[0]

        # Deploy binary
        bin_dir = install_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        found_binary = False
        for candidate in ["miloco-mcp-server", "bin/miloco-mcp-server"]:
            src = inner / candidate
            if src.exists():
                dest = bin_dir / "miloco-mcp-server"
                shutil.copy2(src, dest)
                dest.chmod(0o755)
                print(f"  [OK] bin/miloco-mcp-server")
                found_binary = True
                break

        if not found_binary:
            raise RuntimeError(
                f"No executable found in archive. Contents: {[e.name for e in inner.iterdir()]}"
            )

        # Deploy libraries
        lib_dir = install_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        inner_lib = inner / "lib"
        lib_count = 0
        if inner_lib.is_dir():
            for f in inner_lib.iterdir():
                if f.is_file():
                    shutil.copy2(f, lib_dir / f.name)
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
    print("FeyaGate Skill Setup")
    print(f"  Platform: {os_name}-{arch}")
    print(f"  Install:  {install_dir}")
    print()

    # Fetch version info
    print("Fetching latest version info...")
    try:
        fota_data = _fetch_fota()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return False

    # Find matching entry
    entry = None
    for item in fota_data:
        if item.get("type") == fota_type:
            entry = item
            break

    if not entry:
        print(f"ERROR: No release found for {fota_type}")
        available = [i["type"] for i in fota_data if "feyagate-skill" in i.get("type", "")]
        print(f"  Available: {', '.join(available)}")
        return False

    version = entry["version"]
    download_url = entry["url"]
    expected_md5 = entry.get("md5", "")

    print(f"  Latest version: {version}")
    print(f"  Download URL: {download_url}")
    print()

    # Download
    archive_name = download_url.rsplit("/", 1)[-1]
    archive_path = install_dir / "packages" / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    need_download = True
    if archive_path.exists() and expected_md5:
        local_md5 = _md5(archive_path)
        if local_md5 == expected_md5:
            print("Package already downloaded (MD5 verified)")
            need_download = False

    if need_download:
        try:
            _download(download_url, archive_path)
        except RuntimeError as exc:
            print(f"\nERROR: {exc}")
            return False

        # Verify MD5
        if expected_md5:
            local_md5 = _md5(archive_path)
            if local_md5 != expected_md5:
                print(f"WARNING: MD5 mismatch (expected {expected_md5}, got {local_md5})")
                print("  File may be corrupted")

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
