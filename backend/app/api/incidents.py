from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.database import get_db
    from backend.app.models import OperationalIncident
    from backend.app.schemas import OperationalIncidentCreate, OperationalIncidentResponse
except ImportError:
    from app.database import get_db
    from app.models import OperationalIncident
    from app.schemas import OperationalIncidentCreate, OperationalIncidentResponse

router = APIRouter(prefix="/incidents", tags=["Operational Incidents"])


@router.post("/", response_model=OperationalIncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(incident_in: OperationalIncidentCreate, db: Session = Depends(get_db)):
    """Create a new master Operational Incident."""
    incident = OperationalIncident(**incident_in.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/", response_model=List[OperationalIncidentResponse])
def list_incidents(
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List master operational incidents with optional filtering."""
    query = db.query(OperationalIncident)
    if status_filter:
        query = query.filter(OperationalIncident.status == status_filter)
    if severity:
        query = query.filter(OperationalIncident.severity == severity)
    return query.order_by(OperationalIncident.created_at.desc()).all()


@router.get("/{incident_id}", response_model=OperationalIncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get operational incident by ID with all associated responder reports."""
    incident = db.query(OperationalIncident).filter(
        OperationalIncident.incident_id == incident_id
    ).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operational Incident with id '{incident_id}' not found."
        )
    return incident


@router.patch("/{incident_id}", response_model=OperationalIncidentResponse)
def update_incident_status(
    incident_id: str,
    status_val: Optional[str] = None,
    severity: Optional[str] = None,
    summary: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update incident operational status, severity, or AI summary."""
    incident = db.query(OperationalIncident).filter(
        OperationalIncident.incident_id == incident_id
    ).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operational Incident with id '{incident_id}' not found."
        )

    if status_val:
        incident.status = status_val
    if severity:
        incident.severity = severity
    if summary is not None:
        incident.summary = summary

    db.commit()
    db.refresh(incident)
    return incident
