from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import OperationalIncident, Report
from backend.app.ai.clustering import IncidentClusteringEngine, ClusterAction
from backend.app.services.incident_matcher import IncidentMatcherService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_clustering_engine_auto_merge_decision():
    engine = IncidentClusteringEngine()
    now = datetime.now(timezone.utc)

    new_report = {
        "lat": 12.9716,
        "lon": 77.5946,
        "category": "fire",
        "description": "Massive building fire main gate",
        "created_at": now,
    }

    active_incidents = [
        {
            "id": "inc-100",
            "lat": 12.9718,
            "lon": 77.5948,
            "category": "fire",
            "description": "Building fire main gate with trapped civilians",
            "created_at": now - timedelta(minutes=1),
        }
    ]

    res = engine.evaluate_report_against_incidents(new_report, active_incidents)
    assert res["action"] == ClusterAction.AUTO_MERGE
    assert res["target_incident_id"] == "inc-100"
    assert res["confidence_score"] >= 0.75


def test_clustering_engine_new_incident_decision():
    engine = IncidentClusteringEngine()
    now = datetime.now(timezone.utc)

    new_report = {
        "lat": 13.5000,
        "lon": 78.5000,
        "category": "medical",
        "description": "Heart attack patient at distant medical center",
        "created_at": now,
    }

    active_incidents = [
        {
            "id": "inc-100",
            "lat": 12.9718,
            "lon": 77.5948,
            "category": "fire",
            "description": "Building fire main gate",
            "created_at": now - timedelta(minutes=1),
        }
    ]

    res = engine.evaluate_report_against_incidents(new_report, active_incidents)
    assert res["action"] == ClusterAction.NEW_INCIDENT


def test_incident_matcher_service_integration(db_session):
    service = IncidentMatcherService(db=db_session)

    # Initial report -> Spawns new Master Incident
    rep1 = Report(
        report_id="rep-001",
        device_id="dev-01",
        user_id="user-01",
        category="fire",
        description="Transformer explosion near main station",
        latitude=12.9716,
        longitude=77.5946,
    )
    db_session.add(rep1)
    db_session.commit()

    res1 = service.process_new_report(rep1)
    assert res1["action"] == ClusterAction.NEW_INCIDENT.value
    assert res1["target_incident_id"] is not None

    # Check incident was created in DB
    created_inc = (
        db_session.query(OperationalIncident)
        .filter(OperationalIncident.incident_id == res1["target_incident_id"])
        .first()
    )
    assert created_inc is not None
    assert created_inc.category == "fire"

    # Second nearby matching report -> Auto-merges with master incident
    rep2 = Report(
        report_id="rep-002",
        device_id="dev-02",
        user_id="user-02",
        category="fire",
        description="Electrical transformer explosion main station area",
        latitude=12.9718,
        longitude=77.5948,
    )
    db_session.add(rep2)
    db_session.commit()

    res2 = service.process_new_report(rep2)
    assert res2["action"] == ClusterAction.AUTO_MERGE.value
    assert res2["target_incident_id"] == created_inc.incident_id
