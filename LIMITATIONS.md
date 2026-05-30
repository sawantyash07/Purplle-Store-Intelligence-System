# Limitations and Production Follow-Up

## Cross-Camera Identity

Visitor IDs are camera-local. Entrance sessions can be counted and local doorway re-entry can be detected, but a floor-camera token is not automatically treated as the same physical person as an entrance-camera token.

This is a deliberate integrity decision. The available extraction does not contain labelled cross-camera trajectories. Timestamp-only matching is ambiguous: the measured stream contains up to 94 candidate zone entries inside a two-minute window for one re-entry session.

**Impact:** Heatmaps and dwell metrics remain useful, while the verified session funnel under-reports downstream stages.

**Production follow-up:** Label trajectories, calibrate transition windows, evaluate appearance embeddings, and use confidence-aware one-to-one assignment. Leave uncertain tracks unlinked.

## Official Camera Calibration

The problem statement references `store_layout.json`, but that official file was not present in the available extraction. Camera roles and zone polygons were inferred from representative frames.

**Impact:** Zone boundaries are auditable and runnable, but they are not store-certified calibration data.

**Production follow-up:** Version official polygons per store and camera. Add a visual calibration workflow and regression clips.

## Ground Truth

No labelled entry counts, staff labels, cross-camera identities, or queue-depth truth set were supplied.

**Impact:** Schema correctness, API behavior, and end-to-end execution are measured. Detection precision and recall cannot be claimed as ground-truth accuracy.

**Production follow-up:** Build a labelled evaluation set and compare model size, confidence threshold, stride, and tracker settings before rollout.

## Staff Classification

Staff classification uses long continuous presence as a transparent proxy.

**Impact:** It is explainable but weaker than a calibrated uniform classifier.

**Production follow-up:** Use consented staff examples, shift context, and confidence-aware classification.

## POS Transactions

The supplied POS CSV contains only its header.

**Impact:** The canonical dashboard correctly reports zero purchases and zero conversion. Positive conversion behavior is covered in automated tests with controlled POS records.

**Production follow-up:** Ingest real POS rows and monitor camera-clock drift because transaction correlation depends on timestamps.

## Storage Scale

SQLite WAL mode is appropriate for the single-node challenge submission.

**Impact:** It keeps Docker startup simple but is not the final persistence layer for 40 stores.

**Production follow-up:** Introduce a durable event broker, PostgreSQL or ClickHouse persistence, and incremental aggregates.
