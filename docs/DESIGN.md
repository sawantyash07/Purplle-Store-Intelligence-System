# Design

## 1. Architecture Overview

The system is divided into an edge-style computer-vision pipeline and a central intelligence API. This is a deliberate production boundary. Raw CCTV frames are high-volume, privacy-sensitive inputs. Behavioural events are compact, inspectable, and sufficient for analytics. The pipeline reads video locally, detects people, tracks trajectories, interprets movement, and emits JSON Lines. The API validates those events, stores them in SQLite, correlates billing visits with POS transactions, calculates live metrics, and exposes a polling dashboard.

The checked-in API container intentionally excludes Torch, OpenCV, and Ultralytics. A store-side worker would normally own those dependencies close to each camera. The central container therefore builds quickly and starts through `docker compose up` without requiring a model download.

## 2. End-to-End Data Flow

`pipeline.run_all` loads `config/store_layout.json`, processes configured videos one at a time, and sorts the final JSONL stream globally by timestamp. `pipeline.detect` opens a clip with OpenCV and invokes YOLO11 nano persistent tracking on sampled frames. Each tracked bounding box becomes a bottom-centre floor point. `pipeline.tracker` converts point movement into semantic events. `pipeline.emit` writes immutable records with UUID event IDs and UTC timestamps derived from clip start plus frame offset.

After detection, `pipeline.correlate_pos` reads the event stream and POS CSV. It appends `BILLING_QUEUE_ABANDON` when a visitor leaves billing without a transaction in the permitted time window. `pipeline.replay` posts events to the API in configurable batches and can shift archived timestamps to the current time for a simulated-live dashboard demo.

## 3. Detection Layer

The selected detector is Ultralytics YOLO11 nano using the person class only. The nano variant is a practical CPU baseline for a take-home challenge: fast enough to process the supplied clips locally, small enough to download quickly, and capable of retaining partially visible people better than classical HOG detection. Detection confidence is intentionally permissive at `0.18`; low-confidence detections are not silently promoted. Their original confidence reaches emitted events so downstream consumers can reason about uncertainty.

Frame stride is configurable. A higher stride accelerates offline evaluation. A lower stride should be used where group entry recall or occlusion recovery matters more than throughput.

## 4. Tracking Layer

Ultralytics persistent tracking supplies local tracker IDs. The interpreter uses the bottom-centre point because it is a better approximation of floor position than bounding-box centre when displays occlude a person's torso. Entry cameras use a horizontal threshold. Crossing direction determines `ENTRY` or `EXIT`. Floor and billing cameras use configured rectangles for `ZONE_ENTER`, `ZONE_EXIT`, and `ZONE_DWELL`.

The tracker allows a surviving track to cross the doorway again after a two-second debounce. This matters for exits and returns. It also prunes tracks absent for more than three seconds and closes any open zones at the last observed timestamp. That prevents silent missing `ZONE_EXIT` events when a person leaves frame during occlusion.

## 5. Re-ID Strategy

Re-ID is conservative by design. After `EXIT`, the entrance tracker stores a recent exit token, time, and door position. An inbound crossing inside five minutes and within 180 horizontal pixels reuses that token and emits `REENTRY`. The API counts the session once because both records share `visitor_id`.

This approach avoids aggressive identity claims from anonymised footage, but it is not appearance-based cross-camera Re-ID. Floor-camera tracker IDs are therefore used for zone heatmaps and dwell data but are intersected with known entrance sessions before funnel calculation. This prevents inflated conversion funnels when local camera IDs cannot be linked confidently.

The measured canonical replay makes this boundary visible: three entrance-session tokens overlap with zero of the 105 floor-zone tokens. The resulting funnel intentionally under-reports downstream stages rather than asserting unverified identities. `CROSS_CAMERA_REID_FEASIBILITY.md` documents why a submission-time Re-ID patch was rejected after a safety review.

## 6. Event Stream Design

