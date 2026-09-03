import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.ai.vector_store import LocalVectorStore
from backend.app.ai.rag_pipeline import RAGPipeline

client = TestClient(app)


def test_vector_store_sop_retrieval():
    """Verify local vector store correctly retrieves top relevant SOPs for disaster scenarios."""
    store = LocalVectorStore()
    store.seed_default_sops()

    # 1. Fire scenario
    fire_results = store.search("severe structural fire with heavy smoke", top_k=2)
    assert len(fire_results) > 0
    best_doc, score = fire_results[0]
    assert best_doc.category == "fire"
    assert score > 0.15

    # 2. Flood scenario
    flood_results = store.search("flash flood water rescue high ground", top_k=2)
    assert len(flood_results) > 0
    assert any(doc.category == "flood" for doc, _ in flood_results)

    # 3. Medical triage scenario
    med_results = store.search("unconscious victim severe bleeding arterial trauma", top_k=2)
    assert len(med_results) > 0
    assert any(doc.category == "medical" for doc, _ in med_results)


def test_rag_pipeline_guidance():
    """Verify RAG pipeline synthesizes tactical recommendations from retrieved SOPs."""
    pipeline = RAGPipeline()
    guidance = pipeline.generate_sop_guidance(
        description="Transformer oil burning vigorously near residential homes",
        category="fire",
        top_k=2,
    )

    assert "recommendation" in guidance
    assert len(guidance["recommendation"]) > 10
    assert "retrieved_sops" in guidance
    assert len(guidance["retrieved_sops"]) > 0
    assert guidance["retrieved_sops"][0]["category"] in ["fire", "industrial_disaster", "hazmat"]


def test_ai_triage_and_query_endpoints():
    """Verify FastAPI /ai/triage, /ai/query, and /ai/sops endpoints."""
    # 1. POST /ai/triage
    triage_resp = client.post(
        "/ai/triage",
        json={
            "description": "Flash flood inundation trapping people on rooftops",
            "category": "flood",
            "top_k": 2,
        },
    )
    assert triage_resp.status_code == 200
    data = triage_resp.json()
    assert "recommendation" in data
    assert "suggested_resources" in data
    assert len(data["suggested_resources"]) > 0

    # 2. POST /ai/query
    query_resp = client.post(
        "/ai/query",
        json={"query": "How to approach hazardous chemical spill?"},
    )
    assert query_resp.status_code == 200
    qdata = query_resp.json()
    assert "recommendation" in qdata

    # 3. GET /ai/sops
    sops_resp = client.get("/ai/sops")
    assert sops_resp.status_code == 200
    sops_list = sops_resp.json()
    assert isinstance(sops_list, list)
    assert len(sops_list) >= 3
