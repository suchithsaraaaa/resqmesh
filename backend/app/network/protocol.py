import json
import zlib
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("ResQMesh.Protocol")

PACKET_TYPE_DATA = "DATA"
PACKET_TYPE_ACK = "ACK"
PACKET_TYPE_HEARTBEAT = "HEARTBEAT"


def compute_checksum(payload_bytes: bytes) -> str:
    """Compute CRC32 checksum hex string for data integrity verification."""
    return f"{zlib.crc32(payload_bytes) & 0xffffffff:08x}"


class Packet:
    """Transport-agnostic packet envelope with sequence numbering and checksums."""

    def __init__(
        self,
        packet_id: str,
        sender_id: str,
        packet_type: str = PACKET_TYPE_DATA,
        seq_num: int = 1,
        total_frags: int = 1,
        frag_idx: int = 0,
        payload: Optional[dict] = None,
        checksum: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        self.packet_id = packet_id
        self.sender_id = sender_id
        self.packet_type = packet_type
        self.seq_num = seq_num
        self.total_frags = total_frags
        self.frag_idx = frag_idx
        self.payload = payload or {}
        self.timestamp = timestamp or time.time()

        if checksum:
            self.checksum = checksum
        else:
            self.checksum = self._generate_checksum()

    def _generate_checksum(self) -> str:
        data_str = json.dumps(self.payload, sort_keys=True)
        return compute_checksum(data_str.encode("utf-8"))

    def verify_checksum(self) -> bool:
        return self.checksum == self._generate_checksum()

    def to_dict(self) -> dict:
        return {
            "packet_id": self.packet_id,
            "sender_id": self.sender_id,
            "packet_type": self.packet_type,
            "seq_num": self.seq_num,
            "total_frags": self.total_frags,
            "frag_idx": self.frag_idx,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Packet":
        pkt = cls(
            packet_id=data["packet_id"],
            sender_id=data["sender_id"],
            packet_type=data.get("packet_type", PACKET_TYPE_DATA),
            seq_num=data.get("seq_num", 1),
            total_frags=data.get("total_frags", 1),
            frag_idx=data.get("frag_idx", 0),
            payload=data.get("payload", {}),
            checksum=data.get("checksum"),
            timestamp=data.get("timestamp"),
        )
        return pkt


class PacketFramingParser:
    """Encodes packets into length-prefixed bytes streams and decodes stream chunks."""

    @staticmethod
    def encode_frame(packet: Packet) -> bytes:
        payload_bytes = json.dumps(packet.to_dict()).encode("utf-8")
        length = len(payload_bytes)
        # 4-byte big-endian header for frame length + payload
        return length.to_bytes(4, byteorder="big") + payload_bytes

    def __init__(self):
        self._buffer = bytearray()

    def feed_bytes(self, chunk: bytes) -> List[Packet]:
        """Feed bytes chunk and extract complete framed packets."""
        self._buffer.extend(chunk)
        packets = []

        while len(self._buffer) >= 4:
            frame_len = int.from_bytes(self._buffer[:4], byteorder="big")
            if len(self._buffer) < 4 + frame_len:
                break  # Wait for full payload

            payload_bytes = bytes(self._buffer[4 : 4 + frame_len])
            del self._buffer[: 4 + frame_len]

            try:
                data = json.loads(payload_bytes.decode("utf-8"))
                pkt = Packet.from_dict(data)
                if pkt.verify_checksum():
                    packets.append(pkt)
                else:
                    logger.warning(f"Checksum mismatch for packet {pkt.packet_id}, dropping.")
            except Exception as e:
                logger.error(f"Error parsing packet payload frame: {e}")

        return packets


class ACKTracker:
    """Manages pending unacknowledged packets and retransmission tracking."""

    def __init__(self, sender_id: str, timeout_seconds: float = 5.0, max_retries: int = 3):
        self.sender_id = sender_id
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.seq_counter = 0
        self.pending_acks: Dict[str, dict] = {}

    def get_next_seq_num(self) -> int:
        self.seq_counter += 1
        return self.seq_counter

    def track_packet(self, packet: Packet) -> None:
        if packet.packet_type == PACKET_TYPE_DATA:
            self.pending_acks[packet.packet_id] = {
                "packet": packet,
                "sent_at": time.time(),
                "retries": 0,
            }

    def process_ack(self, ack_packet: Packet) -> Optional[str]:
        if ack_packet.packet_type == PACKET_TYPE_ACK:
            acked_id = ack_packet.payload.get("acked_packet_id")
            if acked_id in self.pending_acks:
                del self.pending_acks[acked_id]
                logger.info(f"Received ACK for packet: {acked_id}")
                return acked_id
        return None

    def get_packets_due_for_retransmission(self) -> List[Packet]:
        now = time.time()
        due: List[Packet] = []
        expired_ids: List[str] = []

        for pkt_id, item in self.pending_acks.items():
            if now - item["sent_at"] >= self.timeout_seconds:
                if item["retries"] < self.max_retries:
                    item["retries"] += 1
                    item["sent_at"] = now
                    due.append(item["packet"])
                    logger.info(f"Retransmitting packet {pkt_id} (Attempt {item['retries']})")
                else:
                    expired_ids.append(pkt_id)
                    logger.warning(f"Packet {pkt_id} reached max retries, dropping.")

        for pkt_id in expired_ids:
            del self.pending_acks[pkt_id]

        return due

    def create_ack_packet(self, data_packet: Packet) -> Packet:
        return Packet(
            packet_id=f"ack-{data_packet.packet_id}",
            sender_id=self.sender_id,
            packet_type=PACKET_TYPE_ACK,
            payload={"acked_packet_id": data_packet.packet_id, "acked_seq_num": data_packet.seq_num},
        )
