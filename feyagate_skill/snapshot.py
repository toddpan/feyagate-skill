"""Camera snapshot capture tool."""

import base64
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from . import MCP_DEFAULT_HOST, MCP_DEFAULT_PORT
from .mcp import mcp_call

logger = logging.getLogger(__name__)

def do_snapshot(host=None, port=None, camera_id=None, connect=False,
                channel=0, count=1, output_dir=None, list_cameras=False):
    """Capture camera snapshots via MCP server.

    Args:
        host: MCP server host.
        port: MCP server port.
        camera_id: Camera DID to capture (required unless --list).
        connect: Connect to camera before snapshot.
        channel: Camera channel number.
        count: Number of frames to capture.
        output_dir: Output directory for saved images.
        list_cameras: If True, list available cameras instead.
    """
    host = host or MCP_DEFAULT_HOST
    port = port or MCP_DEFAULT_PORT

    if output_dir is None:
        output_dir = Path.home() / ".feyagate" / "data" / "snapshots"
    output_dir = Path(output_dir)

    if list_cameras:
        try:
            result = mcp_call(host, port, "xiaomi/camera_list")
        except Exception as exc:
            print(f"Error listing cameras: {exc}")
            return
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        cameras = result.get("cameras", [])
        if not cameras:
            print("No cameras found.")
            return
        print(f"Found {len(cameras)} camera(s):\n")
        for cam in cameras:
            status_icon = {"connected": "[ON]", "connecting": "[..]"}.get(
                cam.get("camera_status", ""), "[--]"
            )
            print(f"  {status_icon} {cam.get('name', 'unknown')}")
            print(f"    DID:      {cam.get('did', '?')}")
            print(f"    Model:    {cam.get('model', '?')}")
            print(f"    Location: {cam.get('home_name', '?')} / {cam.get('room_name', '?')}")
            print()
        return

    if not camera_id:
        print("ERROR: --camera-id required (use --list to see cameras)")
        return

    if connect:
        print(f"Connecting to camera {camera_id}...")
        try:
            result = mcp_call(host, port, "xiaomi/camera_connect", {"camera_id": camera_id})
        except Exception as exc:
            print(f"Connection failed: {exc}")
            return
        if result.get("success"):
            print("Connected. Waiting for frames...")
            time.sleep(3)
        else:
            print(f"Connection failed: {result}")
            return

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Cannot create output directory {output_dir}: {exc}")
        return

    try:
        result = mcp_call(host, port, "xiaomi/camera_snapshot", {
            "camera_id": camera_id, "channel": channel, "count": count,
        })
    except Exception as exc:
        print(f"Snapshot error: {exc}")
        return

    if "error" in result:
        print(f"Snapshot error: {result['error']}")
        return

    images = result.get("images", [])
    if not images:
        print("No images returned. Is camera connected?")
        return

    success_count = 0
    for i, img in enumerate(images):
        data_url = img.get("data_url", "")
        if not data_url:
            logger.warning("Empty data_url in image %d", i)
            continue
        timestamp = img.get("timestamp", int(time.time()))
        try:
            b64_data = data_url.split(",", 1)[1] if "," in data_url else data_url
            jpeg_bytes = base64.b64decode(b64_data)
        except Exception as exc:
            logger.warning("Failed to decode image %d: %s", i, exc)
            continue

        dt = datetime.fromtimestamp(timestamp)
        filename = f"{camera_id}_ch{channel}_{dt.strftime('%Y%m%d_%H%M%S')}_{i:02d}.jpg"
        filepath = output_dir / filename

        try:
            filepath.write_bytes(jpeg_bytes)
            print(f"  Saved: {filepath} ({len(jpeg_bytes)/1024:.1f} KB)")
            success_count += 1
        except OSError as exc:
            logger.warning("Failed to save image %s: %s", filepath, exc)

    print(f"\nCaptured {success_count}/{len(images)} snapshot(s)")
