# Final Acceptance Audit

> Historical strict-compliance audit. For the current post-fix submission
> readiness decision, see `FINAL_SUBMISSION_REASSESSMENT.md`.

## Evaluation Scope

This audit evaluates the repository against the supplied Round 2 problem
statement using actual execution results. It does not treat documentation of a
limitation as implementation of a requirement.

Evaluation date: 2026-05-30

Repository: `D:\Purplle Store Intelligence System`

## Executive Verdict

| Item | Result |
|---|---|
| Acceptance gate | **PASS** |
| Exact challenge compliance | **FAIL** |
| Weighted checklist compliance | **84.3%** |
| Estimated base rubric score | **70 / 100** |
| Dashboard bonus evidence | **Eligible: +8 points** |
| Advancement recommendation | **DO NOT RECOMMEND ADVANCE** |

The repository is operational and professionally packaged. The acceptance gate
passes. However, the generated data does not satisfy the challenge's explicit
cross-camera session identity requirement. This causes the required funnel to
report `entry=3` and `zone_visit=0` while the heatmap reports 20 billing, 45
makeup, and 48 skincare visits. The generated event stream also contains zero
`is_staff=true` events, so staff handling is not demonstrated on the supplied
clips.

Checklist compliance uses `PASS=1`, `PARTIAL=0.5`, and `FAIL=0` across the 54
requirements below: `(40 + 11 * 0.5) / 54 = 84.3%`.

## Problem Statement Mapping

