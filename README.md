# Purplle Store Intelligence System

An end-to-end offline retail analytics system for the Purplle engineering challenge. It converts anonymised CCTV clips into structured visitor events, correlates billing activity with POS transactions, serves live intelligence through FastAPI, and renders a lightweight dashboard.

## Architecture

```text
Raw CCTV clips
    |
    v
YOLO11 nano person detector + persistent tracker
    |
    v
Trajectory interpreter
ENTRY / EXIT / REENTRY / zone dwell / billing queue
    |
    v
JSONL event stream ---> POS correlation ---> BILLING_QUEUE_ABANDON
    |
    v
POST /events/ingest
    |
    v
SQLite WAL database ---> Metrics / Funnel / Heatmap / Anomalies / Health
    |
    v
Live dashboard at http://localhost:8000
```

Raw footage stays outside the API container. Only compact behavioural events are ingested centrally, which keeps the acceptance path lightweight and mirrors an edge-processing deployment.

## Verified Results

| Signal | Verified result |
| --- | ---: |
| CCTV videos processed | 5 |
| Valid events generated | 326 |
| Duplicate event IDs | 0 |
| Timestamp inversions | 0 |
| Tests passed | 16 |
| Statement coverage | 93.15% |
| Docker deployment | Verified |
| Dashboard | Verified |
| Metrics API | Verified |
| Heatmap API | Verified |
| Health endpoint | Verified |

## Challenge Requirements Coverage

| Requirement | Status |
| --- | --- |
| CCTV Processing | ✅ |
| Person Detection & Tracking | ✅ |
| Entry / Exit Detection | ✅ |
| Re-entry Detection | ✅ |
| Queue Detection | ✅ |
| Queue Abandonment Detection | ✅ |
| Metrics API | ✅ |
| Funnel API | ✅ Conservative due to documented Re-ID limitation |
| Heatmap API | ✅ |
| Anomaly Detection | ✅ |
| Health Monitoring | ✅ |
| Docker Deployment | ✅ |
| Dashboard | ✅ |
| Test Coverage > 70% | ✅ 93.15% |

## Quick Evaluation Guide

A reviewer can verify the containerized intelligence surface in less than five minutes:

```powershell
cd "<repository-path>"
docker compose up --build -d
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/stores/STORE_BLR_002/metrics
start http://localhost:8000
```

If a locally generated `data/events.jsonl` artifact is available, populate live metrics in seconds:

```powershell
python -m pipeline.replay --events data/events.jsonl --shift-to-now --batch-size 50 --delay 0
```

Then inspect the required analytics endpoints:

```powershell
curl.exe http://localhost:8000/stores/STORE_BLR_002/metrics
curl.exe http://localhost:8000/stores/STORE_BLR_002/funnel
curl.exe http://localhost:8000/stores/STORE_BLR_002/heatmap
curl.exe http://localhost:8000/stores/STORE_BLR_002/anomalies
```

Expected verified results after replaying the locally generated canonical stream:

| Signal | Value |
| --- | ---: |
| Canonical events ingested | 326 |
| Unique visitors | 3 |
| Current queue depth | 2 |
| Heatmap zones | Billing, Makeup, Skincare |
| Feed health | `OK` |

`data/events.jsonl` is generated locally and intentionally ignored by Git because it is derived from restricted challenge footage. To reproduce it, follow **Run Detection** below.

## Folder Structure

```text
app/                 FastAPI service, SQLite layer, analytics, schema models
pipeline/            Detection, tracking, event emission, POS correlation, replay
config/              Camera roles, inferred zones, and clip timestamps
data/                Generated JSONL events and POS CSV input
docs/                Design rationale and engineering choices
tests/               API and pipeline tests with AI prompt blocks
docker-compose.yml   One-command API startup
Dockerfile           Minimal API image without the large CV runtime
```

## Start the API

Docker Desktop must be running. From the project directory:

```powershell
cd "<repository-path>"
docker compose up --build -d
curl.exe http://localhost:8000/health
```

