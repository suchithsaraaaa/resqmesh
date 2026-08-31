from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.database import get_db
    from backend.app.models import ChatMessage, ResourceRequest, OperationalIncident
    from backend.app.schemas import (
        ChatMessageCreate, ChatMessageResponse,
        ResourceRequestCreate, ResourceRequestResponse
    )
    from backend.app.network.event_protocol import EventProtocolEngine
    from backend.app.sync.outbox_worker import StoreAndForwardWorker
except ImportError:
    from app.database import get_db
    from app.models import ChatMessage, ResourceRequest, OperationalIncident
    from app.schemas import (
        ChatMessageCreate, ChatMessageResponse,
        ResourceRequestCreate, ResourceRequestResponse
    )
    from app.network.event_protocol import EventProtocolEngine
    from app.sync.outbox_worker import StoreAndForwardWorker

router = APIRouter(prefix="/comms", tags=["Communications & Resources"])


# --- Chat Messages ---
@router.post("/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(msg_in: ChatMessageCreate, db: Session = Depends(get_db)):
    """Publish a new chat message and broadcast across mesh."""
    if msg_in.incident_id:
        incident = db.query(OperationalIncident).filter(
            OperationalIncident.incident_id == msg_in.incident_id
        ).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operational Incident with id '{msg_in.incident_id}' not found."
            )

    msg = ChatMessage(**msg_in.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)

    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="message.created",
            payload={
                "message_id": msg.message_id,
                "incident_id": msg.incident_id,
                "sender_device_id": msg.sender_device_id,
                "sender_user_id": msg.sender_user_id,
                "text": msg.text,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit message.created: {e}")

    return msg


@router.get("/messages", response_model=List[ChatMessageResponse])
def list_messages(incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List chat messages with optional incident filter."""
    query = db.query(ChatMessage)
    if incident_id:
        query = query.filter(ChatMessage.incident_id == incident_id)
    return query.order_by(ChatMessage.timestamp.asc()).all()


# --- Resource Requests ---
@router.post("/resources", response_model=ResourceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_resource_request(res_in: ResourceRequestCreate, db: Session = Depends(get_db)):
    """Submit a resource dispatch request tied to an incident and broadcast across mesh."""
    inc_title = None
    if res_in.incident_id:
        incident = db.query(OperationalIncident).filter(
            OperationalIncident.incident_id == res_in.incident_id
        ).first()
        if incident:
            inc_title = incident.title

    res = ResourceRequest(**res_in.model_dump())
    db.add(res)
    db.commit()
    db.refresh(res)

    resp = ResourceRequestResponse.model_validate(res)
    resp.incident_title = inc_title

    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="resource.created",
            payload={
                "resource_id": res.resource_id,
                "incident_id": res.incident_id,
                "incident_title": inc_title,
                "requester_id": res.requester_id,
                "resource_type": res.resource_type,
                "quantity": res.quantity,
                "urgency": res.urgency,
                "status": res.status,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit resource.created: {e}")

    return resp


@router.get("/resources", response_model=List[ResourceRequestResponse])
def list_resource_requests(incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List resource dispatch requests with incident titles (seeding initial items if empty)."""
    query = db.query(ResourceRequest).filter(ResourceRequest.status != "rescinded")
    if incident_id:
        query = query.filter(ResourceRequest.incident_id == incident_id)
    results = query.order_by(ResourceRequest.timestamp.desc()).all()

    resp_list = []
    for r in results:
        resp = ResourceRequestResponse.model_validate(r)
        if r.incident_id:
            inc = db.query(OperationalIncident).filter_by(incident_id=r.incident_id).first()
            if inc:
                resp.incident_title = inc.title
        resp_list.append(resp)

    return resp_list


@router.patch("/resources/{resource_id}", response_model=ResourceRequestResponse)
def update_resource_status(
    resource_id: str,
    status_val: str,
    db: Session = Depends(get_db)
):
    """Update resource dispatch status (pending, dispatched, fulfilled) and broadcast across mesh."""
    res = db.query(ResourceRequest).filter(ResourceRequest.resource_id == resource_id).first()
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource request with id '{resource_id}' not found."
        )
    res.status = status_val
    db.commit()
    db.refresh(res)

    resp = ResourceRequestResponse.model_validate(res)
    if res.incident_id:
        inc = db.query(OperationalIncident).filter_by(incident_id=res.incident_id).first()
        if inc:
            resp.incident_title = inc.title

    try:
        EventProtocolEngine.emit_event(
            db=db,
            event_type="resource.updated",
            payload={
                "resource_id": res.resource_id,
                "incident_id": res.incident_id,
                "incident_title": resp.incident_title,
                "status": res.status,
                "resource_type": res.resource_type,
                "quantity": res.quantity,
                "urgency": res.urgency,
            },
        )
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception as e:
        print(f"[Warning] Failed to emit resource.updated: {e}")

    return resp

