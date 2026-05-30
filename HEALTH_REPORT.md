# Health Endpoint Report

Endpoint: `GET /health`

## Pre-Replay Result

After starting against an empty Docker volume:

```json
{"status":"ok","stores":{},"warnings":[]}
```

## Post-Replay Result

After replaying the canonical stream:

```json
{
  "status": "ok",
  "stores": {
    "STORE_BLR_002": {
      "last_event_timestamp": "2026-05-30T14:34:11.803766Z",
      "lag_seconds": 0,
      "status": "OK"
    }
  },
  "warnings": []
}
```

## Result

**PASS**

The endpoint returned HTTP `200`, exposed service status, and reported the store's last event timestamp.

