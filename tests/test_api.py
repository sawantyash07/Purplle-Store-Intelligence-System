# PROMPT: Generate API tests for idempotent partial ingest, empty metrics, POS conversion,
# and session-level re-entry deduplication for a retail intelligence FastAPI service.
# CHANGES MADE: Added explicit malformed input and queue assertions to mirror the challenge.
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
import importlib
import sqlite3
from uuid import uuid4

import app.analytics as analytics
from fastapi.testclient import TestClient


def event(kind="ENTRY", visitor="VIS_1", zone=None, **extra):
    timestamp = extra.pop("timestamp", datetime.now(timezone.utc))
    return {
        "event_id": str(uuid4()),
        "store_id": "STORE_BLR_002",
        "camera_id": "CAM_ENTRY_01",
        "visitor_id": visitor,
        "event_type": kind,
        "timestamp": timestamp.isoformat(),
        "zone_id": zone,
        "dwell_ms": extra.pop("dwell_ms", 0),
        "is_staff": extra.pop("is_staff", False),
        "confidence": extra.pop("confidence", 0.91),
        "metadata": extra.pop("metadata", {}),
        **extra,
    }


def test_empty_store_metrics_are_zero(client):
    body = client.get("/stores/EMPTY/metrics").json()
    assert body["unique_visitors"] == 0
    assert body["conversion_rate"] == 0.0
    assert body["queue_depth"] == 0


def test_ingest_is_idempotent_and_partially_accepts(client):
    good = event()
    bad = {**event(), "confidence": 4}
    response = client.post("/events/ingest", json=[good, bad])
    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    assert response.json()["rejected"] == 1
    duplicate = client.post("/events/ingest", json=[good]).json()
    assert duplicate == {"accepted": 0, "duplicates": 1, "rejected": 0, "errors": []}


def test_metrics_funnel_and_pos_correlation(client):
    now = datetime.now(timezone.utc)
    events = [
        event("ENTRY", "VIS_A", timestamp=now - timedelta(minutes=4)),
        event("ZONE_ENTER", "VIS_A", "MAKEUP", timestamp=now - timedelta(minutes=3)),
        event("BILLING_QUEUE_JOIN", "VIS_A", "BILLING", timestamp=now - timedelta(minutes=2), metadata={"queue_depth": 3}),
        event("REENTRY", "VIS_A", timestamp=now - timedelta(minutes=1)),
        event("ENTRY", "STAFF", timestamp=now, is_staff=True),
    ]
    assert client.post("/events/ingest", json=events).json()["accepted"] == 5
    txn = {"store_id": "STORE_BLR_002", "transaction_id": "TXN_1", "timestamp": now.isoformat(), "basket_value_inr": 500}
    assert client.post("/pos/ingest", json=[txn]).json()["accepted"] == 1
    metrics = client.get("/stores/STORE_BLR_002/metrics").json()
    assert metrics["unique_visitors"] == 1
    assert metrics["converted_visitors"] == 1
    assert metrics["conversion_rate"] == 1.0
    assert metrics["queue_depth"] == 3
    stages = client.get("/stores/STORE_BLR_002/funnel").json()["stages"]
    assert [stage["count"] for stage in stages] == [1, 1, 1, 1]


def test_queue_spike_anomaly(client):
    assert client.post("/events/ingest", json=[
        event("ENTRY"),
        event("BILLING_QUEUE_JOIN", zone="BILLING", metadata={"queue_depth": 8}),
    ]).status_code == 200
    anomaly = client.get("/stores/STORE_BLR_002/anomalies").json()["active_anomalies"][0]
    assert anomaly["type"] == "BILLING_QUEUE_SPIKE"
    assert anomaly["severity"] == "CRITICAL"


def test_invalid_json_and_oversized_batch_are_client_errors(client):
    assert client.post("/events/ingest", content="{", headers={"content-type": "application/json"}).status_code == 400
    assert client.post("/events/ingest", json=[event() for _ in range(501)]).status_code == 413
    assert client.post("/events/ingest", json=[]).json()["accepted"] == 0
    assert client.post("/events/ingest", json=[{"event_id": "incomplete"}]).json()["rejected"] == 1


