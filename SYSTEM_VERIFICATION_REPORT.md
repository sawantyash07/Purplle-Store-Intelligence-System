# Store Intelligence System Verification Report

Validation date: 2026-05-30  
Project: `D:\Purplle Store Intelligence System`

## Executive Summary

The complete Store Intelligence System was verified end to end using the actual CCTV footage folder, generated event stream, POS correlation utility, Docker Compose deployment, API, dashboard, SQLite database, stress scenarios, and automated test suite.

Two defects were found and fixed during measured execution:

1. The inferred camera mapping did not match the filenames in `CCTV Footage` and omitted `CAM 4.mp4`.
2. Event sorting compared ISO timestamps lexically, which misordered fractional-second values against whole-second values.

Regression coverage was added for the ordering fix. The final clean container state is running and healthy.

## Videos Processed

| Video | OpenCV Valid | Pipeline Processed | Events |
| --- | --- | --- | ---: |
| `CAM 1.mp4` | PASS | PASS | 83 |
| `CAM 2.mp4` | PASS | PASS | 127 |
| `CAM 3.mp4` | PASS | PASS | 8 |
| `CAM 4.mp4` | PASS | PASS | 0 |
| `CAM 5.mp4` | PASS | PASS | 88 |

## Generated Events

- Pre-correlation events: `306`
- POS abandonment events added: `20`
- Final events: `326`
- Unique event IDs: `326`
- Schema-valid events: `326`
- Duplicate IDs: `0`
- Chronological ordering: `PASS`

## API and Dashboard

| Component | Status | Evidence |
| --- | --- | --- |
| Event ingestion | PASS | Full replay accepted `326` events |
| Metrics | PASS | HTTP `200`, visitors `3`, conversion `0.0`, queue `2` |
| Funnel | PARTIAL | HTTP `200`, monotonic stage counts; downstream stages intentionally under-report without cross-camera identity linkage |
| Heatmap | PASS | HTTP `200`, valid 0-100 scores |
| Anomalies | PASS | HTTP `200`, valid structure |
| Health | PASS | HTTP `200`, status `ok`, fresh last event |
| Dashboard | PASS | Loaded in browser with visible metrics and no console errors |

## Docker and Database

| Component | Status | Evidence |
| --- | --- | --- |
| Docker build | PASS | `docker compose up --build -d` completed |
| API container | PASS | Running on port `8000` |
| SQLite database | PASS | Embedded volume inspected |
| Event rows | PASS | `326` |
| Transaction rows | PASS | `0`, matching supplied empty POS CSV |
| Duplicate primary keys | PASS | `0` |
| Sessions | PASS | Derived from immutable events; no separate table by design |

## Automated Tests

```text
16 passed
93.15% statement coverage
```

The suite covers idempotency, malformed payloads, invalid JSON, batch cap, empty traffic, all-staff traffic, re-entry, queue spike baselines, dead zones, stale feed, heatmap confidence, conversion drops, POS abandonment, event ordering, and structured database-outage degradation.

## Component Scorecard

| Component | Status |
| --- | --- |
| Input video folder | PASS |
| OpenCV metadata | PASS |
| Detection pipeline | PASS |
| Event schema | PASS |
| POS correlation | PASS |
| Docker startup | PASS |
| Replay | PASS |
| Required API endpoints | PASS |
| Dashboard | PASS |
| SQLite persistence | PASS |
| Stress behavior | PASS |
| Automated coverage target | PASS |

## Remaining Risks

- The official layout JSON, POS records, sample events, and assertions referenced by the challenge were not present. Zones are inferred and should be replaced if official calibration assets arrive.
- `CAM 4.mp4` yielded zero retained events due to the heavily occluded backroom view.
- The supplied POS file is empty, so the live canonical dashboard correctly shows zero conversion. Positive conversion remains verified by automated tests.
- Cross-camera Re-ID remains a documented limitation in `CROSS_CAMERA_REID_FEASIBILITY.md`.
- Staff classification is implemented as a conservative long-presence proxy, tested at the API layer, and not demonstrated by the supplied clips. See `STAFF_CLASSIFICATION_REVIEW.md`.
- The funnel limitation is explicitly analyzed in `CROSS_CAMERA_REID_FEASIBILITY.md`. A safety review rejected a submission-time Re-ID patch because correct linkage cannot be measured without labelled trajectories.

## Estimated Challenge Score

Estimated base score: **70/100**, with an eligible dashboard bonus. API correctness, containerization, documentation, dashboard, resilience, and test coverage are strong. The unresolved scoring risks are held-out computer-vision accuracy, camera-local identity, and staff-classification evidence because official calibration and ground-truth assets were unavailable.

## Overall Status

**PASS**

The system runs end to end from real MP4 inputs to validated JSONL, repeat-safe POS correlation, Docker replay, live metrics, browser dashboard, SQLite persistence, and stress-tested API behavior. Remaining limitations are documented data-quality and calibration risks, not execution failures.
