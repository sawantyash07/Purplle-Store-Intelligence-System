# Detection Pipeline Report

## Command

```powershell
python -m pipeline.run_all --clips "D:\Purplle Store Intelligence System\CCTV Footage" --output data/events.jsonl
```

## Execution Result

**PASS**

The default-stride detection run completed without errors or skipped configured videos.

| Video | Result | Events |
| --- | --- | ---: |
| `CAM 1.mp4` | Processed | 83 |
| `CAM 2.mp4` | Processed | 127 |
| `CAM 3.mp4` | Processed | 8 |
| `CAM 4.mp4` | Processed | 0 |
| `CAM 5.mp4` | Processed | 88 |
| **Total before POS correlation** |  | **306** |

## Event Counts After POS Correlation

| Type | Count |
| --- | ---: |
| `ENTRY` | 1 |
| `EXIT` | 5 |
| `REENTRY` | 2 |
| `ZONE_ENTER` | 128 |
| `ZONE_EXIT` | 119 |
| `ZONE_DWELL` | 22 |
| `BILLING_QUEUE_JOIN` | 29 |
| `BILLING_QUEUE_ABANDON` | 20 |
| **Total** | **326** |

## Notes

- `data/events.jsonl` exists and validates.
- `CAM 4.mp4` produced zero events. This is not a pipeline error; the backroom view is heavily occluded and no person track met the retained detection path during this run.
- POS correlation initially exposed an ordering bug because appended abandonment events were placed at end-of-file. The correlator was fixed to rewrite the combined stream chronologically, and a regression test was added.

