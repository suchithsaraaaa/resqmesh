import time
import logging
from typing import Dict, List, Optional, Set
try:
    from backend.app.network.protocol import Packet
except ImportError:
    from app.network.protocol import Packet

logger = logging.getLogger("ResQMesh.Router")

DEFAULT_INITIAL_TTL = 5
SEEN_CACHE_EXPIRY_SECONDS = 300  # 5 minutes


class SeenPacketCache:
    """Bounded cache for suppressing duplicate mesh packets."""

    def __init__(self, expiry_seconds: float = SEEN_CACHE_EXPIRY_SECONDS):
        self.expiry_seconds = expiry_seconds
        self._seen: Dict[str, float] = {}

    def is_seen(self, packet_id: str) -> bool:
        self._cleanup()
        return packet_id in self._seen

    def mark_seen(self, packet_id: str) -> None:
        self._cleanup()
        self._seen[packet_id] = time.time()

    def _cleanup(self) -> None:
        now = time.time()
        expired = [pid for pid, ts in self._seen.items() if now - ts > self.expiry_seconds]
        for pid in expired:
            del self._seen[pid]


class MeshRoute:
    """Representation of a route entry to a target destination node."""

    def __init__(
        self,
        dest_id: str,
        next_hop_id: str,
        hop_count: int,
        latency_ms: float = 0.0,
        relay_path: Optional[List[str]] = None,
    ):
        self.dest_id = dest_id
        self.next_hop_id = next_hop_id
        self.hop_count = hop_count
        self.latency_ms = latency_ms
        self.relay_path = relay_path or [next_hop_id]
        self.last_updated = time.time()

    def to_dict(self) -> dict:
        quality = "EXCELLENT" if self.latency_ms < 30 and self.hop_count <= 1 else ("GOOD" if self.hop_count <= 2 else "MULTI_HOP")
        return {
            "dest_id": self.dest_id,
            "next_hop_id": self.next_hop_id,
            "hop_count": self.hop_count,
            "latency_ms": round(self.latency_ms, 1),
            "relay_path": self.relay_path,
            "link_quality": quality,
            "last_updated": self.last_updated,
            "age_seconds": round(time.time() - self.last_updated, 1),
        }


