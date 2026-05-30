# Event Validation Report

Validated file: `data/events.jsonl`

## Result

**PASS**

Every line was parsed as JSON and validated with `app.models.StoreEvent`.

| Check | Result | Measured Value |
| --- | --- | --- |
| File exists | PASS | `data/events.jsonl` |
| Total records | PASS | 326 |
| Valid JSON records | PASS | 326 |
| Schema-valid records | PASS | 326 |
| Required fields present | PASS | 326 of 326 |
| Unique `event_id` | PASS | 326 unique IDs |
| Duplicate IDs | PASS | 0 |
| Timestamp parsing | PASS | Every timestamp is timezone-aware |
| Timestamp ordering | PASS | Globally chronological |
| Confidence range | PASS | Every value is between 0 and 1 |
| Dwell values | PASS | Every `dwell_ms` is a non-negative integer |

Required fields checked: `event_id`, `store_id`, `camera_id`, `visitor_id`, `event_type`, `timestamp`, and `confidence`.