def test_all_staff_events_are_excluded(client):
    assert client.post("/events/ingest", json=[
        event("ENTRY", "STAFF_1", is_staff=True),
        event("ZONE_ENTER", "STAFF_1", "MAKEUP", is_staff=True),
    ]).json()["accepted"] == 2
    metrics = client.get("/stores/STORE_BLR_002/metrics").json()
    assert metrics["unique_visitors"] == 0
    assert metrics["conversion_rate"] == 0.0


def test_heatmap_and_dead_zone_anomaly(client):
    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=1)
    client.post("/events/ingest", json=[
        event("ENTRY", "VIS_1", timestamp=old),
        event("ZONE_ENTER", "VIS_1", "MAKEUP", timestamp=old),
        event("ZONE_DWELL", "VIS_1", "MAKEUP", timestamp=old, dwell_ms=30_000),
    ])
    heatmap = client.get("/stores/STORE_BLR_002/heatmap").json()
    assert heatmap["data_confidence"] == "LOW"
    assert heatmap["zones"][0]["intensity"] == 100.0
    assert heatmap["zones"][0]["avg_dwell_ms"] == 30_000
    anomalies = client.get("/stores/STORE_BLR_002/anomalies").json()["active_anomalies"]
    assert any(item["type"] == "DEAD_ZONE" and item["details"]["zone_id"] == "MAKEUP" for item in anomalies)


def test_health_reports_stale_feed(client):
    old = datetime.now(timezone.utc) - timedelta(minutes=11)
    client.post("/events/ingest", json=[event(timestamp=old)])
    health = client.get("/health").json()
    assert health["status"] == "degraded"
    assert health["stores"]["STORE_BLR_002"]["status"] == "STALE_FEED"


def test_conversion_drop_against_seven_day_average(client, monkeypatch):
    now = datetime(2026, 5, 30, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(analytics, "_now", lambda: now)
    historical = []
    transactions = []
    for days_ago in range(1, 8):
        day = now - timedelta(days=days_ago, hours=2)
        visitor = f"HIST_{days_ago}"
        historical.extend([
            event("ENTRY", visitor, timestamp=day),
            event("BILLING_QUEUE_JOIN", visitor, "BILLING", timestamp=day + timedelta(minutes=1), metadata={"queue_depth": 1}),
        ])
        transactions.append({"store_id": "STORE_BLR_002", "transaction_id": f"TXN_{days_ago}", "timestamp": (day + timedelta(minutes=2)).isoformat(), "basket_value_inr": 100})
    historical.append(event("ENTRY", "TODAY", timestamp=now - timedelta(minutes=1)))
    client.post("/events/ingest", json=historical)
    client.post("/pos/ingest", json=transactions)
    anomalies = client.get("/stores/STORE_BLR_002/anomalies").json()["active_anomalies"]
    assert any(item["type"] == "CONVERSION_DROP" for item in anomalies)


def test_queue_spike_uses_rolling_baseline(client):
    now = datetime.now(timezone.utc)
    events = [event("ENTRY", "VIS")]
    events.extend(
        event("BILLING_QUEUE_JOIN", f"VIS_{index}", "BILLING", timestamp=now + timedelta(seconds=index), metadata={"queue_depth": depth})
        for index, depth in enumerate([1, 2, 1, 6])
    )
    client.post("/events/ingest", json=events)
    anomaly = next(item for item in client.get("/stores/STORE_BLR_002/anomalies").json()["active_anomalies"] if item["type"] == "BILLING_QUEUE_SPIKE")
    assert anomaly["details"]["detection_mode"] == "ROLLING_BASELINE"


def test_database_failure_returns_structured_503(client, monkeypatch):
    main_module = importlib.import_module("app.main")

    @contextmanager
    def unavailable_database():
        raise sqlite3.OperationalError("database unavailable")
        yield

    monkeypatch.setattr(main_module, "database", unavailable_database)
    response = client.post("/events/ingest", json=[event()])
    assert response.status_code == 503
    assert response.json()["error"] == "SERVICE_UNAVAILABLE"