| # | Requirement | Implementation | Evidence | Status |
|---:|---|---|---|---|
| 1 | CCTV clips are available | Five MP4 files are present | OpenCV probe opened all five files | PASS |
| 2 | Process raw CCTV clips | `pipeline.run_all` processes a clips directory | Actual run completed for five clips | PASS |
| 3 | Detect people | YOLO detector filters the person class | Pipeline produced tracked events from footage | PASS |
| 4 | Track movement | Tracker maintains per-track state | `pipeline/tracker.py:33-80` | PASS |
| 5 | Determine entry and exit direction | Threshold crossing is implemented | `pipeline/tracker.py:82-97`; no official ground truth supplied for accuracy measurement | PARTIAL |
| 6 | Assign one token per visit session | Tokens are generated from camera ID, tracker ID, and timestamp | `pipeline/tracker.py:9-11` | PARTIAL |
| 7 | Deduplicate the same visitor across overlapping cameras | No cross-camera Re-ID or token reconciliation exists | Camera ID is embedded into token seed at `pipeline/tracker.py:10`; canonical funnel evidence below | FAIL |
| 8 | Count group entry individually | Person tracks can emit individual crossings | Individual tracking exists; no group-entry ground-truth assertion was supplied | PARTIAL |
| 9 | Exclude staff from visitor analytics using classification | Tracker has an eight-minute continuous-presence proxy | `pipeline/tracker.py:60-61`; all 326 generated events have `is_staff=false` | FAIL |
| 10 | Handle re-entry without a new visitor count | Entrance-local recent exit matching is implemented | `pipeline/tracker.py:88-102`; generated stream includes 2 `REENTRY` events | PARTIAL |
| 11 | Preserve low-confidence evidence gracefully | Confidence is stored and propagated | Generated minimum confidence is `0.1803`; detector threshold prevents verification below threshold | PARTIAL |
| 12 | Detect billing queue joins | Billing zone emits queue join with depth metadata | `pipeline/tracker.py:71-72`; 29 events generated | PASS |
| 13 | Detect queue abandonment | POS correlation emits abandonment events | Correlation added 20 abandonment events and is repeat-safe | PASS |
| 14 | Handle empty-store periods | Empty responses return valid zero values | Automated edge test passed | PASS |
| 15 | Emit all eight required event types | All types exist in output | Actual counts below | PASS |
| 16 | Emit required event schema | Required fields are present | All 326 JSONL events validated | PASS |
| 17 | Use globally unique UUID-v4 event IDs | Emitter creates UUID-v4 IDs | 326 UUID-v4 IDs, all unique | PASS |
| 18 | Use ordered UTC timestamps | Timestamps are timezone-aware and ordered | JSONL validation passed | PASS |
| 19 | Include metadata keys | Metadata contains queue depth, SKU zone, and session sequence | JSONL validation passed | PASS |
| 20 | Do not suppress low-confidence events | Low-confidence events remain in output | 83 events have confidence below `0.3`; behavior below detector threshold is not observable | PARTIAL |
| 21 | Provide `POST /events/ingest` | FastAPI route exists | `app/main.py:81-104`; live requests passed | PASS |
| 22 | Limit ingest batches to 500 | Oversized batches return 413 | Live 501-event request returned 413 | PASS |
| 23 | Validate malformed events with structured partial errors | Per-item Pydantic validation is used | Live malformed request returned one indexed rejection | PASS |
| 24 | Make event ingest idempotent | Primary key plus `INSERT OR IGNORE` | `app/db.py:36`; `app/main.py:94-101`; duplicate request reported duplicates | PASS |
| 25 | Compute unique visitors | Metrics count entry-session tokens | Live response reports 3; cross-camera session identity is not reconciled | PARTIAL |
| 26 | Compute conversion rate | Purchases correlate to billing-session tokens | Zero-purchase output and synthetic positive-path test passed; canonical POS data contains no transactions | PARTIAL |
| 27 | Compute average dwell time | Zone dwell values are averaged | `app/analytics.py:79-100`; live output contains three zone averages | PASS |
| 28 | Compute queue depth | Latest queue-depth metadata is returned | Live output reports queue depth 2 | PASS |
| 29 | Compute abandonment rate | Explicit abandonments and unpurchased joins are counted | Live output reports abandonment rate 1.0 | PASS |
| 30 | Exclude staff events from analytics | Analytics SQL filters `is_staff=0` | `app/analytics.py:20-28` | PASS |
| 31 | Handle zero purchases | Division-by-zero fallback exists | Canonical metrics response returns conversion rate 0.0 | PASS |
| 32 | Update from replayed events | API reads newly ingested data | Replay followed by live API responses passed | PASS |
| 33 | Return an accurate entry-to-purchase funnel on generated data | Funnel intersects downstream tokens with entry tokens | `app/analytics.py:65-70`; canonical response incorrectly drops zone visits to zero | FAIL |
| 34 | Avoid double-counting re-entry in funnel | Set-based aggregation is implemented for matching IDs | `app/analytics.py:42-71`; camera-local IDs prevent end-to-end proof | PARTIAL |
| 35 | Aggregate heatmap frequency and dwell | Zone visitor sets and dwell averages are returned | `app/analytics.py:119-142`; live response passed | PASS |
| 36 | Label low-data heatmap confidence | Session count below 20 returns LOW | Live response returns `data_confidence="LOW"` | PASS |
| 37 | Detect queue spikes | Rolling baseline and cold-start rules exist | `app/analytics.py:150-172`; live injected scenario triggered correctly | PASS |
| 38 | Detect conversion drops | Current conversion is compared to seven-day average | `app/analytics.py:178-195`; live injected scenario triggered correctly | PASS |
| 39 | Detect dead zones | Known zones absent for 30 minutes are flagged | `app/analytics.py:173-177`; live injected scenario triggered correctly | PASS |
| 40 | Provide `GET /health` | Route returns store freshness | `app/main.py:163-165`; live healthy response passed | PASS |
| 41 | Detect stale feed after 10 minutes | Lag greater than 600 seconds degrades health | `app/analytics.py:199-212`; live 11-minute-old scenario returned `STALE_FEED` | PASS |
| 42 | Start with Docker Compose | API image builds and container starts | Clean `docker compose down -v` then `docker compose up --build -d` passed | PASS |
| 43 | Provide a connected dashboard | Root page polls live metrics every two seconds | `app/main.py:168-175`; browser verification passed with no console errors | PASS |
| 44 | Emit structured request logs | Middleware logs trace, store, endpoint, latency, count, and status | `app/main.py:34-53`; container logs verified | PASS |
| 45 | Return structured 503 on database failure | SQLite handler returns structured dependency error | `app/main.py:75-78`; automated test passed | PASS |
| 46 | Cover required edge cases with tests | API and pipeline suites exist | 16 tests passed | PASS |
| 47 | Maintain coverage above 70% | Pytest coverage is configured | Actual total coverage: 93.15% | PASS |
| 48 | Document setup in at most five commands | README includes a quick evaluation guide | README reviewed | PASS |
| 49 | Include AI-assisted design discussion | Design document contains the requested discussion | `docs/DESIGN.md` reviewed | PASS |
| 50 | Include implementation choices and alternatives | Choices document records engineering tradeoffs | `CHOICES.md` reviewed | PASS |
| 51 | Include prompt blocks above test files | Prompt headers are present | Test files reviewed | PASS |
| 52 | Document cross-camera limitation | Feasibility study exists | `CROSS_CAMERA_REID_FEASIBILITY.md` reviewed | PASS |
| 53 | Supply expected supporting dataset files | Footage is available locally; official layout, assertions, and populated POS rows are not available in the package | Repository and `data/pos_transactions.csv` inspected | PARTIAL |
| 54 | Demonstrate detector accuracy against ground truth | Pipeline runs and emits events | Official labeled ground truth was not supplied, so accuracy cannot be verified | PARTIAL |

