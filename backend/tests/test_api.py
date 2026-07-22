import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from backend.app.main import app
    from backend.app.database import Base, get_db
except ImportError:
    from app.main import app
    from app.database import Base, get_db

from sqlalchemy.pool import StaticPool

# Create isolated test database using StaticPool for in-memory connection persistence
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_operational_incident():
    payload = {
        "title": "Flood near Central Station",
        "severity": "high",
        "category": "flood",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    create_res = client.post("/incidents/", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert "incident_id" in data
    incident_id = data["incident_id"]

    get_res = client.get(f"/incidents/{incident_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Flood near Central Station"


def test_create_report_and_attach_to_incident():
    # 1. Create Incident
    inc_res = client.post("/incidents/", json={
        "title": "Building Fire",
        "severity": "critical",
        "category": "fire"
    })
    incident_id = inc_res.json()["incident_id"]

    # 2. Create standalone report
    rep_res = client.post("/reports/", json={
        "device_id": "dev-001",
        "user_id": "usr-001",
        "description": "Smoke visible on 3rd floor",
        "category": "fire",
        "latitude": 12.9720,
        "longitude": 77.5950
    })
    assert rep_res.status_code == 201
    report_id = rep_res.json()["report_id"]
    assert rep_res.json()["incident_id"] is None

    # 3. Attach report to incident
    attach_res = client.patch(f"/reports/{report_id}/attach?incident_id={incident_id}")
    assert attach_res.status_code == 200
    assert attach_res.json()["incident_id"] == incident_id

    # 4. Fetch incident and verify report in nested array
    inc_fetch = client.get(f"/incidents/{incident_id}")
    assert inc_fetch.status_code == 200
    assert len(inc_fetch.json()["reports"]) == 1
    assert inc_fetch.json()["reports"][0]["report_id"] == report_id


def test_chat_message_and_resource_endpoints():
    msg_res = client.post("/comms/messages", json={
        "sender_device_id": "dev-001",
        "sender_user_id": "usr-001",
        "text": "Evacuation complete."
    })
    assert msg_res.status_code == 201

    list_msg = client.get("/comms/messages")
    assert list_msg.status_code == 200
    assert len(list_msg.json()) == 1

    res_res = client.post("/comms/resources", json={
        "requester_id": "usr-001",
        "resource_type": "water_bottles",
        "quantity": 100
    })
    assert res_res.status_code == 201

    list_res = client.get("/comms/resources")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
