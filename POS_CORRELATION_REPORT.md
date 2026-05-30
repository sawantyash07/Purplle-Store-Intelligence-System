# POS Correlation Report

## Input

`data/pos_transactions.csv` contains the required header and no transaction rows:

```csv
store_id,transaction_id,timestamp,basket_value_inr
```

## Commands and Results

```powershell
python -m pipeline.correlate_pos --events data/events.jsonl --pos data/pos_transactions.csv
python -m pipeline.correlate_pos --events data/events.jsonl --pos data/pos_transactions.csv
```

The first execution after fresh detection appended `20` `BILLING_QUEUE_ABANDON` events. The immediate repeat appended `0`. After fixing timestamp sorting, two verification runs both appended `0`.

## Result

**PASS**

| Check | Result | Measured Value |
| --- | --- | --- |
| Abandonment events generated | PASS | 20 |
| Duplicate abandonment session keys | PASS | 0 |
| Repeat-safe execution | PASS | Second execution adds 0 |
| Stream ordering after correlation | PASS | Chronological |
| Positive purchase conversion on supplied CSV | NOT APPLICABLE | Supplied CSV contains no transactions |

Positive conversion behavior remains covered by the automated API test suite using controlled POS records.

