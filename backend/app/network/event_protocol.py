import json
import time
import uuid
import logging
from typing import Dict, Optional, Tuple

try:
    from backend.app.models import EventLog, OutboxItem, OperationalIncident, Report, ChatMessage, ResourceRequest
    from backend.app.crypto.security import DeviceKeyPair, verify_signature
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.models import EventLog, OutboxItem, OperationalIncident, Report, ChatMessage, ResourceRequest
    from app.crypto.security import DeviceKeyPair, verify_signature
    from app.services.node_manager import NodeManager

logger = logging.getLogger("ResQMesh.EventProtocol")


class EventEnvelope:
    """Standard idempotent multi-hop event envelope."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        origin_node_id: str,
        timestamp: float,
        device_clock: int,
        payload: dict,
        version: int = 1,
        hop_count: int = 0,
        ttl: int = 5,
        signature: Optional[str] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.origin_node_id = origin_node_id
        self.timestamp = timestamp
        self.device_clock = device_clock
        self.payload = payload
        self.version = version
        self.hop_count = hop_count
        self.ttl = ttl
        self.signature = signature

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "origin_node_id": self.origin_node_id,
            "timestamp": self.timestamp,
            "device_clock": self.device_clock,
            "version": self.version,
            "hop_count": self.hop_count,
            "ttl": self.ttl,
            "signature": self.signature,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EventEnvelope":
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            origin_node_id=data["origin_node_id"],
            timestamp=data["timestamp"],
            device_clock=data.get("device_clock", 0),
            payload=data.get("payload", {}),
            version=data.get("version", 1),
            hop_count=data.get("hop_count", 0),
            ttl=data.get("ttl", 5),
            signature=data.get("signature"),
        )


class EventProtocolEngine:
    """Manages event creation, signing, outbox queuing, and ACK processing."""

    _clock: int = 0

    @classmethod
    def get_next_clock(cls) -> int:
        cls._clock += 1
        return cls._clock

    @staticmethod
    def emit_event(
        db,
        event_type: str,
        payload: dict,
        target_node_id: Optional[str] = None,
        node_manager: Optional[NodeManager] = None,
    ) -> EventEnvelope:
        """Create, sign, persist, and enqueue an event for peer broadcast."""
        nm = node_manager or NodeManager.get_instance()
        event_id = str(uuid.uuid4())
        now = time.time()
        clock = EventProtocolEngine.get_next_clock()

        # Sign canonical payload
        payload_str = json.dumps(payload, sort_keys=True)
        sign_bytes = f"{event_id}:{event_type}:{now}:{clock}:{payload_str}".encode("utf-8")
        sig = nm.keypair.sign(sign_bytes) if nm.keypair else None

        envelope = EventEnvelope(
            event_id=event_id,
            event_type=event_type,
            origin_node_id=nm.node_id,
            timestamp=now,
            device_clock=clock,
            payload=payload,
            signature=sig,
        )

        # 1. Record in immutable EventLog
        log_entry = EventLog(
            event_id=event_id,
            event_type=event_type,
            origin_node_id=nm.node_id,
            timestamp=now,
            payload=payload_str,
            version=1,
            hop_count=0,
            signature=sig,
        )
        db.add(log_entry)

        # 2. Enqueue in OutboxItem for delay-tolerant peer sync
        outbox = OutboxItem(
            event_id=event_id,
            target_node_id=target_node_id,
            status="pending",
            attempts=0,
        )
        db.add(outbox)
        db.commit()

        return envelope

    @staticmethod
    def receive_and_acknowledge(db, envelope_dict: dict, local_node_id: str) -> dict:
        """
        Ingest incoming event idempotently and return delivery ACK.
        If already processed, returns duplicate_suppressed without failing.
        """
        event_id = envelope_dict.get("event_id")
        event_type = envelope_dict.get("event_type")
        origin_node = envelope_dict.get("origin_node_id")
        timestamp = envelope_dict.get("timestamp", time.time())
        raw_payload = envelope_dict.get("payload", {})
        payload_str = json.dumps(raw_payload) if isinstance(raw_payload, dict) else str(raw_payload)

        # Check existing
        existing = db.query(EventLog).filter_by(event_id=event_id).first()
        if existing:
            return {
                "type": "EVENT_ACK",
                "ack_id": str(uuid.uuid4()),
                "event_id": event_id,
                "recipient_node_id": local_node_id,
                "status": "duplicate_suppressed",
                "timestamp": time.time(),
            }

        # Store in EventLog
        log_entry = EventLog(
            event_id=event_id,
            event_type=event_type,
            origin_node_id=origin_node,
            timestamp=timestamp,
            payload=payload_str,
            version=envelope_dict.get("version", 1),
            hop_count=envelope_dict.get("hop_count", 0),
            signature=envelope_dict.get("signature"),
        )
        db.add(log_entry)

        # Materialize domain entity in local SQLite
        try:
            data = raw_payload if isinstance(raw_payload, dict) else json.loads(payload_str)
            inc_id = data.get("incident_id")

            if event_type == "incident.created":
                raw_lat = data.get("latitude")
                raw_lon = data.get("longitude")
                lat_val = float(raw_lat) if raw_lat is not None else None
                lon_val = float(raw_lon) if raw_lon is not None else None
                acc_val = float(data.get("accuracy")) if data.get("accuracy") is not None else None
                loc_source = data.get("location_source", "unavailable" if lat_val is None else "gps")

                existing_inc = db.query(OperationalIncident).filter_by(incident_id=inc_id).first() if inc_id else None
                if existing_inc:
                    existing_inc.title = data.get("title", existing_inc.title)
                    existing_inc.category = data.get("category", existing_inc.category)
                    existing_inc.severity = data.get("severity", existing_inc.severity)
                    existing_inc.latitude = lat_val if lat_val is not None else existing_inc.latitude
                    existing_inc.longitude = lon_val if lon_val is not None else existing_inc.longitude
                    existing_inc.accuracy = acc_val if acc_val is not None else existing_inc.accuracy
                    existing_inc.location_source = loc_source
                    existing_inc.summary = data.get("summary", existing_inc.summary)
                    existing_inc.status = data.get("status", existing_inc.status)
                    if "broadcaster_name" in data:
                        existing_inc.broadcaster_name = data["broadcaster_name"]
                else:
                    db.add(
                        OperationalIncident(
                            incident_id=inc_id or str(uuid.uuid4()),
                            title=data.get("title", "Untitled Incident"),
                            category=data.get("category", "general"),
                            severity=data.get("severity", "medium"),
                            latitude=lat_val,
                            longitude=lon_val,
                            accuracy=acc_val,
                            location_source=loc_source,
                            summary=data.get("summary", ""),
                            status=data.get("status", "open"),
                            broadcaster_name=data.get("broadcaster_name", origin_node),
                        )
                    )
                attachments_list = data.get("attachments", [])
                if inc_id and attachments_list:
                    try:
                        from backend.app.models import Attachment
                    except ImportError:
                        from app.models import Attachment
                    for att_data in attachments_list:
                        att_id = att_data.get("attachment_id") or att_data.get("id")
                        sha256 = att_data.get("sha256_hash")
                        if att_id and sha256:
                            exists = db.query(Attachment).filter_by(id=att_id).first()
                            if not exists:
                                db.add(
                                    Attachment(
                                        id=att_id,
                                        incident_id=inc_id,
                                        filename=att_data.get("filename", "attachment.jpg"),
                                        mime_type=att_data.get("mime_type", "image/jpeg"),
                                        file_size=att_data.get("file_size", 0),
                                        sha256_hash=sha256,
                                        local_path="",
                                        source_node_id=att_data.get("source_node_id", origin_node),
                                        sync_status="pending",
                                    )
                                )
            elif event_type == "incident.segregated":
                cand_id = data.get("candidate_id")
                mast_id = data.get("master_id")
                if cand_id and mast_id:
                    try:
                        from backend.app.models import SegregatedCorrelation
                    except ImportError:
                        from app.models import SegregatedCorrelation
                    exists = db.query(SegregatedCorrelation).filter_by(candidate_id=cand_id, master_id=mast_id).first()
                    if not exists:
                        db.add(SegregatedCorrelation(candidate_id=cand_id, master_id=mast_id))
            elif event_type == "incident.attachment_added":
                inc_id = data.get("incident_id")
                attachments_list = data.get("attachments", [])
                if inc_id and attachments_list:
                    try:
                        from backend.app.models import Attachment
                    except ImportError:
                        from app.models import Attachment
                    for att_data in attachments_list:
                        att_id = att_data.get("attachment_id") or att_data.get("id")
                        sha256 = att_data.get("sha256_hash")
                        if att_id and sha256:
                            exists = db.query(Attachment).filter_by(id=att_id).first()
                            if not exists:
                                db.add(
                                    Attachment(
                                        id=att_id,
                                        incident_id=inc_id,
                                        filename=att_data.get("filename", "attachment.jpg"),
                                        mime_type=att_data.get("mime_type", "image/jpeg"),
                                        file_size=att_data.get("file_size", 0),
                                        sha256_hash=sha256,
                                        local_path="",
                                        source_node_id=att_data.get("source_node_id", origin_node),
                                        sync_status="pending",
                                    )
                                )
            elif event_type in ["incident.updated", "incident.merged"]:
                if inc_id:
                    existing_inc = db.query(OperationalIncident).filter_by(incident_id=inc_id).first()
                    if existing_inc:
                        if "status" in data:
                            existing_inc.status = data["status"]
                        if "severity" in data:
                            existing_inc.severity = data["severity"]
                        if "summary" in data:
                            existing_inc.summary = data["summary"]
                        if "title" in data:
                            existing_inc.title = data["title"]
                    else:
                        existing_inc = OperationalIncident(
                            incident_id=inc_id,
                            title=data.get("title", "Updated Incident"),
                            category=data.get("category", "general"),
                            severity=data.get("severity", "medium"),
                            latitude=float(data.get("latitude", 0.0)),
                            longitude=float(data.get("longitude", 0.0)),
                            summary=data.get("summary", ""),
                            status=data.get("status", "open"),
                            broadcaster_name=data.get("broadcaster_name", origin_node),
                        )
                        db.add(existing_inc)

                    if event_type == "incident.merged":
                        dup_inc_id = data.get("duplicate_incident_id")
                        if dup_inc_id:
                            dup_inc = db.query(OperationalIncident).filter_by(incident_id=dup_inc_id).first()
                            if dup_inc:
                                dup_inc.status = "merged"

                        rep_id = data.get("report_id")
                        if rep_id:
                            existing_rep = db.query(Report).filter_by(report_id=rep_id).first()
                            if existing_rep:
                                existing_rep.incident_id = inc_id
                            else:
                                db.add(
                                    Report(
                                        report_id=rep_id,
                                        incident_id=inc_id,
                                        device_id=data.get("merged_by", origin_node),
                                        user_id="commander",
                                        category=existing_inc.category if existing_inc else "general",
                                        description=data.get("description", "Merged field report"),
                                        latitude=existing_inc.latitude if existing_inc else 0.0,
                                        longitude=existing_inc.longitude if existing_inc else 0.0,
                                    )
                                )
            elif event_type == "report.created":
                rep_id = data.get("report_id")
                if not db.query(Report).filter_by(report_id=rep_id).first():
                    db.add(
                        Report(
                            report_id=rep_id or str(uuid.uuid4()),
                            incident_id=data.get("incident_id"),
                            device_id=data.get("device_id", origin_node),
                            user_id=data.get("user_id", "responder"),
                            category=data.get("category", "general"),
                            description=data.get("description", ""),
                            latitude=float(data.get("latitude", 0.0)),
                            longitude=float(data.get("longitude", 0.0)),
                        )
                    )
            elif event_type == "message.created":
                msg_id = data.get("message_id")
                if not db.query(ChatMessage).filter_by(message_id=msg_id).first():
                    db.add(
                        ChatMessage(
                            message_id=msg_id or str(uuid.uuid4()),
                            incident_id=data.get("incident_id"),
                            sender_device_id=data.get("sender_device_id", origin_node),
                            sender_user_id=data.get("sender_user_id", "responder"),
                            text=data.get("text", ""),
                        )
                    )
            elif event_type in ["resource.created", "resource.updated"]:
                res_id = data.get("resource_id")
                existing_res = db.query(ResourceRequest).filter_by(resource_id=res_id).first() if res_id else None
                if existing_res:
                    if "status" in data:
                        existing_res.status = data["status"]
                    if "quantity" in data:
                        existing_res.quantity = int(data["quantity"])
                    if "urgency" in data:
                        existing_res.urgency = data["urgency"]
                    if "incident_id" in data and data["incident_id"]:
                        existing_res.incident_id = data["incident_id"]
                else:
                    db.add(
                        ResourceRequest(
                            resource_id=res_id or str(uuid.uuid4()),
                            incident_id=data.get("incident_id"),
                            requester_id=data.get("requester_id", origin_node),
                            resource_type=data.get("resource_type", "general"),
                            quantity=int(data.get("quantity", 1)),
                            urgency=data.get("urgency", "medium"),
                            status=data.get("status", "pending"),
                        )
                    )
        except Exception as e:
            logger.debug(f"Domain materialization skipped for {event_type}: {e}")

        db.commit()

        return {
            "type": "EVENT_ACK",
            "ack_id": str(uuid.uuid4()),
            "event_id": event_id,
            "recipient_node_id": local_node_id,
            "status": "delivered",
            "timestamp": time.time(),
        }

    @staticmethod
    def process_ack(db, ack_dict: dict) -> bool:
        """Process incoming ACK from peer and transition outbox status to acknowledged."""
        event_id = ack_dict.get("event_id")
        if not event_id:
            return False

        outbox_items = db.query(OutboxItem).filter_by(event_id=event_id).all()
        if not outbox_items:
            return False

        for item in outbox_items:
            item.status = "acknowledged"
            item.last_attempt_at = None
        db.commit()
        logger.info(f"Event {event_id} delivery confirmed via ACK from {ack_dict.get('recipient_node_id')}")
        return True
