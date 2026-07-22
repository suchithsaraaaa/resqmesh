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
except ImportError:
    from app.database import get_db
    from app.models import ChatMessage, ResourceRequest, OperationalIncident
    from app.schemas import (
        ChatMessageCreate, ChatMessageResponse,
        ResourceRequestCreate, ResourceRequestResponse
    )

router = APIRouter(prefix="/comms", tags=["Communications & Resources"])


# --- Chat Messages ---
@router.post("/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(msg_in: ChatMessageCreate, db: Session = Depends(get_db)):
    """Publish a new chat message."""
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
    """Submit a resource dispatch request."""
    if res_in.incident_id:
        incident = db.query(OperationalIncident).filter(
            OperationalIncident.incident_id == res_in.incident_id
        ).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operational Incident with id '{res_in.incident_id}' not found."
            )

    res = ResourceRequest(**res_in.model_dump())
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


@router.get("/resources", response_model=List[ResourceRequestResponse])
def list_resource_requests(incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List resource dispatch requests."""
    query = db.query(ResourceRequest)
    if incident_id:
        query = query.filter(ResourceRequest.incident_id == incident_id)
    return query.order_by(ResourceRequest.timestamp.desc()).all()