## Input Validation

The folder `D:\Purplle Store Intelligence System\CCTV Footage` exists and
contains five readable MP4 files.

| File | FPS | Frames | Resolution | OpenCV readable |
|---|---:|---:|---|---|
| `CAM 1.mp4` | 29.9700 | 4193 | 1920x1080 | Yes |
| `CAM 2.mp4` | 29.9700 | 3774 | 1920x1080 | Yes |
| `CAM 3.mp4` | 29.9700 | 4436 | 1920x1080 | Yes |
| `CAM 4.mp4` | 25.0000 | 3647 | 1920x1080 | Yes |
| `CAM 5.mp4` | 25.0000 | 3465 | 1920x1080 | Yes |

Actual detection execution:

```text
python -m pipeline.run_all --clips "D:\Purplle Store Intelligence System\CCTV Footage" --output data/events.jsonl

CAM 1.mp4: 83 events
CAM 2.mp4: 127 events
CAM 3.mp4: 8 events
CAM 4.mp4: 0 events
CAM 5.mp4: 88 events
Detection subtotal: 306 events
POS correlation additions: 20 abandonment events
Final events.jsonl: 326 events
```

## Event Generation

All 326 lines in `data/events.jsonl` are valid JSON objects. Event IDs are
unique UUID-v4 values, timestamps are ordered, confidence values are in range,
and dwell values are non-negative.

| Event type | Count |
|---|---:|
| `ENTRY` | 1 |
| `EXIT` | 5 |
| `REENTRY` | 2 |
| `ZONE_ENTER` | 128 |
| `ZONE_EXIT` | 119 |
| `ZONE_DWELL` | 22 |
| `BILLING_QUEUE_JOIN` | 29 |
| `BILLING_QUEUE_ABANDON` | 20 |
| **Total** | **326** |

Additional schema evidence:

```text
invalid_json=0
duplicate_event_ids=0
uuid_v4_all=True
timestamps_ordered=True
confidence_min=0.1803
confidence_max=0.9036
confidence_below_0.3=83
is_staff_true=0
```

## API Compliance

The API was rebuilt from a clean Compose volume, replayed with all 326 events,
and queried live.

| Endpoint | Request | Actual response summary | Status |
|---|---|---|---|
| `POST /events/ingest` | Replay batches of 50, final batch 26 | Each batch returned accepted count, `duplicates=0`, `rejected=0` | PASS |
| `POST /events/ingest` | Repeat first three canonical events | `{"accepted":0,"duplicates":3,"rejected":0,"errors":[]}` | PASS |
| `POST /events/ingest` | `[{"event_id":"malformed"}]` | `accepted=0`, `duplicates=0`, `rejected=1`, indexed validation errors | PASS |
| `POST /events/ingest` | `[]` | `{"accepted":0,"duplicates":0,"rejected":0,"errors":[]}` | PASS |
| `POST /events/ingest` | 501 events | HTTP 413: maximum 500 events | PASS |
| `GET /stores/STORE_BLR_002/metrics` | GET | `unique_visitors=3`, `conversion_rate=0.0`, three dwell averages, `queue_depth=2`, `abandonment_rate=1.0` | PARTIAL |
| `GET /stores/STORE_BLR_002/funnel` | GET | `entry=3`, `zone_visit=0`, `billing_queue=0`, `purchase=0` | FAIL |
| `GET /stores/STORE_BLR_002/heatmap` | GET | Billing 20, makeup 45, skincare 48; confidence LOW | PASS |
| `GET /stores/STORE_BLR_002/anomalies` | GET | Canonical state: `active_anomalies=[]` | PASS |
| `GET /health` | GET | HTTP 200; `status="ok"`; store freshness status `OK` | PASS |

