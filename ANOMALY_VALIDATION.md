# Anomaly Validation

## Billing Queue Spike

For at least three prior queue samples in the active 30-minute window:

```text
current_depth > rolling_mean + 2 * rolling_std
```

For cold start, depth `>= 5` is a documented fallback. Severity is `CRITICAL` at depth `>= 8`, otherwise `WARN`. Tests prove both modes.

## Conversion Drop

The API calculates daily conversion rates for the previous seven days where entry sessions exist. It emits `CONVERSION_DROP` when today's store has visitors and:

```text
today_conversion < seven_day_average
```

This follows the challenge rule directly. A production alerting layer can add duration-based suppression to avoid noise.

## Dead Zone

The API finds historically known non-billing zones and emits `DEAD_ZONE` when no `ZONE_ENTER` or `ZONE_DWELL` event occurred during the last 30 minutes.

## Operational Notes

The rules are deliberately auditable. At production scale, baselines should become time-of-week aware and alert suppression should prevent repeated notifications for the same condition.
