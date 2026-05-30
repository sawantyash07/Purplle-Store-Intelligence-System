# API Validation Report

## Ingestion

`POST /events/ingest` has been validated for:

- Valid event storage.
- Repeated `event_id` deduplication.
- Partial success when one record fails schema validation.
- Missing required fields.
- Invalid JSON.
- Empty arrays.
- Rejection above 500 records.
- Structured logs with trace ID, store, endpoint, count, latency, and status.

## Query Endpoints

| Endpoint | Validated Behavior |
| --- | --- |
| `/stores/{id}/metrics` | Empty traffic, no purchase, all-staff exclusion, queue depth, dwell, abandonment. |
| `/stores/{id}/funnel` | Session counts and re-entry deduplication. |
| `/stores/{id}/heatmap` | Normalized intensity and fewer-than-20-session confidence flag. |
| `/stores/{id}/anomalies` | Queue spike, dead zone, and conversion drop. |
| `/health` | Empty database, fresh feed, and stale feed. |
| `/` | Dashboard HTML loads and polls live metrics. |

## Error Handling

Client mistakes receive `400`, `413`, or `422`. Unexpected service and database errors are handled by the global exception handler as structured `503` responses. Raw stack traces remain in server logs only.

