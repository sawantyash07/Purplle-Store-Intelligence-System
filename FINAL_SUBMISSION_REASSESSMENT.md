# Final Submission Reassessment

## Scope

This reassessment covers objectively verified submission blockers only. It
does not redesign tracking, change visitor identity generation, or introduce
cross-camera Re-ID.

Evaluation date: 2026-05-30

## Executive Result

| Item | Result |
|---|---|
| Submission package verification | **PASS** |
| Acceptance gate | **PASS** |
| Exact challenge checklist compliance | **84.3%** |
| Estimated base rubric score | **70 / 100** |
| Dashboard bonus evidence | **Eligible: +8 points** |
| Submission recommendation | **READY FOR SUBMISSION WITH KNOWN LIMITATIONS** |

The two objectively verified submission blockers were resolved:

1. Root-level `DESIGN.md` and `CHOICES.md` references now exist.
2. The canonical JSONL timestamp-ordering defect was fixed and validated.

Cross-camera identity remains intentionally unchanged after the documented
NO-GO feasibility review. The funnel limitation remains a known functional
limitation, not a resolved requirement.

## Root-Level Document Check

| Document | Before | Action | After |
|---|---|---|---|
| `DESIGN.md` | Missing at repository root; canonical content existed at `docs/DESIGN.md` | Added root reference preserving canonical content | PASS |
| `CHOICES.md` | Missing at repository root; canonical content existed at `docs/CHOICES.md` | Added root reference preserving canonical content | PASS |

## Timestamp Ordering Resolution

The original canonical artifact contained 9 adjacent timestamp inversions.
Investigation found lexical sorting of ISO timestamp strings in both
`pipeline.run_all.sort_events` and `pipeline.correlate_pos.add_abandonment_events`.

Both paths now sort parsed datetimes. The fix changes ordering only: no event
schema, API, tracker, or visitor-ID behavior changed.

Post-fix validation:

```text
events=326
adjacent_inversions=0
duplicate_event_ids=0
billing_queue_abandon_events_added=0
```

The correlation rerun added no events. It only re-sorted the derived artifact.
See `TIMESTAMP_ORDERING_ANALYSIS.md` for the original offending rows and root
cause.

## Staff Classification Review

| Question | Result |
|---|---|
| Feature implemented? | Yes: long-presence proxy |
| Analytics exclusion implemented? | Yes: staff rows are filtered |
| Automated exclusion tested? | Yes |
| Demonstrated by supplied footage? | No |
| Canonical `is_staff=true` events | `0 / 326` |

No staff events were fabricated. See `STAFF_CLASSIFICATION_REVIEW.md`.

## Final Test Validation

Actual command:

```text
python -m pytest --cov=app --cov=pipeline --cov-report=term-missing
```

Actual result:

```text
16 passed
TOTAL: 511 statements, 35 missed, 93.15% coverage
```

Coverage remains above the requested 90% reassessment threshold.

## Docker and Replay Validation

Actual clean-state flow:

```text
docker compose down -v
docker compose up --build -d
python -m pipeline.replay --events data\events.jsonl --shift-to-now --batch-size 50 --delay 0
```

Replay accepted all seven batches:

```text
accepted=326
duplicates=0
rejected=0
```

Mounted SQLite validation:

```text
events=326
transactions=0
duplicate_event_ids=0
```

## Live Endpoint Validation

| Endpoint | HTTP status | Actual result | Status |
|---|---:|---|---|
| `GET /stores/STORE_BLR_002/metrics` | 200 | Visitors 3, conversion 0.0, queue depth 2, abandonment 1.0 | PASS |
| `GET /stores/STORE_BLR_002/heatmap` | 200 | Billing 20, makeup 45, skincare 48; confidence LOW | PASS |
| `GET /health` | 200 | Service `ok`, store freshness `OK`, no warnings | PASS |
| `GET /stores/STORE_BLR_002/funnel` | 200 | Entry 3, zone 0, billing 0, purchase 0 | PARTIAL |
| `GET /stores/STORE_BLR_002/anomalies` | 200 | Valid canonical empty anomaly list | PASS |
| Dashboard `/` | 200 | Rendered visitors 3, conversion 0.0%, queue depth 2; no console errors | PASS |

## Acceptance Gate

| Gate item | Evidence | Status |
|---|---|---|
| Compose starts the API | Clean build and startup passed | PASS |
| README explains detection execution | Reviewed | PASS |
| Event ingest accepts events | Canonical replay accepted 326 events | PASS |
| Metrics endpoint returns JSON | Live HTTP 200 response verified | PASS |
| Root-level design and choices entry points exist | Added references to canonical documents | PASS |

## Strengths

1. Docker Compose, replay, API, and connected dashboard work end to end.
2. The canonical stream has 326 schema-valid, unique, chronologically ordered
   events spanning all eight required event types.
3. The low-risk ordering correction is narrow and covered by a regression test.
4. The complete deterministic suite passes with 93.15% statement coverage.
5. Known identity, calibration, POS, and staff-evidence limitations are stated
   explicitly rather than hidden behind inflated claims.

## Remaining Weaknesses

1. Cross-camera identity resolution is not implemented.
2. The canonical funnel under-reports downstream stages because camera-local
   IDs cannot be linked safely.
3. Staff exclusion is implemented and tested but not demonstrated by the
   supplied clips.
4. Official camera calibration and labelled ground truth were not supplied.
5. The canonical POS CSV contains no transactions, so the live conversion rate
   remains zero.

## Final Recommendation

**READY FOR SUBMISSION WITH KNOWN LIMITATIONS**

The objectively verified packaging and timestamp blockers are resolved without
changing tracker behavior, visitor IDs, APIs, or the event schema. The
repository is stable, reproducible, and honest about the unresolved
cross-camera funnel limitation. This is a submission-readiness PASS, not a
claim of complete compliance with every challenge behavior.

## Overall Status

**PASS**