Events implement the required catalogue: `ENTRY`, `EXIT`, `REENTRY`, `ZONE_ENTER`, `ZONE_EXIT`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, and `BILLING_QUEUE_ABANDON`. Every event includes a globally unique UUID, store, camera, visitor token, UTC timestamp, optional zone, dwell duration, staff flag, confidence, and metadata. JSONL is easy to inspect, append, replay, and archive. The API accepts batches of up to 500 records.

Queue joins are emitted only when a tracked point enters the configured billing rectangle while queue depth is positive. Queue depth counts tracked points inside that rectangle, not every visible person in the billing camera.

## 7. Database Design

SQLite runs in WAL mode. `event_id` is the primary key, which makes replay retries idempotent through `INSERT OR IGNORE`. Indexed `(store_id, timestamp)` and `(store_id, visitor_id)` paths support time-window metrics and session grouping. Transactions use `transaction_id` as their deduplication key and have a store-time index.

SQLite is intentionally challenge-scale. It is a strong fit for a single-container acceptance gate because it has no external service dependency. For a 40-store rollout, the event contract remains stable while storage migrates to PostgreSQL, ClickHouse, or a time-series store.

## 8. API Design

FastAPI and Pydantic validate typed events. Ingestion validates items independently, returns partial success, rejects malformed JSON as `400`, rejects non-array input as `422`, caps batches at 500 with `413`, and reports duplicate counts. Unexpected database or dependency errors are converted to structured `503` responses without leaking raw exceptions.

Metrics exclude staff. `/metrics` returns unique visitors, conversion, zone dwell, latest queue depth, and abandonment. `/funnel` calculates session-level entry, zone visit, billing, and purchase counts. `/heatmap` returns normalized 0-100 zone intensity with a low-confidence flag below 20 sessions. `/anomalies` reports queue spikes, conversion drops, and dead zones. `/health` reports last-event time and `STALE_FEED` after ten minutes.

## 9. Dashboard Architecture

The dashboard is a deliberately small HTML page served by FastAPI. It polls `/stores/STORE_BLR_002/metrics` every two seconds and displays visitors, conversion, and queue depth. Polling is sufficient to demonstrate a genuinely connected pipeline without introducing WebSocket lifecycle complexity. A production dashboard could add store selection, historical charts, and server-sent events.

## 10. Scalability Discussion

At 40 stores, the first pressure point is not YOLO model selection; it is durable ingestion and repeated analytics scans. A production design would publish edge events to Kafka, Redpanda, or a managed queue, persist canonical events in PostgreSQL or ClickHouse, and maintain incremental aggregates. Each detector worker would expose model, camera, dropped-frame, and lag metrics. Camera layout calibration would be versioned and deployed independently of the API.

## 11. Production Readiness

Compose starts the API in one command with a persistent volume. Structured logs contain trace ID, store, endpoint, latency, ingest count, and status. The health endpoint is useful to on-call engineers because it reports per-store freshness. Tests cover idempotency, malformed input, all-staff traffic, stale feed, empty traffic, funnel deduplication, queue spikes, conversion drops, dead zones, heatmap confidence, event ordering, zone closure, and POS abandonment.

## 12. AI-Assisted Decisions

AI recommended an edge detector plus central event API. I accepted that boundary because it reduces raw-video movement and keeps the central container operationally small.

AI suggested a hosted VLM for staff uniform classification and zone labelling. I rejected that for this submission. The extracted dataset omitted official layouts, the footage is anonymised, and hosted frame inference would add privacy, latency, and cost concerns. Auditable geometry and a documented long-presence staff proxy are more honest defaults.

AI suggested treating every tracker ID as a session. I rejected that because occlusion can churn tracker IDs and cross-camera IDs are not identities. Entrance crossing starts the authoritative visit session; funnel stages are intersected with those entrance tokens.

AI also suggested a fixed queue threshold. I refined that recommendation: queue spikes use `current_depth > rolling_mean + 2 * rolling_std` after enough samples and retain a threshold fallback only during cold start. This is more actionable across stores with different normal traffic patterns.
