from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# --- Report Schemas ---
class ReportBase(BaseModel):
    device_id: str
    user_id: str
    latitude: float = 0.0
    longitude: float = 0.0
    description: str
    category: str = "general"
    attachments: Optional[str] = None
    device_clock: int = 0


class ReportCreate(ReportBase):
    incident_id: Optional[str] = None


class ReportResponse(ReportBase):
    report_id: str
    incident_id: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Attachment Schemas ---
class AttachmentBase(BaseModel):
    filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    source_node_id: Optional[str] = None
    sync_status: str = "synced"


class AttachmentCreate(AttachmentBase):
    incident_id: str
    local_path: str


class AttachmentResponse(AttachmentBase):
    id: str
    incident_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Operational Incident Schemas ---
class OperationalIncidentBase(BaseModel):
    title: str
    status: str = "open"
    severity: str = "medium"
    category: str = "general"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    location_source: Optional[str] = "gps"  # "gps" or "unavailable"
    captured_at: Optional[datetime] = None
    summary: Optional[str] = None
    broadcaster_name: Optional[str] = "Commander"


class OperationalIncidentCreate(OperationalIncidentBase):
    pass


class OperationalIncidentResponse(OperationalIncidentBase):
    incident_id: str
    created_at: datetime
    updated_at: datetime
    report_count: int = 1
    reports: List[ReportResponse] = []
    attachments: List[AttachmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Chat Message Schemas ---
class ChatMessageBase(BaseModel):
    sender_device_id: str
    sender_user_id: str
    text: str
    device_clock: int = 0


class ChatMessageCreate(ChatMessageBase):
    incident_id: Optional[str] = None


class ChatMessageResponse(ChatMessageBase):
    message_id: str
    incident_id: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Resource Request Schemas ---
class ResourceRequestBase(BaseModel):
    requester_id: str
    resource_type: str
    quantity: int = 1
    urgency: str = "medium"
    status: str = "pending"


class ResourceRequestCreate(ResourceRequestBase):
    incident_id: Optional[str] = None


class ResourceRequestResponse(ResourceRequestBase):
    resource_id: str
    incident_id: Optional[str] = None
    incident_title: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Node Schemas ---
class NodeRecordBase(BaseModel):
    node_id: str
    name: str
    role: str = "responder"
    public_key: Optional[str] = None
    ip_address: Optional[str] = None
    api_port: int = 8000
    status: str = "online"
    latency_ms: float = 0.0


class NodeRecordCreate(NodeRecordBase):
    pass


class NodeRecordResponse(NodeRecordBase):
    last_seen: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


from typing import Optional, List, Dict, Any, Union

# --- Event Log Schemas ---
class EventLogBase(BaseModel):
    event_id: str
    event_type: str
    origin_node_id: str
    timestamp: float
    payload: Any
    version: int = 1
    hop_count: int = 0
    signature: Optional[str] = None


class EventLogCreate(EventLogBase):
    pass


class EventLogResponse(EventLogBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Outbox Schemas ---
class OutboxItemBase(BaseModel):
    event_id: str
    target_node_id: Optional[str] = None
    status: str = "pending"
    attempts: int = 0


class OutboxItemCreate(OutboxItemBase):
    pass


class OutboxItemResponse(OutboxItemBase):
    outbox_id: str
    last_attempt_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Sync Vector Schemas ---
class SyncVectorBase(BaseModel):
    peer_node_id: str
    last_event_id: Optional[str] = None
    last_timestamp: float = 0.0
    last_clock: int = 0


class SyncVectorCreate(SyncVectorBase):
    pass


class SyncVectorResponse(SyncVectorBase):
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Sync Ack Schemas ---
class SyncAckBase(BaseModel):
    source_device: str
    target_device: str
    device_clock: int = 0


class SyncAckCreate(SyncAckBase):
    pass


class SyncAckResponse(SyncAckBase):
    ack_id: str
    last_sync_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

