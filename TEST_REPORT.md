# Test Report

## Result

The final deterministic suite passes with **15 tests** and **93.15% statement coverage**, above the requested 85% target. Run:

```powershell
python -m pytest --cov=app --cov=pipeline --cov-report=term-missing
```

## Covered Scenarios

| Scenario | Coverage |
| --- | --- |
| Empty store | Metrics return zeros, not nulls. |
| Duplicate ingest | Second submission reports duplicates without extra rows. |
| Invalid JSON | Returns client error. |
| Invalid schema | Bad record rejected while valid siblings persist. |
| Batch cap | More than 500 events returns `413`. |
| Empty batch | Accepted safely with zero counts. |
| POS conversion | Billing session correlates to purchase within five minutes. |
| Re-entry funnel | Same `visitor_id` counts once. |
| All staff | Staff events do not affect visitor metrics. |
| Queue spike | Cold-start and rolling-baseline rules are both tested. |
| Dead zone | No visit in 30 minutes produces anomaly. |
| Stale feed | More than 10 minutes lag produces degraded health. |
| Heatmap | Intensity normalization, dwell average, and low-confidence flag. |
| Billing abandonment | POS correlation appends once and remains idempotent. |
| Zone closure | Idle-track pruning emits `ZONE_EXIT`. |
| Event ordering | JSONL sorting is globally chronological. |
| Database outage | SQLite failure returns structured `503`. |

## Stability

Tests use isolated temporary SQLite databases and controlled timestamps. No test depends on the YOLO download, external network, or Docker daemon.
