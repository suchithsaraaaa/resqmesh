from enum import Enum
from typing import Dict, List, Optional
try:
    from backend.app.ai.similarity import IncidentSimilarityEngine
except ImportError:
    from app.ai.similarity import IncidentSimilarityEngine


class ClusterAction(str, Enum):
    AUTO_MERGE = "AUTO_MERGE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NEW_INCIDENT = "NEW_INCIDENT"


class IncidentClusteringEngine:
    """Clustering engine for grouping responder reports into master operational incidents."""

    def __init__(
        self,
        auto_merge_threshold: float = 0.75,
        review_threshold: float = 0.45,
        similarity_engine: Optional[IncidentSimilarityEngine] = None,
    ):
        self.auto_merge_threshold = auto_merge_threshold
        self.review_threshold = review_threshold
        self.similarity_engine = similarity_engine or IncidentSimilarityEngine()

    def evaluate_report_against_incidents(
        self, new_report_data: dict, active_incidents: List[dict]
    ) -> dict:
        """
        Evaluates a newly arrived report against all active operational incidents.
        Returns recommended action (AUTO_MERGE, NEEDS_REVIEW, NEW_INCIDENT) and matching incident details.
        """
        best_match_incident: Optional[dict] = None
        highest_score = 0.0
        best_breakdown: Optional[dict] = None

        for incident in active_incidents:
            scores = self.similarity_engine.calculate_similarity_score(
                new_report_data, incident
            )
            composite_score = scores["composite"]
            if composite_score > highest_score:
                highest_score = composite_score
                best_match_incident = incident
                best_breakdown = scores

        if highest_score >= self.auto_merge_threshold and best_match_incident:
            action = ClusterAction.AUTO_MERGE
        elif highest_score >= self.review_threshold and best_match_incident:
            action = ClusterAction.NEEDS_REVIEW
        else:
            action = ClusterAction.NEW_INCIDENT

        return {
            "action": action,
            "confidence_score": highest_score,
            "target_incident_id": best_match_incident.get("id") if best_match_incident else None,
            "target_incident": best_match_incident,
            "score_breakdown": best_breakdown or {},
        }
