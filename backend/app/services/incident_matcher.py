import uuid
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

try:
    from backend.app.models import OperationalIncident, Report
    from backend.app.ai.clustering import IncidentClusteringEngine, ClusterAction
except ImportError:
    from app.models import OperationalIncident, Report
    from app.ai.clustering import IncidentClusteringEngine, ClusterAction


class IncidentMatcherService:
    """Service layer linking database records with AI incident clustering and correlation."""

    def __init__(self, db: Session, clustering_engine: Optional[IncidentClusteringEngine] = None):
        self.db = db
        self.clustering_engine = clustering_engine or IncidentClusteringEngine()

    def process_new_report(self, report: Report) -> dict:
        """Process incoming Report, correlate with active operational Incidents, and link or spawn."""
        active_incidents = (
            self.db.query(OperationalIncident)
            .filter(OperationalIncident.status != "closed")
            .all()
        )

        active_incidents_data = [
            {
                "id": inc.incident_id,
                "title": inc.title,
                "category": inc.category,
                "description": inc.summary,
                "lat": inc.latitude,
                "lon": inc.longitude,
                "created_at": inc.created_at,
            }
            for inc in active_incidents
        ]

        report_data = {
            "id": report.report_id,
            "category": report.category,
            "description": report.description,
            "lat": report.latitude,
            "lon": report.longitude,
            "created_at": report.timestamp,
        }

        result = self.clustering_engine.evaluate_report_against_incidents(
            report_data, active_incidents_data
        )

        action = result["action"]
        target_incident_id = result.get("target_incident_id")

        if action == ClusterAction.AUTO_MERGE and target_incident_id:
            report.incident_id = target_incident_id
            target_inc = (
                self.db.query(OperationalIncident)
                .filter_by(incident_id=target_incident_id)
                .first()
            )
            if target_inc:
                # Escalate severity if report urgency is higher
                severity_ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                rep_urgency = getattr(report, "urgency", "medium") or "medium"
                rep_rank = severity_ranks.get(rep_urgency.lower(), 2)
                inc_rank = severity_ranks.get(target_inc.severity.lower(), 2)
                if rep_rank > inc_rank:
                    target_inc.severity = rep_urgency.lower()
            self.db.commit()
            self.db.refresh(report)

        elif action == ClusterAction.NEW_INCIDENT or not target_incident_id:
            # Spawn new master operational incident
            category_title = report.category.capitalize() if report.category else "Emergency"
            new_inc = OperationalIncident(
                incident_id=str(uuid.uuid4()),
                title=f"Incident: {category_title}",
                category=report.category or "general",
                severity=getattr(report, "urgency", "medium") or "medium",
                summary=report.description,
                latitude=report.latitude,
                longitude=report.longitude,
                status="open",
            )
            self.db.add(new_inc)
            self.db.flush()

            report.incident_id = new_inc.incident_id
            self.db.commit()
            self.db.refresh(report)
            target_incident_id = new_inc.incident_id

        return {
            "report_id": report.report_id,
            "action": action.value if hasattr(action, "value") else str(action),
            "target_incident_id": target_incident_id,
            "confidence_score": result["confidence_score"],
            "score_breakdown": result["score_breakdown"],
        }
