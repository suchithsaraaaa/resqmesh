from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from backend.app.database import get_db
    from backend.app.ai.rag_pipeline import RAGPipeline
    from backend.app.ai.clustering import IncidentClusteringEngine
except ImportError:
    from app.database import get_db
    from app.ai.rag_pipeline import RAGPipeline
    from app.ai.clustering import IncidentClusteringEngine

router = APIRouter(prefix="/ai", tags=["On-Device AI Engine"])

rag_pipeline = RAGPipeline()
clustering_engine = IncidentClusteringEngine()


class RAGRequest(BaseModel):
    description: str
    category: Optional[str] = None
    top_k: int = 5
    incident_context: Optional[dict] = None
    debug: bool = False


class CorrelateRequest(BaseModel):
    category: str
    description: str
    latitude: float
    longitude: float


@router.post("/rag-guidance")
def get_rag_sop_guidance(req: RAGRequest):
    """Retrieve on-device Standard Operating Procedures (SOPs) and synthesize tactical guidance."""
    return rag_pipeline.generate_sop_guidance(
        description=req.description,
        category=req.category,
        top_k=req.top_k,
        incident_context=req.incident_context,
        debug=req.debug,
    )


@router.post("/correlate")
def evaluate_report_correlation(req: CorrelateRequest, db: Session = Depends(get_db)):
    """Evaluate multi-factor similarity of a report against all active operational incidents."""
    try:
        from backend.app.models import OperationalIncident
    except ImportError:
        from app.models import OperationalIncident

    active_incidents = (
        db.query(OperationalIncident)
        .filter(OperationalIncident.status != "closed")
        .all()
    )

    incidents_data = [
        {
            "id": inc.incident_id,
            "title": inc.title,
            "category": inc.category,
            "description": inc.summary or inc.title,
            "lat": inc.latitude,
            "lon": inc.longitude,
            "created_at": inc.created_at,
        }
        for inc in active_incidents
    ]

    report_data = {
        "category": req.category,
        "description": req.description,
        "lat": req.latitude,
        "lon": req.longitude,
    }

    result = clustering_engine.evaluate_report_against_incidents(
        report_data, incidents_data
    )

    return result


@router.post("/triage")
def generate_incident_triage(req: RAGRequest):
    """
    Generate actionable triage recommendation, resource dispatch advice, and SOP guidelines.
    """
    guidance = rag_pipeline.generate_sop_guidance(
        description=req.description,
        category=req.category,
        top_k=req.top_k,
    )

    # Resource suggestions based on category
    resource_map = {
        "fire": [
            {"type": "Fire Engine / Water Tender", "quantity": 2, "urgency": "critical"},
            {"type": "Breathing Apparatus (SCBA)", "quantity": 4, "urgency": "high"},
        ],
        "flood": [
            {"type": "Inflatable Rescue Boat", "quantity": 2, "urgency": "critical"},
            {"type": "Life Jackets & Throw Bags", "quantity": 10, "urgency": "high"},
        ],
        "medical": [
            {"type": "Paramedic Field Trauma Kit", "quantity": 3, "urgency": "critical"},
            {"type": "Transport Stretchers", "quantity": 2, "urgency": "high"},
        ],
        "hazmat": [
            {"type": "Level A/B Hazmat Encapsulation Suits", "quantity": 4, "urgency": "critical"},
            {"type": "Multi-Gas Detector & Neutralizer", "quantity": 2, "urgency": "high"},
        ],
        "structural": [
            {"type": "Hydraulic Shoring / Spreaders", "quantity": 2, "urgency": "critical"},
            {"type": "Acoustic Void Listening Device", "quantity": 1, "urgency": "high"},
        ],
    }

    cat_key = (req.category or "general").lower()
    suggested_resources = resource_map.get(
        cat_key,
        [{"type": "General First Aid Kit", "quantity": 2, "urgency": "medium"}],
    )

    return {
        "category": req.category,
        "recommendation": guidance.get("recommendation"),
        "retrieved_sops": guidance.get("retrieved_sops", []),
        "suggested_resources": suggested_resources,
    }


@router.post("/query")
def query_emergency_knowledge_base(req: dict):
    """Query offline emergency knowledge base for operator advice."""
    query = req.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query string is required.")

    return rag_pipeline.generate_sop_guidance(
        description=query,
        category=req.get("category"),
        top_k=req.get("top_k", 5),
        incident_context=req.get("incident_context"),
        debug=req.get("debug", False),
    )


@router.get("/sops")
def list_available_sops():
    """List all Standard Operating Procedures indexed in the on-device vector store."""
    docs = rag_pipeline.vector_store.documents.values()
    return [doc.to_dict() for doc in docs]
