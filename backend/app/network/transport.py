import os
import json
import time
import uuid
import secrets
import logging
import threading
from typing import Dict, Optional, Tuple, List
import urllib.request
import urllib.error

try:
    from backend.app.crypto.security import DeviceKeyPair, verify_signature
    from backend.app.network.protocol import Packet, PacketFramingParser, PACKET_TYPE_DATA, PACKET_TYPE_ACK
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.crypto.security import DeviceKeyPair, verify_signature
    from app.network.protocol import Packet, PacketFramingParser, PACKET_TYPE_DATA, PACKET_TYPE_ACK
    from app.services.node_manager import NodeManager

logger = logging.getLogger("ResQMesh.Transport")

HANDSHAKE_SYN = "HANDSHAKE_SYN"
HANDSHAKE_ACK = "HANDSHAKE_ACK"


class HandshakeManager:
    """Handles cryptographic node-to-node challenge-response mutual authentication."""

    @staticmethod
    def create_syn(local_node_id: str, role: str, keypair: DeviceKeyPair) -> dict:
        """Create signed SYN challenge packet."""
        nonce = secrets.token_hex(16)
        timestamp = time.time()
        # Challenge text to sign
        challenge = f"{local_node_id}:{nonce}:{timestamp}".encode("utf-8")
        signature = keypair.sign(challenge)

        return {
            "type": HANDSHAKE_SYN,
            "node_id": local_node_id,
            "role": role,
            "public_key": keypair.get_public_key_b64(),
            "nonce": nonce,
            "timestamp": timestamp,
            "signature": signature,
        }

    @staticmethod
    def verify_syn_and_create_ack(
        syn_payload: dict, local_node_id: str, keypair: DeviceKeyPair
    ) -> Tuple[bool, Optional[dict]]:
        """Verify remote node's SYN challenge and produce signed ACK response."""
        try:
            remote_node_id = syn_payload.get("node_id")
            remote_pub_key = syn_payload.get("public_key")
            nonce = syn_payload.get("nonce")
            timestamp = syn_payload.get("timestamp")
            sig = syn_payload.get("signature")

            if not all([remote_node_id, remote_pub_key, nonce, timestamp, sig]):
                return False, None

            # Verify Ed25519 signature of the remote challenge
            challenge = f"{remote_node_id}:{nonce}:{timestamp}".encode("utf-8")
            if not verify_signature(remote_pub_key, challenge, sig):
                logger.warning(f"Handshake SYN signature verification failed for {remote_node_id}")
                return False, None

            # Create ACK signing remote nonce + local node id
            ack_challenge = f"{local_node_id}:{nonce}".encode("utf-8")
            ack_sig = keypair.sign(ack_challenge)

            ack_payload = {
                "type": HANDSHAKE_ACK,
                "node_id": local_node_id,
                "public_key": keypair.get_public_key_b64(),
                "echo_nonce": nonce,
                "signature": ack_sig,
            }
            return True, ack_payload
        except Exception as e:
            logger.error(f"Error validating handshake SYN: {e}")
            return False, None

    @staticmethod
    def verify_ack(ack_payload: dict, original_nonce: str) -> bool:
        """Verify remote node's signed response to our original nonce."""
        try:
            remote_node_id = ack_payload.get("node_id")
            remote_pub_key = ack_payload.get("public_key")
            echo_nonce = ack_payload.get("echo_nonce")
            sig = ack_payload.get("signature")

            if echo_nonce != original_nonce:
                return False

            ack_challenge = f"{remote_node_id}:{echo_nonce}".encode("utf-8")
            return verify_signature(remote_pub_key, ack_challenge, sig)
        except Exception as e:
            logger.error(f"Error verifying handshake ACK: {e}")
            return False


class PeerConnection:
    """Manages connection state and HTTP/TCP framing transport to a single remote peer."""

    def __init__(self, node_id: str, ip: str, port: int, role: str = "responder"):
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.role = role
        self.state = "DISCONNECTED"  # DISCONNECTED, CONNECTING, AUTHENTICATED, FAILED
        self.public_key: Optional[str] = None
        self.last_contact = time.time()
        self.latency_ms = 0.0

    def get_base_url(self) -> str:
        return f"http://{self.ip}:{self.port}"

    def send_handshake_syn(self, syn_payload: dict, timeout: float = 3.0) -> Tuple[bool, Optional[dict]]:
        """Send handshake SYN to remote peer /api/handshake endpoint."""
        url = f"{self.get_base_url()}/handshake"
        data = json.dumps(syn_payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            start = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode("utf-8"))
                    self.latency_ms = round((time.time() - start) * 1000, 1)
                    return True, resp_data
        except Exception as e:
            logger.debug(f"Handshake request to {self.node_id} ({url}) failed: {e}")
            self.state = "FAILED"

        return False, None

    def post_event(self, event_dict: dict, timeout: float = 4.0) -> bool:
        """Send an event packet to the peer's /events/ingest endpoint."""
        url = f"{self.get_base_url()}/events/ingest"
        data = json.dumps(event_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"Failed to post event to peer {self.node_id}: {e}")
            return False


class PeerTransportPool:
    """Maintains active authenticated peer connections across the local network."""

    _instance: Optional["PeerTransportPool"] = None

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or NodeManager.get_instance()
        self.connections: Dict[str, PeerConnection] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "PeerTransportPool":
        if cls._instance is None:
            cls._instance = PeerTransportPool()
        return cls._instance

    def connect_and_authenticate(self, peer_info: dict) -> bool:
        """Establish connection and execute mutual Ed25519 handshake."""
        peer_id = peer_info.get("node_id")
        ip = peer_info.get("ip_address")
        port = peer_info.get("api_port", 8000)
        role = peer_info.get("role", "responder")

        if not peer_id or not ip or peer_id == self.node_manager.node_id:
            return False

        with self._lock:
            conn = self.connections.get(peer_id)
            if not conn:
                conn = PeerConnection(peer_id, ip, port, role)
                self.connections[peer_id] = conn
            else:
                conn.ip = ip
                conn.port = port

        # Execute Handshake SYN -> ACK
        if not self.node_manager.keypair:
            self.node_manager.keypair = DeviceKeyPair()

        syn = HandshakeManager.create_syn(
            local_node_id=self.node_manager.node_id,
            role=self.node_manager.role,
            keypair=self.node_manager.keypair,
        )

        success, ack = conn.send_handshake_syn(syn)
        if success and ack:
            if HandshakeManager.verify_ack(ack, syn["nonce"]):
                conn.state = "AUTHENTICATED"
                conn.public_key = ack.get("public_key")
                conn.last_contact = time.time()
                logger.info(f"Mutual Ed25519 Handshake SUCCESS with peer {peer_id} [{role}]")
                return True

        conn.state = "FAILED"
        return False

    def broadcast_event(self, event_dict: dict) -> int:
        """Broadcast an event to all currently authenticated peers."""
        success_count = 0
        with self._lock:
            active_conns = [c for c in self.connections.values() if c.state == "AUTHENTICATED"]

        for conn in active_conns:
            if conn.post_event(event_dict):
                success_count += 1
                conn.last_contact = time.time()

        return success_count

    def get_authenticated_peer_ids(self) -> List[str]:
        with self._lock:
            return [cid for cid, c in self.connections.items() if c.state == "AUTHENTICATED"]
