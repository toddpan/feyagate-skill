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

from . import (
    FOTA_URL,
    MILOCO_DOWNLOAD_URLS,
    SERVER_BINARY_VERSION,
    VERIFY_MILOCO_CHECKSUM,
    __version__,
    resolve_install_dir,
    save_install_dir,
)

logger = logging.getLogger(__name__)

FOTA_TYPE_MAP = {
    ("Linux", "x86_64"): "feyagate-skill-linux-x64",
    ("Linux", "amd64"): "feyagate-skill-linux-x64",
    ("Darwin", "x86_64"): "feyagate-skill-mac-x64",
    ("Darwin", "arm64"): "feyagate-skill-mac-arm64",
    # fota.json uses the -x64 suffix for Windows (feyagate-skill-win-x64);
    # without it the OTA fallback lookup never matches on Windows.
    ("Windows", "AMD64"): "feyagate-skill-win-x64",
    ("Windows", "ARM64"): "feyagate-skill-win-x64",
}


def _resolve_miloco_download_url():
    """Return the manually configured download URL for the current platform."""
    key = (platform.system(), platform.machine())
    url = MILOCO_DOWNLOAD_URLS.get(key)
    if not url:
        raise RuntimeError(
            f"Unsupported platform for miloco download URL: {key[0]}-{key[1]}"
        )
    return url, url.rsplit("/", 1)[-1]


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


def _validate_install_dir(install_dir):
    """Reject dangerous install directories.

    do_setup may rmtree (webui) and overwrite under install_dir, so guard
    against pointing it at filesystem root, common system dirs, or the bare
    home directory. install_dir is an already-resolved absolute Path.

    Raises:
        RuntimeError: if the directory is unsafe.
    """
    p = Path(install_dir).resolve()
    home = Path(os.path.expanduser("~")).resolve()

    # Filesystem / drive root (cross-platform: root's parent is itself).
    if p.parent == p:
        raise RuntimeError(f"refusing filesystem root as install dir: {p}")

    # The home directory itself (subdirs like ~/.feyagate are fine).
    if p == home:
        raise RuntimeError(
            f"refusing to install directly into home dir ({home}); "
            "use a subdirectory such as ~/.feyagate"
        )

    # Common POSIX system directories (no-op on Windows paths).
    dangerous = {
        "/root", "/home", "/usr", "/bin", "/sbin", "/etc", "/var",
        "/tmp", "/opt", "/lib", "/lib64", "/boot", "/dev", "/proc", "/sys",
    }
    if p.as_posix() in dangerous:
        raise RuntimeError(f"refusing dangerous system directory: {p}")


def do_setup(install_dir=None, local_package=None):
    """Download and install the MCP server binary.

    Args:
        install_dir: Target install directory (default: resolved ~/.feyagate).
        local_package: Path to a pre-downloaded archive. When given, skips all
            network access and extracts this archive directly — used by the
            clone/offline path (scripts/setup.sh) to reuse this one installer
            instead of a parallel shell implementation.

    Returns:
        True on success, False on failure.
    """
    install_dir = resolve_install_dir(install_dir)
    try:
        _validate_install_dir(install_dir)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return False
    install_dir.mkdir(parents=True, exist_ok=True)
    # Record the chosen location so start/stop/status find it later.
    save_install_dir(install_dir)

    fota_type, os_name, arch = _detect_fota_type()
    print("FeyaGate Skill Setup")
    print(f"  Platform: {os_name}-{arch}")
    print(f"  Install:  {install_dir}")
    print()

    # Binary version is pinned in __init__.py (SERVER_BINARY_VERSION), decoupled
    # from the Python package version. Bump it there only when a binary release
    # exists for all platforms.
    version = SERVER_BINARY_VERSION

    # ── Offline path: a local archive was supplied; skip all network access. ──
    if local_package is not None:
        archive_path = Path(local_package)
        if not archive_path.is_file():
            print(f"\nERROR: local package not found: {archive_path}")
            return False
        archive_name = archive_path.name
        print(f"  Local package: {archive_path}")
        if VERIFY_MILOCO_CHECKSUM:
            # Best-effort checksum against a sibling .sha256 sidecar, if present.
            sidecar = Path(str(archive_path) + ".sha256")
            if sidecar.is_file():
                try:
                    want = sidecar.read_text(encoding="utf-8").strip().split()[0].lower()
                    if _sha256(archive_path) == want:
                        print("  [OK] checksum verified (local .sha256)")
                    else:
                        print("\nERROR: local package checksum mismatch — refusing to install")
                        return False
                except (OSError, IndexError):
                    print("  [!] could not read local .sha256 — skipping integrity check")
            else:
                print("  [!] no local checksum — skipping integrity check")
        else:
            print("  [!] checksum verification disabled for this release")
        return _finish_setup(
            archive_path, archive_name, install_dir, version,
            os_name, arch, fota_type,
        )

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

    # Primary source: GitHub Releases. Use an explicit per-platform URL map
    # maintained by hand for each binary release to avoid filename inference
    # mismatches.
    try:
        download_url, archive_name = _resolve_miloco_download_url()
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return False
    expected_sha256 = _fetch_sha256(download_url + ".sha256") if VERIFY_MILOCO_CHECKSUM else ""

    print(f"  Version:      v{version}")
    print(f"  Download URL: {download_url}")
    print()

    # Download
    archive_path = install_dir / "packages" / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    def _verify(path):
        if not VERIFY_MILOCO_CHECKSUM:
            return None
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
            if not downloaded and fota_url:
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

            if not downloaded:
                print(f"\nERROR: {exc}")
                return False

        if downloaded:
            ok = _verify(archive_path)
            if ok is False:
                # Corrupt or tampered package: delete and abort rather than
                # extracting/executing untrusted bytes.
                try:
                    archive_path.unlink()
                except OSError:
                    pass
                print(
                    "\nERROR: checksum mismatch — downloaded package is corrupt "
                    "or tampered. Deleted. Please re-run setup."
                )
                return False
            elif ok is True:
                print("  [OK] checksum verified")
            else:
                print("  [!] no checksum available — skipping integrity check")

    return _finish_setup(
        archive_path, archive_name, install_dir, version,
        os_name, arch, fota_type,
    )


def _finish_setup(archive_path, archive_name, install_dir, version,
                  os_name, arch, fota_type):
    """Common tail shared by the online and offline setup paths:
    stop running server → extract → init config → copy docs → write version.

    Returns True on success, False on failure.
    """
    # Stop running server before overwriting binary
    from .service import _is_running, do_stop
    running, _ = _is_running()
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
