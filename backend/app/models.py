import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
try:
    from backend.app.database import Base
except ImportError:
    from app.database import Base



def generate_uuid():
    return str(uuid.uuid4())


def current_utc_time():
    return datetime.now(timezone.utc)


class OperationalIncident(Base):
    __tablename__ = "operational_incidents"

    incident_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="open")  # open, in_progress, resolved, closed
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    category = Column(String(100), nullable=False, default="general")  # fire, flood, medical, structural, etc.
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    # Relationships
    reports = relationship("Report", back_populates="incident", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="incident")
    resources = relationship("ResourceRequest", back_populates="incident")


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("operational_incidents.incident_id"), nullable=True)
    device_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=current_utc_time)
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, default="general")
    attachments = Column(Text, nullable=True)  # JSON string of media URIs
    device_clock = Column(Integer, nullable=False, default=0)

    # Relationships
    incident = relationship("OperationalIncident", back_populates="reports")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("operational_incidents.incident_id"), nullable=True)
    sender_device_id = Column(String(255), nullable=False)
    sender_user_id = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=current_utc_time)
    device_clock = Column(Integer, nullable=False, default=0)

    # Relationships
    incident = relationship("OperationalIncident", back_populates="messages")


class ResourceRequest(Base):
    __tablename__ = "resource_requests"

    resource_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("operational_incidents.incident_id"), nullable=True)
    requester_id = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)  # water, medical_kit, ambulance, boat
    quantity = Column(Integer, nullable=False, default=1)
    urgency = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(50), nullable=False, default="pending")  # pending, assigned, fulfilled
    timestamp = Column(DateTime, nullable=False, default=current_utc_time)

    # Relationships
    incident = relationship("OperationalIncident", back_populates="resources")


class SyncAck(Base):
    __tablename__ = "sync_acks"

    ack_id = Column(String(36), primary_key=True, default=generate_uuid)
    source_device = Column(String(255), nullable=False)
    target_device = Column(String(255), nullable=False)
    last_sync_timestamp = Column(DateTime, nullable=False, default=current_utc_time)
    device_clock = Column(Integer, nullable=False, default=0)
