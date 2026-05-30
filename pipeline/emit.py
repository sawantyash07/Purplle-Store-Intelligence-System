from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def iso_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class EventEmitter:
    output: Path
    store_id: str
    camera_id: str
    sequence: dict[str, int] = field(default_factory=dict)

    def emit(
        self,
        visitor_id: str,
        event_type: str,
        timestamp: datetime,
        *,
        zone_id: str | None = None,
        dwell_ms: int = 0,
        is_staff: bool = False,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        self.sequence[visitor_id] = self.sequence.get(visitor_id, 0) + 1
        details = {"queue_depth": None, "sku_zone": zone_id, "session_seq": self.sequence[visitor_id]}
        details.update(metadata or {})
        event = {
            "event_id": str(uuid.uuid4()),
            "store_id": self.store_id,
            "camera_id": self.camera_id,
            "visitor_id": visitor_id,
            "event_type": event_type,
            "timestamp": iso_timestamp(timestamp),
            "zone_id": zone_id,
            "dwell_ms": dwell_ms,
            "is_staff": is_staff,
            "confidence": round(max(0.0, min(1.0, confidence)), 4),
            "metadata": details,
        }
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
        return event

