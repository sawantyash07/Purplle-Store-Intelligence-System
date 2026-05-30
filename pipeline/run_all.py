from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from pipeline.detect import load_config, process_video


def sort_events(output: Path) -> None:
    events = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    events.sort(key=lambda event: (datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")), event["event_id"]))
    output.write_text("".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Process every configured CCTV clip found in a directory.")
    parser.add_argument("--clips", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/store_layout.json"))
    parser.add_argument("--output", type=Path, default=Path("data/events.jsonl"))
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--limit-frames", type=int)
    args = parser.parse_args()
    config = load_config(args.config)
    args.output.unlink(missing_ok=True)
    total = 0
    for stem in config["cameras"]:
        video = args.clips / f"{stem}.mp4"
        if not video.exists():
            print(f"skip: {video} not found")
            continue
        count = process_video(video, args.output, config, model_name=args.model, stride=args.stride, limit_frames=args.limit_frames)
        total += count
        print(f"processed: {video.name}, events={count}")
    if args.output.exists():
        sort_events(args.output)
    print(f"complete: events={total}, output={args.output}")


if __name__ == "__main__":
    main()
