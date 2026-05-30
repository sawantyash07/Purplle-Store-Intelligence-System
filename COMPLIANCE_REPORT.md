# Compliance Report

| Requirement | Status | Evidence |
| --- | --- | --- |
| `ENTRY` | PASS | Directional inbound threshold crossing in `pipeline/tracker.py`. |
| `EXIT` | PASS | Directional outbound threshold crossing in `pipeline/tracker.py`. |
| `REENTRY` | PASS | Recent same-door exit matching reuses `visitor_id`. |
| `ZONE_ENTER` | PASS | Region transition emitted on first inside point. |
| `ZONE_EXIT` | PASS | Emitted on region departure and idle-track pruning. |
| `ZONE_DWELL` | PASS | Emitted every 30 seconds of continuous presence. |
| `BILLING_QUEUE_JOIN` | PASS | Billing-region entry with queue depth metadata. |
| `BILLING_QUEUE_ABANDON` | PASS | Idempotent POS-correlation utility appends abandonment. |
| `POST /events/ingest` | PASS | Batch validation, max 500, deduplication, partial success. |
| `GET /stores/{id}/metrics` | PASS | Staff exclusion, zero handling, live metrics. |
| `GET /stores/{id}/funnel` | PARTIAL | Contract and session deduplication pass. Verified multi-camera output is conservative because camera-local identities are not cross-linked. |
| `GET /stores/{id}/heatmap` | PASS | Zone visits, dwell, 0-100 intensity, confidence flag. |
| `GET /stores/{id}/anomalies` | PASS | Queue spike, conversion drop, dead zone. |
| `GET /health` | PASS | Per-store last event and stale-feed warning. |
| Docker Compose | PASS | API builds and runs through `docker compose up --build -d`. |
| Structured logs | PASS | Trace, store, endpoint, latency, count, and status fields. |
| Graceful degradation | PASS | Unexpected dependency errors return structured `503`. |
| Idempotency | PASS | Events and transactions use primary-key deduplication. |
| Coverage | PASS | Audited coverage is 93.15%, above the required threshold. |
| Timestamp ordering | PASS | Parsed-datetime sorting produces a globally chronological canonical JSONL stream. |
| `DESIGN.md` | PASS | Expanded architecture and AI-assisted decisions. |
| `CHOICES.md` | PASS | Model, schema, API, and anomaly rationale. |
| Prompt blocks | PASS | Every test file starts with `# PROMPT` and `# CHANGES MADE`. |
| Official camera layout | PARTIAL | Inferred defaults are checked in because official layout was absent. |
| Appearance-based staff classifier | PARTIAL | Transparent long-presence proxy used; labelled uniform data absent. |
| Appearance-based cross-camera Re-ID | PARTIAL | Conservative doorway Re-ID avoids unsupported identity guesses. |

## Acceptance Gate

The API starts via Compose, generated events validate, ingestion accepts events without `5xx`, `/stores/STORE_BLR_002/metrics` returns JSON, and both required design documents are non-trivial.
