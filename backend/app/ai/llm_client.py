import json
import logging
import requests
from typing import Dict, Optional
try:
    from backend.app.ai.prompts import (
        SYSTEM_PROMPT_EMERGENCY_ANALYST,
        INCIDENT_SUMMARY_PROMPT_TEMPLATE,
        INCIDENT_SEVERITY_TAGGING_PROMPT_TEMPLATE,
    )
except ImportError:
    from app.ai.prompts import (
        SYSTEM_PROMPT_EMERGENCY_ANALYST,
        INCIDENT_SUMMARY_PROMPT_TEMPLATE,
        INCIDENT_SEVERITY_TAGGING_PROMPT_TEMPLATE,
    )

logger = logging.getLogger("ResQMesh.LocalLLM")

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL_NAME = "phi3"  # Phi-3 mini / Llama 3 8B quantized model for edge deployment


class LocalLLMClient:
    """Client for local Ollama / llama.cpp LLM runtime with fallback deterministic rule-based analysis."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model_name: str = DEFAULT_MODEL_NAME,
        timeout: float = 3.0,
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Send prompt to local Ollama inference API."""
        import time
        if getattr(self, "_is_offline", False):
            if time.time() - getattr(self, "_last_offline_check", 0.0) < 30.0:
                return None
            else:
                self._is_offline = False

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or SYSTEM_PROMPT_EMERGENCY_ANALYST,
            "stream": False,
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                self._is_offline = False
                data = response.json()
                return data.get("response", "").strip()
            else:
                logger.warning(f"Local LLM API returned status {response.status_code}")
                return None
        except Exception as e:
            self._is_offline = True
            self._last_offline_check = time.time()
            logger.warning(f"Local LLM service unreachable ({e}). Using deterministic fallback.")
            return None

    def summarize_incident(self, description: str, category: str = "general", lat: float = 0.0, lon: float = 0.0) -> str:
        """Generate situation summary with fallback if LLM offline."""
        prompt = INCIDENT_SUMMARY_PROMPT_TEMPLATE.format(
            category=category, lat=lat, lon=lon, description=description
        )

        llm_response = self.generate(prompt)
        if llm_response:
            return llm_response

        # Fallback summary generator
        return f"Reported {category} incident near ({lat:.2f}, {lon:.2f}): {description[:120]}..."

    def tag_severity_and_category(self, description: str) -> Dict[str, str]:
        """Classify incident severity and category into structured JSON with fallback."""
        prompt = INCIDENT_SEVERITY_TAGGING_PROMPT_TEMPLATE.format(description=description)

        llm_response = self.generate(prompt)
        if llm_response:
            try:
                # Attempt to extract JSON snippet from LLM output
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                if json_start != -1 and json_end != -1:
                    json_str = llm_response[json_start:json_end]
                    parsed = json.loads(json_str)
                    return {
                        "severity": str(parsed.get("severity", "medium")).lower(),
                        "category": str(parsed.get("category", "general")).lower(),
                        "summary": str(parsed.get("summary", description[:100])),
                    }
            except Exception as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")

        # Deterministic Rule-Based Fallback Classifier
        desc_lower = description.lower()
        severity = "medium"
        category = "general"

        if any(w in desc_lower for w in ["trapped", "casualty", "critical", "explosion", "collapse", "drowning"]):
            severity = "critical"
        elif any(w in desc_lower for w in ["fire", "flood", "heavy", "injured", "urgent"]):
            severity = "high"
        elif any(w in desc_lower for w in ["minor", "stable", "standing"]):
            severity = "low"

        if any(w in desc_lower for w in ["fire", "smoke", "flame", "burn"]):
            category = "fire"
        elif any(w in desc_lower for w in ["flood", "water", "tsunami", "inundation"]):
            category = "flood"
        elif any(w in desc_lower for w in ["medical", "doctor", "bleeding", "patient", "ambulance"]):
            category = "medical"
        elif any(w in desc_lower for w in ["building", "collapse", "structure", "debris"]):
            category = "structural"

        return {
            "severity": severity,
            "category": category,
            "summary": f"{category.capitalize()} incident: {description[:100]}",
        }
