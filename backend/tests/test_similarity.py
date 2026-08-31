from datetime import datetime, timedelta
import pytest
from backend.app.ai.similarity import (
    haversine_distance_meters,
    compute_spatial_similarity,
    compute_temporal_similarity,
    compute_categorical_similarity,
    compute_text_similarity,
    IncidentSimilarityEngine,
)


def test_haversine_distance():
    # Co-located point
    dist_zero = haversine_distance_meters(12.9716, 77.5946, 12.9716, 77.5946)
    assert round(dist_zero, 2) == 0.0

    # ~111km apart (1 degree latitude)
    dist_1deg = haversine_distance_meters(12.0, 77.0, 13.0, 77.0)
    assert 110000 < dist_1deg < 112000


def test_spatial_similarity():
    sim_close = compute_spatial_similarity(12.9716, 77.5946, 12.9720, 77.5950)
    assert sim_close > 0.9

    sim_far = compute_spatial_similarity(12.9716, 77.5946, 13.5000, 78.5000)
    assert sim_far == 0.0


def test_temporal_similarity():
    now = datetime.utcnow()
    sim_identical = compute_temporal_similarity(now, now)
    assert sim_identical == 1.0

    sim_10m_apart = compute_temporal_similarity(now, now - timedelta(minutes=10))
    assert 0.9 < sim_10m_apart < 1.0

    sim_far = compute_temporal_similarity(now, now - timedelta(hours=5))
    assert sim_far == 0.0


def test_categorical_similarity():
    assert compute_categorical_similarity("fire", "fire") == 1.0
    assert compute_categorical_similarity("fire", "smoke") == 0.75
    assert compute_categorical_similarity("fire", "medical") == 0.0


def test_text_similarity():
    sim = compute_text_similarity(
        "Building fire on 3rd avenue with heavy smoke",
        "Structure fire 3rd avenue heavy smoke spreading",
    )
    assert sim > 0.5


def test_multi_factor_similarity_engine():
    engine = IncidentSimilarityEngine()

    now = datetime.utcnow()
    r1 = {
        "lat": 12.9716,
        "lon": 77.5946,
        "category": "fire",
        "description": "Building fire near main gate",
        "created_at": now,
    }
    r2 = {
        "lat": 12.9720,
        "lon": 77.5950,
        "category": "fire",
        "description": "Structure fire main gate building",
        "created_at": now - timedelta(minutes=2),
    }

    result = engine.calculate_similarity_score(r1, r2)
    assert result["composite"] > 0.8
    assert result["spatial"] > 0.9
    assert result["categorical"] == 1.0
