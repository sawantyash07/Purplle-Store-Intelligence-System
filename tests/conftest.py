# PROMPT: Build a pytest fixture that isolates SQLite state for every FastAPI test.
# CHANGES MADE: Kept the fixture small and reset the app-level database path directly.
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.db as db_module
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    with TestClient(app) as test_client:
        yield test_client