class ResQMeshRouter:
    """Multi-hop ad-hoc mesh router with TTL hop counts, duplicate suppression, and forwarding decisions."""

    _instance: Optional["ResQMeshRouter"] = None

    def __init__(self, local_device_id: str, default_ttl: int = DEFAULT_INITIAL_TTL):
        self.local_device_id = local_device_id
        self.default_ttl = default_ttl
        self.seen_cache = SeenPacketCache()
        self.routing_table: Dict[str, MeshRoute] = {}

    @classmethod
    def get_instance(cls, local_device_id: Optional[str] = None) -> "ResQMeshRouter":
        if cls._instance is None:
            try:
                from backend.app.services.node_manager import NodeManager
            except ImportError:
                from app.services.node_manager import NodeManager
            dev_id = local_device_id or NodeManager.get_instance().node_id or "node-local"
            cls._instance = ResQMeshRouter(local_device_id=dev_id)
        return cls._instance

    def update_route(
        self,
        dest_id: str,
        next_hop_id: str,
        hop_count: int,
        latency_ms: float = 0.0,
        relay_path: Optional[List[str]] = None,
    ) -> None:
        """Update routing table entry if shorter or newer route discovered."""
        if dest_id == self.local_device_id:
            return

        existing = self.routing_table.get(dest_id)
        if not existing or hop_count <= existing.hop_count or (time.time() - existing.last_updated > 60):
            self.routing_table[dest_id] = MeshRoute(
                dest_id=dest_id,
                next_hop_id=next_hop_id,
                hop_count=hop_count,
                latency_ms=latency_ms or (existing.latency_ms if existing else 0.0),
                relay_path=relay_path or ([next_hop_id] if next_hop_id != dest_id else [dest_id]),
            )

    def remove_route(self, dest_id: str) -> None:
        """Explicitly remove a route when a node departs the mesh."""
        if dest_id in self.routing_table:
            del self.routing_table[dest_id]

    def prune_stale_routes(self, active_peer_ids: Set[str], max_age_seconds: float = 45.0) -> None:
        """Prune 1-hop direct routes no longer in active peers, and expired multi-hop routes."""
        now = time.time()
        to_delete = []
        for dest_id, route in self.routing_table.items():
            if route.hop_count == 1 and dest_id not in active_peer_ids:
                to_delete.append(dest_id)
            elif route.hop_count > 1 and (now - route.last_updated > 120.0):
                to_delete.append(dest_id)
        for did in to_delete:
            del self.routing_table[did]

    def get_routes(self) -> List[dict]:
        """Return list of active routes sorted by hop count."""
        now = time.time()
        expired = [did for did, r in self.routing_table.items() if now - r.last_updated > 600]
        for did in expired:
            del self.routing_table[did]

        return [r.to_dict() for r in sorted(self.routing_table.values(), key=lambda x: (x.hop_count, x.latency_ms))]

    def get_topology(self) -> dict:
        """Return graph representation of multi-hop mesh topology."""
        try:
            from backend.app.services.node_manager import NodeManager
        except ImportError:
            from app.services.node_manager import NodeManager

        nm = NodeManager.get_instance()
        direct_peers = nm.get_active_peers()
        active_peer_ids = {p.get("node_id") for p in direct_peers if p.get("node_id")}

        # Prune direct routes that are no longer in active peers
        self.prune_stale_routes(active_peer_ids)

        # Seed/update routes with active direct peers (hop_count: 1)
        for p in direct_peers:
            pid = p.get("node_id")
            if pid:
                self.update_route(
                    dest_id=pid,
                    next_hop_id=pid,
                    hop_count=1,
                    latency_ms=float(p.get("latency_ms", 12.0) or 12.0),
                    relay_path=[pid],
                )

        routes = self.get_routes()
        nodes = [
            {
                "id": nm.node_id,
                "name": nm.node_name or "Local Commander",
                "role": nm.role or "commander",
                "is_local": True,
                "hop_count": 0,
                "status": "online",
            }
        ]

        links = []
        seen_node_ids = {nm.node_id}

        for r in routes:
            did = r["dest_id"]
            if did not in seen_node_ids:
                seen_node_ids.add(did)
                matched_name = next((p.get("name") for p in direct_peers if p.get("node_id") == did), None)
                nodes.append({
                    "id": did,
                    "name": matched_name or f"Node-{did[-4:].upper()}",
                    "role": "responder",
                    "is_local": False,
                    "hop_count": r["hop_count"],
                    "next_hop": r["next_hop_id"],
                    "latency_ms": r["latency_ms"],
                    "link_quality": r["link_quality"],
                    "status": "online" if r["age_seconds"] < 45 else "degraded",
                })

            if r["hop_count"] == 1:
                links.append({
                    "source": nm.node_id,
                    "target": did,
                    "hops": 1,
                    "latency_ms": r["latency_ms"],
                    "quality": r["link_quality"],
                    "direct": True,
                })
            else:
                links.append({
                    "source": r["next_hop_id"],
                    "target": did,
                    "hops": r["hop_count"],
                    "latency_ms": r["latency_ms"],
                    "quality": r["link_quality"],
                    "direct": False,
                })

        return {
            "local_node_id": nm.node_id,
            "total_nodes": len(nodes),
            "direct_peer_count": len([n for n in nodes if n.get("hop_count") == 1]),
            "relayed_node_count": len([n for n in nodes if n.get("hop_count", 0) > 1]),
            "nodes": nodes,
            "links": links,
            "routes": routes,
        }

    def process_incoming_packet(self, packet: Packet, arrived_from_id: str) -> Dict[str, any]:
        """
        Process incoming packet for local consumption and forwarding decision.
        Returns dict containing:
          - 'should_process_locally': bool
          - 'should_forward': bool
          - 'updated_packet': Packet or None
          - 'reason': str
        """
        packet_id = packet.packet_id

        # 1. Duplicate Suppression Check
        if self.seen_cache.is_seen(packet_id):
            return {
                "should_process_locally": False,
                "should_forward": False,
                "updated_packet": None,
                "reason": "DUPLICATE_PACKET",
            }

        # Mark packet as seen
        self.seen_cache.mark_seen(packet_id)

        # Update reverse route back to sender
        sender_id = packet.sender_id
        if sender_id != self.local_device_id:
            self.update_route(
                dest_id=sender_id,
                next_hop_id=arrived_from_id,
                hop_count=packet.frag_idx + 1 if hasattr(packet, "frag_idx") else 1,
            )

        # Extract target destination from payload if unicast
        target_dest = packet.payload.get("target_device_id")
        is_for_me = (target_dest is None) or (target_dest == self.local_device_id)

        # 2. TTL Check & Hop Count Increment
        current_ttl = packet.payload.get("ttl", self.default_ttl)
        current_hops = packet.payload.get("hop_count", 0)

        if current_ttl <= 1:
            # TTL expired -> Do not forward further
            return {
                "should_process_locally": is_for_me,
                "should_forward": False,
                "updated_packet": None,
                "reason": "TTL_EXPIRED" if not is_for_me else "PROCESSED_LOCALLY_TTL_EXPIRED",
            }

        # 3. Prepare Packet for Forwarding (Decrement TTL, Increment Hop Count)
        forward_payload = dict(packet.payload)
        forward_payload["ttl"] = current_ttl - 1
        forward_payload["hop_count"] = current_hops + 1

        forward_packet = Packet(
            packet_id=packet.packet_id,
            sender_id=packet.sender_id,
            packet_type=packet.packet_type,
            seq_num=packet.seq_num,
            total_frags=packet.total_frags,
            frag_idx=packet.frag_idx,
            payload=forward_payload,
            timestamp=packet.timestamp,
        )

        return {
            "should_process_locally": is_for_me,
            "should_forward": True,
            "updated_packet": forward_packet,
            "reason": "OK_FORWARD",
        }
