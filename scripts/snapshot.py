#!/usr/bin/env python3
"""
Capture camera snapshots from Miloco MCP server and save as JPEG files.

Usage (run from miloco-camera/ package root):
    python3 scripts/snapshot.py --list
    python3 scripts/snapshot.py --camera-id CAMERA_DID
    python3 scripts/snapshot.py --connect CAMERA_DID --count 3
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "data" / "snapshots"


def mcp_call(host: str, port: int, tool: str, arguments: dict | None = None) -> dict:
    url = f"http://{host}:{port}/mcp/http"
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }
    req = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except URLError as e:
        return {"error": f"Connection failed: {e}"}

    if "error" in result:
        return result

    try:
        text = result["result"]["content"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError):
        return result


def list_cameras(host: str, port: int):
    result = mcp_call(host, port, "xiaomi/camera_list")
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    cameras = result.get("cameras", [])
    if not cameras:
        print("No cameras found. Check auth status with: bash scripts/health_check.sh")
        return

    print(f"Found {len(cameras)} camera(s):\n")
    for cam in cameras:
        status_icon = {"connected": "[ON]", "connecting": "[..]"}.get(cam.get("camera_status", ""), "[--]")
        print(f"  {status_icon} {cam.get('name', 'unknown')}")
        print(f"    DID:      {cam.get('did', '?')}")
        print(f"    Model:    {cam.get('model', '?')}")
        print(f"    Location: {cam.get('home_name', '?')} / {cam.get('room_name', '?')}")
        print(f"    Channels: {cam.get('channel_count', 1)}")
        print()


def connect_camera(host: str, port: int, camera_id: str) -> bool:
    print(f"Connecting to camera {camera_id}...")
    result = mcp_call(host, port, "xiaomi/camera_connect", {"camera_id": camera_id})
    if result.get("success"):
        print("Connected. Waiting for frames...")
        time.sleep(3)
        return True
    print(f"Connection failed: {result}")
    return False


def capture_snapshot(host, port, camera_id, channel=0, count=1, output_dir=None):
    output_dir = Path(output_dir or DEFAULT_OUTPUT)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = mcp_call(host, port, "xiaomi/camera_snapshot", {
        "camera_id": camera_id, "channel": channel, "count": count,
    })

    if "error" in result:
        print(f"Snapshot error: {result['error']}")
        return []

    images = result.get("images", [])
    if not images:
        print("No images returned. Is camera connected?")
        return []

    saved = []
    for i, img in enumerate(images):
        data_url = img.get("data_url", "")
        timestamp = img.get("timestamp", int(time.time()))
        b64_data = data_url.split(",", 1)[1] if "," in data_url else data_url
        jpeg_bytes = base64.b64decode(b64_data)

        dt = datetime.fromtimestamp(timestamp)
        filename = f"{camera_id}_ch{channel}_{dt.strftime('%Y%m%d_%H%M%S')}_{i:02d}.jpg"
        filepath = output_dir / filename

        filepath.write_bytes(jpeg_bytes)
        saved.append(str(filepath))
        print(f"  Saved: {filepath} ({len(jpeg_bytes)/1024:.1f} KB)")

    return saved


def main():
    parser = argparse.ArgumentParser(description="Miloco Camera Snapshot Tool")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=38080)
    parser.add_argument("--list", action="store_true", help="List cameras")
    parser.add_argument("--connect", metavar="CAMERA_ID", help="Connect then snapshot")
    parser.add_argument("--camera-id", help="Camera DID for snapshot")
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--count", type=int, default=1, help="Frames 1-10")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    if args.list:
        list_cameras(args.host, args.port)
        return

    if args.connect:
        if not connect_camera(args.host, args.port, args.connect):
            sys.exit(1)
        files = capture_snapshot(args.host, args.port, args.connect, args.channel, args.count, args.output_dir)
        if files:
            print(f"\nCaptured {len(files)} snapshot(s)")
        return

    if args.camera_id:
        files = capture_snapshot(args.host, args.port, args.camera_id, args.channel, args.count, args.output_dir)
        if files:
            print(f"\nCaptured {len(files)} snapshot(s)")
        else:
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
