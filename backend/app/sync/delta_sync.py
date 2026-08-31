import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

try:
    from backend.app.models import EventLog, SyncVector, OperationalIncident, Report, OutboxItem
    from backend.app.network.event_protocol import EventProtocolEngine
    from backend.app.sync.sync_engine import resolve_lww_conflict
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.models import EventLog, SyncVector, OperationalIncident, Report, OutboxItem
    from app.network.event_protocol import EventProtocolEngine
    from app.sync.sync_engine import resolve_lww_conflict
    from app.services.node_manager import NodeManager

logger = logging.getLogger("ResQMesh.DeltaSync")


class DeltaSyncEngine:
    """Computes event deltas from version vectors and resolves conflicts with LWW."""

    @staticmethod
    def get_local_vector(db) -> Dict[str, dict]:
        """
        Compute latest event timestamp and clock counter for all known origin nodes.
        Returns: { node_id: { "last_timestamp": 1724..., "last_clock": 5 } }
        """
        vector_map: Dict[str, dict] = {}
        # Fetch all distinct events
        logs = db.query(EventLog).all()
        for log in logs:
            origin = log.origin_node_id
            if origin not in vector_map:
                vector_map[origin] = {
                    "last_timestamp": log.timestamp,
                    "last_clock": 1,
                    "last_event_id": log.event_id,
                }
            else:
                if log.timestamp > vector_map[origin]["last_timestamp"]:
                    vector_map[origin]["last_timestamp"] = log.timestamp
                    vector_map[origin]["last_event_id"] = log.event_id
                    vector_map[origin]["last_clock"] += 1

        return vector_map

    @staticmethod
    def calculate_missing_events(db, remote_vector: Dict[str, dict]) -> List[dict]:
        """
        Find events in local EventLog that remote peer has not yet received.
        """
        missing_events = []
        all_local_events = db.query(EventLog).order_by(EventLog.timestamp.asc()).all()

        for ev in all_local_events:
            origin = ev.origin_node_id
            remote_info = remote_vector.get(origin)

            if not remote_info:
                # Remote has never heard from this origin node
                missing_events.append(ev)
            else:
                remote_ts = remote_info.get("last_timestamp", 0.0)
                if ev.timestamp > remote_ts + 0.0001:
                    missing_events.append(ev)

        # Convert to wire format
        result = []
        for ev in missing_events:
            try:
                payload_data = json.loads(ev.payload)
            except Exception:
                payload_data = ev.payload

            result.append(
                {
                    "event_id": ev.event_id,
                    "event_type": ev.event_type,
                    "origin_node_id": ev.origin_node_id,
                    "timestamp": ev.timestamp,
                    "version": ev.version,
                    "hop_count": ev.hop_count,
                    "signature": ev.signature,
                    "payload": payload_data,
                }
            )
        return result

    @staticmethod
    def apply_delta_events(db, delta_events: List[dict], local_node_id: str) -> dict:
        """
        Idempotently apply incoming delta events using EventProtocolEngine and LWW consensus.
        """
        applied = 0
        duplicates = 0

        for ev in delta_events:
            event_type = ev.get("event_type")
            event_id = ev.get("event_id")

            # Handle Incident Update Conflict Resolution (LWW)
            if event_type == "incident.updated":
                payload = ev.get("payload", {})
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        pass

                inc_id = payload.get("incident_id")
                if inc_id:
                    existing_inc = db.query(OperationalIncident).filter_by(incident_id=inc_id).first()
                    if existing_inc:
                        local_dict = {
                            "incident_id": existing_inc.incident_id,
                            "timestamp": existing_inc.updated_at.timestamp() if existing_inc.updated_at else 0.0,
                            "device_id": local_node_id,
                            "status": existing_inc.status,
                            "severity": existing_inc.severity,
                        }
                        remote_dict = {
                            "incident_id": inc_id,
                            "timestamp": ev.get("timestamp", 0.0),
                            "device_id": ev.get("origin_node_id"),
                            "status": payload.get("status", existing_inc.status),
                            "severity": payload.get("severity", existing_inc.severity),
                        }

                        winner, source = resolve_lww_conflict(local_dict, remote_dict)
                        if source == "REMOTE":
                            existing_inc.status = remote_dict["status"]
                            existing_inc.severity = remote_dict["severity"]
                            if "title" in payload:
                                existing_inc.title = payload["title"]
                            if "summary" in payload:
                                existing_inc.summary = payload["summary"]
                            db.commit()

            # Record event through protocol engine
            ack = EventProtocolEngine.receive_and_acknowledge(db, ev, local_node_id)
            if ack.get("status") == "delivered":
                applied += 1
            else:
                duplicates += 1

            # Update SyncVector
            origin = ev.get("origin_node_id")
            if origin:
                sv = db.query(SyncVector).filter_by(peer_node_id=origin).first()
                if sv:
                    if ev.get("timestamp", 0) > sv.last_timestamp:
                        sv.last_timestamp = ev.get("timestamp", 0)
                        sv.last_event_id = event_id
                        sv.last_clock += 1
                else:
                    db.add(
                        SyncVector(
                            peer_node_id=origin,
                            last_event_id=event_id,
                            last_timestamp=ev.get("timestamp", 0.0),
                            last_clock=1,
                        )
                    )
                db.commit()

        return {"applied": applied, "duplicates": duplicates, "total": len(delta_events)}

    @staticmethod
    def sync_with_peer_url(peer_url: str, db, local_node_id: str) -> dict:
        """Execute bidirectional delta sync handshake with a remote peer."""
        local_vector = DeltaSyncEngine.get_local_vector(db)
        sync_req_url = f"{peer_url.rstrip('/')}/sync/vector"

        data = json.dumps({"sender_node_id": local_node_id, "vector": local_vector}).encode("utf-8")
        req = urllib.request.Request(
            sync_req_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    delta_events = body.get("missing_events", [])
                    result = DeltaSyncEngine.apply_delta_events(db, delta_events, local_node_id)

                    # 2-WAY HANDSHAKE: Send verification ACK back to peer so its outbox transitions to ACKed
                    if delta_events:
                        ack_url = f"{peer_url.rstrip('/')}/sync/ack"
                        ack_ids = [ev.get("event_id") for ev in delta_events if ev.get("event_id")]
                        if ack_ids:
                            try:
                                ack_req = urllib.request.Request(
                                    ack_url,
                                    data=json.dumps({"sender_node_id": local_node_id, "acknowledged_event_ids": ack_ids}).encode("utf-8"),
                                    headers={"Content-Type": "application/json"},
                                    method="POST",
                                )
                                urllib.request.urlopen(ack_req, timeout=3.0)
                            except Exception as e:
                                logger.debug(f"2-way sync ACK to {peer_url} failed: {e}")

                    # RECONCILE: Check peer's local_vector to acknowledge local outbox items
                    peer_vector = body.get("local_vector", {})
                    if peer_vector and local_node_id in peer_vector:
                        last_confirmed_ts = peer_vector[local_node_id].get("last_timestamp", 0.0)
                        if last_confirmed_ts > 0:
                            pending_items = db.query(OutboxItem).filter_by(status="pending").all()
                            for item in pending_items:
                                ev_log = db.query(EventLog).filter_by(event_id=item.event_id).first()
                                if ev_log and ev_log.timestamp <= last_confirmed_ts + 0.001:
                                    item.status = "acknowledged"
                            db.commit()

                    # Out-of-band P2P attachment binary synchronization
                    try:
                        try:
                            from backend.app.sync.attachment_sync import AttachmentSyncManager
                        except ImportError:
                            from app.sync.attachment_sync import AttachmentSyncManager
                        att_result = AttachmentSyncManager.sync_pending_attachments(peer_url, db)
                        if att_result.get("synced", 0) > 0 or att_result.get("deduplicated", 0) > 0:
                            logger.info(f"Attachment sync with {peer_url}: {att_result}")
                    except Exception as att_err:
                        logger.debug(f"Attachment sync with {peer_url} failed: {att_err}")

                    logger.info(
                        f"Delta sync with {peer_url} complete: applied {result['applied']}, duplicates {result['duplicates']}"
                    )
                    return result
        except Exception as e:
            logger.debug(f"Delta sync failed with {peer_url}: {e}")

        return {"status": "failed"}
