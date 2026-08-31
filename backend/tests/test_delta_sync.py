import os
import sys
import time
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import backend.app.models
from backend.app.database import Base
from backend.app.main import app
from backend.app.models import EventLog, OperationalIncident, OutboxItem
from backend.app.sync.delta_sync import DeltaSyncEngine
from backend.app.sync.sync_engine import resolve_lww_conflict

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    db.query(EventLog).delete()
    db.query(OperationalIncident).delete()
    db.query(OutboxItem).delete()
    db.commit()
    try:
        yield db
    finally:
        db.close()


def test_delta_sync_vector_calculation(db_session):
    """Verify local vector calculation and missing event delta computation."""
    t0 = 1000.0
    t1 = 1010.0
    t2 = 1020.0

    # Node Alpha events
    db_session.add(
        EventLog(
            event_id="ev-a-1",
            event_type="incident.created",
            origin_node_id="NODE-ALPHA",
            timestamp=t0,
            payload=json.dumps({"title": "Fire"}),
        )
    )
    db_session.add(
        EventLog(
            event_id="ev-a-2",
            event_type="incident.updated",
            origin_node_id="NODE-ALPHA",
            timestamp=t2,
            payload=json.dumps({"title": "Fire Escalated"}),
        )
    )

    # Node Beta event
    db_session.add(
        EventLog(
            event_id="ev-b-1",
            event_type="report.created",
            origin_node_id="NODE-BETA",
            timestamp=t1,
            payload=json.dumps({"description": "Smoke sighted"}),
        )
    )
    db_session.commit()

    # 1. Verify get_local_vector
    vector = DeltaSyncEngine.get_local_vector(db_session)
    assert "NODE-ALPHA" in vector
    assert vector["NODE-ALPHA"]["last_timestamp"] == t2
    assert vector["NODE-BETA"]["last_timestamp"] == t1

    # 2. Remote peer only saw NODE-ALPHA up to t0, and never saw NODE-BETA
    remote_vector = {
        "NODE-ALPHA": {"last_timestamp": t0, "last_clock": 1},
    }

    missing = DeltaSyncEngine.calculate_missing_events(db_session, remote_vector)
    missing_ids = [m["event_id"] for m in missing]
    assert "ev-a-2" in missing_ids  # Newer than t0
    assert "ev-b-1" in missing_ids  # NODE-BETA completely missing on remote
    assert "ev-a-1" not in missing_ids  # Remote already has it


def test_lww_conflict_resolution():
    """Verify Last-Writer-Wins tie-breaking logic."""
    # Scenario 1: Remote timestamp is newer
    local_rec = {
        "status": "in_progress",
        "timestamp": 100.0,
        "device_clock": 5,
        "device_id": "NODE-A",
    }
    remote_rec = {
        "status": "resolved",
        "timestamp": 120.0,
        "device_clock": 4,
        "device_id": "NODE-B",
    }
    winner, source = resolve_lww_conflict(local_rec, remote_rec)
    assert source == "REMOTE"
    assert winner["status"] == "resolved"

    # Scenario 2: Timestamps equal, higher device clock wins
    local_rec2 = {
        "status": "open",
        "timestamp": 100.0,
        "device_clock": 10,
        "device_id": "NODE-A",
    }
    remote_rec2 = {
        "status": "closed",
        "timestamp": 100.0,
        "device_clock": 8,
        "device_id": "NODE-B",
    }
    winner2, source2 = resolve_lww_conflict(local_rec2, remote_rec2)
    assert source2 == "LOCAL"
    assert winner2["status"] == "open"

    # Scenario 3: Timestamps and clocks equal, lexicographical device_id wins
    local_rec3 = {
        "status": "state-a",
        "timestamp": 100.0,
        "device_clock": 5,
        "device_id": "NODE-ALPHA",
    }
    remote_rec3 = {
        "status": "state-b",
        "timestamp": 100.0,
        "device_clock": 5,
        "device_id": "NODE-BETA",
    }
    winner3, source3 = resolve_lww_conflict(local_rec3, remote_rec3)
    assert source3 == "REMOTE"  # "NODE-BETA" > "NODE-ALPHA"
    assert winner3["status"] == "state-b"


def test_sync_vector_api_endpoint(db_session):
    """Verify POST /sync/vector returns missing delta."""
    db_session.add(
        EventLog(
            event_id="ev-sync-100",
            event_type="incident.created",
            origin_node_id="NODE-ALPHA",
            timestamp=500.0,
            payload=json.dumps({"title": "Landslide"}),
        )
    )
    db_session.commit()

    # Request missing events from empty remote vector
    from fastapi.testclient import TestClient
    from backend.app.database import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    resp = client.post("/sync/vector", json={"vector": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "missing_events" in data
    assert len(data["missing_events"]) >= 1
    assert data["missing_events"][0]["event_id"] == "ev-sync-100"

    # Check GET /sync/status
    status_resp = client.get("/sync/status")
    assert status_resp.status_code == 200
    assert "local_vector" in status_resp.json()