The live dashboard is available at [http://localhost:8000](http://localhost:8000). Interactive OpenAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Run Detection

Install the local computer-vision dependencies:

```powershell
python -m pip install -r requirements.txt
```

Process all configured clips:

```powershell
python -m pipeline.run_all `
  --clips "<repository-path>\CCTV Footage" `
  --output data/events.jsonl
```

The first run downloads `yolo11n.pt`. `pipeline.run_all` processes every configured clip and globally sorts emitted events by timestamp. Reduce `--stride` for higher recall at the cost of CPU time.

## Correlate POS Transactions

Place transactions in `data/pos_transactions.csv` with this schema:

```csv
store_id,transaction_id,timestamp,basket_value_inr
STORE_BLR_002,TXN_00441,2026-03-03T14:38:12Z,1240.00
```

Append billing abandonment events after time-window correlation:

```powershell
python -m pipeline.correlate_pos `
  --events data/events.jsonl `
  --pos data/pos_transactions.csv
```

The operation is idempotent: rerunning it does not append duplicate abandonment events.

## Replay Events

Replay events into the API with timestamps shifted to the current time for the live demo:

```powershell
python -m pipeline.replay `
  --events data/events.jsonl `
  --shift-to-now `
  --batch-size 50 `
  --delay 0.5
```

The dashboard polls the metrics endpoint every two seconds and updates while batches arrive.

## API Examples

```powershell
curl.exe http://localhost:8000/stores/STORE_BLR_002/metrics
curl.exe http://localhost:8000/stores/STORE_BLR_002/funnel
curl.exe http://localhost:8000/stores/STORE_BLR_002/heatmap
curl.exe http://localhost:8000/stores/STORE_BLR_002/anomalies
curl.exe http://localhost:8000/health
curl.exe -X POST -F "file=@data/pos_transactions.csv" http://localhost:8000/pos/upload-csv
```

`POST /events/ingest` accepts arrays of up to 500 events. Each event is independently validated, valid siblings are stored, malformed items are reported by index, and repeated `event_id` values are safely deduplicated.

## Run Tests

```powershell
python -m pytest --cov=app --cov=pipeline --cov-report=term-missing
```

The audited suite contains 16 deterministic tests with 93.15% statement coverage, exceeding the challenge's 70% requirement.

## Supplied-Data Assumptions

The verified CCTV folder contains five clips but omits the referenced official `store_layout.json`, populated `pos_transactions.csv`, `sample_events.jsonl`, and `assertions.py`. The checked-in layout is therefore an inferred, editable default:

| Clip | Role | Notes |
| --- | --- | --- |
| `CAM 1.mp4` | Additional floor view | Skincare coverage |
| `CAM 2.mp4` | Main floor | Makeup and skincare zones |
| `CAM 3.mp4` | Entrance | Directional threshold crossing |
| `CAM 4.mp4` | Additional floor view | Backroom coverage |
| `CAM 5.mp4` | Billing | Billing-region queue tracking |

Replace `config/store_layout.json` coordinates with official definitions if those files become available.

## Known Limitations

- Cross-camera Re-ID is conservative. Floor-camera tracker tokens enrich heatmaps but are not guessed into entrance sessions.
- The funnel is intentionally conservative: camera-local tokens are intersected with authoritative entrance sessions. Without labelled cross-camera Re-ID, the verified stream reports downstream funnel stages as zero while heatmap activity remains available. See `CROSS_CAMERA_REID_FEASIBILITY.md`.
- Staff classification uses long continuous presence as a transparent proxy because no labelled uniform data was supplied.
- Queue depth is region-based, not pose-aware. A person inside the billing polygon is considered part of the queue.
- SQLite is appropriate for this single-node submission. A multi-store deployment should move ingestion behind a durable broker and persist to PostgreSQL or a time-series store.

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Docker pipe not found | Start Docker Desktop, wait for `docker info`, then rerun Compose. |
| Port `8000` already in use | Stop the existing service with `docker compose down` or change the Compose port mapping. |
| YOLO model download fails | Confirm internet access or place `yolo11n.pt` in the project root. |
| No events from a clip | Lower `--stride`, inspect zone coordinates, and check whether the angle is heavily occluded. |
| Dashboard shows stale feed | Replay with `--shift-to-now`; archived clip timestamps are intentionally historical. |

## Review Material

Start with:

| Document | Purpose |
| --- | --- |
| `EXECUTIVE_SUMMARY.md` | One-page evaluator overview |
| `RESULTS.md` | Measured execution results |
| `ARCHITECTURE_DECISIONS.md` | Key design rationale |
| `SYSTEM_VERIFICATION_REPORT.md` | End-to-end evidence |
| `LIMITATIONS.md` | Explicit boundaries and future work |
| `EVALUATOR_SCORECARD.md` | Rubric-based score estimate |
| `TIMESTAMP_ORDERING_ANALYSIS.md` | Verified timestamp-ordering root cause and correction |
| `STAFF_CLASSIFICATION_REVIEW.md` | Staff exclusion implementation and dataset evidence |
| `FINAL_SUBMISSION_REASSESSMENT.md` | Current submission-readiness decision |
| `FINAL_SUBMISSION_SANITY_CHECK.md` | Final documentation and packaging audit |
| `FINAL_REPOSITORY_HYGIENE_REPORT.md` | Final repository hygiene result |

Additional focused reports remain available for audit evidence, demo preparation, and interview follow-up.
