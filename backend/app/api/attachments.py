import os
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from backend.app.database import get_db
    from backend.app.models import OperationalIncident, Attachment
    from backend.app.schemas import AttachmentResponse
    from backend.app.services.storage_service import (
        save_attachment_file,
        find_attachment_file_by_hash,
        sanitize_filename,
    )
    from backend.app.services.node_manager import NodeManager
    from backend.app.network.event_protocol import EventProtocolEngine
    from backend.app.sync.outbox_worker import StoreAndForwardWorker
except ImportError:
    from app.database import get_db
    from app.models import OperationalIncident, Attachment
    from app.schemas import AttachmentResponse
    from app.services.storage_service import (
        save_attachment_file,
        find_attachment_file_by_hash,
        sanitize_filename,
    )
    from app.services.node_manager import NodeManager
    from app.network.event_protocol import EventProtocolEngine
    from app.sync.outbox_worker import StoreAndForwardWorker

router = APIRouter(tags=["Incident Attachments"])


@router.post("/incidents/{incident_id}/attachments", response_model=List[AttachmentResponse], status_code=status.HTTP_201_CREATED)
async def upload_incident_attachments(
    incident_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload one or more photo attachments associated with an operational incident."""
    incident = db.query(OperationalIncident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )

    nm = NodeManager.get_instance()
    created_attachments: List[Attachment] = []
    attachment_events_payload = []

    for upload_file in files:
        content = await upload_file.read()
        if not content:
            continue

        filename = sanitize_filename(upload_file.filename or "attachment.jpg")
        mime_type = upload_file.content_type or "image/jpeg"

        try:
            sha256_hash, local_path, file_size = save_attachment_file(
                content=content,
                original_filename=filename,
                mime_type=mime_type,
            )
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

        attachment = Attachment(
            incident_id=incident_id,
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            sha256_hash=sha256_hash,
            local_path=local_path,
            source_node_id=nm.node_id or "local",
            sync_status="synced",
        )
        db.add(attachment)
        created_attachments.append(attachment)

        attachment_events_payload.append({
            "attachment_id": attachment.id,
            "filename": filename,
            "mime_type": mime_type,
            "file_size": file_size,
            "sha256_hash": sha256_hash,
            "source_node_id": attachment.source_node_id,
        })

    db.commit()
    for att in created_attachments:
        db.refresh(att)

    # Emit incident.attachment_added event to mesh outbox
    if created_attachments:
        try:
            EventProtocolEngine.emit_event(
                db=db,
                event_type="incident.attachment_added",
                payload={
                    "incident_id": incident_id,
                    "attachments": attachment_events_payload,
                    "added_by": nm.node_name,
                },
            )
            StoreAndForwardWorker.get_instance().trigger_flush()
        except Exception as e:
            print(f"[Warning] Failed to emit incident.attachment_added: {e}")

    return [AttachmentResponse.model_validate(att) for att in created_attachments]


@router.get("/incidents/{incident_id}/attachments", response_model=List[AttachmentResponse])
def get_incident_attachments(incident_id: str, db: Session = Depends(get_db)):
    """List all attachments for a specific operational incident."""
    attachments = db.query(Attachment).filter_by(incident_id=incident_id).order_by(Attachment.created_at.asc()).all()
    return [AttachmentResponse.model_validate(att) for att in attachments]


@router.get("/attachments/{attachment_id}", response_model=AttachmentResponse)
def get_attachment_metadata(attachment_id: str, db: Session = Depends(get_db)):
    """Get metadata for a specific attachment."""
    att = db.query(Attachment).filter_by(id=attachment_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    return AttachmentResponse.model_validate(att)


@router.get("/attachments/{attachment_id}/file")
def get_attachment_file(attachment_id: str, db: Session = Depends(get_db)):
    """Stream binary file content of an attachment."""
    att = db.query(Attachment).filter_by(id=attachment_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    local_path = Path(att.local_path)
    if not local_path.exists():
        # Attempt fallback via hash lookup
        fallback = find_attachment_file_by_hash(att.sha256_hash)
        if fallback and fallback.exists():
            local_path = fallback
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file missing from disk.")

    return FileResponse(
        path=str(local_path),
        media_type=att.mime_type or "image/jpeg",
        filename=att.filename,
    )


@router.get("/attachments/download/{sha256_hash}")
def download_attachment_by_hash(sha256_hash: str):
    """Download attachment file content by SHA-256 hash (used for peer mesh synchronization)."""
    target = find_attachment_file_by_hash(sha256_hash)
    if not target or not target.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No attachment found with hash '{sha256_hash}'."
        )

    # Infer basic media type
    ext = target.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"

    return FileResponse(
        path=str(target),
        media_type=mime,
        filename=target.name,
    )
