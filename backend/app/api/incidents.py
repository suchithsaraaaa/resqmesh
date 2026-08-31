from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

try:
    from backend.app.database import get_db
    from backend.app.models import OperationalIncident, Report
    from backend.app.schemas import OperationalIncidentCreate, OperationalIncidentResponse
    from backend.app.network.event_protocol import EventProtocolEngine
    from backend.app.sync.outbox_worker import StoreAndForwardWorker
except ImportError:
    from app.database import get_db
    from app.models import OperationalIncident, Report
    from app.schemas import OperationalIncidentCreate, OperationalIncidentResponse
    from app.network.event_protocol import EventProtocolEngine
    from app.sync.outbox_worker import StoreAndForwardWorker

router = APIRouter(prefix="/incidents", tags=["Operational Incidents"])


class MergeIncidentRequest(BaseModel):
    report_id: Optional[str] = None
    summary_note: Optional[str] = None


@router.post("/", response_model=OperationalIncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(incident_in: OperationalIncidentCreate, db: Session = Depends(get_db)):
    """Create a new master Operational Incident with broadcaster name and broadcast across mesh."""
    try:
        from backend.app.services.node_manager import NodeManager
    except ImportError:
        from app.services.node_manager import NodeManager
    nm = NodeManager.get_instance()

    inc_dict = incident_in.model_dump()
    if not inc_dict.get("broadcaster_name") or inc_dict.get("broadcaster_name") == "Commander":
        inc_dict["broadcaster_name"] = nm.node_name or "Commander"

    incident = OperationalIncident(**inc_dict)
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Emit signed event into mesh outbox for immediate peer broadcast
    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="incident.created",
            payload={
                "incident_id": incident.incident_id,
                "title": incident.title,
                "category": incident.category,
                "severity": incident.severity,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "accuracy": incident.accuracy,
                "location_source": incident.location_source,
                "captured_at": incident.captured_at.isoformat() if incident.captured_at else None,
                "summary": incident.summary or "",
                "status": incident.status or "open",
                "broadcaster_name": incident.broadcaster_name,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit incident.created event: {e}")

    resp = OperationalIncidentResponse.model_validate(incident)
    resp.report_count = 1 + len(incident.reports)
    return resp


@router.get("/", response_model=List[OperationalIncidentResponse])
def list_incidents(
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List master operational incidents excluding merged duplicates."""
    query = db.query(OperationalIncident)
    if status_filter:
        query = query.filter(OperationalIncident.status == status_filter)
    else:
        # Exclude merged duplicate incidents from active list
        query = query.filter(OperationalIncident.status != "merged")
    if severity:
        query = query.filter(OperationalIncident.severity == severity)
    incidents = query.order_by(OperationalIncident.created_at.desc()).all()
    results = []
    for inc in incidents:
        inc_data = OperationalIncidentResponse.model_validate(inc)
        inc_data.report_count = 1 + len(inc.reports)
        results.append(inc_data)
    return results


class SegregateCorrelationRequest(BaseModel):
    report_id: str
    target_incident_id: Optional[str] = None


@router.post("/clusters/dismiss")
def dismiss_correlation_cluster(req: SegregateCorrelationRequest, db: Session = Depends(get_db)):
    """Mark a duplicate correlation candidate as segregated so it never reappears in AI screening."""
    try:
        from backend.app.models import SegregatedCorrelation
    except ImportError:
        from app.models import SegregatedCorrelation

    candidate_id = req.report_id
    master_id = req.target_incident_id or "all"

    existing = db.query(SegregatedCorrelation).filter_by(candidate_id=candidate_id, master_id=master_id).first()
    if not existing:
        db.add(SegregatedCorrelation(candidate_id=candidate_id, master_id=master_id))
        db.commit()

    # Emit signed mesh event so peers also suppress this duplicate correlation
    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="incident.segregated",
            payload={
                "candidate_id": candidate_id,
                "master_id": master_id,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit incident.segregated event: {e}")

    return {"status": "segregated", "candidate_id": candidate_id, "master_id": master_id}


@router.get("/clusters/pending")
def get_pending_clusters(db: Session = Depends(get_db)):
    """Return pending AI correlation report clusters awaiting approval, actively screening all active incidents."""
    try:
        from backend.app.ai.similarity import IncidentSimilarityEngine, haversine_distance_meters
        from backend.app.models import SegregatedCorrelation
    except ImportError:
        from app.ai.similarity import IncidentSimilarityEngine, haversine_distance_meters
        from app.models import SegregatedCorrelation

    sim_engine = IncidentSimilarityEngine()
    active_incidents = (
        db.query(OperationalIncident)
        .filter(OperationalIncident.status.notin_(["closed", "merged"]))
        .order_by(OperationalIncident.created_at.asc())
        .all()
    )

    # Load all persisted segregated pairs to suppress dismissed duplicate matches
    seg_rows = db.query(SegregatedCorrelation).all()
    segregated_pairs = set()
    for s in seg_rows:
        segregated_pairs.add((s.candidate_id, s.master_id))
        segregated_pairs.add((s.master_id, s.candidate_id))
        segregated_pairs.add((s.candidate_id, "all"))

    clusters = []
    matched_ids = set()

    # Active pairwise screening across all operational incidents
    for i in range(len(active_incidents)):
        inc_a = active_incidents[i]
        if inc_a.incident_id in matched_ids:
            continue

        for j in range(i + 1, len(active_incidents)):
            inc_b = active_incidents[j]
            if inc_b.incident_id in matched_ids:
                continue

            # Skip pairs marked as Keep Segregated
            if (inc_b.incident_id, inc_a.incident_id) in segregated_pairs or (inc_a.incident_id, inc_b.incident_id) in segregated_pairs:
                continue

            data_a = {
                "lat": inc_a.latitude,
                "lon": inc_a.longitude,
                "created_at": inc_a.created_at,
                "category": inc_a.category,
                "description": f"{inc_a.title} {inc_a.summary or ''}".strip(),
            }
            data_b = {
                "lat": inc_b.latitude,
                "lon": inc_b.longitude,
                "created_at": inc_b.created_at,
                "category": inc_b.category,
                "description": f"{inc_b.title} {inc_b.summary or ''}".strip(),
            }

            scores = sim_engine.calculate_similarity_score(data_b, data_a)
            composite = scores.get("composite", 0.0)

            title_a = inc_a.title.strip().lower()
            title_b = inc_b.title.strip().lower()
            title_match = (title_a == title_b) or (title_a in title_b) or (title_b in title_a)

            if inc_a.latitude is not None and inc_a.longitude is not None and inc_b.latitude is not None and inc_b.longitude is not None:
                dist_m = haversine_distance_meters(inc_a.latitude, inc_a.longitude, inc_b.latitude, inc_b.longitude)
            else:
                dist_m = 999999.0

            # High confidence threshold for duplicate detection
            if (title_match and dist_m <= 5000) or composite >= 0.45:
                confidence = max(composite, 0.94 if (title_match and dist_m <= 1000) else 0.85)
                matched_ids.add(inc_b.incident_id)
                clusters.append({
                    "reportId": inc_b.incident_id,
                    "category": inc_b.category,
                    "description": f"Duplicate incident '{inc_b.title}' broadcasted by {inc_b.broadcaster_name or 'Field Unit'}",
                    "lat": inc_b.latitude if inc_b.latitude is not None else 0.0,
                    "lon": inc_b.longitude if inc_b.longitude is not None else 0.0,
                    "confidenceScore": round(confidence, 2),
                    "targetIncidentId": inc_a.incident_id,
                    "targetIncidentTitle": inc_a.title,
                })

    # Also check demo report if not yet merged and no duplicate clusters found
    demo_merged = db.query(Report).filter(Report.report_id == "rep-mesh-demo-1").first()
    if not (demo_merged and demo_merged.incident_id) and active_incidents and not clusters:
        active_inc = active_incidents[0]
        clusters.append({
            "reportId": "rep-mesh-demo-1",
            "category": "fire",
            "description": "Secondary transformer spark sighted 200m north of station",
            "lat": active_inc.latitude + 0.001,
            "lon": active_inc.longitude + 0.001,
            "confidenceScore": 0.88,
            "targetIncidentId": active_inc.incident_id,
            "targetIncidentTitle": active_inc.title,
        })

    return clusters


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
    resp = OperationalIncidentResponse.model_validate(incident)
    resp.report_count = 1 + len(incident.reports)
    return resp


@router.patch("/{incident_id}", response_model=OperationalIncidentResponse)
def update_incident_status(
    incident_id: str,
    status_val: Optional[str] = None,
    severity: Optional[str] = None,
    summary: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update incident operational status, severity, or AI summary and broadcast across mesh."""
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
    if summary:
        incident.summary = summary

    db.commit()
    db.refresh(incident)

    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="incident.updated",
            payload={
                "incident_id": incident.incident_id,
                "title": incident.title,
                "status": incident.status,
                "severity": incident.severity,
                "summary": incident.summary,
                "broadcaster_name": incident.broadcaster_name,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit incident.updated event: {e}")

    resp = OperationalIncidentResponse.model_validate(incident)
    resp.report_count = 1 + len(incident.reports)
    return resp


@router.post("/{incident_id}/merge", response_model=OperationalIncidentResponse)
def merge_incident_report(
    incident_id: str,
    merge_in: MergeIncidentRequest,
    db: Session = Depends(get_db)
):
    """Approve merge of a duplicate incident or report into an incident and broadcast across mesh."""
    import uuid
    try:
        from backend.app.services.node_manager import NodeManager
    except ImportError:
        from app.services.node_manager import NodeManager
    nm = NodeManager.get_instance()

    incident = db.query(OperationalIncident).filter(
        OperationalIncident.incident_id == incident_id
    ).first()
    if not incident:
        incident = db.query(OperationalIncident).filter(OperationalIncident.status != "merged").order_by(OperationalIncident.created_at.asc()).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No operational incident found to merge into."
            )

    rep_id = merge_in.report_id or f"rep-{uuid.uuid4().hex[:8]}"
    summary_note = merge_in.summary_note or "Duplicate observation verified & merged"

    # Check if report_id is another OperationalIncident (Duplicate Incident Merge)
    dup_inc = db.query(OperationalIncident).filter(OperationalIncident.incident_id == rep_id).first()
    dup_inc_id = None
    if dup_inc:
        dup_inc_id = dup_inc.incident_id
        dup_inc.status = "merged"
        summary_note = f"Duplicate incident '{dup_inc.title}' (by {dup_inc.broadcaster_name or 'Peer'}) merged"

        # Re-link any reports from dup_inc to master incident
        for r in dup_inc.reports:
            r.incident_id = incident.incident_id

        # Re-link any resources from dup_inc to master incident
        for res in dup_inc.resources:
            res.incident_id = incident.incident_id

        # Create a report entity representing this duplicate sighting
        new_report = Report(
            report_id=f"rep-dup-{dup_inc.incident_id[:8]}",
            incident_id=incident.incident_id,
            device_id=dup_inc.broadcaster_name or nm.node_id,
            user_id=dup_inc.broadcaster_name or "Responder",
            category=dup_inc.category,
            description=summary_note,
            latitude=dup_inc.latitude,
            longitude=dup_inc.longitude,
        )
        db.add(new_report)
        rep_id = new_report.report_id
    else:
        # Standard report merge
        report = db.query(Report).filter(Report.report_id == rep_id).first()
        if report:
            report.incident_id = incident.incident_id
        else:
            new_report = Report(
                report_id=rep_id,
                incident_id=incident.incident_id,
                device_id=nm.node_id,
                user_id=nm.node_name,
                category=incident.category,
                description=summary_note,
                latitude=incident.latitude,
                longitude=incident.longitude,
            )
            db.add(new_report)

    incident.summary = (
        f"{incident.summary} | Merged: {summary_note}"
        if incident.summary
        else f"Merged: {summary_note}"
    )

    db.commit()
    db.refresh(incident)

    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="incident.merged",
            payload={
                "incident_id": incident.incident_id,
                "duplicate_incident_id": dup_inc_id,
                "report_id": rep_id,
                "title": incident.title,
                "summary": incident.summary,
                "description": summary_note,
                "merged_by": nm.node_name,
                "report_count": 1 + len(incident.reports),
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit incident.merged event: {e}")

    resp = OperationalIncidentResponse.model_validate(incident)
    resp.report_count = 1 + len(incident.reports)
    return resp
