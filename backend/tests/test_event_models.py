import time
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.app.database import Base
from backend.app.models import (
    NodeRecord,
    OperationalIncident,
    Report,
    ChatMessage,
    ResourceRequest,
    EventLog,
    OutboxItem,
    SyncVector,
)


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for model testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_node_record_lifecycle(db_session):
    """Verify NodeRecord peer tracking and status updates."""
    node = NodeRecord(
        node_id="NODE-LAPTOP-A",
        name="Laptop Alpha",
        role="commander",
        public_key="ed25519_pub_key_mock_alpha",
        ip_address="192.168.1.10",
        api_port=8000,
        status="online",
        latency_ms=12.5,
    )
    db_session.add(node)
    db_session.commit()

    retrieved = db_session.query(NodeRecord).filter_by(node_id="NODE-LAPTOP-A").first()
    assert retrieved is not None
    assert retrieved.name == "Laptop Alpha"
    assert retrieved.role == "commander"
    assert retrieved.latency_ms == 12.5


def test_incident_and_report_separation(db_session):
    """Verify clear distinction: Reports are raw sightings; Incident is the master operational event."""
    # 1. Commander creates Master Operational Incident
    incident = OperationalIncident(
        title="Industrial Plant Fire",
        category="fire",
        severity="critical",
        latitude=12.9716,
        longitude=77.5946,
        summary="Transformer explosion with heavy toxic fumes",
    )
    db_session.add(incident)
    db_session.commit()
    inc_id = incident.incident_id

    # 2. Responder 1 submits observation
    rep1 = Report(
        incident_id=inc_id,
        device_id="NODE-RESP-01",
        user_id="responder-john",
        category="fire",
        description="Transformer fire near Sector 4 gate, 2 civilian casualties",
        latitude=12.9718,
        longitude=77.5948,
    )
    # 3. Responder 2 submits a separate observation of the same event
    rep2 = Report(
        incident_id=inc_id,
        device_id="NODE-RESP-02",
        user_id="responder-sarah",
        category="fire",
        description="Heavy black smoke spreading to nearby loading dock",
        latitude=12.9720,
        longitude=77.5950,
    )
    db_session.add_all([rep1, rep2])
    db_session.commit()

    # Master incident should aggregate both reports without overwriting either
    queried_inc = db_session.query(OperationalIncident).filter_by(incident_id=inc_id).first()
    assert len(queried_inc.reports) == 2
    report_descs = [r.description for r in queried_inc.reports]
    assert "Transformer fire near Sector 4 gate, 2 civilian casualties" in report_descs
    assert "Heavy black smoke spreading to nearby loading dock" in report_descs


def test_event_log_idempotency(db_session):
    """Ensure duplicate events with the same event_id cannot be inserted twice."""
    event_payload = json.dumps({"title": "Flood Warning", "category": "flood"})
    event_id = "550e8400-e29b-41d4-a716-446655440000"

    event1 = EventLog(
        event_id=event_id,
        event_type="incident.created",
        origin_node_id="NODE-LAPTOP-A",
        timestamp=time.time(),
        payload=event_payload,
        version=1,
    )
    db_session.add(event1)
    db_session.commit()

    # Duplicate insertion attempt
    event2 = EventLog(
        event_id=event_id,
        event_type="incident.created",
        origin_node_id="NODE-LAPTOP-B",
        timestamp=time.time(),
        payload=event_payload,
        version=1,
    )
    db_session.expunge(event1)
    db_session.add(event2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_outbox_queue_and_sync_vectors(db_session):
    """Verify outbox item lifecycle and vector state tracking."""
    # Outbox item for peer broadcast
    outbox = OutboxItem(
        event_id="evt-101",
        target_node_id=None,  # Broadcast
        status="pending",
        attempts=0,
    )
    db_session.add(outbox)

    # Sync vector tracking
    vector = SyncVector(
        peer_node_id="NODE-LAPTOP-B",
        last_event_id="evt-101",
        last_timestamp=time.time(),
        last_clock=5,
    )
    db_session.add(vector)
    db_session.commit()

    retrieved_outbox = db_session.query(OutboxItem).filter_by(event_id="evt-101").first()
    assert retrieved_outbox.status == "pending"
    assert retrieved_outbox.target_node_id is None

    retrieved_vector = db_session.query(SyncVector).filter_by(peer_node_id="NODE-LAPTOP-B").first()
    assert retrieved_vector.last_clock == 5
