import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional
try:
    from backend.app.network.protocol import Packet
except ImportError:
    from app.network.protocol import Packet

logger = logging.getLogger("ResQMesh.WiFiDirect")

DEFAULT_WIFI_DIRECT_PORT = 8002
WIFI_DIRECT_GO_IP = "192.168.49.1"


class WiFiDirectPeerInfo:
    """Representation of a Wi-Fi Direct (P2P) peer node."""

    def __init__(self, device_address: str, device_name: str, is_group_owner: bool = False):
        self.device_address = device_address
        self.device_name = device_name
        self.is_group_owner = is_group_owner
        self.status = "available"
        self.ip_address: Optional[str] = None


class ResQMeshWiFiDirectManager:
    """High-Throughput Wi-Fi Direct Manager for group creation, peer socket streaming, and file/media transfers."""

    def __init__(self, device_id: str, port: int = DEFAULT_WIFI_DIRECT_PORT):
        self.device_id = device_id
        self.port = port
        self.is_group_owner = False
        self.group_owner_ip: Optional[str] = None
        self.discovered_peers: Dict[str, WiFiDirectPeerInfo] = {}
        self.packet_handlers: List[Callable[[Packet, str], None]] = []

    def register_packet_handler(self, handler: Callable[[Packet, str], None]) -> None:
        self.packet_handlers.append(handler)

    def create_group(self) -> bool:
        """Promote self to Wi-Fi Direct Group Owner (GO)."""
        self.is_group_owner = True
        self.group_owner_ip = WIFI_DIRECT_GO_IP
        logger.info(f"Wi-Fi Direct Group Owner created. IP: {self.group_owner_ip}")
        return True

    def remove_group(self) -> None:
        """Teardown Wi-Fi Direct P2P Group."""
        self.is_group_owner = False
        self.group_owner_ip = None
        logger.info("Wi-Fi Direct Group removed.")

    def add_discovered_peer(
        self, device_address: str, device_name: str, is_go: bool = False
    ) -> WiFiDirectPeerInfo:
        peer = WiFiDirectPeerInfo(
            device_address=device_address, device_name=device_name, is_group_owner=is_go
        )
        self.discovered_peers[device_address] = peer
        logger.info(f"Discovered Wi-Fi Direct Peer: {device_name} ({device_address})")
        return peer

    async def send_packet_to_peer(self, peer_ip: str, packet: Packet) -> bool:
        """Send high-throughput packet payload directly over Wi-Fi Direct socket stream."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(peer_ip, self.port), timeout=5.0
            )
            payload_data = json.dumps(packet.to_dict()) + "\n"
            writer.write(payload_data.encode("utf-8"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            logger.error(f"Failed to send Wi-Fi Direct packet to {peer_ip}:{self.port} - {e}")
            return False

    def process_incoming_payload(self, raw_json: str, sender_ip: str) -> Optional[Packet]:
        try:
            data = json.loads(raw_json)
            packet = Packet.from_dict(data)
            if packet.verify_checksum():
                for handler in self.packet_handlers:
                    handler(packet, sender_ip)
                return packet
            else:
                logger.warning(f"Wi-Fi Direct checksum failure from {sender_ip}")
                return None
        except Exception as e:
            logger.error(f"Error parsing Wi-Fi Direct payload: {e}")
            return None
