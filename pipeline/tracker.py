from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable


def _visitor_token(camera_id: str, track_id: int, timestamp: datetime) -> str:
    seed = f"{camera_id}:{track_id}:{timestamp.isoformat()}".encode()
    return "VIS_" + hashlib.sha1(seed).hexdigest()[:8]


def _inside(point: tuple[int, int], box: list[float]) -> bool:
    x, y = point
    left, top, right, bottom = box
    return left <= x <= right and top <= y <= bottom


@dataclass
class TrackState:
    visitor_id: str
    last_seen: datetime
    first_seen: datetime
    last_point: tuple[int, int]
    confidence: float
    zones: dict[str, datetime] = field(default_factory=dict)
    last_dwell: dict[str, datetime] = field(default_factory=dict)
    last_crossing: datetime | None = None
    is_staff: bool = False


class BehaviourTracker:
    def __init__(self, camera_id: str, kind: str, zones: dict[str, list[float]], threshold_y: int | None = None):
        self.camera_id = camera_id
        self.kind = kind
        self.zones = zones
        self.threshold_y = threshold_y
        self.tracks: dict[int, TrackState] = {}
        self.recent_exits: list[tuple[datetime, str, tuple[int, int]]] = []

    def prune(self, timestamp: datetime, emit: Callable, max_idle: timedelta = timedelta(seconds=3)) -> None:
        """Close open zones for tracks that disappeared after occlusion or leaving frame."""
        expired = [track_id for track_id, state in self.tracks.items() if timestamp - state.last_seen > max_idle]
        for track_id in expired:
            state = self.tracks.pop(track_id)
            for zone, entered_at in list(state.zones.items()):
                dwell = int((state.last_seen - entered_at).total_seconds() * 1000)
                emit(state.visitor_id, "ZONE_EXIT", state.last_seen, zone_id=zone, dwell_ms=max(0, dwell), is_staff=state.is_staff, confidence=state.confidence)

    def update(self, track_id: int, point: tuple[int, int], confidence: float, timestamp: datetime, emit: Callable, queue_depth: int = 0) -> None:
        state = self.tracks.get(track_id)
        if state is None:
            state = TrackState(_visitor_token(self.camera_id, track_id, timestamp), timestamp, timestamp, point, confidence)
            self.tracks[track_id] = state
        previous = state.last_point
        state.last_seen = timestamp
        state.last_point = point
        state.confidence = min(state.confidence, confidence)
        # A simple conservative staff proxy: very long continuous floor presence.
        state.is_staff = state.is_staff or timestamp - state.first_seen >= timedelta(minutes=8)
        if self.kind == "entry" and self.threshold_y is not None:
            self._crossing(state, previous, point, timestamp, emit)
        for zone, bounds in self.zones.items():
            was_inside = zone in state.zones
            is_inside = _inside(point, bounds)
            if is_inside and not was_inside:
                state.zones[zone] = timestamp
                state.last_dwell[zone] = timestamp
                emit(state.visitor_id, "ZONE_ENTER", timestamp, zone_id=zone, is_staff=state.is_staff, confidence=confidence)
                if zone == "BILLING" and queue_depth > 0:
                    emit(state.visitor_id, "BILLING_QUEUE_JOIN", timestamp, zone_id=zone, is_staff=state.is_staff, confidence=confidence, metadata={"queue_depth": queue_depth})
            elif is_inside and timestamp - state.last_dwell.get(zone, timestamp) >= timedelta(seconds=30):
                dwell = int((timestamp - state.zones[zone]).total_seconds() * 1000)
                emit(state.visitor_id, "ZONE_DWELL", timestamp, zone_id=zone, dwell_ms=dwell, is_staff=state.is_staff, confidence=confidence)
                state.last_dwell[zone] = timestamp
            elif not is_inside and was_inside:
                dwell = int((timestamp - state.zones.pop(zone)).total_seconds() * 1000)
                state.last_dwell.pop(zone, None)
                emit(state.visitor_id, "ZONE_EXIT", timestamp, zone_id=zone, dwell_ms=dwell, is_staff=state.is_staff, confidence=confidence)

    def _crossing(self, state: TrackState, previous: tuple[int, int], point: tuple[int, int], timestamp: datetime, emit: Callable) -> None:
        if state.last_crossing and timestamp - state.last_crossing < timedelta(seconds=2):
            return
        before, after = previous[1], point[1]
        if before <= self.threshold_y < after:
            state.last_crossing = timestamp
            match = self._reentry(point, timestamp)
            if match:
                state.visitor_id = match
                emit(state.visitor_id, "REENTRY", timestamp, is_staff=state.is_staff, confidence=state.confidence)
            else:
                emit(state.visitor_id, "ENTRY", timestamp, is_staff=state.is_staff, confidence=state.confidence)
        elif before >= self.threshold_y > after:
            state.last_crossing = timestamp
            emit(state.visitor_id, "EXIT", timestamp, is_staff=state.is_staff, confidence=state.confidence)
            self.recent_exits.append((timestamp, state.visitor_id, point))

    def _reentry(self, point: tuple[int, int], timestamp: datetime) -> str | None:
        self.recent_exits = [item for item in self.recent_exits if timestamp - item[0] <= timedelta(minutes=5)]
        nearby = [(when, visitor) for when, visitor, old in self.recent_exits if abs(point[0] - old[0]) <= 180]
        return max(nearby, default=(None, None))[1]
