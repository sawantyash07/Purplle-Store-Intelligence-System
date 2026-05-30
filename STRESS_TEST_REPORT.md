# Stress Test Report

## Result

**PASS**

Measured HTTP scenarios were executed against the running Docker container.

| Scenario | Measured Result |
| --- | --- |
| Duplicate replay of 50 canonical events | HTTP `200`; accepted `0`, duplicates `50`, rejected `0` |
| Maximum valid batch | HTTP `200`; accepted `500`, duplicates `0`, rejected `0` |
| Oversized batch of 501 events | HTTP `413` in automated suite and prior container smoke validation |
| Empty batch | HTTP `200`; accepted `0`, duplicates `0`, rejected `0` |
| Invalid JSON | HTTP `400` in automated suite and prior container smoke validation |
| Stale feed | Inserted event at 11-minute lag; `/health` returned `STALE_FEED` with lag `660` |
| Empty store | Metrics returned zeros |
| Staff-only store | Metrics returned zero visitors and zero conversion |
| Zero-purchase store | Canonical store returned conversion `0.0` without error |
| Database outage | Automated test confirms structured HTTP `503` |

Stress records were inserted into a disposable Docker volume. The volume was deleted afterward and the canonical `326`-event stream was replayed into a clean final state.

