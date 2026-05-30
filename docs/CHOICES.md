# Engineering Choices

## Decision 1: Detection Model and Tracking Approach

### Problem

The detection layer must find individuals in realistic CCTV footage, including groups entering together, partial occlusion near counters, lighting variation, and blurred faces. It must preserve confidence and work locally on a CPU-only evaluation machine.

### Options Considered

**YOLOv8 nano** is a mature baseline with broad examples and stable Ultralytics integration. It is easy to explain and remains a valid deployment choice.

**YOLO11 nano** is the current small Ultralytics detector available in the installed runtime. It has the same practical integration advantages as YOLOv8 while using the newer model family.

**RT-DETR** is an attractive transformer detector with strong accuracy potential, particularly when object interactions are difficult. Its heavier compute profile makes CPU iteration slower for this take-home workload.

I also considered classical OpenCV HOG detection. It avoids a model download but is substantially weaker under the partial occlusion and retail displays visible in the supplied clips.

### AI Recommendation

AI initially recommended YOLOv8 nano because it is familiar, documented, and likely to be understood quickly by reviewers. It also recommended appearance embeddings for Re-ID.

### Final Choice

I selected YOLO11 nano with Ultralytics persistent tracking and a trajectory interpreter. The model is restricted to person detections and runs with a permissive `0.18` confidence threshold. Each event preserves detection confidence. Tracking semantics use bounding-box bottom-centre points, explicit camera zones, and threshold crossings.

### Tradeoffs and Reasoning

The model is not the entire solution. The scoring criteria depend on turning detections into reliable business events. YOLO11 nano is fast enough for local replay and gives a clean upgrade path if a larger model is justified by labelled evaluation. RT-DETR might improve difficult frames, but using it before measuring recall would add compute cost without proving a scoring gain.

I did not add appearance-based Re-ID because the supplied extraction has anonymised footage and no labelled cross-camera identities. Instead, re-entry matching is deliberately conservative: reuse a visitor token only after a recent exit near the same door. This limits re-entry inflation without pretending the system knows more than it does.

For staff, the pipeline uses long continuous presence as a transparent proxy. A production system should train or calibrate a uniform classifier using consented staff examples and combine it with roster or shift context.

## Decision 2: Behavioural Event Schema

### Problem

The API must support metrics, funnels, heatmaps, anomalies, POS conversion, replay, and idempotency without transmitting raw footage. The stream also needs to preserve uncertainty and source provenance.

### Options Considered

**Raw bounding-box events** would retain maximum debugging detail but expose more footage-derived information and force every consumer to reimplement semantics.

**Aggregate-only counters** would be cheap to transmit but make re-entry correction, partial replay, debugging, and new analytics difficult.

**Immutable behavioural events** represent meaningful transitions while retaining source camera, visitor token, timestamp, confidence, and staff classification.

### AI Recommendation

AI recommended immutable behavioural events and suggested adding bounding-box coordinates to metadata for debugging.

### Final Choice

I selected immutable behavioural events matching the challenge catalogue: `ENTRY`, `EXIT`, `REENTRY`, `ZONE_ENTER`, `ZONE_EXIT`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, and `BILLING_QUEUE_ABANDON`. Each event contains UUID `event_id`, `store_id`, `camera_id`, `visitor_id`, UTC timestamp, optional zone, dwell milliseconds, `is_staff`, confidence, and metadata.

The disk format is JSON Lines. The network format is a JSON array of up to 500 records. `pipeline.run_all` sorts the output globally by timestamp before replay. `pipeline.correlate_pos` is idempotent and appends abandonment events only when no matching event already exists.

### Tradeoffs and Reasoning

I rejected public bounding-box coordinates because the required API does not need them. They can remain in private observability traces if future calibration requires them. Behavioural JSONL is human-readable and easy to replay during a demo. The UUID primary key makes at-least-once delivery safe. Partial success prevents one malformed event from losing valid siblings.

The stream is intentionally append-oriented. It is not a mutable session table. This supports auditability and makes future broker-based ingestion straightforward.

## Decision 3: API Architecture and Storage

### Problem

The service must start through Docker Compose, validate and deduplicate events, answer live analytics queries, degrade gracefully, and remain explainable during follow-up questions.

### Options Considered

**FastAPI plus SQLite** minimizes operational dependencies and fits the challenge scale.

**FastAPI plus PostgreSQL** offers stronger concurrent-write behavior and a better fleet-scale foundation, but adds a service and migration setup to the acceptance gate.

**PostgreSQL plus Redis aggregates** would improve query latency under sustained traffic, at the cost of cache invalidation and more operational surface.

**In-memory state** would be simple but fails restart persistence and makes replay behavior less representative.

### AI Recommendation

AI initially recommended PostgreSQL plus Redis because the business describes 40 stores. It also recommended WebSockets for the dashboard.

### Final Choice

I chose FastAPI, Pydantic, and SQLite WAL mode for the challenge submission. Events and POS transactions have primary-key deduplication. The API computes analytics from persisted canonical events on request. The dashboard polls every two seconds.

### Tradeoffs and Reasoning

The acceptance gate matters: `docker compose up` should start a dependable API with no manual initialization. SQLite satisfies that requirement while retaining persistence and clear SQL semantics. WAL mode improves concurrent reads. Indexes on store-time and store-visitor fields match the dominant access paths.

This is not presented as the final fleet architecture. At 40 stores, repeated scans and serialized SQLite writes become the first bottlenecks. The next design would ingest into a durable broker, persist to PostgreSQL or ClickHouse, and maintain incremental aggregates. The existing event schema and HTTP surface remain useful during that migration.

Polling wins over WebSockets for this submission because the dashboard requirement is proof of live connection, not a high-frequency trading interface. Polling is easier to operate and sufficient at two-second refresh intervals.

## Additional Decision: Anomaly Thresholds

### Problem

A fixed queue threshold behaves poorly across stores with different baseline traffic. A queue depth of five may be normal in a flagship store and severe in a quiet outlet.

### Options Considered

I considered a fixed threshold, a rolling statistical threshold, and a learned seasonal model.

### AI Recommendation

AI recommended a fixed threshold first because it is easy to test. During review, that was refined to a rolling rule.

### Final Choice

With at least three historical queue samples in the active window, a spike is `current_depth > rolling_mean + 2 * rolling_std`. During cold start, depth five remains a practical fallback. Severity becomes critical at depth eight. The response exposes threshold mode, rolling mean, and standard deviation for explainability.

### Tradeoffs and Reasoning

A learned seasonal model would be stronger after weeks of data but is unjustified for a small challenge dataset. The rolling rule is auditable, easy to validate, and adapts to local behavior without hiding its basis.
