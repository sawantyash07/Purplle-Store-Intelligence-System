# Timestamp Ordering Analysis

## Summary

The canonical `data/events.jsonl` artifact contained 9 adjacent timestamp
inversions. The issue was reproduced, traced to lexical ISO timestamp sorting,
fixed with parsed datetime sorting, and validated after re-sorting the derived
artifact.

## Evidence Before Fix

```text
events=326
adjacent_inversions=9
duplicate_event_ids=0
```

| Earlier file row | Event type | Timestamp | Later file row | Event type | Timestamp |
|---:|---|---|---:|---|---|
| 23 | `ZONE_EXIT` | `2026-04-10T14:10:02.834167Z` | 24 | `ZONE_ENTER` | `2026-04-10T14:10:02Z` |
| 55 | `ZONE_EXIT` | `2026-04-10T14:10:11.175833Z` | 56 | `ZONE_ENTER` | `2026-04-10T14:10:11Z` |
| 86 | `ZONE_EXIT` | `2026-04-10T14:10:27.859167Z` | 87 | `ZONE_ENTER` | `2026-04-10T14:10:27Z` |
| 107 | `ZONE_ENTER` | `2026-04-10T14:10:33.600000Z` | 108 | `ZONE_EXIT` | `2026-04-10T14:10:33Z` |
| 131 | `ZONE_DWELL` | `2026-04-10T14:10:45.877167Z` | 132 | `ZONE_ENTER` | `2026-04-10T14:10:45Z` |
| 155 | `ZONE_EXIT` | `2026-04-10T14:10:48.713333Z` | 156 | `ZONE_ENTER` | `2026-04-10T14:10:48Z` |
| 171 | `ZONE_ENTER` | `2026-04-10T14:10:51.858167Z` | 172 | `BILLING_QUEUE_JOIN` | `2026-04-10T14:10:51Z` |
| 217 | `ZONE_EXIT` | `2026-04-10T14:11:13.237833Z` | 218 | `BILLING_QUEUE_ABANDON` | `2026-04-10T14:11:13Z` |
| 228 | `BILLING_QUEUE_JOIN` | `2026-04-10T14:11:15.600000Z` | 229 | `BILLING_QUEUE_JOIN` | `2026-04-10T14:11:15Z` |

## Root Cause

`pipeline.run_all.sort_events` and `pipeline.correlate_pos.add_abandonment_events`
sorted timestamps as strings:

```python
events.sort(key=lambda event: (event["timestamp"], event["event_id"]))
```

ISO strings with fractional seconds do not sort chronologically against
whole-second `...Z` values. For example, lexical ordering places
`14:10:02.834167Z` before `14:10:02Z`, although it occurs later.

The source was the sorting implementation used after detection and POS
correlation. Replay and JSON serialization preserved the order they received;
they were not the root cause.

## Low-Risk Fix

Both sorting paths now parse timestamps before sorting:

```python
events.sort(key=lambda event: (_time(event["timestamp"]), event["event_id"]))
```

The change does not alter tracker behavior, visitor IDs, event schema, API
responses, or event content. It only corrects file ordering.

## Validation After Fix

The existing idempotent POS-correlation command re-sorted the derived artifact:

```text
python -m pipeline.correlate_pos --events data\events.jsonl --pos data\pos_transactions.csv
{"billing_queue_abandon_events_added": 0}

events=326
adjacent_inversions=0
duplicate_event_ids=0
```

A regression test covers the fractional-second case. The complete suite passes:

```text
16 passed
93.15% statement coverage
```

## Impact

Before the fix, consumers requiring strictly chronological JSONL could observe
out-of-order adjacent records. Stored event semantics and API analytics were
not changed. After the fix, the canonical artifact is globally chronological.
