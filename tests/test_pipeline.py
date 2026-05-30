# PROMPT: Test a trajectory-based retail tracker without loading a computer vision model.
# CHANGES MADE: Focused on deterministic threshold crossing, zone dwell, and schema emission.
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from pipeline.correlate_pos import add_abandonment_events
from pipeline.emit import EventEmitter
from pipeline.run_all import sort_events
from pipeline.tracker import BehaviourTracker


def test_entry_and_zone_dwell_events(tmp_path):
    output = tmp_path / "events.jsonl"
    emitter = EventEmitter(output, "STORE_BLR_002", "CAM_ENTRY_01")
    tracker = BehaviourTracker("CAM_ENTRY_01", "entry", {"DOOR": [0, 0, 500, 800]}, threshold_y=100)
    now = datetime.now(timezone.utc)
    tracker.update(1, (50, 90), 0.8, now, emitter.emit)
    tracker.update(1, (50, 110), 0.7, now + timedelta(seconds=1), emitter.emit)
    tracker.update(1, (50, 120), 0.7, now + timedelta(seconds=31), emitter.emit)
    events = [json.loads(line) for line in output.read_text().splitlines()]
    assert {row["event_type"] for row in events} >= {"ENTRY", "ZONE_ENTER", "ZONE_DWELL"}
    assert all(row["event_id"] for row in events)
    assert all(0 <= row["confidence"] <= 1 for row in events)


def test_pos_correlation_adds_billing_abandonment(tmp_path):
    output = tmp_path / "events.jsonl"
    pos = tmp_path / "pos.csv"
    emitter = EventEmitter(output, "STORE_BLR_002", "CAM_BILLING_01")
    now = datetime.now(timezone.utc)
    emitter.emit("VIS_1", "BILLING_QUEUE_JOIN", now, zone_id="BILLING", metadata={"queue_depth": 2})
    emitter.emit("VIS_1", "ZONE_EXIT", now + timedelta(minutes=1), zone_id="BILLING")
    pos.write_text("store_id,transaction_id,timestamp,basket_value_inr\n", encoding="utf-8")
    assert add_abandonment_events(output, pos) == 1
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert any(row["event_type"] == "BILLING_QUEUE_ABANDON" for row in rows)
    assert all(rows[index]["timestamp"] <= rows[index + 1]["timestamp"] for index in range(len(rows) - 1))
    assert add_abandonment_events(output, pos) == 0


def test_exit_reentry_and_idle_zone_close(tmp_path):
    output = tmp_path / "events.jsonl"
    emitter = EventEmitter(output, "STORE_BLR_002", "CAM_ENTRY_01")
    tracker = BehaviourTracker("CAM_ENTRY_01", "entry", {"DOOR": [0, 0, 500, 800]}, threshold_y=100)
    now = datetime.now(timezone.utc)
    tracker.update(1, (50, 110), 0.9, now, emitter.emit)
    tracker.update(1, (50, 90), 0.8, now + timedelta(seconds=3), emitter.emit)
    tracker.update(2, (55, 90), 0.8, now + timedelta(seconds=5), emitter.emit)
    tracker.update(2, (55, 110), 0.7, now + timedelta(seconds=8), emitter.emit)
    tracker.prune(now + timedelta(seconds=20), emitter.emit)
    events = [json.loads(line) for line in output.read_text().splitlines()]
    assert {"EXIT", "REENTRY", "ZONE_EXIT"} <= {row["event_type"] for row in events}
    exited = next(row for row in events if row["event_type"] == "EXIT")
    reentered = next(row for row in events if row["event_type"] == "REENTRY")
    assert exited["visitor_id"] == reentered["visitor_id"]


def test_sort_events_orders_jsonl_by_timestamp(tmp_path):
    output = tmp_path / "events.jsonl"
    rows = [
        {"event_id": "b", "timestamp": "2026-01-02T00:00:00Z"},
        {"event_id": "a", "timestamp": "2026-01-01T00:00:00Z"},
    ]
    output.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    sort_events(output)
    sorted_rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["event_id"] for row in sorted_rows] == ["a", "b"]


def test_sort_events_orders_fractional_timestamp_after_whole_second(tmp_path):
    output = tmp_path / "events.jsonl"
    rows = [
        {"event_id": "later", "timestamp": "2026-01-01T00:00:00.500000Z"},
        {"event_id": "earlier", "timestamp": "2026-01-01T00:00:00Z"},
    ]
    output.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    sort_events(output)
    sorted_rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["event_id"] for row in sorted_rows] == ["earlier", "later"]
