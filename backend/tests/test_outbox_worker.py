import os
import sys
import time
import json
import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import backend.app.models
from backend.app.database import Base
from backend.app.models import OutboxItem, EventLog
from backend.app.services.node_manager import NodeManager
from backend.app.network.transport import PeerTransportPool
from backend.app.sync.outbox_worker import StoreAndForwardWorker

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
    db.query(OutboxItem).delete()
    db.query(EventLog).delete()
    db.commit()
    # Reset singleton registries
    NodeManager.get_instance()._active_peers = {}
    PeerTransportPool.get_instance().connections = {}
    try:
        yield db
    finally:
        db.close()


def test_outbox_flush_no_peers(db_session):
    """Verify items remain pending when no peers are connected."""
    evt_id = "evt-no-peers-1"
    db_session.add(
        EventLog(
            event_id=evt_id,
            event_type="incident.created",
            origin_node_id="LOCAL-NODE",
            timestamp=time.time(),
            payload=json.dumps({"title": "Test Incident"}),
        )
    )
    db_session.add(OutboxItem(event_id=evt_id, status="pending"))
    db_session.commit()

    worker = StoreAndForwardWorker()
    delivered = worker.flush_outbox(session=db_session)
    assert delivered == 0

    item = db_session.query(OutboxItem).filter_by(event_id=evt_id).first()
    assert item.status == "pending"
    assert item.attempts == 0


def test_outbox_flush_successful_delivery(db_session):
    """Verify item transitions to acknowledged when remote peer accepts event."""
    evt_id = "evt-deliver-ok-1"
    db_session.add(
        EventLog(
            event_id=evt_id,
            event_type="report.created",
            origin_node_id="LOCAL-NODE",
            timestamp=time.time(),
            payload=json.dumps({"description": "Downed powerline"}),
        )
    )
    db_session.add(OutboxItem(event_id=evt_id, status="pending"))
    db_session.commit()

    # Mock active peer and mock connection
    nm = NodeManager.get_instance()
    nm.register_peer({
        "node_id": "NODE-MOCK-PEER",
        "name": "Peer-Alpha",
        "role": "responder",
        "ip_address": "127.0.0.1",
        "api_port": 8000,
    })

    mock_conn = MagicMock()
    mock_conn.post_event.return_value = True  # Simulated successful post

    pool = PeerTransportPool.get_instance()
    pool.connections["NODE-MOCK-PEER"] = mock_conn

    worker = StoreAndForwardWorker()
    delivered = worker.flush_outbox(session=db_session)
    assert delivered == 1

    item = db_session.query(OutboxItem).filter_by(event_id=evt_id).first()
    assert item.status == "acknowledged"


def test_outbox_flush_failed_delivery_increments_attempt(db_session):
    """Verify attempt counter increments and last_attempt_at is updated on transmission failure."""
    evt_id = "evt-deliver-fail-1"
    db_session.add(
        EventLog(
            event_id=evt_id,
            event_type="message.created",
            origin_node_id="LOCAL-NODE",
            timestamp=time.time(),
            payload=json.dumps({"text": "SOS evacuation needed"}),
        )
    )
    db_session.add(OutboxItem(event_id=evt_id, status="pending", attempts=0))
    db_session.commit()

    # Mock active peer with failing connection
    nm = NodeManager.get_instance()
    nm.register_peer({
        "node_id": "NODE-FAIL-PEER",
        "name": "Peer-Unreachable",
        "role": "responder",
        "ip_address": "127.0.0.1",
        "api_port": 8000,
    })

    mock_conn = MagicMock()
    mock_conn.post_event.return_value = False  # Simulated failed transmission

    pool = PeerTransportPool.get_instance()
    pool.connections["NODE-FAIL-PEER"] = mock_conn

    worker = StoreAndForwardWorker()
    delivered = worker.flush_outbox(session=db_session)
    assert delivered == 0

    item = db_session.query(OutboxItem).filter_by(event_id=evt_id).first()
    assert item.status == "pending"
    assert item.attempts == 1
    assert item.last_attempt_at is not None
