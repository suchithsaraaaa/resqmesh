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
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import EventLog, OutboxItem, OperationalIncident
from backend.app.services.node_manager import NodeManager
from backend.app.network.event_protocol import EventProtocolEngine, EventEnvelope

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
    try:
        yield db
    finally:
        db.close()


def test_emit_event_lifecycle(db_session):
    """Verify emit_event signs payload, stores in EventLog, and queues in Outbox."""
    nm = NodeManager.get_instance()
    nm.setup_node("Emitter-Node", "responder")

    payload = {"title": "Flash Flood", "category": "flood", "severity": "high"}
    envelope = EventProtocolEngine.emit_event(
        db=db_session,
        event_type="incident.created",
        payload=payload,
        target_node_id=None,
        node_manager=nm,
    )

    assert envelope.event_id is not None
    assert envelope.origin_node_id == nm.node_id
    assert envelope.signature is not None

    # Check EventLog
    logged = db_session.query(EventLog).filter_by(event_id=envelope.event_id).first()
    assert logged is not None
    assert logged.event_type == "incident.created"

    # Check OutboxItem
    outbox = db_session.query(OutboxItem).filter_by(event_id=envelope.event_id).first()
    assert outbox is not None
    assert outbox.status == "pending"


def test_receive_and_acknowledge_idempotency(db_session):
    """Verify first reception delivers, second reception acknowledges as duplicate_suppressed."""
    event_dict = {
        "event_id": "evt-idempotent-uuid-1",
        "event_type": "incident.created",
        "origin_node_id": "REMOTE-NODE-01",
        "timestamp": time.time(),
        "payload": {
            "incident_id": "inc-idem-01",
            "title": "Structure Collapse",
            "category": "structural",
            "severity": "critical",
        },
        "version": 1,
        "hop_count": 1,
    }

    # 1. First reception
    ack1 = EventProtocolEngine.receive_and_acknowledge(db_session, event_dict, "LOCAL-NODE")
    assert ack1["type"] == "EVENT_ACK"
    assert ack1["event_id"] == "evt-idempotent-uuid-1"
    assert ack1["status"] == "delivered"

    # Verify incident materialized in SQLite
    inc = db_session.query(OperationalIncident).filter_by(incident_id="inc-idem-01").first()
    assert inc is not None
    assert inc.title == "Structure Collapse"

    # 2. Second reception (duplicate)
    ack2 = EventProtocolEngine.receive_and_acknowledge(db_session, event_dict, "LOCAL-NODE")
    assert ack2["type"] == "EVENT_ACK"
    assert ack2["status"] == "duplicate_suppressed"


def test_ack_processing_and_endpoint(db_session):
    """Verify processing incoming ACK transitions OutboxItem to acknowledged."""
    test_evt_id = "evt-outbox-ack-test"

    # Create pending outbox item
    outbox = OutboxItem(event_id=test_evt_id, status="pending")
    db_session.add(outbox)
    db_session.commit()

    # Process ACK directly on session
    ack_payload = {
        "type": "EVENT_ACK",
        "ack_id": "ack-12345",
        "event_id": test_evt_id,
        "recipient_node_id": "NODE-PEER-BETA",
        "status": "delivered",
        "timestamp": time.time(),
    }

    processed = EventProtocolEngine.process_ack(db_session, ack_payload)
    assert processed is True

    # Verify status in database
    updated_outbox = db_session.query(OutboxItem).filter_by(event_id=test_evt_id).first()
    assert updated_outbox.status == "acknowledged"
