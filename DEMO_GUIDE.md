# Demo Guide

## 1. Start Docker

```powershell
cd "D:\Purplle Store Intelligence System"
docker compose up --build -d
curl.exe http://localhost:8000/health
```

## 2. Run Detection

```powershell
python -m pip install -r requirements.txt
python -m pipeline.run_all --clips "C:\Users\ysawa\AppData\Local\Temp" --output data/events.jsonl --stride 10
```

## 3. Correlate POS

```powershell
python -m pipeline.correlate_pos --events data/events.jsonl --pos data/pos_transactions.csv
```

## 4. Replay Events

```powershell
python -m pipeline.replay --events data/events.jsonl --shift-to-now --batch-size 20 --delay 1
```

## 5. Open Dashboard

Open [http://localhost:8000](http://localhost:8000) while replay runs. Visitor, conversion, and queue metrics refresh every two seconds.

## 6. Verify Intelligence Endpoints

```powershell
curl.exe http://localhost:8000/stores/STORE_BLR_002/metrics
curl.exe http://localhost:8000/stores/STORE_BLR_002/funnel
curl.exe http://localhost:8000/stores/STORE_BLR_002/heatmap
curl.exe http://localhost:8000/stores/STORE_BLR_002/anomalies
curl.exe http://localhost:8000/health
```

## 7. Demonstrate Idempotency

Replay the same file again. The ingest response reports duplicates rather than inserting a second copy.

