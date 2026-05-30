# API Test Report

## Result

**PASS**

All required endpoints returned HTTP `200`.

## Ingestion Checks

| Scenario | HTTP Status | Result |
| --- | ---: | --- |
| Valid event | 200 | Accepted `1` |
| Duplicate event | 200 | Duplicates `1`, accepted `0` |
| Malformed event | 200 | Rejected `1` with indexed field errors |
| Empty batch | 200 | Accepted `0`, rejected `0` |

## Analytics Responses

### Metrics

```json
{
  "unique_visitors": 3,
  "converted_visitors": 0,
  "conversion_rate": 0.0,
  "queue_depth": 2,
  "abandonment_rate": 1.0
}
```

The supplied POS CSV is empty, so zero conversion is correct.

### Funnel

| Stage | Count |
| --- | ---: |
| Entry | 3 |
| Zone visit | 0 |
| Billing queue | 0 |
| Purchase | 0 |

Monotonicity check: `entry >= zone >= billing >= purchase` is **PASS**.

### Heatmap

| Zone | Frequency | Average Dwell MS | Intensity |
| --- | ---: | ---: | ---: |
| Billing | 20 | 30000 | 41.67 |
| Makeup | 45 | 55770 | 93.75 |
| Skincare | 48 | 49335 | 100.00 |

All intensity scores are valid values from 0 to 100. `data_confidence` is `LOW`, which is correct below 20 entrance sessions.

### Anomalies

The endpoint returned the valid structure:

```json
{"store_id":"STORE_BLR_002","active_anomalies":[]}
```