Canonical metrics response:

```json
{
  "store_id": "STORE_BLR_002",
  "window": "today",
  "unique_visitors": 3,
  "converted_visitors": 0,
  "conversion_rate": 0.0,
  "avg_dwell_ms_by_zone": {
    "BILLING": 30000.0,
    "MAKEUP": 55770.0,
    "SKINCARE": 49335.0
  },
  "queue_depth": 2,
  "abandonment_rate": 1.0
}
```

Canonical heatmap response:

```json
{
  "store_id": "STORE_BLR_002",
  "window": "today",
  "data_confidence": "LOW",
  "zones": [
    {"zone_id": "BILLING", "visit_frequency": 20, "avg_dwell_ms": 30000.0, "intensity": 41.67},
    {"zone_id": "MAKEUP", "visit_frequency": 45, "avg_dwell_ms": 55770.0, "intensity": 93.75},
    {"zone_id": "SKINCARE", "visit_frequency": 48, "avg_dwell_ms": 49335.0, "intensity": 100.0}
  ]
}
```

## Funnel Root Cause

The funnel discrepancy is not a heatmap error. It is caused by camera-local
visitor identities combined with conservative funnel intersection.

1. `pipeline/tracker.py:9-11` generates a visitor token from
   `camera_id`, `track_id`, and timestamp.
2. Entry-camera tokens therefore differ from floor-camera and billing-camera
   tokens for the same physical visitor.
3. `app/analytics.py:65-70` intersects zone, billing, and purchase sets with
   entry-session tokens.
4. The canonical event stream has no overlap between entry tokens and
   downstream camera tokens.
5. `app/analytics.py:128-140` computes heatmap visits directly from zone-local
   visitor sets, so those visits remain visible.

Observed token evidence:

```text
entry_sessions=3
zone_tokens=105
billing_tokens=20
entry_zone_overlap=0
entry_billing_overlap=0
```

Classification of root cause:

| Candidate | Result |
|---|---|
| Event type mismatch | No |
| Session aggregation issue | Yes, as a consequence |
| Visitor deduplication issue | **Yes: primary cause** |
| Funnel query bug | No: the conservative intersection behaves as implemented, but cannot satisfy the required funnel without cross-camera identity |

## Anomaly Validation

Each required anomaly was triggered with a controlled live API scenario. The
Compose volume was reset after testing and the canonical 326-event stream was
replayed.

| Anomaly | Implementation | Actual evidence | Status |
|---|---|---|---|
| Queue spike | Rolling baseline or cold-start threshold at `app/analytics.py:150-172` | Injected queue depths `1,2,1,6`; returned `BILLING_QUEUE_SPIKE`, severity `WARN`, queue depth 6 | PASS |
| Conversion drop | Seven-day baseline comparison at `app/analytics.py:178-195` | Injected seven historical converted sessions and one current unconverted session; returned `CONVERSION_DROP`, current rate 0, baseline 1.0 | PASS |
| Dead zone | Known zone absent from last 30 minutes at `app/analytics.py:173-177` | Injected old zone visit; returned `DEAD_ZONE`, severity `WARN` | PASS |
| Stale feed | Store lag greater than 600 seconds at `app/analytics.py:199-212` | Injected 11-minute-old event; `/health` returned `degraded` and `STALE_FEED` | PASS |

## Health Validation

Healthy canonical response:

```json
{
  "status": "ok",
  "stores": {
    "STORE_BLR_002": {
      "last_event_timestamp": "2026-05-30T15:25:55.555236Z",
      "lag_seconds": 0,
      "status": "OK"
    }
  },
  "warnings": []
}
```

The stale-feed live scenario returned a degraded service state and a
`STALE_FEED` warning after the store's latest event was shifted 11 minutes into
the past.

## Database Validation

After the clean rebuild and canonical replay:

