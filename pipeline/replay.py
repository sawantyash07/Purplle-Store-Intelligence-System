from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay JSONL events into the API.")
    parser.add_argument("--events", type=Path, default=Path("data/events.jsonl"))
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between batches for live dashboard simulation.")
    parser.add_argument("--shift-to-now", action="store_true", help="Preserve event spacing but replay with current timestamps.")
    args = parser.parse_args()
    events = [json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.shift_to_now and events:
        first = datetime.fromisoformat(events[0]["timestamp"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        for event in events:
            original = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            event["timestamp"] = (now + (original - first)).isoformat().replace("+00:00", "Z")
    for index in range(0, len(events), args.batch_size):
        batch = events[index:index + args.batch_size]
        response = requests.post(f"{args.api}/events/ingest", json=batch, timeout=15)
        response.raise_for_status()
        print(json.dumps(response.json()))
        time.sleep(args.delay)


if __name__ == "__main__":
    main()
