import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

try:
    from backend.app.database import Base
except ImportError:
    from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def current_utc_time():
    return datetime.now(timezone.utc)


class NodeRecord(Base):
    """Registered peer nodes discovered on the local mesh/LAN."""
    __tablename__ = "node_records"

    node_id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="responder")  # responder, commander, relay
    public_key = Column(Text, nullable=True)  # Ed25519 public key b64
    ip_address = Column(String(64), nullable=True)
    api_port = Column(Integer, nullable=False, default=8000)
    status = Column(String(30), nullable=False, default="online")  # online, offline, unreachable
    latency_ms = Column(Float, nullable=False, default=0.0)
    last_seen = Column(DateTime, nullable=False, default=current_utc_time)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)


class OperationalIncident(Base):
    """The master real-world incident created and managed at the command center."""
    __tablename__ = "operational_incidents"

    incident_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="open")  # open, in_progress, resolved, closed
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    category = Column(String(100), nullable=False, default="general")  # fire, flood, medical, structural, etc.
    latitude = Column(Float, nullable=True, default=None)
    longitude = Column(Float, nullable=True, default=None)
    accuracy = Column(Float, nullable=True)
    location_source = Column(String(50), nullable=True, default="gps")  # gps, unavailable
    captured_at = Column(DateTime, nullable=True, default=current_utc_time)
    summary = Column(Text, nullable=True)
    broadcaster_name = Column(String(100), nullable=True, default="Commander")
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    # Relationships
    reports = relationship("Report", back_populates="incident", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="incident")
    resources = relationship("ResourceRequest", back_populates="incident")
    attachments = relationship("Attachment", back_populates="incident", cascade="all, delete-orphan")


class Attachment(Base):
    """Binary media attachment (photo/document) associated with an incident."""
    __tablename__ = "attachments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("operational_incidents.incident_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), index=True, nullable=False)
    local_path = Column(String(500), nullable=False)
    source_node_id = Column(String(64), nullable=True)
    sync_status = Column(String(30), nullable=False, default="synced")  # synced, pending, failed
    created_at = Column(DateTime, nullable=False, default=current_utc_time)

    # Relationships
    incident = relationship("OperationalIncident", back_populates="attachments")


class SegregatedCorrelation(Base):
    """Persisted record of correlation reviews where user chose 'Keep Segregated'."""
    __tablename__ = "segregated_correlations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), nullable=False)
    master_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)


class Report(Base):
    """Individual field responder observation / sighting. Never destroyed on duplicate merge."""
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
    """Tactical emergency message broadcast across the mesh."""
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
    """Logistical resource dispatch request."""
    __tablename__ = "resource_requests"

    resource_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("operational_incidents.incident_id"), nullable=True)
    requester_id = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)  # water, medical_kit, ambulance, boat
    quantity = Column(Integer, nullable=False, default=1)
    urgency = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(50), nullable=False, default="pending")  # pending, dispatched, fulfilled
    timestamp = Column(DateTime, nullable=False, default=current_utc_time)

    # Relationships
    incident = relationship("OperationalIncident", back_populates="resources")


class EventLog(Base):
    """Immutable distributed event ledger for idempotent synchronization."""
    __tablename__ = "event_logs"

    event_id = Column(String(36), primary_key=True)  # Unique UUID
    event_type = Column(String(100), nullable=False)  # incident.created, report.created, etc.
    origin_node_id = Column(String(64), nullable=False)
    timestamp = Column(Float, nullable=False)
    payload = Column(Text, nullable=False)  # JSON-serialized payload
    version = Column(Integer, nullable=False, default=1)
    hop_count = Column(Integer, nullable=False, default=0)
    signature = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)


class OutboxItem(Base):
    """Delay-tolerant store-and-forward queue for events awaiting transmission to peers."""
    __tablename__ = "outbox_items"

    outbox_id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), nullable=False)
    target_node_id = Column(String(64), nullable=True)  # None = broadcast to all peers
    status = Column(String(30), nullable=False, default="pending")  # pending, sent, acknowledged, failed
    attempts = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)


class SyncVector(Base):
    """Vector clock / state sync tracking highest synchronized event per peer node."""
    __tablename__ = "sync_vectors"

    peer_node_id = Column(String(64), primary_key=True)
    last_event_id = Column(String(36), nullable=True)
    last_timestamp = Column(Float, nullable=False, default=0.0)
    last_clock = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)


class SyncAck(Base):
    __tablename__ = "sync_acks"

    ack_id = Column(String(36), primary_key=True, default=generate_uuid)
    source_device = Column(String(255), nullable=False)
    target_device = Column(String(255), nullable=False)
    last_sync_timestamp = Column(DateTime, nullable=False, default=current_utc_time)
    device_clock = Column(Integer, nullable=False, default=0)
