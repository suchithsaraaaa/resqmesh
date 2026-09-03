import pytest
from unittest.mock import patch, MagicMock
from backend.app.ai.vector_store import (
    LocalVectorStore,
    tokenize_and_vectorize,
    cosine_similarity,
)
from backend.app.ai.rag_pipeline import RAGPipeline
from backend.app.ai.llm_client import LocalLLMClient


def test_tokenization_and_cosine_similarity():
    vec1 = tokenize_and_vectorize("fire rescue evacuation safety perimeter")
    vec2 = tokenize_and_vectorize("structural fire building evacuation safety")
    vec3 = tokenize_and_vectorize("flood boat water inundation river")

    assert len(vec1) > 0
    assert len(vec2) > 0

    sim_high = cosine_similarity(vec1, vec2)
    sim_low = cosine_similarity(vec1, vec3)

    assert sim_high > 0.4
    assert sim_high > sim_low


def test_vector_store_seed_and_search():
    store = LocalVectorStore()
    store.seed_default_sops()

    assert len(store.documents) >= 5
    assert "sop-fire-01" in store.documents
    assert "sop-flood-01" in store.documents

    # Search for water rescue
    results = store.search("trapped civilians in rising flood waters", top_k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert top_doc.category == "flood"
    assert "rescue" in top_doc.title.lower() or "flood" in top_doc.title.lower()
    assert score > 0.0

    # Search for triage medical
    med_results = store.search("severe arterial bleeding tourniquet triage", top_k=1)
    assert len(med_results) == 1
    assert med_results[0][0].category == "medical"


def test_vector_store_category_filter():
    store = LocalVectorStore()
    store.seed_default_sops()

    # Search with structural category filter
    results = store.search("collapsed walls and rubble", top_k=3, category_filter="structural")
    assert len(results) > 0
    for doc, _ in results:
        assert doc.category in ["structural", "building_collapse"]


def test_rag_pipeline_offline_fallback():
    mock_llm = LocalLLMClient(base_url="http://127.0.0.1:59999/invalid/api", timeout=0.01)
    pipeline = RAGPipeline(llm_client=mock_llm)

    response = pipeline.generate_sop_guidance(
        description="Heavy structural fire on 2nd floor with thick black smoke",
        category="fire",
    )

    assert response["category"] == "fire"
    assert len(response["retrieved_sops"]) > 0
    assert "sop-fire-01" in response["source_sop_ids"]
    assert "Structural Fire" in response["recommendations"] or "safety" in response["recommendations"].lower()


@patch("requests.post")
def test_rag_pipeline_llm_synthesis(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": (
            "1. Deploy PFDs and launch inflatable rescue boat immediately.\n"
            "2. Establish upstream spotter for floating debris.\n"
            "3. Evacuate civilians to high-ground shelter."
        )
    }
    mock_post.return_value = mock_resp

    client = LocalLLMClient()
    pipeline = RAGPipeline(llm_client=client)

    result = pipeline.generate_sop_guidance(
        description="Responders needed with boats for stranded family in flash flood",
        category="flood",
    )

    assert len(result["retrieved_sops"]) > 0
    assert "sop-flood-01" in result["source_sop_ids"]
    assert "inflatable rescue boat" in result["recommendations"].lower()
