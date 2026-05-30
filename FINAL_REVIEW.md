# Final Technical Review

## Architecture Summary

The repository implements an edge-style CCTV analytics pipeline and a central FastAPI service. `pipeline.detect` runs YOLO11 nano person detection and persistent tracking. `pipeline.tracker` turns bottom-centre trajectories into doorway, zone, dwell, and billing events. `pipeline.correlate_pos` appends abandonment events after POS time-window correlation. The API validates event batches, deduplicates with SQLite primary keys, computes live analytics, and serves a polling dashboard.

## Strengths

- All eight required event types are implemented.
- Ingestion is idempotent, batch-limited, partial-success, and explicit about malformed JSON.
- Session funnels count entrance sessions rather than raw event volume.
- Queue spikes use a rolling mean plus two standard deviations with an explained cold-start fallback.
- Track pruning closes zones when people disappear after occlusion.
- The API container excludes the large CV stack and starts cleanly through Compose.
- Tests cover rubric edge cases and exceed the requested coverage target.

## Weaknesses

- Cross-camera Re-ID is deliberately not implemented. Camera-local identities protect metric integrity but make the verified funnel conservative: `entry=3`, `zone_visit=0`.
- Staff classification is a long-presence proxy because no labelled uniform examples were supplied.
- The inferred layout must be replaced if the official dataset layout becomes available.
- SQLite analytics scan persisted rows on request. That is appropriate for challenge scale, not fleet scale.

## Hidden-Test Risks

- Hidden detection scoring may penalize the missing official layout and conservative cross-camera matching.
- Hidden tests may assume different anomaly cold-start semantics. The response exposes `detection_mode` to make the behavior auditable.
- Empty POS data correctly produces zero conversion but cannot demonstrate positive conversion on the supplied stream.

## Production Risks

- Model recall should be calibrated against labelled footage before rollout.
- Layout configuration needs versioning and store-specific calibration.
- A durable broker and production database are required before multi-store deployment.
- Camera clock drift should be monitored because timestamps drive POS matching.

## Missing Challenge Inputs

The provided extraction omitted the referenced official `store_layout.json`, `pos_transactions.csv`, `sample_events.jsonl`, and `assertions.py`. The repository includes an inferred editable layout and valid empty POS CSV so the full system remains runnable.

## Submission Recommendation

Submit the current implementation. Do not add cross-camera identity linking without labelled trajectories and calibrated transition rules. The feasibility review found timestamp-only matching ambiguous, with up to 94 candidate zone entries inside a two-minute window for one re-entry session.

## Estimated Score

Estimated base score: **70/100**, with an eligible dashboard bonus. API, production readiness, documentation, AI reasoning, and dashboard evidence are strong. The largest uncertainties are detection accuracy against ground truth, camera-local identity, and staff-classification evidence because official calibration assets were unavailable.
