from __future__ import annotations

import argparse
import csv
import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def add_abandonment_events(events_path: Path, pos_path: Path) -> int:
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    with pos_path.open(encoding="utf-8-sig", newline="") as handle:
        transactions = list(csv.DictReader(handle))
    joins: dict[tuple[str, str], dict] = {}
    exits: dict[tuple[str, str], list[dict]] = defaultdict(list)
    abandoned: set[tuple[str, str]] = set()
    for event in events:
        key = (event["store_id"], event["visitor_id"])
        if event["event_type"] == "BILLING_QUEUE_JOIN":
            joins[key] = event
        elif event["event_type"] == "ZONE_EXIT" and event["zone_id"] == "BILLING":
            exits[key].append(event)
        elif event["event_type"] == "BILLING_QUEUE_ABANDON":
            abandoned.add(key)
    added = []
    for key, join in joins.items():
        if key in abandoned:
            continue
        store_id, _ = key
        left = exits.get(key, [])
        if not left:
            continue
        exited = left[-1]
        joined_at, exited_at = _time(join["timestamp"]), _time(exited["timestamp"])
        converted = any(
            transaction["store_id"] == store_id
            and joined_at <= _time(transaction["timestamp"]) <= exited_at + timedelta(minutes=5)
            for transaction in transactions
        )
        if not converted:
            added.append({
                **exited,
                "event_id": str(uuid.uuid4()),
                "event_type": "BILLING_QUEUE_ABANDON",
                "dwell_ms": 0,
                "metadata": {**exited["metadata"], "queue_depth": join["metadata"].get("queue_depth")},
            })
    events.extend(added)
    events.sort(key=lambda event: (event["timestamp"], event["event_id"]))
    events_path.write_text(
        "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )
    return len(added)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append billing abandonment events after POS correlation.")
    parser.add_argument("--events", type=Path, default=Path("data/events.jsonl"))
    parser.add_argument("--pos", type=Path, default=Path("data/pos_transactions.csv"))
    args = parser.parse_args()
    print(json.dumps({"billing_queue_abandon_events_added": add_abandonment_events(args.events, args.pos)}))


if __name__ == "__main__":
    main()
