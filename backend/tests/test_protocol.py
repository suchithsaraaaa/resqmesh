import time
import pytest
from backend.app.network.protocol import (
    Packet,
    PacketFramingParser,
    ACKTracker,
    PACKET_TYPE_DATA,
    PACKET_TYPE_ACK,
    compute_checksum,
)


def test_packet_checksum_and_serialization():
    pkt = Packet(
        packet_id="pkt-101",
        sender_id="device-alpha",
        payload={"incident_id": "inc-001", "status": "REPORTED"},
    )

    assert pkt.verify_checksum() is True

    # Test dictionary conversion round-trip
    pkt_dict = pkt.to_dict()
    restored_pkt = Packet.from_dict(pkt_dict)
    assert restored_pkt.packet_id == "pkt-101"
    assert restored_pkt.sender_id == "device-alpha"
    assert restored_pkt.checksum == pkt.checksum
    assert restored_pkt.verify_checksum() is True

    # Test corrupted payload detection
    restored_pkt.payload["status"] = "TAMPERED"
    assert restored_pkt.verify_checksum() is False


def test_packet_framing_parser():
    parser = PacketFramingParser()

    pkt1 = Packet(packet_id="p1", sender_id="node1", payload={"msg": "hello"})
    pkt2 = Packet(packet_id="p2", sender_id="node1", payload={"msg": "world"})

    frame1 = PacketFramingParser.encode_frame(pkt1)
    frame2 = PacketFramingParser.encode_frame(pkt2)

    # Feed full frame 1
    packets = parser.feed_bytes(frame1)
    assert len(packets) == 1
    assert packets[0].packet_id == "p1"

    # Feed split frame 2 in chunks
    chunk1 = frame2[:5]
    chunk2 = frame2[5:]

    packets_split1 = parser.feed_bytes(chunk1)
    assert len(packets_split1) == 0  # incomplete

    packets_split2 = parser.feed_bytes(chunk2)
    assert len(packets_split2) == 1
    assert packets_split2[0].packet_id == "p2"


def test_ack_tracker_lifecycle():
    tracker = ACKTracker(sender_id="node-local", timeout_seconds=0.1, max_retries=2)

    seq1 = tracker.get_next_seq_num()
    assert seq1 == 1

    pkt = Packet(packet_id="pkt-data-1", sender_id="node-local", seq_num=seq1, payload={"data": "test"})
    tracker.track_packet(pkt)
    assert "pkt-data-1" in tracker.pending_acks

    # Create and process ACK
    ack_pkt = tracker.create_ack_packet(pkt)
    acked_id = tracker.process_ack(ack_pkt)
    assert acked_id == "pkt-data-1"
    assert "pkt-data-1" not in tracker.pending_acks


def test_ack_tracker_retransmission():
    tracker = ACKTracker(sender_id="node-local", timeout_seconds=0.05, max_retries=1)
    pkt = Packet(packet_id="pkt-unacked", sender_id="node-local", payload={"data": "retransmit_me"})

    tracker.track_packet(pkt)
    time.sleep(0.06)

    # First retransmission due
    due1 = tracker.get_packets_due_for_retransmission()
    assert len(due1) == 1
    assert due1[0].packet_id == "pkt-unacked"

    time.sleep(0.06)
    # Exceeded max retries -> dropped
    due2 = tracker.get_packets_due_for_retransmission()
    assert len(due2) == 0
    assert "pkt-unacked" not in tracker.pending_acks
