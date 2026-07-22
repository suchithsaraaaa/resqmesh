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


# --- Operational Incident Schemas ---
class OperationalIncidentBase(BaseModel):
    title: str
    status: str = "open"
    severity: str = "medium"
    category: str = "general"
    latitude: float = 0.0
    longitude: float = 0.0
    summary: Optional[str] = None


class OperationalIncidentCreate(OperationalIncidentBase):
    pass


class OperationalIncidentResponse(OperationalIncidentBase):
    incident_id: str
    created_at: datetime
    updated_at: datetime
    reports: List[ReportResponse] = []

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
    timestamp: datetime

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
