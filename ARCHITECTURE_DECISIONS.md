# Architecture Decisions

## 1. Why YOLO11 Nano

The detector must work on realistic store footage with partial occlusion, variable lighting, blurred faces, and groups. YOLO11 nano was selected because it is available in the installed Ultralytics runtime, runs acceptably on CPU, supports person-class filtering, and integrates with persistent tracking in one operationally simple path.

YOLOv8 nano was considered as a mature baseline. RT-DETR was considered for potentially stronger difficult-frame accuracy. The nano model won for this submission because local reproducibility and iteration speed matter before labelled benchmarking exists. The design preserves a clean upgrade path: swap the model after measuring count accuracy against ground truth.

## 2. Why Camera-Local Identities

The tracker generates visitor tokens from camera ID, local track ID, and first-seen timestamp. This is intentionally conservative. The footage is anonymised and the extraction does not include labelled cross-camera trajectories. Claiming global identity from timestamps alone would make metrics look richer while introducing unmeasured false matches.

Entrance-camera re-entry is supported because the system has a defensible local signal: a recent exit near the same doorway. Cross-camera Re-ID is not implemented. Floor-camera identities remain useful for heatmap and dwell analytics, but the funnel intersects downstream stages with authoritative entrance sessions.

The result is a known limitation: the verified funnel under-reports downstream stages. `CROSS_CAMERA_REID_FEASIBILITY.md` documents the NO-GO decision for a submission-time patch.

## 3. Why FastAPI

FastAPI aligns well with the challenge requirements:

- Pydantic schema validation
- Clear partial-success ingestion
- OpenAPI documentation
- Straightforward middleware for structured logs
- Strong test support through `TestClient`
- Good compatibility with automated scoring harnesses

The API contract is intentionally small and production-aware. Invalid JSON returns `400`, non-array payloads return `422`, oversized batches return `413`, and dependency failures return structured `503` responses.

## 4. Why SQLite Now, PostgreSQL Later

SQLite WAL mode is the right challenge-scale choice. It starts inside the API container with no manual provisioning, survives restarts through a Docker volume, supports indexed store-time queries, and makes idempotency simple through primary keys.

PostgreSQL is the first production migration when concurrent writes, multi-store retention, or analytics volume outgrow SQLite. At larger scale, ingestion should flow through a durable broker and incremental aggregates should replace repeated scans. The immutable event schema remains valid across that migration.

## 5. Why the Current Anomaly Logic

Anomaly rules are explicit and auditable:

- Queue spike: current depth exceeds rolling mean plus two standard deviations once enough samples exist.
- Queue cold start: threshold fallback before a baseline exists.
- Conversion drop: current conversion falls below the prior seven-day average.
- Dead zone: historically observed non-billing zone receives no visit for 30 minutes.

These rules are easy to explain during operations and straightforward to test. A seasonal or learned baseline is a future improvement after sufficient historical data exists.

## 6. Why the Conservative Funnel

The funnel must use sessions, not raw event counts. Without cross-camera identity linkage, accepting every floor-camera token would inflate the funnel and violate the north-star metric. The current implementation chooses under-counting over false attribution.

Measured evidence supports that decision:

| Identity Set | Unique Tokens |
| --- | ---: |
| Entrance sessions | 3 |
| Zone-camera tokens | 105 |
| Billing tokens | 20 |
| Entrance and zone overlap | 0 |

Timestamp-only matching is not a safe patch: individual entrance sessions have up to 94 plausible zone-entry candidates inside two minutes. A correct future solution needs labelled trajectories, camera adjacency, transition windows, appearance embeddings, and confidence-aware one-to-one assignment.
