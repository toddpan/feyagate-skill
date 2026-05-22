"""Scheduled camera snapshot capture with AI analysis preparation."""

import base64
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from . import MCP_DEFAULT_HOST, MCP_DEFAULT_PORT
from .mcp import mcp_call

logger = logging.getLogger(__name__)

_running = True


# ---------------------------------------------------------------------------
# Signal handling (Windows doesn't support SIGTERM the same way)
# ---------------------------------------------------------------------------
def _signal_handler(signum, frame):
    global _running
    logger.info("Received signal %d, shutting down...", signum)
    _running = False


# Register SIGTERM (available on all platforms)
signal.signal(signal.SIGTERM, _signal_handler)
# SIGINT only on non-Windows (Windows uses different Ctrl+C handling)
if sys.platform != "win32":
    signal.signal(signal.SIGINT, _signal_handler)


def _ensure_connected(host, port, camera_id):
    try:
        status = mcp_call(host, port, "xiaomi/camera_status", {"camera_id": camera_id})
        if status.get("status") == "connected" and status.get("buffered_frames", 0) > 0:
            return True
    except Exception as exc:
        logger.warning("Status check failed for %s: %s", camera_id, exc)
    try:
        mcp_call(host, port, "xiaomi/camera_connect", {"camera_id": camera_id})
    except Exception as exc:
        logger.warning("Connection failed for %s: %s", camera_id, exc)
        return False
    time.sleep(3)
    try:
        status = mcp_call(host, port, "xiaomi/camera_status", {"camera_id": camera_id})
        return status.get("status") == "connected"
    except Exception as exc:
        logger.warning("Status check after connect failed: %s", exc)
        return False


def _capture_and_save(host, port, camera_id, channel, output_dir):
    """Capture a single snapshot and save to disk.

    Returns:
        Dict with capture metadata, or None on failure.
    """
    try:
        result = mcp_call(host, port, "xiaomi/camera_snapshot", {
            "camera_id": camera_id, "channel": channel, "count": 1,
        })
    except Exception as exc:
        logger.error("Snapshot call failed for %s: %s", camera_id, exc)
        return None

    images = result.get("images", [])
    if not images:
        return None

    img = images[0]
    data_url = img.get("data_url", "")
    if not data_url:
        logger.warning("Empty data_url for camera %s", camera_id)
        return None

    timestamp = img.get("timestamp", int(time.time()))
    try:
        b64_data = data_url.split(",", 1)[1] if "," in data_url else data_url
        jpeg_bytes = base64.b64decode(b64_data)
    except Exception as exc:
        logger.error("Failed to decode image from %s: %s", camera_id, exc)
        return None

    try:
        dt = datetime.fromtimestamp(timestamp)
        date_dir = output_dir / dt.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{camera_id}_ch{channel}_{dt.strftime('%H%M%S')}.jpg"
        filepath = date_dir / filename
        filepath.write_bytes(jpeg_bytes)
    except OSError as exc:
        logger.error("Failed to save image from %s: %s", camera_id, exc)
        return None

    return {
        "camera_id": camera_id, "channel": channel,
        "timestamp": timestamp, "datetime": dt.isoformat(),
        "image_path": str(filepath), "image_size_bytes": len(jpeg_bytes),
    }


def do_scheduled(host=None, port=None, camera_ids=None, channel=0,
                 interval=300, output_dir=None, prompt="",
                 auto_connect=False, max_runs=0, one_shot=False):
    """Run scheduled camera capture loop.

    Args:
        host: MCP server host.
        port: MCP server port.
        camera_ids: List of camera DIDs.
        channel: Camera channel.
        interval: Seconds between capture cycles.
        output_dir: Output directory.
        prompt: AI analysis prompt.
        auto_connect: Auto-connect cameras if needed.
        max_runs: Max cycles (0 = unlimited).
        one_shot: Run once and exit.
    """
    global _running

    host = host or MCP_DEFAULT_HOST
    port = port or MCP_DEFAULT_PORT

    if not camera_ids:
        print("ERROR: --camera-id required")
        return

    if output_dir is None:
        output_dir = Path.home() / ".feyagate" / "data" / "analysis"
    output_dir = Path(output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Cannot create output directory: {exc}")
        return

    print("=== FeyaGate Scheduled Analysis ===")
    print(f"  Cameras:  {', '.join(camera_ids)}")
    print(f"  Interval: {interval}s")
    print(f"  Output:   {output_dir}")
    print()

    run_count = 0
    total = 0

    while _running:
        run_count += 1
        print(f"--- Cycle {run_count} [{datetime.now().strftime('%H:%M:%S')}] ---")

        for cam_id in camera_ids:
            if auto_connect and not _ensure_connected(host, port, cam_id):
                print(f"  [WARN] Cannot connect {cam_id}")
                continue

            record = _capture_and_save(host, port, cam_id, channel, output_dir)
            if record:
                total += 1
                kb = record["image_size_bytes"] / 1024
                print(f"  [{record['datetime']}] {cam_id}: {kb:.1f} KB")

                if prompt:
                    try:
                        dt = datetime.fromtimestamp(record["timestamp"])
                        date_dir = output_dir / dt.strftime("%Y-%m-%d")
                        jsonl_path = date_dir / "analysis_queue.jsonl"
                        entry = {
                            "id": f"{cam_id}_{record['timestamp']}",
                            "camera_id": cam_id, "channel": channel,
                            "timestamp": record["timestamp"],
                            "datetime": record["datetime"],
                            "image_path": record["image_path"],
                            "prompt": prompt, "status": "pending",
                        }
                        with open(jsonl_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    except OSError as exc:
                        logger.error("Failed to write analysis queue: %s", exc)
            else:
                print(f"  [{datetime.now().isoformat()}] {cam_id}: no frame")

        if one_shot or (max_runs and run_count >= max_runs):
            break

        if _running:
            wait_until = time.time() + interval
            while _running and time.time() < wait_until:
                time.sleep(min(1, wait_until - time.time()))

    print(f"\nDone: {run_count} cycles, {total} images")
