from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.getenv("STORE_INTEL_DB", "/data/store_intelligence.db"))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with database() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                store_id TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                visitor_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                zone_id TEXT,
                dwell_ms INTEGER NOT NULL,
                is_staff INTEGER NOT NULL,
                confidence REAL NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_store_time
                ON events(store_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_store_visitor
                ON events(store_id, visitor_id);
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                store_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                basket_value_inr REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_store_time
                ON transactions(store_id, timestamp);
            """
        )


def event_values(event: object) -> tuple:
    data = event.model_dump(mode="json")
    return (
        data["event_id"],
        data["store_id"],
        data["camera_id"],
        data["visitor_id"],
        data["event_type"],
        data["timestamp"],
        data["zone_id"],
        data["dwell_ms"],
        int(data["is_staff"]),
        data["confidence"],
        json.dumps(data["metadata"], separators=(",", ":")),
    )

