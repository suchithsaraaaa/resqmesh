import json
import logging
import time
from typing import Callable, Dict, List, Optional
try:
    from backend.app.network.protocol import Packet
except ImportError:
    from app.network.protocol import Packet

logger = logging.getLogger("ResQMesh.BLE")

RESQMESH_BLE_SERVICE_UUID = "0000fd00-0000-1000-8000-00805f9b34fb"
RESQMESH_BLE_TX_CHARACTERISTIC_UUID = "0000fd01-0000-1000-8000-00805f9b34fb"
RESQMESH_BLE_RX_CHARACTERISTIC_UUID = "0000fd02-0000-1000-8000-00805f9b34fb"


class BLEPeerDevice:
    """Representation of a discovered BLE peer node."""

    def __init__(self, device_id: str, address: str, rssi: int = -60):
        self.device_id = device_id
        self.address = address
        self.rssi = rssi
        self.last_seen = time.time()
        self.connected = False


class ResQMeshBLEManager:
    """Manager for BLE advertising, scanning, GATT service connection, and payload chunking."""

    def __init__(self, device_id: str, mtu_size: int = 512):
        self.device_id = device_id
        self.mtu_size = mtu_size
        self.is_advertising = False
        self.is_scanning = False
        self.discovered_peers: Dict[str, BLEPeerDevice] = {}
        self.packet_handlers: List[Callable[[Packet, str], None]] = []

    def register_packet_handler(self, handler: Callable[[Packet, str], None]) -> None:
        self.packet_handlers.append(handler)

    def start_advertising(self) -> bool:
        self.is_advertising = True
        logger.info(f"BLE advertising started for device {self.device_id}")
        return True

    def stop_advertising(self) -> None:
        self.is_advertising = False
        logger.info("BLE advertising stopped")

    def start_scanning(self) -> bool:
        self.is_scanning = True
        logger.info("BLE scanning started")
        return True

    def stop_scanning(self) -> None:
        self.is_scanning = False
        logger.info("BLE scanning stopped")

    def handle_discovered_peer(self, device_id: str, address: str, rssi: int) -> BLEPeerDevice:
        peer = BLEPeerDevice(device_id=device_id, address=address, rssi=rssi)
        self.discovered_peers[device_id] = peer
        logger.info(f"Discovered BLE peer: {device_id} ({address}) RSSI: {rssi}dBm")
        return peer

    def chunk_payload(self, data: str, max_chunk_size: Optional[int] = None) -> List[str]:
        chunk_size = max_chunk_size or (self.mtu_size - 20)
        return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]

    def reassemble_chunks(self, chunks: List[str]) -> str:
        return "".join(chunks)

    def process_incoming_raw_payload(self, raw_data: str, sender_id: str) -> Optional[Packet]:
        try:
            payload_dict = json.loads(raw_data)
            packet = Packet.from_dict(payload_dict)
            if packet.verify_checksum():
                for handler in self.packet_handlers:
                    handler(packet, sender_id)
                return packet
            else:
                logger.warning(f"BLE packet checksum failure from {sender_id}")
                return None
        except Exception as e:
            logger.error(f"Error parsing incoming BLE raw payload: {e}")
            return None
