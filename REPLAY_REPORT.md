# Replay Report

## Command

```powershell
python -m pipeline.replay --events data/events.jsonl --shift-to-now
```

## Result

**PASS**

All `326` canonical events were accepted into a clean Docker volume:

| Batch | Accepted | Duplicates | Rejected |
| ---: | ---: | ---: | ---: |
| 1 | 50 | 0 | 0 |
| 2 | 50 | 0 | 0 |
| 3 | 50 | 0 | 0 |
| 4 | 50 | 0 | 0 |
| 5 | 50 | 0 | 0 |
| 6 | 50 | 0 | 0 |
| 7 | 26 | 0 | 0 |
| **Total** | **326** | **0** | **0** |

The `--shift-to-now` option preserved relative event spacing while making the dashboard and `/health` feed freshness meaningful for a live demo.

