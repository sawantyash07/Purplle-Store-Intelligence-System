# Five-Minute Demo Script

**0:00-0:45 - Problem and architecture**

"This system turns anonymised store CCTV into actionable offline conversion analytics. Video stays at the edge. The central API receives compact behavioural events."

**0:45-1:45 - Detection**

"I run `pipeline.run_all` across configured clips. YOLO11 nano detects people, persistent tracking provides local IDs, and the trajectory interpreter emits entry, exit, re-entry, zone, dwell, and queue events. Output is globally sorted JSONL."

**1:45-2:20 - POS correlation**

"The POS correlator appends abandonment when a visitor leaves billing without a matching transaction. It is safe to rerun."

**2:20-3:10 - Live replay**

"I replay archived events with timestamps shifted to now. The dashboard polls every two seconds, proving the CV output is connected to live API metrics."

**3:10-4:15 - API**

"The API exposes metrics, funnel, heatmap, anomalies, and health. Funnel stages are session-based, staff is excluded, re-entry is deduplicated, queue spikes use a rolling baseline, and stale feeds surface after ten minutes."

**4:15-5:00 - Production readiness**

"Compose starts the API in one command. SQLite primary keys make replay idempotent. Logs include trace IDs and latency. The audited tests cover rubric edge cases with coverage above 85%. For 40 stores, I would add a durable broker and PostgreSQL or ClickHouse while keeping this event contract."

