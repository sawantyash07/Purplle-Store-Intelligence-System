from __future__ import annotations

import csv
import io
import json
import logging
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.analytics import anomalies, funnel, health, heatmap, metrics
from app.db import database, event_values, init_db
from app.models import BatchResult, StoreEvent, Transaction

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("store-intelligence")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Purplle Store Intelligence System", version="1.0.0", lifespan=lifespan)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        request.state.trace_id = trace_id
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["x-trace-id"] = trace_id
            return response
        finally:
            logger.info(json.dumps({
                "trace_id": trace_id,
                "store_id": request.path_params.get("id") or getattr(request.state, "store_id", None),
                "endpoint": request.url.path,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "event_count": getattr(request.state, "event_count", None),
                "status_code": status_code,
            }))


app.add_middleware(RequestLoggingMiddleware)


async def list_payload(request: Request, item_name: str) -> list:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Request body must contain valid JSON.") from exc
    if not isinstance(payload, list):
        raise HTTPException(status_code=422, detail=f"Request body must be an array of {item_name}.")
    return payload


@app.exception_handler(Exception)
async def unexpected_error(_: Request, exc: Exception):
    logger.exception("unhandled error")
    return JSONResponse(status_code=503, content={"error": "SERVICE_UNAVAILABLE", "detail": "Storage or service dependency unavailable."})


@app.exception_handler(sqlite3.Error)
async def database_error(_: Request, exc: sqlite3.Error):
    logger.exception("database unavailable")
    return JSONResponse(status_code=503, content={"error": "SERVICE_UNAVAILABLE", "detail": "Storage dependency unavailable."})


@app.post("/events/ingest", response_model=BatchResult)
async def ingest_events(request: Request):
    payload = await list_payload(request, "events")
    if len(payload) > 500:
        raise HTTPException(status_code=413, detail="A maximum of 500 events is accepted per batch.")
    request.state.event_count = len(payload)
    request.state.store_id = ",".join(sorted({str(item.get("store_id")) for item in payload if isinstance(item, dict) and item.get("store_id")})) or None
    accepted = duplicates = 0
    errors = []
    with database() as db:
        for index, raw in enumerate(payload):
            try:
                event = StoreEvent.model_validate(raw)
                result = db.execute(
                    "INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    event_values(event),
                )
                if result.rowcount:
                    accepted += 1
                else:
                    duplicates += 1
            except ValidationError as exc:
                errors.append({"index": index, "event_id": raw.get("event_id") if isinstance(raw, dict) else None, "errors": exc.errors(include_url=False)})
    return BatchResult(accepted=accepted, duplicates=duplicates, rejected=len(errors), errors=errors)


@app.post("/pos/ingest", response_model=BatchResult)
async def ingest_pos(request: Request):
    payload = await list_payload(request, "transactions")
    accepted = duplicates = 0
    errors = []
    with database() as db:
        for index, raw in enumerate(payload):
            try:
                transaction = Transaction.model_validate(raw)
                data = transaction.model_dump(mode="json")
                result = db.execute("INSERT OR IGNORE INTO transactions VALUES (?,?,?,?)", (data["transaction_id"], data["store_id"], data["timestamp"], data["basket_value_inr"]))
                accepted += int(bool(result.rowcount))
                duplicates += int(not result.rowcount)
            except ValidationError as exc:
                errors.append({"index": index, "transaction_id": raw.get("transaction_id") if isinstance(raw, dict) else None, "errors": exc.errors(include_url=False)})
    return BatchResult(accepted=accepted, duplicates=duplicates, rejected=len(errors), errors=errors)


@app.post("/pos/upload-csv", response_model=BatchResult)
async def upload_pos_csv(file: UploadFile = File(...)):
    reader = csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig")))
    accepted = duplicates = 0
    errors = []
    with database() as db:
        for index, raw in enumerate(reader):
            try:
                transaction = Transaction.model_validate(raw)
                data = transaction.model_dump(mode="json")
                result = db.execute("INSERT OR IGNORE INTO transactions VALUES (?,?,?,?)", (data["transaction_id"], data["store_id"], data["timestamp"], data["basket_value_inr"]))
                accepted += int(bool(result.rowcount))
                duplicates += int(not result.rowcount)
            except ValidationError as exc:
                errors.append({"index": index, "transaction_id": raw.get("transaction_id"), "errors": exc.errors(include_url=False)})
    return BatchResult(accepted=accepted, duplicates=duplicates, rejected=len(errors), errors=errors)


@app.get("/stores/{id}/metrics")
def store_metrics(id: str):
    return metrics(id)


@app.get("/stores/{id}/funnel")
def store_funnel(id: str):
    return funnel(id)


@app.get("/stores/{id}/heatmap")
def store_heatmap(id: str):
    return heatmap(id)


@app.get("/stores/{id}/anomalies")
def store_anomalies(id: str):
    return anomalies(id)


@app.get("/health")
def service_health():
    return health()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """<!doctype html><html><head><title>Store Intelligence</title>
    <style>body{font:16px system-ui;background:#f6f2fb;color:#251435;margin:32px}.cards{display:flex;gap:16px;flex-wrap:wrap}.card{background:white;padding:18px;border-radius:12px;min-width:180px;box-shadow:0 2px 10px #ddd}b{font-size:30px;color:#7c3aed}pre{background:#21152c;color:#eee;padding:16px;border-radius:12px}</style></head>
    <body><h1>Purplle Store Intelligence</h1><p>Live metrics for <code>STORE_BLR_002</code></p><div class=cards>
    <div class=card>Visitors<br><b id=v>0</b></div><div class=card>Conversion<br><b id=c>0%</b></div><div class=card>Queue depth<br><b id=q>0</b></div></div>
    <h2>Live response</h2><pre id=json></pre><script>
    async function refresh(){let r=await fetch('/stores/STORE_BLR_002/metrics');let d=await r.json();v.textContent=d.unique_visitors;c.textContent=(d.conversion_rate*100).toFixed(1)+'%';q.textContent=d.queue_depth;json.textContent=JSON.stringify(d,null,2)}refresh();setInterval(refresh,2000)</script></body></html>"""
