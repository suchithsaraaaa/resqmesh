import os
import sys
import time
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import backend.app.models
from backend.app.database import Base
from backend.app.models import OperationalIncident, Report
from backend.app.ai.similarity import (
    IncidentSimilarityEngine,
    compute_spatial_similarity,
    compute_temporal_similarity,
    compute_categorical_similarity,
    compute_text_similarity,
)
from backend.app.ai.clustering import IncidentClusteringEngine, ClusterAction
from backend.app.services.incident_matcher import IncidentMatcherService

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
    db.query(Report).delete()
    db.query(OperationalIncident).delete()
    db.commit()
    try:
        yield db
    finally:
        db.close()


def test_similarity_engine_factors():
    """Verify individual spatial, temporal, categorical, and text similarity factors."""
    # 1. Spatial co-located vs distant
    assert compute_spatial_similarity(12.9716, 77.5946, 12.9716, 77.5946) == 1.0
    # 50km apart -> 0.0
    assert compute_spatial_similarity(12.9716, 77.5946, 13.5000, 78.5000) == 0.0

    # 2. Categorical exact and semantic match
    assert compute_categorical_similarity("fire", "fire") == 1.0
    assert compute_categorical_similarity("fire", "explosion") == 0.75
    assert compute_categorical_similarity("fire", "flood") == 0.0

    # 3. Text similarity
    text_sim = compute_text_similarity(
        "transformer fire with thick black smoke",
        "black smoke from electric transformer fire",
    )
    assert text_sim >= 0.50


def test_incident_matcher_auto_merge_and_escalation(db_session):
    """
    Verify full AI correlation pipeline:
    - Report 1 creates Incident 1
    - Report 2 merges into Incident 1
    - Report 3 (unrelated) spawns Incident 2
    """
    matcher = IncidentMatcherService(db=db_session)

    # 1. First report: Transformer fire near Station
    rep1 = Report(
        report_id="rep-corr-1",
        device_id="DEV-1",
        user_id="USR-1",
        category="fire",
        description="Transformer fire near railway station, small flames",
        latitude=12.9716,
        longitude=77.5946,
        timestamp=datetime.utcnow(),
    )
    db_session.add(rep1)
    db_session.commit()

    res1 = matcher.process_new_report(rep1)
    assert res1["action"] == ClusterAction.NEW_INCIDENT.value
    assert rep1.incident_id is not None
    master_inc_id = rep1.incident_id

    master_inc = db_session.query(OperationalIncident).filter_by(incident_id=master_inc_id).first()
    assert master_inc is not None

    # 2. Second report: Similar location (25 meters away), same category, similar text
    rep2 = Report(
        report_id="rep-corr-2",
        device_id="DEV-2",
        user_id="USR-2",
        category="fire",
        description="Heavy black smoke from sparking transformer near railway station",
        latitude=12.9718,
        longitude=77.5948,
        timestamp=datetime.utcnow(),
    )
    db_session.add(rep2)
    db_session.commit()

    res2 = matcher.process_new_report(rep2)
    assert res2["action"] == ClusterAction.AUTO_MERGE.value
    assert rep2.incident_id == master_inc_id
    assert res2["confidence_score"] >= 0.75

    # 3. Third report: Completely distant flood report (25km away)
    rep3 = Report(
        report_id="rep-corr-3",
        device_id="DEV-3",
        user_id="USR-3",
        category="flood",
        description="Underpass waterlogging after sudden downpour",
        latitude=13.1500,
        longitude=77.8000,
        timestamp=datetime.utcnow(),
    )
    db_session.add(rep3)
    db_session.commit()

    res3 = matcher.process_new_report(rep3)
    assert res3["action"] == ClusterAction.NEW_INCIDENT.value
    assert rep3.incident_id != master_inc_id

    # Total operational incidents should be 2
    total_incidents = db_session.query(OperationalIncident).count()
    assert total_incidents == 2
