import pytest
from unittest.mock import patch, MagicMock
from backend.app.ai.llm_client import LocalLLMClient
from backend.app.ai.prompts import (
    INCIDENT_SUMMARY_PROMPT_TEMPLATE,
    INCIDENT_SEVERITY_TAGGING_PROMPT_TEMPLATE,
)


def test_prompt_formatting():
    p_summary = INCIDENT_SUMMARY_PROMPT_TEMPLATE.format(
        category="fire", lat=12.97, lon=77.59, description="Transformer explosion"
    )
    assert "fire" in p_summary
    assert "Transformer explosion" in p_summary

    p_tag = INCIDENT_SEVERITY_TAGGING_PROMPT_TEMPLATE.format(description="Building collapse")
    assert "Building collapse" in p_tag


def test_llm_client_fallback_when_offline():
    client = LocalLLMClient(base_url="http://127.0.0.1:59999/invalid/api", timeout=0.01)

    # Test summary fallback
    summary = client.summarize_incident(
        description="Massive flood in low lying residential area",
        category="flood",
        lat=12.97,
        lon=77.59,
    )
    assert "flood" in summary.lower()
    assert "Massive flood" in summary

    # Test tagging fallback
    tags = client.tag_severity_and_category("Trapped civilians inside collapsed building structure")
    assert tags["severity"] in ["critical", "high"]
    assert tags["category"] == "structural"


@patch("requests.post")
def test_llm_client_mock_successful_response(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": '{"severity": "critical", "category": "fire", "summary": "Active fire with casualties"}'
    }
    mock_post.return_value = mock_resp

    client = LocalLLMClient()
    tags = client.tag_severity_and_category("Severe chemical fire in industrial plant")

    assert tags["severity"] == "critical"
    assert tags["category"] == "fire"
    assert tags["summary"] == "Active fire with casualties"
