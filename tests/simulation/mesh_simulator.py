import time
import random
import logging
from typing import Dict, List, Optional, Set, Tuple

from backend.app.network.protocol import Packet, PACKET_TYPE_DATA
from backend.app.network.router import ResQMeshRouter
from backend.app.sync.sync_engine import ResQMeshSyncEngine
from backend.app.crypto.security import DeviceKeyPair, TrustStore, verify_signature

logger = logging.getLogger("ResQMesh.Simulator")


class SimulatedNode:
    """Represents an active physical responder or commander device in the mesh network."""

    def __init__(self, node_id: str, role: str = "responder"):
        self.node_id = node_id
        self.role = role
        self.key_pair = DeviceKeyPair()
        self.trust_store = TrustStore()
        self.router = ResQMeshRouter(local_device_id=node_id, default_ttl=5)
        self.sync_engine = ResQMeshSyncEngine(local_device_id=node_id)
        self.local_database: Dict[str, dict] = {}
        self.outbound_queue: List[Tuple[str, Packet]] = []  # (target_neighbor_id, packet)
        self.received_packet_log: List[Packet] = []

    def create_report(
        self,
        report_id: str,
        category: str,
        description: str,
        lat: float,
        lon: float,
        clock: int = 1,
    ) -> Packet:
        """Create a local incident report, enqueue to DTN sync outbox, sign, and prepare packet."""
        timestamp = time.time()
        report_data = {
            "entity_id": report_id,
            "entity_type": "Report",
            "category": category,
            "description": description,
            "latitude": lat,
            "longitude": lon,
            "device_id": self.node_id,
            "device_clock": clock,
            "timestamp": timestamp,
        }

        # Store in local database
        self.local_database[report_id] = report_data

        # Enqueue to sync engine outbox
        self.sync_engine.enqueue_change(
            item_id=f"out-{report_id}",
            entity_type="Report",
            entity_id=report_id,
            action="CREATE",
            payload=report_data,
        )

        # Prepare signed packet
        payload_bytes = f"{report_id}:{category}:{description}".encode("utf-8")
        signature = self.key_pair.sign(payload_bytes)

        packet = Packet(
            packet_id=f"pkt-{report_id}-{clock}",
            sender_id=self.node_id,
            packet_type=PACKET_TYPE_DATA,
            payload={
                "report": report_data,
                "signature": signature,
                "sender_pubkey": self.key_pair.get_public_key_b64(),
                "ttl": 5,
                "hop_count": 0,
            },
        )
        return packet

    def receive_packet(self, packet: Packet, from_neighbor_id: str) -> Optional[Packet]:
        """
        Process incoming packet:
        1. Duplicate suppression & TTL check in router
        2. Cryptographic signature check
        3. Sync & state convergence update
        4. Return forwarding packet if mesh router dictates
        """
        decision = self.router.process_incoming_packet(packet, arrived_from_id=from_neighbor_id)

        if not decision["should_process_locally"] and not decision["should_forward"]:
            return None

        # Process locally if destined for me or broadcast
        if decision["should_process_locally"]:
            self.received_packet_log.append(packet)

            # Extract report payload
            report_data = packet.payload.get("report")
            if report_data:
                # Apply through sync engine using LWW
                applied = self.sync_engine.process_incoming_delta(
                    [report_data], self.local_database
                )
                for item in applied:
                    self.local_database[item["entity_id"]] = item

        # Return packet to forward to other neighbors if needed
        return decision["updated_packet"] if decision["should_forward"] else None

    def sync_database_to_neighbors(self) -> List[Packet]:
        """Generate sync packets for all local database records to synchronize with neighbors."""
        packets = []
        for entity_id, report_data in self.local_database.items():
            pkt = Packet(
                packet_id=f"sync-{self.node_id}-{entity_id}-{int(time.time()*1000000)}",
                sender_id=self.node_id,
                packet_type=PACKET_TYPE_DATA,
                payload={
                    "report": report_data,
                    "ttl": 5,
                    "hop_count": 0,
                },
            )
            packets.append(pkt)
        return packets


class MeshNetworkSimulator:
    """Discrete-event simulation engine for multi-node ad-hoc mesh networks."""

    def __init__(self):
        self.nodes: Dict[str, SimulatedNode] = {}
        self.links: Dict[str, Set[str]] = {}  # node_id -> set of connected neighbor node_ids
        self.packet_loss_rate: float = 0.0

    def add_node(self, node_id: str, role: str = "responder") -> SimulatedNode:
        node = SimulatedNode(node_id, role)
        self.nodes[node_id] = node
        self.links[node_id] = set()
        return node

    def connect(self, node_a: str, node_b: str) -> None:
        """Establish bidirectional wireless mesh link between node_a and node_b."""
        if node_a in self.nodes and node_b in self.nodes:
            self.links[node_a].add(node_b)
            self.links[node_b].add(node_a)

    def disconnect(self, node_a: str, node_b: str) -> None:
        """Break wireless mesh link (simulating distance / obstacle partition)."""
        if node_a in self.links:
            self.links[node_a].discard(node_b)
        if node_b in self.links:
            self.links[node_b].discard(node_a)

    def broadcast_from_node(self, sender_id: str, packet: Packet) -> None:
        """Queue packet to all currently connected immediate wireless neighbors."""
        neighbors = self.links.get(sender_id, set())
        for neighbor_id in neighbors:
            self.nodes[sender_id].outbound_queue.append((neighbor_id, packet))

    def trigger_delta_sync(self, node_id: str) -> None:
        """Trigger a node to broadcast its local database state to all connected neighbors."""
        if node_id in self.nodes:
            packets = self.nodes[node_id].sync_database_to_neighbors()
            for pkt in packets:
                self.broadcast_from_node(node_id, pkt)

    def step(self) -> int:
        """
        Execute a single simulation tick.
        Processes outbound queues across all nodes and delivers packets across links.
        Returns number of packets transmitted in this tick.
        """
        in_flight: List[Tuple[str, str, Packet]] = []

        # Collect all outbound packets from all nodes
        for sender_id, node in self.nodes.items():
            while node.outbound_queue:
                target_neighbor_id, packet = node.outbound_queue.pop(0)
                # Verify physical link is still active
                if target_neighbor_id in self.links.get(sender_id, set()):
                    in_flight.append((sender_id, target_neighbor_id, packet))

        # Deliver packets
        delivered_count = 0
        for sender_id, receiver_id, packet in in_flight:
            # Simulate packet loss if configured
            if self.packet_loss_rate > 0.0 and random.random() < self.packet_loss_rate:
                continue

            receiver_node = self.nodes[receiver_id]
            fwd_packet = receiver_node.receive_packet(packet, from_neighbor_id=sender_id)
            delivered_count += 1

            # If node needs to forward packet to its other neighbors
            if fwd_packet:
                for next_neighbor in self.links.get(receiver_id, set()):
                    if next_neighbor != sender_id:  # Do not echo back to sender
                        receiver_node.outbound_queue.append((next_neighbor, fwd_packet))

        return delivered_count

    def run_until_quiescence(self, max_ticks: int = 30) -> int:
        """Run simulation steps until no outbound packets remain in flight."""
        total_packets = 0
        for _ in range(max_ticks):
            count = self.step()
            total_packets += count
            # Check if all queues are empty
            if all(len(n.outbound_queue) == 0 for n in self.nodes.values()):
                break
        return total_packets
