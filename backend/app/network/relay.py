import time
import logging
import threading
from typing import Dict, List, Optional

try:
    from backend.app.network.router import SeenPacketCache
    from backend.app.network.transport import PeerTransportPool
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.network.router import SeenPacketCache
    from app.network.transport import PeerTransportPool
    from app.services.node_manager import NodeManager

logger = logging.getLogger("ResQMesh.Relay")

DEFAULT_TTL = 5


class MeshRelayManager:
    """Manages multi-hop event forwarding, TTL decrementing, and broadcast storm suppression."""

    _instance: Optional["MeshRelayManager"] = None

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or NodeManager.get_instance()
        self.seen_cache = SeenPacketCache(expiry_seconds=600.0)  # 10 minute LRU cache

    @classmethod
    def get_instance(cls) -> "MeshRelayManager":
        if cls._instance is None:
            cls._instance = MeshRelayManager()
        return cls._instance

    def handle_and_relay_event(self, event_dict: dict, incoming_sender_id: str) -> dict:
        """
        Evaluate an event envelope for multi-hop relay forwarding.
        1. If already seen -> drop.
        2. If TTL <= 1 -> drop.
        3. Else decrement TTL, increment hop count, and forward to adjacent peers.
        """
        event_id = event_dict.get("event_id")
        if not event_id:
            return {"relayed": False, "reason": "MISSING_EVENT_ID"}

        # 1. Deduplication loop suppression
        if self.seen_cache.is_seen(event_id):
            logger.debug(f"Relay dropping duplicate event {event_id}")
            return {"relayed": False, "reason": "DUPLICATE_SUPPRESSED"}

        # Mark seen
        self.seen_cache.mark_seen(event_id)

        # 2. TTL & Hop limit check
        ttl = int(event_dict.get("ttl", DEFAULT_TTL))
        hop_count = int(event_dict.get("hop_count", 0))

        if ttl <= 1:
            logger.info(f"Event {event_id} TTL expired ({ttl}). Dropping relay forwarding.")
            return {"relayed": False, "reason": "TTL_EXPIRED"}

        # 3. Create forwarded envelope
        forwarded_envelope = dict(event_dict)
        forwarded_envelope["ttl"] = ttl - 1
        forwarded_envelope["hop_count"] = hop_count + 1

        # 4. Asynchronously broadcast to all active peers except the sender
        relay_thread = threading.Thread(
            target=self._broadcast_to_adjacent_peers,
            args=(forwarded_envelope, incoming_sender_id),
            daemon=True,
            name=f"Relay-{event_id[:8]}",
        )
        relay_thread.start()

        return {
            "relayed": True,
            "new_ttl": ttl - 1,
            "new_hop_count": hop_count + 1,
        }

    def _broadcast_to_adjacent_peers(self, envelope: dict, incoming_sender_id: str) -> None:
        """Forward envelope to all adjacent peers excluding the incoming sender."""
        pool = PeerTransportPool.get_instance()
        nm = NodeManager.get_instance()
        active_peers = nm.get_active_peers()

        relayed_peers = []
        for peer in active_peers:
            peer_id = peer.get("node_id")
            if not peer_id or peer_id == nm.node_id or peer_id == incoming_sender_id:
                continue

            conn = pool.connections.get(peer_id)
            if not conn:
                pool.connect_and_authenticate(peer)
                conn = pool.connections.get(peer_id)

            if conn:
                try:
                    if conn.post_event(envelope):
                        relayed_peers.append(peer_id)
                except Exception as e:
                    logger.debug(f"Relay error sending to {peer_id}: {e}")

        if relayed_peers:
            logger.info(
                f"Multi-hop relayed event {envelope.get('event_id')} "
                f"(hops: {envelope.get('hop_count')}, ttl: {envelope.get('ttl')}) to peers: {relayed_peers}"
            )
