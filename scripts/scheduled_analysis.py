#!/usr/bin/env python3
"""
Scheduled camera snapshot capture with AI analysis preparation.

Captures snapshots at configurable intervals, saves images with metadata,
and outputs analysis-ready JSONL for downstream VLM/LLM processing.

Usage (run from miloco-camera/ package root):
    python3 scripts/scheduled_analysis.py --camera-id CAMERA_DID --interval 300
    python3 scripts/scheduled_analysis.py --camera-id CAM1 --camera-id CAM2 \
        --interval 60 --prompt "Describe the scene. Flag security concerns."
    python3 scripts/scheduled_analysis.py --camera-id CAM1 --auto-connect --one-shot
"""

import argparse
import base64
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "data" / "analysis"

running = True


def signal_handler(signum, frame):
    global running
    print("\nShutdown signal received...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
            return json.loads(json.loads(resp.read())["result"]["content"][0]["text"])
    except Exception:
        return {"error": "request failed"}


def ensure_connected(host, port, camera_id):
    status = mcp_call(host, port, "xiaomi/camera_status", {"camera_id": camera_id})
    if status.get("status") == "connected" and status.get("buffered_frames", 0) > 0:
        return True
    mcp_call(host, port, "xiaomi/camera_connect", {"camera_id": camera_id})
    time.sleep(3)
    status = mcp_call(host, port, "xiaomi/camera_status", {"camera_id": camera_id})
    return status.get("status") == "connected"


def capture_and_save(host, port, camera_id, channel, output_dir):
    result = mcp_call(host, port, "xiaomi/camera_snapshot", {
        "camera_id": camera_id, "channel": channel, "count": 1,
    })
    images = result.get("images", [])
    if not images:
        return None

    img = images[0]
    data_url = img.get("data_url", "")
    timestamp = img.get("timestamp", int(time.time()))
    b64_data = data_url.split(",", 1)[1] if "," in data_url else data_url
    jpeg_bytes = base64.b64decode(b64_data)

    dt = datetime.fromtimestamp(timestamp)
    date_dir = output_dir / dt.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{camera_id}_ch{channel}_{dt.strftime('%H%M%S')}.jpg"
    filepath = date_dir / filename
    filepath.write_bytes(jpeg_bytes)

    return {
        "camera_id": camera_id,
        "channel": channel,
        "timestamp": timestamp,
        "datetime": dt.isoformat(),
        "image_path": str(filepath),
        "image_size_bytes": len(jpeg_bytes),
        "data_url": data_url,
    }


def write_analysis_record(output_dir, record, prompt):
    dt = datetime.fromtimestamp(record["timestamp"])
    date_dir = output_dir / dt.strftime("%Y-%m-%d")
    jsonl_path = date_dir / "analysis_queue.jsonl"

    entry = {
        "id": f"{record['camera_id']}_{record['timestamp']}",
        "camera_id": record["camera_id"],
        "channel": record["channel"],
        "timestamp": record["timestamp"],
        "datetime": record["datetime"],
        "image_path": record["image_path"],
        "prompt": prompt,
        "status": "pending",
    }

    with open(jsonl_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_cycle(host, port, camera_ids, channel, output_dir, prompt, auto_connect):
    captured = 0
    for cam_id in camera_ids:
        if auto_connect and not ensure_connected(host, port, cam_id):
            print(f"  [WARN] Cannot connect {cam_id}")
            continue

        record = capture_and_save(host, port, cam_id, channel, output_dir)
        if record:
            captured += 1
            kb = record["image_size_bytes"] / 1024
            print(f"  [{record['datetime']}] {cam_id}: {kb:.1f} KB")
            if prompt:
                write_analysis_record(output_dir, record, prompt)
        else:
            print(f"  [{datetime.now().isoformat()}] {cam_id}: no frame")

    return captured


def main():
    parser = argparse.ArgumentParser(description="Miloco Scheduled Camera Analysis")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=38080)
    parser.add_argument("--camera-id", action="append", required=True, help="Camera DID (repeatable)")
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--interval", type=int, default=300, help="Seconds between captures")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--prompt", default="", help="AI analysis prompt")
    parser.add_argument("--auto-connect", action="store_true")
    parser.add_argument("--max-runs", type=int, default=0, help="0 = unlimited")
    parser.add_argument("--one-shot", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== Miloco Scheduled Analysis ===")
    print(f"Cameras:  {', '.join(args.camera_id)}")
    print(f"Interval: {args.interval}s")
    print(f"Output:   {output_dir}")
    if args.prompt:
        print(f"Prompt:   {args.prompt[:80]}...")
    print()

    config_path = output_dir / "session_config.json"
    config_path.write_text(json.dumps({
        "cameras": args.camera_id, "channel": args.channel,
        "interval": args.interval, "prompt": args.prompt,
        "started_at": datetime.now().isoformat(),
    }, indent=2, ensure_ascii=False))

    run_count = 0
    total = 0

    while running:
        run_count += 1
        print(f"--- Cycle {run_count} [{datetime.now().strftime('%H:%M:%S')}] ---")
        total += run_cycle(
            args.host, args.port, args.camera_id,
            args.channel, output_dir, args.prompt, args.auto_connect,
        )

        if args.one_shot or (args.max_runs and run_count >= args.max_runs):
            break

        if running:
            wait_until = time.time() + args.interval
            while running and time.time() < wait_until:
                time.sleep(min(1, wait_until - time.time()))

    print(f"\n=== Done: {run_count} cycles, {total} images ===")
    summary = output_dir / "session_summary.json"
    summary.write_text(json.dumps({
        "total_cycles": run_count, "total_captures": total,
        "cameras": args.camera_id, "ended_at": datetime.now().isoformat(),
    }, indent=2))


if __name__ == "__main__":
    main()
