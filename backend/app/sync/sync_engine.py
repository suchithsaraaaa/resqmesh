import time
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("ResQMesh.SyncEngine")


class OutboxItem:
    """DTN Store-and-Forward Outbox record."""

    def __init__(
        self,
        item_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
        device_clock: int = 0,
        timestamp: Optional[float] = None,
    ):
        self.item_id = item_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action  # CREATE, UPDATE, DELETE
        self.payload = payload
        self.device_clock = device_clock
        self.timestamp = timestamp or time.time()
        self.status = "PENDING"  # PENDING, ACKNOWLEDGED, FAILED
        self.attempts = 0

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "payload": self.payload,
            "device_clock": self.device_clock,
            "timestamp": self.timestamp,
            "status": self.status,
            "attempts": self.attempts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OutboxItem":
        item = cls(
            item_id=data["item_id"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            action=data["action"],
            payload=data["payload"],
            device_clock=data.get("device_clock", 0),
            timestamp=data.get("timestamp"),
        )
        item.status = data.get("status", "PENDING")
        item.attempts = data.get("attempts", 0)
        return item


def resolve_lww_conflict(local_record: dict, remote_record: dict) -> Tuple[dict, str]:
    """
    Last-Writer-Wins (LWW) Conflict Resolution algorithm.
    Tie-breakers:
      1. Timestamp (newer timestamp wins)
      2. Logical device_clock (higher counter wins)
      3. Device ID lexicographical comparison (deterministic winner)

    Returns (winning_record, winner_source: "LOCAL" | "REMOTE")
    """
    local_ts = local_record.get("timestamp") or 0.0
    remote_ts = remote_record.get("timestamp") or 0.0

    if remote_ts > local_ts:
        return remote_record, "REMOTE"
    elif local_ts > remote_ts:
        return local_record, "LOCAL"

    # Tie-breaker 1: device_clock
    local_clock = local_record.get("device_clock") or 0
    remote_clock = remote_record.get("device_clock") or 0

    if remote_clock > local_clock:
        return remote_record, "REMOTE"
    elif local_clock > remote_clock:
        return local_record, "LOCAL"

    # Tie-breaker 2: device_id
    local_dev = str(local_record.get("device_id") or "")
    remote_dev = str(remote_record.get("device_id") or "")

    if remote_dev > local_dev:
        return remote_record, "REMOTE"
    else:
        return local_record, "LOCAL"


class ResQMeshSyncEngine:
    """DTN Store-and-Forward Sync Engine with Delta Sync Handshakes and LWW Conflict Resolution."""

    def __init__(self, local_device_id: str):
        self.local_device_id = local_device_id
        self.outbox: Dict[str, OutboxItem] = {}
        self.peer_sync_vector: Dict[str, float] = {}  # peer_id -> last_sync_timestamp

    def enqueue_change(
        self, item_id: str, entity_type: str, entity_id: str, action: str, payload: dict
    ) -> OutboxItem:
        """Enqueue local modification to DTN outbox."""
        item = OutboxItem(
            item_id=item_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            payload=payload,
            timestamp=time.time(),
        )
        self.outbox[item_id] = item
        logger.info(f"Enqueued DTN outbox change: {entity_type} {entity_id} ({action})")
        return item

    def generate_delta_bundle(self, since_timestamp: float) -> List[dict]:
        """Generate delta sync bundle for changes created after since_timestamp."""
        delta = []
        for item in self.outbox.values():
            if item.timestamp > since_timestamp:
                delta.append(item.to_dict())
        return delta

    def process_incoming_delta(
        self, delta_items: List[dict], local_db_records: Dict[str, dict]
    ) -> List[dict]:
        """
        Process incoming remote delta bundle against local database state using LWW.
        Returns list of applied winning updates.
        """
        applied_updates = []

        for remote_dict in delta_items:
            entity_id = remote_dict.get("entity_id")
            local_dict = local_db_records.get(entity_id)

            if not local_dict:
                # New entity -> Apply directly
                applied_updates.append(remote_dict)
            else:
                winner, source = resolve_lww_conflict(local_dict, remote_dict)
                if source == "REMOTE":
                    applied_updates.append(remote_dict)

        return applied_updates

    def process_sync_ack(self, peer_id: str, acked_item_ids: List[str], sync_timestamp: float) -> None:
        """Mark outbox items as acknowledged by peer node."""
        self.peer_sync_vector[peer_id] = sync_timestamp
        for item_id in acked_item_ids:
            if item_id in self.outbox:
                self.outbox[item_id].status = "ACKNOWLEDGED"
                del self.outbox[item_id]
                logger.info(f"DTN Outbox item {item_id} acknowledged by peer {peer_id}")
