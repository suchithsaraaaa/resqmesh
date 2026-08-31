from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.database import get_db
    from backend.app.models import Report, OperationalIncident
    from backend.app.schemas import ReportCreate, ReportResponse
except ImportError:
    from app.database import get_db
    from app.models import Report, OperationalIncident
    from app.schemas import ReportCreate, ReportResponse

try:
    from backend.app.services.incident_matcher import IncidentMatcherService
    from backend.app.network.event_protocol import EventProtocolEngine
    from backend.app.sync.outbox_worker import StoreAndForwardWorker
except ImportError:
    from app.services.incident_matcher import IncidentMatcherService
    from app.network.event_protocol import EventProtocolEngine
    from app.sync.outbox_worker import StoreAndForwardWorker

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(report_in: ReportCreate, db: Session = Depends(get_db)):
    """Create a new responder field report and broadcast across mesh."""
    if report_in.incident_id:
        incident = db.query(OperationalIncident).filter(
            OperationalIncident.incident_id == report_in.incident_id
        ).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operational Incident with id '{report_in.incident_id}' not found."
            )

    report = Report(**report_in.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)

    # Emit signed event into mesh outbox
    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="report.created",
            payload={
                "report_id": report.report_id,
                "incident_id": report.incident_id,
                "device_id": report.device_id,
                "user_id": report.user_id,
                "category": report.category,
                "description": report.description,
                "latitude": report.latitude,
                "longitude": report.longitude,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit report.created: {e}")

    # If no incident_id assigned, run AI incident correlation engine
    if not report.incident_id:
        try:
            IncidentMatcherService(db).process_new_report(report)
        except Exception:
            pass

    return report


@router.get("/", response_model=List[ReportResponse])
def list_reports(
    incident_id: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List field reports with optional filters."""
    query = db.query(Report)
    if incident_id:
        query = query.filter(Report.incident_id == incident_id)
    if category:
        query = query.filter(Report.category == category)
    return query.order_by(Report.timestamp.desc()).all()


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get a specific report by ID."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id '{report_id}' not found."
        )
    return report


@router.patch("/{report_id}/attach", response_model=ReportResponse)
def attach_report_to_incident(
    report_id: str,
    incident_id: str,
    db: Session = Depends(get_db)
):
    """Attach or re-assign a report to a master Operational Incident."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id '{report_id}' not found."
        )

    incident = db.query(OperationalIncident).filter(
        OperationalIncident.incident_id == incident_id
    ).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operational Incident with id '{incident_id}' not found."
        )

    report.incident_id = incident_id
    db.commit()
    db.refresh(report)
    return report
