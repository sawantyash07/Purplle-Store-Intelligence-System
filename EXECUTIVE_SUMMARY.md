# Executive Summary

## Problem Statement

Online retail has mature conversion analytics, but physical stores often lack comparable visibility. This project converts anonymised CCTV footage into a queryable offline store-intelligence surface: visitor sessions, zone attention, billing queues, abandonment, conversion, anomalies, and feed health.

The north-star metric is offline store conversion:

```text
converted visitor sessions / unique visitor sessions
```

## Architecture Overview

The design separates privacy-sensitive video processing from the central analytics API:

```text
CCTV clips
  -> YOLO11 nano person detection
  -> persistent local tracking
  -> trajectory interpretation
  -> immutable JSONL behavioural events
  -> optional POS correlation
  -> FastAPI ingestion
  -> SQLite WAL persistence
  -> metrics, funnel, heatmap, anomalies, health
  -> live polling dashboard
```

Raw footage stays outside the API container. Only compact behavioural events are transmitted centrally. This keeps the acceptance path small and mirrors a practical edge-processing deployment.

## Detection Pipeline

The pipeline uses YOLO11 nano with the person class and persistent local tracking. Each bounding box is reduced to a bottom-centre floor point, which is more stable under torso occlusion than a box centre. Camera-specific geometry then produces the required event catalogue:

- `ENTRY`
- `EXIT`
- `REENTRY`
- `ZONE_ENTER`
- `ZONE_EXIT`
- `ZONE_DWELL`
- `BILLING_QUEUE_JOIN`
- `BILLING_QUEUE_ABANDON`

The verified CCTV folder contains five 1080p MP4 clips. A complete default-stride run produced 306 detection events. POS correlation appended 20 abandonment events, resulting in 326 schema-valid events with unique IDs and chronological ordering.

## Analytics Layer

FastAPI validates each event independently and accepts batches of up to 500 records. SQLite primary keys make replay idempotent. The API exposes:

- Live store metrics
- Session-level funnel
- Normalized zone heatmap
- Queue spike, conversion drop, and dead-zone anomalies
- Feed freshness health checks

Structured logs include trace ID, store, endpoint, latency, event count, and status code. Unexpected SQLite outages return structured HTTP `503` responses.

## Dashboard

The dashboard is served at [http://localhost:8000](http://localhost:8000). It polls live metrics every two seconds and displays visitor count, conversion rate, queue depth, and the latest metrics response. Browser validation confirmed visible metrics and no console errors.

## Verified Results

| Signal | Measured Result |
| --- | ---: |
| Videos processed | 5 |
| Final events | 326 |
| Schema-valid events | 326 |
| Duplicate event IDs | 0 |
| Tests passing | 16 |
| Statement coverage | 93.15% |
| Docker startup | PASS |
| Required API endpoints | PASS |
| Dashboard | PASS |
| Health status after replay | `ok` |

## Known Limitations

The supplied extraction omitted the official layout JSON, populated POS transactions, sample events, and example assertions. Camera roles and polygons were therefore inferred and documented.

Cross-camera identity is intentionally conservative. Visitor IDs are camera-local, so heatmaps report real zone activity while the session funnel under-reports downstream stages unless a floor-camera identity can be proven to match an entrance session. A safety review rejected a rushed Re-ID patch because timestamp-only matching was ambiguous and no labelled cross-camera ground truth was supplied.

## Future Improvements

The production path is clear:

1. Label doorway counts and cross-camera trajectories.
2. Calibrate camera polygons and transition windows.
3. Benchmark YOLO model sizes and stride settings.
4. Evaluate appearance embeddings with confidence thresholds.
5. Move multi-store ingestion behind a durable broker.
6. Replace SQLite with PostgreSQL, ClickHouse, or a time-series store when scale requires it.

The current repository is submission-ready: it is runnable, testable, auditable, and explicit about the boundary between verified behavior and future work.
