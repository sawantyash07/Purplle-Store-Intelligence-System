# Database Validation Report

Database: SQLite at `/data/store_intelligence.db` inside the API volume.

## Result

**PASS**

Final clean-state inspection after canonical replay:

| Table | Rows | Duplicate Primary Keys |
| --- | ---: | ---: |
| `events` | 326 | 0 |
| `transactions` | 0 | 0 |

## Event Type Counts

| Event Type | Rows |
| --- | ---: |
| `ENTRY` | 1 |
| `EXIT` | 5 |
| `REENTRY` | 2 |
| `ZONE_ENTER` | 128 |
| `ZONE_EXIT` | 119 |
| `ZONE_DWELL` | 22 |
| `BILLING_QUEUE_JOIN` | 29 |
| `BILLING_QUEUE_ABANDON` | 20 |

## Sessions

There is intentionally no mutable `sessions` table. Sessions are derived from immutable event records by `visitor_id` inside the analytics layer. This matches the documented architecture and avoids a second source of truth.

## Transactions

The table exists and is structurally valid. It contains zero rows because the supplied `data/pos_transactions.csv` contains only its header.

