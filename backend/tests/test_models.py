import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path for test discovery and IDE import resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from backend.app.database import Base
    from backend.app.models import OperationalIncident, Report, ChatMessage, ResourceRequest, SyncAck
    from backend.app.schemas import ReportCreate, OperationalIncidentCreate, ReportResponse
except ImportError:
    from app.database import Base
    from app.models import OperationalIncident, Report, ChatMessage, ResourceRequest, SyncAck
    from app.schemas import ReportCreate, OperationalIncidentCreate, ReportResponse



@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_operational_incident_with_reports(db_session):
    incident = OperationalIncident(
        title="Building Collapse near Downtown",
        severity="critical",
        category="structural",
        latitude=37.7749,
        longitude=-122.4194
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    assert incident.incident_id is not None
    assert incident.status == "open"
    assert incident.severity == "critical"

    report1 = Report(
        incident_id=incident.incident_id,
        device_id="device-alpha",
        user_id="user-1",
        description="South wall collapsed, 2 trapped",
        category="structural",
        latitude=37.7750,
        longitude=-122.4195
    )
    report2 = Report(
        incident_id=incident.incident_id,
        device_id="device-beta",
        user_id="user-2",
        description="Heavy smoke coming from rubble",
        category="fire",
        latitude=37.7748,
        longitude=-122.4193
    )

    db_session.add_all([report1, report2])
    db_session.commit()
    db_session.refresh(incident)

    assert len(incident.reports) == 2
    assert incident.reports[0].device_id in ["device-alpha", "device-beta"]


def test_standalone_report_creation(db_session):
    report = Report(
        device_id="device-gamma",
        user_id="user-3",
        description="Flooded street, water depth 2 feet",
        category="flood",
        latitude=12.9716,
        longitude=77.5946
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    assert report.report_id is not None
    assert report.incident_id is None
    assert report.category == "flood"


def test_chat_message_and_resource_request(db_session):
    msg = ChatMessage(
        sender_device_id="dev-1",
        sender_user_id="usr-1",
        text="Sending search and rescue team."
    )
    res = ResourceRequest(
        requester_id="usr-1",
        resource_type="medical_kit",
        quantity=5,
        urgency="high"
    )
    ack = SyncAck(
        source_device="dev-1",
        target_device="dev-2",
        device_clock=10
    )

    db_session.add_all([msg, res, ack])
    db_session.commit()

    assert msg.message_id is not None
    assert res.resource_id is not None
    assert ack.ack_id is not None
    assert ack.device_clock == 10


def test_pydantic_schema_validation():
    report_in = ReportCreate(
        device_id="dev-100",
        user_id="usr-100",
        description="Test description",
        latitude=10.0,
        longitude=20.0
    )
    assert report_in.device_id == "dev-100"
    assert report_in.category == "general"
