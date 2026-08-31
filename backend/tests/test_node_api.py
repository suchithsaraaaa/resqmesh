import json
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

import backend.app.models
from backend.app.database import Base, get_db
from backend.app.main import app

# Set up test database with StaticPool so all requests share in-memory SQLite tables
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_node_status_endpoint():
    """Verify local node returns status, role, and identity."""
    response = client.get("/node/status")
    assert response.status_code == 200
    data = response.json()
    assert "node_id" in data
    assert "role" in data
    assert data["status"] == "online"
    assert "uptime_seconds" in data


def test_node_setup_endpoint():
    """Verify first-run onboarding configuration sets name and role."""
    setup_payload = {
        "name": "Command-Laptop-Alpha",
        "role": "commander",
        "port": 8000,
    }
    response = client.post("/node/setup", json=setup_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["node_name"] == "Command-Laptop-Alpha"
    assert data["role"] == "commander"
    assert data["is_configured"] is True

    # Re-check status reflects updated configuration
    status_resp = client.get("/node/status").json()
    assert status_resp["name"] == "Command-Laptop-Alpha"
    assert status_resp["role"] == "commander"


def test_peer_registration_and_listing():
    """Verify discovered peer registration and retrieval."""
    peer_payload = {
        "node_id": "NODE-PEER-BETA",
        "name": "Responder-Laptop-Beta",
        "role": "responder",
        "ip_address": "192.168.1.55",
        "api_port": 8000,
        "latency_ms": 14.2,
    }
    reg_resp = client.post("/peers/register", json=peer_payload)
    assert reg_resp.status_code == 200

    peers_resp = client.get("/peers/")
    assert peers_resp.status_code == 200
    peers = peers_resp.json()
    peer_ids = [p["node_id"] for p in peers]
    assert "NODE-PEER-BETA" in peer_ids


def test_idempotent_event_ingestion_and_materialization():
    """
    Verify /events/ingest stores in EventLog and materializes domain records,
    suppressing duplicates without error.
    """
    event_id = "evt-inc-999-uuid"
    inc_payload = {
        "incident_id": "inc-999",
        "title": "Substation Fire",
        "category": "fire",
        "severity": "critical",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "summary": "Electrical transformer explosion",
        "status": "open",
    }

    event_data = {
        "event_id": event_id,
        "event_type": "incident.created",
        "origin_node_id": "NODE-PEER-BETA",
        "timestamp": time.time(),
        "payload": json.dumps(inc_payload),
        "version": 1,
        "hop_count": 1,
    }

    # First ingestion -> should materialize incident
    r1 = client.post("/events/ingest", json=event_data)
    assert r1.status_code == 200
    assert r1.json()["status"] in ["delivered", "ingested"]

    # Verify incident exists in operational incidents API
    inc_resp = client.get("/incidents/inc-999")
    assert inc_resp.status_code == 200
    assert inc_resp.json()["title"] == "Substation Fire"

    # Duplicate ingestion with same event_id -> should be suppressed
    r2 = client.post("/events/ingest", json=event_data)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate_suppressed"

    # Ingest related report event
    rep_event_id = "evt-rep-888-uuid"
    rep_payload = {
        "report_id": "rep-888",
        "incident_id": "inc-999",
        "device_id": "NODE-PEER-BETA",
        "user_id": "responder-sarah",
        "category": "fire",
        "description": "Large smoke plume visible from 500 meters",
        "latitude": 12.9718,
        "longitude": 77.5948,
    }
    r3 = client.post(
        "/events/ingest",
        json={
            "event_id": rep_event_id,
            "event_type": "report.created",
            "origin_node_id": "NODE-PEER-BETA",
            "timestamp": time.time(),
            "payload": json.dumps(rep_payload),
        },
    )
    assert r3.status_code == 200
    assert r3.json()["status"] in ["delivered", "ingested"]

    # Verify report is linked to incident
    inc_with_reports = client.get("/incidents/inc-999").json()
    assert len(inc_with_reports["reports"]) >= 1
    assert inc_with_reports["reports"][0]["report_id"] == "rep-888"