```text
events=326
transactions=0
duplicate_event_ids=0
duplicate_transaction_ids=0
```

The database enforces primary keys for both event IDs and transaction IDs in
`app/db.py:35-57`. Replay and direct duplicate-ingest tests reported duplicates
without inserting duplicate rows.

## Docker and Dashboard Validation

Clean-state command:

```text
docker compose down -v
docker compose up --build -d
```

The image built successfully and the API container remained up on port 8000.
The dashboard at `http://localhost:8000` loaded in the browser, displayed
visitors `3`, conversion `0.0%`, and queue depth `2`, refreshed live metrics,
and produced no browser console errors.

## Test Validation

Actual command:

```text
pytest --cov=app --cov=pipeline --cov-report=term-missing
```

Actual result:

```text
16 passed
TOTAL: 511 statements, 35 missed, 93.15% coverage
```

Coverage exceeds the required 70% threshold.

## Known Limitation Assessment

`CROSS_CAMERA_REID_FEASIBILITY.md` accurately documents the camera-local
identity limitation and recommends against a risky late implementation.
That is an appropriate engineering decision for preserving a stable
submission, but it does not satisfy the challenge requirement.

The limitation invalidates full compliance because:

1. The problem statement explicitly requires overlap-camera deduplication.
2. The visitor token is required to represent a visit session, not a
   camera-local track.
3. Funnel reporting is a required endpoint and central north-star metric.
4. The canonical generated stream demonstrates the resulting funnel failure.

## Strengths

1. The system runs end to end from Docker Compose and serves a connected live
   dashboard.
2. The event stream contains all eight required event types with valid,
   ordered, unique UUID-v4 IDs.
3. Ingest is idempotent, bounded to 500 events, and reports structured partial
   validation errors.
4. All four required anomaly types and healthy/degraded feed states were
   demonstrated with live execution.
5. The automated suite passes with 93.15% coverage, comfortably above the
   challenge threshold.

## Weaknesses and Risks

1. Cross-camera identities are not reconciled, violating an explicit challenge
   requirement.
2. The required funnel materially under-reports downstream stages on the
   repository's own generated data.
3. Staff classification is only an eight-minute presence proxy and produces
   zero staff events on the supplied short clips.
4. Official labeled ground truth is absent, so entry/exit, group-entry, and
   detection accuracy cannot be measured.
5. The supplied POS CSV contains no transaction rows, so canonical conversion
   remains zero and the positive conversion path relies on controlled tests.

## Rubric Score Estimate

| Rubric area | Maximum | Estimated score | Evidence-based reasoning |
|---|---:|---:|---|
| Detection and event generation | 30 | 15 | Pipeline and schema work, but ground-truth accuracy is unverified, cross-camera deduplication fails, and staff handling is not demonstrated |
| Intelligence API | 35 | 22 | Required endpoints, metrics, heatmap, anomalies, health, and ingest work; required funnel is materially incorrect on canonical generated data |
| Production readiness | 20 | 19 | Compose, logging, graceful 503 handling, test suite, and coverage are strong |
| AI-assisted engineering evidence | 15 | 14 | Required documentation and prompt evidence are present |
| **Base score** | **100** | **70** |  |
| Connected dashboard bonus | **+10** | **+8** | Live connected dashboard is functional and verified |

## Acceptance Gate

| Gate item | Evidence | Status |
|---|---|---|
| `docker compose up` starts the API | Clean Compose build and start passed | PASS |
| README explains detection pipeline execution | README reviewed | PASS |
| `POST /events/ingest` accepts events | Live replay accepted 326 events | PASS |
| `GET /stores/{id}/metrics` returns JSON | Live request returned HTTP 200 JSON | PASS |
| Design and choices documents exist | Documents reviewed | PASS |

## Final Recommendation

**DO NOT RECOMMEND ADVANCE**

The submission passes the minimum acceptance gate and demonstrates substantial
engineering quality. It does not satisfy the challenge requirements exactly as
written because cross-camera visitor deduplication is absent and the required
funnel is incorrect on the canonical generated event stream. Staff exclusion
is also not demonstrated by the supplied footage. These are core behavioral
requirements rather than presentation issues.

## Overall Status

**FAIL**

The repository is stable and runnable, but it is not ready for submission as a
fully compliant implementation without further functional changes.
