from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import fmean, pstdev
from typing import Iterable

from app.db import database


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _rows(store_id: str, start: datetime | None = None) -> list[dict]:
    query = "SELECT * FROM events WHERE store_id=? AND is_staff=0"
    params: list[object] = [store_id]
    if start:
        query += " AND timestamp>=?"
        params.append(_iso(start))
    query += " ORDER BY timestamp"
    with database() as db:
        return [dict(row) for row in db.execute(query, params)]


def _transactions(store_id: str, start: datetime | None = None) -> list[dict]:
    query = "SELECT * FROM transactions WHERE store_id=?"
    params: list[object] = [store_id]
    if start:
        query += " AND timestamp>=?"
        params.append(_iso(start))
    query += " ORDER BY timestamp"
    with database() as db:
        return [dict(row) for row in db.execute(query, params)]


def _session_sets(rows: Iterable[dict], transactions: Iterable[dict]) -> dict[str, set[str]]:
    stages = {"entry": set(), "zone_visit": set(), "billing_queue": set(), "purchase": set()}
    billing_times: dict[str, list[datetime]] = defaultdict(list)
    for row in rows:
        visitor = row["visitor_id"]
        event_type = row["event_type"]
        if event_type in {"ENTRY", "REENTRY"}:
            stages["entry"].add(visitor)
        if event_type in {"ZONE_ENTER", "ZONE_DWELL", "ZONE_EXIT"}:
            stages["zone_visit"].add(visitor)
        if event_type == "BILLING_QUEUE_JOIN" or row["zone_id"] == "BILLING":
            stages["billing_queue"].add(visitor)
            billing_times[visitor].append(datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")))
    for transaction in transactions:
        txn_time = datetime.fromisoformat(transaction["timestamp"].replace("Z", "+00:00"))
        candidates = [
            (txn_time - seen, visitor)
            for visitor, visits in billing_times.items()
            for seen in visits
            if timedelta(0) <= txn_time - seen <= timedelta(minutes=5) and visitor not in stages["purchase"]
        ]
        if candidates:
            stages["purchase"].add(min(candidates)[1])
    # Floor cameras may produce local tracker IDs that cannot safely be linked
    # to an entrance session. Keep the funnel conservative instead of inflating it.
    if stages["entry"]:
        stages["zone_visit"] &= stages["entry"]
        stages["billing_queue"] &= stages["entry"]
        stages["purchase"] &= stages["entry"]
    return stages


def metrics(store_id: str) -> dict:
    start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = _rows(store_id, start)
    transactions = _transactions(store_id, start)
    stages = _session_sets(rows, transactions)
    dwells: dict[str, list[int]] = defaultdict(list)
    queue_depth = 0
    explicit_abandons: set[str] = set()
    joined_visitors: set[str] = set()
    for row in rows:
        if row["event_type"] == "ZONE_DWELL" and row["zone_id"]:
            dwells[row["zone_id"]].append(row["dwell_ms"])
        if row["event_type"] == "BILLING_QUEUE_JOIN":
            joined_visitors.add(row["visitor_id"])
            queue_depth = json.loads(row["metadata_json"]).get("queue_depth") or 0
        if row["event_type"] == "BILLING_QUEUE_ABANDON":
            explicit_abandons.add(row["visitor_id"])
    abandons = max(len(explicit_abandons), len(stages["billing_queue"] - stages["purchase"]))
    visitors = len(stages["entry"])
    return {
        "store_id": store_id,
        "window": "today",
        "unique_visitors": visitors,
        "converted_visitors": len(stages["purchase"]),
        "conversion_rate": round(len(stages["purchase"]) / visitors, 4) if visitors else 0.0,
        "avg_dwell_ms_by_zone": {zone: round(sum(values) / len(values), 2) for zone, values in dwells.items()},
        "queue_depth": queue_depth,
        "abandonment_rate": round(abandons / len(joined_visitors), 4) if joined_visitors else 0.0,
    }


def funnel(store_id: str) -> dict:
    start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    stages = _session_sets(_rows(store_id, start), _transactions(store_id, start))
    names = ["entry", "zone_visit", "billing_queue", "purchase"]
    result = []
    previous = None
    for name in names:
        count = len(stages[name])
        drop = 0.0 if previous in (None, 0) else round((previous - count) / previous * 100, 2)
        result.append({"stage": name, "count": count, "drop_off_pct": drop})
        previous = count
    return {"store_id": store_id, "window": "today", "stages": result}


def heatmap(store_id: str) -> dict:
    start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = _rows(store_id, start)
    visits: dict[str, set[str]] = defaultdict(set)
    dwells: dict[str, list[int]] = defaultdict(list)
    sessions: set[str] = set()
    for row in rows:
        if row["event_type"] in {"ENTRY", "REENTRY"}:
            sessions.add(row["visitor_id"])
        if row["zone_id"] and row["event_type"] in {"ZONE_ENTER", "ZONE_DWELL"}:
            visits[row["zone_id"]].add(row["visitor_id"])
        if row["zone_id"] and row["event_type"] == "ZONE_DWELL":
            dwells[row["zone_id"]].append(row["dwell_ms"])
    high = max((len(value) for value in visits.values()), default=0)
    zones = []
    for zone in sorted(visits):
        values = dwells[zone]
        zones.append({
            "zone_id": zone,
            "visit_frequency": len(visits[zone]),
            "avg_dwell_ms": round(sum(values) / len(values), 2) if values else 0.0,
            "intensity": round(len(visits[zone]) / high * 100, 2) if high else 0.0,
        })
    return {"store_id": store_id, "window": "today", "data_confidence": "LOW" if len(sessions) < 20 else "HIGH", "zones": zones}


def anomalies(store_id: str) -> dict:
    current = metrics(store_id)
    now = _now()
    rows = _rows(store_id, now - timedelta(minutes=30))
    active = []
    queue_samples = [
        json.loads(row["metadata_json"]).get("queue_depth") or 0
        for row in rows
        if row["event_type"] == "BILLING_QUEUE_JOIN"
    ]
    current_depth = queue_samples[-1] if queue_samples else current["queue_depth"]
    baseline = queue_samples[:-1]
    rolling_mean = fmean(baseline) if baseline else 0.0
    rolling_std = pstdev(baseline) if len(baseline) > 1 else 0.0
    statistical_spike = len(baseline) >= 3 and current_depth > rolling_mean + 2 * rolling_std
    cold_start_spike = len(baseline) < 3 and current_depth >= 5
    if statistical_spike or cold_start_spike:
        active.append({
            "type": "BILLING_QUEUE_SPIKE",
            "severity": "CRITICAL" if current_depth >= 8 else "WARN",
            "suggested_action": "Open an additional billing counter.",
            "details": {
                "queue_depth": current_depth,
                "rolling_mean": round(rolling_mean, 2),
                "rolling_std": round(rolling_std, 2),
                "detection_mode": "ROLLING_BASELINE" if statistical_spike else "COLD_START_THRESHOLD",
            },
        })
    visited = {row["zone_id"] for row in rows if row["zone_id"] and row["event_type"] in {"ZONE_ENTER", "ZONE_DWELL"}}
    with database() as db:
        known = {row[0] for row in db.execute("SELECT DISTINCT zone_id FROM events WHERE store_id=? AND zone_id IS NOT NULL AND zone_id!='BILLING'", (store_id,))}
    for zone in sorted(known - visited):
        active.append({"type": "DEAD_ZONE", "severity": "WARN", "suggested_action": f"Inspect merchandising and camera coverage in {zone}.", "details": {"zone_id": zone}})
    historical_rows = _rows(store_id, now - timedelta(days=7))
    historical_transactions = _transactions(store_id, now - timedelta(days=7))
    rates = []
    for days_ago in range(1, 8):
        day = (now - timedelta(days=days_ago)).date()
        day_rows = [row for row in historical_rows if datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).date() == day]
        day_transactions = [row for row in historical_transactions if datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).date() == day]
        stages = _session_sets(day_rows, day_transactions)
        if stages["entry"]:
            rates.append(len(stages["purchase"]) / len(stages["entry"]))
    baseline = sum(rates) / len(rates) if rates else None
    if baseline and current["unique_visitors"] and current["conversion_rate"] < baseline:
        active.append({
            "type": "CONVERSION_DROP",
            "severity": "WARN",
            "suggested_action": "Review staffing, queue conditions, and recent merchandising changes.",
            "details": {"current_rate": current["conversion_rate"], "seven_day_avg": round(baseline, 4)},
        })
    return {"store_id": store_id, "active_anomalies": active}


def health() -> dict:
    now = _now()
    with database() as db:
        rows = list(db.execute("SELECT store_id, MAX(timestamp) AS latest FROM events GROUP BY store_id"))
    stores = {}
    warnings = []
    for row in rows:
        timestamp = datetime.fromisoformat(row["latest"].replace("Z", "+00:00"))
        lag = max(0, int((now - timestamp).total_seconds()))
        stale = lag > 600
        stores[row["store_id"]] = {"last_event_timestamp": row["latest"], "lag_seconds": lag, "status": "STALE_FEED" if stale else "OK"}
        if stale:
            warnings.append({"store_id": row["store_id"], "warning": "STALE_FEED"})
    return {"status": "degraded" if warnings else "ok", "stores": stores, "warnings": warnings}
